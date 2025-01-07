from gtts import gTTS
import logging

logger = logging.getLogger("TTS")

def generate_speech(text, language="it", output_file="output.mp3"):
    """
    Genera parlato da testo utilizzando Google Text-to-Speech.

    Args:
        text (str): Testo da convertire in parlato.
        language (str): Codice della lingua (es. "it" per italiano).
        output_file (str): Nome del file di output.

    Returns:
        str: Percorso al file audio generato.
    """
    try:
        tts = gTTS(text=text, lang=language, slow=False)
        tts.save(output_file)
        logger.debug(f"Parlato generato e salvato in {output_file}")
        return output_file
    except Exception as e:
        logger.error(f"Errore durante la generazione del parlato: {e}")
        return ""
