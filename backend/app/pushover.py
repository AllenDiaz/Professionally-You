"""Pushover notification helper.

Ports ``push()`` from the original ``app.py``. Unlike the original it no-ops
gracefully (with a log warning) when Pushover is not configured, and it uses a
request timeout so a slow Pushover API can't hang a chat turn.
"""

import logging

import certifi
import requests

from .config import get_settings

logger = logging.getLogger(__name__)

PUSHOVER_URL = "https://api.pushover.net/1/messages.json"


def push(text: str) -> None:
    """Send a Pushover notification, or skip it if credentials are missing."""
    settings = get_settings()
    if not (settings.pushover_user and settings.pushover_token):
        logger.warning("Pushover not configured; skipping notification: %s", text)
        return
    try:
        requests.post(
            PUSHOVER_URL,
            data={
                "token": settings.pushover_token,
                "user": settings.pushover_user,
                "message": text,
            },
            verify=certifi.where(),
            timeout=10,
        )
    except requests.RequestException as exc:
        logger.error("Pushover notification failed: %s", exc)
