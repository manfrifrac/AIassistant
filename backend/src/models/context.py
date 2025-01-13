from typing import TypedDict, Dict, Any, List
from .interaction import Interaction
from .memory import Memory

class Context(TypedDict):
    """Context model for agent interactions"""
    user_message: str
    stm_data: List[Interaction]  # Short-term memory (recent messages)
    ltm_data: Dict[str, Memory]  # Long-term memory (persistent data)
    agent_specific_data: Dict[str, Any]  # Additional data for specific agents
