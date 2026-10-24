from typing import Any

from pydantic.json_schema import models_json_schema

from src.agent.tools.registry import CONTRACT_MODELS, TOOL_NAMES


def contract_schemas() -> dict[str, Any]:
    """Return the JSON Schemas the agent and the browser share, by name."""
    _, schema = models_json_schema(
        [(model, "validation") for model in CONTRACT_MODELS],
        ref_template="#/components/schemas/{model}",
    )
    names = {
        "title": "ToolName",
        "description": "The names of the tools the agent runs and the browser draws or runs.",
        "type": "string",
        "enum": TOOL_NAMES,
    }
    return {**schema["$defs"], "ToolName": names}
