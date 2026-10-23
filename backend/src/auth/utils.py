import hashlib
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher
from pwdlib.hashers.bcrypt import BcryptHasher

from src.auth.config import auth_settings

ALGORITHM = "HS256"
ACCESS_AUDIENCE = "access"
PASSWORD_RESET_AUDIENCE = "password-reset"

password_hash = PasswordHash(
    (
        Argon2Hasher(),
        BcryptHasher(),
    )
)


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
    return jwt.encode(to_encode, auth_settings.SECRET_KEY, algorithm=ALGORITHM)


def verify_password(
    plain_password: str, hashed_password: str
) -> tuple[bool, str | None]:
    """Verify a password against its stored hash."""
    return password_hash.verify_and_update(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return password_hash.hash(password)


def password_fingerprint(hashed_password: str) -> str:
    """Return a short digest of a password hash."""
    return hashlib.sha256(hashed_password.encode()).hexdigest()[:16]


def generate_email_token(
    *, audience: str, claims: dict[str, str], expires_in: timedelta
) -> str:
    """Create a signed, expiring token for an emailed link."""
    now = datetime.now(UTC)
    return jwt.encode(
        {**claims, "aud": audience, "nbf": now, "exp": now + expires_in},
        auth_settings.SECRET_KEY,
        algorithm=ALGORITHM,
    )


def verify_email_token(token: str, *, audience: str) -> dict[str, Any] | None:
    """Return the claims of a valid token for the audience, otherwise None."""
    try:
        return jwt.decode(
            token,
            auth_settings.SECRET_KEY,
            algorithms=[ALGORITHM],
            audience=audience,
        )
    except InvalidTokenError:
        return None


def generate_password_reset_token(email: str, hashed_password: str) -> str:
    """Create a password reset token for the email."""
    return generate_email_token(
        audience=PASSWORD_RESET_AUDIENCE,
        claims={"sub": email, "pwd": password_fingerprint(hashed_password)},
        expires_in=timedelta(minutes=auth_settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES),
    )


def verify_password_reset_token(token: str) -> tuple[str, str] | None:
    """Return the email and password fingerprint in a valid reset token, otherwise None."""
    claims = verify_email_token(token, audience=PASSWORD_RESET_AUDIENCE)
    if not claims or "sub" not in claims or "pwd" not in claims:
        return None
    return str(claims["sub"]), str(claims["pwd"])
