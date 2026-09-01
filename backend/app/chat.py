"""Core chat loop.

Ports ``Me.chat()`` from the original ``app.py`` with one important fix: the
tool-calling loop is now bounded by ``settings.max_tool_iterations`` instead of
being an unbounded ``while`` loop. If the cap is reached, a final call without
tools forces a plain text answer.

Phase 4 adds an input guardrail before the model runs and an output evaluator
after — with a single feedback-guided retry if the evaluator rejects the draft.
See ``stream.py`` for the streaming counterpart (guardrail only; evaluating a
full reply before releasing it would defeat the point of streaming).
"""

import logging

from . import guardrails
from .config import get_settings
from .context import conversation_scope
from .prompt import build_system_prompt, get_person_name
from .tools import TOOLS, handle_tool_calls
from .vertex import vertex_client

logger = logging.getLogger(__name__)


def run_chat(
    message: str,
    history: list[dict] | None = None,
    conversation_id: int | None = None,
) -> str:
    """Run a full chat turn (including tool calls) and return the reply text.

    ``conversation_id`` is exposed to tool handlers via a context var so any
    lead / unknown-question they record is linked to this conversation.
    """
    settings = get_settings()
    history = history or []

    allowed, reason = guardrails.check_input(message)
    if not allowed:
        logger.info("Input blocked by guardrail: %s", reason)
        return guardrails.GUARDRAIL_REDIRECT_MESSAGE

    system_prompt = build_system_prompt(message)
    messages: list = (
        [{"role": "system", "content": system_prompt}]
        + list(history)
        + [{"role": "user", "content": message}]
    )

    client = vertex_client()

    with conversation_scope(conversation_id):
        draft = _run_loop(client, settings, messages)

        acceptable, feedback = guardrails.evaluate_reply(
            get_person_name(), system_prompt, message, draft
        )
        if acceptable:
            return draft

        logger.info("Evaluator rejected draft reply; retrying once: %s", feedback)
        messages.append({"role": "assistant", "content": draft})
        messages.append(
            {
                "role": "user",
                "content": (
                    "Your previous reply failed an internal quality check: "
                    f"{feedback}\nPlease provide a corrected reply."
                ),
            }
        )
        return _run_loop(client, settings, messages)


def _run_loop(client, settings, messages: list) -> str:
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
