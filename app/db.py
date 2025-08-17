import os
import json
from typing import Any, Optional, Union
from pathlib import Path
from app.logger import Logger, LogType, LogLevel
from datetime import datetime

# SQLAlchemy ORM for SQLite-backed key/value store
from sqlalchemy import JSON, String, create_engine, select
from sqlalchemy.exc import DatabaseError as SA_DatabaseError
import sqlite3
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


class Base(DeclarativeBase):
    pass


class KeyValue(Base):
    __tablename__ = "kv_store"

    key: Mapped[str] = mapped_column(String(255), primary_key=True)
    value: Mapped[Any] = mapped_column(JSON)


class DB:
    def __init__(self, db_path: Union[str, Path] = ""):
        self.db_path: str = str(db_path)
        if self.db_path == "":
            NAUTICAL_DB_PATH = os.getenv("NAUTICAL_DB_PATH", "/config")
            NAUTICAL_DB_NAME = os.getenv("NAUTICAL_DB_NAME", "nautical.db")
            self.db_path = f"{NAUTICAL_DB_PATH}/{NAUTICAL_DB_NAME}"
        self.logger = Logger()

        # If db_path is a folder (not a file), append the default db filename
        if os.path.exists(self.db_path) and not os.path.isfile(self.db_path):
            self.db_path += "/nautical.db"

        # Ensure parent directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        # Initialize engine and create tables, handle invalid pre-existing files
        self.engine = create_engine(f"sqlite:///{self.db_path}", future=True)
        try:
            Base.metadata.create_all(self.engine)
        except (SA_DatabaseError, sqlite3.DatabaseError):
            # If a non-SQLite file exists at path, remove and recreate
            try:
                if os.path.exists(self.db_path):
                    os.remove(self.db_path)
            except Exception:
                pass
            self.engine.dispose()
            self.engine = create_engine(f"sqlite:///{self.db_path}", future=True)
            Base.metadata.create_all(self.engine)

        # Log connect/init
        if os.path.isfile(self.db_path):
            self.log_this(f"Connected to SQLite database at '{self.db_path}'", log_type=LogType.INIT)
        else:
            self.log_this(f"Initializing SQLite database at '{self.db_path}'...", log_type=LogType.INIT)

        # Seed default keys
        self._seed_db()

    def __repr__(self) -> str:
        return str({"db_path": self.db_path, "db": dict(self._read_db())})

    def log_this(self, log_message, log_level=LogLevel.INFO, log_type: LogType = LogType.DEFAULT) -> None:
        """Wrapper for log this"""
        return self.logger.log_this(log_message, log_level, log_type)  # TODO: Fix

    def _initialize_db(self):
        """Deprecated: JSON file init replaced by SQLite ORM."""
        pass

    def _seed_db(self):
        """Seed the database with default values."""
        defaults = {
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "created_by_version": os.getenv("NAUTICAL_VERSION", "0.0.0"),
            "backup_running": False,
            "containers_skipped": 0,
            "containers_completed": 0,
            "number_of_containers": 0,
            "errors": 0,
        }

        with Session(self.engine) as session:
            for k, v in defaults.items():
                exists = session.get(KeyValue, k)
                if not exists:
                    session.add(KeyValue(key=k, value=v))
            session.commit()

    def _read_db(self):
        """Read all key/value pairs into a dict."""
        result: dict[str, Any] = {}
        with Session(self.engine) as session:
            for row in session.execute(select(KeyValue)).scalars().all():
                result[row.key] = row.value
        return result

    def _write_db(self, data):
        """Overwrite all keys with provided dict (used sparingly)."""
        with Session(self.engine) as session:
            # Upsert provided keys
            for k, v in data.items():
                obj = session.get(KeyValue, k)
                if obj:
                    obj.value = v
                else:
                    session.add(KeyValue(key=k, value=v))
            session.commit()

    def get(self, key: str, default=None):
        with Session(self.engine) as session:
            obj = session.get(KeyValue, key)
            return obj.value if obj is not None else default

    def put(self, key: str, value):
        with Session(self.engine) as session:
            obj = session.get(KeyValue, key)
            if obj:
                obj.value = value
            else:
                session.add(KeyValue(key=key, value=value))
            session.commit()

    def delete(self, key: str):
        with Session(self.engine) as session:
            obj = session.get(KeyValue, key)
            if obj:
                session.delete(obj)
                session.commit()

    def dump_json(self):
        return self._read_db()


if __name__ == "__main__":
    db = DB()  # This will seed and create the database if necessary (run at startup)
