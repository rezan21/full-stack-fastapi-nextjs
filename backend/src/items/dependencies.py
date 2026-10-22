import uuid
from typing import Annotated

from fastapi import Depends

from src.auth import dependencies as auth_dependencies
from src.database import SessionDep
from src.items.exceptions import ItemNotFound, NotEnoughPermissions
from src.items.models import Item


async def valid_item_id(item_id: uuid.UUID, session: SessionDep) -> Item:
    """Return the item with the id, or raise a 404."""
    item = await session.get(Item, item_id)
    if not item:
        raise ItemNotFound()
    return item


async def valid_owned_item(
    item: Annotated[Item, Depends(valid_item_id)],
    current_user: auth_dependencies.CurrentUser,
) -> Item:
    """Return the item when the user owns it or is a superuser, or raise a 403."""
    if not current_user.is_superuser and item.owner_id != current_user.id:
        raise NotEnoughPermissions()
    return item


OwnedItem = Annotated[Item, Depends(valid_owned_item)]
