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
        self.report_file = f"Backup Report - {datetime.datetime.now().strftime('%Y-%m-%d')}.txt"

    @staticmethod
    def set_to_string(input: set) -> str:
        """Converts a set to a string with comma separated values."""
        return ", ".join(str(i) for i in input)

    @staticmethod
    def _parse_log_level(log_level: str) -> Optional[LogLevel]:
        # Override the defaults with environment variables if they exist
        if log_level.lower() == "trace":
            return LogLevel.TRACE
        elif log_level.lower() == "debug":
            return LogLevel.DEBUG
        elif log_level.lower() == "info":
            return LogLevel.INFO
        elif log_level.lower() == "warn":
            return LogLevel.WARN
        elif log_level.lower() == "error":
            return LogLevel.ERROR
        return None

    def _delete_old_report_files(self):
        """Only completed on Nautical init"""
        if not os.path.exists(self.dest_location):
            return

        for file in os.listdir(self.dest_location):
            file.strip()
            if file.startswith("Backup Report -") and file.endswith(".txt"):
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
            f.write(f"Backup Report - {datetime.datetime.now()}\n")

    def log_this(self, log_message, log_level: Union[str, LogLevel] = LogLevel.INFO, log_type=LogType.DEFAULT):
        # Check if level exists
        log_level = self._parse_log_level(str(log_level)) or log_level
        if log_level not in self.levels:
            return

        # Check if level is enough for console logging
        if self.levels[log_level] >= self.levels[self.script_logging_level]:
            print(f"{str(log_level)[9:]}: {log_message}")

        # Check if level is enough for report file logging
        if self.levels[log_level] >= self.levels[self.report_file_logging_level]:
            if self.report_file_on_backup_only == False or log_type == LogType.DEFAULT:
                if not os.path.exists(os.path.join(self.dest_location, self.report_file)):
                    self._create_new_report_file()
                with open(os.path.join(self.dest_location, self.report_file), "a") as f:
                    f.write(f"{datetime.datetime.now()} - {str(log_level)[9:]}: {log_message}\n")
