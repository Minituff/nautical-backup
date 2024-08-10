import os
import time
import pytest
from pathlib import Path
from mock import PropertyMock, mock, MagicMock, patch
from pathlib import Path
import docker
from docker.models.containers import Container
from itertools import cycle
from mock import call

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


def create_folder(pth: Path, and_file: bool = False):
    """Useful for creating folders and files for testing"""
    pth.mkdir(parents=True, exist_ok=True)

    if and_file:
        # Create test files
        test_file = pth / "test_file.txt"
        with open(test_file, "w") as test_file:
            test_file.write("This is a test file")


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

        cls.db_location = Path(nautical_env.NAUTICAL_DB_PATH)
        cls.src_location = Path(nautical_env.SOURCE_LOCATION)
        cls.dest_location = Path(nautical_env.DEST_LOCATION)

        # Before each test, clean the relavent directories
        rm_tree(cls.src_location)
        rm_tree(cls.dest_location)
        rm_tree(cls.db_location)

        # Make sure the directories exist
        cls.db_location.mkdir(parents=True, exist_ok=True)
        cls.src_location.mkdir(parents=True, exist_ok=True)
        cls.dest_location.mkdir(parents=True, exist_ok=True)

    @classmethod
    def teardown_class(cls):
        """Runs 1 time after all tests in this class"""
        nautical_env = NauticalEnv()

        cls.db_location = Path(nautical_env.NAUTICAL_DB_PATH)
        cls.src_location = Path(nautical_env.SOURCE_LOCATION)
        cls.dest_location = Path(nautical_env.DEST_LOCATION)

        # Before each test, clean the relavent directories
        rm_tree(cls.src_location)
        rm_tree(cls.dest_location)
        rm_tree(cls.db_location)

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
    @pytest.mark.parametrize(
        "mock_container1", [{"name": "container1", "id": "123456789", "source_exists": False}], indirect=True
    )
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

    @mock.patch("subprocess.run")
    @pytest.mark.parametrize(
        "mock_container1",
        [
            {
                "name": "container1",
                "id": "123456789",
                "status_side_effect": ["running", "running", "running", "running", "running"],
                "source_exists": False,
            }
        ],
        indirect=True,
    )
    def test_missing_source_dir_no_stop_and_start(
        self,
        mock_subprocess_run: MagicMock,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
    ):
        """Test 'docker stop' and 'rsync' is not called if source dir is missing"""

        mock_docker_client.containers.list.return_value = [mock_container1]
        nb = NauticalBackup(mock_docker_client)
        nb.backup()

        # Container once has no source dir, so no rsync or stop is called
        mock_container1.stop.assert_not_called()
        mock_container1.start.assert_not_called()

        mock_subprocess_run.assert_not_called()

    @mock.patch("subprocess.run")
    @pytest.mark.parametrize("mock_container1", [{"name": "nautical-backup", "id": "123456789"}], indirect=True)
    def test_skip_self_by_name(
        self,
        mock_subprocess_run: MagicMock,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """Test that Nautical skips itself"""

        monkeypatch.setenv("SELF_CONTAINER_ID", "nautical-backup")

        mock_docker_client.containers.list.return_value = [mock_container1]
        nb = NauticalBackup(mock_docker_client)
        nb.backup()

        # Rsync should only be called once
        mock_subprocess_run.assert_not_called()

    @mock.patch("subprocess.run")
    @pytest.mark.parametrize("mock_container1", [{"name": "container1", "id": "123456789"}], indirect=True)
    def test_skip_self_by_id(
        self,
        mock_subprocess_run: MagicMock,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """Test that Nautical skips itself"""

        monkeypatch.setenv("SELF_CONTAINER_ID", "123456789")

        mock_docker_client.containers.list.return_value = [mock_container1]
        nb = NauticalBackup(mock_docker_client)
        nb.backup()

        # Rsync should only be called once
        mock_subprocess_run.assert_not_called()

    @mock.patch("subprocess.run")
    @pytest.mark.parametrize("mock_container1", [{"name": "container1", "id": "123456789"}], indirect=True)
    def test_rsync_commands(
        self,
        mock_subprocess_run: MagicMock,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
    ):
        """Test if Rsync was called with the correct arguments"""

        mock_docker_client.containers.list.return_value = [mock_container1]
        nb = NauticalBackup(mock_docker_client)
        nb.backup()

        # Rsync should only be called once
        mock_subprocess_run.assert_called_once()

        mock_subprocess_run.assert_any_call(
            ["-raq", f"{self.src_location}/container1/", f"{self.dest_location}/container1/"],
            shell=True,
            executable="/usr/bin/rsync",
            capture_output=False,
        )

    @mock.patch("subprocess.run")
    @pytest.mark.parametrize("mock_container1", [{"name": "container1", "id": "123456789"}], indirect=True)
    @pytest.mark.parametrize("mock_container2", [{"name": "container2", "id": "9876543210"}], indirect=True)
    @pytest.mark.parametrize("mock_container3", [{"name": "container3", "id": "6969696969"}], indirect=True)
    def test_skip_container_env(
        self,
        mock_subprocess_run: MagicMock,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
        mock_container2: MagicMock,
        mock_container3: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """Test that the backup method calls the correct docker methods"""

        monkeypatch.setenv("SKIP_CONTAINERS", "container-name2,container1,container-fake,6969696969")

        mock_docker_client.containers.list.return_value = [mock_container1, mock_container2, mock_container3]
        nb = NauticalBackup(mock_docker_client)
        nb.backup()

        # Container1 should be skipped by NAME
        mock_container1.stop.assert_not_called()
        mock_container1.start.assert_not_called()

        # Container2 should be stopped and started
        mock_container2.stop.assert_called()
        mock_container2.start.assert_called()

        # Container3 should be skipped by ID
        mock_container3.stop.assert_not_called()
        mock_container3.start.assert_not_called()

        # Rsync should only be called once (on container2)
        assert mock_subprocess_run.call_count == 1

    @mock.patch("subprocess.run")
    @pytest.mark.parametrize(
        "mock_container1",
        [{"name": "container1", "id": "123456789", "labels": {"nautical-backup.enable": "false"}}],
        indirect=True,
    )
    @pytest.mark.parametrize("mock_container2", [{"name": "container2", "id": "9876543210"}], indirect=True)
    def test_enable_label(
        self,
        mock_subprocess_run: MagicMock,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
        mock_container2: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """Test that the backup method calls the correct docker methods"""

        mock_docker_client.containers.list.return_value = [mock_container1, mock_container2]
        nb = NauticalBackup(mock_docker_client)
        nb.backup()

        # Container1 should be skipped
        mock_container1.stop.assert_not_called()
        mock_container1.start.assert_not_called()

        # Container2 should be stopped and started
        mock_container2.stop.assert_called()
        mock_container2.start.assert_called()

        # Rsync should only be called once (on container2)
        assert mock_subprocess_run.call_count == 1

    @mock.patch("subprocess.run")
    @pytest.mark.parametrize(
        "mock_container1",
        [{"name": "container1", "id": "123456789", "labels": {"nautical-backup.enable": "false"}}],
        indirect=True,
    )
    @pytest.mark.parametrize(
        "mock_container2",
        [{"name": "container2", "id": "9876543210", "labels": {"nautical-backup.enable": "true"}}],
        indirect=True,
    )
    @pytest.mark.parametrize("mock_container3", [{"name": "container3", "id": "1112131415"}], indirect=True)
    def test_require_label(
        self,
        mock_subprocess_run: MagicMock,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
        mock_container2: MagicMock,
        mock_container3: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """Test that the REQUIRE_LABEL variable works as expected"""

        monkeypatch.setenv("REQUIRE_LABEL", "true")

        mock_docker_client.containers.list.return_value = [mock_container1, mock_container2, mock_container3]
        nb = NauticalBackup(mock_docker_client)
        nb.backup()

        # Container1 should be skipped
        mock_container1.stop.assert_not_called()
        mock_container1.start.assert_not_called()

        # Container3 should be skipped
        mock_container3.stop.assert_not_called()
        mock_container3.start.assert_not_called()

        # Container2 should be stopped and started
        mock_container2.stop.assert_called()
        mock_container2.start.assert_called()

        # Rsync should only be called once (on container2)
        assert mock_subprocess_run.call_count == 1

    @mock.patch("subprocess.run")
    @pytest.mark.parametrize("mock_container1", [{"name": "container1", "id": "123456789"}], indirect=True)
    @pytest.mark.parametrize("mock_container2", [{"name": "container2", "id": "9876543210"}], indirect=True)
    @pytest.mark.parametrize("mock_container3", [{"name": "container3", "id": "1112131415"}], indirect=True)
    def test_override_src_env(
        self,
        mock_subprocess_run: MagicMock,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
        mock_container2: MagicMock,
        mock_container3: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """Test that override source dir works with environment variables"""

        monkeypatch.setenv("OVERRIDE_SOURCE_DIR", "container1:container1-override,9876543210:container2-new")

        # Folders must be created before the backup is called
        nautical_env = NauticalEnv()
        create_folder(Path(nautical_env.SOURCE_LOCATION) / "container1-override", and_file=True)
        create_folder(Path(nautical_env.SOURCE_LOCATION) / "container2-new", and_file=True)

        mock_docker_client.containers.list.return_value = [mock_container1, mock_container2, mock_container3]
        nb = NauticalBackup(mock_docker_client)
        nb.backup()

        mock_subprocess_run.assert_any_call(
            ["-raq", f"{self.src_location}/container1-override/", f"{self.dest_location}/container1-override/"],
            shell=True,
            executable="/usr/bin/rsync",
            capture_output=False,
        )
        mock_subprocess_run.assert_any_call(
            ["-raq", f"{self.src_location}/container2-new/", f"{self.dest_location}/container2-new/"],
            shell=True,
            executable="/usr/bin/rsync",
            capture_output=False,
        )
        assert mock_subprocess_run.call_count == 3

    @mock.patch("subprocess.run")
    @pytest.mark.parametrize(
        "mock_container1",
        [
            {
                "name": "container1",
                "id": "123456789",
                "labels": {"nautical-backup.override-source-dir": "container1-override-label"},
            }
        ],
        indirect=True,
    )
    def test_override_src_label(
        self,
        mock_subprocess_run: MagicMock,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
    ):
        """Test override source dir with label"""

        # Folders must be created before the backup is called
        nautical_env = NauticalEnv()
        create_folder(Path(nautical_env.SOURCE_LOCATION) / "container1-override-label", and_file=True)

        mock_docker_client.containers.list.return_value = [mock_container1]
        nb = NauticalBackup(mock_docker_client)
        nb.backup()

        mock_subprocess_run.assert_any_call(
            [
                "-raq",
                f"{self.src_location}/container1-override-label/",
                f"{self.dest_location}/container1-override-label/",
            ],
            shell=True,
            executable="/usr/bin/rsync",
            capture_output=False,
        )

    @mock.patch("subprocess.run")
    @pytest.mark.parametrize("mock_container1", [{"name": "container1", "id": "123456789"}], indirect=True)
    @pytest.mark.parametrize("mock_container2", [{"name": "container2", "id": "9876543210"}], indirect=True)
    @pytest.mark.parametrize("mock_container3", [{"name": "container3", "id": "1112131415"}], indirect=True)
    def test_override_dest_env(
        self,
        mock_subprocess_run: MagicMock,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
        mock_container2: MagicMock,
        mock_container3: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """Test that override destination dir works with environment variables"""

        monkeypatch.setenv("OVERRIDE_DEST_DIR", "container1:container1-override,9876543210:container2-new")

        # Folders must be created before the backup is called
        nautical_env = NauticalEnv()
        create_folder(Path(nautical_env.DEST_LOCATION) / "container1-override", and_file=True)
        create_folder(Path(nautical_env.DEST_LOCATION) / "container2-new", and_file=True)

        mock_docker_client.containers.list.return_value = [mock_container1, mock_container2, mock_container3]
        nb = NauticalBackup(mock_docker_client)
        nb.backup()

        mock_subprocess_run.assert_any_call(
            ["-raq", f"{self.src_location}/container1/", f"{self.dest_location}/container1-override/"],
            shell=True,
            executable="/usr/bin/rsync",
            capture_output=False,
        )
        mock_subprocess_run.assert_any_call(
            ["-raq", f"{self.src_location}/container2/", f"{self.dest_location}/container2-new/"],
            shell=True,
            executable="/usr/bin/rsync",
            capture_output=False,
        )
        assert mock_subprocess_run.call_count == 3

    @mock.patch("subprocess.run")
    @pytest.mark.parametrize(
        "mock_container1",
        [
            {
                "name": "container1",
                "id": "123456789",
                "labels": {"nautical-backup.override-destination-dir": "container1-override-label"},
            }
        ],
        indirect=True,
    )
    def test_override_dest_label(
        self,
        mock_subprocess_run: MagicMock,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
    ):
        """Test override source dir with label"""

        mock_docker_client.containers.list.return_value = [mock_container1]
        nb = NauticalBackup(mock_docker_client)
        nb.backup()

        mock_subprocess_run.assert_any_call(
            [
                "-raq",
                f"{self.src_location}/container1/",
                f"{self.dest_location}/container1-override-label/",
            ],
            shell=True,
            executable="/usr/bin/rsync",
            capture_output=False,
        )

    @mock.patch("subprocess.run")
    @pytest.mark.parametrize(
        "mock_container1",
        [
            {
                "name": "container1",
                "id": "123456789",
                "status_side_effect": ["running", "running", "running", "running", "running"],
            }
        ],
        indirect=True,
    )
    @pytest.mark.parametrize("mock_container2", [{"name": "container2", "id": "9876543210"}], indirect=True)
    @pytest.mark.parametrize("mock_container3", [{"name": "container3", "id": "1112131415"}], indirect=True)
    def test_skip_stopping_env(
        self,
        mock_subprocess_run: MagicMock,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
        mock_container2: MagicMock,
        mock_container3: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """Test that the backup method calls the correct docker methods"""

        # Skip stopping container1 and container2 (by name and id)
        monkeypatch.setenv("SKIP_STOPPING", "container-fake,container1,9876543210")

        mock_docker_client.containers.list.return_value = [mock_container1, mock_container2, mock_container3]
        nb = NauticalBackup(mock_docker_client)
        nb.backup()

        # Container1 should not be stopped
        mock_container1.stop.assert_not_called()

        # Container2 should not be stopped
        mock_container2.stop.assert_not_called()

        # Container3 should be stopped and started
        mock_container3.stop.assert_called()

        # Rsync should only for all containers
        assert mock_subprocess_run.call_count == 3

    @mock.patch("subprocess.run")
    @pytest.mark.parametrize(
        "mock_container1",
        [
            {
                "name": "container1",
                "id": "123456789",
                "labels": {"nautical-backup.stop-before-backup": "false"},
                "status_side_effect": ["running", "running", "running", "running", "running"],
            }
        ],
        indirect=True,
    )
    @pytest.mark.parametrize("mock_container2", [{"name": "container2", "id": "9876543210"}], indirect=True)
    def test_skip_stopping_label_false(
        self,
        mock_subprocess_run: MagicMock,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
        mock_container2: MagicMock,
    ):
        """Test skip stopping (false) label"""

        mock_docker_client.containers.list.return_value = [mock_container1, mock_container2]
        nb = NauticalBackup(mock_docker_client)
        nb.backup()

        # Container1 should not be stopped because of the label
        mock_container1.stop.assert_not_called()

        # Container2 should be stopped since nothing has changed
        mock_container2.stop.assert_called()

        # Rsync should be run for both containers
        assert mock_subprocess_run.call_count == 2

    @mock.patch("subprocess.run")
    @pytest.mark.parametrize(
        "mock_container1",
        [
            {
                "name": "container1",
                "id": "123456789",
                "labels": {"nautical-backup.stop-before-backup": "true"},
            }
        ],
        indirect=True,
    )
    @pytest.mark.parametrize("mock_container2", [{"name": "container2", "id": "9876543210"}], indirect=True)
    def test_skip_stopping_label_true(
        self,
        mock_subprocess_run: MagicMock,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
        mock_container2: MagicMock,
    ):
        """Test skip stopping (true) label"""

        mock_docker_client.containers.list.return_value = [mock_container1, mock_container2]
        nb = NauticalBackup(mock_docker_client)
        nb.backup()

        # Container1 should be stopped because of the label
        mock_container1.stop.assert_called()

        # Container2 should be stopped since nothing has changed
        mock_container2.stop.assert_called()

        # Rsync should be run for both containers
        assert mock_subprocess_run.call_count == 2

    @mock.patch("subprocess.run")
    @pytest.mark.parametrize("mock_container1", [{"name": "container1", "id": "123456789"}], indirect=True)
    def test_custom_rsync_args_env(
        self,
        mock_subprocess_run: MagicMock,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """Test that the backup method calls the correct docker methods"""

        # Skip stopping container1 and container2 (by name and id)
        monkeypatch.setenv("USE_DEFAULT_RSYNC_ARGS", "false")
        monkeypatch.setenv("RSYNC_CUSTOM_ARGS", "-aq")

        mock_docker_client.containers.list.return_value = [mock_container1]
        nb = NauticalBackup(mock_docker_client)
        nb.backup()

        # Rsync should only be called once
        # Rsync should be called with custom args
        # Rsync custom args should overwrite the default args
        mock_subprocess_run.assert_called_once_with(
            [
                "-aq",
                f"{self.src_location}/container1/",
                f"{self.dest_location}/container1/",
            ],
            shell=True,
            executable="/usr/bin/rsync",
            capture_output=False,
        )

    @mock.patch("subprocess.run")
    @pytest.mark.parametrize(
        "mock_container1",
        [
            {
                "name": "container1",
                "id": "123456789",
                "labels": {
                    "nautical-backup.use-default-rsync-args": "false",
                    "nautical-backup.rsync-custom-args": "-aq",
                },
            }
        ],
        indirect=True,
    )
    def test_custom_rsync_args_label(
        self,
        mock_subprocess_run: MagicMock,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
    ):
        """Test custom rsync args with label"""

        mock_docker_client.containers.list.return_value = [mock_container1]
        nb = NauticalBackup(mock_docker_client)
        nb.backup()

        mock_subprocess_run.assert_any_call(
            [
                "-aq",
                f"{self.src_location}/container1/",
                f"{self.dest_location}/container1/",
            ],
            shell=True,
            executable="/usr/bin/rsync",
            capture_output=False,
        )

    @mock.patch("subprocess.run")
    @pytest.mark.parametrize(
        "mock_container1",
        [
            {
                "name": "container1",
                "id": "123456789",
                "labels": {
                    "nautical-backup.use-default-rsync-args": "false",
                    "nautical-backup.rsync-custom-args": "--exclude=AsdF",
                },
            }
        ],
        indirect=True,
    )
    def test_custom_rsync_args_label_case_sensitivity(
        self,
        mock_subprocess_run: MagicMock,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
    ):
        """Test custom rsync args with label and that it keeps case sensitivity"""

        mock_docker_client.containers.list.return_value = [mock_container1]
        nb = NauticalBackup(mock_docker_client)
        nb.backup()

        assert mock_subprocess_run.call_args_list[0][0][0] == [
            "--exclude=AsdF",
            f"{self.src_location}/container1/",
            f"{self.dest_location}/container1/",
        ]

    @mock.patch("subprocess.run")
    @pytest.mark.parametrize(
        "mock_container1",
        [
            {
                "name": "container1",
                "id": "123456789",
                "labels": {
                    "nautical-backup.use-default-rsync-args": "false",
                    "nautical-backup.rsync-custom-args": "-aq",
                },
            }
        ],
        indirect=True,
    )
    @pytest.mark.parametrize("mock_container2", [{"name": "container2", "id": "9876543210"}], indirect=True)
    def test_custom_rsync_args_env_and_label(
        self,
        mock_subprocess_run: MagicMock,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
        mock_container2: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """Test custom rsync args with label"""

        monkeypatch.setenv("USE_DEFAULT_RSYNC_ARGS", "false")
        monkeypatch.setenv("RSYNC_CUSTOM_ARGS", "-something")

        mock_docker_client.containers.list.return_value = [mock_container1, mock_container2]
        nb = NauticalBackup(mock_docker_client)
        nb.backup()

        # Container 1 will use the label's custom rsync args
        mock_subprocess_run.assert_any_call(
            [
                "-aq",
                f"{self.src_location}/container1/",
                f"{self.dest_location}/container1/",
            ],
            shell=True,
            executable="/usr/bin/rsync",
            capture_output=False,
        )

        # Container 2 will use env custom rsync args
        mock_subprocess_run.assert_any_call(
            [
                "-something",
                f"{self.src_location}/container2/",
                f"{self.dest_location}/container2/",
            ],
            shell=True,
            executable="/usr/bin/rsync",
            capture_output=False,
        )

    @mock.patch("subprocess.run")
    @pytest.mark.parametrize("mock_container1", [{"name": "Pi.Alert", "id": "123456789"}], indirect=True)
    def test_keep_src_dir_name_env_false(
        self,
        mock_subprocess_run: MagicMock,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """This test checks if the destination directory is renamed when KEEP_SRC_DIR_NAME is false"""

        # Folders must be created before the backup is called
        nautical_env = NauticalEnv()
        create_folder(Path(nautical_env.SOURCE_LOCATION) / "pialert", and_file=True)

        # Skip stopping container1 and container2 (by name and id)
        monkeypatch.setenv("KEEP_SRC_DIR_NAME", "false")
        monkeypatch.setenv(
            "OVERRIDE_SOURCE_DIR",
            "Pi.Alert:pialert",
        )

        mock_docker_client.containers.list.return_value = [mock_container1]
        nb = NauticalBackup(mock_docker_client)
        nb.backup()

        # Rsync should only be called once
        # Rsync should be called with custom args
        # Rsync custom args should overwrite the default args
        mock_subprocess_run.assert_called_once_with(
            [
                "-raq",
                f"{self.src_location}/pialert/",
                f"{self.dest_location}/Pi.Alert/",
            ],
            shell=True,
            executable="/usr/bin/rsync",
            capture_output=False,
        )

    @mock.patch("subprocess.run")
    @pytest.mark.parametrize("mock_container1", [{"name": "container1", "id": "123456789"}], indirect=True)
    def test_keep_src_dir_name_env_true(
        self,
        mock_subprocess_run: MagicMock,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """This test ensures that the source directory name is mirrored in the destination directory name when KEEP_SRC_DIR_NAME is set to true."""

        # Folders must be created before the backup is called
        nautical_env = NauticalEnv()
        create_folder(Path(nautical_env.SOURCE_LOCATION) / "container1-override", and_file=True)

        # Skip stopping container1 and container2 (by name and id)
        monkeypatch.setenv("KEEP_SRC_DIR_NAME", "true")
        monkeypatch.setenv(
            "OVERRIDE_SOURCE_DIR",
            "container1:container1-override,container2:container2-override,container3:container3-new",
        )

        mock_docker_client.containers.list.return_value = [mock_container1]
        nb = NauticalBackup(mock_docker_client)
        nb.backup()

        # Rsync should only be called once
        # Rsync should be called with custom args
        # Rsync custom args should overwrite the default args
        mock_subprocess_run.assert_called_once_with(
            [
                "-raq",
                f"{self.src_location}/container1-override/",
                f"{self.dest_location}/container1-override/",
            ],
            shell=True,
            executable="/usr/bin/rsync",
            capture_output=False,
        )

    @mock.patch("subprocess.run")
    @pytest.mark.parametrize(
        "mock_container1",
        [
            {
                "name": "container1",
                "id": "123456789",
                "labels": {
                    "nautical-backup.keep_src_dir_name": "false",
                    "nautical-backup.override-source-dir": "container1-new",
                },
            }
        ],
        indirect=True,
    )
    def test_keep_src_dir_name_label_false(
        self,
        mock_subprocess_run: MagicMock,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
    ):
        """Test test_keep_src_dir_name_label_false"""

        # Folders must be created before the backup is called
        nautical_env = NauticalEnv()
        create_folder(Path(nautical_env.SOURCE_LOCATION) / "container1-new", and_file=True)

        mock_docker_client.containers.list.return_value = [mock_container1]
        nb = NauticalBackup(mock_docker_client)
        nb.backup()

        mock_subprocess_run.assert_any_call(
            [
                "-raq",
                f"{self.src_location}/container1-new/",
                f"{self.dest_location}/container1/",
            ],
            shell=True,
            executable="/usr/bin/rsync",
            capture_output=False,
        )

    @mock.patch("subprocess.run")
    @pytest.mark.parametrize(
        "mock_container1",
        [
            {
                "name": "container1",
                "id": "123456789",
                "labels": {
                    "nautical-backup.keep_src_dir_name": "true",
                    "nautical-backup.override-source-dir": "container1-new",
                },
            }
        ],
        indirect=True,
    )
    def test_keep_src_dir_name_label_true(
        self,
        mock_subprocess_run: MagicMock,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
    ):
        """Test that the source directory name is mirrored in the destination directory name when KEEP_SRC_DIR_NAME is set to true."""

        # Folders must be created before the backup is called
        nautical_env = NauticalEnv()
        create_folder(Path(nautical_env.SOURCE_LOCATION) / "container1-new", and_file=True)

        mock_docker_client.containers.list.return_value = [mock_container1]
        nb = NauticalBackup(mock_docker_client)
        nb.backup()

        mock_subprocess_run.assert_any_call(
            [
                "-raq",
                f"{self.src_location}/container1-new/",
                f"{self.dest_location}/container1-new/",
            ],
            shell=True,
            executable="/usr/bin/rsync",
            capture_output=False,
        )

    @pytest.mark.parametrize(
        "mock_container1",
        [{"name": "container1", "id": "123456789"}],
        indirect=True,
    )
    def test_get_dest_dir(
        self,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
    ):
        """Test test_get_dest_dir"""

        mock_docker_client.containers.list.return_value = [mock_container1]
        nb = NauticalBackup(mock_docker_client)
        dest_name = nb._get_dest_dir(mock_container1, "container1")

        assert str(dest_name) == f"{self.dest_location}/container1"

    @pytest.mark.parametrize(
        "mock_container1",
        [{"name": "container1", "id": "123456789"}],
        indirect=True,
    )
    def test_USE_DEST_DATE_FOLDER(
        self,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """Test test_USE_DEST_DATE_FOLDER"""

        time_format = time.strftime("%Y-%m-%d")

        monkeypatch.setenv("USE_DEST_DATE_FOLDER", "true")

        mock_docker_client.containers.list.return_value = [mock_container1]
        nb = NauticalBackup(mock_docker_client)
        dest_name = nb._get_dest_dir(mock_container1, "container1")

        assert str(dest_name) == f"{self.dest_location}/{time_format}/container1"

        monkeypatch.setenv("USE_DEST_DATE_FOLDER", "false")
        nb = NauticalBackup(mock_docker_client)
        dest_name = nb._get_dest_dir(mock_container1, "container1")
        assert str(dest_name) == f"{self.dest_location}/container1"

    @pytest.mark.parametrize(
        "mock_container1",
        [{"name": "container1", "id": "123456789"}],
        indirect=True,
    )
    def test_DEST_DATE_PATH_FORMAT(
        self,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """Test DEST_DATE_PATH_FORMAT"""

        time_format = time.strftime("%Y-%m-%d")
        monkeypatch.setenv("USE_DEST_DATE_FOLDER", "true")
        mock_docker_client.containers.list.return_value = [mock_container1]

        monkeypatch.setenv("DEST_DATE_PATH_FORMAT", "date/container")
        nb = NauticalBackup(mock_docker_client)
        dest_name = nb._get_dest_dir(mock_container1, "container1")

        assert str(dest_name) == f"{self.dest_location}/{time_format}/container1"

        monkeypatch.setenv("DEST_DATE_PATH_FORMAT", "container/date")
        nb = NauticalBackup(mock_docker_client)
        dest_name = nb._get_dest_dir(mock_container1, "container1")

        assert str(dest_name) == f"{self.dest_location}/container1/{time_format}"

        monkeypatch.setenv("DEST_DATE_PATH_FORMAT", "")
        nb = NauticalBackup(mock_docker_client)
        dest_name = nb._get_dest_dir(mock_container1, "container1")

        assert str(dest_name) == f"{self.dest_location}/{time_format}/container1"

    @pytest.mark.parametrize(
        "mock_container1",
        [{"name": "container1", "id": "123456789"}],
        indirect=True,
    )
    def test_DEST_DATE_FORMAT(
        self,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """Test DEST_DATE_FORMAT"""

        time_format = time.strftime("%Y-%m-%d")
        monkeypatch.setenv("USE_DEST_DATE_FOLDER", "true")
        mock_docker_client.containers.list.return_value = [mock_container1]

        nb = NauticalBackup(mock_docker_client)
        dest_name = nb._get_dest_dir(mock_container1, "container1")

        assert str(dest_name) == f"{self.dest_location}/{time_format}/container1"

        time_format_str = "%b %d %Y %H:%M:%S"
        time_format = time.strftime(time_format_str)
        monkeypatch.setenv("DEST_DATE_FORMAT", time_format_str)

        nb = NauticalBackup(mock_docker_client)
        dest_name = nb._get_dest_dir(mock_container1, "container1")
        assert str(dest_name) == f"{self.dest_location}/{time_format}/container1"

        time_format_str = "Prefix %D %T Suffix"
        time_format = time.strftime(time_format_str)
        monkeypatch.setenv("DEST_DATE_FORMAT", time_format_str)

        nb = NauticalBackup(mock_docker_client)
        dest_name = nb._get_dest_dir(mock_container1, "container1")
        assert str(dest_name) == f"{self.dest_location}/{time_format}/container1"

    @pytest.mark.parametrize(
        "mock_container1",
        [
            {
                "name": "container1",
                "id": "123456789",
                "labels": {
                    "nautical-backup.override-source-dir": "ctr1-src",
                    "nautical-backup.override-destination-dir": "ctr1-dest",
                },
            }
        ],
        indirect=True,
    )
    def test_USE_DEST_DATE_FOLDER_with_overrides(
        self,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """Test USE_DEST_DATE_FOLDER with overrides"""

        # Folders must be created before the backup is called
        nautical_env = NauticalEnv()
        create_folder(Path(nautical_env.SOURCE_LOCATION) / "ctr1-src", and_file=True)

        time_format = time.strftime("%Y-%m-%d")
        monkeypatch.setenv("USE_DEST_DATE_FOLDER", "true")
        mock_docker_client.containers.list.return_value = [mock_container1]

        nb = NauticalBackup(mock_docker_client)
        src_pth, src_name = nb._get_src_dir(mock_container1)
        dest_name = nb._get_dest_dir(mock_container1, src_name)

        assert str(src_pth) == f"{self.src_location}/ctr1-src"
        assert str(dest_name) == f"{self.dest_location}/{time_format}/ctr1-dest"

    @pytest.mark.parametrize(
        "mock_container1",
        [
            {
                "name": "container1",
                "id": "123456789",
                "labels": {
                    "nautical-backup.override-source-dir": "ctr1-src",
                    "nautical-backup.override-destination-dir": "ctr1-dest",
                },
            }
        ],
        indirect=True,
    )
    def test_USE_DEST_DATE_FOLDER_with_overrides_and_DEST_DATE_PATH_FORMAT(
        self,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """Test USE_DEST_DATE_FOLDER with overrides and DEST_DATE_PATH_FORMAT"""

        # Folders must be created before the backup is called
        nautical_env = NauticalEnv()
        create_folder(Path(nautical_env.SOURCE_LOCATION) / "ctr1-src", and_file=True)

        time_format = time.strftime("%Y-%m-%d")
        monkeypatch.setenv("USE_DEST_DATE_FOLDER", "true")
        monkeypatch.setenv("DEST_DATE_PATH_FORMAT", "container/date")
        mock_docker_client.containers.list.return_value = [mock_container1]

        nb = NauticalBackup(mock_docker_client)
        src_pth, src_name = nb._get_src_dir(mock_container1)
        dest_name = nb._get_dest_dir(mock_container1, src_name)

        assert str(src_pth) == f"{self.src_location}/ctr1-src"
        assert str(dest_name) == f"{self.dest_location}/ctr1-dest/{time_format}"

    @mock.patch("subprocess.run")
    @pytest.mark.parametrize(
        "mock_container1",
        [
            {
                "name": "container1",
                "id": "123456789",
                "labels": {
                    "nautical-backup.additional-folders": "add1",
                },
            }
        ],
        indirect=True,
    )
    def test_additional_folders_and_USE_DEST_DATE_FOLDER(
        self,
        mock_subprocess_run: MagicMock,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """Test test_additional_folders_label and USE_DEST_DATE_FOLDER"""

        # Folders must be created before the backup is called
        nautical_env = NauticalEnv()
        create_folder(Path(nautical_env.SOURCE_LOCATION) / "add1", and_file=True)

        time_format = time.strftime("%Y-%m-%d")
        monkeypatch.setenv("USE_DEST_DATE_FOLDER", "true")
        mock_docker_client.containers.list.return_value = [mock_container1]
        nb = NauticalBackup(mock_docker_client)
        nb.backup()

        assert mock_subprocess_run.call_count == 2

        # Src location
        assert mock_subprocess_run.call_args_list[1][0][0][1] == f"{self.src_location}/add1/"

        # Dest location
        assert mock_subprocess_run.call_args_list[1][0][0][2] == f"{self.dest_location}/{time_format}/add1/"

    @mock.patch("subprocess.run")
    @pytest.mark.parametrize(
        "mock_container1",
        [
            {
                "name": "container1",
                "id": "123456789",
                "labels": {
                    "nautical-backup.additional-folders": "add1",
                },
            }
        ],
        indirect=True,
    )
    def test_additional_folders_and_USE_DEST_DATE_FOLDER_and_DEST_DATE_FORMAT(
        self,
        mock_subprocess_run: MagicMock,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """Test test_additional_folders_label and DEST_DATE_FORMAT"""

        # Folders must be created before the backup is called
        nautical_env = NauticalEnv()
        create_folder(Path(nautical_env.SOURCE_LOCATION) / "add1", and_file=True)

        time_format = time.strftime("%Y-%m-%d")
        time_format_str = "%D_%d"
        time_format = time.strftime(time_format_str)
        monkeypatch.setenv("DEST_DATE_FORMAT", rf"{time_format_str}")
        monkeypatch.setenv("USE_DEST_DATE_FOLDER", "true")
        mock_docker_client.containers.list.return_value = [mock_container1]
        nb = NauticalBackup(mock_docker_client)
        nb.backup()

        assert mock_subprocess_run.call_count == 2

        # Src location
        assert mock_subprocess_run.call_args_list[1][0][0][1] == f"{self.src_location}/add1/"

        # Dest location
        assert mock_subprocess_run.call_args_list[1][0][0][2] == f"{self.dest_location}/{time_format}/add1/"

    @mock.patch("subprocess.run")
    @pytest.mark.parametrize(
        "mock_container1",
        [
            {
                "name": "container1",
                "id": "123456789",
                "labels": {
                    "nautical-backup.additional-folders": "add1",
                },
            }
        ],
        indirect=True,
    )
    def test_additional_folders_and_DEST_DATE_PATH_FORMAT(
        self,
        mock_subprocess_run: MagicMock,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """Test test_additional_folders_label and DEST_DATE_PATH_FORMAT"""

        # Folders must be created before the backup is called
        nautical_env = NauticalEnv()
        create_folder(Path(nautical_env.SOURCE_LOCATION) / "add1", and_file=True)

        time_format = time.strftime("%Y-%m-%d")
        monkeypatch.setenv("USE_DEST_DATE_FOLDER", "true")
        monkeypatch.setenv("DEST_DATE_PATH_FORMAT", "container/date")
        mock_docker_client.containers.list.return_value = [mock_container1]
        nb = NauticalBackup(mock_docker_client)
        nb.backup()

        assert mock_subprocess_run.call_count == 2

        # Src location
        assert mock_subprocess_run.call_args_list[1][0][0][1] == f"{self.src_location}/add1/"

        # Dest location
        assert mock_subprocess_run.call_args_list[1][0][0][2] == f"{self.dest_location}/add1/{time_format}/"

    @mock.patch("subprocess.run")
    @pytest.mark.parametrize(
        "mock_container1",
        [{"name": "container1", "id": "123456789"}],
        indirect=True,
    )
    def test_custom_destination_folders_are_used_in_rsync(
        self,
        mock_subprocess_run: MagicMock,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """Test DEST_DATE_FORMAT gets passed to rsync"""

        monkeypatch.setenv("USE_DEST_DATE_FOLDER", "true")
        mock_docker_client.containers.list.return_value = [mock_container1]

        time_format_str = "%D_%d"
        time_format = time.strftime(time_format_str)
        monkeypatch.setenv("DEST_DATE_FORMAT", rf"{time_format_str}")

        nb = NauticalBackup(mock_docker_client)
        nb.backup()

        print(mock_subprocess_run.call_args_list)
        mock_subprocess_run.assert_any_call(
            [
                "-raq",
                f"{self.src_location}/container1/",
                f"{self.dest_location}/{time_format}/container1/",
            ],
            shell=True,
            executable="/usr/bin/rsync",
            capture_output=False,
        )
        rm_tree(Path(self.dest_location) / time_format / "container1")

    @mock.patch("subprocess.run")
    @pytest.mark.parametrize("mock_container1", [{"name": "container1", "id": "123456789"}], indirect=True)
    def test_additional_folders_env_before(
        self,
        mock_subprocess_run: MagicMock,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """Test additional folders env before"""

        # Folders must be created before the backup is called
        nautical_env = NauticalEnv()
        create_folder(Path(nautical_env.SOURCE_LOCATION) / "container1-override", and_file=True)

        # Skip stopping container1 and container2 (by name and id)
        monkeypatch.setenv("ADDITIONAL_FOLDERS", "add1,add2")
        monkeypatch.setenv("ADDITIONAL_FOLDERS_WHEN", "before")

        mock_docker_client.containers.list.return_value = [mock_container1]
        nb = NauticalBackup(mock_docker_client)
        nb.backup()

        assert mock_subprocess_run.call_args_list[0][0][0] == [
            "-raq",
            f"{self.src_location}/add1/",
            f"{self.dest_location}/add1/",
        ]
        assert mock_subprocess_run.call_args_list[1][0][0] == [
            "-raq",
            f"{self.src_location}/add2/",
            f"{self.dest_location}/add2/",
        ]
        assert mock_subprocess_run.call_args_list[2][0][0] == [
            "-raq",
            f"{self.src_location}/container1/",
            f"{self.dest_location}/container1/",
        ]

    @mock.patch("subprocess.run")
    @pytest.mark.parametrize("mock_container1", [{"name": "container1", "id": "123456789"}], indirect=True)
    def test_additional_folders_env_after(
        self,
        mock_subprocess_run: MagicMock,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """Test additional folders env after"""

        # Folders must be created before the backup is called
        nautical_env = NauticalEnv()
        create_folder(Path(nautical_env.SOURCE_LOCATION) / "container1-override", and_file=True)

        # Skip stopping container1 and container2 (by name and id)
        monkeypatch.setenv("ADDITIONAL_FOLDERS", "add1,add2")
        monkeypatch.setenv("ADDITIONAL_FOLDERS_WHEN", "after")

        mock_docker_client.containers.list.return_value = [mock_container1]
        nb = NauticalBackup(mock_docker_client)
        nb.backup()

        assert mock_subprocess_run.call_args_list[0][0][0] == [
            "-raq",
            f"{self.src_location}/container1/",
            f"{self.dest_location}/container1/",
        ]
        assert mock_subprocess_run.call_args_list[1][0][0] == [
            "-raq",
            f"{self.src_location}/add1/",
            f"{self.dest_location}/add1/",
        ]
        assert mock_subprocess_run.call_args_list[2][0][0] == [
            "-raq",
            f"{self.src_location}/add2/",
            f"{self.dest_location}/add2/",
        ]

    @mock.patch("subprocess.run")
    @pytest.mark.parametrize(
        "mock_container1",
        [
            {
                "name": "container1",
                "id": "123456789",
                "labels": {
                    "nautical-backup.additional-folders": "add1",
                    "nautical-backup.additional-folders.when": "after",
                },
            }
        ],
        indirect=True,
    )
    def test_additional_folders_label_after(
        self,
        mock_subprocess_run: MagicMock,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
    ):
        """Test test_additional_folders_label"""

        # Folders must be created before the backup is called
        nautical_env = NauticalEnv()
        create_folder(Path(nautical_env.SOURCE_LOCATION) / "add1", and_file=True)

        mock_docker_client.containers.list.return_value = [mock_container1]
        nb = NauticalBackup(mock_docker_client)
        nb.backup()

        assert mock_subprocess_run.call_count == 2

        # This specifies the order. Additional folders must come after container1
        expected_calls = [
            call(
                [
                    "-raq",
                    f"{self.src_location}/container1/",
                    f"{self.dest_location}/container1/",
                ],
                shell=True,
                executable="/usr/bin/rsync",
                capture_output=False,
            ),
            call(
                [
                    "-raq",
                    f"{self.src_location}/add1/",
                    f"{self.dest_location}/add1/",
                ],
                shell=True,
                executable="/usr/bin/rsync",
                capture_output=False,
            ),
        ]

        mock_subprocess_run.assert_has_calls(expected_calls)

    @mock.patch("subprocess.run")
    @pytest.mark.parametrize(
        "mock_container1",
        [
            {
                "name": "container1",
                "id": "123456789",
                "labels": {
                    "nautical-backup.additional-folders": "add1",
                    "nautical-backup.additional-folders.when": "before",
                },
            }
        ],
        indirect=True,
    )
    def test_additional_folders_label_before(
        self,
        mock_subprocess_run: MagicMock,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
    ):
        """Test test_additional_folders_label"""

        # Folders must be created before the backup is called
        nautical_env = NauticalEnv()
        create_folder(Path(nautical_env.SOURCE_LOCATION) / "add1", and_file=True)

        mock_docker_client.containers.list.return_value = [mock_container1]
        nb = NauticalBackup(mock_docker_client)
        nb.backup()

        assert mock_subprocess_run.call_count == 2

        # This specifies the order. Additional folders must come after container1
        expected_calls = [
            call(
                [
                    "-raq",
                    f"{self.src_location}/add1/",
                    f"{self.dest_location}/add1/",
                ],
                shell=True,
                executable="/usr/bin/rsync",
                capture_output=False,
            ),
            call(
                [
                    "-raq",
                    f"{self.src_location}/container1/",
                    f"{self.dest_location}/container1/",
                ],
                shell=True,
                executable="/usr/bin/rsync",
                capture_output=False,
            ),
        ]

        mock_subprocess_run.assert_has_calls(expected_calls)

    @mock.patch("subprocess.run")
    @pytest.mark.parametrize(
        "mock_container1",
        [
            {
                "name": "container1",
                "id": "123456789",
                "labels": {
                    "nautical-backup.additional-folders": "add1",
                    "nautical-backup.additional-folders.when": "during",
                },
            }
        ],
        indirect=True,
    )
    def test_additional_folders_label_during(
        self,
        mock_subprocess_run: MagicMock,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
    ):
        """Test backing up additional folders 'during' the container backup"""

        # Folders must be created before the backup is called
        nautical_env = NauticalEnv()
        create_folder(Path(nautical_env.SOURCE_LOCATION) / "add1", and_file=True)

        # You can check the order of calls to mockContainer1.stop and subprocess.run
        parent_mock = MagicMock()
        parent_mock.attach_mock(mock_container1.stop, "mockContainer1_stop")
        parent_mock.attach_mock(mock_container1.start, "mockContainer1_start")
        parent_mock.attach_mock(mock_subprocess_run, "mock_subprocess_run")

        mock_docker_client.containers.list.return_value = [mock_container1]
        nb = NauticalBackup(mock_docker_client)
        nb.backup()

        call_names = [c[0] for c in parent_mock.mock_calls]

        # This just checks the order of the calls
        assert call_names == [
            "mockContainer1_stop",
            "mock_subprocess_run",  # Container 1
            "mock_subprocess_run",  # Additional folder
            "mockContainer1_start",
        ]

    @mock.patch("subprocess.run")
    @pytest.mark.parametrize(
        "mock_container1",
        [{"name": "container1", "id": "123456789"}],
        indirect=True,
    )
    def test_pre_and_post_backup_curl_env(
        self,
        mock_subprocess_run: MagicMock,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """Test curl commands set by enviornment variables"""

        monkeypatch.setenv("PRE_BACKUP_CURL", "curl -X GET 'google.com'")
        monkeypatch.setenv("POST_BACKUP_CURL", "curl -X GET 'bing.com'")

        mock_docker_client.containers.list.return_value = [mock_container1]
        nb = NauticalBackup(mock_docker_client)
        nb.backup()

        assert mock_subprocess_run.call_count == 3
        assert mock_subprocess_run.call_args_list[0][0][0] == "curl -X GET 'google.com'"
        assert mock_subprocess_run.call_args_list[1][0][0] == [
            "-raq",
            f"{self.src_location}/container1/",
            f"{self.dest_location}/container1/",
        ]
        assert mock_subprocess_run.call_args_list[2][0][0] == "curl -X GET 'bing.com'"

    @mock.patch("subprocess.run")
    @pytest.mark.parametrize(
        "mock_container1",
        [
            {
                "name": "container1",
                "id": "123456789",
                "labels": {
                    "nautical-backup.curl.before": "curl -X GET 'aol.com'",
                    "nautical-backup.curl.during": "curl -X GET 'msn.com'",
                    "nautical-backup.curl.after": "curl -X GET 'espn.com'",
                },
            }
        ],
        indirect=True,
    )
    def test_curl_label(
        self,
        mock_subprocess_run: MagicMock,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
    ):
        """Test curl commands by labels"""

        mock_docker_client.containers.list.return_value = [mock_container1]
        nb = NauticalBackup(mock_docker_client)
        nb.backup()

        assert mock_subprocess_run.call_count == 4
        assert mock_subprocess_run.call_args_list[0][0][0] == "curl -X GET 'aol.com'"
        assert mock_subprocess_run.call_args_list[1][0][0] == [
            "-raq",
            f"{self.src_location}/container1/",
            f"{self.dest_location}/container1/",
        ]
        assert mock_subprocess_run.call_args_list[2][0][0] == "curl -X GET 'msn.com'"
        assert mock_subprocess_run.call_args_list[3][0][0] == "curl -X GET 'espn.com'"

    @pytest.mark.parametrize(
        "mock_container1",
        [
            {
                "name": "container1",
                "id": "123456789",
                "labels": {
                    "nautical-backup.curl.before": "This will be set later, in the function",
                },
            }
        ],
        indirect=True,
    )
    def test_exec_variables_label(
        self,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
    ):
        """Test curl commands by labels"""
        container_name = "cont1"
        container_id = "9839343"

        # Set mock attributes
        mock_container1.__setattr__("name", container_name)
        mock_container1.__setattr__("id", container_id)
        mock_container1.__setattr__(
            "labels",
            {
                "nautical-backup.curl.before": "echo container_id: $NB_EXEC_CONTAINER_NAME container_id: $NB_EXEC_CONTAINER_ID",
            },
        )

        mock_docker_client.containers.list.return_value = [mock_container1]
        nb = NauticalBackup(mock_docker_client)
        nb.backup()

    @mock.patch("subprocess.run")
    @pytest.mark.parametrize(
        "mock_container1",
        [
            {
                "name": "container1",
                "id": "123456789",
                "labels": {
                    "nautical-backup.lifecycle.before": "echo test1",
                    "nautical-backup.lifecycle.before.timeout": "420s",
                    "nautical-backup.lifecycle.after": "echo test2",
                },
            }
        ],
        indirect=True,
    )
    @pytest.mark.parametrize(
        "mock_container2",
        [
            {
                "name": "container2",
                "id": "101112231415",
                "labels": {
                    "nautical-backup.lifecycle.before": "/bin/sh ./script.sh",
                    "nautical-backup.lifecycle.before.timeout": "0",
                },
            }
        ],
        indirect=True,
    )
    def test_lifecycle_hools(
        self,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
        mock_container2: MagicMock,
    ):
        """Test lifecycle hooks"""

        mock_docker_client.containers.list.return_value = [mock_container1, mock_container2]
        nb = NauticalBackup(mock_docker_client)
        nb.backup()

        exepected1 = [call("timeout 420s echo test1"), call("timeout 60 echo test2")]
        assert mock_container1.exec_run.call_args_list == exepected1

        exepected2 = [call("timeout 0 /bin/sh ./script.sh")]
        assert mock_container2.exec_run.call_args_list == exepected2

    @mock.patch("subprocess.run")
    @pytest.mark.parametrize(
        "mock_container1",
        [
            {
                "name": "container1",
                "id": "123456789",
                "labels": {
                    "nautical-backup.group": "authentic",
                },
            }
        ],
        indirect=True,
    )
    @pytest.mark.parametrize(
        "mock_container2",
        [
            {
                "name": "container2",
                "id": "101112231415",
                "labels": {
                    "nautical-backup.group": "authentic,paperless",
                },
            }
        ],
        indirect=True,
    )
    @pytest.mark.parametrize(
        "mock_container3",
        [
            {
                "name": "container3",
                "id": "09129213232",
                "labels": {
                    "nautical-backup.group": "paperless",
                },
            }
        ],
        indirect=True,
    )
    def test_grouping_with_overlap(
        self,
        mock_subprocess_run: MagicMock,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
        mock_container2: MagicMock,
        mock_container3: MagicMock,
    ):
        """Test groups with overlaps"""

        # You can check the order of calls to mockContainer1.stop and subprocess.run
        parent_mock = MagicMock()
        parent_mock.attach_mock(mock_container1.stop, "mockContainer1_stop")
        parent_mock.attach_mock(mock_container2.stop, "mockContainer2_stop")
        parent_mock.attach_mock(mock_container3.stop, "mockContainer3_stop")

        parent_mock.attach_mock(mock_container1.start, "mockContainer1_start")
        parent_mock.attach_mock(mock_container2.start, "mockContainer2_start")
        parent_mock.attach_mock(mock_container3.start, "mockContainer3_start")

        parent_mock.attach_mock(mock_subprocess_run, "mock_subprocess_run")

        mock_docker_client.containers.list.return_value = [mock_container1, mock_container2, mock_container3]
        nb = NauticalBackup(mock_docker_client)
        nb.backup()

        call_names = [c[0] for c in parent_mock.mock_calls]

        excepted = [
            # Group authentic
            "mockContainer2_stop",
            "mockContainer1_stop",
            "mock_subprocess_run",
            "mock_subprocess_run",
            "mockContainer2_start",
            "mockContainer1_start",
            # Group paperless
            "mockContainer3_stop",
            "mockContainer2_stop",
            "mock_subprocess_run",
            "mock_subprocess_run",
            "mockContainer3_start",
            "mockContainer2_start",
        ]

        assert call_names == excepted

    @mock.patch("subprocess.run")
    @pytest.mark.parametrize(
        "mock_container1",
        [
            {
                "name": "container1",
                "id": "123456789",
                "labels": {
                    "nautical-backup.group": "services",
                },
            }
        ],
        indirect=True,
    )
    @pytest.mark.parametrize(
        "mock_container2",
        [
            {
                "name": "container2",
                "id": "101112231415",
                "labels": {
                    "nautical-backup.group": "services",
                },
            }
        ],
        indirect=True,
    )
    @pytest.mark.parametrize(
        "mock_container3",
        [
            {
                "name": "container3",
                "id": "09129213232",
            }
        ],
        indirect=True,
    )
    def test_grouping(
        self,
        mock_subprocess_run: MagicMock,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
        mock_container2: MagicMock,
        mock_container3: MagicMock,
    ):
        """Test groups"""

        # You can check the order of calls to mockContainer1.stop and subprocess.run
        parent_mock = MagicMock()
        parent_mock.attach_mock(mock_container1.stop, "mockContainer1_stop")
        parent_mock.attach_mock(mock_container2.stop, "mockContainer2_stop")
        parent_mock.attach_mock(mock_container3.stop, "mockContainer3_stop")

        parent_mock.attach_mock(mock_container1.start, "mockContainer1_start")
        parent_mock.attach_mock(mock_container2.start, "mockContainer2_start")
        parent_mock.attach_mock(mock_container3.start, "mockContainer3_start")

        parent_mock.attach_mock(mock_subprocess_run, "mock_subprocess_run")

        mock_docker_client.containers.list.return_value = [mock_container1, mock_container2, mock_container3]
        nb = NauticalBackup(mock_docker_client)
        nb.backup()

        call_names = [c[0] for c in parent_mock.mock_calls]

        assert call_names == [
            "mockContainer2_stop",
            "mockContainer1_stop",
            "mock_subprocess_run",
            "mock_subprocess_run",
            "mockContainer2_start",
            "mockContainer1_start",
            # Group "services"
            "mockContainer3_stop",
            "mock_subprocess_run",
            "mockContainer3_start",
        ]

    @pytest.mark.parametrize(
        "mock_container1",
        [
            {
                "name": "container1",
                "id": "123456789",
                "labels": {
                    "nautical-backup.group": "authentic",
                },
            }
        ],
        indirect=True,
    )
    @pytest.mark.parametrize(
        "mock_container2",
        [
            {
                "name": "container2",
                "id": "101112231415",
                "labels": {
                    "nautical-backup.group": "authentic,paperless",
                },
            }
        ],
        indirect=True,
    )
    @pytest.mark.parametrize(
        "mock_container3",
        [
            {
                "name": "container3",
                "id": "09129213232",
                "labels": {
                    "nautical-backup.group": "paperless",
                },
            }
        ],
        indirect=True,
    )
    def test_grouping_function(
        self,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
        mock_container2: MagicMock,
        mock_container3: MagicMock,
    ):
        """Test container group function"""
        mock_docker_client.containers.list.return_value = [mock_container1, mock_container2, mock_container3]
        nb = NauticalBackup(mock_docker_client)
        groups = nb.group_containers()

        assert groups["authentic"] == [mock_container2, mock_container1]
        assert groups["paperless"] == [mock_container3, mock_container2]

    @pytest.mark.parametrize(
        "mock_container1",
        [
            {
                "name": "container1",
                "id": "123456789",
                "labels": {
                    "nautical-backup.group": "authentic",
                    "nautical-backup.group.authentic.priority": "90",
                },
            }
        ],
        indirect=True,
    )
    @pytest.mark.parametrize(
        "mock_container2",
        [
            {
                "name": "container2",
                "id": "101112231415",
                "labels": {
                    "nautical-backup.group": "authentic,paperless",
                    "nautical-backup.group.authentic.priority": "101",
                    "nautical-backup.group.paperless.priority": "105",
                },
            }
        ],
        indirect=True,
    )
    @pytest.mark.parametrize(
        "mock_container3",
        [
            {
                "name": "container3",
                "id": "09129213232",
                "labels": {
                    "nautical-backup.group": "paperless",
                },
            }
        ],
        indirect=True,
    )
    @pytest.mark.parametrize(
        "mock_container4",
        [
            {
                "name": "container4",
                "id": "9038383223",
                "labels": {
                    "nautical-backup.group": "authentic,paperless",
                    "nautical-backup.group.authentic.priority": "103",
                    "nautical-backup.group.paperless.priority": "80",
                },
            }
        ],
        indirect=True,
    )
    def test_grouping_function_with_priority(
        self,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
        mock_container2: MagicMock,
        mock_container3: MagicMock,
        mock_container4: MagicMock,
    ):
        """Test container group function with priority"""
        mock_docker_client.containers.list.return_value = [
            mock_container1,
            mock_container2,
            mock_container3,
            mock_container4,
        ]
        nb = NauticalBackup(mock_docker_client)
        groups = nb.group_containers()

        # Priority                           103            101              90
        assert groups["authentic"] == [mock_container4, mock_container2, mock_container1]
        # Priority                           105            100             80
        assert groups["paperless"] == [mock_container2, mock_container3, mock_container4]

    def test_exception_on_no_src_dir(
        self,
        mock_docker_client: MagicMock,
    ):
        """Assert exception is raised on no source directory"""

        # Folders must be created before the backup is called
        nautical_env = NauticalEnv()
        rm_tree(Path(nautical_env.SOURCE_LOCATION))

        with pytest.raises(FileNotFoundError) as err:
            nb = NauticalBackup(mock_docker_client)

        assert "Source directory" in str(err.value)

    @pytest.mark.parametrize("mock_container1", [{"name": "container1", "id": "123456789"}], indirect=True)
    def test_exception_on_no_dest_dir(
        self,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
    ):
        """Assert exception is raised on no dest directory"""

        # Folders must be created before the backup is called
        nautical_env = NauticalEnv()
        rm_tree(Path(nautical_env.DEST_LOCATION))

        with pytest.raises(FileNotFoundError) as err:
            nb = NauticalBackup(mock_docker_client)

        assert "Destination directory" in str(err.value)

    @mock.patch("os.access", side_effect=[False, True, True])
    @pytest.mark.parametrize("mock_container1", [{"name": "container1", "id": "123456789"}], indirect=True)
    def test_exception_on_no_access_to_src_dir(
        self,
        mock_os_access: MagicMock,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
    ):
        """Assert exception is raised on no dest directory"""

        # Folders must be created before the backup is called
        nautical_env = NauticalEnv()

        with pytest.raises(PermissionError) as err:
            nb = NauticalBackup(mock_docker_client)

        assert "No read access to source directory" in str(err.value)

    @mock.patch("os.access", side_effect=[True, False, True])
    @pytest.mark.parametrize("mock_container1", [{"name": "container1", "id": "123456789"}], indirect=True)
    def test_exception_on_no_read_access_to_dest_dir(
        self,
        mock_os_access: MagicMock,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
    ):
        """Assert exception is raised on no dest directory"""

        # Folders must be created before the backup is called
        nautical_env = NauticalEnv()

        with pytest.raises(PermissionError) as err:
            nb = NauticalBackup(mock_docker_client)

        assert "No read access to destination directory" in str(err.value)

    @mock.patch("os.access", side_effect=[True, True, False])
    @pytest.mark.parametrize("mock_container1", [{"name": "container1", "id": "123456789"}], indirect=True)
    def test_exception_on_no_write_access_to_dest_dir(
        self,
        mock_os_access: MagicMock,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
    ):
        """Assert exception is raised on no dest directory"""

        # Folders must be created before the backup is called
        nautical_env = NauticalEnv()

        with pytest.raises(PermissionError) as err:
            nb = NauticalBackup(mock_docker_client)

        assert "No write access to destination directory" in str(err.value)
