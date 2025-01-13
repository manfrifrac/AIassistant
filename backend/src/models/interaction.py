from datetime import datetime
from typing import Optional, Dict
from .base import BaseDbModel

class Interaction(BaseDbModel):
    def __init__(self, 
                 id: Optional[int] = None,
                 content: str = "",
                 interaction_type: str = "",
                 user_id: Optional[int] = None,
                 agent_id: Optional[str] = None,
                 data: Optional[Dict] = None,  # Added data field
                 created_at: Optional[datetime] = None,
                 updated_at: Optional[datetime] = None):
        super().__init__()
        self.id = id
        self.content = content
        self.interaction_type = interaction_type
        self.user_id = user_id
        self.agent_id = agent_id
        self.data = data or {}
        self.created_at = created_at or self.created_at
        self.updated_at = updated_at or self.updated_at
