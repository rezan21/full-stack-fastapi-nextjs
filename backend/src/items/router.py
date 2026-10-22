from fastapi import APIRouter, Depends

from src.auth import dependencies as auth_dependencies
from src.database import SessionDep
from src.exceptions import AUTH_ERRORS, error_responses
from src.items import service as items_service
from src.items.dependencies import OwnedItem
from src.items.models import Item
from src.items.schemas import ItemCreate, ItemPublic, ItemsPublic, ItemUpdate
from src.pagination import PaginationDep

router = APIRouter(
    prefix="/items",
    tags=["items"],
    dependencies=[Depends(auth_dependencies.get_current_user)],
    responses=AUTH_ERRORS,
)


@router.get("", response_model=ItemsPublic)
async def read_items(
    session: SessionDep,
    current_user: auth_dependencies.CurrentUser,
    pagination: PaginationDep,
) -> dict[str, object]:
    """Retrieve items."""
    items, count = await items_service.list_items(
        session,
        owner_id=None if current_user.is_superuser else current_user.id,
        pagination=pagination,
    )
    return {"data": items, "count": count}


@router.get("/{item_id}", response_model=ItemPublic, responses=error_responses(404))
async def read_item(item: OwnedItem) -> Item:
    """Get item by ID."""
    return item


@router.post("", response_model=ItemPublic, status_code=201)
async def create_item(
    session: SessionDep,
    current_user: auth_dependencies.CurrentUser,
    item_in: ItemCreate,
) -> Item:
    """Create new item."""
    return await items_service.create_item(session, item_in, current_user.id)


@router.patch("/{item_id}", response_model=ItemPublic, responses=error_responses(404))
async def update_item(
    session: SessionDep, item: OwnedItem, item_in: ItemUpdate
) -> Item:
    """Update an item."""
    return await items_service.update_item(session, item, item_in)


@router.delete("/{item_id}", status_code=204, responses=error_responses(404))
async def delete_item(session: SessionDep, item: OwnedItem) -> None:
    """Delete an item."""
    await items_service.delete_item(session, item)
