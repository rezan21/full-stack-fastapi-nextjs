from math import ceil

from src.exceptions import BadRequest, NotFound, ServiceUnavailable, TooManyRequests
from src.utils import describe_duration


class ConversationNotFound(NotFound):
    DETAIL = "Conversation not found"


class ChatNotConfigured(ServiceUnavailable):
    DETAIL = "AI chat is not configured"


class InvalidChatInput(BadRequest):
    pass


class NoUserMessage(InvalidChatInput):
    DETAIL = "The request has no user message"


class EmptyMessage(InvalidChatInput):
    DETAIL = "The message must be non-empty text"


class MessageTooLong(InvalidChatInput):
    def __init__(self, limit: int) -> None:
        super().__init__(f"The message is over {limit} characters")


class InvalidToolResult(InvalidChatInput):
    def __init__(self, limit: int) -> None:
        super().__init__(f"The tool result must be text of at most {limit} characters")


class NoPendingToolCall(InvalidChatInput):
    DETAIL = "No browser tool is waiting for that result"


class ChatQuotaExceeded(TooManyRequests):
    def __init__(self, retry_after: int) -> None:
        wait = describe_duration(ceil(retry_after / 60))
        super().__init__(
            f"Too many messages. Try again in {wait}.", retry_after=retry_after
        )
