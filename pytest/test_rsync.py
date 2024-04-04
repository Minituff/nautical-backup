import pytest
from pathlib import Path
from mock import PropertyMock, mock, MagicMock, patch
from pathlib import Path

from app.nautical_env import NauticalEnv

        
        
# class TestRsync:
#     def test_rsync_commands(self, monkeypatch: pytest.MonkeyPatch):

#         # Define the source location
#         monkeypatch.setenv("DEST_LOCATION", "./tests/destination")
#         monkeypatch.setenv("SOURCE_LOCATION", "./tests/source")

#         env = NauticalEnv()
#         SOURCE_LOCATION = env.SOURCE_LOCATION

#         # Create directories and files
#         Path(SOURCE_LOCATION, "container1").mkdir(parents=True, exist_ok=True)
#         Path(SOURCE_LOCATION, "container1", "test.txt").touch()

#         Path(SOURCE_LOCATION, "container2").mkdir(parents=True, exist_ok=True)
#         Path(SOURCE_LOCATION, "container1", "test.txt").touch()
