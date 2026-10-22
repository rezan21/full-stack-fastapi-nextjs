import uuid
from datetime import datetime

from pydantic.experimental.missing_sentinel import MISSING
from sqlmodel import SQLModel

from src.items.models import ItemBase, ItemDescription, ItemTitle


class ItemCreate(ItemBase):
    pass


class ItemUpdate(SQLModel):
    title: ItemTitle | MISSING = MISSING  # type: ignore[valid-type]
    description: ItemDescription | MISSING = MISSING  # type: ignore[valid-type]


class ItemPublic(SQLModel):
    id: uuid.UUID
    owner_id: uuid.UUID
    title: str
    description: str | None
    created_at: datetime


class ItemsPublic(SQLModel):
    data: list[ItemPublic]
    count: int
