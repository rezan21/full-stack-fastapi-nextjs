from collections.abc import Generator
from typing import Annotated, Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError
from sqlmodel import Session

from app.core import security
from app.core.config import settings
from app.core.db import engine
from app.models import HTTPError, TokenPayload, User

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token"
)


def get_db() -> Generator[Session]:
    """Yield a database session."""
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_db)]
TokenDep = Annotated[str, Depends(reusable_oauth2)]


def invalid_credentials() -> HTTPException:
    """Build the error for unauthenticated requests."""
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(session: SessionDep, token: TokenDep) -> User:
    """Return the user the bearer token belongs to."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[security.ALGORITHM],
            audience=security.ACCESS_AUDIENCE,
        )
        token_data = TokenPayload(**payload)
    except InvalidTokenError, ValidationError:
        raise invalid_credentials()
    user = session.get(User, token_data.sub)
    if not user or user.token_version != token_data.ver:
        raise invalid_credentials()
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user"
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def error_responses(*codes: int) -> dict[int | str, dict[str, Any]]:
    """Build the documented error responses for the status codes."""
    return {code: {"model": HTTPError} for code in codes}


AUTH_ERRORS = error_responses(401, 403)
