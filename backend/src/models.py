from datetime import UTC, datetime
from typing import Annotated

from pydantic import AfterValidator, StringConstraints
from sqlmodel import Field, SQLModel

POSTGRES_INDEXES_NAMING_CONVENTION = {
    "ix": "%(column_0_label)s_idx",
    "uq": "%(table_name)s_%(column_0_N_name)s_key",
    "ck": "%(table_name)s_%(constraint_name)s_check",
    "fk": "%(table_name)s_%(column_0_name)s_fkey",
    "pk": "%(table_name)s_pkey",
}
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
