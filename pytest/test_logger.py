from datetime import datetime
import os
import pytest
from pathlib import Path
from mock import mock, MagicMock, patch
from app.logger import LogType, Logger, LogLevel
import pytest
from datetime import datetime


class TestLogger:
    @classmethod
    def setup_class(cls):
        """Runs 1 time before all tests in this class"""
        pass

    def test_init_(self, monkeypatch: pytest.MonkeyPatch):
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

    @patch("builtins.open", new_callable=MagicMock)
    def test_create_report_file(self, mock_open: MagicMock, tmp_path: Path):
        logger = Logger()
        logger.dest_location = tmp_path
        logger.report_file = "mock_report_file.txt"

        mock_path = tmp_path / logger.report_file

        # Call log_this
        logger.log_this("mock_message", LogLevel.WARN)

        # Check that the message was written to the report file
        mock_open.assert_called_once_with(str(mock_path), "a")

    @patch("builtins.open", new_callable=MagicMock)
    @patch("builtins.print")
    def test_log_level_trace(
        self, mock_print: MagicMock, mock_open: MagicMock, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.setenv("LOG_LEVEL", "TRACE")
        monkeypatch.setenv("REPORT_FILE_LOG_LEVEL", "TRACE")

        logger = Logger()
        logger.dest_location = tmp_path
        logger.report_file = "mock_report_file.txt"
        logger.report_file_on_backup_only = False

        # Call log_this
        logger.log_this("mock_trace", LogLevel.TRACE, LogType.DEFAULT)
        logger.log_this("mock_debug", LogLevel.DEBUG, LogType.DEFAULT)
        logger.log_this("mock_info", LogLevel.INFO, LogType.DEFAULT)
        logger.log_this("mock_warn", LogLevel.WARN, LogType.DEFAULT)
        logger.log_this("mock_error", LogLevel.ERROR, LogType.DEFAULT)

        assert mock_open.call_count == 5
        assert mock_print.call_count == 5

        assert mock_print.call_args_list[0][0][0] == "TRACE: mock_trace"
        assert mock_print.call_args_list[1][0][0] == "DEBUG: mock_debug"
        assert mock_print.call_args_list[2][0][0] == "INFO: mock_info"
        assert mock_print.call_args_list[3][0][0] == "WARN: mock_warn"
        assert mock_print.call_args_list[4][0][0] == "ERROR: mock_error"

    @patch("builtins.open", new_callable=MagicMock)
    @patch("builtins.print")
    def test_log_level_debug(
        self, mock_print: MagicMock, mock_open: MagicMock, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        monkeypatch.setenv("REPORT_FILE_LOG_LEVEL", "DEBUG")

        logger = Logger()
        logger.dest_location = tmp_path
        logger.report_file = "mock_report_file.txt"

        # Call log_this
        logger.log_this("mock_trace", LogLevel.TRACE)
        logger.log_this("mock_debug", LogLevel.DEBUG)
        logger.log_this("mock_info", LogLevel.INFO)
        logger.log_this("mock_warn", LogLevel.WARN)
        logger.log_this("mock_error", LogLevel.ERROR)

        assert mock_print.call_count == 4
        assert mock_open.call_count == 4

        assert mock_print.call_args_list[0][0][0] == "DEBUG: mock_debug"
        assert mock_print.call_args_list[1][0][0] == "INFO: mock_info"
        assert mock_print.call_args_list[2][0][0] == "WARN: mock_warn"
        assert mock_print.call_args_list[3][0][0] == "ERROR: mock_error"

    @patch("builtins.open", new_callable=MagicMock)
    @patch("builtins.print")
    def test_log_level_info(
        self, mock_print: MagicMock, mock_open: MagicMock, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.setenv("LOG_LEVEL", "INFO")
        monkeypatch.setenv("REPORT_FILE_LOG_LEVEL", "INFO")

        logger = Logger()
        logger.dest_location = tmp_path
        logger.report_file = "mock_report_file.txt"

        # Call log_this
        logger.log_this("mock_trace", LogLevel.TRACE)
        logger.log_this("mock_debug", LogLevel.DEBUG)
        logger.log_this("mock_info", LogLevel.INFO)
        logger.log_this("mock_warn", LogLevel.WARN)
        logger.log_this("mock_error", LogLevel.ERROR)

        assert mock_print.call_count == 3
        assert mock_open.call_count == 3

        assert mock_print.call_args_list[0][0][0] == "INFO: mock_info"
        assert mock_print.call_args_list[1][0][0] == "WARN: mock_warn"
        assert mock_print.call_args_list[2][0][0] == "ERROR: mock_error"

    @patch("builtins.open", new_callable=MagicMock)
    @patch("builtins.print")
    def test_log_level_warn(
        self, mock_print: MagicMock, mock_open: MagicMock, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.setenv("LOG_LEVEL", "WARN")
        monkeypatch.setenv("REPORT_FILE_LOG_LEVEL", "WARN")

        logger = Logger()
        logger.dest_location = tmp_path
        logger.report_file = "mock_report_file.txt"

        # Call log_this
        logger.log_this("mock_trace", LogLevel.TRACE)
        logger.log_this("mock_debug", LogLevel.DEBUG)
        logger.log_this("mock_info", LogLevel.INFO)
        logger.log_this("mock_warn", LogLevel.WARN)
        logger.log_this("mock_error", LogLevel.ERROR)

        assert mock_print.call_count == 2
        assert mock_open.call_count == 2

        assert mock_print.call_args_list[0][0][0] == "WARN: mock_warn"
        assert mock_print.call_args_list[1][0][0] == "ERROR: mock_error"

    @patch("builtins.open", new_callable=MagicMock)
    @patch("builtins.print")
    def test_log_level_error(
        self, mock_print: MagicMock, mock_open: MagicMock, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.setenv("LOG_LEVEL", "ERROR")
        monkeypatch.setenv("REPORT_FILE_LOG_LEVEL", "ERROR")

        logger = Logger()
        logger.dest_location = tmp_path
        logger.report_file = "mock_report_file.txt"

        # Call log_this
        logger.log_this("mock_trace", LogLevel.TRACE)
        logger.log_this("mock_debug", LogLevel.DEBUG)
        logger.log_this("mock_info", LogLevel.INFO)
        logger.log_this("mock_warn", LogLevel.WARN)
        logger.log_this("mock_error", LogLevel.ERROR)

        assert mock_print.call_count == 1
        assert mock_open.call_count == 1

        assert mock_print.call_args_list[0][0][0] == "ERROR: mock_error"

    @patch("builtins.open", new_callable=MagicMock)
    @patch("builtins.print")
    def test_differnt_log_levels(
        self, mock_print: MagicMock, mock_open: MagicMock, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        monkeypatch.setenv("REPORT_FILE_LOG_LEVEL", "ERROR")

        logger = Logger()
        logger.dest_location = tmp_path
        logger.report_file = "mock_report_file.txt"

        # Call log_this
        logger.log_this("mock_trace", LogLevel.TRACE)
        logger.log_this("mock_debug", LogLevel.DEBUG)
        logger.log_this("mock_info", LogLevel.INFO)
        logger.log_this("mock_warn", LogLevel.WARN)
        logger.log_this("mock_error", LogLevel.ERROR)

        assert mock_print.call_count == 4
        assert mock_open.call_count == 1

    @patch("builtins.open", new_callable=MagicMock)
    @patch("builtins.print")
    def test_differnt_log_levels2(
        self, mock_print: MagicMock, mock_open: MagicMock, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        monkeypatch.setenv("LOG_LEVEL", "WARN")
        monkeypatch.setenv("REPORT_FILE_LOG_LEVEL", "INFO")

        logger = Logger()
        logger.dest_location = tmp_path
        logger.report_file = "mock_report_file.txt"

        # Call log_this
        logger.log_this("mock_trace", LogLevel.TRACE)
        logger.log_this("mock_debug", LogLevel.DEBUG)
        logger.log_this("mock_info", LogLevel.INFO)
        logger.log_this("mock_warn", LogLevel.WARN)
        logger.log_this("mock_error", LogLevel.ERROR)

        assert mock_print.call_count == 2
        assert mock_open.call_count == 3

    @patch("builtins.print")
    def test_print(self, mock_print: MagicMock, tmp_path: Path):
        logger = Logger()
        logger.dest_location = tmp_path
        logger.report_file = "mock_report_file.txt"

        # Call log_this
        logger.log_this("mock_message", LogLevel.WARN)

        assert mock_print.call_args[0][0] == "WARN: mock_message"
