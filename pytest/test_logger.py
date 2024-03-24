from datetime import datetime
import os
import pytest
from pathlib import Path
from mock import mock, MagicMock, patch
from app.logger import Logger, LogLevel


    
class TestBackup:
    @classmethod
    def setup_class(cls):
        """Runs 1 time before all tests in this class"""
        pass
    
    def test_init_(self,monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("LOG_LEVEL", "INFO")
        monkeypatch.setenv("REPORT_FILE_LOG_LEVEL", "INFO")
        monkeypatch.setenv("REPORT_FILE_ON_BACKUP_ONLY", "TRUE")
        monkeypatch.setenv("DEST_LOCATION", "/app/destination")
        
        logger = Logger()
        assert logger.script_logging_level is LogLevel.INFO
        assert logger.report_file_logging_level is LogLevel.INFO
        assert logger.report_file_on_backup_only is True
        assert logger.dest_location == "/app/destination"
        
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        monkeypatch.setenv("REPORT_FILE_LOG_LEVEL", "DEBUG")
        monkeypatch.setenv("REPORT_FILE_ON_BACKUP_ONLY", "FALSE")
        
        logger = Logger()
        assert logger.script_logging_level is LogLevel.DEBUG
        assert logger.report_file_logging_level is LogLevel.DEBUG
        assert logger.report_file_on_backup_only is False
        
        monkeypatch.setenv("LOG_LEVEL", "")
        monkeypatch.setenv("REPORT_FILE_LOG_LEVEL", "")
        monkeypatch.setenv("REPORT_FILE_ON_BACKUP_ONLY", "")
        
        logger = Logger()
        assert logger.script_logging_level is LogLevel.INFO
        assert logger.report_file_logging_level is LogLevel.INFO
        assert logger.report_file_on_backup_only is True
        
        rf = f"Backup Report - {datetime.now().strftime('%Y-%m-%d')}.txt"
        assert logger.report_file == rf