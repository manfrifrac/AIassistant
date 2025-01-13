# src/state/state_manager.py

import logging
from typing import Type, get_origin, get_args, Dict, Any, Optional, TypeVar, cast, TypedDict, List, Literal, Sequence, Union
from backend.src.state.state_schema import StateSchema as BaseStateSchema, manage_short_term_memory, manage_long_term_memory, Context
from backend.src.memory_store import MemoryStore
from typing_extensions import Annotated
from backend.src.utils.log_config import setup_logging
from ..models.interaction import Interaction
from ..models.user import User
from ..models.memory import Memory
from datetime import datetime
from uuid import uuid4, UUID
from ..database.database import Database
from enum import Enum
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine
from sqlalchemy import insert
from contextlib import asynccontextmanager

T = TypeVar('T', bound=Dict[str, Any])

logger = logging.getLogger("StateManager")

class InteractionType(Enum):
    USER = "user"
    AGENT = "agent"

class StateSchema(TypedDict):
    short_term_memory: List[Dict[str, Any]]  # Changed from Sequence[Context]
    long_term_memory: Dict[str, Any]  # Remove Optional since TypedDict doesn't support it
    session_id: str
    should_terminate: bool
    user: Optional[User]
    interactions: List[Interaction]
    user_messages: List[Dict[str, Any]]
    agent_messages: List[Dict[str, Any]]
    memory: Optional[Memory]
    processed_messages: List[str]
    terminate: bool
    contexts: List[Dict[str, Any]]  # Added missing field
    last_user_message: Optional[str]  # Add this field
    next_agent: Optional[str]  # Add this field

