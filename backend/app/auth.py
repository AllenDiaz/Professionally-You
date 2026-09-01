"""Shared admin auth dependency.

A single bearer token (``ADMIN_TOKEN``) guards every admin-only route —
deliberately simple for a single-owner site. If the token is unset the guarded
route returns 503 rather than silently allowing access.
"""

from fastapi import Header, HTTPException

from .config import get_settings


def require_admin(authorization: str | None = Header(default=None)) -> None:
    settings = get_settings()
    if not settings.admin_token:
        raise HTTPException(status_code=503, detail="Admin API not configured (set ADMIN_TOKEN)")
    if authorization != f"Bearer {settings.admin_token}":
        raise HTTPException(status_code=401, detail="Unauthorized")
