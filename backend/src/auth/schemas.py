from typing import Annotated

from sqlmodel import Field, SQLModel

from src.models import Email

PASSWORD_MAX_LENGTH = 128

Password = Annotated[str, Field(min_length=8, max_length=PASSWORD_MAX_LENGTH)]
CurrentPassword = Annotated[str, Field(min_length=1, max_length=PASSWORD_MAX_LENGTH)]


class Credentials(SQLModel):
    username: Email
    password: CurrentPassword


class Token(SQLModel):
    access_token: str
    token_type: str
    expires_in: int


class TokenPayload(SQLModel):
    sub: str | None = None
    ver: int | None = None


class PasswordRecovery(SQLModel):
    email: Email


class NewPassword(SQLModel):
    token: str
    new_password: Password
