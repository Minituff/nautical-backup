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


class TestNauticalEnv:
    @classmethod
    def setup_class(cls):
        """Runs 1 time before all tests in this class"""
        pass

    def test_populate_override_dirs(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("OVERRIDE_SOURCE_DIR", "example1:example1-new-source-data,ctr2:ctr2-new-source")
        monkeypatch.setenv("OVERRIDE_DEST_DIR", "example3:example3-new-deste-data,ctr4:ctr4-new-dest")
        nautical_env = NauticalEnv()

        assert nautical_env.OVERRIDE_SOURCE_DIR == {"example1": "example1-new-source-data", "ctr2": "ctr2-new-source"}

        assert "example1" in nautical_env.OVERRIDE_SOURCE_DIR
        assert "fake" not in nautical_env.OVERRIDE_SOURCE_DIR

        assert nautical_env.OVERRIDE_DEST_DIR == {"example3": "example3-new-deste-data", "ctr4": "ctr4-new-dest"}

        assert "example3" in nautical_env.OVERRIDE_DEST_DIR
        assert "fake" not in nautical_env.OVERRIDE_DEST_DIR
