from dotenv import load_dotenv
load_dotenv()

from src.tts import generate_speech

def test_generate_speech():
    output = generate_speech("Ciao, questo è un test.", voice="alloy")
    assert output == "output.mp3"
