from fastapi.testclient import TestClient
import os
from pathlib import Path
from api.main import app
import pytest

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

    # @pytest.mark.it("Test base test-api is accessible")
    # def test_read_main(self):
    #     response = client.get("/test")
    #     assert response.status_code == 200
    #     assert response.json() == {"msg": "Hello World"}

    # @pytest.mark.it("Test getting items")
    # def test_get_items(self):
    #     response = client.get("/items")
    #     assert response.status_code == 200
    #     assert response.json() == ["Test Item 1", "Test Item 2", "Test Item 3"]

    # @pytest.mark.it("Test remove item")
    # def test_remove_item(self):
    #     client.post("/items/remove")
    #     response = client.get("/items")
    #     assert response.status_code == 200
    #     assert response.json() == ["Test Item 1", "Test Item 2"]

    # @pytest.mark.it("Test add item")
    # def test_add_items(self):
    #     client.post("/items/add")
    #     response = client.get("/items")
    #     assert response.status_code == 200
    #     assert response.json() == ["Test Item 1", "Test Item 2", "Item 3"]

    # @pytest.mark.it("Test reset items")
    # def test_reset(self):
    #     client.post("/items/reset")
    #     response = client.get("/items")
    #     assert response.status_code == 200
    #     assert response.json() == ["Default Item 1", "Default Item 2", "Default Item 3"]

    # @pytest.mark.it("Test clear all items")
    # def test_clear(self):
    #     client.post("/items/clear")
    #     response = client.get("/items")
    #     assert response.status_code == 200
    #     assert response.json() == []
