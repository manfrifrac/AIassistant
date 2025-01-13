from typing import Optional
import logging
from backend.src.state.state_manager import StateManager
from backend.src.voice_assistant import VoiceAssistant
from backend.src.memory_store import MemoryStore
from backend.src.database.database import Database  # Import the existing Database class

logger = logging.getLogger("CoreComponents")

class CoreComponents:
    _instance: Optional['CoreComponents'] = None

    def __init__(self):
        self.db = Database.get_instance()  # Use the singleton instance
        self.memory_store = MemoryStore()
        self.state_manager = StateManager(self.memory_store, self.db)
        self.assistant = VoiceAssistant(self.state_manager)
        logger.info("Core components initialized")

    @classmethod
    def get_instance(cls) -> 'CoreComponents':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def initialize(self):
        """Initialize any components that need startup configuration"""
        pass