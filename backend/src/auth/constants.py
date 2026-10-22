from enum import StrEnum

PASSWORD_MAX_LENGTH = 128
ALGORITHM = "HS256"
ACCESS_AUDIENCE = "access"
PASSWORD_RESET_AUDIENCE = "password-reset"
DUMMY_HASH = "$argon2id$v=19$m=65536,t=3,p=4$MjQyZWE1MzBjYjJlZTI0Yw$YTU4NGM5ZTZmYjE2NzZlZjY0ZWY3ZGRkY2U2OWFjNjk"


class ErrorCode(StrEnum):
    INVALID_CREDENTIALS = "Could not validate credentials"
    INACTIVE_USER = "Inactive user"
    INCORRECT_LOGIN = "Incorrect email or password"
    INCORRECT_PASSWORD = "Incorrect password"
    INVALID_TOKEN = "Invalid token"
    ACCOUNT_LOCKED = "Too many failed attempts. Try again in {wait}."
