import uuid
from datetime import datetime

from pydantic.experimental.missing_sentinel import MISSING
from sqlmodel import SQLModel

from src.auth.schemas import CurrentPassword, Password
from src.models import Email
from src.users.models import FullName, UserBase


class UserCreate(UserBase):
    password: Password


class UserRegister(SQLModel):
    email: Email
    full_name: FullName


class UserUpdateMe(SQLModel):
    full_name: FullName | MISSING = MISSING  # type: ignore[valid-type]


class EmailChange(SQLModel):
    email: Email
    current_password: CurrentPassword


class AccountDeletion(SQLModel):
    current_password: CurrentPassword


class EmailChangeConfirm(SQLModel):
    token: str


class UpdatePassword(SQLModel):
    current_password: CurrentPassword
    new_password: Password


class UserPublic(SQLModel):
    id: uuid.UUID
    email: str
    full_name: str
    is_active: bool
    is_superuser: bool
    created_at: datetime
