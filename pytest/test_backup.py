import os
import pytest
from pathlib import Path
from mock import PropertyMock, mock, MagicMock, patch
from pathlib import Path
import docker
from docker.models.containers import Container
from itertools import cycle

from app.nautical_env import NauticalEnv
from app.backup import NauticalBackup


@pytest.fixture
def docker_mocks(request: pytest.FixtureRequest) -> tuple[MagicMock, MagicMock, MagicMock]:
    """Creates a mock Docker client and two mock containers.

    To use:
    ```
    def test_docker_run(self, docker_mocks):
        mockDockerClient, mockContainer1, mockContainer2 = docker_mocks
        mockDockerClient.containers.list.return_value = [mockContainer1, mockContainer2]
        # Do something...
    ```
    """
    # Set defaults
    default_labels = {
        "nautical-backup.group": "",
        "nautical-backup.additional-folders.when": "",
        "nautical-backup.additional-folders": "",
        "nautical-backup.rsync-custom-args": "",
        "nautical-backup.use-default-rsync-args": "",
        "nautical-backup.override-source-dir": "",
        "nautical-backup.override-destination-dir": "",
    }

    labels = dict(request.param.get("labels", default_labels))

    # These status are exactly what is required for the backup to run
    status_side_effect = request.param.get("status_side_effect", ["running", "exited", "exited", "exited", "running"])

    # Create mocks

    mockDockerClient = MagicMock(spec=docker.DockerClient)
    mockContainer1 = MagicMock(spec=Container)
    mockContainer1.name = "container1"
    mockContainer1.id = "1234456789"
    type(mockContainer1).status = PropertyMock(side_effect=cycle(status_side_effect))

    def fake_labels(key, default=None):
        return labels.get(key, default)

    mockContainer1.labels.get.side_effect = fake_labels

    mockContainer2 = MagicMock(spec=Container)
    mockContainer2.name = "container2"
    mockContainer2.id = "9876543210"
    type(mockContainer1).status = PropertyMock(side_effect=cycle(status_side_effect))
    mockContainer2.labels.get.side_effect = fake_labels

    return mockDockerClient, mockContainer1, mockContainer2


class TestBackup:
    # Default parameters for the entire class
    pytestmark = pytest.mark.parametrize(
        "docker_mocks",
        [
            {
                # "status_side_effect": ["running", "exited", "exited", "exited", "running"],
            },
        ],
        indirect=["docker_mocks"],
    )

    @classmethod
    def setup_class(cls):
        """Runs 1 time before all tests in this class"""
        pass

    def test_docker_run(self, docker_mocks):
        mockDockerClient, mockContainer1, mockContainer2 = docker_mocks
        mockDockerClient.containers.list.return_value = [mockContainer1, mockContainer2]

        nb = NauticalBackup(mockDockerClient)
        nb.backup()


class TestRsync:
    def test_rsync_commands(self, monkeypatch: pytest.MonkeyPatch):

        # Define the source location
        monkeypatch.setenv("DEST_LOCATION", "./tests/destination")
        monkeypatch.setenv("SOURCE_LOCATION", "./tests/source")

        env = NauticalEnv()
        SOURCE_LOCATION = env.SOURCE_LOCATION

        # Create directories and files
        Path(SOURCE_LOCATION, "container1").mkdir(parents=True, exist_ok=True)
        Path(SOURCE_LOCATION, "container1", "test.txt").touch()

        Path(SOURCE_LOCATION, "container2").mkdir(parents=True, exist_ok=True)
        Path(SOURCE_LOCATION, "container1", "test.txt").touch()
