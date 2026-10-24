from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class AgentMessage:
    id: str
    role: Literal["user", "assistant"]
    content: str
