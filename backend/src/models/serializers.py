from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from uuid import UUID

class MessageRequest(BaseModel):
    message: str
    user_id: UUID
    session_id: Optional[UUID] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class MessageResponse(BaseModel):
    message: str
    session_id: UUID
    metadata: Dict[str, Any] = Field(default_factory=dict)
    status: str = "success"
    audio_response: Optional[str] = None

class AudioRequest(BaseModel):
    user_id: UUID
    session_id: Optional[UUID] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
