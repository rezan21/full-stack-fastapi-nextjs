from collections.abc import Iterable

from ag_ui.core import Tool

FLY_TO = Tool(
    name="fly_to",
    description=(
        "Move the map the user is looking at to a place. "
        "Give the place's name and its latitude and longitude."
    ),
    parameters={
        "type": "object",
        "properties": {
            "place": {
                "type": "string",
                "description": "The place's name, such as London",
            },
            "lat": {"type": "number", "minimum": -90, "maximum": 90},
            "lng": {"type": "number", "minimum": -180, "maximum": 180},
        },
        "required": ["place", "lat", "lng"],
    },
)

FRONTEND_TOOLS = {tool.name: tool for tool in (FLY_TO,)}


def offered(names: Iterable[str]) -> list[Tool]:
    """Return the browser tools the client says it can run, limited to those the server defines."""
    return [
        FRONTEND_TOOLS[name] for name in dict.fromkeys(names) if name in FRONTEND_TOOLS
    ]
