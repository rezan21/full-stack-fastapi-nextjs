from collections.abc import Iterable

from ag_ui.core import Tool
from copilotkit import CopilotKitMiddleware
from langchain.agents.middleware import ModelRequest

from src.agent.tools.registry import BROWSER_TOOLS


def offered(names: Iterable[str]) -> list[Tool]:
    """Return the browser tools the browser says it can run, limited to those the server defines."""
    return [
        BROWSER_TOOLS[name] for name in dict.fromkeys(names) if name in BROWSER_TOOLS
    ]


class BrowserToolsMiddleware(CopilotKitMiddleware):
    """Serves the browser's tools to the model without printing the run's context into the prompt."""

    def _apply_app_context_note(self, request: ModelRequest) -> ModelRequest:
        return request
