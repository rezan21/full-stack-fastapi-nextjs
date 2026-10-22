import uuid
from datetime import datetime
from typing import Annotated

from sqlmodel import Field, SQLModel

from src.models import Email, get_datetime_utc

FullName = Annotated[str, Field(min_length=1, max_length=255)]


class UserBase(SQLModel):
    email: Email = Field(unique=True, index=True)
    is_active: bool = True
    is_superuser: bool = False
    full_name: FullName


class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    token_version: int = Field(default=0, sa_column_kwargs={"server_default": "0"})
    created_at: datetime = Field(default_factory=get_datetime_utc)
