import pytest
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["status"] == "ok"
    assert "timestamp" in data


def test_devices_endpoint(client):
    response = client.get("/api/devices")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "devices" in data
    assert isinstance(data["devices"], list)


def test_sessions_endpoint(client):
    response = client.get("/api/sessions")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "sessions" in data
    assert "metrics" in data
