import logging
import uvicorn
import signal

import uvicorn.logging
from backend.src.utils.log_config import setup_logging
from backend.src.state.state_manager import StateManager
from backend.src.state.state_schema import StateSchema
from backend.src.voice_assistant import VoiceAssistant
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from backend.src.api import app  # Importa app direttamente da api.py

def handle_interrupt(signum, frame):
    """Gestore per interruzioni (Ctrl+C)"""
    logger = logging.getLogger(__name__)
    logger.info("Interruzione rilevata, chiusura in corso...")
    exit(0)

def start_frontend():
    # Registra handler per SIGINT
    signal.signal(signal.SIGINT, handle_interrupt)
    
    # Setup logging solo se non è già stato fatto
    if not logging.getLogger().handlers:
        setup_logging(global_debug_mode=True)
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Frontend Server")

    # Initialize state manager and voice assistant for logging purposes
    state_manager = StateManager()
    state_manager.set_state_schema(StateSchema)
    assistant = VoiceAssistant(state_manager)
    assistant.is_web_mode = True  # Imposta il web mode
    
    logger.debug("Stato iniziale: %s", state_manager.state)

    # Define the app variable
    app = FastAPI()

    # Correggi il percorso per puntare alla directory corretta
    frontend_build_path = Path(__file__).parent.parent / "frontend/appfront/build"
    app.mount("/", StaticFiles(directory=frontend_build_path, html=True), name="build")

    try:
        uvicorn.run(
            "src.api:app",  # Cambiato per riferirsi al modulo corretto
            host="0.0.0.0", 
            port=8000, 
            reload=True,  # Riabilitato il reload
            log_level="debug"
        )
    except KeyboardInterrupt:
        logger.info("Chiusura ordinata del server...")
    except Exception as e:
        logger.error(f"Errore durante l'esecuzione del server: {e}", exc_info=True)
    finally:
        logger.info("Server fermato")

if __name__ == "__main__":
    start_frontend()
