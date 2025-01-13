import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock  # Added import for AsyncMock
from uuid import UUID, uuid4
from backend.src.app import app
from backend.src.models.serializers import MessageRequest, AudioRequest, MessageResponse  # Added MessageResponse
from backend.src.agents.supervisor_agent import SupervisorAgent
from backend.src.dependencies import get_supervisor

client = TestClient(app)

@pytest.fixture
def mock_supervisor():
    """Fixture to mock SupervisorAgent using dependency_overrides."""
    mock = AsyncMock(spec=SupervisorAgent)
    app.dependency_overrides[get_supervisor] = lambda: mock
    yield mock
    app.dependency_overrides.pop(get_supervisor, None)

@pytest.fixture
def valid_message_request():
    return MessageRequest(
        message="Test message",
        user_id=uuid4(),
        session_id=uuid4(),
        metadata={"test": "data"}
    )

@pytest.fixture
def valid_audio_request():
    return AudioRequest(
        user_id=uuid4(),
        session_id=uuid4(),
        metadata={"test": "data"}
    )

def test_chat_status():
    response = client.get("/api/v1/chat")
    assert response.status_code == 200
    assert response.json() == {"status": "success", "message": "Chat service is connected!"}

def test_process_chat_message_success(mock_supervisor):
    session_uuid = UUID("123e4567-e89b-12d3-a456-426614174000")
    request_data = {
        "user_id": "123e4567-e89b-12d3-a456-426614174000",
        "message": "Hello!",
        "session_id": str(session_uuid),
        "metadata": {}
    }
    
    # Crea la risposta con i campi corretti
    response_data = MessageResponse(
        message="Hi there!",
        session_id=session_uuid,
        metadata={},
        status="success"
    )
    mock_supervisor.process_request.return_value = response_data
    
    response = client.post("/api/v1/chat", json=request_data)
    assert response.status_code == 200
    assert response.json() == {
        "message": "Hi there!",
        "session_id": str(session_uuid),
        "metadata": {},
        "status": "success",
        "audio_response": None
    }
    
    mock_supervisor.process_request.assert_awaited_once_with(
        user_id=UUID(request_data["user_id"]),
        message=request_data["message"],
        session_id=session_uuid,
        metadata=request_data["metadata"]
    )

def test_process_chat_message_failure(mock_supervisor):
    request_data = {
        "user_id": "123e4567-e89b-12d3-a456-426614174000",
        "message": "Hello!",
        "session_id": "123e4567-e89b-12d3-a456-426614174000",
        "metadata": {}
    }
    mock_supervisor.process_request.side_effect = Exception("Test Exception")
    
    response = client.post("/api/v1/chat", json=request_data)
    assert response.status_code == 500
    assert response.json() == {"detail": "Test Exception"}
    mock_supervisor.process_request.assert_awaited_once_with(
        user_id=UUID(request_data["user_id"]),  # Changed to UUID object
        message=request_data["message"],
        session_id=UUID(request_data["session_id"]),  # Changed to UUID object
        metadata=request_data["metadata"]
    )

def test_chat_endpoint(valid_message_request):
    response = client.post(
        "/api/v1/chat",
        json=valid_message_request.dict()
    )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "status" in data

def test_audio_endpoint(valid_audio_request):
    # Crea un file audio di test
    audio_content = b"test audio data"
    files = {"audio": ("test.wav", audio_content, "audio/wav")}
    data = {
        "user_id": str(valid_audio_request.user_id),
        "session_id": str(valid_audio_request.session_id),
        "metadata": str(valid_audio_request.metadata)
    }
    
    response = client.post("/api/v1/audio", files=files, data=data)
    assert response.status_code in [200, 400]  # 400 è accettabile se l'audio non è valido

def test_invalid_message_request():
    invalid_request = {
        "message": "",  # Messaggio vuoto
        "user_id": str(uuid4()),
        "session_id": str(uuid4()),
    }
    response = client.post("/api/v1/chat", json=invalid_request)
    assert response.status_code in [400, 422]

def test_invalid_audio_request():
    invalid_request = {
        "user_id": "invalid-uuid",
        "session_id": str(uuid4()),
    }
    files = {"audio": ("test.wav", b"invalid audio", "audio/wav")}
    response = client.post("/api/v1/audio", files=files, data=invalid_request)
    assert response.status_code == 400

def test_websocket():
    with client.websocket_connect("/api/v1/ws") as websocket:
        websocket.send_text("Test message")
        data = websocket.receive_text()
        assert data is not None