from copilotkit import CopilotKitMiddleware
from langchain.agents.middleware import ModelRequest


class BrowserToolsMiddleware(CopilotKitMiddleware):
    """Serves the browser's tools to the model, without printing the run's context into the prompt."""

    def _apply_app_context_note(self, request: ModelRequest) -> ModelRequest:
        return request
