"""Tests for per-IP rate limiting on the chat endpoints."""

from fastapi.testclient import TestClient

import app.routers.chat as chat_router
from app.config import get_settings
from app.main import app

client = TestClient(app)


def test_chat_rate_limit_blocks_excess_requests(monkeypatch):
    monkeypatch.setattr(get_settings(), "chat_rate_limit", "1/minute")
    monkeypatch.setattr(chat_router, "run_chat", lambda *a, **k: "ok")

    statuses = [client.post("/api/chat", json={"message": "hi"}).status_code for _ in range(5)]

    assert 429 in statuses
    assert all(status in (200, 429) for status in statuses)
