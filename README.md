# Voice Assistant Project

Un assistente vocale basato su Python che utilizza tecnologie di machine learning e API per rispondere a comandi vocali, analizzare intenti, interagire con Spotify e molto altro.

## Caratteristiche

- **Trascrizione vocale**: Utilizza l'API Whisper di OpenAI per convertire l'audio in testo.
- **Analisi degli intenti**: Rileva intenti con modelli di linguaggio basati su OpenAI GPT-4.
- **Interazione musicale**: Cerca e riproduce brani tramite l'API Spotify.
- **Risposte vocali**: Genera risposte vocali con Google Text-to-Speech.
- **Esecuzione sicura di codice Python**: Grazie a `RestrictedPython`.

## Struttura del Progetto
├── logs/ # File di log generati 
├── main.py # Script principale per avviare l'assistente 
├── output.mp3 # File audio generati (temporanei) 
├── output.wav # File audio temporanei 
├── requirements.txt # File delle dipendenze 
├── src/ # Codice sorgente 
│ ├── agents/ # Moduli degli agenti per intenti specifici 
│ ├── tools/ # Utilità per API e funzioni di supporto 
│ ├── config.py # Configurazione del progetto 
│ ├── stt.py # Modulo per la trascrizione vocale 
│ ├── tts.py # Modulo per la generazione di audio 
│ ├── voice_assistant.py # Classe principale per l'assistente vocale


## Requisiti

- **Python**: 3.10 o superiore
- **Chiavi API**: Configura le seguenti API:
  - OpenAI (Whisper, GPT-4)
  - Spotify
  - Google Text-to-Speech (gTTS)

## Installazione

1. **Clona il repository**:
   ```bash
   git clone https://github.com/username/repository-name.git
   cd repository-name


2. **Installa le dipendenze**:
    ```bash
    pip install -r requirements.txt

3. **Configura le variabili d'ambiente: Crea un file .env nella root del progetto e aggiungi le chiavi API:**:
    ```bash
    OPENAI_API_KEY=your_openai_api_key
    SPOTIFY_CLIENT_ID=your_spotify_client_id
    SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
    SPOTIFY_REDIRECT_URI=your_spotify_redirect_uri


## Utilizzo
Avvia l'assistente vocale con:
    ```bash
    python main.py

L'assistente inizierà ad ascoltare i comandi vocali tramite il microfono.

## Contributi

I contributi sono benvenuti! Per contribuire:

1. Fai un fork di questo repository.
2. Crea un branch per le tue modifiche:
   ```bash
   git checkout -b feature-nome-della-tua-feature
   ```
3. Fai un commit delle modifiche:
   ```bash
   git commit -m "Descrizione delle modifiche"
   ```
4. Esegui il push del branch:
   ```bash
   git push origin feature-nome-della-tua-feature
   ```
5. Apri una Pull Request.

## Licenza

Questo progetto è distribuito sotto licenza **MIT**. Vedi il file `LICENSE` per maggiori dettagli.

## Contatti

Se hai domande o suggerimenti, contattami su **manfredo.fraccola@gmail.com**.
