"""Core chat loop.

Ports ``Me.chat()`` from the original ``app.py`` with one important fix: the
tool-calling loop is now bounded by ``settings.max_tool_iterations`` instead of
being an unbounded ``while`` loop. If the cap is reached, a final call without
tools forces a plain text answer.

Phase 4 adds a streaming variant; this synchronous path stays as the
non-streaming implementation (also used later by the evaluator).
"""

import logging

from .config import get_settings
from .prompt import build_system_prompt
from .tools import TOOLS, handle_tool_calls
from .vertex import vertex_client

logger = logging.getLogger(__name__)


def run_chat(message: str, history: list[dict] | None = None) -> str:
    """Run a full chat turn (including tool calls) and return the reply text."""
    settings = get_settings()
    history = history or []
    messages: list = (
        [{"role": "system", "content": build_system_prompt()}]
        + list(history)
        + [{"role": "user", "content": message}]
    )

    client = vertex_client()

    for _ in range(settings.max_tool_iterations):
        response = client.chat.completions.create(
            model=settings.model_name, messages=messages, tools=TOOLS
        )
        choice = response.choices[0]
        if choice.finish_reason == "tool_calls":
            messages.append(choice.message)
            messages.extend(handle_tool_calls(choice.message.tool_calls))
            continue
        return choice.message.content or ""

    # Safety valve: too many tool rounds. Ask once more with no tools available
    # so the model is forced to produce a text answer.
    logger.warning(
        "Tool loop hit max iterations (%s); forcing a final answer.",
        settings.max_tool_iterations,
    )
    response = client.chat.completions.create(
        model=settings.model_name, messages=messages
    )
    return response.choices[0].message.content or ""
