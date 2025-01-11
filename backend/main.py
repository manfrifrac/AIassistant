from backend.src.voice_assistant import VoiceAssistant
from backend.src.state.state_manager import StateManager
from backend.src.state.state_schema import StateSchema
from backend.src.utils.log_config import setup_logging
from backend.src.api import app  # Import the app directly instead of the module
import logging
import uvicorn
from fastapi import FastAPI

def main():
    # Clear any existing handlers before setup
    logging.getLogger().handlers = []
    
    debug_mode = True  # Esplicita l'impostazione
    
    # Setup logging con debug mode
    setup_logging(global_debug_mode=debug_mode)
    logger = logging.getLogger(__name__)
    
    # Verifica il livello di logging
    print(f"Main logger level: {logger.getEffectiveLevel()}")
    print(f"Root logger level: {logging.getLogger().getEffectiveLevel()}")
    
    logger.debug("Debug logging test message")  # Questo messaggio apparirà solo se debug_mode è True
    logger.info("Starting Voice Assistant")
    
    # Initialize variables before try block using CoreComponents
    from backend.src.core_components import CoreComponents  # Local import to prevent circular dependency
    core = CoreComponents.get_instance()
    
    try:
        logger.debug("Stato iniziale: %s", core.state_manager.state)

        if core.assistant.listening:
            core.assistant.run()
                
    except KeyboardInterrupt:
        logger.info("Voice Assistant terminated by user.")
    except Exception as e:
        logger.error("Unexpected error: %s", e, exc_info=True)
    finally:
        core.assistant.update_state("")
        logger.debug("Stato dopo update_state: %s", core.state_manager.state)
        logger.info("Voice Assistant shutdown complete.")

    # Run the FastAPI application
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    main()
