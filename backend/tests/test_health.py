"""Tests for the health endpoint."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_ok():
    response = client.get("/api/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert set(body) == {"status", "vertex_configured", "pushover_configured", "model"}
    assert isinstance(body["vertex_configured"], bool)
    assert isinstance(body["pushover_configured"], bool)
