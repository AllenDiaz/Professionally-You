"""Vertex AI client construction.

Ports ``vertex_client()`` from the original ``app.py`` but caches the ADC
credentials and only refreshes the access token when it is missing or expired
(``creds.valid``), instead of refreshing on every single request.
"""

import threading

import google.auth
import google.auth.transport.requests
from openai import OpenAI

from .config import get_settings

_CLOUD_PLATFORM_SCOPE = "https://www.googleapis.com/auth/cloud-platform"

_lock = threading.Lock()
_credentials = None


def _get_credentials():
    """Lazily load and cache Application Default Credentials (thread-safe)."""
    global _credentials
    if _credentials is None:
        with _lock:
            if _credentials is None:
                _credentials, _ = google.auth.default(scopes=[_CLOUD_PLATFORM_SCOPE])
    return _credentials


def vertex_client() -> OpenAI:
    """Return an OpenAI client pointed at the Vertex AI OpenAI-compatible endpoint.

    The access token is only refreshed when it is absent or expired, so warm
    requests reuse a still-valid token instead of re-authenticating every call.
    """
    settings = get_settings()
    creds = _get_credentials()
    if not creds.valid:
        creds.refresh(google.auth.transport.requests.Request())
    return OpenAI(base_url=settings.vertex_base_url, api_key=creds.token)
