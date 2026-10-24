from enum import StrEnum
from typing import Any

from ag_ui.core import ResumeEntry
from langchain.tools import ToolRuntime
from langgraph.types import interrupt

UNANSWERED_RESULT = (
    "The user did not answer the request and sent a new message instead. "
    "The action was not carried out."
)


class Decision(StrEnum):
    APPROVED = "approved"
    DECLINED = "declined"
    UNANSWERED = "unanswered"


def _ask(
    runtime: ToolRuntime[Any],
    reason: str,
    message: str,
    form: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Pause the run until the user answers the request, and return the answer."""
    if runtime.tool_call_id is None:
        raise RuntimeError("A request to the user needs a tool call to attach to")
    request: dict[str, Any] = {
        "reason": reason,
        "toolCallId": runtime.tool_call_id,
        "message": message,
    }
    if form is not None:
        request["responseSchema"] = form
    answer: dict[str, Any] = interrupt(request)
    return answer


def ask_for_approval(runtime: ToolRuntime[Any], message: str) -> Decision:
    """Pause until the user approves or declines the tool call that is running."""
    answer = _ask(runtime, "tool_call", message)
    if answer.get("approved") is True:
        return Decision.APPROVED
    if answer.get("cancelled") is True:
        return Decision.UNANSWERED
    return Decision.DECLINED


def ask_for_input(
    runtime: ToolRuntime[Any], message: str, form: dict[str, Any]
) -> dict[str, Any] | None:
    """Pause until the user fills in the form, returning their values, or None when they cancel."""
    answer = _ask(runtime, "input_required", message, form)
    return None if answer.get("cancelled") is True else answer


def resume_value(entry: ResumeEntry) -> dict[str, Any]:
    """Return what the waiting tool is handed for the answer in a resume entry."""
    if entry.status == "resolved" and isinstance(entry.payload, dict):
        return entry.payload
    return {"cancelled": True}
