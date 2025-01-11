import requests
import os
import logging

logger = logging.getLogger("STT")

API_KEY = os.getenv("OPENAI_API_KEY")

def transcribe_audio(file_path, language="it"):
    """
    Trascrive l'audio in testo utilizzando l'API Whisper di OpenAI.
    
    Args:
        file_path (str): Percorso al file audio.
        language (str): Lingua dell'audio (ISO-639-1, es. "it").
    
    Returns:
        str: Testo trascritto.
    """
    url = "https://api.openai.com/v1/audio/transcriptions"
    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }
    with open(file_path, "rb") as f:
        files = {
            "file": (os.path.basename(file_path), f, "audio/wav"),
        }
        data = {
            "model": "whisper-1",
            "language": language
        }
        try:
            response = requests.post(url, headers=headers, files=files, data=data)
            response.raise_for_status()
            transcription = response.json().get("text", "")
            logger.debug(f"Trascrizione riuscita: {transcription}")
            return transcription
        except requests.RequestException as e:
            logger.error(f"Errore durante la trascrizione audio: {e}")
            return ""
