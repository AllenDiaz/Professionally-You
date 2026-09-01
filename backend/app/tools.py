"""LLM tool definitions and dispatch.

Ports the two tools from the original ``app.py``. The key change: tool dispatch
now goes through an explicit ``TOOL_HANDLERS`` mapping instead of the original
``globals().get(tool_name)`` lookup, which could invoke any global by name with
model-controlled arguments.
"""

import json
import logging

from . import pushover

logger = logging.getLogger(__name__)


def record_user_details(email, name="Name not provided", notes="not provided") -> dict:
    pushover.push(f"Recording interest from {name} with email {email} and notes {notes}")
    return {"recorded": "ok"}


def record_unknown_question(question) -> dict:
    pushover.push(f"Recording unanswerable question: {question}")
    return {"recorded": "ok"}


# Explicit dispatch table — the safe replacement for globals()[tool_name].
TOOL_HANDLERS = {
    "record_user_details": record_user_details,
    "record_unknown_question": record_unknown_question,
}

record_user_details_json = {
    "name": "record_user_details",
    "description": "Use this tool to record that a user is interested in being in touch and provided an email address",
    "parameters": {
        "type": "object",
        "properties": {
            "email": {"type": "string", "description": "The email address of this user"},
            "name": {"type": "string", "description": "The user's name, if they provided it"},
            "notes": {
                "type": "string",
                "description": "Any additional information about the conversation that's worth recording to give context",
            },
        },
        "required": ["email"],
        "additionalProperties": False,
    },
}

record_unknown_question_json = {
    "name": "record_unknown_question",
    "description": "Always use this tool to record any question that couldn't be answered as you didn't know the answer",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The question that couldn't be answered",
            },
        },
        "required": ["question"],
        "additionalProperties": False,
    },
}

TOOLS = [
    {"type": "function", "function": record_user_details_json},
    {"type": "function", "function": record_unknown_question_json},
]


def handle_tool_calls(tool_calls) -> list[dict]:
    """Execute tool calls via the explicit dispatch table and return tool messages."""
    results = []
    for tool_call in tool_calls:
        tool_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)
        logger.info("Tool called: %s", tool_name)
        handler = TOOL_HANDLERS.get(tool_name)
        if handler is None:
            logger.warning("Unknown tool requested by model: %s", tool_name)
            result = {"error": f"unknown tool: {tool_name}"}
        else:
            result = handler(**arguments)
        results.append(
            {
                "role": "tool",
                "content": json.dumps(result),
                "tool_call_id": tool_call.id,
            }
        )
    return results
