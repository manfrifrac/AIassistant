from typing import TypedDict, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from .base import BaseDbModel

class Agent(BaseDbModel):
    """Agent model matching database schema"""
    name: str
    task: str
    parameters: Dict[str, Any]

class AgentMessage(BaseDbModel):
    """Model for agent messages"""
    agent_id: int
    content: str
    role: str
