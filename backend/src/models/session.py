from typing import TypedDict
from datetime import datetime
from .base import BaseDbModel

class Session(BaseDbModel):
    """Session model matching database schema"""
    user_id: int
    token: str
    active: bool
    expires_at: datetime
