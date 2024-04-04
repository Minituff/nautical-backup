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


def rm_tree(pth: Path):
    if not pth.exists():
        return
    for child in pth.iterdir():
        if child.is_file():
            child.unlink()
        else:
            rm_tree(child)
    pth.rmdir()
    
@pytest.fixture
def mock_docker_client() -> MagicMock:
    return MagicMock(spec=docker.DockerClient)


@pytest.fixture
def mock_container1(request: pytest.FixtureRequest) -> MagicMock:
    return create_mock_container(request)


@pytest.fixture
def mock_container2(request: pytest.FixtureRequest) -> MagicMock:
    return create_mock_container(request)


@pytest.fixture
def mock_container3(request: pytest.FixtureRequest) -> MagicMock:
    return create_mock_container(request)


@pytest.fixture
def mock_container4(request: pytest.FixtureRequest) -> MagicMock:
    return create_mock_container(request)


def create_mock_container(request: pytest.FixtureRequest) -> MagicMock:
    default_labels = {
        "nautical-backup.group": "",
        "nautical-backup.additional-folders.when": "",
        "nautical-backup.additional-folders": "",
        "nautical-backup.rsync-custom-args": "",
        "nautical-backup.use-default-rsync-args": "",
        "nautical-backup.override-source-dir": "",
        "nautical-backup.override-destination-dir": "",
    }

    # Use default labels but overwrite as added
    labels = default_labels
    request_labels = dict(request.param.get("labels", {}))
    if request_labels:
        labels.update(request_labels)

    status_side_effect = request.param.get("status_side_effect", ["running", "exited", "exited", "exited", "running"])

    mock_container = MagicMock(spec=Container)
    mock_container.name = request.param.get("name", "containerName_default")
    mock_container.id = request.param.get("id", "id_default")

    type(mock_container).status = PropertyMock(side_effect=cycle(status_side_effect))

    mock_container.labels.get.side_effect = lambda key, default=None: labels.get(key, default)

    nautical_env = NauticalEnv()
    # Create source and dest directories if they don't already exist
    if request.param.get("source_exists", True):
        source_dir = Path(nautical_env.SOURCE_LOCATION) / mock_container.name
        source_dir.mkdir(parents=True, exist_ok=True)

        if request.param.get("source_file_exists", True):
            # Create test files
            test_file = source_dir / "test_file.txt"
            with open(test_file, "w") as test_file:
                test_file.write("This is a test file")
    else:
        source_dir = Path(nautical_env.SOURCE_LOCATION) / mock_container.name
        rm_tree(source_dir)

    if request.param.get("dest_exists", True):
        dest_dir = Path(nautical_env.DEST_LOCATION) / mock_container.name
        dest_dir.mkdir(parents=True, exist_ok=True)
    else:
        dest_dir = Path(nautical_env.DEST_LOCATION) / mock_container.name
        rm_tree(dest_dir)

    return mock_container


class TestBackup:
    # Default parameters for the entire class
    # pytestmark = [
        # pytest.mark.parametrize("mock_container1", [{"name": "container1", "id": "123456789"}], indirect=True),
        # pytest.mark.parametrize("mock_container2", [{"name": "container2", "id": "9876543210"}], indirect=True),
    # ]

    @classmethod
    def setup_class(cls):
        """Runs 1 time before all tests in this class"""
        nautical_env = NauticalEnv()
        db_location = Path(nautical_env.NAUTICAL_DB_PATH)
        db_location.mkdir(parents=True, exist_ok=True)

    @mock.patch("subprocess.run")
    @pytest.mark.parametrize("mock_container1", [{"name": "container1", "id": "123456789"}], indirect=True)
    @pytest.mark.parametrize("mock_container2", [{"name": "container2", "id": "9876543210"}], indirect=True)
    def test_docker_calls(
        self,
        mock_subprocess_run: MagicMock,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
        mock_container2: MagicMock,
    ):
        """Test that the backup method calls the correct docker methods"""

        mock_docker_client.containers.list.return_value = [mock_container1, mock_container2]
        nb = NauticalBackup(mock_docker_client)
        nb.backup()

        # Containers are only listed once
        mock_docker_client.containers.list.assert_called()

        # Containers are stopped and started
        # Correct mocks have been used
        assert mock_container1.id == "123456789"
        assert mock_container1.name == "container1"
        mock_container1.stop.assert_called()
        mock_container1.start.assert_called()
        mock_container1.labels.get.assert_called()

        assert mock_container2.id == "9876543210"
        assert mock_container2.name == "container2"
        mock_container2.stop.assert_called()
        mock_container2.start.assert_called()
        mock_container2.labels.get.assert_called()

        # Here we assert the backup was atleast called
        # This would mean the mocks worked, and the src folders were created
        assert mock_subprocess_run.call_count == 2

    @mock.patch("subprocess.run")
    @pytest.mark.parametrize("mock_container1", [{"name": "container1", "id": "123456789", "source_exists": False}], indirect=True)
    @pytest.mark.parametrize("mock_container2", [{"name": "container2", "id": "9876543210"}], indirect=True)
    def test_missing_source_dir(
        self,
        mock_subprocess_run: MagicMock,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
        mock_container2: MagicMock,
    ):
        """Test 'docker stop' and 'rsync' is not called if source dir is missing"""

        mock_docker_client.containers.list.return_value = [mock_container1, mock_container2]
        nb = NauticalBackup(mock_docker_client)
        nb.backup()
        
        # Container once has no source dir, so no rsync or stop is called
        mock_container1.stop.assert_not_called()
        
        mock_container2.stop.assert_called()
        
        # Rsync should only be called once
        mock_subprocess_run.assert_called_once()