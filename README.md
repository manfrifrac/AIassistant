# AIassistant

A voice-based assistant built with LangGraph for conversation flow management.

## Setup

1. Clone this repository.
   ```bash
   git clone https://github.com/manfrifrac/AIassistant.git
   cd AIassistant
   ```
2. Create and activate a Python virtual environment.
   ```bash
   # Creare un virtual environment
   python -m venv venv

   # Attivare il virtual environment su Windows
   venv\Scripts\activate

   # Attivare il virtual environment su Unix o MacOS
   source venv/bin/activate
   ```
3. Install dependencies from requirements.txt.
   ```bash
   pip install -r requirements.txt
   ```
4. Run python main.py to start the assistant.
   ```bash
   python main.py
   ```

## Running the Application

You can run the AI Assistant in two modes using the main entry point:

```bash
# Run in backend mode (default)
python main.py

# Run in frontend mode
python main.py --mode frontend
```

## Usage

- Provide a thread ID (optional).
- Speak your query when prompted.
- The assistant processes your message and responds via TTS.

## Contributing

- Fork the repository.
- Submit pull requests for improvements.

## License

[MIT](LICENSE)

## Caratteristiche

- **Trascrizione vocale**: Utilizza l'API Whisper di OpenAI per convertire l'audio in testo.
- **Analisi degli intenti**: Rileva intenti con modelli di linguaggio basati su OpenAI GPT-4.
- **Interazione musicale**: Cerca e riproduce brani tramite l'API Spotify.
- **Risposte vocali**: Genera risposte vocali con Google Text-to-Speech.
- **Esecuzione sicura di codice Python**: Grazie a `RestrictedPython`.

## Struttura del Progetto
- **logs/**: File di log generati.
- **main.py**: Script principale per avviare l'assistente.
- **output.mp3**: File audio generati (temporanei).
- **requirements.txt**: File delle dipendenze.
- **src/**: Codice sorgente.
  - **agents/**: Moduli degli agenti per intenti specifici.
  - **tools/**: Utilità per API e funzioni di supporto.
  - **config.py**: Configurazione del progetto.
  - **stt.py**: Modulo per la trascrizione vocale.
  - **tts.py**: Modulo per la generazione di audio.
  - **voice_assistant.py**: Classe principale per l'assistente vocale.

## Requisiti

- **Python**: 3.10 o superiore
- **Chiavi API**: Configura le seguenti API:
  - OpenAI (Whisper, GPT-4)
  - Spotify
  - Google Text-to-Speech (gTTS)

## Configura le variabili d'ambiente
Crea un file `.env` nella root del progetto e aggiungi le chiavi API:
    ```
    OPENAI_API_KEY=your_openai_api_key
    # SPOTIFY_CLIENT_ID=your_spotify_client_id
    # SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
    # SPOTIFY_REDIRECT_URI=your_spotify_redirect_uri
    # TAVILY_API_KEY=tyou_tavily_api_key
    ```

## Contatti

Se hai domande o suggerimenti, contattami su **manfredo.fraccola@gmail.com**.
