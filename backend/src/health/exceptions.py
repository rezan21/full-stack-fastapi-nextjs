from src.exceptions import ServiceUnavailable
from src.health.constants import ErrorCode


class DatabaseUnavailable(ServiceUnavailable):
    DETAIL = ErrorCode.DATABASE_UNAVAILABLE
