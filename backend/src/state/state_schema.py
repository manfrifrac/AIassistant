# src/state_schema.py

from typing import TypedDict, List, Dict, Any, Optional
from ..models.interaction import Interaction
from ..models.memory import Memory
from ..models.context import Context
from ..models.user import User
from ..models.base import BaseDbModel

class StateSchema(TypedDict, total=True):
    """Schema dello stato basato sui modelli del database"""
    # User context & session
    user: Optional[User]
    session_id: Optional[str]
    interactions: List[Interaction]
    
    # Messages
    user_messages: List[Dict[str, Any]]
    agent_messages: List[Dict[str, Any]]
    processed_messages: List[str]
    
    # State flags
    terminate: bool
    should_terminate: bool
    
    # Memory
    memory: Optional[Memory]
    short_term_memory: List[Context]
    long_term_memory: Optional[Dict[str, Any]]
    
    # Flow control
    next_agent: Optional[str]  # Add this field
    contexts: List[Dict[str, Any]]
    
    # Last user message
    last_user_message: Optional[str]

def manage_short_term_memory(existing: List[Dict[str, Any]], new_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Gestisce la memoria a breve termine mantenendo solo gli elementi recenti e unici"""
    if not new_items:
        return existing[-100:] if existing else []
    return (existing + new_items)[-100:]

async def manage_long_term_memory(existing: Dict[str, Any], new_items: Dict[str, Any]) -> Dict[str, Any]:
    """Merge existing and new memory items"""
    if not existing:
        return new_items
    result = existing.copy()
    result.update(new_items)
    return result

def manage_list(old: List[Any], new: List[Any]) -> List[Any]:
    """Generic list management with deduplication"""
    combined = old + new
    unique = []
    seen = set()
    for item in combined:
        item_key = str(item) if not isinstance(item, dict) else str(sorted(item.items()))
        if item_key not in seen:
            seen.add(item_key)
            unique.append(item)
    return unique

