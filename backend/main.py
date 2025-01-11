from src.voice_assistant import VoiceAssistant
from src.state.state_manager import StateManager
from src.state.state_schema import StateSchema
from src.utils.log_config import setup_logging
from src.api import app  # Import the app directly instead of the module
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
    
    # Initialize variables before try block
    state_manager = StateManager()
    state_manager.set_state_schema(StateSchema)
    assistant = VoiceAssistant(state_manager)
    
    try:
        logger.debug("Stato iniziale: %s", state_manager.state)

        iteration = 0
        max_iterations = 10
        while iteration < max_iterations and assistant.listening:
            assistant.run()
            iteration += 1
            
        if iteration >= max_iterations:
            logger.warning("Maximum iterations reached. Forced termination.")
            
    except KeyboardInterrupt:
        logger.info("Voice Assistant terminated by user.")
    except Exception as e:
        logger.error("Unexpected error: %s", e, exc_info=True)
    finally:
        assistant.update_state("")
        logger.debug("Stato dopo update_state: %s", state_manager.state)
        logger.info("Voice Assistant shutdown complete.")

    # Run the FastAPI application
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    main()
