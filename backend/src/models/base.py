from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel

class BaseDbModel(BaseModel):
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self):
        """Convert model to dictionary, excluding None values"""
        return self.model_dump(exclude_none=True)  # For Pydantic v2
        # Use self.dict(exclude_none=True) for Pydantic v1

@dataclass
class BaseMessageModel:
    """Base model for messages"""
    content: str
    timestamp: datetime
    type: str
