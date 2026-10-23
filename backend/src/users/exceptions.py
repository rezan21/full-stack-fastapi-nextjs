from src.exceptions import BadRequest, PermissionDenied


class SuperuserCannotDelete(PermissionDenied):
    DETAIL = "Super users are not allowed to delete themselves"


class PasswordUnchanged(BadRequest):
    DETAIL = "New password cannot be the same as the current one"
