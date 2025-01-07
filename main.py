# main.py

import logging
import os
from src.voice_assistant import VoiceAssistant

def setup_logging():
    # Verifica se la directory 'logs' esiste, altrimenti creala
    log_directory = "logs"
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)
        print(f"Directory '{log_directory}' creata per i log.")
    
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(os.path.join(log_directory, "app.log")),
            logging.StreamHandler()
        ]
    )
    # Configura i logger per i moduli specifici
    logging.getLogger("LLMTools").setLevel(logging.DEBUG)
    logging.getLogger("SpotifyTools").setLevel(logging.DEBUG)
    logging.getLogger("SupervisorAgent").setLevel(logging.DEBUG)
    logging.getLogger("VoiceAssistant").setLevel(logging.DEBUG)
    logging.getLogger("PythonREPLTool").setLevel(logging.DEBUG)
    logging.getLogger("TimeTools").setLevel(logging.DEBUG)
    logging.getLogger("TTS").setLevel(logging.DEBUG)

if __name__ == "__main__":
    setup_logging()
    logger = logging.getLogger("Main")
    logger.info("Voice Assistant with ToolNode and Spotify. Press Ctrl+C to exit.")
    
    assistant = VoiceAssistant()
    try:
        assistant.run()
    except KeyboardInterrupt:
        logger.info("Voice Assistant terminato dall'utente.")
        print("Voice Assistant terminato.")
    except Exception as e:
        logger.error(f"Errore inatteso: {e}")
        print(f"Errore inatteso: {e}")
    finally:
        logger.info("Chiusura del Voice Assistant.")
