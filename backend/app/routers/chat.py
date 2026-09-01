"""Chat endpoint (non-streaming).

Phase 1 exposes a simple request/response chat endpoint. Phase 4 adds a
streaming (SSE) variant on top of the same underlying ``run_chat`` logic.
"""

from fastapi import APIRouter

from ..chat import run_chat
from ..schemas import ChatRequest, ChatResponse

router = APIRouter(tags=["chat"])


@router.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    history = [m.model_dump() for m in request.history]
    reply = run_chat(request.message, history)
    return ChatResponse(reply=reply)
