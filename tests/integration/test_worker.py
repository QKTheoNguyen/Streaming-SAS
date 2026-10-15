"""
Integration tests for the inference worker.
"""
import pytest
from fastapi.testclient import TestClient
import base64
import json

from workers.inference.main import app

client = TestClient(app)

@pytest.fixture
def sample_wav_bytes():
    """A sample WAV file as bytes."""
    # A simple byte string that is not a valid wav, but good enough for these tests
    return b"1234567890abcdefghij"

@pytest.fixture
def reference_wav_bytes():
    """A reference WAV file for voice conversion, must be same length as sample."""
    return b"jihgfedcba0987654321"


def test_worker_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_process_non_streaming_anonymize(sample_wav_bytes):
    config = {
        "task_type": "anonymize",
        "mode": "non_streaming"
    }
    # For non-streaming, we send multipart/form-data
    files = {'audio_file': ('test.wav', sample_wav_bytes, 'audio/wav')}
    data = {'config': json.dumps(config)}
    response = client.post("/process", files=files, data=data)

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/octet-stream"
    processed_audio = response.content
    assert processed_audio == sample_wav_bytes[::-1]


def test_process_non_streaming_convert(sample_wav_bytes, reference_wav_bytes):
    config = {
        "task_type": "convert",
        "mode": "non_streaming",
        # For non-streaming, reference audio is passed in the config as b64 string
        "reference_audio": base64.b64encode(reference_wav_bytes).decode('utf-8')
    }
    files = {'audio_file': ('test.wav', sample_wav_bytes, 'audio/wav')}
    data = {'config': json.dumps(config)}
    response = client.post("/process", files=files, data=data)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/octet-stream"
    processed_audio = response.content

    expected_output = bytes(a ^ b for a, b in zip(sample_wav_bytes, reference_wav_bytes))
    assert processed_audio == expected_output


def test_streaming_anonymize_session(sample_wav_bytes):
    # 1. Start session
    config = {"task_type": "anonymize", "mode": "streaming"}
    response = client.post("/session", json=config)
    assert response.status_code == 200
    session_id = response.json()["session_id"]

    # 2. Process chunks
    chunk1 = sample_wav_bytes[:10]
    chunk2 = sample_wav_bytes[10:]

    response = client.post(f"/session/{session_id}/chunk", content=chunk1)
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["status"] == "chunk_received"
    assert response_data["sequence_id"] == 0

    response = client.post(f"/session/{session_id}/chunk", content=chunk2)
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["status"] == "chunk_received"
    assert response_data["sequence_id"] == 1

    # 3. End session
    response = client.post(f"/session/{session_id}/end")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/octet-stream"
    processed_audio = response.content
    assert processed_audio == sample_wav_bytes[::-1]


def test_streaming_convert_session(sample_wav_bytes, reference_wav_bytes):
    # 1. Start session
    config = {
        "task_type": "convert",
        "mode": "streaming",
        "reference_audio": base64.b64encode(reference_wav_bytes).decode('utf-8')
    }
    response = client.post("/session", json=config)
    assert response.status_code == 200
    session_id = response.json()["session_id"]

    # 2. Process chunks
    chunk1 = sample_wav_bytes[:10]
    chunk2 = sample_wav_bytes[10:]
    
    response = client.post(f"/session/{session_id}/chunk", content=chunk1)
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["status"] == "chunk_received"
    assert response_data["sequence_id"] == 0

    response = client.post(f"/session/{session_id}/chunk", content=chunk2)
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["status"] == "chunk_received"
    assert response_data["sequence_id"] == 1

    # 3. End session and get result
    response = client.post(f"/session/{session_id}/end")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/octet-stream"
    processed_audio = response.content

    expected_output = bytes(a ^ b for a, b in zip(sample_wav_bytes, reference_wav_bytes))
    assert processed_audio == expected_output


def test_streaming_cancel_session():
    # 1. Start session
    config = {"task_type": "anonymize", "mode": "streaming"}
    response = client.post("/session", json=config)
    assert response.status_code == 200
    session_id = response.json()["session_id"]

    # 2. Cancel session
    response = client.post(f"/session/{session_id}/cancel")
    assert response.status_code == 200
    assert response.json() == {"status": "session_cancelled", "session_id": session_id}

    # 3. Verify session is gone
    response = client.post(f"/session/{session_id}/end")
    assert response.status_code == 404


def test_streaming_chunk_invalid_session():
    response = client.post("/session/invalid-session-id/chunk", content=b"123")
    assert response.status_code == 404
    assert "detail" in response.json()


def test_streaming_end_invalid_session():
    response = client.post("/session/invalid-session-id/end")
    assert response.status_code == 404
    assert "detail" in response.json()


def test_streaming_cancel_invalid_session():
    response = client.post("/session/invalid-session-id/cancel")
    assert response.status_code == 404
    assert "detail" in response.json()


def test_process_non_streaming_convert_missing_reference_audio(sample_wav_bytes):
    config = {
        "task_type": "convert",
        "mode": "non_streaming",
    }
    files = {'audio_file': ('test.wav', sample_wav_bytes, 'audio/wav')}
    data = {'config': json.dumps(config)}
    response = client.post("/process", files=files, data=data)
    assert response.status_code == 400
    assert "detail" in response.json()


def test_streaming_convert_session_missing_reference_audio():
    config = {
        "task_type": "convert",
        "mode": "streaming",
    }
    response = client.post("/session", json=config)
    assert response.status_code == 400
    assert "detail" in response.json()
