from fastapi.testclient import TestClient
import os
import pytest
from pathlib import Path
import base64

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
        # print(response)
        # assert response.json() == {
        #     "next_cron": next_cron_occurrences(5),
        #     "last_cron": db.get("last_cron", "None"),
        #     "number_of_containers": db.get("number_of_containers", 0),
        #     "completed": db.get("containers_completed", 0),
        #     "skipped": db.get("containers_skipped", 0),
        #     "errors": db.get("errors", 0),
        #     "backup_running": db.get("containers_skipped", "false"),
        # }

    # def test_get_items(self):
    #     response = client.get("/items")
    #     assert response.status_code == 200
    #     assert response.json() == ["Test Item 1", "Test Item 2", "Test Item 3"]

    # def test_remove_item(self):
    #     client.post("/items/remove")
    #     response = client.get("/items")
    #     assert response.status_code == 200
    #     assert response.json() == ["Test Item 1", "Test Item 2"]

    # def test_add_items(self):
    #     client.post("/items/add")
    #     response = client.get("/items")
    #     assert response.status_code == 200
    #     assert response.json() == ["Test Item 1", "Test Item 2", "Item 3"]

    # def test_reset(self):
    #     client.post("/items/reset")
    #     response = client.get("/items")
    #     assert response.status_code == 200
    #     assert response.json() == ["Default Item 1", "Default Item 2", "Default Item 3"]

    # def test_clear(self):
    #     client.post("/items/clear")
    #     response = client.get("/items")
    #     assert response.status_code == 200
    #     assert response.json() == []
