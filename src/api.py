from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from src.voice_assistant import VoiceAssistant
import asyncio
import logging

app = FastAPI()

# Abilita CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permetti richieste da qualsiasi origine (puoi limitarle)
    allow_credentials=True,
    allow_methods=["*"],  # Permetti tutti i metodi HTTP (GET, POST, ecc.)
    allow_headers=["*"],  # Permetti tutti gli header
)

assistant = VoiceAssistant()

# Stato condiviso
state = {"status": "idle", "last_message": ""}

@app.get("/")
async def serve_ui():
    with open("frontend/index.html", "r") as file:
        return HTMLResponse(file.read())

@app.post("/command")
async def process_command(command: str):
    """Processa un comando ricevuto dal frontend."""
    try:
        state["status"] = "processing"
        state["last_message"] = command
        asyncio.create_task(assistant.process_command(command))  # Processa il comando in background
        state["status"] = "speaking"
        return {"status": "success", "message": "Command processed"}
    except Exception as e:
        logging.error(f"Errore durante l'elaborazione del comando: {e}")
        return {"status": "error", "message": str(e)}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Invia aggiornamenti sullo stato dell'assistente al frontend."""
    await websocket.accept()
    try:
        while True:
            await websocket.send_json(state)
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        logging.info("Client disconnected from WebSocket.")
    except Exception as e:
        logging.error(f"Errore nel WebSocket: {e}")
