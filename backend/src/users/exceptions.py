from src.exceptions import BadRequest, PermissionDenied
from src.users.constants import ErrorCode


class SuperuserCannotDelete(PermissionDenied):
    DETAIL = ErrorCode.SUPERUSER_CANNOT_DELETE


class PasswordUnchanged(BadRequest):
    DETAIL = ErrorCode.PASSWORD_UNCHANGED
