import uuid
from collections.abc import Sequence

from sqlmodel import col, func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.items.models import Item
from src.items.schemas import ItemCreate, ItemUpdate
from src.pagination import Pagination


async def list_items(
    session: AsyncSession, *, owner_id: uuid.UUID | None, pagination: Pagination
) -> tuple[Sequence[Item], int]:
    """Return a page of items, newest first, and how many there are in all."""
    count_statement = select(func.count()).select_from(Item)
    statement = select(Item)
    if owner_id is not None:
        count_statement = count_statement.where(Item.owner_id == owner_id)
        statement = statement.where(Item.owner_id == owner_id)
    count = (await session.exec(count_statement)).one()
    result = await session.exec(
        statement.order_by(col(Item.created_at).desc(), col(Item.id))
        .offset(pagination.skip)
        .limit(pagination.limit)
    )
    return result.all(), count


async def create_item(
    session: AsyncSession, item_in: ItemCreate, owner_id: uuid.UUID
) -> Item:
    """Create an item for the owner."""
    item = Item.model_validate(item_in, update={"owner_id": owner_id})
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item


async def update_item(session: AsyncSession, item: Item, item_in: ItemUpdate) -> Item:
    """Apply the fields the user sent."""
    item.sqlmodel_update(item_in.model_dump(exclude_unset=True))
    session.add(item)
    await session.commit()
    await session.refresh(item)
    return item


async def delete_item(session: AsyncSession, item: Item) -> None:
    """Delete the item."""
    await session.delete(item)
    await session.commit()
