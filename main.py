import logging
from src.voice_assistant import VoiceAssistant
import sys
from langgraph.types import Command
from typing import Literal
from src.tools.llm_tools import generate_response, save_to_long_term_memory  # Ensure correct import
from langgraph.graph import END  # Importa END se necessario
from src.memory_store import MemoryStore  # Importa MemoryStore
from src.state.state_manager import StateManager
from src.state.state_schema import StateSchema  # Importa StateSchema

def main():
    logging.basicConfig(
        level=logging.INFO,  # Cambiato da DEBUG a INFO
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("logs/app.log", mode="a", encoding="utf-8"),
        ]
    )
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    # Riduci la verbosità dei log di gtts e urllib3
    logging.getLogger("gtts").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    # Altri loggers specifici
    logging.getLogger("gtts.tts").setLevel(logging.WARNING)

    logging.getLogger("LangGraphSetup").setLevel(logging.DEBUG)
    logging.getLogger("StateManager").setLevel(logging.INFO)
    logging.getLogger("VoiceAssistant").setLevel(logging.DEBUG)
    logging.getLogger("SupervisorAgent").setLevel(logging.INFO)
    logging.getLogger("ResearcherAgent").setLevel(logging.INFO)
    logging.getLogger("GreetingAgent").setLevel(logging.INFO)
    logging.getLogger("LLMTools").setLevel(logging.WARNING)
    logging.getLogger("PythonREPLTool").setLevel(logging.DEBUG)
    logging.getLogger("SpotifyTools").setLevel(logging.DEBUG)
    logging.getLogger("TTS").setLevel(logging.INFO)
    logging.getLogger("AudioHandler").setLevel(logging.WARNING)
    logging.getLogger("ErrorHandler").setLevel(logging.DEBUG)
    state_manager = StateManager()
    state_manager.set_state_schema(StateSchema)  # Passa il tipo, non un'istanza
    assistant = VoiceAssistant(state_manager)  # Pass StateManager instance

    try:
        iteration = 0
        max_iterations = 10  # Define a maximum number of iterations
        while iteration < max_iterations and assistant.listening:
            assistant.run()
            iteration += 1
        if iteration >= max_iterations:
            logging.warning("Numero massimo di iterazioni raggiunto. Terminazione forzata.")
    except KeyboardInterrupt:
        logging.info("Voice Assistant terminato dall'utente.")
    finally:
        # Salva la memoria a lungo termine prima di chiudere
        assistant.update_state("")
        logging.info("Chiusura del Voice Assistant.")

if __name__ == "__main__":
    main()
