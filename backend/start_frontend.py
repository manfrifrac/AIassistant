import logging
import uvicorn
import signal

from src.utils.log_config import setup_logging
from src.state.state_manager import StateManager
from src.state.state_schema import StateSchema
from src.voice_assistant import VoiceAssistant
from pathlib import Path
from fastapi import FastAPI

def handle_interrupt(signum, frame):
    """Gestore per interruzioni (Ctrl+C)"""
    logger = logging.getLogger(__name__)
    logger.info("Interruzione rilevata, chiusura in corso...")
    exit(0)

def start_frontend():
    # Registra handler per SIGINT
    signal.signal(signal.SIGINT, handle_interrupt)
    
    # Clear any existing handlers before setup
    logging.getLogger().handlers = []
    
    debug_mode = True
    
    # Setup logging con debug mode
    setup_logging(global_debug_mode=debug_mode)
    logger = logging.getLogger(__name__)
    
    # Verifica il livello di logging
    logger.debug("Debug logging test message")
    logger.info("Starting Frontend Server")

    # Initialize state manager and voice assistant for logging purposes
    state_manager = StateManager()
    state_manager.set_state_schema(StateSchema)
    assistant = VoiceAssistant(state_manager)
    
    logger.debug("Stato iniziale: %s", state_manager.state)

    # Define the app variable
    app = FastAPI()

    # Serve React build from the new frontend_react directory
    from fastapi.staticfiles import StaticFiles
    app.mount("/", StaticFiles(directory=Path(__file__).parent / "frontend_react" / "build", html=True), name="build")

    try:
        uvicorn.run(
            "src.api:app", 
            host="0.0.0.0", 
            port=8000, 
            reload=True,
            log_config=None,  # Remove custom log_config
            log_level="debug" if debug_mode else "info"
        )
    except KeyboardInterrupt:
        logger.info("Chiusura ordinata del server...")
    except Exception as e:
        logger.error(f"Errore durante l'esecuzione del server: {e}", exc_info=True)
    finally:
        logger.info("Server fermato")

if __name__ == "__main__":
    start_frontend()
