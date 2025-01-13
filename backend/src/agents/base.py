from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Literal, TypeVar, Union
from uuid import UUID
from langgraph.types import Command
from langchain_openai import ChatOpenAI
import logging

# Define common node types
NodeType = Literal["supervisor", "researcher", "greeting", "manage_memory", "__end__"]

class BaseAgent(ABC):
    def __init__(self, agent_id: UUID, config: Dict[str, Any]):
        self.agent_id = agent_id
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.llm = ChatOpenAI(model=config.get("model", "gpt-3.5-turbo"))

    @abstractmethod
    def process(self, state: dict) -> Command[NodeType]:
        """Process the current state and return next command"""
        pass

    def validate_state(self, state: Dict[str, Any]) -> bool:
        """Validate the input state"""
        return True

    def handle_error(self, error: Exception) -> Dict[str, Any]:
        """Common error handling method"""
        self.logger.error(f"Error in {self.__class__.__name__}: {error}", exc_info=True)
        return {
            "error": str(error),
            "terminate": False,
            "agent": self.__class__.__name__
        }

    def _format_debug_state(self, state: dict) -> dict:
        """Enhanced debug state formatting"""
        base_info = {
            'agent_id': str(self.agent_id),
            'agent_type': self.__class__.__name__,
            'last_message': state.get('last_user_message', ''),
            'processed_count': len(state.get('processed_messages', [])),
            'has_error': 'error' in state
        }
        if 'error' in state:
            base_info['error'] = state['error']
        return base_info
