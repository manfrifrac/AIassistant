from typing import TypedDict, Dict, Any, Union, List, Optional
from datetime import datetime
from .base import BaseDbModel

class MemoryData(TypedDict):
    important_info: List[str]
    metadata: Dict[str, Any]

class Memory(BaseDbModel):
    """Memory model matching database schema"""
    def __init__(self,
                 content: str,
                 memory_type: str,
                 user_id: Optional[str] = None,
                 id: Optional[int] = None,
                 key: Optional[str] = None,
                 value: Optional[str] = None,
                 timestamp: Optional[datetime] = None,
                 created_at: Optional[datetime] = None,
                 updated_at: Optional[datetime] = None):
        super().__init__()
        self.id = id
        self.user_id = user_id
        self.content = content
        self.memory_type = memory_type
        self.key = key
        self.value = value
        self.timestamp = timestamp or datetime.now()
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
