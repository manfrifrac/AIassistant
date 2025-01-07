# main.py

import logging
from src.voice_assistant import VoiceAssistant

# Configurazione del logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

def main():
    assistant = VoiceAssistant()
    try:
        assistant.run()
    except KeyboardInterrupt:
        logging.info("Voice Assistant terminato dall'utente.")
    finally:
        logging.info("Chiusura del Voice Assistant.")

if __name__ == "__main__":
    main()
