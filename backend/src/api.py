from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends, File, UploadFile, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from uuid import UUID
import uuid
from backend.src.voice_assistant import VoiceAssistant
from backend.src.state.state_manager import StateManager
from backend.src.state.state_schema import StateSchema
from backend.src.utils.log_config import setup_logging
from backend.src.tts import generate_speech
from backend.src.stt import transcribe_audio
from backend.src.core_components import CoreComponents  # Import CoreComponents
from backend.src.models.serializers import MessageRequest, MessageResponse, AudioRequest  # Update import
from backend.src.agents import SupervisorAgent  # Updated import
from backend.src.dependencies import get_supervisor  # Correct import path
import logging
from pathlib import Path
import os
import base64

# Base setup - fai questo solo se non è già stato fatto
if not logging.getLogger().handlers:
    setup_logging(global_debug_mode=True)
logger = logging.getLogger(__name__)

# Remove the separate FastAPI app
# app = FastAPI()

router = APIRouter()

# Initialize core components after app creation
core = CoreComponents.get_instance()
state_manager = core.state_manager
assistant = core.assistant
assistant.is_web_mode = True  # Imposta il web mode
    
# Models - Solo modelli specifici per questo modulo
class Command(BaseModel):
    command: str

class ChatMessage(BaseModel):
    command: str

# API Endpoints - Verifica che corrispondano al frontend
@router.get("/chat", tags=["chat"])
async def chat_status():
    """Check if chat service is available"""
    return {"status": "success", "message": "Chat service is connected!"}

@router.post("/chat", tags=["chat"], response_model=MessageResponse)
async def process_message(
    request: MessageRequest,  # Ora usa il MessageRequest importato
    supervisor: SupervisorAgent = Depends(get_supervisor)  # Updated type
):
    try:
        # Converti le stringhe in UUID se necessario
        response = await supervisor.process_request(
            user_id=request.user_id,
            message=request.message,
            session_id=request.session_id,
            metadata=request.metadata or {}
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/chat", tags=["chat"])  # Changed from /api/test
async def process_chat_message(message: ChatMessage):  # Renamed from process_test_command
    """Process chat messages"""
    try:
        logger.debug(f"Chat message received: {message.command}")  # Cambiato da message.message a message.command
        await assistant.process_command(message.command)  # Cambiato da message.message a message.command
        response_text = state_manager.get_assistant_message()
        
        if response_text:
            # Genera l'audio di risposta
            audio_path = generate_speech(response_text)
            
            if audio_path:
                try:
                    with open(audio_path, "rb") as audio_file:
                        audio_content = audio_file.read()
                    audio_base64 = base64.b64encode(audio_content).decode()
                    os.remove(audio_path)
                    
                    return {
                        "status": "success",
                        "message": response_text,
                        "audio_response": audio_base64  # Cambiato da 'audio' a 'audio_response'
                    }
                except Exception as e:
                    logger.error(f"Audio processing error: {e}")
                    if os.path.exists(audio_path):
                        os.remove(audio_path)
        
        return {
            "status": "success",
            "message": response_text or "No response generated"
        }
    except Exception as e:
        logger.error(f"Error processing chat message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/audio", tags=["audio"])
async def process_audio(
    audio: UploadFile = File(...),
    user_id: str = Form(...),
    session_id: Optional[str] = Form(None),
    metadata: Optional[str] = Form(None)
):
    try:
        # Converti le stringhe in UUID
        user_id_uuid = uuid.UUID(user_id)
        session_id_uuid = uuid.UUID(session_id) if session_id else None
        metadata_dict = {} if metadata is None else eval(metadata)  # Usa json.loads per maggiore sicurezza

        temp_path = f"temp_{audio.filename}"
        with open(temp_path, "wb") as buffer:
            content = await audio.read()
            buffer.write(content)
        
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
                audio_path = generate_speech(response_text)
                
                if (audio_path):
                    try:
                        with open(audio_path, "rb") as audio_file:
                            audio_content = audio_file.read()
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
    except ValueError as e:
        return JSONResponse(
            content={"status": "error", "message": "Invalid UUID format"},
            status_code=400
        )
    except Exception as e:
        logger.error(f"Error processing audio: {e}", exc_info=True)
        return JSONResponse(
            content={"status": "error", "message": str(e)},
            status_code=500
        )

@router.websocket("/ws")
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
# frontend_path = Path(__file__).parent.parent.parent / "frontend/appfront/build"
# if frontend_path.exists():
#     # Mount static files before the catch-all route
#     app.mount("/static", StaticFiles(directory=str(frontend_path / "static")), name="static")
#     app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")
#     logger.info(f"Serving frontend from {frontend_path}")
# else:
#     logger.warning(f"Frontend directory not found at {frontend_path}")
