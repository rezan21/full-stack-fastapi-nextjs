from math import ceil

from src.exceptions import (
    BadRequest,
    NotAuthenticated,
    PermissionDenied,
    TooManyRequests,
)
from src.utils import describe_duration


class InvalidCredentials(NotAuthenticated):
    DETAIL = "Could not validate credentials"


class InactiveUser(PermissionDenied):
    DETAIL = "Inactive user"


class AccountInactive(BadRequest):
    DETAIL = "Inactive user"


class IncorrectLogin(BadRequest):
    DETAIL = "Incorrect email or password"


class IncorrectPassword(BadRequest):
    DETAIL = "Incorrect password"


class InvalidToken(BadRequest):
    DETAIL = "Invalid token"


class AccountLocked(TooManyRequests):
    def __init__(self, retry_after: int) -> None:
        wait = describe_duration(ceil(retry_after / 60))
        super().__init__(
            f"Too many failed attempts. Try again in {wait}.", retry_after=retry_after
        )
