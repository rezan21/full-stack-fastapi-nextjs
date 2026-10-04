from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from pwdlib.hashers.bcrypt import BcryptHasher

from app.core.config import settings
from app.models import Token, User

password_hash = PasswordHash(
    (
        Argon2Hasher(),
        BcryptHasher(),
    )
)


ALGORITHM = "HS256"
ACCESS_AUDIENCE = "access"


def create_access_token(
    subject: str | Any, expires_delta: timedelta, token_version: int
) -> str:
    """Create an access token for the subject at a token version."""
    to_encode = {
        "exp": datetime.now(UTC) + expires_delta,
        "sub": str(subject),
        "aud": ACCESS_AUDIENCE,
        "ver": token_version,
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)


def issue_token(user: User) -> Token:
    """Create a login token for the user."""
    expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return Token(
        access_token=create_access_token(user.id, expires_delta, user.token_version),
        expires_in=int(expires_delta.total_seconds()),
    )


def verify_password(
    plain_password: str, hashed_password: str
) -> tuple[bool, str | None]:
    """Verify a password against its stored hash."""
    return password_hash.verify_and_update(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return password_hash.hash(password)
