import os
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
    def test_skip_container_env(
        self,
        mock_subprocess_run: MagicMock,
        mock_docker_client: MagicMock,
        mock_container1: MagicMock,
        mock_container2: MagicMock,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """Test that the backup method calls the correct docker methods"""

        monkeypatch.setenv("SKIP_CONTAINERS", "container-name2,container1,container-name3")

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

    # TODO: Skip container with label

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
    @pytest.mark.parametrize("mock_container1", [{"name": "container1", "id": "123456789"}], indirect=True)
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

    # TODO: Test backup on start
    # TODO: Test standalone additional folders
    # TODO: Test standalone addional folders when (before/after)

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
