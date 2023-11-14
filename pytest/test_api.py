from fastapi.testclient import TestClient
import os
import pytest
from pathlib import Path
from api.main import app
from api.db import DB
from api.utils import next_cron_occurrences

client = TestClient(app)


class TestAPI:
    @classmethod
    def setup_class(cls):
        """
        Runs 1 time before all tests in this class

        This will delete the inventory.json` and add test items.
        """
        pass

    def test_root(self):
        response = client.get("/")
        assert response.status_code == 200

    # def test_login(self, client, test_user):
    #     response = client.get("/auth", data=test_user)
    #     assert response.status_code == 200
    #     token = response.json()["access_token"]
    #     assert token is not None
    #     return token

    # def test_dashboard(self):
    #     db = DB()
    #     response = client.get("/api/v1/nautical/dashboard", auth=)
    #     assert response.status_code == 200
    #     assert response.json() == {
    #         "next_cron": next_cron_occurrences(5),
    #         "last_cron": db.get("last_cron", "None"),
    #         "number_of_containers": db.get("number_of_containers", 0),
    #         "completed": db.get("containers_completed", 0),
    #         "skipped": db.get("containers_skipped", 0),
    #         "errors": db.get("errors", 0),
    #         "backup_running": db.get("containers_skipped", "false"),
    #     }

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
