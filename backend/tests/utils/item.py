import uuid

from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.database import SessionFactory
from src.items.models import Item
from src.users.models import User
from tests.utils.user import create_random_user
from tests.utils.utils import random_lower_string


async def create_random_item(db: AsyncSession) -> Item:
    user = await create_random_user(db)
    item = Item(
        title=random_lower_string(),
        description=random_lower_string(),
        owner_id=user.id,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


async def add_items(db: AsyncSession, owner: User, count: int) -> list[Item]:
    items = [
        Item(title=f"{owner.id}-{number}", description=None, owner_id=owner.id)
        for number in range(count)
    ]
    db.add_all(items)
    await db.commit()
    return items


async def stored(item_id: uuid.UUID) -> Item | None:
    async with SessionFactory() as session:
        return await session.get(Item, item_id)


async def count_items(owner: User) -> int:
    async with SessionFactory() as session:
        counted = await session.exec(
            select(func.count()).select_from(Item).where(Item.owner_id == owner.id)
        )
        return counted.one()
