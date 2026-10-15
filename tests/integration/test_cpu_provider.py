import pytest
from starlette.testclient import TestClient
from apps.api.main import app

@pytest.fixture
def client():
    return TestClient(app)

@pytest.mark.asyncio
async def test_list_providers(client):
    response = client.get("/providers")
    assert response.status_code == 200
    providers = response.json()
    assert "cpu" in providers

@pytest.mark.asyncio
async def test_start_session_anonymize(client):
    payload = {
        "task_type": "anonymize",
        "mode": "non_streaming",
        "device": "cpu",
    }
    response = client.post("/sessions/start", json=payload)
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "session_started"
    assert "session_id" in json_data

@pytest.mark.asyncio
async def test_start_session_convert(client):
    payload = {
        "task_type": "convert",
        "mode": "non_streaming",
        "device": "cpu",
        "reference_audio": "some_reference.wav"
    }
    response = client.post("/sessions/start", json=payload)
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "session_started"
    assert "session_id" in json_data

@pytest.mark.asyncio
async def test_process_non_streaming(client):
    # Start a session first
    start_payload = {
        "task_type": "anonymize",
        "mode": "non_streaming",
        "device": "cpu",
    }
    response = client.post("/sessions/start", json=start_payload)
    session_id = response.json()["session_id"]

    # Process audio
    audio_data = b"some audio data"
    response = client.post(f"/sessions/{session_id}/process", content=audio_data)
    assert response.status_code == 200
    assert response.content == audio_data

@pytest.mark.asyncio
async def test_process_streaming(client):
    # Start a session
    start_payload = {
        "task_type": "anonymize",
        "mode": "streaming",
        "device": "cpu",
    }
    response = client.post("/sessions/start", json=start_payload)
    session_id = response.json()["session_id"]

    with client.websocket_connect(f"/sessions/{session_id}") as websocket:
        audio_data = b"test chunk 1"
        websocket.send_json({"audio": audio_data.decode('latin-1'), "sequence_id": 0})
        result = websocket.receive_json()
        assert result["sequence_id"] == 0
        assert result["audio"].encode('latin-1') == audio_data

        audio_data = b"test chunk 2"
        websocket.send_json({"audio": audio_data.decode('latin-1'), "sequence_id": 1})
        result = websocket.receive_json()
        assert result["sequence_id"] == 1
        assert result["audio"].encode('latin-1') == audio_data
