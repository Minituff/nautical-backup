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

    def _read_db(self):
        if os.path.exists(self.db_path) and os.path.isfile(self.db_path):
            with open(self.db_path, "r") as f:
                return json.load(f)
        else:
            return {}

    def _write_db(self, data):
        with open(self.db_path, "w") as f:
            json.dump(data, f, indent=4)

    def get(self, key, default=None):
        data = self._read_db()
        return data.get(key, default)

    def put(self, key, value):
        data = self._read_db()
        data[key] = value
        self._write_db(data)

    def delete(self, key):
        data = self._read_db()
        if key in data:
            del data[key]
            self._write_db(data)

    def dump_json(self):
        return self._read_db()
