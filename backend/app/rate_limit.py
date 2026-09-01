"""Shared slowapi Limiter instance.

Kept in its own module (rather than ``main.py``) so both ``main.py`` (which
registers it on the app) and the routers (which decorate endpoints with it) can
import it without a circular import.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

from .config import get_settings

limiter = Limiter(key_func=get_remote_address)


def chat_rate_limit() -> str:
    """Read the current chat rate limit from settings (evaluated per request)."""
    return get_settings().chat_rate_limit
