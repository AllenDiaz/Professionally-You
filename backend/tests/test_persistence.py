"""Tests for conversation persistence and tool -> DB writes."""

from fastapi.testclient import TestClient

import app.routers.chat as chat_router
from app import crud
from app.db import SessionLocal
from app.main import app
from app.models import Conversation, Lead, Message, UnknownQuestion
from app.tools import record_unknown_question, record_user_details

client = TestClient(app)


def test_chat_persists_conversation_and_messages(monkeypatch):
    monkeypatch.setattr(chat_router, "run_chat", lambda *a, **k: "Hello there!")

    response = client.post("/api/chat", json={"message": "hi"})
    assert response.status_code == 200
    body = response.json()
    assert body["reply"] == "Hello there!"
    conversation_id = body["conversation_id"]

    with SessionLocal() as db:
        messages = db.query(Message).filter_by(conversation_id=conversation_id).all()
        roles = [(m.role, m.content) for m in messages]
    assert ("user", "hi") in roles
    assert ("assistant", "Hello there!") in roles


def test_chat_continues_existing_conversation(monkeypatch):
    monkeypatch.setattr(chat_router, "run_chat", lambda *a, **k: "ok")

    first = client.post("/api/chat", json={"message": "one"}).json()
    cid = first["conversation_id"]
    second = client.post("/api/chat", json={"message": "two", "conversation_id": cid}).json()

    assert second["conversation_id"] == cid
    with SessionLocal() as db:
        count = db.query(Message).filter_by(conversation_id=cid).count()
    assert count == 4  # two user + two assistant


def test_record_user_details_persists_lead(monkeypatch):
    monkeypatch.setattr("app.pushover.push", lambda text: None)

    with SessionLocal() as db:
        conversation = crud.get_or_create_conversation(db, None)
        db.commit()
        cid = conversation.id

    record_user_details(email="a@b.com", name="Ada", notes="keen", conversation_id=cid)

    with SessionLocal() as db:
        lead = db.query(Lead).one()
    assert lead.email == "a@b.com"
    assert lead.name == "Ada"
    assert lead.conversation_id == cid


def test_record_unknown_question_persists(monkeypatch):
    monkeypatch.setattr("app.pushover.push", lambda text: None)

    record_unknown_question(question="what is the meaning of life?")

    with SessionLocal() as db:
        unknown = db.query(UnknownQuestion).one()
    assert "meaning of life" in unknown.question
    assert unknown.conversation_id is None  # no conversation_id passed
