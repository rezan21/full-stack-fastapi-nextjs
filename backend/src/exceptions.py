from typing import Any

from fastapi import HTTPException, status
from sqlmodel import SQLModel


class HTTPError(SQLModel):
    detail: str


class DetailedHTTPException(HTTPException):
    STATUS_CODE = status.HTTP_500_INTERNAL_SERVER_ERROR
    DETAIL = "Server error"

    def __init__(
        self, detail: str | None = None, headers: dict[str, str] | None = None
    ) -> None:
        super().__init__(
            status_code=self.STATUS_CODE, detail=detail or self.DETAIL, headers=headers
        )


class BadRequest(DetailedHTTPException):
    STATUS_CODE = status.HTTP_400_BAD_REQUEST
    DETAIL = "Bad request"


class NotAuthenticated(DetailedHTTPException):
    STATUS_CODE = status.HTTP_401_UNAUTHORIZED
    DETAIL = "User not authenticated"

    def __init__(self, detail: str | None = None) -> None:
        super().__init__(detail=detail, headers={"WWW-Authenticate": "Bearer"})


class PermissionDenied(DetailedHTTPException):
    STATUS_CODE = status.HTTP_403_FORBIDDEN
    DETAIL = "Permission denied"


class NotFound(DetailedHTTPException):
    STATUS_CODE = status.HTTP_404_NOT_FOUND
    DETAIL = "Not found"


class TooManyRequests(DetailedHTTPException):
    STATUS_CODE = status.HTTP_429_TOO_MANY_REQUESTS
    DETAIL = "Too many requests"

    def __init__(self, detail: str | None = None, *, retry_after: int) -> None:
        super().__init__(detail=detail, headers={"Retry-After": str(retry_after)})
        self.retry_after = retry_after


class ServiceUnavailable(DetailedHTTPException):
    STATUS_CODE = status.HTTP_503_SERVICE_UNAVAILABLE
    DETAIL = "Service unavailable"


def error_responses(*codes: int) -> dict[int | str, dict[str, Any]]:
    """Build the documented error responses for the status codes."""
    return {code: {"model": HTTPError} for code in codes}


AUTH_ERRORS = error_responses(401, 403)
