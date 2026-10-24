import uuid

from pydantic import BaseModel


class AgentContext(BaseModel):
    user_id: uuid.UUID
