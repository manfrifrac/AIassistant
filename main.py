import logging
from src.voice_assistant import VoiceAssistant
import sys
from langgraph.types import Command
from typing import Literal
from src.tools.llm_tools import generate_response
from langgraph.graph import END  # Importa END se necessario

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
    logging.getLogger("StateManager").setLevel(logging.DEBUG)
    logging.getLogger("VoiceAssistant").setLevel(logging.DEBUG)
    logging.getLogger("SupervisorAgent").setLevel(logging.DEBUG)
    logging.getLogger("ResearcherAgent").setLevel(logging.DEBUG)
    logging.getLogger("GreetingAgent").setLevel(logging.DEBUG)
    logging.getLogger("LLMTools").setLevel(logging.WARNING)
    logging.getLogger("PythonREPLTool").setLevel(logging.DEBUG)
    logging.getLogger("SpotifyTools").setLevel(logging.DEBUG)
    logging.getLogger("TTS").setLevel(logging.DEBUG)
    logging.getLogger("AudioHandler").setLevel(logging.WARNING)
    logging.getLogger("ErrorHandler").setLevel(logging.DEBUG)
    logging.getLogger("StateManager").setLevel(logging.DEBUG)

    assistant = VoiceAssistant()
    try:
        while True:
            thread_id = input("Inserisci un thread ID (o premi Enter per continuare): ")
            if thread_id:
                assistant.set_thread_id(thread_id)
            assistant.run()
    except KeyboardInterrupt:
        logging.info("Voice Assistant terminato dall'utente.")
    finally:
        logging.info("Chiusura del Voice Assistant.")

if __name__ == "__main__":
    main()
