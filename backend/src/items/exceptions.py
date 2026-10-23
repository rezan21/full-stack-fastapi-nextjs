from src.exceptions import NotFound, PermissionDenied


class ItemNotFound(NotFound):
    DETAIL = "Item not found"


class NotEnoughPermissions(PermissionDenied):
    DETAIL = "Not enough permissions"
