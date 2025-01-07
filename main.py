import logging
from src.voice_assistant import VoiceAssistant

def pretty_print_messages(update):
    print(update)

def main():
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()]
    )
    assistant = VoiceAssistant()
    try:
        assistant.run()
    except KeyboardInterrupt:
        logging.info("Voice Assistant terminato dall'utente.")
    finally:
        logging.info("Chiusura del Voice Assistant.")

if __name__ == "__main__":
    main()
