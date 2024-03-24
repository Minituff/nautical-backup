import datetime
import os
from typing import Optional
from app.nautical_env import NauticalEnv
from enum import Enum

class LogLevel(Enum):
    TRACE = 0
    DEBUG = 1
    INFO = 2
    WARN = 3
    ERROR = 4
    
class Logger:
    def __init__(self):
        self.levels = {LogLevel.TRACE: 0, LogLevel.DEBUG: 1, LogLevel.INFO: 2, LogLevel.WARN: 3, LogLevel.ERROR: 4}
        self.env = NauticalEnv()
        
        # Defaults
        self.script_logging_level: LogLevel = LogLevel.INFO
        self.report_file_logging_level = LogLevel.INFO
        self.report_file_on_backup_only: bool = True


        self.script_logging_level = self._parse_log_level(self.env.LOG_LEVEL) or self.script_logging_level
        self.report_file_logging_level = self._parse_log_level(self.env.REPORT_FILE_LOG_LEVEL) or self.report_file_logging_level    
        
        if self.env.REPORT_FILE_ON_BACKUP_ONLY.lower() == "true":
            self.report_file_on_backup_only = True
        elif self.env.REPORT_FILE_ON_BACKUP_ONLY.lower() == "false":
            self.report_file_on_backup_only = False
            
        self.dest_location = os.environ.get("DEST_LOCATION", "")
        self.report_file = f"Backup Report - {datetime.datetime.now().strftime('%Y-%m-%d')}.txt"
   
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
        
    def delete_report_file(self):
        for file in os.listdir(self.dest_location):
            if file.startswith("Backup Report -") and file.endswith(".txt"):
                os.remove(os.path.join(self.dest_location, file))

    def create_new_report_file(self):
        if self.report_file_on_backup_only == True:
            self.delete_report_file()
            # Initialize the current report file with a header
            with open(os.path.join(self.dest_location, self.report_file), 'w') as f:
                f.write(f"Backup Report - {datetime.datetime.now()}\n")

    def log_this(self, log_message, log_priority="INFO", message_type="default"):
        # Check if level exists
        if log_priority not in self.levels:
            return

        # Check if level is enough for console logging
        if self.levels[log_priority] >= self.levels[self.script_logging_level]:
            print(f"{log_priority}: {log_message}")

        # Check if level is enough for report file logging
        if self.report_file_on_backup_only == "true" and self.levels[log_priority] >= self.levels[self.report_file_logging_level]:
            if not (message_type == "init" and self.report_file_on_backup_only == "true"):
                with open(os.path.join(self.dest_location, self.report_file), 'a') as f:
                    f.write(f"{datetime.datetime.now()} - {log_priority}: {log_message}\n")

if __name__ == "__main__":
    # Example usage
    logger = Logger()
    logger.create_new_report_file()
    logger.log_this("This is an info message")
    logger.log_this("This is a debug message", log_priority="DEBUG")
