import logging
from src.voice_assistant import VoiceAssistant
import sys

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
    logging.getLogger("supervisor_agent").setLevel(logging.DEBUG)
    logging.getLogger("researcher_agent").setLevel(logging.DEBUG)
    logging.getLogger("greeting_agent").setLevel(logging.DEBUG)
    logging.getLogger("LLMTools").setLevel(logging.DEBUG)
    logging.getLogger("PythonREPLTool").setLevel(logging.DEBUG)
    logging.getLogger("SpotifyTools").setLevel(logging.DEBUG)
    logging.getLogger("TTS").setLevel(logging.DEBUG)
    logging.getLogger("AudioHandler").setLevel(logging.DEBUG)
    logging.getLogger("ErrorHandler").setLevel(logging.DEBUG)
    logging.getLogger("StateManager").setLevel(logging.DEBUG)

    assistant = VoiceAssistant()
    try:
        assistant.run()
    except KeyboardInterrupt:
        logging.info("Voice Assistant terminated by user.")
    finally:
        logging.info("Closing Voice Assistant.")

if __name__ == "__main__":
    main()
