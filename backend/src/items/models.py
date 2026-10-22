import uuid
from datetime import datetime
from typing import Annotated

from sqlalchemy import Index
from sqlmodel import Field, SQLModel

from src.models import get_datetime_utc

ItemTitle = Annotated[str, Field(min_length=1, max_length=255)]
ItemDescription = Annotated[str | None, Field(max_length=255)]


class ItemBase(SQLModel):
    title: ItemTitle
    description: ItemDescription = None


class Item(ItemBase, table=True):
    __table_args__ = (Index("item_owner_id_created_at_idx", "owner_id", "created_at"),)

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=get_datetime_utc)
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
