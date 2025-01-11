from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, File, UploadFile, HTTPException
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
import os

# Base setup - fai questo solo se non è già stato fatto
if not logging.getLogger().handlers:
    setup_logging(global_debug_mode=True)
logger = logging.getLogger(__name__)

# Singleton pattern per i componenti core
class CoreComponents:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
            cls._instance.init_components()
        return cls._instance
    
    def init_components(self):
        self.state_manager = StateManager()
        self.state_manager.set_state_schema(StateSchema)
        self.assistant = VoiceAssistant(self.state_manager)
        self.assistant.is_web_mode = True
        logger.info("Core components initialized")

# Inizializza l'app FastAPI e i componenti core
app = FastAPI()
core = CoreComponents.get_instance()

# Utilizza i componenti dal singleton
state_manager = core.state_manager
assistant = core.assistant

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class Command(BaseModel):
    command: str

# API Endpoints
@app.get("/api/chat")  # Changed from /api/test
async def chat_status():
    return {"message": "Chat service is connected!", "status": "success"}

@app.post("/api/chat")  # Changed from /api/test
async def process_chat_message(command: Command):  # Renamed from process_test_command
    try:
        logger.debug(f"Chat message received: {command.command}")
        await assistant.process_command(command.command)
        response_text = state_manager.get_assistant_message()
        
        if response_text:
            # Genera l'audio di risposta
            from src.tts import generate_speech
            audio_path = generate_speech(response_text)
            
            if audio_path:
                try:
                    with open(audio_path, "rb") as audio_file:
                        audio_content = audio_file.read()
                    import base64
                    audio_base64 = base64.b64encode(audio_content).decode()
                    os.remove(audio_path)
                    
                    return {
                        "status": "success",
                        "message": response_text,
                        "audio_response": audio_base64
                    }
                except Exception as e:
                    logger.error(f"Errore nella lettura/codifica dell'audio: {e}")
                    os.remove(audio_path)
        
        return {
            "message": response_text,
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Error processing test command: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/audio")
async def process_audio(audio: UploadFile = File(...)):
    try:
        temp_path = f"temp_{audio.filename}"
        with open(temp_path, "wb") as buffer:
            content = await audio.read()
            buffer.write(content)
        
        from src.stt import transcribe_audio
        text = transcribe_audio(temp_path)
        import os
        os.remove(temp_path)
        
        if text:
            # Processa il comando e ottieni la risposta
            await assistant.process_command(text)
            response_text = state_manager.get_assistant_message()
            
            # Log per debug
            logger.debug(f"Testo trascritto: {text}")
            logger.debug(f"Risposta dell'assistente: {response_text}")
            
            if response_text:
                # Genera l'audio di risposta
                from src.tts import generate_speech
                audio_path = generate_speech(response_text)
                
                if audio_path:
                    try:
                        with open(audio_path, "rb") as audio_file:
                            audio_content = audio_file.read()
                        import base64
                        audio_base64 = base64.b64encode(audio_content).decode()
                        os.remove(audio_path)
                        
                        # Ritorna sia il testo che l'audio
                        return {
                            "status": "success",
                            "text": text,
                            "assistant_response": response_text,  # Aggiunto il testo della risposta
                            "audio_response": audio_base64
                        }
                    except Exception as e:
                        logger.error(f"Errore nella lettura/codifica dell'audio: {e}")
                        os.remove(audio_path)  # Pulizia file in caso di errore
                else:
                    logger.error("Generazione audio fallita")
            
            # Fallback: ritorna solo il testo se non è stato possibile generare l'audio
            return {
                "status": "success",
                "text": text,
                "assistant_response": response_text
            }
            
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
    await websocket.accept()
    client_id = id(websocket)
    logger.info(f"WebSocket connection established - Client ID: {client_id}")
    
    try:
        while True:
            data = await websocket.receive_text()
            await assistant.process_command(data)
            response = state_manager.get_assistant_message()
            if response:
                await websocket.send_text(response)
    except WebSocketDisconnect:
        logger.info(f"Client {client_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        await websocket.close(code=1011)
    
# Static files serving - must be last
frontend_path = Path(__file__).parent.parent.parent / "frontend/appfront/build"
if frontend_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")
    logger.info(f"Serving frontend from {frontend_path}")
else:
    logger.warning(f"Frontend directory not found at {frontend_path}")
