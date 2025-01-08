from gtts import gTTS
import logging
import os

logger = logging.getLogger("TTS")

def generate_speech(text, language="it", output_file="output.mp3"):
    """
    Genera parlato da testo utilizzando Google Text-to-Speech.
    """
    try:
        tts = gTTS(text=text, lang=language, slow=False)
        tts.save(output_file)
        if os.path.exists(output_file):
            logger.debug(f"Parlato generato correttamente in {output_file}")
        else:
            logger.error(f"Errore: il file {output_file} non è stato creato.")
        return output_file
    except Exception as e:
        logger.error(f"Errore durante la generazione del parlato: {e}")
        return ""
