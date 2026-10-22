from math import ceil

from src.chat.constants import ErrorCode
from src.exceptions import BadRequest, NotFound, ServiceUnavailable, TooManyRequests
from src.utils import describe_duration


class ConversationNotFound(NotFound):
    DETAIL = ErrorCode.CONVERSATION_NOT_FOUND


class ChatNotConfigured(ServiceUnavailable):
    DETAIL = ErrorCode.NOT_CONFIGURED


class InvalidChatInput(BadRequest):
    pass


class ChatQuotaExceeded(TooManyRequests):
    def __init__(self, retry_after: int) -> None:
        wait = describe_duration(ceil(retry_after / 60))
        super().__init__(
            ErrorCode.QUOTA_EXCEEDED.format(wait=wait), retry_after=retry_after
        )
