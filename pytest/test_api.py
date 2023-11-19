import os
import pytest
from pathlib import Path
from mock import mock, MagicMock, patch

from fastapi.testclient import TestClient

from api.db import DB
from api.utils import next_cron_occurrences
from api.config import Settings
from api.main import app
from api.authorize import get_settings

client = TestClient(app)


def get_settings_override() -> Settings:
    return Settings(
        HTTP_REST_API_USERNAME="new-username",
        HTTP_REST_API_PASSWORD="new-password",
    )


def get_settings_disable() -> Settings:
    return Settings(
        HTTP_REST_API_USERNAME="",
        HTTP_REST_API_PASSWORD="",
    )
    
def reset_settings_override() -> Settings:
    return Settings(
        HTTP_REST_API_USERNAME="admin",
        HTTP_REST_API_PASSWORD="password",
    )


class TestAPI:
    @classmethod
    def setup_class(cls):
        """Runs 1 time before all tests in this class"""
        app.dependency_overrides[get_settings] = reset_settings_override

    def test_root(self):
        response = client.get("/")
        assert response.status_code == 200

    def test_login_on_default_settings(self):
        response = client.get("/auth", auth=("admin", "password"))
        assert response.status_code == 200
        assert response.json() == {"username": "admin"}

        response = client.get("/auth", auth=("admin", "BAD"))
        assert response.status_code == 401

        response = client.get("/auth")
        assert response.status_code == 401

    def test_login_disable(self, monkeypatch: pytest.MonkeyPatch):
        # Apply the environment variable override
        app.dependency_overrides[get_settings] = get_settings_disable

        response = client.get("/auth", auth=("", ""))
        assert response.status_code == 200
        
        app.dependency_overrides[get_settings] = reset_settings_override

        
    def test_login_on_with_env(self, monkeypatch: pytest.MonkeyPatch):
        # Apply the environment variable override
        app.dependency_overrides[get_settings] = get_settings_override

        response = client.get("/auth", auth=("admin", "password"))
        assert response.status_code == 401

        response = client.get("/auth", auth=("new-username", "new-password"))
        assert response.status_code == 200
        assert response.json() == {"username": "new-username"}

        # Reset the override
        app.dependency_overrides[get_settings] = reset_settings_override

        response = client.get("/auth", auth=("admin", "password"))
        assert response.status_code == 200
        assert response.json() == {"username": "admin"}

    def test_dashboard(self):
        db = DB()
        response = client.get("/api/v1/nautical/dashboard", auth=("admin", "password"))
        assert response.status_code == 200
        
        
        assert response.json()["backup_running"] == db.get("backup_running", "false")
        assert response.json()["errors"] == db.get("errors", 0)
        assert response.json()["skipped"] == db.get("containers_skipped", 0)
        assert response.json()["completed"] == db.get("containers_completed", 0)
        assert response.json()["number_of_containers"] == db.get("number_of_containers", 0)
        assert response.json()["last_cron"] == db.get("last_cron", "None")
        assert len(response.json()["next_cron"]) == 7
        assert set(response.json()["next_cron"]) == set(next_cron_occurrences(5))
        
        
    @patch("subprocess.run")
    def test_start_backup(self, patched_subprocess_run):
        response = client.post("/api/v1/nautical/start_backup", auth=("admin", "password"))
        assert response.status_code == 200

    def test_next_cron(self):
        response = client.get("/api/v1/nautical/next_cron/1", auth=("admin", "password"))
        assert response.status_code == 200
