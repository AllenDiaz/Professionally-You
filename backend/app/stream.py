"""Streaming chat loop.

Mirrors ``chat.run_chat`` but yields incremental text deltas as they arrive from
the model, for use behind an SSE endpoint. Tool-call fragments are accumulated
across chunks, executed once complete, and streaming resumes for the model's
next turn — transparent to the client. The tool loop is bounded the same way as
the non-streaming path.

The input guardrail still runs up front. The output evaluator does **not** run
here: judging a full reply before releasing any of it would defeat the purpose
of streaming. Use the non-streaming ``/api/chat`` endpoint when the evaluator
pass matters more than latency.
"""

import logging
from collections.abc import Iterator
from types import SimpleNamespace

from . import guardrails
from .config import get_settings
from .context import conversation_scope
from .prompt import build_system_prompt
from .tools import TOOLS, handle_tool_calls
from .vertex import vertex_client

logger = logging.getLogger(__name__)


def stream_chat(
    message: str,
    history: list[dict] | None = None,
    conversation_id: int | None = None,
) -> Iterator[str]:
    """Yield text deltas for a chat turn, handling tool calls transparently."""
    settings = get_settings()
    history = history or []

    allowed, reason = guardrails.check_input(message)
    if not allowed:
        logger.info("Input blocked by guardrail: %s", reason)
        yield guardrails.GUARDRAIL_REDIRECT_MESSAGE
        return

    messages: list = (
        [{"role": "system", "content": build_system_prompt(message)}]
        + list(history)
        + [{"role": "user", "content": message}]
    )
    client = vertex_client()

    with conversation_scope(conversation_id):
        yield from _stream_loop(client, settings, messages)


def _stream_once(client, settings, messages: list):
    """Stream one model turn; yield content deltas, return (tool_calls, finish_reason)."""
    response_stream = client.chat.completions.create(
        model=settings.model_name, messages=messages, tools=TOOLS, stream=True
    )

    tool_call_parts: dict[int, dict] = {}
    finish_reason = None
    for chunk in response_stream:
        choice = chunk.choices[0]
        if choice.finish_reason:
            finish_reason = choice.finish_reason
        delta = choice.delta
        if delta and delta.content:
            yield delta.content
        if delta and delta.tool_calls:
            for tc in delta.tool_calls:
                entry = tool_call_parts.setdefault(
                    tc.index, {"id": None, "name": None, "arguments": ""}
                )
                if tc.id:
                    entry["id"] = tc.id
                if tc.function and tc.function.name:
                    entry["name"] = tc.function.name
                if tc.function and tc.function.arguments:
                    entry["arguments"] += tc.function.arguments

    tool_calls = [
        SimpleNamespace(
            id=entry["id"],
            function=SimpleNamespace(name=entry["name"], arguments=entry["arguments"]),
        )
        for _, entry in sorted(tool_call_parts.items())
    ]
    return tool_calls, finish_reason


def _stream_loop(client, settings, messages: list) -> Iterator[str]:
    for _ in range(settings.max_tool_iterations):
        tool_calls, finish_reason = yield from _stream_once(client, settings, messages)
        if finish_reason != "tool_calls":
            return
        messages.append(
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in tool_calls
                ],
            }
        )
        messages.extend(handle_tool_calls(tool_calls))

    # Safety valve: too many tool rounds. Ask once more with no tools available
    # so the model is forced to produce a text answer (non-streamed).
    logger.warning(
        "Tool loop hit max iterations (%s) while streaming; forcing a final answer.",
        settings.max_tool_iterations,
    )
    response = client.chat.completions.create(model=settings.model_name, messages=messages)
    text = response.choices[0].message.content or ""
    if text:
        yield text
