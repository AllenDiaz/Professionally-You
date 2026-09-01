"""Tests for the token-guarded admin API."""

from fastapi.testclient import TestClient

from app.crud import add_lead, add_unknown_question
from app.db import SessionLocal
from app.main import app

client = TestClient(app)
AUTH = {"Authorization": "Bearer test-admin-token"}


def _seed():
    with SessionLocal() as db:
        add_lead(db, email="lead@x.com", name="Lead", notes="hi")
        add_unknown_question(db, question="unanswered?")
        db.commit()


def test_admin_requires_token():
    assert client.get("/api/admin/leads").status_code == 401
    assert client.get("/api/admin/leads", headers={"Authorization": "Bearer wrong"}).status_code == 401


def test_admin_lists_leads():
    _seed()
    response = client.get("/api/admin/leads", headers=AUTH)
    assert response.status_code == 200
    leads = response.json()
    assert len(leads) == 1
    assert leads[0]["email"] == "lead@x.com"


def test_admin_lists_unknown_questions():
    _seed()
    response = client.get("/api/admin/unknown-questions", headers=AUTH)
    assert response.status_code == 200
    assert response.json()[0]["question"] == "unanswered?"


def test_admin_conversation_detail():
    # Create a conversation with messages through the chat endpoint.
    import app.routers.chat as chat_router
    from unittest.mock import patch

    with patch.object(chat_router, "run_chat", lambda *a, **k: "answer"):
        cid = client.post("/api/chat", json={"message": "question"}).json()["conversation_id"]

    response = client.get(f"/api/admin/conversations/{cid}", headers=AUTH)
    assert response.status_code == 200
    detail = response.json()
    assert detail["id"] == cid
    assert [m["role"] for m in detail["messages"]] == ["user", "assistant"]


def test_admin_conversation_not_found():
    assert client.get("/api/admin/conversations/99999", headers=AUTH).status_code == 404
