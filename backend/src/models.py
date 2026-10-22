from datetime import UTC, datetime
from typing import Annotated

from pydantic import AfterValidator, StringConstraints
from sqlmodel import Field, SQLModel

from src.constants import POSTGRES_INDEXES_NAMING_CONVENTION

SQLModel.metadata.naming_convention = POSTGRES_INDEXES_NAMING_CONVENTION

EMAIL_PATTERN = (
    r"^[A-Za-z0-9_'+-]+(\.[A-Za-z0-9_'+-]+)*"
    r"@([A-Za-z0-9]([A-Za-z0-9-]*[A-Za-z0-9])?\.)+[A-Za-z]{2,}$"
)

Email = Annotated[
    str,
    Field(max_length=255),
    StringConstraints(pattern=EMAIL_PATTERN),
    AfterValidator(str.lower),
]


def get_datetime_utc() -> datetime:
    return datetime.now(UTC)


class Message(SQLModel):
    message: str
