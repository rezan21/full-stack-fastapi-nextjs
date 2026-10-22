from src.exceptions import NotFound, PermissionDenied
from src.items.constants import ErrorCode


class ItemNotFound(NotFound):
    DETAIL = ErrorCode.ITEM_NOT_FOUND


class NotEnoughPermissions(PermissionDenied):
    DETAIL = ErrorCode.NOT_ENOUGH_PERMISSIONS
