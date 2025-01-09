import pyttsx3
import logging
import os
import tempfile
from pydub import AudioSegment

logger = logging.getLogger("TTS")

def generate_speech(text, language="it", speed=200, voice=None) -> str:
    """
    Genera parlato da testo utilizzando pyttsx3 e converte in WAV.
    :param text: Il testo da convertire in parlato.
    :param language: La lingua da utilizzare (es. "it" per italiano).
    :param speed: La velocità del parlato (default: 150 WPM).
    :param voice: Il nome o ID della voce (opzionale).
    :return: Percorso al file WAV generato.
    """
    try:
        # Inizializza il motore di sintesi vocale
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        
        # Configura la voce
        if voice:
            engine.setProperty('voice', voice)
        else:
            # Trova una voce italiana se possibile
            italian_voice = next((v.id for v in voices if 'italian' in v.name.lower()), None)
            if italian_voice:
                engine.setProperty('voice', italian_voice)
            else:
                logger.warning("Voce italiana non trovata, usando la voce di default.")
        
        # Configura la velocità del parlato
        engine.setProperty('rate', speed)
        
        # Genera il parlato in un file temporaneo
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_wav:
            wav_file = tmp_wav.name
        
        engine.save_to_file(text, wav_file)
        engine.runAndWait()
        
        if os.path.exists(wav_file):
            logger.debug(f"Parlato generato correttamente in {wav_file}")
        else:
            logger.error(f"Errore: il file {wav_file} non è stato creato.")
            return ""
        
        # Converti in formato WAV standard (se necessario)
        standardized_wav = os.path.splitext(wav_file)[0] + "_standard.wav"
        sound = AudioSegment.from_file(wav_file)
        sound.export(standardized_wav, format="wav")
        logger.debug(f"Parlato convertito in WAV standard in {standardized_wav}")
        
        # Rimuovi il file WAV originale
        os.remove(wav_file)
        return standardized_wav
    except Exception as e:
        logger.error(f"Errore durante la generazione del parlato: {e}")
        return ""
