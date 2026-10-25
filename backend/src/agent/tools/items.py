import uuid
from typing import Annotated, Any

from langchain.tools import ToolRuntime, tool
from pydantic import BaseModel, Field, ValidationError
from sqlmodel.ext.asyncio.session import AsyncSession

from src.agent import interrupts as agent_interrupts
from src.agent.context import AgentContext
from src.agent.interrupts import UNANSWERED_RESULT, Decision
from src.database import SessionFactory
from src.items import service as items_service
from src.items.models import Item, ItemDescription, ItemTitle
from src.items.schemas import ItemCreate, ItemUpdate
from src.pagination import Pagination

MAX_ITEMS = 20

ItemId = Annotated[str, Field(description="The id of one of the user's items")]


class AgentItem(BaseModel):
    id: str
    title: ItemTitle
    description: ItemDescription


class AgentItems(BaseModel):
    data: list[AgentItem]
    count: int


class AgentItemChange(BaseModel):
    changed: bool
    message: str
    item: AgentItem | None = None


def shown(item: Item) -> AgentItem:
    """Return an item as the model and the user see it."""
    return AgentItem(id=str(item.id), title=item.title, description=item.description)


def unchanged(message: str) -> str:
    """Return the result of a tool that changed nothing, saying why."""
    return AgentItemChange(changed=False, message=message).model_dump_json()


def changed(message: str, item: Item | None = None) -> str:
    """Return the result of a tool that changed the user's items."""
    return AgentItemChange(
        changed=True,
        message=message,
        item=shown(item) if item is not None else None,
    ).model_dump_json()


NO_SUCH_ITEM = unchanged("You have no item with that id.")


def refused(error: ValidationError) -> str:
    """Return the result that says which of the item's details are not valid."""
    reasons = "; ".join(
        f"{'.'.join(map(str, e['loc']))}: {e['msg']}" for e in error.errors()
    )
    return unchanged(f"The item was not saved. {reasons}")


async def find_item(
    session: AsyncSession, item_id: str, owner_id: uuid.UUID
) -> Item | None:
    """Return the owner's item the id names, or None when the id is not an item of theirs."""
    try:
        return await items_service.get_owned_item(session, uuid.UUID(item_id), owner_id)
    except ValueError:
        return None


def delete_prompt(item: Item) -> str:
    """Return the question that asks the user to approve deleting the item."""
    question = f"Delete “{item.title}”?"
    return f"{question}\n{item.description}" if item.description else question


def item_form(title: str | None, description: str | None) -> dict[str, Any]:
    """Return the form for an item: its input schema, with the values the assistant has as defaults."""
    schema = ItemCreate.model_json_schema()
    for field, value in (("title", title), ("description", description)):
        if value is not None:
            schema["properties"][field]["default"] = value
    return schema


@tool
async def list_items(
    runtime: ToolRuntime[AgentContext],
    skip: Annotated[int, Field(description="How many items to skip")] = 0,
) -> str:
    """List the signed-in user's own items, newest first, a page at a time."""
    skip = max(skip, 0)
    async with SessionFactory() as session:
        items, count = await items_service.list_items(
            session,
            owner_id=runtime.context.user_id,
            pagination=Pagination(skip=skip, limit=MAX_ITEMS),
        )
    return AgentItems(
        data=[shown(item) for item in items], count=count
    ).model_dump_json()


@tool
async def create_item(
    runtime: ToolRuntime[AgentContext],
    title: Annotated[
        str | None, Field(description="The title the user gave, if they gave one")
    ] = None,
    description: Annotated[
        str | None, Field(description="The description the user gave, if they gave one")
    ] = None,
) -> str:
    """Add an item to the signed-in user's items. When the user asks to add one, call this right away, even if they gave no title or description: the app then asks the user for the details in a form, so never ask for them in chat. Pass the title and description when the user gave them."""
    if title:
        payload: dict[str, Any] = {"title": title, "description": description}
    else:
        answer = agent_interrupts.ask_for_input(
            runtime, "Add an item", item_form(title, description)
        )
        if answer is None:
            return unchanged("Cancelled. Nothing was added.")
        payload = answer
    try:
        item_in = ItemCreate.model_validate(payload)
    except ValidationError as error:
        return refused(error)
    async with SessionFactory() as session:
        item = await items_service.create_item(
            session, item_in, runtime.context.user_id
        )
    return changed(f"Added “{item.title}”.", item)


@tool
async def update_item(
    item_id: ItemId,
    runtime: ToolRuntime[AgentContext],
    title: Annotated[
        str | None,
        Field(description="The new title. Leave out to keep it"),
    ] = None,
    description: Annotated[
        str | None,
        Field(
            description="The new description. Empty text clears it. Leave out to keep it"
        ),
    ] = None,
) -> str:
    """Change the title or the description of one of the signed-in user's items. When the user asks to edit an item without saying what to change, call this right away with only the item id: the app shows the user a form that starts with the current values, so never ask them in chat what to change."""
    changes: dict[str, Any] = {
        field: value
        for field, value in (("title", title), ("description", description))
        if value is not None
    }
    async with SessionFactory() as session:
        item = await find_item(session, item_id, runtime.context.user_id)
    if item is None:
        return NO_SUCH_ITEM
    if not changes:
        answer = agent_interrupts.ask_for_input(
            runtime, "Edit the item", item_form(item.title, item.description)
        )
        if answer is None:
            return unchanged("Cancelled. Nothing was changed.")
        changes = answer
    try:
        item_in = ItemUpdate.model_validate(changes)
    except ValidationError as error:
        return refused(error)
    async with SessionFactory() as session:
        item = await find_item(session, item_id, runtime.context.user_id)
        if item is None:
            return NO_SUCH_ITEM
        previous_title = item.title
        item = await items_service.update_item(session, item, item_in)
    message = (
        f"Renamed “{previous_title}” to “{item.title}”."
        if item.title != previous_title
        else f"Updated “{item.title}”."
    )
    return changed(message, item)


@tool
async def delete_item(item_id: ItemId, runtime: ToolRuntime[AgentContext]) -> str:
    """Delete one of the signed-in user's items. The app asks the user to approve it, so do not ask first."""
    async with SessionFactory() as session:
        item = await find_item(session, item_id, runtime.context.user_id)
    if item is None:
        return NO_SUCH_ITEM
    title = item.title

    decision = agent_interrupts.ask_for_approval(runtime, delete_prompt(item))
    if decision is Decision.UNANSWERED:
        return unchanged(UNANSWERED_RESULT)
    if decision is Decision.DECLINED:
        return unchanged(f"The user declined to delete “{title}”. Nothing was deleted.")

    async with SessionFactory() as session:
        item = await find_item(session, item_id, runtime.context.user_id)
        if item is None:
            return NO_SUCH_ITEM
        await items_service.delete_item(session, item)
    return changed(f"Deleted “{title}”.")


SERVER_TOOLS = [list_items, create_item, update_item, delete_item]
CONTRACT_MODELS: list[type[BaseModel]] = [AgentItem, AgentItems, AgentItemChange]
