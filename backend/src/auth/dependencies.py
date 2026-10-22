from typing import Annotated

import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError

from src.auth import constants as auth_constants
from src.auth.config import auth_settings
from src.auth.exceptions import InactiveUser, InvalidCredentials
from src.auth.schemas import TokenPayload
from src.config import settings
from src.database import SessionDep
from src.users.models import User

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/login/access-token"
)

TokenDep = Annotated[str, Depends(reusable_oauth2)]


async def parse_jwt_data(token: TokenDep) -> TokenPayload:
    """Return the claims of a valid access token."""
    try:
        payload = jwt.decode(
            token,
            auth_settings.SECRET_KEY,
            algorithms=[auth_constants.ALGORITHM],
            audience=auth_constants.ACCESS_AUDIENCE,
        )
        return TokenPayload(**payload)
    except InvalidTokenError, ValidationError:
        raise InvalidCredentials()


async def get_current_user(
    session: SessionDep, token_data: Annotated[TokenPayload, Depends(parse_jwt_data)]
) -> User:
    """Return the active user the bearer token belongs to."""
    user = await session.get(User, token_data.sub)
    if not user or user.token_version != token_data.ver:
        raise InvalidCredentials()
    if not user.is_active:
        raise InactiveUser()
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
