"""Profile + RAG management endpoints.

- ``GET  /api/profile``          — current editable profile
- ``PUT  /api/profile``          — replace the profile
- ``POST /api/profile/reindex``  — rebuild the RAG index from the LinkedIn source
"""

from fastapi import APIRouter
from pydantic import BaseModel

from .. import rag
from ..profile import Profile, load_profile, save_profile

router = APIRouter(tags=["profile"])


class ReindexResponse(BaseModel):
    chunks: int


@router.get("/api/profile", response_model=Profile)
def get_profile() -> Profile:
    return load_profile()


@router.put("/api/profile", response_model=Profile)
def update_profile(profile: Profile) -> Profile:
    return save_profile(profile)


@router.post("/api/profile/reindex", response_model=ReindexResponse)
def reindex() -> ReindexResponse:
    return ReindexResponse(chunks=rag.build_index())
