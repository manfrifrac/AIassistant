from typing_extensions import TypedDict
from typing import Dict, Any
from datetime import datetime
from .base import BaseDbModel

class UserPreferences(TypedDict):
    """User preferences structure"""
    language: str
    notification_enabled: bool
    custom_settings: Dict[str, Any]

class User(BaseDbModel):
    """User model matching database schema"""
    name: str
    preferences: UserPreferences
    created_at: datetime
