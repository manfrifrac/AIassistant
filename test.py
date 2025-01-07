from gtts import gTTS
import pygame
import os

def test_gtts_pygame():
    text = "Ciao, questo è un test con Google Text-to-Speech."
    output_file = "test_output.mp3"
    try:
        # Genera il file audio
        tts = gTTS(text=text, lang="it", slow=False)
        tts.save(output_file)
        
        # Riproduci con pygame
        pygame.mixer.init()
        pygame.mixer.music.load(output_file)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        
        # Rimuovi il file dopo la riproduzione
        os.remove(output_file)
    except Exception as e:
        print(f"Errore: {e}")

test_gtts_pygame()