class StateManager:
    def __init__(self, memory_store, db: Database):
        self.memory_store = memory_store
        self.db = db
        self._interactions = db.interactions  # Access through property instead of get_collection
        self._state: StateSchema = {
            "user": None,
            "session_id": "",
            "interactions": [],
            "user_messages": [],
            "agent_messages": [],
            "memory": None,
            "short_term_memory": [],
            "long_term_memory": {},
            "processed_messages": [],
            "terminate": False,
            "should_terminate": False,
            "contexts": [],  # Added missing field
            "last_user_message": None,  # Add this field
            "next_agent": None  # Add this field
        }
        self.state_schema = StateSchema  # Add this line to initialize state_schema
        self.state = self._state  # Add state property
        logger.debug("StateManager initialized with database schema.")

    @property
    def state(self) -> StateSchema:
        return self._state

    @state.setter 
    def state(self, value: StateSchema):
        self._state = value

    def set_state_schema(self, schema: Type[StateSchema]):
        """Imposta un nuovo schema per lo stato."""
        self.state_schema = schema
        logger.debug("StateSchema aggiornato in StateManager.")

    def _format_state_for_log(self, state_dict: dict) -> dict:
        """Formatta lo stato per il logging in modo più leggibile"""
        return {
            key: (
                value[-3:] if isinstance(value, list) and key in ['user_messages', 'agent_messages'] 
                else value
            )
            for key, value in state_dict.items()
            if key in ['user_messages', 'agent_messages', 'last_agent', 'next_agent']
        }

    async def update_state(self, updates: dict) -> None:
        """Aggiorna lo stato con i nuovi valori forniti"""
        if not isinstance(updates, dict):
            logger.error("Updates must be a dictionary")
            return

        # Update last_user_message if there are user messages
        if "user_messages" in updates and updates["user_messages"]:
            updates["last_user_message"] = updates["user_messages"][-1]["content"]

        for key, value in updates.items():
            if key in StateSchema.__annotations__:
                annotation = StateSchema.__annotations__[key]
                origin = get_origin(annotation)

                if origin is list:
                    if key == "short_term_memory":
                        self.state[key] = list(manage_short_term_memory(self.state[key], value))
                    else:
                        self.state[key].extend(value)
                elif key == "long_term_memory" and value:
                    self.state[key] = await manage_long_term_memory(self.state.get(key), value)
                else:
                    self.state[key] = value
                    
                logger.debug(f"Updated {key}: {str(self.state[key])[:100]}...")
            else:
                logger.warning(f"Unknown state key: {key}")

        self.validate_state()

        # Log before deduplication
        logger.debug("Pre-deduplication processed_messages: %s", self.state.get('processed_messages', []))

        # Ensure terminate remains False
        self.state["terminate"] = False  

        # Elimina duplicati mantenendo l'ordine in 'processed_messages'
        seen = set()
        unique_processed = []
        for msg in self.state.get("processed_messages", []):
            if msg not in seen:
                seen.add(msg)
                unique_processed.append(msg)
        self.state["processed_messages"] = unique_processed

        if "long_term_memory" in updates:
            # Merge long-term memory updates
            self.memory_store.save_to_long_term_memory("long_term_namespace", "memory_key", updates["long_term_memory"])
            logger.debug("Memoria a lungo termine aggiornata.")
        
        # Log after deduplication
        logger.debug("Post-deduplication processed_messages: %s", self.state['processed_messages'])
        logger.debug("Stato dopo update_state: %s", self.state)
        
        # **Log current agent_messages**
        logger.debug("Current agent_messages: %s", self.state.get('agent_messages', []))

        # Log in modo più leggibile
        logger.debug("Pre-deduplication processed_messages count: %d", 
                     len(self.state.get('processed_messages', [])))
        logger.debug("Post-deduplication processed_messages count: %d", 
                     len(self.state['processed_messages']))
    
        formatted_state = self._format_state_for_log(dict(self.state))
        logger.debug("State after update: %s", formatted_state)

    def validate_state(self):
        """Valida lo stato attuale contro lo StateSchema."""
        try:
            for key, value in self.state.items():
                if key in StateSchema.__annotations__:
                    expected_type = StateSchema.__annotations__[key]
                    origin = get_origin(expected_type)
                    args = get_args(expected_type)
                    
                    # Handle Optional types
                    if origin is Union and type(None) in args:
                        expected_type = next(arg for arg in args if arg != type(None))
                        if value is not None and not isinstance(value, expected_type):
                            logger.warning(f"Invalid type for '{key}': expected {expected_type}, got {type(value)}")
                        continue
                        
                    if origin is list:
                        if not isinstance(value, list):
                            logger.warning(f"Invalid type for '{key}': expected list, got {type(value)}")
                    elif origin is dict:
                        if not isinstance(value, dict):
                            logger.warning(f"Invalid type for '{key}': expected dict, got {type(value)}")
                    elif value is not None and not isinstance(value, expected_type):
                        logger.warning(f"Invalid type for '{key}': expected {expected_type}, got {type(value)}")
                        
            logger.debug("State validation completed successfully")
        except Exception as e:
            logger.error(f"Error during state validation: {e}")

    def get_assistant_message(self) -> Optional[str]:
        """Recupera l'ultimo messaggio generato dall'assistente."""
        if "agent_messages" in self.state and self.state["agent_messages"]:
            return self.state["agent_messages"][-1].get("content")
        return None

    def to_dict(self):
        """Convert the state to a dictionary."""
        return dict(self.state)

    def get_state(self) -> Dict[str, Any]:
        """Get current state"""
        return cast(Dict[str, Any], self.state.copy())

    def get_current_state(self) -> Dict[str, Any]:
        """Alias for get_state"""
        return self.get_state()

    def add_user_message(self, message: Dict[str, Any]) -> None:
        """Add a user message to state"""
        if "user_messages" not in self.state:
            self.state["user_messages"] = []
        self.state["user_messages"].append(message)

    def create_interaction(self, content: str, interaction_type: InteractionType, agent_id: Optional[str] = None) -> Interaction:
        """Create interaction object"""
        current_user = self.state.get("user")
        return Interaction(
            id=None,
            content=content,
            interaction_type=interaction_type.value,
            user_id=current_user.id if current_user else None,
            agent_id=agent_id
        )

    def append_interaction(self, data: Dict[str, Any]) -> None:
        interaction = Interaction(
            id=None,
            content=data["content"],
            interaction_type=data["type"],
            user_id=int(data["user_id"]) if data.get("user_id") else None,
            agent_id=data.get("agent_id")
        )
        self.state["interactions"].append(interaction)

    async def save_interaction(self, user: User, content: str, interaction_type: InteractionType, agent_id: Optional[str] = None) -> None:
        """Save interaction to database"""
        interaction_data = {
            "session_id": self.state["session_id"],
            "user_id": user.id,
            "content": content,
            "interaction_type": interaction_type.value,
            "agent_id": agent_id,
            "created_at": datetime.utcnow()
        }
        async with self.db.get_session() as session:  # Remove await
            await session.execute(insert(self._interactions).values(interaction_data))

    async def create_agent_interaction(self, user: User, content: str, agent_id: str) -> None:
        """Create agent interaction record"""
        async with self.db.get_session() as session:  # Remove await
            await session.execute(
                insert(self._interactions).values({
                    "session_id": self.state["session_id"],
                    "user_id": user.id, 
                    "content": content,
                    "interaction_type": InteractionType.AGENT.value,
                    "agent_id": agent_id,
                    "created_at": datetime.utcnow()
                })
            )

    def update_long_term_memory(self, memory: Dict[str, Any]) -> None:
        if isinstance(self._state, dict):
            self._state["long_term_memory"] = memory
        else:
            self._state.long_term_memory = memory

    def update_context(self, contexts: List[Dict[str, Any]]) -> None:
        """Update contexts with proper typing"""
        self.state["contexts"] = contexts  # Store as Dict instead of Context objects

    def manage_short_term_memory(self, existing: List[Dict[str, Any]], new_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Manage short term memory with consistent typing"""
        if not existing and not new_items:
            return []
        # ...implementation...
        return (existing + new_items)[-100:]  # Always return a list