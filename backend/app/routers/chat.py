"""Chat endpoint (non-streaming).

Persists the conversation and both sides of each turn. Phase 4 adds a streaming
(SSE) variant on top of the same underlying ``run_chat`` logic.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import crud
from ..chat import run_chat
from ..db import get_db
from ..schemas import ChatRequest, ChatResponse

router = APIRouter(tags=["chat"])


@router.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    conversation = crud.get_or_create_conversation(db, request.conversation_id)
    crud.add_message(db, conversation.id, "user", request.message)
    db.commit()  # persist the conversation + user message before running the model

    history = [m.model_dump() for m in request.history]
    reply = run_chat(request.message, history, conversation_id=conversation.id)

    crud.add_message(db, conversation.id, "assistant", reply)
    db.commit()

    return ChatResponse(reply=reply, conversation_id=conversation.id)
