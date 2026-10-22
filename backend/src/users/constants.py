from enum import StrEnum

SIGNUP_AUDIENCE = "signup"
EMAIL_CHANGE_AUDIENCE = "email-change"


class ErrorCode(StrEnum):
    SUPERUSER_CANNOT_DELETE = "Super users are not allowed to delete themselves"
    PASSWORD_UNCHANGED = "New password cannot be the same as the current one"
