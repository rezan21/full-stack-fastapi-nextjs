from src.exceptions import ServiceUnavailable


class DatabaseUnavailable(ServiceUnavailable):
    DETAIL = "Database unavailable"
