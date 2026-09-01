"""Profile + RAG management endpoints.

- ``GET  /api/profile``          — current editable profile (public read)
- ``PUT  /api/profile``          — replace the profile (admin only)
- ``POST /api/profile/reindex``  — rebuild the RAG index (admin only)
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from .. import rag
from ..auth import require_admin
from ..profile import Profile, load_profile, save_profile

router = APIRouter(tags=["profile"])


class ReindexResponse(BaseModel):
    chunks: int


@router.get("/api/profile", response_model=Profile)
def get_profile() -> Profile:
    return load_profile()


@router.put("/api/profile", response_model=Profile, dependencies=[Depends(require_admin)])
def update_profile(profile: Profile) -> Profile:
    return save_profile(profile)


@router.post(
    "/api/profile/reindex", response_model=ReindexResponse, dependencies=[Depends(require_admin)]
)
def reindex() -> ReindexResponse:
    return ReindexResponse(chunks=rag.build_index())
