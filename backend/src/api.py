from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from src.voice_assistant import VoiceAssistant
from src.state.state_manager import StateManager
from src.state.state_schema import StateSchema
from src.utils.log_config import setup_logging
import asyncio
import logging
from pathlib import Path

# Configura il logging all'avvio dell'applicazione
setup_logging(global_debug_mode=True)
logger = logging.getLogger(__name__)

app = FastAPI()

# Abilita CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permetti richieste da qualsiasi origine (puoi limitarle)
    allow_credentials=True,
    allow_methods=["*"],  # Permetti tutti i metodi HTTP (GET, POST, ecc.)
    allow_headers=["*"],  # Permetti tutti gli header
)

# Monta i file statici del frontend React
frontend_path = Path("ai-assistant-frontend/build")
if frontend_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")
    logger.info(f"Serving frontend from {frontend_path}")
else:
    logger.warning(f"Frontend directory not found at {frontend_path}")

state_manager = StateManager()
state_manager.set_state_schema(StateSchema)
assistant = VoiceAssistant(state_manager)

# Stato condiviso
state = {"status": "idle", "last_message": ""}

@app.on_event("startup")
async def startup_event():
    logger.info("Application startup complete.")
    logger.debug("Stato iniziale: %s", state_manager.state)

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutdown complete.")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming HTTP requests"""
    logger.debug(f"Incoming request: {request.method} {request.url}")
    response = await call_next(request)
    logger.debug(f"Response status: {response.status_code}")
    return response

@app.get("/")
async def serve_ui():
    """Serve the React frontend index.html"""
    try:
        with open(frontend_path / "index.html", "r") as file:
            return HTMLResponse(file.read())
    except FileNotFoundError:
        logger.error(f"Frontend index.html not found in {frontend_path}")
        return JSONResponse(
            content={"error": "Frontend not built"},
            status_code=500
        )

class CommandRequest(BaseModel):
    command: str

@app.post("/command")
async def process_command(request: CommandRequest):
    """Processa un comando ricevuto dal frontend."""
    try:
        logger.debug(f"Ricevuto comando: {request.command}")
        state["status"] = "processing"
        state["last_message"] = request.command
        asyncio.create_task(assistant.process_command(request.command))  # Processa il comando in background
        state["status"] = "speaking"
        logger.info(f"Comando processato con successo: {request.command}")
        return JSONResponse(content={"status": "success", "message": "Command processed"})
    except Exception as e:
        logger.error(f"Errore durante l'elaborazione del comando: {e}", exc_info=True)
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)

@app.post("/audio")
async def process_audio(audio: UploadFile = File(...)):
    """Process uploaded audio file and return transcription."""
    try:
        # Create a temporary file to store the uploaded audio
        temp_path = f"temp_{audio.filename}"
        with open(temp_path, "wb") as buffer:
            content = await audio.read()
            buffer.write(content)
        
        # Transcribe the audio using the STT module
        from src.stt import transcribe_audio
        text = transcribe_audio(temp_path)
        
        # Remove temporary file
        import os
        os.remove(temp_path)
        
        if text:
            # Process the transcribed command
            asyncio.create_task(assistant.process_command(text))
            return {"status": "success", "text": text}
        else:
            return JSONResponse(
                content={"status": "error", "message": "Could not transcribe audio"},
                status_code=400
            )
            
    except Exception as e:
        logger.error(f"Error processing audio: {e}", exc_info=True)
        return JSONResponse(
            content={"status": "error", "message": str(e)},
            status_code=500
        )

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Invia aggiornamenti sullo stato dell'assistente al frontend."""
    await websocket.accept()
    client_id = id(websocket)  # Unique ID for each connection
    logger.info(f"WebSocket connection established - Client ID: {client_id}")
    
    try:
        while True:
            data = await websocket.receive_text()
            logger.debug(f"Client {client_id} - Received command: {data}")
            
            # Process the command using the same voice assistant instance
            await assistant.process_command(data)
            
            # Get the response from the state manager
            response = state_manager.get_assistant_message()
            logger.debug(f"Client {client_id} - Sending response: {response}")
            
            if response:
                await websocket.send_text(response)
            
    except WebSocketDisconnect:
        logger.info(f"Client {client_id} disconnected from WebSocket")
    except Exception as e:
        logger.error(f"Client {client_id} - Errore nel WebSocket: {e}", exc_info=True)
        try:
            await websocket.close(code=1011)  # Internal server error
        except Exception:
            pass  # Ignora errori durante la chiusura forzata
    finally:
        # Log della chiusura ma non tentare di chiudere nuovamente
        logger.info(f"Client {client_id} - WebSocket connection ended")
