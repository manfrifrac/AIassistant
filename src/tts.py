import pyttsx3
import logging
import os
import tempfile
from pydub import AudioSegment
import boto3
from botocore.exceptions import BotoCoreError, ClientError

logger = logging.getLogger("TTS")

# Initialize Polly client once to improve performance
polly_client = boto3.Session(
    aws_access_key_id='AKIAVTDS55OXNR7TEEQV',
    aws_secret_access_key='JlTTqLGyg9FsvR/aBO8G/w8X6/oMvN8TdkDbbU0y',
    region_name='eu-west-3'  # Specify your region here
).client('polly')

def create_ssml(text: str, rate: int = 100, pitch: str = "+0st", volume: str = "medium") -> str:
    """Genera una stringa SSML con controlli di prosodia per una voce più naturale."""
    return f"""
    <speak>
        <prosody rate="{rate}%" pitch="{pitch}" volume="{volume}">
            {text}
        </prosody>
    </speak>
    """
    
def generate_speech(text, language="it", speed=130, voice="Bianca") -> str:
    """
    Genera parlato da testo utilizzando Amazon Polly e converte in WAV.
    :param text: Il testo da convertire in parlato.
    :param language: La lingua da utilizzare (es. "it" per italiano).
    :param speed: La velocità del parlato.
    :param voice: Il nome della voce da utilizzare (opzionale).
    :return: Percorso al file WAV generato.
    """
    try:
        # Configura la voce
        voice_id = voice if voice else 'Bianca'  # Bianca è una voce italiana in Polly
        
        # Utilizza SSML per controllare intonazione, volume ed enfasi
        ssml_text = create_ssml(text, rate=speed, volume="medium")
        
        response = polly_client.synthesize_speech(
            TextType='ssml',
            Text=ssml_text,
            OutputFormat='mp3',
            VoiceId=voice_id
        )
        
        # Salva il parlato in un file temporaneo
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_mp3:
            tmp_mp3.write(response['AudioStream'].read())
            mp3_file = tmp_mp3.name
        
        logger.debug(f"Parlato generato correttamente in {mp3_file}")
        
        # Converti in formato WAV standard
        standardized_wav = os.path.splitext(mp3_file)[0] + "_standard.wav"
        sound = AudioSegment.from_file(mp3_file, format="mp3")
        sound.export(standardized_wav, format="wav")
        
        # Rimuovi il file MP3 originale
        os.remove(mp3_file)
        return standardized_wav
    except (BotoCoreError, ClientError) as error:
        logger.error(f"Errore durante la generazione del parlato con Polly: {error}")
        return ""
    except Exception as e:
        logger.error(f"Errore durante la generazione del parlato: {e}")
        return ""
