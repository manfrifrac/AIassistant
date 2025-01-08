import logging
from src.voice_assistant import VoiceAssistant
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')


def main():
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("logs/app.log", mode="a", encoding="utf-8"),
        ]
    )
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


    assistant = VoiceAssistant()
    try:
        assistant.run()
    except KeyboardInterrupt:
        logging.info("Voice Assistant terminated by user.")
    finally:
        logging.info("Closing Voice Assistant.")

if __name__ == "__main__":
    main()
