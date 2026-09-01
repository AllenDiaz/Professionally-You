"""Admin API — review captured leads, unanswered questions, and conversations.

Guarded by a single bearer token (``ADMIN_TOKEN``). This is deliberately simple
for a single-owner site; if the token is unset the whole namespace returns 503.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import crud
from ..auth import require_admin
from ..db import get_db
from ..schemas import ConversationDetail, ConversationOut, LeadOut, UnknownQuestionOut

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/leads", response_model=list[LeadOut], dependencies=[Depends(require_admin)])
def get_leads(db: Session = Depends(get_db)):
    return crud.list_leads(db)


@router.get(
    "/unknown-questions",
    response_model=list[UnknownQuestionOut],
    dependencies=[Depends(require_admin)],
)
def get_unknown_questions(db: Session = Depends(get_db)):
    return crud.list_unknown_questions(db)


@router.get(
    "/conversations",
    response_model=list[ConversationOut],
    dependencies=[Depends(require_admin)],
)
def get_conversations(db: Session = Depends(get_db)):
    return crud.list_conversations(db)


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationDetail,
    dependencies=[Depends(require_admin)],
)
def get_conversation(conversation_id: int, db: Session = Depends(get_db)):
    conversation = crud.get_conversation(db, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation
