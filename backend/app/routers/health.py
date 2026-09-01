"""Health / readiness endpoint.

Reports whether the key integrations are configured — without leaking any secret
values — echoing the diagnostic idea from the original notebook.
"""

from fastapi import APIRouter

from ..config import get_settings
from ..schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="ok",
        vertex_configured=bool(settings.gcp_project),
        pushover_configured=bool(settings.pushover_user and settings.pushover_token),
        model=settings.model_name,
    )
