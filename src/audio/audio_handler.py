import pygame
from src.audio.audio_cache import AudioCache
from src.tts import generate_speech
import logging
import os

logger = logging.getLogger("AudioHandler")

class AudioHandler:
    def __init__(self):
        pygame.mixer.init()
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
                pygame.mixer.music.load(audio_file)
                pygame.mixer.music.play()

                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)
            else:
                logger.error("Errore: file audio non trovato.")
        except Exception as e:
            logger.error(f"Errore nella riproduzione audio: {e}")
