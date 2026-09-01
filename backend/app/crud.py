"""Thin data-access helpers over the ORM models."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Conversation, Lead, Message, UnknownQuestion


def get_or_create_conversation(db: Session, conversation_id: int | None) -> Conversation:
    if conversation_id is not None:
        existing = db.get(Conversation, conversation_id)
        if existing is not None:
            return existing
    conversation = Conversation()
    db.add(conversation)
    db.flush()  # assign the primary key
    return conversation


def add_message(db: Session, conversation_id: int, role: str, content: str) -> Message:
    message = Message(conversation_id=conversation_id, role=role, content=content)
    db.add(message)
    return message


def add_lead(
    db: Session,
    email: str,
    name: str | None = None,
    notes: str | None = None,
    conversation_id: int | None = None,
) -> Lead:
    lead = Lead(email=email, name=name, notes=notes, conversation_id=conversation_id)
    db.add(lead)
    return lead


def add_unknown_question(
    db: Session, question: str, conversation_id: int | None = None
) -> UnknownQuestion:
    unknown = UnknownQuestion(question=question, conversation_id=conversation_id)
    db.add(unknown)
    return unknown


def list_leads(db: Session) -> list[Lead]:
    return list(db.scalars(select(Lead).order_by(Lead.id.desc())))


def list_unknown_questions(db: Session) -> list[UnknownQuestion]:
    return list(db.scalars(select(UnknownQuestion).order_by(UnknownQuestion.id.desc())))


def list_conversations(db: Session) -> list[Conversation]:
    return list(db.scalars(select(Conversation).order_by(Conversation.id.desc())))


def get_conversation(db: Session, conversation_id: int) -> Conversation | None:
    return db.get(Conversation, conversation_id)
