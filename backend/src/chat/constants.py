from datetime import timedelta
from enum import StrEnum

CONVERSATION_TITLE_MAX_LENGTH = 60
MAX_MESSAGE_CHARS = 4000
MESSAGES_PAGE_SIZE = 100
MAX_MESSAGES_PAGE_SIZE = 500
RUN_ID_MAX_LENGTH = 100
QUOTA_WINDOW = timedelta(hours=1)
MAX_OUTPUT_TOKENS = 8192
MODEL_TIMEOUT_SECONDS = 60
MODEL_MAX_RETRIES = 2
POOL_MAX_SIZE = 4
RECURSION_LIMIT = 30
GENERIC_ERROR = "The assistant ran into a problem. Please try again."
SYSTEM_PROMPT = "You are a helpful assistant. Keep answers concise."


class ErrorCode(StrEnum):
    CONVERSATION_NOT_FOUND = "Conversation not found"
    NOT_CONFIGURED = "AI chat is not configured"
    NO_USER_MESSAGE = "The request has no user message"
    EMPTY_MESSAGE = "The message must be non-empty text"
    MESSAGE_TOO_LONG = "The message is over {limit} characters"
    QUOTA_EXCEEDED = "Too many messages. Try again in {wait}."
