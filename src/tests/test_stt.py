from dotenv import load_dotenv
load_dotenv()

from src.stt import transcribe_audio

def test_transcribe_audio():
    result = transcribe_audio("test.m4a", language="it")
    assert isinstance(result, str) and len(result) > 0
