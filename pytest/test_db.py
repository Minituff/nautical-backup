import os
from api.db import DB
import pytest
from pathlib import Path


class TestADB:
    @classmethod
    def setup_class(cls):
        """
        Runs 1 time before all tests in this class
        """
        pass

    def test_read_invalid_db(self, tmp_path: Path):
        db = DB(tmp_path)  # This is a folder, so it is invalid
        assert db.get("test") == None
        assert db.get("test", {}) == {}

    def test_db_paths(self, tmp_path: Path):
        db = DB(os.path.join(tmp_path, "test-db.json"))
        assert db.db_path.endswith("test-db.json")

        db = DB(tmp_path)
        assert db.db_path.endswith("nautical-db.json")

    def test_db_get(self, tmp_path):
        db = DB(tmp_path)
        db.put("test", "testVal")
        assert db.get("test") == "testVal"

    def test_db_get_override(self, tmp_path):
        db = DB(tmp_path)

        val = {"value": 1, "value2": True, "value3": "value3"}
        db.put("test", val)

        assert db.get("test") == val

        db.put("test", "override")
        assert db.get("test") == "override"

    def test_db_delete(self, tmp_path):
        db = DB(tmp_path)
        db.put("test", "testVal")
        assert db.get("test") == "testVal"

        db.put("test", "")
        assert db.get("test") == ""

        db.delete("test")
        assert db.get("test") == None

    @pytest.fixture(scope="function", autouse=True)
    def test_db_env(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("NAUTICAL_DB_PATH", "fake-path")
        monkeypatch.setenv("NAUTICAL_DB_NAME", "test-db.json")

        db = DB()
        assert db.db_path == "fake-path/test-db.json"

        monkeypatch.setenv("NAUTICAL_DB_PATH", "fake-path2")
        monkeypatch.setenv("NAUTICAL_DB_NAME", "test-db2.json")

        db = DB()
        assert db.db_path == "fake-path2/test-db2.json"

        monkeypatch.setenv("NAUTICAL_DB_PATH", "fake-path3")
        # Should not be used since we only pass a folder. the default name should be used
        monkeypatch.setenv("NAUTICAL_DB_NAME", "test-db3.json")
        db = DB(tmp_path)
        assert db.db_path.endswith("nautical-db.json")
