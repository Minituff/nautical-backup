import os
import pytest
from pathlib import Path
from mock import mock, MagicMock, patch
import datetime

from app.api.utils import next_cron_occurrences


class TestUtils:
    @classmethod
    def setup_class(cls):
        """
        Runs 1 time before all tests in this class
        """
        pass

    def test_next_cron_occurrences(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ):
        faked_now = datetime.datetime(2022, 1, 1, 14, 0, 0)
        assert next_cron_occurrences(1, faked_now) == {
            "cron": "0 4 * * *",
            "tz": "Etc/UTC",
            "1": ["Sunday, January 02, 2022 at 04:00 AM", "01/02/22 04:00"],
        }

        monkeypatch.setenv("CRON_SCHEDULE", "0 4 * * *")
        monkeypatch.setenv("TZ", "Etc/UTC")
        assert next_cron_occurrences(1, faked_now) == {
            "cron": "0 4 * * *",
            "tz": "Etc/UTC",
            "1": ["Sunday, January 02, 2022 at 04:00 AM", "01/02/22 04:00"],
        }

        faked_now = datetime.datetime(2023, 11, 1, 14, 0, 0)
        monkeypatch.setenv("CRON_SCHEDULE", "0 8 * * *")
        monkeypatch.setenv("TZ", "America/Phoenix")
        assert next_cron_occurrences(2, faked_now) == {
            "cron": "0 8 * * *",
            "tz": "America/Phoenix",
            "1": ["Thursday, November 02, 2023 at 08:00 AM", "11/02/23 08:00"],
            "2": ["Friday, November 03, 2023 at 08:00 AM", "11/03/23 08:00"],
        }

        assert next_cron_occurrences(-10, faked_now) == {
            "cron": "0 8 * * *",
            "tz": "America/Phoenix",
            "1": ["Thursday, November 02, 2023 at 08:00 AM", "11/02/23 08:00"],
        }

    def test_next_cron_occurrences_disabled(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ):
        monkeypatch.setenv("CRON_SCHEDULE_ENABLED", "false")
        faked_now = datetime.datetime(2022, 1, 1, 14, 0, 0)
        assert next_cron_occurrences(1, faked_now) == None
