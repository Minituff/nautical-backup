import os
import pytest
from pathlib import Path
from mock import mock, MagicMock, patch
from pathlib import Path
import docker
from docker.models.containers import Container

from app.nautical_env import NauticalEnv
from app.backup import NauticalBackup


class TestBackup:
    global default_labels
    default_labels = {
        "nautical-backup.group": "",
        "nautical-backup.additional-folders.when": "during",
        "nautical-backup.additional-folders": "",
        "nautical-backup.rsync-custom-args": "",
        "nautical-backup.use-default-rsync-args": ""
        
    }
    
    @classmethod
    def setup_class(cls):
        """Runs 1 time before all tests in this class"""
        pass

    def test_docker_run(
        self,
    ):
        # Create a mock container instance
        mockDockerClient = MagicMock(spec=docker.DockerClient)
        
        
   
        # Set up the mock labels dictionary and its get method
        def fake_labels(*args):
            if args[0] in default_labels:
                return default_labels[args[0]]
            
            if args[1]: # Default value
                return args[1]
            
        mockContainer1 = MagicMock(spec=Container)
        mockContainer1.name = "container1"
        mockContainer1.id = "1234456789"
        mockContainer1.labels.get.side_effect = fake_labels
        
        mockDockerClient.containers.list.return_value = [mockContainer1]
        
        nb = NauticalBackup(mockDockerClient)
        nb.backup()

        print(mockDockerClient.call_count)

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
