# src/audio/audio_handler.py

import simpleaudio as sa
from src.audio.audio_cache import AudioCache
from src.tts import generate_speech
import logging
import os

logger = logging.getLogger("AudioHandler")

class AudioHandler:
    def __init__(self):
        self.cache = AudioCache()

    def speak(self, text: str):
        """Converte il testo in parlato e lo riproduce."""
        try:
            # Controlla la cache
            audio_file = self.cache.get_audio(text)
            if not audio_file:
                audio_file = generate_speech(text)
                self.cache.save_audio(text, audio_file)

            if os.path.exists(audio_file):
                logger.debug(f"Riproduzione audio: {audio_file}")
                
                # Normalizza il percorso per Windows
                normalized_path = os.path.normpath(audio_file)
                logger.debug(f"Piattaforma Normalizzata Path: {normalized_path}")
                
                # Riproduci il file WAV
                wave_obj = sa.WaveObject.from_wave_file(normalized_path)
                play_obj = wave_obj.play()
                play_obj.wait_done()
                logger.debug(f"File audio riprodotto: {normalized_path}")

                # Rimuovi il file dopo la riproduzione
                try:
                    os.remove(audio_file)
                    logger.debug(f"File audio rimosso dopo la riproduzione: {audio_file}")
                except PermissionError as pe:
                    logger.error(f"Errore nella rimozione del file audio: {pe}")
            else:
                logger.error("Errore: file audio non trovato.")
        except Exception as e:
            logger.error(f"Errore nella riproduzione audio: {e}")
