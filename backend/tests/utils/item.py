from sqlmodel.ext.asyncio.session import AsyncSession

from src.items.models import Item
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
