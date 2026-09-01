"""Chat endpoints.

- ``POST /api/chat``        — non-streaming JSON reply, runs the output evaluator.
- ``POST /api/chat/stream`` — SSE streaming reply (guardrail only, no evaluator).

Both persist the conversation and both sides of the turn, and are rate-limited
per client IP via ``CHAT_RATE_LIMIT``.
"""

import json
import logging

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from .. import crud
from ..chat import run_chat
from ..db import SessionLocal, get_db
from ..rate_limit import chat_rate_limit, limiter
from ..schemas import ChatRequest, ChatResponse
from ..stream import stream_chat

logger = logging.getLogger(__name__)
router = APIRouter(tags=["chat"])


@router.post("/api/chat", response_model=ChatResponse)
@limiter.limit(chat_rate_limit)
def chat(request: Request, payload: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    conversation = crud.get_or_create_conversation(db, payload.conversation_id)
    crud.add_message(db, conversation.id, "user", payload.message)
    db.commit()  # persist the conversation + user message before running the model

    history = [m.model_dump() for m in payload.history]
    reply = run_chat(payload.message, history, conversation_id=conversation.id)

    crud.add_message(db, conversation.id, "assistant", reply)
    db.commit()

    return ChatResponse(reply=reply, conversation_id=conversation.id)


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"


@router.post("/api/chat/stream")
@limiter.limit(chat_rate_limit)
def chat_stream(request: Request, payload: ChatRequest, db: Session = Depends(get_db)) -> StreamingResponse:
    conversation = crud.get_or_create_conversation(db, payload.conversation_id)
    crud.add_message(db, conversation.id, "user", payload.message)
    db.commit()
    conversation_id = conversation.id
    history = [m.model_dump() for m in payload.history]

    def event_stream():
        chunks: list[str] = []
        try:
            for delta in stream_chat(payload.message, history, conversation_id=conversation_id):
                chunks.append(delta)
                yield _sse({"delta": delta})
        except Exception:
            logger.exception("Streaming chat failed")
            yield _sse({"error": "stream_failed"})
        finally:
            # The request-scoped `db` session is closed by the time this generator
            # runs (FastAPI closes it once the endpoint function returns the
            # StreamingResponse), so use a fresh session for the final write.
            reply = "".join(chunks)
            if reply:
                with SessionLocal() as write_db:
                    crud.add_message(write_db, conversation_id, "assistant", reply)
                    write_db.commit()

        yield _sse({"done": True, "conversation_id": conversation_id})

    return StreamingResponse(event_stream(), media_type="text/event-stream")
