from math import ceil

from src.auth.constants import ErrorCode
from src.exceptions import (
    BadRequest,
    NotAuthenticated,
    PermissionDenied,
    TooManyRequests,
)
from src.utils import describe_duration


class InvalidCredentials(NotAuthenticated):
    DETAIL = ErrorCode.INVALID_CREDENTIALS


class InactiveUser(PermissionDenied):
    DETAIL = ErrorCode.INACTIVE_USER


class AccountInactive(BadRequest):
    DETAIL = ErrorCode.INACTIVE_USER


class IncorrectLogin(BadRequest):
    DETAIL = ErrorCode.INCORRECT_LOGIN


class IncorrectPassword(BadRequest):
    DETAIL = ErrorCode.INCORRECT_PASSWORD


class InvalidToken(BadRequest):
    DETAIL = ErrorCode.INVALID_TOKEN


class AccountLocked(TooManyRequests):
    def __init__(self, retry_after: int) -> None:
        wait = describe_duration(ceil(retry_after / 60))
        super().__init__(
            ErrorCode.ACCOUNT_LOCKED.format(wait=wait), retry_after=retry_after
        )
