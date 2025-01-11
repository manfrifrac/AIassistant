import logging
from backend.src.state.state_manager import StateManager
from backend.src.state.state_schema import StateSchema
from backend.src.memory_store import MemoryStore
from backend.src.langgraph_setup import initialize_graph, set_graph

logger = logging.getLogger("CoreComponents")

class CoreComponents:
    _instance = None
    _memory_store = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
            cls._instance.init_components()
        return cls._instance

    @classmethod
    def get_memory_store(cls):
        """Get the singleton MemoryStore instance"""
        if cls._memory_store is None:
            cls._memory_store = MemoryStore()
            logger.info("MemoryStore initialized")
        return cls._memory_store

    def init_components(self):
        """Initialize all components using the singleton MemoryStore"""
        self.memory_store = self.get_memory_store()
        self.state_manager = StateManager(self.memory_store)
        self.state_manager.set_state_schema(StateSchema)
        
        # Initialize and store graph
        compiled_graph = initialize_graph(self.memory_store)
        set_graph(compiled_graph)
        logger.info("LangGraphSetup initialized")
        
        # Initialize VoiceAssistant with state_manager
        from backend.src.voice_assistant import VoiceAssistant
        self.assistant = VoiceAssistant(self.state_manager)
        logger.info("VoiceAssistant initialized")
        
        logger.info("Core components initialized")