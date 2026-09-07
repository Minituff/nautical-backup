import datetime
import os
from pathlib import Path
from typing import Optional, Union
from app.nautical_env import NauticalEnv
from enum import Enum


class LogLevel(Enum):
    TRACE = 0
    DEBUG = 1
    INFO = 2
    WARN = 3
    ERROR = 4


class LogType(Enum):
    INIT = 0
    DEFAULT = 1


class Logger:
    DEFAULT_REPORT_FILE_PREFIX = "Backup Report"
    # All of these are treated as equivalent placeholders for LABEL_PREFIX,
    # so users can use whichever spelling reads naturally in REPORT_FILE_NAME.
    PREFIX_TOKENS = ("{label_prefix}", "{LABEL_PREFIX}", "{prefix}", "{PREFIX}")

    def __init__(self):
        self.levels = {LogLevel.TRACE: 0, LogLevel.DEBUG: 1, LogLevel.INFO: 2, LogLevel.WARN: 3, LogLevel.ERROR: 4}
        self.env = NauticalEnv()

        # Defaults
        self.script_logging_level: LogLevel = LogLevel.INFO
        self.report_file_logging_level = LogLevel.INFO
        self.report_file_on_backup_only: bool = True

        self.script_logging_level = self._parse_log_level(self.env.LOG_LEVEL) or self.script_logging_level
        self.report_file_logging_level = (
            self._parse_log_level(self.env.REPORT_FILE_LOG_LEVEL) or self.report_file_logging_level
        )

        if self.env.REPORT_FILE_ON_BACKUP_ONLY.lower() == "true":
            self.report_file_on_backup_only = True
        elif self.env.REPORT_FILE_ON_BACKUP_ONLY.lower() == "false":
            self.report_file_on_backup_only = False

        self.dest_location: Union[str, Path] = os.environ.get("DEST_LOCATION", "")
        self.report_file_prefix = self._resolve_report_file_prefix(self.env.REPORT_FILE_NAME)
        self.report_file = f"{self.report_file_prefix} - {datetime.datetime.now().strftime('%Y-%m-%d')}.txt"

    @staticmethod
    def set_to_string(input: set) -> str:
        """Converts a set to a string with comma separated values."""
        return ", ".join(str(i) for i in input)

    @staticmethod
    def _parse_log_level(log_level: Union[str, LogLevel]) -> Optional[LogLevel]:
        if isinstance(log_level, LogLevel):
            return log_level

        # Map a string log level to LogLevel, returning None for unknown values.
        if log_level.lower().strip() == "trace":
            return LogLevel.TRACE
        elif log_level.lower().strip() == "debug":
            return LogLevel.DEBUG
        elif log_level.lower().strip() == "info":
            return LogLevel.INFO
        elif log_level.lower().strip() == "warn":
            return LogLevel.WARN
        elif log_level.lower().strip() == "error":
            return LogLevel.ERROR
        return None

    def _resolve_report_file_prefix(self, report_file_name: str) -> str:
        """Turn REPORT_FILE_NAME into a safe report file prefix.

        Falls back to the default prefix (and warns) if REPORT_FILE_NAME is unset,
        or if it would escape dest_location via a path separator or "..".
        """
        prefix = report_file_name.strip()
        if not prefix:
            return self.DEFAULT_REPORT_FILE_PREFIX

        for token in self.PREFIX_TOKENS:
            prefix = prefix.replace(token, self.env.LABEL_PREFIX)

        if "/" in prefix or "\\" in prefix or ".." in prefix:
            print(
                f"WARN: Invalid REPORT_FILE_NAME '{report_file_name}' (must not contain "
                f"'/', '\\', or '..'); falling back to the default report file name."
            )
            return self.DEFAULT_REPORT_FILE_PREFIX

        return prefix

    def _delete_old_report_files(self):
        """Only completed on Nautical init"""
        if not os.path.exists(self.dest_location):
            return

        prefix = f"{self.report_file_prefix} - "
        for file in os.listdir(self.dest_location):
            file.strip()
            if file.startswith(prefix) and file.endswith(".txt"):
                if file != self.report_file:
                    # Don't delete today's report file
                    os.remove(os.path.join(self.dest_location, file))

    def _create_new_report_file(self):
        """Only completed on Nautical init"""
        self._delete_old_report_files()

        if not os.path.exists(self.dest_location):
            raise FileNotFoundError(f"Destination location {self.dest_location} does not exist.")

        # Initialize the current report file with a header
        with open(os.path.join(self.dest_location, self.report_file), "w+") as f:
            f.write(f"{self.report_file_prefix} - {datetime.datetime.now()}\n")

    def _write_to_report_file(self, log_message, log_level: Union[str, LogLevel] = LogLevel.INFO):
        level = self._parse_log_level(log_level)
        if level not in self.levels:
            return  # Check if level exists

        # Check if folder exists
        if not os.path.exists(self.dest_location):
            raise FileNotFoundError(f"Destination location {self.dest_location} does not exist.")

        with open(os.path.join(self.dest_location, self.report_file), "a") as f:
            f.write(f"{datetime.datetime.now()} - {str(level)[9:]}: {log_message}\n")

    def log_this(self, log_message, log_level: Union[str, LogLevel] = LogLevel.INFO, log_type=LogType.DEFAULT):

        level = self._parse_log_level(log_level)
        if level not in self.levels:
            return  # Check if level exists

        # Check if level is enough for console logging
        if self.levels[level] >= self.levels[self.script_logging_level]:
            print(f"{str(level)[9:]}: {log_message}")

        if self.env.REPORT_FILE == False:
            return

        # Check if level is enough for report file logging
        if self.levels[level] >= self.levels[self.report_file_logging_level]:
            if self.report_file_on_backup_only == True:
                if log_type != LogType.INIT:
                    self._write_to_report_file(log_message, log_level)
            else:
                # Always write to report file
                self._write_to_report_file(log_message, log_level)
