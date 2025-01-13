from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import ValidationError  # Add this import
from pathlib import Path
import logging
import json
import uuid
from backend.src.api import router as api_router
from .core_components import CoreComponents
from backend.src.models.serializers import MessageRequest, MessageResponse, AudioRequest

# Move core initialization before app creation for better error handling
core = CoreComponents.get_instance()
app = FastAPI()

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Routes - Move this before the endpoint definitions
app.include_router(api_router, prefix="/api")

# Exception handlers
@app.exception_handler(422)
async def validation_exception_handler(request, exc):
    """Handle validation errors with more detail"""
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Validation Error",
            "errors": exc.errors() if hasattr(exc, 'errors') else str(exc)
        }
    )

# API endpoints with explicit methods
@app.get("/api/status", include_in_schema=True)
async def get_status():
    return {"message": "Service is running"}

@app.post("/api/chat/message", response_model=MessageResponse, include_in_schema=True)
async def process_chat_message(message: MessageRequest):
    try:
        # First validate session_id
        if message.session_id is None:
            raise HTTPException(status_code=422, detail="session_id cannot be null")

        # Then validate message content
        if not message.message.strip():
            raise HTTPException(status_code=400, detail="Empty message not allowed")

        response = await core.assistant.handle_message(message.model_dump())
        session_id = message.session_id or uuid.uuid4()
        return MessageResponse(session_id=session_id, **response)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors())
    except HTTPException as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Validation error: {e.detail}")
        raise e
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Error processing message: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/audio", include_in_schema=True)
async def process_audio(
    audio: UploadFile = File(...),
    request: str = Form(...)
):
    try:
        # Check if content_type exists and is valid
        if not audio.content_type or not audio.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="Invalid audio file format")
            
        audio_bytes = await audio.read()
        request_data = AudioRequest.model_validate_json(request)
        session_id = str(request_data.session_id) if request_data.session_id else ""
        
        response = await core.assistant.handle_audio(
            audio_bytes, 
            str(request_data.user_id),
            session_id,
            request_data.metadata
        )
        return {"status": "success", "response": response}
    except json.JSONDecodeError:
        raise HTTPException(status_code=422, detail="Invalid JSON format in request")
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Error processing audio: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))

# Serve frontend static files
frontend_path = Path(__file__).parent.parent.parent / "frontend" / "appfront" / "build"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path / "static")), name="static")
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")
    logging.getLogger(__name__).info(f"Serving frontend from {frontend_path}")
else:
    logging.getLogger(__name__).warning(f"Frontend directory not found at {frontend_path}")