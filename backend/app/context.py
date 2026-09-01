"""Per-turn context.

Carries the active conversation id so tool handlers can attach the lead /
unknown-question rows they create to the right conversation, without threading
the id through every function signature.
"""

import contextvars
from contextlib import contextmanager

_conversation_id: contextvars.ContextVar[int | None] = contextvars.ContextVar(
    "conversation_id", default=None
)


def get_conversation_id() -> int | None:
    return _conversation_id.get()


@contextmanager
def conversation_scope(conversation_id: int | None):
    token = _conversation_id.set(conversation_id)
    try:
        yield
    finally:
        _conversation_id.reset(token)
