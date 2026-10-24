from ag_ui.core import Tool
from langchain_core.tools import BaseTool
from pydantic import BaseModel

from src.agent.tools import items, place

SERVER_TOOLS: list[BaseTool] = [*items.SERVER_TOOLS]
BROWSER_TOOLS: dict[str, Tool] = {tool.name: tool for tool in place.BROWSER_TOOLS}
TOOL_NAMES: list[str] = [*(tool.name for tool in SERVER_TOOLS), *BROWSER_TOOLS]
CONTRACT_MODELS: list[type[BaseModel]] = [
    *items.CONTRACT_MODELS,
    *place.CONTRACT_MODELS,
]
