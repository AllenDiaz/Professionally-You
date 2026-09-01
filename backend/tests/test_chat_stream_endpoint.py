"""Tests for the SSE streaming chat endpoint."""

import json

from fastapi.testclient import TestClient

import app.routers.chat as chat_router
from app.db import SessionLocal
from app.main import app
from app.models import Message

client = TestClient(app)


def _fake_stream(message, history=None, conversation_id=None):
    yield "Hel"
    yield "lo!"


def _parse_sse(body: str) -> list[dict]:
    return [
        json.loads(line[len("data: ") :])
        for line in body.splitlines()
        if line.startswith("data: ")
    ]


def test_stream_endpoint_emits_sse_and_persists(monkeypatch):
    monkeypatch.setattr(chat_router, "stream_chat", _fake_stream)

    with client.stream("POST", "/api/chat/stream", json={"message": "hi"}) as response:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        body = "".join(response.iter_text())

    events = _parse_sse(body)
    deltas = "".join(e["delta"] for e in events if "delta" in e)
    assert deltas == "Hello!"

    done_events = [e for e in events if e.get("done")]
    assert done_events
    conversation_id = done_events[0]["conversation_id"]

    with SessionLocal() as db:
        messages = db.query(Message).filter_by(conversation_id=conversation_id).all()
    roles_content = [(m.role, m.content) for m in messages]
    assert ("user", "hi") in roles_content
    assert ("assistant", "Hello!") in roles_content


def test_stream_endpoint_continues_existing_conversation(monkeypatch):
    monkeypatch.setattr(chat_router, "stream_chat", _fake_stream)

    with client.stream("POST", "/api/chat/stream", json={"message": "one"}) as response:
        events = _parse_sse("".join(response.iter_text()))
    cid = [e for e in events if e.get("done")][0]["conversation_id"]

    with client.stream(
        "POST", "/api/chat/stream", json={"message": "two", "conversation_id": cid}
    ) as response:
        events = _parse_sse("".join(response.iter_text()))
    assert [e for e in events if e.get("done")][0]["conversation_id"] == cid

    with SessionLocal() as db:
        count = db.query(Message).filter_by(conversation_id=cid).count()
    assert count == 4  # two user + two assistant turns
