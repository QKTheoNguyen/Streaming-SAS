import pytest
import httpx
from httpx import ASGITransport

from providers.remote.provider import RemoteProvider
from workers.inference.main import app, provider as worker_provider

# Use a single client for all tests, running the app in-process
@pytest.fixture
async def client():
    # Clear sessions before each test to ensure isolation
    worker_provider.sessions.clear()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

@pytest.mark.anyio
async def test_remote_provider_health(client: httpx.AsyncClient):
    """
    Tests that the remote provider can successfully check the health of the worker.
    """
    provider = RemoteProvider(settings={}, client=client)
    health = await provider.health()
    assert health == {"status": "ok"}

@pytest.mark.anyio
async def test_remote_provider_capabilities(client: httpx.AsyncClient):
    """
    Tests that the remote provider can successfully fetch capabilities from the worker.
    """
    provider = RemoteProvider(settings={}, client=client)
    caps = await provider.capabilities()
    assert caps["task_types"] == ["anonymize", "convert"]
    assert sorted(caps["modes"]) == sorted(["streaming", "non_streaming"])
    assert caps["devices"] == ["remote_gpu"]

@pytest.mark.anyio
async def test_remote_provider_health_unreachable():
    """
    Tests that the provider correctly handles a failure to connect to the worker.
    """
    # This test does NOT use the in-process client.
    provider = RemoteProvider(settings={"worker_url": "http://localhost:8009"})
    health = await provider.health()
    assert health["status"] == "error"
    assert "Failed to connect to worker" in health["detail"]

@pytest.mark.anyio
async def test_session_lifecycle(client: httpx.AsyncClient):
    """
    Tests the full session lifecycle: start, process chunks, and end.
    """
    provider = RemoteProvider(settings={}, client=client)
    config = {"task_type": "anonymize", "mode": "streaming"}

    # 1. Start session
    session_response = await provider.start_session(config)
    assert "session_id" in session_response
    session_id = session_response["session_id"]

    # 2. Process a chunk
    audio_chunk = b"\x00\x01\x02\x03"
    chunk_response = await provider.process_chunk(session_id, audio_chunk)
    assert chunk_response["status"] == "chunk_received"
    assert "sequence_id" in chunk_response

    # 3. End session
    end_response = await provider.end_session(session_id)
    assert end_response == audio_chunk[::-1] # Mock provider reverses the audio


@pytest.mark.anyio
async def test_cancel_session(client: httpx.AsyncClient):
    """
    Tests that a session can be successfully cancelled.
    """
    provider = RemoteProvider(settings={}, client=client)
    config = {"task_type": "anonymize", "mode": "streaming"}

    # Start a session to cancel
    session_response = await provider.start_session(config)
    session_id = session_response["session_id"]

    # Cancel the session
    cancel_response = await provider.cancel(session_id)
    assert cancel_response == {"status": "session_cancelled", "session_id": session_id}

    # Verify the session is gone (should raise 404, which provider translates to an error)
    end_response = await provider.end_session(session_id)
    assert end_response["status"] == "error"


@pytest.mark.anyio
async def test_non_streaming_anonymize(client: httpx.AsyncClient):
    """
    Tests a successful non-streaming 'anonymize' task.
    """
    provider = RemoteProvider(settings={}, client=client)
    config = {"task_type": "anonymize", "mode": "non_streaming"}
    audio_data = b"some-audio-bytes-for-anonymize"

    response = await provider.process(audio_data, config)

    # The provider returns raw bytes, which for the mock anonymizer is the reversed input.
    assert response == audio_data[::-1]


