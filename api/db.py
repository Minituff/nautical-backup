import os
import json
from typing import Any, Optional, Union
from pathlib import Path


class DB:
    def __init__(self, db_path: Union[str, Path] = ""):
        self.db_path: str = str(db_path)
        if self.db_path == "":
            NAUTICAL_DB_PATH = os.getenv("NAUTICAL_DB_PATH", "/config")
            NAUTICAL_DB_NAME = os.getenv("NAUTICAL_DB_NAME", "nautical-db.json")
            self.db_path = f"{NAUTICAL_DB_PATH}/{NAUTICAL_DB_NAME}"

        if os.path.exists(self.db_path) and not os.path.isfile(self.db_path):
            # If db_path is a folder (not a file), just make it a file
            self.db_path += "/nautical-db.json"

        self._initialize_db()
        self._seed_db()

    def __repr__(self) -> str:
        return str({"db_path": self.db_path, "db": dict(self._read_db())})

    def _initialize_db(self):
        """Initialize the database if it doesn't exist."""
        if os.path.isfile(self.db_path):
            print(f"Connected to database at '{self.db_path}'")
        else:
            print(f"Initializing database at '{self.db_path}'...")
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

            if not os.path.isfile(self.db_path):
                print(f"Creating Database at path: '{self.db_path}'...")
                with open(self.db_path, "w") as db_file:
                    json.dump({}, db_file)

                print(f"Database initialized at '{self.db_path}'...")

    def _seed_db(self):
        """Seed the database with default values."""
        with open(self.db_path, "r+") as db_file:
            data = json.load(db_file)

            if data.get("backup_running") is None:
                data["backup_running"] = False

            if data.get("containers_skipped") is None:
                data["containers_skipped"] = 0

            if data.get("containers_completed") is None:
                data["containers_completed"] = 0

            if data.get("number_of_containers") is None:
                data["number_of_containers"] = 0

            if data.get("errors") is None:
                data["errors"] = 0

            db_file.seek(0)
            json.dump(data, db_file, indent=4)
            db_file.truncate()

    def _read_db(self):
        if os.path.exists(self.db_path) and os.path.isfile(self.db_path):
            with open(self.db_path, "r") as f:
                return json.load(f)
        else:
            return {}

    def _write_db(self, data):
        with open(self.db_path, "w") as f:
            json.dump(data, f, indent=4)

    def get(self, key: str, default=None):
        data = self._read_db()
        return data.get(key, default)

    def put(self, key: str, value):
        data = self._read_db()
        data[key] = value
        self._write_db(data)

    def delete(self, key: str):
        data = self._read_db()
        if key in data:
            del data[key]
            self._write_db(data)

    def dump_json(self):
        return self._read_db()
