# tests/test_main.py
"""Test main application endpoints"""
from fastapi.testclient import TestClient


def test_read_root(client: TestClient):
    """Test root endpoint"""
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Welcome to Morse-Me!"
    assert data["status"] == "running"


def test_health_check(client: TestClient):
    """Test health check endpoint"""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "app" in data


def test_404_endpoint(client: TestClient):
    """Test non-existent endpoint returns 404"""
    response = client.get("/nonexistent-endpoint")

    assert response.status_code == 404