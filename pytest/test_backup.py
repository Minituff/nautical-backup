import os
import time
import pytest
from pathlib import Path
from mock import PropertyMock, mock, MagicMock, patch
from pathlib import Path
import docker
from docker.models.containers import Container
from itertools import cycle
import shlex
from mock import call
from requests.exceptions import ReadTimeout

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

    if not pth.is_dir():
        raise Exception(f"Failed to create folder: {pth}")
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
            f"/usr/bin/rsync -raq  {self.src_location}/container1/ {self.dest_location}/container1/",
            shell=True,
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
            f"/usr/bin/rsync -raq  {self.src_location}/container1-override/ {self.dest_location}/container1-override/",
            shell=True,
            capture_output=False,
        )
        mock_subprocess_run.assert_any_call(
            f"/usr/bin/rsync -raq  {self.src_location}/container2-new/ {self.dest_location}/container2-new/",
            shell=True,
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
            f"/usr/bin/rsync -raq  {self.src_location}/container1-override-label/ {self.dest_location}/container1-override-label/",
            shell=True,
            capture_output=False,
        )

    @mock.patch("subprocess.run")
    @pytest.mark.parametrize(
        "mock_container1",
        [
            {
                "name": "container1",
                "id": "123456789",
                "labels": {"nautical-backup.override-source-dir": "parent/child"},
            }
        ],
        indirect=True,
    )
    def test_override_src_label_subpath(
        self,
        mock_subprocess_run: MagicMock,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
    ):
        """Test that override-source-dir with a subpath creates the full destination tree"""

        nautical_env = NauticalEnv()
        create_folder(Path(nautical_env.SOURCE_LOCATION) / "parent" / "child", and_file=True)

        # Intentionally do NOT pre-create destination/parent/ — this is the bug scenario
        dest_subdir = Path(nautical_env.DEST_LOCATION) / "parent" / "child"
        rm_tree(dest_subdir.parent)

        mock_subprocess_run.return_value.returncode = 0

        mock_docker_client.containers.list.return_value = [mock_container1]
        nb = NauticalBackup(mock_docker_client)
        nb.backup()

        # Destination tree should have been created by the backup code
        assert dest_subdir.exists(), f"Expected dest tree '{dest_subdir}' to be created before rsync"

        mock_subprocess_run.assert_any_call(
            f"/usr/bin/rsync -raq  {self.src_location}/parent/child/ {self.dest_location}/parent/child/",
            shell=True,
            capture_output=False,
        )

        # Container should be in completed, not skipped
        assert "container1" in nb.containers_completed
        assert "container1" not in nb.containers_skipped

    @mock.patch("subprocess.run")
    @pytest.mark.parametrize(
        "mock_container1",
        [
            {
                "name": "container1",
                "id": "123456789",
                "labels": {"nautical-backup.override-source-dir": "folder_one,folder_two"},
                "source_exists": False,  # disable auto-create for container1 name
            }
        ],
        indirect=True,
    )
    def test_override_src_label_multiple(
        self,
        mock_subprocess_run: MagicMock,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
    ):
        """Comma-separated override-source-dir label backs up each folder separately"""

        mock_subprocess_run.return_value.returncode = 0
        nautical_env = NauticalEnv()
        create_folder(Path(nautical_env.SOURCE_LOCATION) / "folder_one", and_file=True)
        create_folder(Path(nautical_env.SOURCE_LOCATION) / "folder_two", and_file=True)

        mock_docker_client.containers.list.return_value = [mock_container1]
        nb = NauticalBackup(mock_docker_client)
        nb.backup()

        # rsync should be called once per source folder
        assert mock_subprocess_run.call_count == 2
        mock_subprocess_run.assert_any_call(
            f"/usr/bin/rsync -raq  {self.src_location}/folder_one/ {self.dest_location}/folder_one/",
            shell=True,
            capture_output=False,
        )
        mock_subprocess_run.assert_any_call(
            f"/usr/bin/rsync -raq  {self.src_location}/folder_two/ {self.dest_location}/folder_two/",
            shell=True,
            capture_output=False,
        )

    @mock.patch("subprocess.run")
    @pytest.mark.parametrize(
        "mock_container1",
        [
            {
                "name": "container1",
                "id": "123456789",
                "labels": {"nautical-backup.override-source-dir": "exists_folder,missing_folder"},
                "source_exists": False,
            }
        ],
        indirect=True,
    )
    def test_override_src_label_multiple_one_missing(
        self,
        mock_subprocess_run: MagicMock,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
    ):
        """When one of the comma-separated source dirs is missing, only the existing one is backed up"""

        mock_subprocess_run.return_value.returncode = 0
        nautical_env = NauticalEnv()
        create_folder(Path(nautical_env.SOURCE_LOCATION) / "exists_folder", and_file=True)
        rm_tree(Path(nautical_env.SOURCE_LOCATION) / "missing_folder")

        mock_docker_client.containers.list.return_value = [mock_container1]
        nb = NauticalBackup(mock_docker_client)
        nb.backup()

        # Only one rsync call for the folder that exists
        assert mock_subprocess_run.call_count == 1
        mock_subprocess_run.assert_any_call(
            f"/usr/bin/rsync -raq  {self.src_location}/exists_folder/ {self.dest_location}/exists_folder/",
            shell=True,
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
            f"/usr/bin/rsync -raq  {self.src_location}/container1/ {self.dest_location}/container1-override/",
            shell=True,
            capture_output=False,
        )
        mock_subprocess_run.assert_any_call(
            f"/usr/bin/rsync -raq  {self.src_location}/container2/ {self.dest_location}/container2-new/",
            shell=True,
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
            f"/usr/bin/rsync -raq  {self.src_location}/container1/ {self.dest_location}/container1-override-label/",
            shell=True,
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
            f"/usr/bin/rsync  -aq {self.src_location}/container1/ {self.dest_location}/container1/",
            shell=True,
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
            f"/usr/bin/rsync  -aq {self.src_location}/container1/ {self.dest_location}/container1/",
            shell=True,
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

        assert (
            mock_subprocess_run.call_args_list[0][0][0]
            == f"/usr/bin/rsync  --exclude=AsdF {self.src_location}/container1/ {self.dest_location}/container1/"
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
            f"/usr/bin/rsync  -aq {self.src_location}/container1/ {self.dest_location}/container1/",
            shell=True,
            capture_output=False,
        )

        # Container 2 will use env custom rsync args
        mock_subprocess_run.assert_any_call(
            f"/usr/bin/rsync  -something {self.src_location}/container2/ {self.dest_location}/container2/",
            shell=True,
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
            f"/usr/bin/rsync -raq  {self.src_location}/pialert/ {self.dest_location}/Pi.Alert/",
            shell=True,
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
            f"/usr/bin/rsync -raq  {self.src_location}/container1-override/ {self.dest_location}/container1-override/",
            shell=True,
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
            f"/usr/bin/rsync -raq  {self.src_location}/container1-new/ {self.dest_location}/container1/",
            shell=True,
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
            f"/usr/bin/rsync -raq  {self.src_location}/container1-new/ {self.dest_location}/container1-new/",
            shell=True,
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
        dest_name, dest_dir_no_path = nb._get_dest_dir(mock_container1, "container1")

        assert str(dest_name) == f"{self.dest_location}/container1"
        assert str(dest_dir_no_path) == f"container1"

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
        dest_name, dest_name_no_path = nb._get_dest_dir(mock_container1, "container1")

        assert str(dest_name) == f"{self.dest_location}/{time_format}/container1"
        assert str(dest_name_no_path) == f"{time_format}/container1"

        monkeypatch.setenv("USE_DEST_DATE_FOLDER", "false")
        nb = NauticalBackup(mock_docker_client)
        dest_name, dest_name_no_path = nb._get_dest_dir(mock_container1, "container1")
        assert str(dest_name) == f"{self.dest_location}/container1"
        assert str(dest_name_no_path) == "container1"

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
        dest_name, dest_dir_no_path = nb._get_dest_dir(mock_container1, "container1")

        assert str(dest_name) == f"{self.dest_location}/{time_format}/container1"
        assert str(dest_dir_no_path) == f"{time_format}/container1"

        monkeypatch.setenv("DEST_DATE_PATH_FORMAT", "container/date")
        nb = NauticalBackup(mock_docker_client)
        dest_name, dest_dir_no_path = nb._get_dest_dir(mock_container1, "container1")

        assert str(dest_name) == f"{self.dest_location}/container1/{time_format}"
        assert str(dest_dir_no_path) == f"container1/{time_format}"

        monkeypatch.setenv("DEST_DATE_PATH_FORMAT", "")
        nb = NauticalBackup(mock_docker_client)
        dest_name, dest_dir_no_path = nb._get_dest_dir(mock_container1, "container1")

        assert str(dest_name) == f"{self.dest_location}/{time_format}/container1"
        assert str(dest_dir_no_path) == f"{time_format}/container1"

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
        dest_name, dest_dir_no_path = nb._get_dest_dir(mock_container1, "container1")

        assert str(dest_name) == f"{self.dest_location}/{time_format}/container1"
        assert str(dest_dir_no_path) == f"{time_format}/container1"

        time_format_str = "%b %d %Y %H:%M:%S"
        time_format = time.strftime(time_format_str)
        monkeypatch.setenv("DEST_DATE_FORMAT", time_format_str)

        nb = NauticalBackup(mock_docker_client)
        dest_name, dest_dir_no_path = nb._get_dest_dir(mock_container1, "container1")
        assert str(dest_name) == f"{self.dest_location}/{time_format}/container1"
        assert str(dest_dir_no_path) == f"{time_format}/container1"

        time_format_str = "Prefix %D %T Suffix"
        time_format = time.strftime(time_format_str)
        monkeypatch.setenv("DEST_DATE_FORMAT", time_format_str)

        nb = NauticalBackup(mock_docker_client)
        dest_name, dest_dir_no_path = nb._get_dest_dir(mock_container1, "container1")
        assert str(dest_name) == f"{self.dest_location}/{time_format}/container1"
        assert str(dest_dir_no_path) == f"{time_format}/container1"

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
        dest_name, dest_dir_no_path = nb._get_dest_dir(mock_container1, src_name)

        assert str(src_pth) == f"{self.src_location}/ctr1-src"
        assert str(dest_name) == f"{self.dest_location}/{time_format}/ctr1-dest"
        assert str(dest_dir_no_path) == f"{time_format}/ctr1-dest"

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
        dest_name, dest_dir_no_path = nb._get_dest_dir(mock_container1, src_name)

        assert str(src_pth) == f"{self.src_location}/ctr1-src"
        assert str(dest_name) == f"{self.dest_location}/ctr1-dest/{time_format}"
        assert str(dest_dir_no_path) == f"ctr1-dest/{time_format}"

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

        # Check the full command for the additional folder
        assert (
            mock_subprocess_run.call_args_list[1][0][0]
            == f"/usr/bin/rsync -raq  {self.src_location}/add1/ {self.dest_location}/{time_format}/add1/"
        )

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

        # Check the full command for the additional folder
        assert (
            mock_subprocess_run.call_args_list[1][0][0]
            == f"/usr/bin/rsync -raq  {self.src_location}/add1/ {self.dest_location}/{time_format}/add1/"
        )

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
    def test_additional_folders_and_USE_DEST_DATE_FOLDER_and_DEST_DATE_FORMAT_and_SECONDARY_LOCATION(
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
        create_folder(Path(nautical_env.DEST_LOCATION) / "backup", and_file=True)

        time_format = time.strftime("%Y-%m-%d")
        time_format_str = "%D_%d"
        time_format = time.strftime(time_format_str)
        monkeypatch.setenv("DEST_DATE_FORMAT", rf"{time_format_str}")
        monkeypatch.setenv("USE_DEST_DATE_FOLDER", "true")

        # The enviorment variable must be a string
        monkeypatch.setenv("SECONDARY_DEST_DIRS", nautical_env.DEST_LOCATION + "/backup")

        mock_docker_client.containers.list.return_value = [mock_container1]
        nb = NauticalBackup(mock_docker_client)
        nb.backup()

        assert mock_subprocess_run.call_count == 4

        # Check the full commands for secondary destination backups
        assert (
            mock_subprocess_run.call_args_list[2][0][0]
            == f"/usr/bin/rsync -raq  {self.src_location}/container1/ {self.dest_location}/backup/{time_format}/container1/"
        )
        assert (
            mock_subprocess_run.call_args_list[3][0][0]
            == f"/usr/bin/rsync -raq  {self.src_location}/add1/ {self.dest_location}/backup/{time_format}/add1/"
        )

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
        args = shlex.split(mock_subprocess_run.call_args_list[1][0][0])

        # Src location
        assert args[2] == f"{self.src_location}/add1/"

        # Dest location
        assert args[3] == f"{self.dest_location}/add1/{time_format}/"

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

        mock_subprocess_run.assert_any_call(
            f"/usr/bin/rsync -raq  {self.src_location}/container1/ {self.dest_location}/{time_format}/container1/",
            shell=True,
            capture_output=False,
        )
        rm_tree(Path(self.dest_location) / time_format / "container1")

    @mock.patch("subprocess.run")
    @pytest.mark.parametrize("mock_container1", [{"name": "container1", "id": "123456789"}], indirect=True)
    def test_additional_folders_and_DEST_DATE_PATH_FORMAT2(
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
        monkeypatch.setenv("ADDITIONAL_FOLDERS_USE_DEST_DATE_FOLDER", "true")

        mock_docker_client.containers.list.return_value = [mock_container1]
        nb = NauticalBackup(mock_docker_client)
        nb.backup()

        time_format = time.strftime("%Y-%m-%d")

        # Additional folder 1
        assert (
            mock_subprocess_run.call_args_list[0][0][0]
            == f"/usr/bin/rsync -raq  {self.src_location}/add1/ {self.dest_location}/{time_format}/add1/"
        )

        # Additional folder 2
        assert (
            mock_subprocess_run.call_args_list[1][0][0]
            == f"/usr/bin/rsync -raq  {self.src_location}/add2/ {self.dest_location}/{time_format}/add2/"
        )

        # Container
        assert (
            mock_subprocess_run.call_args_list[2][0][0]
            == f"/usr/bin/rsync -raq  {self.src_location}/container1/ {self.dest_location}/container1/"
        )

    @mock.patch("subprocess.run")
    @pytest.mark.parametrize(
        "mock_container1",
        [
            {
                "name": "container1",
                "id": "123456789",
                "labels": {"nautical-backup.override-source-dir": "container1-override"},
            }
        ],
        indirect=True,
    )
    def test_override_src_label_and_USE_DEST_DATE_FOLDER(
        self,
        mock_subprocess_run: MagicMock,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """Test override source dir with USE_DEST_DATE_FOLDER"""

        # Folders must be created before the backup is called
        nautical_env = NauticalEnv()
        create_folder(Path(nautical_env.SOURCE_LOCATION) / "container1-override", and_file=True)

        monkeypatch.setenv("USE_DEST_DATE_FOLDER", "true")

        mock_docker_client.containers.list.return_value = [mock_container1]
        nb = NauticalBackup(mock_docker_client)
        nb.backup()

        time_format = time.strftime("%Y-%m-%d")

        # Additional folder 1
        assert (
            mock_subprocess_run.call_args_list[0][0][0]
            == f"/usr/bin/rsync -raq  {self.src_location}/container1-override/ {self.dest_location}/{time_format}/container1-override/"
        )

        rm_tree(Path(self.src_location) / "container1-override")
        rm_tree(Path(self.dest_location) / time_format / "container1-override")

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

        assert (
            mock_subprocess_run.call_args_list[0][0][0]
            == f"/usr/bin/rsync -raq  {self.src_location}/add1/ {self.dest_location}/add1/"
        )
        assert (
            mock_subprocess_run.call_args_list[1][0][0]
            == f"/usr/bin/rsync -raq  {self.src_location}/add2/ {self.dest_location}/add2/"
        )
        assert (
            mock_subprocess_run.call_args_list[2][0][0]
            == f"/usr/bin/rsync -raq  {self.src_location}/container1/ {self.dest_location}/container1/"
        )

    @mock.patch("subprocess.run")
    @pytest.mark.parametrize("mock_container1", [{"name": "container1", "id": "123456789"}], indirect=True)
    def test_secondary_dest_dir_env_before(
        self,
        mock_subprocess_run: MagicMock,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """Test secondary dest dir env before"""

        # Folders must be created before the backup is called
        nautical_env = NauticalEnv()
        create_folder(Path(nautical_env.SOURCE_LOCATION) / "add1", and_file=True)
        create_folder(Path(nautical_env.DEST_LOCATION) / "backup", and_file=True)
        create_folder(Path(nautical_env.DEST_LOCATION) / "backup2", and_file=True)

        monkeypatch.setenv("ADDITIONAL_FOLDERS", "add1")
        monkeypatch.setenv("ADDITIONAL_FOLDERS_WHEN", "before")
        # The enviorment variable must be a string
        monkeypatch.setenv(
            "SECONDARY_DEST_DIRS",
            nautical_env.DEST_LOCATION + "/backup" + "," + nautical_env.DEST_LOCATION + "/backup2",
        )

        mock_docker_client.containers.list.return_value = [mock_container1]
        nb = NauticalBackup(mock_docker_client)
        nb.backup()

        # 1st call is for additional folder to dest dir
        # 2nd call is for additional folder to secondary dest dir #1
        # 3th call is for additional folder to secondary dest dir #2
        # 4th call is for container1 to dest dir
        # 5th call is for container1 to secondary dest dir #1
        # 6th call is for container1 to secondary dest dir #2
        assert mock_subprocess_run.call_count == 6

        assert (
            mock_subprocess_run.call_args_list[1][0][0]
            == f"/usr/bin/rsync -raq  {self.src_location}/add1/ {self.dest_location}/backup/add1/"
        )
        assert (
            mock_subprocess_run.call_args_list[2][0][0]
            == f"/usr/bin/rsync -raq  {self.src_location}/add1/ {self.dest_location}/backup2/add1/"
        )

        # 3rd call is for container1 to dest dir (tested elsewhere)

        assert (
            mock_subprocess_run.call_args_list[4][0][0]
            == f"/usr/bin/rsync -raq  {self.src_location}/container1/ {self.dest_location}/backup/container1/"
        )
        assert (
            mock_subprocess_run.call_args_list[5][0][0]
            == f"/usr/bin/rsync -raq  {self.src_location}/container1/ {self.dest_location}/backup2/container1/"
        )

    @mock.patch("subprocess.run")
    @pytest.mark.parametrize("mock_container1", [{"name": "container1", "id": "123456789"}], indirect=True)
    def test_secondary_dest_dir_env_after(
        self,
        mock_subprocess_run: MagicMock,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """Test secondary dest dir env after"""

        # Folders must be created before the backup is called
        nautical_env = NauticalEnv()
        create_folder(Path(nautical_env.SOURCE_LOCATION) / "add1", and_file=True)
        create_folder(Path(nautical_env.DEST_LOCATION) / "backup", and_file=True)
        create_folder(Path(nautical_env.DEST_LOCATION) / "backup2", and_file=True)

        monkeypatch.setenv("ADDITIONAL_FOLDERS", "add1")
        monkeypatch.setenv("ADDITIONAL_FOLDERS_WHEN", "after")
        # The enviorment variable must be a string
        monkeypatch.setenv(
            "SECONDARY_DEST_DIRS",
            nautical_env.DEST_LOCATION + "/backup" + "," + nautical_env.DEST_LOCATION + "/backup2",
        )

        mock_docker_client.containers.list.return_value = [mock_container1]
        nb = NauticalBackup(mock_docker_client)
        nb.backup()

        # Call 1 is for container1 to dest dir
        # Call 2 is for container1 to secondary dest dir #1
        # Call 3 is for container1 to secondary dest dir #2
        # Call 4 is for additional folder to dest dir
        # Call 5 is for additional folder to secondary dest dir #1
        # Call 6 is for additional folder to secondary dest dir #2
        assert mock_subprocess_run.call_count == 6

        # 1st call is for container1 to dest dir (tested elsewhere)

        assert (
            mock_subprocess_run.call_args_list[1][0][0]
            == f"/usr/bin/rsync -raq  {self.src_location}/container1/ {self.dest_location}/backup/container1/"
        )
        assert (
            mock_subprocess_run.call_args_list[2][0][0]
            == f"/usr/bin/rsync -raq  {self.src_location}/container1/ {self.dest_location}/backup2/container1/"
        )
        assert (
            mock_subprocess_run.call_args_list[3][0][0]
            == f"/usr/bin/rsync -raq  {self.src_location}/add1/ {self.dest_location}/add1/"
        )
        assert (
            mock_subprocess_run.call_args_list[4][0][0]
            == f"/usr/bin/rsync -raq  {self.src_location}/add1/ {self.dest_location}/backup/add1/"
        )
        assert (
            mock_subprocess_run.call_args_list[5][0][0]
            == f"/usr/bin/rsync -raq  {self.src_location}/add1/ {self.dest_location}/backup2/add1/"
        )

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

        assert (
            mock_subprocess_run.call_args_list[0][0][0]
            == f"/usr/bin/rsync -raq  {self.src_location}/container1/ {self.dest_location}/container1/"
        )
        assert (
            mock_subprocess_run.call_args_list[1][0][0]
            == f"/usr/bin/rsync -raq  {self.src_location}/add1/ {self.dest_location}/add1/"
        )
        assert (
            mock_subprocess_run.call_args_list[2][0][0]
            == f"/usr/bin/rsync -raq  {self.src_location}/add2/ {self.dest_location}/add2/"
        )

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

        mock_subprocess_run.return_value.returncode = 0
        mock_docker_client.containers.list.return_value = [mock_container1]
        nb = NauticalBackup(mock_docker_client)
        nb.backup()

        assert mock_subprocess_run.call_count == 2

        # This specifies the order. Additional folders must come after container1
        expected_calls = [
            call(
                f"/usr/bin/rsync -raq  {self.src_location}/container1/ {self.dest_location}/container1/",
                shell=True,
                capture_output=False,
            ),
            call(
                f"/usr/bin/rsync -raq  {self.src_location}/add1/ {self.dest_location}/add1/",
                shell=True,
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

        mock_subprocess_run.return_value.returncode = 0
        mock_docker_client.containers.list.return_value = [mock_container1]
        nb = NauticalBackup(mock_docker_client)
        nb.backup()

        assert mock_subprocess_run.call_count == 2

        # This specifies the order. Additional folders must come after container1
        expected_calls = [
            call(
                f"/usr/bin/rsync -raq  {self.src_location}/add1/ {self.dest_location}/add1/",
                shell=True,
                capture_output=False,
            ),
            call(
                f"/usr/bin/rsync -raq  {self.src_location}/container1/ {self.dest_location}/container1/",
                shell=True,
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

        mock_subprocess_run.return_value.returncode = 0
        mock_docker_client.containers.list.return_value = [mock_container1]
        nb = NauticalBackup(mock_docker_client)
        nb.backup()

        call_names = [c[0] for c in parent_mock.mock_calls]

        print(call_names)

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
        assert (
            mock_subprocess_run.call_args_list[1][0][0]
            == f"/usr/bin/rsync -raq  {self.src_location}/container1/ {self.dest_location}/container1/"
        )
        assert mock_subprocess_run.call_args_list[2][0][0] == "curl -X GET 'bing.com'"

    @mock.patch("subprocess.run")
    @pytest.mark.parametrize(
        "mock_container1",
        [{"name": "container1", "id": "123456789"}],
        indirect=True,
    )
    def test_pre_and_post_backup_exec_env(
        self,
        mock_subprocess_run: MagicMock,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """Test exec commands set by enviornment variables"""

        monkeypatch.setenv("PRE_BACKUP_EXEC", "curl -X GET 'google.com'")
        monkeypatch.setenv("POST_BACKUP_EXEC", "curl -X GET 'bing.com'")

        mock_docker_client.containers.list.return_value = [mock_container1]
        nb = NauticalBackup(mock_docker_client)
        nb.backup()

        assert mock_subprocess_run.call_count == 3
        assert mock_subprocess_run.call_args_list[0][0][0] == "curl -X GET 'google.com'"
        assert (
            mock_subprocess_run.call_args_list[1][0][0]
            == f"/usr/bin/rsync -raq  {self.src_location}/container1/ {self.dest_location}/container1/"
        )
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
        assert (
            mock_subprocess_run.call_args_list[1][0][0]
            == f"/usr/bin/rsync -raq  {self.src_location}/container1/ {self.dest_location}/container1/"
        )
        assert mock_subprocess_run.call_args_list[2][0][0] == "curl -X GET 'msn.com'"
        assert mock_subprocess_run.call_args_list[3][0][0] == "curl -X GET 'espn.com'"

    @mock.patch("subprocess.run")
    @pytest.mark.parametrize(
        "mock_container1",
        [
            {
                "name": "container1",
                "id": "123456789",
                "labels": {
                    "nautical-backup.exec.before": "curl -X GET 'aol.com'",
                    "nautical-backup.exec.during": "curl -X GET 'msn.com'",
                    "nautical-backup.exec.after": "curl -X GET 'espn.com'",
                },
            }
        ],
        indirect=True,
    )
    def test_exec_label(
        self,
        mock_subprocess_run: MagicMock,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
    ):
        """Test exec commands by labels"""

        mock_docker_client.containers.list.return_value = [mock_container1]
        nb = NauticalBackup(mock_docker_client)
        nb.backup()

        assert mock_subprocess_run.call_count == 4
        assert mock_subprocess_run.call_args_list[0][0][0] == "curl -X GET 'aol.com'"
        assert (
            mock_subprocess_run.call_args_list[1][0][0]
            == f"/usr/bin/rsync -raq  {self.src_location}/container1/ {self.dest_location}/container1/"
        )
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
    @patch("codecs.decode")
    def test_exec_variables_label(
        self,
        mock_decode: MagicMock,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
    ):
        """Test exec variables labels"""
        nautical_env = NauticalEnv()

        container_name = "cont1"
        container_id = "9839343"

        create_folder(Path(nautical_env.SOURCE_LOCATION) / container_name, and_file=True)
        create_folder(Path(nautical_env.DEST_LOCATION) / container_name, and_file=True)

        label = "echo"
        label += " exec_commmand: $NB_EXEC_COMMAND"
        label += " container_name: $NB_EXEC_CONTAINER_NAME"
        label += " container_id: $NB_EXEC_CONTAINER_ID"
        label += " attached_to_container: $NB_EXEC_ATTACHED_TO_CONTAINER"
        label += " before_during_or_after: $NB_EXEC_BEFORE_DURING_OR_AFTER"

        # Set mock attributes
        mock_container1.__setattr__("name", container_name)
        mock_container1.__setattr__("id", container_id)
        mock_container1.__setattr__("labels", {"nautical-backup.exec.before": label})

        mock_docker_client.containers.list.return_value = [mock_container1]
        nb = NauticalBackup(mock_docker_client)
        nb.backup()

        decoded = str(mock_decode.call_args_list[0][0][0], encoding="utf-8").strip()

        # Assert all variables are set and accessible
        assert f"container_name: {container_name}" in decoded
        assert f"container_id: {container_id}" in decoded
        assert f"attached_to_container: True" in decoded
        assert f"before_during_or_after: BEFORE" in decoded

    @mock.patch("subprocess.run")
    @pytest.mark.parametrize(
        "mock_container1",
        [{"name": "container1", "id": "123456789"}],
        indirect=True,
    )
    def test_exec_total_variables(
        self,
        mock_subprocess_run: MagicMock,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """Test that global POST_BACKUP_EXEC sets NB_EXEC_TOTAL_* env vars correctly.
        These vars are only populated for the global after-exec (attached_to_container=False),
        not for per-container exec labels.
        """
        monkeypatch.setenv("POST_BACKUP_EXEC", "echo test")
        mock_subprocess_run.return_value.returncode = 0

        mock_docker_client.containers.list.return_value = [mock_container1]
        nb = NauticalBackup(mock_docker_client)
        nb.backup()

        import os

        assert os.environ.get("NB_EXEC_TOTAL_CONTAINERS_COMPLETED") == "1"
        assert os.environ.get("NB_EXEC_TOTAL_CONTAINERS_SKIPPED") == "0"
        assert os.environ.get("NB_EXEC_TOTAL_NUMBER_OF_CONTAINERS") == "1"
        assert os.environ.get("NB_EXEC_BACKUP_STATUS") == "success"
        assert os.environ.get("NB_EXEC_CONTAINERS_COMPLETED") == "container1"
        assert os.environ.get("NB_EXEC_CONTAINERS_SKIPPED") == ""
        assert os.environ.get("NB_EXEC_CONTAINERS_FAILED") == ""
        assert os.environ.get("NB_EXEC_CONTAINER_SKIP_REASONS") == ""
        assert os.environ.get("NB_EXEC_CONTAINER_FAILURE_REASONS") == ""
        assert os.environ.get("NB_EXEC_ERROR_MESSAGES") == ""
        assert os.environ.get("NB_EXEC_BACKUP_STARTED_AT") != ""
        assert os.environ.get("NB_EXEC_BACKUP_FINISHED_AT") != ""
        assert os.environ.get("NB_EXEC_BACKUP_DURATION_SECONDS") != ""

    @mock.patch("builtins.print")
    @mock.patch("subprocess.run")
    @pytest.mark.parametrize("mock_container1", [{"name": "container1", "id": "123456789"}], indirect=True)
    @pytest.mark.parametrize("mock_container2", [{"name": "container2", "id": "9876543210"}], indirect=True)
    def test_post_backup_exec_variables_for_configured_skips(
        self,
        mock_subprocess_run: MagicMock,
        mock_print: MagicMock,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
        mock_container2: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """Test configured skips are warnings and available to POST_BACKUP_EXEC."""

        monkeypatch.setenv("SKIP_CONTAINERS", "container1")
        monkeypatch.setenv("POST_BACKUP_EXEC", "echo test")
        mock_subprocess_run.return_value.returncode = 0

        mock_docker_client.containers.list.return_value = [mock_container1, mock_container2]
        nb = NauticalBackup(mock_docker_client)
        nb.backup()

        printed = [call_args[0][0] for call_args in mock_print.call_args_list]

        assert "WARN: Skipping container1 based on name" in printed
        assert "WARN: Skipped 1 containers: container1" in printed
        assert os.environ.get("NB_EXEC_BACKUP_STATUS") == "warning"
        assert os.environ.get("NB_EXEC_TOTAL_CONTAINERS_COMPLETED") == "1"
        assert os.environ.get("NB_EXEC_TOTAL_CONTAINERS_SKIPPED") == "1"
        assert os.environ.get("NB_EXEC_TOTAL_ERRORS") == "0"
        assert os.environ.get("NB_EXEC_CONTAINERS_COMPLETED") == "container2"
        assert os.environ.get("NB_EXEC_CONTAINERS_SKIPPED") == "container1"
        assert os.environ.get("NB_EXEC_CONTAINERS_FAILED") == ""
        assert os.environ.get("NB_EXEC_CONTAINER_SKIP_REASONS") == "container1=skip_containers_name"

    @mock.patch("builtins.print")
    @mock.patch("subprocess.run")
    @pytest.mark.parametrize(
        "mock_container1",
        [
            {
                "name": "container1",
                "id": "123456789",
                "source_exists": False,
                "status_side_effect": ["running", "running", "running", "running", "running"],
            }
        ],
        indirect=True,
    )
    def test_post_backup_exec_variables_for_missing_source_skip(
        self,
        mock_subprocess_run: MagicMock,
        mock_print: MagicMock,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """Test missing required source directory is a warning and script-visible skip."""

        monkeypatch.setenv("POST_BACKUP_EXEC", "echo test")
        mock_subprocess_run.return_value.returncode = 0

        mock_docker_client.containers.list.return_value = [mock_container1]
        nb = NauticalBackup(mock_docker_client)
        nb.backup()

        printed = [call_args[0][0] for call_args in mock_print.call_args_list]

        assert any(
            line.startswith("WARN: container1 - Source directory") and line.endswith("does not exist. Skipping")
            for line in printed
        )
        assert os.environ.get("NB_EXEC_BACKUP_STATUS") == "warning"
        assert os.environ.get("NB_EXEC_TOTAL_CONTAINERS_COMPLETED") == "0"
        assert os.environ.get("NB_EXEC_TOTAL_CONTAINERS_SKIPPED") == "1"
        assert os.environ.get("NB_EXEC_CONTAINERS_SKIPPED") == "container1"
        assert os.environ.get("NB_EXEC_CONTAINER_SKIP_REASONS") == "container1=source_directory_missing"

    @mock.patch("subprocess.run")
    @pytest.mark.parametrize("mock_container1", [{"name": "container1", "id": "123456789"}], indirect=True)
    def test_post_backup_exec_variables_for_rsync_failure(
        self,
        mock_subprocess_run: MagicMock,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """Test rsync failures are errors and available to POST_BACKUP_EXEC."""

        monkeypatch.setenv("POST_BACKUP_EXEC", "echo test")

        rsync_result = MagicMock()
        rsync_result.returncode = 23
        exec_result = MagicMock()
        exec_result.returncode = 0
        exec_result.stderr = b""
        exec_result.stdout = b""
        mock_subprocess_run.side_effect = [rsync_result, exec_result]

        mock_docker_client.containers.list.return_value = [mock_container1]
        nb = NauticalBackup(mock_docker_client)
        nb.backup()

        assert "container1" in nb.containers_skipped
        assert "container1" in nb.containers_failed
        assert "container1" not in nb.containers_completed
        assert os.environ.get("NB_EXEC_BACKUP_STATUS") == "error"
        assert os.environ.get("NB_EXEC_TOTAL_CONTAINERS_COMPLETED") == "0"
        assert os.environ.get("NB_EXEC_TOTAL_CONTAINERS_SKIPPED") == "1"
        assert os.environ.get("NB_EXEC_TOTAL_ERRORS") == "1"
        assert os.environ.get("NB_EXEC_CONTAINERS_SKIPPED") == "container1"
        assert os.environ.get("NB_EXEC_CONTAINERS_FAILED") == "container1"
        assert os.environ.get("NB_EXEC_CONTAINER_SKIP_REASONS") == "container1=rsync_failed"
        assert os.environ.get("NB_EXEC_CONTAINER_FAILURE_REASONS") == "container1=rsync_failed"
        assert (
            os.environ.get("NB_EXEC_ERROR_MESSAGES")
            == "rsync exited with code 23 for container1 (symlinks may have been skipped — use RSYNC_CUSTOM_ARGS=--no-links to suppress)"
        )

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

        mock_subprocess_run.return_value.returncode = 0
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

        mock_subprocess_run.return_value.returncode = 0
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

    @mock.patch("subprocess.run")
    @pytest.mark.parametrize(
        "mock_container1",
        [
            {
                "name": "container1",
                "id": "123456789",
                "labels": {
                    "nautical-backup.override-source-dir": "immich/database",
                },
            }
        ],
        indirect=True,
    )
    def test_nested_source_and_dest(
        self,
        mock_subprocess_run: MagicMock,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
    ):
        """Test nested source directory"""
        nautical_env = NauticalEnv()
        nested_path = Path(nautical_env.SOURCE_LOCATION) / "immich" / "database"
        nested_path.mkdir(parents=True, exist_ok=True)

        # Remove the destination directory. It should be created
        rm_tree(Path(nautical_env.DEST_LOCATION) / "immich" / "database")

        mock_docker_client.containers.list.return_value = [mock_container1]
        nb = NauticalBackup(mock_docker_client)
        nb.backup()

        assert (
            mock_subprocess_run.call_args_list[0][0][0]
            == f"/usr/bin/rsync -raq  {nautical_env.SOURCE_LOCATION}/immich/database/ {nautical_env.DEST_LOCATION}/immich/database/"
        )

    @mock.patch("subprocess.run")
    @pytest.mark.parametrize(
        "mock_container1",
        [
            {
                "name": "container1",
                "id": "123456789",
                "labels": {
                    "nautical-backup.source-dir-required": "false",
                },
                "source_exists": False,
            }
        ],
        indirect=True,
    )
    def test_source_dir_required_label(
        self,
        mock_subprocess_run: MagicMock,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
    ):
        """Test source-dir-required label"""

        mock_docker_client.containers.list.return_value = [mock_container1]
        nb = NauticalBackup(mock_docker_client)
        nb.backup()

        # Container once has no source dir, so no rsync or stop is called
        mock_container1.stop.assert_called_once()
        mock_subprocess_run.assert_not_called()
        mock_container1.start.assert_called_once()

    @pytest.mark.parametrize("mock_container1", [{"name": "container1", "id": "123456789"}], indirect=True)
    def test_STOP_TIMEOUT_env(
        self,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ):

        mock_docker_client.containers.list.return_value = [mock_container1]
        nb = NauticalBackup(mock_docker_client)
        nb.backup()

        # Ensure the default timeout is 10
        mock_container1.stop.assert_called_once_with(timeout=10)

        monkeypatch.setenv("STOP_TIMEOUT", "15")

        mock_docker_client.containers.list.return_value = [mock_container1]
        nb = NauticalBackup(mock_docker_client)
        nb.backup()

        # Ensure the set timeout is 15
        assert mock_container1.stop.call_args_list[1] == call(timeout=15)

    @pytest.mark.parametrize(
        "mock_container1",
        [
            {
                "name": "container1",
                "id": "123456789",
                "labels": {"nautical-backup.stop-timeout": "20"},
            }
        ],
        indirect=True,
    )
    def test_STOP_TIMEOUT_label(
        self,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ):

        monkeypatch.setenv("STOP_TIMEOUT", "15")

        mock_docker_client.containers.list.return_value = [mock_container1]
        nb = NauticalBackup(mock_docker_client)
        nb.backup()

        # Ensure the set timeout is 20
        mock_container1.stop.assert_called_once_with(timeout=20)

    @mock.patch("subprocess.run")
    @pytest.mark.parametrize("mock_container1", [{"name": "container1", "id": "123456789"}], indirect=True)
    @pytest.mark.parametrize("mock_container2", [{"name": "container2", "id": "9876543210"}], indirect=True)
    def test_stop_container_read_timeout_container_stopped(
        self,
        mock_subprocess_run: MagicMock,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
        mock_container2: MagicMock,
    ):
        """ReadTimeout on stop, but container actually stopped — backup should proceed normally"""
        mock_subprocess_run.return_value.returncode = 0
        mock_container1.stop.side_effect = ReadTimeout()

        mock_docker_client.containers.list.return_value = [mock_container1, mock_container2]
        nb = NauticalBackup(mock_docker_client)
        nb.backup()

        # Both containers should be backed up (container1 stopped despite timeout)
        assert mock_subprocess_run.call_count == 2
        mock_container1.start.assert_called()
        mock_container2.stop.assert_called()
        mock_container2.start.assert_called()

    @mock.patch("subprocess.run")
    @pytest.mark.parametrize(
        "mock_container1",
        [
            {
                "name": "container1",
                "id": "123456789",
                # Container never reaches exited state after the timeout
                "status_side_effect": ["running", "running", "running", "running", "running"],
            }
        ],
        indirect=True,
    )
    @pytest.mark.parametrize("mock_container2", [{"name": "container2", "id": "9876543210"}], indirect=True)
    def test_stop_container_read_timeout_container_not_stopped(
        self,
        mock_subprocess_run: MagicMock,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
        mock_container2: MagicMock,
    ):
        """ReadTimeout on stop and container never stopped — container1 fails, container2 still runs"""
        mock_subprocess_run.return_value.returncode = 0
        mock_container1.stop.side_effect = ReadTimeout()

        mock_docker_client.containers.list.return_value = [mock_container1, mock_container2]
        nb = NauticalBackup(mock_docker_client)
        nb.backup()

        # container1 was not stopped so it should not be backed up
        # container2 should still be processed
        mock_container2.stop.assert_called()
        mock_container2.start.assert_called()
        assert mock_subprocess_run.call_count == 1

    @mock.patch("subprocess.run")
    @pytest.mark.parametrize("mock_container1", [{"name": "container1", "id": "123456789"}], indirect=True)
    def test_start_container_read_timeout(
        self,
        mock_subprocess_run: MagicMock,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
    ):
        """ReadTimeout on start — backup should not crash and container failure should be recorded"""
        mock_subprocess_run.return_value.returncode = 0
        mock_container1.start.side_effect = ReadTimeout()

        mock_docker_client.containers.list.return_value = [mock_container1]
        nb = NauticalBackup(mock_docker_client)
        nb.backup()

        # Backup ran and rsync was called despite the start timeout
        mock_subprocess_run.assert_called_once()
        mock_container1.stop.assert_called()
        mock_container1.start.assert_called()

    @mock.patch("subprocess.run")
    @pytest.mark.parametrize(
        "mock_container1",
        [
            {
                "name": "container1",
                "id": "123456789",
                # Reads: stop-check, after-stop, pre-rsync, start-attempt-1,
                #        after-c.start (restarting), retry-2 (restarting), retry-3 (running)
                "status_side_effect": ["running", "exited", "exited", "exited", "restarting", "restarting", "running"],
            }
        ],
        indirect=True,
    )
    def test_start_container_transitional_state_eventually_running(
        self,
        mock_subprocess_run: MagicMock,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
    ):
        """Container in transitional state (e.g. 'restarting') after c.start() should be retried
        until it reaches 'running', and the backup should be marked as completed — not failed."""
        mock_subprocess_run.return_value.returncode = 0

        mock_docker_client.containers.list.return_value = [mock_container1]
        nb = NauticalBackup(mock_docker_client)
        nb.backup()

        mock_container1.stop.assert_called()
        mock_container1.start.assert_called()
        assert "container1" in nb.containers_completed
        assert "container1" not in nb.containers_failed

    @mock.patch("subprocess.run")
    @pytest.mark.parametrize(
        "mock_container1",
        [
            {
                "name": "container1",
                "id": "123456789",
                # Reads: stop-check, after-stop, pre-rsync, start-attempt-1,
                #        after-c.start (restarting), retry-2 (restarting), retry-3 (restarting), retry-4 (running)
                # Mirrors the exact sequence from issue #683 (2026-05-25 comment)
                "status_side_effect": [
                    "running",
                    "exited",
                    "exited",
                    "exited",
                    "restarting",
                    "restarting",
                    "restarting",
                    "running",
                ],
            }
        ],
        indirect=True,
    )
    def test_start_container_three_restarting_states_eventually_running(
        self,
        mock_subprocess_run: MagicMock,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
    ):
        """Container that stays in 'restarting' for 3 cycles before becoming running should still
        complete successfully. Reproduces the scenario from issue #683 (2026-05-25)."""
        mock_subprocess_run.return_value.returncode = 0

        mock_docker_client.containers.list.return_value = [mock_container1]
        nb = NauticalBackup(mock_docker_client)
        nb.backup()

        mock_container1.stop.assert_called()
        mock_container1.start.assert_called()
        assert "container1" in nb.containers_completed
        assert "container1" not in nb.containers_failed

    @mock.patch("subprocess.run")
    @pytest.mark.parametrize(
        "mock_container1",
        [
            {
                "name": "container1",
                "id": "123456789",
                "labels": {"nautical-backup.start-timeout": "10"},
                # Needs 4 retries after c.start() to reach running.
                # START_TIMEOUT=2 → max_attempts=2 (formula: (2//2)+1=2), so attempt=3 sees
                # "restarting" and returns False — failure without the label.
                # Label start-timeout=10 → max_attempts=6 ((10//2)+1), so it succeeds.
                "status_side_effect": [
                    "running",
                    "exited",
                    "exited",
                    "exited",
                    "restarting",
                    "restarting",
                    "restarting",
                    "restarting",
                    "running",
                ],
            }
        ],
        indirect=True,
    )
    def test_START_TIMEOUT_label_supersedes_env(
        self,
        mock_subprocess_run: MagicMock,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """Per-container start-timeout label should override the global START_TIMEOUT env var."""
        mock_subprocess_run.return_value.returncode = 0
        monkeypatch.setenv("START_TIMEOUT", "2")  # max_attempts=2 — exhausted before container is running

        mock_docker_client.containers.list.return_value = [mock_container1]
        nb = NauticalBackup(mock_docker_client)
        nb.backup()

        assert "container1" in nb.containers_completed
        assert "container1" not in nb.containers_failed

    @mock.patch("subprocess.run")
    @pytest.mark.parametrize(
        "mock_container1",
        [
            {
                "name": "container1",
                "id": "123456789",
                # Reads: stop-check, after-stop, pre-rsync, start-attempt-1,
                #        after-c.start (not running yet), start-attempt-2, after-c.start-2 (running)
                "status_side_effect": ["running", "exited", "exited", "exited", "exited", "exited", "running"],
            }
        ],
        indirect=True,
    )
    def test_start_container_retry_success_propagates(
        self,
        mock_subprocess_run: MagicMock,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
    ):
        """When container start fails on attempt 1 but succeeds on attempt 2, the backup should be
        marked completed (not failed). This tests the missing-return bug fix."""
        mock_subprocess_run.return_value.returncode = 0

        mock_docker_client.containers.list.return_value = [mock_container1]
        nb = NauticalBackup(mock_docker_client)
        nb.backup()

        assert mock_container1.start.call_count == 2
        assert "container1" in nb.containers_completed
        assert "container1" not in nb.containers_failed

    @mock.patch("subprocess.run")
    @pytest.mark.parametrize("mock_container1", [{"name": "container1", "id": "123456789"}], indirect=True)
    def test_rsync_exit_code_23_includes_symlink_hint(
        self,
        mock_subprocess_run: MagicMock,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
    ):
        """rsync exit code 23 (partial transfer) should include a hint about symlinks and the
        RSYNC_CUSTOM_ARGS=--no-links workaround in the error message."""
        rsync_result = MagicMock()
        rsync_result.returncode = 23
        mock_subprocess_run.return_value = rsync_result

        mock_docker_client.containers.list.return_value = [mock_container1]
        nb = NauticalBackup(mock_docker_client)
        nb.backup()

        assert len(nb.error_messages) == 1
        assert "--no-links" in nb.error_messages[0]
        assert "symlinks" in nb.error_messages[0]
        assert "container1" in nb.containers_failed

    @mock.patch("builtins.print")
    @mock.patch("subprocess.run")
    @pytest.mark.parametrize(
        "mock_container1",
        [
            {
                "name": "container1",
                "id": "123456789",
                # Container never reaches running after start — stays restarting through all attempts.
                # START_TIMEOUT=2 → max_attempts=(2//2)+1=2.
                # Reads: stop-check, after-stop, during-backup, attempt-1, post-start, attempt-2, attempt-3(→False)
                "status_side_effect": [
                    "running",
                    "exited",
                    "exited",
                    "exited",
                    "restarting",
                    "restarting",
                    "restarting",
                ],
            }
        ],
        indirect=True,
    )
    def test_start_container_exhausted_retries_not_in_completed(
        self,
        mock_subprocess_run: MagicMock,
        mock_print: MagicMock,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """When _start_container exhausts all retries, container must be in containers_failed,
        NOT in containers_completed, and a WARN about the partial backup should be logged."""
        mock_subprocess_run.return_value.returncode = 0
        monkeypatch.setenv("START_TIMEOUT", "2")  # max_attempts=2 → 3 total attempts before giving up

        mock_docker_client.containers.list.return_value = [mock_container1]
        nb = NauticalBackup(mock_docker_client)
        nb.backup()

        assert "container1" in nb.containers_failed
        assert "container1" not in nb.containers_completed

        printed = [call_args[0][0] for call_args in mock_print.call_args_list]
        assert any("failed to restart within the start timeout" in line for line in printed)
        assert not any("Backup of container1 complete!" in line for line in printed)

    # -------------------------------------------------------------------------
    # Retention policy tests
    # -------------------------------------------------------------------------

    @pytest.mark.parametrize("mock_container1", [{"name": "container1", "id": "123456789"}], indirect=True)
    def test_retention_policy_date_container_format(
        self,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """Retention with date/container path format: oldest date folders are removed."""
        nautical_env = NauticalEnv()
        dest = Path(nautical_env.DEST_LOCATION)
        rm_tree(dest)
        dest.mkdir(parents=True, exist_ok=True)

        # Pre-create 4 dated folders (date/container layout)
        dates = ["2025-01-01", "2025-01-02", "2025-01-03", "2025-01-04"]
        for d in dates:
            (dest / d / "container1").mkdir(parents=True, exist_ok=True)

        monkeypatch.setenv("USE_DEST_DATE_FOLDER", "true")
        monkeypatch.setenv("DEST_DATE_PATH_FORMAT", "date/container")
        monkeypatch.setenv("NUMBER_OF_BACKUPS_TO_KEEP", "2")

        mock_docker_client.containers.list.return_value = [mock_container1]
        nb = NauticalBackup(mock_docker_client)
        nb._apply_retention_policy(dest)

        remaining = sorted(p.name for p in dest.iterdir() if p.is_dir())
        assert "2025-01-01" not in remaining
        assert "2025-01-02" not in remaining
        assert "2025-01-03" in remaining
        assert "2025-01-04" in remaining

    @pytest.mark.parametrize("mock_container1", [{"name": "container1", "id": "123456789"}], indirect=True)
    def test_retention_policy_container_date_format(
        self,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """Retention with container/date path format: oldest date folders per container are removed."""
        nautical_env = NauticalEnv()
        dest = Path(nautical_env.DEST_LOCATION)
        rm_tree(dest)
        dest.mkdir(parents=True, exist_ok=True)

        dates = ["2025-01-01", "2025-01-02", "2025-01-03"]
        for d in dates:
            (dest / "container1" / d).mkdir(parents=True, exist_ok=True)

        monkeypatch.setenv("USE_DEST_DATE_FOLDER", "true")
        monkeypatch.setenv("DEST_DATE_PATH_FORMAT", "container/date")
        monkeypatch.setenv("NUMBER_OF_BACKUPS_TO_KEEP", "2")

        mock_docker_client.containers.list.return_value = [mock_container1]
        nb = NauticalBackup(mock_docker_client)
        nb._apply_retention_policy(dest)

        remaining = sorted(p.name for p in (dest / "container1").iterdir() if p.is_dir())
        assert "2025-01-01" not in remaining
        assert "2025-01-02" in remaining
        assert "2025-01-03" in remaining

    @pytest.mark.parametrize("mock_container1", [{"name": "container1", "id": "123456789"}], indirect=True)
    def test_retention_policy_container_date_prunes_each_container_independently(
        self,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """container/date retention is calculated independently per container folder."""
        nautical_env = NauticalEnv()
        dest = Path(nautical_env.DEST_LOCATION)
        rm_tree(dest)
        dest.mkdir(parents=True, exist_ok=True)

        for d in ["2025-01-01", "2025-01-02", "2025-01-03", "2025-01-04"]:
            (dest / "container1" / d).mkdir(parents=True, exist_ok=True)

        for d in ["2025-01-03", "2025-01-04"]:
            (dest / "container2" / d).mkdir(parents=True, exist_ok=True)

        monkeypatch.setenv("USE_DEST_DATE_FOLDER", "true")
        monkeypatch.setenv("DEST_DATE_PATH_FORMAT", "container/date")
        monkeypatch.setenv("NUMBER_OF_BACKUPS_TO_KEEP", "2")

        mock_docker_client.containers.list.return_value = [mock_container1]
        nb = NauticalBackup(mock_docker_client)
        nb._apply_retention_policy(dest)

        assert not (dest / "container1" / "2025-01-01").exists()
        assert not (dest / "container1" / "2025-01-02").exists()
        assert (dest / "container1" / "2025-01-03").exists()
        assert (dest / "container1" / "2025-01-04").exists()

        assert (dest / "container2" / "2025-01-03").exists()
        assert (dest / "container2" / "2025-01-04").exists()

    @pytest.mark.parametrize("mock_container1", [{"name": "container1", "id": "123456789"}], indirect=True)
    def test_retention_policy_container_date_dry_run(
        self,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """Dry-run mode does not delete old container/date backup folders."""
        nautical_env = NauticalEnv()
        dest = Path(nautical_env.DEST_LOCATION)
        rm_tree(dest)
        dest.mkdir(parents=True, exist_ok=True)

        dates = ["2025-01-01", "2025-01-02", "2025-01-03"]
        for d in dates:
            (dest / "container1" / d).mkdir(parents=True, exist_ok=True)

        monkeypatch.setenv("USE_DEST_DATE_FOLDER", "true")
        monkeypatch.setenv("DEST_DATE_PATH_FORMAT", "container/date")
        monkeypatch.setenv("NUMBER_OF_BACKUPS_TO_KEEP", "1")
        monkeypatch.setenv("RETENTION_DRY_RUN", "true")

        mock_docker_client.containers.list.return_value = [mock_container1]
        nb = NauticalBackup(mock_docker_client)
        nb._apply_retention_policy(dest)

        for d in dates:
            assert (dest / "container1" / d).exists()

    @pytest.mark.parametrize("mock_container1", [{"name": "container1", "id": "123456789"}], indirect=True)
    def test_retention_policy_container_date_skips_symlinked_date_folder(
        self,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ):
        """Symlinked date folders inside a container are ignored and never followed."""
        nautical_env = NauticalEnv()
        dest = Path(nautical_env.DEST_LOCATION)
        rm_tree(dest)
        dest.mkdir(parents=True, exist_ok=True)

        outside = tmp_path / "outside-date"
        (outside / "payload").mkdir(parents=True, exist_ok=True)
        container_dir = dest / "container1"
        container_dir.mkdir(parents=True, exist_ok=True)
        symlinked_date = container_dir / "2025-01-01"
        symlinked_date.symlink_to(outside, target_is_directory=True)

        try:
            (container_dir / "2025-01-02").mkdir(parents=True, exist_ok=True)
            (container_dir / "2025-01-03").mkdir(parents=True, exist_ok=True)

            monkeypatch.setenv("USE_DEST_DATE_FOLDER", "true")
            monkeypatch.setenv("DEST_DATE_PATH_FORMAT", "container/date")
            monkeypatch.setenv("NUMBER_OF_BACKUPS_TO_KEEP", "1")

            mock_docker_client.containers.list.return_value = [mock_container1]
            nb = NauticalBackup(mock_docker_client)
            nb._apply_retention_policy(dest)

            assert (outside / "payload").exists()
            assert symlinked_date.is_symlink()
            assert not (container_dir / "2025-01-02").exists()
            assert (container_dir / "2025-01-03").exists()
        finally:
            if symlinked_date.is_symlink():
                symlinked_date.unlink()

    @pytest.mark.parametrize("mock_container1", [{"name": "container1", "id": "123456789"}], indirect=True)
    def test_retention_policy_custom_date_format(
        self,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """Retention correctly parses and sorts a non-ISO custom DEST_DATE_FORMAT."""
        nautical_env = NauticalEnv()
        dest = Path(nautical_env.DEST_LOCATION)
        rm_tree(dest)
        dest.mkdir(parents=True, exist_ok=True)

        # Use day-first format: oldest should be removed
        dates = ["01-2025-01", "02-2025-01", "03-2025-01"]
        for d in dates:
            (dest / d / "container1").mkdir(parents=True, exist_ok=True)

        monkeypatch.setenv("USE_DEST_DATE_FOLDER", "true")
        monkeypatch.setenv("DEST_DATE_PATH_FORMAT", "date/container")
        monkeypatch.setenv("DEST_DATE_FORMAT", "%d-%Y-%m")
        monkeypatch.setenv("NUMBER_OF_BACKUPS_TO_KEEP", "2")

        mock_docker_client.containers.list.return_value = [mock_container1]
        nb = NauticalBackup(mock_docker_client)
        nb._apply_retention_policy(dest)

        remaining = sorted(p.name for p in dest.iterdir() if p.is_dir())
        assert "01-2025-01" not in remaining
        assert "02-2025-01" in remaining
        assert "03-2025-01" in remaining

    @pytest.mark.parametrize("mock_container1", [{"name": "container1", "id": "123456789"}], indirect=True)
    def test_retention_policy_disabled_without_date_folder(
        self,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """Retention does nothing when USE_DEST_DATE_FOLDER is not true."""
        nautical_env = NauticalEnv()
        dest = Path(nautical_env.DEST_LOCATION)
        rm_tree(dest)
        dest.mkdir(parents=True, exist_ok=True)

        (dest / "container1").mkdir(parents=True, exist_ok=True)

        monkeypatch.setenv("USE_DEST_DATE_FOLDER", "false")
        monkeypatch.setenv("NUMBER_OF_BACKUPS_TO_KEEP", "1")

        mock_docker_client.containers.list.return_value = [mock_container1]
        nb = NauticalBackup(mock_docker_client)
        nb._apply_retention_policy(dest)

        assert (dest / "container1").exists()

    @pytest.mark.parametrize("mock_container1", [{"name": "container1", "id": "123456789"}], indirect=True)
    def test_retention_policy_non_date_folders_untouched(
        self,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """Folders that don't match DEST_DATE_FORMAT are never deleted."""
        nautical_env = NauticalEnv()
        dest = Path(nautical_env.DEST_LOCATION)
        rm_tree(dest)
        dest.mkdir(parents=True, exist_ok=True)

        (dest / "not-a-date").mkdir(parents=True, exist_ok=True)
        (dest / "also-not-a-date").mkdir(parents=True, exist_ok=True)
        dates = ["2025-01-01", "2025-01-02", "2025-01-03"]
        for d in dates:
            (dest / d / "container1").mkdir(parents=True, exist_ok=True)

        monkeypatch.setenv("USE_DEST_DATE_FOLDER", "true")
        monkeypatch.setenv("DEST_DATE_PATH_FORMAT", "date/container")
        monkeypatch.setenv("NUMBER_OF_BACKUPS_TO_KEEP", "1")

        mock_docker_client.containers.list.return_value = [mock_container1]
        nb = NauticalBackup(mock_docker_client)
        nb._apply_retention_policy(dest)

        assert (dest / "not-a-date").exists()
        assert (dest / "also-not-a-date").exists()
        assert not (dest / "2025-01-01").exists()
        assert not (dest / "2025-01-02").exists()
        assert (dest / "2025-01-03").exists()

    @pytest.mark.parametrize("mock_container1", [{"name": "container1", "id": "123456789"}], indirect=True)
    def test_retention_policy_dry_run(
        self,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """Dry-run mode logs candidates but does not delete anything."""
        nautical_env = NauticalEnv()
        dest = Path(nautical_env.DEST_LOCATION)
        rm_tree(dest)
        dest.mkdir(parents=True, exist_ok=True)

        dates = ["2025-01-01", "2025-01-02", "2025-01-03"]
        for d in dates:
            (dest / d / "container1").mkdir(parents=True, exist_ok=True)

        monkeypatch.setenv("USE_DEST_DATE_FOLDER", "true")
        monkeypatch.setenv("DEST_DATE_PATH_FORMAT", "date/container")
        monkeypatch.setenv("NUMBER_OF_BACKUPS_TO_KEEP", "1")
        monkeypatch.setenv("RETENTION_DRY_RUN", "true")

        mock_docker_client.containers.list.return_value = [mock_container1]
        nb = NauticalBackup(mock_docker_client)
        nb._apply_retention_policy(dest)

        # Nothing deleted in dry-run mode
        for d in dates:
            assert (dest / d).exists()

    @pytest.mark.parametrize("mock_container1", [{"name": "container1", "id": "123456789"}], indirect=True)
    def test_retention_policy_secondary_destinations_disabled(
        self,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ):
        """RETENTION_SECONDARY_DESTINATIONS=false skips secondary dirs but still prunes primary."""
        nautical_env = NauticalEnv()
        primary = Path(nautical_env.DEST_LOCATION)
        rm_tree(primary)
        primary.mkdir(parents=True, exist_ok=True)

        secondary = tmp_path / "secondary"
        secondary.mkdir()

        # 3 dated folders in primary, 3 in secondary
        dates = ["2025-01-01", "2025-01-02", "2025-01-03"]
        for d in dates:
            (primary / d / "container1").mkdir(parents=True, exist_ok=True)
            (secondary / d / "container1").mkdir(parents=True, exist_ok=True)

        monkeypatch.setenv("USE_DEST_DATE_FOLDER", "true")
        monkeypatch.setenv("DEST_DATE_PATH_FORMAT", "date/container")
        monkeypatch.setenv("NUMBER_OF_BACKUPS_TO_KEEP", "1")
        monkeypatch.setenv("RETENTION_SECONDARY_DESTINATIONS", "false")
        monkeypatch.setenv("SECONDARY_DEST_DIRS", str(secondary))

        mock_docker_client.containers.list.return_value = [mock_container1]
        nb = NauticalBackup(mock_docker_client)

        # Apply retention manually to primary; secondary skipped because of the env flag
        nb._apply_retention_policy(primary)
        if nb.env.RETENTION_SECONDARY_DESTINATIONS:
            nb._apply_retention_policy(secondary)

        # Primary pruned
        assert not (primary / "2025-01-01").exists()
        assert not (primary / "2025-01-02").exists()
        assert (primary / "2025-01-03").exists()

        # Secondary untouched
        for d in dates:
            assert (secondary / d).exists()

    @mock.patch("subprocess.run")
    @pytest.mark.parametrize("mock_container1", [{"name": "container1", "id": "123456789"}], indirect=True)
    def test_retention_policy_secondary_destinations_disabled_during_backup(
        self,
        mock_subprocess_run: MagicMock,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ):
        """backup() prunes primary retention but skips secondary dirs when configured."""
        mock_subprocess_run.return_value.returncode = 0

        nautical_env = NauticalEnv()
        primary = Path(nautical_env.DEST_LOCATION)
        rm_tree(primary)
        primary.mkdir(parents=True, exist_ok=True)

        secondary = tmp_path / "secondary"
        secondary.mkdir()

        dates = ["2025-01-01", "2025-01-02", "2025-01-03"]
        for d in dates:
            (primary / d / "container1").mkdir(parents=True, exist_ok=True)
            (secondary / d / "container1").mkdir(parents=True, exist_ok=True)

        monkeypatch.setenv("USE_DEST_DATE_FOLDER", "true")
        monkeypatch.setenv("DEST_DATE_PATH_FORMAT", "date/container")
        monkeypatch.setenv("NUMBER_OF_BACKUPS_TO_KEEP", "1")
        monkeypatch.setenv("RETENTION_SECONDARY_DESTINATIONS", "false")
        monkeypatch.setenv("SECONDARY_DEST_DIRS", str(secondary))
        monkeypatch.setenv("REPORT_FILE", "false")

        mock_docker_client.containers.list.return_value = [mock_container1]
        nb = NauticalBackup(mock_docker_client)
        nb.backup()

        for d in dates:
            assert not (primary / d).exists()
            assert (secondary / d).exists()

    @mock.patch("subprocess.run")
    @pytest.mark.parametrize("mock_container1", [{"name": "container1", "id": "123456789"}], indirect=True)
    def test_retention_policy_secondary_destinations_enabled_during_backup(
        self,
        mock_subprocess_run: MagicMock,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ):
        """backup() prunes primary and secondary destinations when secondary retention is enabled."""
        mock_subprocess_run.return_value.returncode = 0

        nautical_env = NauticalEnv()
        primary = Path(nautical_env.DEST_LOCATION)
        rm_tree(primary)
        primary.mkdir(parents=True, exist_ok=True)

        secondary = tmp_path / "secondary"
        secondary.mkdir()

        dates = ["2025-01-01", "2025-01-02", "2025-01-03"]
        for d in dates:
            (primary / d / "container1").mkdir(parents=True, exist_ok=True)
            (secondary / d / "container1").mkdir(parents=True, exist_ok=True)

        monkeypatch.setenv("USE_DEST_DATE_FOLDER", "true")
        monkeypatch.setenv("DEST_DATE_PATH_FORMAT", "date/container")
        monkeypatch.setenv("NUMBER_OF_BACKUPS_TO_KEEP", "1")
        monkeypatch.setenv("RETENTION_SECONDARY_DESTINATIONS", "true")
        monkeypatch.setenv("SECONDARY_DEST_DIRS", str(secondary))
        monkeypatch.setenv("REPORT_FILE", "false")

        mock_docker_client.containers.list.return_value = [mock_container1]
        nb = NauticalBackup(mock_docker_client)
        nb.backup()

        for d in dates:
            assert not (primary / d).exists()
            assert not (secondary / d).exists()

    @pytest.mark.parametrize("mock_container1", [{"name": "container1", "id": "123456789"}], indirect=True)
    def test_retention_policy_date_container_multi_container(
        self,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """date/container: old date folders are removed as whole backup sets."""
        nautical_env = NauticalEnv()
        dest = Path(nautical_env.DEST_LOCATION)
        rm_tree(dest)
        dest.mkdir(parents=True, exist_ok=True)

        dates = ["2025-01-01", "2025-01-02", "2025-01-03"]
        containers = ["container1", "container2"]
        for d in dates:
            for c in containers:
                (dest / d / c).mkdir(parents=True, exist_ok=True)

        monkeypatch.setenv("USE_DEST_DATE_FOLDER", "true")
        monkeypatch.setenv("DEST_DATE_PATH_FORMAT", "date/container")
        monkeypatch.setenv("NUMBER_OF_BACKUPS_TO_KEEP", "2")

        mock_docker_client.containers.list.return_value = [mock_container1]
        nb = NauticalBackup(mock_docker_client)
        nb._apply_retention_policy(dest)

        # Oldest date folder is pruned atomically, including both containers.
        assert not (dest / "2025-01-01").exists()

        # Kept date folders intact for both containers
        assert (dest / "2025-01-02" / "container1").exists()
        assert (dest / "2025-01-02" / "container2").exists()
        assert (dest / "2025-01-03" / "container1").exists()
        assert (dest / "2025-01-03" / "container2").exists()

    @pytest.mark.parametrize("mock_container1", [{"name": "container1", "id": "123456789"}], indirect=True)
    def test_retention_policy_date_container_deletes_entire_old_date_folder(
        self,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """date/container retention deletes the whole old date folder, including direct files."""
        nautical_env = NauticalEnv()
        dest = Path(nautical_env.DEST_LOCATION)
        rm_tree(dest)
        dest.mkdir(parents=True, exist_ok=True)

        for d in ["2025-01-01", "2025-01-02"]:
            (dest / d / "container1").mkdir(parents=True, exist_ok=True)
            (dest / d / "container2").mkdir(parents=True, exist_ok=True)
            (dest / d / "note.txt").write_text(f"backup metadata for {d}")

        monkeypatch.setenv("USE_DEST_DATE_FOLDER", "true")
        monkeypatch.setenv("DEST_DATE_PATH_FORMAT", "date/container")
        monkeypatch.setenv("NUMBER_OF_BACKUPS_TO_KEEP", "1")

        mock_docker_client.containers.list.return_value = [mock_container1]
        nb = NauticalBackup(mock_docker_client)
        nb._apply_retention_policy(dest)

        assert not (dest / "2025-01-01").exists()
        assert (dest / "2025-01-02" / "container1").exists()
        assert (dest / "2025-01-02" / "container2").exists()
        assert (dest / "2025-01-02" / "note.txt").exists()

    @pytest.mark.parametrize("mock_container1", [{"name": "container1", "id": "123456789"}], indirect=True)
    def test_retention_policy_date_container_partial_container_coverage(
        self,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """date/container: pruning is based on date folders, not per-container counts."""
        nautical_env = NauticalEnv()
        dest = Path(nautical_env.DEST_LOCATION)
        rm_tree(dest)
        dest.mkdir(parents=True, exist_ok=True)

        # container1 has 3 backups; container2 only has 2 (missing the oldest date)
        (dest / "2025-01-01" / "container1").mkdir(parents=True, exist_ok=True)
        (dest / "2025-01-02" / "container1").mkdir(parents=True, exist_ok=True)
        (dest / "2025-01-02" / "container2").mkdir(parents=True, exist_ok=True)
        (dest / "2025-01-03" / "container1").mkdir(parents=True, exist_ok=True)
        (dest / "2025-01-03" / "container2").mkdir(parents=True, exist_ok=True)

        monkeypatch.setenv("USE_DEST_DATE_FOLDER", "true")
        monkeypatch.setenv("DEST_DATE_PATH_FORMAT", "date/container")
        monkeypatch.setenv("NUMBER_OF_BACKUPS_TO_KEEP", "2")

        mock_docker_client.containers.list.return_value = [mock_container1]
        nb = NauticalBackup(mock_docker_client)
        nb._apply_retention_policy(dest)

        # Oldest date folder is pruned even though only container1 is present there.
        assert not (dest / "2025-01-01").exists()

        # container1 kept in 2025-01-02 and 2025-01-03
        assert (dest / "2025-01-02" / "container1").exists()
        assert (dest / "2025-01-03" / "container1").exists()

        # container2 is kept because it is only present in retained date folders.
        assert (dest / "2025-01-02" / "container2").exists()
        assert (dest / "2025-01-03" / "container2").exists()

    @pytest.mark.parametrize("mock_container1", [{"name": "mycontainer", "id": "123456789"}], indirect=True)
    def test_retention_policy_min_backups_overrides_keep(
        self,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """MIN_BACKUPS_TO_KEEP overrides NUMBER_OF_BACKUPS_TO_KEEP when the floor is higher."""
        nautical_env = NauticalEnv()
        dest = Path(nautical_env.DEST_LOCATION)
        rm_tree(dest)
        dest.mkdir(parents=True, exist_ok=True)

        # 5 dated backups for one container
        for d in ["2025-01-01", "2025-01-02", "2025-01-03", "2025-01-04", "2025-01-05"]:
            (dest / d / "mycontainer").mkdir(parents=True, exist_ok=True)

        monkeypatch.setenv("USE_DEST_DATE_FOLDER", "true")
        monkeypatch.setenv("DEST_DATE_PATH_FORMAT", "date/container")
        monkeypatch.setenv("NUMBER_OF_BACKUPS_TO_KEEP", "1")
        monkeypatch.setenv("MIN_BACKUPS_TO_KEEP", "3")

        mock_docker_client.containers.list.return_value = [mock_container1]
        nb = NauticalBackup(mock_docker_client)
        nb._apply_retention_policy(dest)

        # Floor of 3 wins over keep=1: 3 most recent kept, 2 oldest deleted
        assert not (dest / "2025-01-01" / "mycontainer").exists()
        assert not (dest / "2025-01-02" / "mycontainer").exists()
        assert (dest / "2025-01-03" / "mycontainer").exists()
        assert (dest / "2025-01-04" / "mycontainer").exists()
        assert (dest / "2025-01-05" / "mycontainer").exists()

    @mock.patch("app.backup.shutil.rmtree")
    @pytest.mark.parametrize("mock_container1", [{"name": "container1", "id": "123456789"}], indirect=True)
    def test_retention_policy_delete_error_is_recorded_without_raising(
        self,
        mock_rmtree: MagicMock,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """Retention delete failures are reported without aborting the backup process."""
        mock_rmtree.side_effect = OSError("permission denied")

        nautical_env = NauticalEnv()
        dest = Path(nautical_env.DEST_LOCATION)
        rm_tree(dest)
        dest.mkdir(parents=True, exist_ok=True)

        for d in ["2025-01-01", "2025-01-02", "2025-01-03"]:
            (dest / d / "container1").mkdir(parents=True, exist_ok=True)

        monkeypatch.setenv("USE_DEST_DATE_FOLDER", "true")
        monkeypatch.setenv("DEST_DATE_PATH_FORMAT", "date/container")
        monkeypatch.setenv("NUMBER_OF_BACKUPS_TO_KEEP", "1")

        mock_docker_client.containers.list.return_value = [mock_container1]
        nb = NauticalBackup(mock_docker_client)
        nb._apply_retention_policy(dest)

        assert mock_rmtree.called
        assert any("failed to remove" in message for message in nb.error_messages)

    @pytest.mark.parametrize("mock_container1", [{"name": "container1", "id": "123456789"}], indirect=True)
    def test_retention_policy_skips_symlinked_date_folder(
        self,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ):
        """Symlinked date folders are ignored so retention cannot prune outside the destination."""
        nautical_env = NauticalEnv()
        dest = Path(nautical_env.DEST_LOCATION)
        rm_tree(dest)
        dest.mkdir(parents=True, exist_ok=True)

        outside = tmp_path / "outside-date"
        (outside / "container1").mkdir(parents=True, exist_ok=True)
        symlinked_date = dest / "2025-01-01"
        symlinked_date.symlink_to(outside, target_is_directory=True)

        try:
            (dest / "2025-01-02" / "container1").mkdir(parents=True, exist_ok=True)
            (dest / "2025-01-03" / "container1").mkdir(parents=True, exist_ok=True)

            monkeypatch.setenv("USE_DEST_DATE_FOLDER", "true")
            monkeypatch.setenv("DEST_DATE_PATH_FORMAT", "date/container")
            monkeypatch.setenv("NUMBER_OF_BACKUPS_TO_KEEP", "1")

            mock_docker_client.containers.list.return_value = [mock_container1]
            nb = NauticalBackup(mock_docker_client)
            nb._apply_retention_policy(dest)

            assert (outside / "container1").exists()
            assert symlinked_date.is_symlink()
            assert not (dest / "2025-01-02").exists()
            assert (dest / "2025-01-03" / "container1").exists()
        finally:
            if symlinked_date.is_symlink():
                symlinked_date.unlink()

    @pytest.mark.parametrize("mock_container1", [{"name": "mycontainer", "id": "123456789"}], indirect=True)
    def test_retention_policy_min_backups_no_effect_when_below_keep(
        self,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """MIN_BACKUPS_TO_KEEP has no effect when it is lower than NUMBER_OF_BACKUPS_TO_KEEP."""
        nautical_env = NauticalEnv()
        dest = Path(nautical_env.DEST_LOCATION)
        rm_tree(dest)
        dest.mkdir(parents=True, exist_ok=True)

        for d in ["2025-01-01", "2025-01-02", "2025-01-03", "2025-01-04", "2025-01-05"]:
            (dest / d / "mycontainer").mkdir(parents=True, exist_ok=True)

        monkeypatch.setenv("USE_DEST_DATE_FOLDER", "true")
        monkeypatch.setenv("DEST_DATE_PATH_FORMAT", "date/container")
        monkeypatch.setenv("NUMBER_OF_BACKUPS_TO_KEEP", "3")
        monkeypatch.setenv("MIN_BACKUPS_TO_KEEP", "1")

        mock_docker_client.containers.list.return_value = [mock_container1]
        nb = NauticalBackup(mock_docker_client)
        nb._apply_retention_policy(dest)

        # keep=3 applies normally; floor of 1 has no influence
        assert not (dest / "2025-01-01" / "mycontainer").exists()
        assert not (dest / "2025-01-02" / "mycontainer").exists()
        assert (dest / "2025-01-03" / "mycontainer").exists()
        assert (dest / "2025-01-04" / "mycontainer").exists()
        assert (dest / "2025-01-05" / "mycontainer").exists()

    @pytest.mark.parametrize("mock_container1", [{"name": "container1", "id": "123456789"}], indirect=True)
    def test_retention_policy_missing_destination_is_skipped(
        self,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ):
        """A missing retention destination is skipped instead of raising."""
        dest = tmp_path / "missing-destination"

        monkeypatch.setenv("USE_DEST_DATE_FOLDER", "true")
        monkeypatch.setenv("DEST_DATE_PATH_FORMAT", "date/container")
        monkeypatch.setenv("NUMBER_OF_BACKUPS_TO_KEEP", "1")

        mock_docker_client.containers.list.return_value = [mock_container1]
        nb = NauticalBackup(mock_docker_client)
        nb._apply_retention_policy(dest)

        assert not dest.exists()

    @pytest.mark.parametrize("mock_container1", [{"name": "container1", "id": "123456789"}], indirect=True)
    def test_retention_policy_iteration_error_is_recorded_without_raising(
        self,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """Directory scan failures are reported without aborting retention."""
        nautical_env = NauticalEnv()
        dest = Path(nautical_env.DEST_LOCATION)
        rm_tree(dest)
        dest.mkdir(parents=True, exist_ok=True)

        monkeypatch.setenv("USE_DEST_DATE_FOLDER", "true")
        monkeypatch.setenv("DEST_DATE_PATH_FORMAT", "date/container")
        monkeypatch.setenv("NUMBER_OF_BACKUPS_TO_KEEP", "1")

        mock_docker_client.containers.list.return_value = [mock_container1]
        nb = NauticalBackup(mock_docker_client)

        with mock.patch("pathlib.Path.iterdir", side_effect=OSError("scan failed")):
            nb._apply_retention_policy(dest)

        assert any("unable to inspect" in message for message in nb.error_messages)