@pytest.mark.anyio
async def test_streaming_convert(client: httpx.AsyncClient):
    """
    Tests a successful streaming 'convert' task.
    """
    provider = RemoteProvider(settings={}, client=client)
    config = {
        "task_type": "convert",
        "mode": "streaming",
        "reference_audio": "dGVzdA==",
    }

    # 1. Start session
    session_response = await provider.start_session(config)
    assert "session_id" in session_response
    session_id = session_response["session_id"]

    # 2. Process a chunk
    audio_chunk = b"\x00\x01\x02\x03"
    chunk_response = await provider.process_chunk(session_id, audio_chunk)
    assert chunk_response["status"] == "chunk_received"
    assert "sequence_id" in chunk_response

    # 3. End session
    end_response = await provider.end_session(session_id)
    import base64
    reference_audio = base64.b64decode(config["reference_audio"])
    expected_len = min(len(audio_chunk), len(reference_audio))
    expected_response = bytes(a ^ b for a, b in zip(audio_chunk[:expected_len], reference_audio[:expected_len]))
    assert end_response == expected_response


@pytest.mark.anyio
async def test_invalid_convert_request_missing_reference_audio(
    client: httpx.AsyncClient,
):
    """
    Tests that a 'convert' request fails if 'reference_audio' is missing.
    """
    provider = RemoteProvider(settings={}, client=client)
    config = {"task_type": "convert", "mode": "non_streaming"}  # Missing reference_audio
    audio_data = b"some-audio-bytes"

    response = await provider.process(audio_data, config)

    assert response["status"] == "error"
    assert "Reference audio is required for voice conversion." in response["detail"]

@pytest.mark.anyio
async def test_non_streaming_convert(client: httpx.AsyncClient):
    """
    Tests a successful non-streaming 'convert' task.
    """
    provider = RemoteProvider(settings={}, client=client)
    config = {
        "task_type": "convert",
        "mode": "non_streaming",
        "reference_audio": "dGVzdA==",
    }
    audio_data = b"some-audio-bytes-for-convert"

    response = await provider.process(audio_data, config)

    # The provider returns raw bytes, which for the mock converter is the XOR of the two inputs.
    import base64
    reference_audio = base64.b64decode(config["reference_audio"])
    expected_len = min(len(audio_data), len(reference_audio))
    expected_response = bytes(a ^ b for a, b in zip(audio_data[:expected_len], reference_audio[:expected_len]))
    assert response == expected_response


@pytest.mark.anyio
async def test_streaming_anonymize(client: httpx.AsyncClient):
    """
    Tests a successful streaming 'anonymize' task.
    """
    provider = RemoteProvider(settings={}, client=client)
    config = {"task_type": "anonymize", "mode": "streaming"}

    # 1. Start session
    session_response = await provider.start_session(config)
    assert "session_id" in session_response
    session_id = session_response["session_id"]

    # 2. Process a chunk
    audio_chunk = b"\x00\x01\x02\x03"
    chunk_response = await provider.process_chunk(session_id, audio_chunk)
    assert chunk_response["status"] == "chunk_received"
    assert "sequence_id" in chunk_response

    # 3. End session
    end_response = await provider.end_session(session_id)
    assert end_response == audio_chunk[::-1] # Mock provider reverses the audio

@pytest.mark.anyio
async def test_process_with_unavailable_worker():
    """
    Tests that a non-streaming request fails when the worker is unavailable.
    """
    provider = RemoteProvider(settings={"worker_url": "http://localhost:8009"})
    config = {"task_type": "anonymize", "mode": "non_streaming"}
    audio_data = b"some-audio-bytes"

    response = await provider.process(audio_data, config)

    assert response["status"] == "error"
    assert "Failed to process audio with worker" in response["detail"]


@pytest.mark.anyio
async def test_start_session_with_unavailable_worker():
    """
    Tests that a streaming request fails when the worker is unavailable.
    """
    provider = RemoteProvider(settings={"worker_url": "http://localhost:8009"})
    config = {"task_type": "anonymize", "mode": "streaming"}

    response = await provider.start_session(config)

    assert response["status"] == "error"
    assert "Failed to start session with worker" in response["detail"]
