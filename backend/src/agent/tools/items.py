import json

from langchain.tools import ToolRuntime, tool

from src.agent.context import AgentContext
from src.database import SessionFactory
from src.items import service as items_service
from src.pagination import Pagination

MAX_ITEMS = 20


@tool
async def list_items(runtime: ToolRuntime[AgentContext]) -> str:
    """List the signed-in user's own items, newest first."""
    async with SessionFactory() as session:
        items, count = await items_service.list_items(
            session,
            owner_id=runtime.context.user_id,
            pagination=Pagination(skip=0, limit=MAX_ITEMS),
        )
    shown = [
        {"id": str(item.id), "title": item.title, "description": item.description}
        for item in items
    ]
    return json.dumps({"count": count, "items": shown})
