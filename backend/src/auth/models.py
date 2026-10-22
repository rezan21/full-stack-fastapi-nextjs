from datetime import datetime

from sqlmodel import Field, SQLModel

from src.models import get_datetime_utc


class AuthThrottle(SQLModel, table=True):
    __tablename__ = "auth_throttle"

    key: str = Field(primary_key=True, max_length=64)
    failures: int = 0
    last_failure_at: datetime = Field(default_factory=get_datetime_utc, index=True)
    lock_expires_at: datetime | None = None
