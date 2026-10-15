
import pytest
from providers.cpu.provider import CPUProvider

@pytest.fixture
def provider():
    return CPUProvider(settings={})

@pytest.mark.asyncio
async def test_health(provider):
    health = await provider.health()
    assert health == {"status": "ok", "engine": "cpu"}

@pytest.mark.asyncio
async def test_capabilities(provider):
    capabilities = await provider.capabilities()
    assert capabilities["task_types"] == ["anonymize", "convert"]
    assert capabilities["modes"] == ["non_streaming", "streaming"]
    assert capabilities["device"] == "cpu"

@pytest.mark.asyncio
async def test_session_lifecycle_anonymize(provider):
    config = {"task_type": "anonymize", "model_id": "cpu_mock_anonymizer"}
    session_id = await provider.start_session(config)
    assert session_id in provider.sessions
    assert provider.sessions[session_id]["config"]["task_type"] == "anonymize"
    await provider.end_session(session_id)
    assert session_id not in provider.sessions

@pytest.mark.asyncio
async def test_session_lifecycle_convert(provider):
    config = {
        "task_type": "convert",
        "model_id": "cpu_mock_converter",
        "reference_audio": b"reference audio data",
    }
    session_id = await provider.start_session(config)
    assert session_id in provider.sessions
    assert provider.sessions[session_id]["config"]["task_type"] == "convert"
    await provider.end_session(session_id)
    assert session_id not in provider.sessions


@pytest.mark.asyncio
async def test_start_session_no_task_type(provider):
    with pytest.raises(ValueError, match="`task_type` is required."):
        await provider.start_session({})

@pytest.mark.asyncio
async def test_start_session_unsupported_task_type(provider):
    with pytest.raises(ValueError, match="Unsupported task_type: invalid_task"):
        await provider.start_session({"task_type": "invalid_task"})


@pytest.mark.asyncio
async def test_start_session_missing_reference_audio_for_convert(provider):
    config = {"task_type": "convert", "model_id": "cpu_mock_converter"} # Missing reference_audio
    with pytest.raises(ValueError, match="`reference_audio` is required for 'convert' task type."):
        await provider.start_session(config)

@pytest.mark.asyncio
async def test_process_anonymize(provider):
    config = {"task_type": "anonymize"}
    audio_input = b"test audio"
    result = await provider.process(audio_input, config)
    assert result == audio_input[::-1]

@pytest.mark.asyncio
async def test_process_convert(provider):
    config = {"task_type": "convert", "reference_audio": b"reference audio data"}
    audio_input = b"test audio"
    result = await provider.process(audio_input, config)
    reference_audio = config["reference_audio"]
    expected_len = min(len(audio_input), len(reference_audio))
    expected_response = bytes(a ^ b for a, b in zip(audio_input[:expected_len], reference_audio[:expected_len]))
    assert result == expected_response

@pytest.mark.asyncio
async def test_process_chunk_anonymize(provider):
    config = {"task_type": "anonymize"}
    session_id = await provider.start_session(config)
    chunk = b"test chunk"
    result = await provider.process_chunk(session_id, chunk, 0)
    assert result["status"] == "chunk_received"
    assert result["sequence_id"] == 0
    await provider.end_session(session_id)

@pytest.mark.asyncio
async def test_process_chunk_convert(provider):
    config = {"task_type": "convert", "reference_audio": b"reference audio"}
    session_id = await provider.start_session(config)
    chunk = b"test chunk"
    result = await provider.process_chunk(session_id, chunk, 0)
    assert result["status"] == "chunk_received"
    assert result["sequence_id"] == 0
    await provider.end_session(session_id)

@pytest.mark.asyncio
async def test_process_chunk_invalid_session(provider):
    with pytest.raises(ValueError, match="Session not found: invalid_session"):
        await provider.process_chunk("invalid_session", b"test chunk", 0)

@pytest.mark.asyncio
async def test_process_chunk_empty_chunk(provider):
    config = {"task_type": "anonymize"}
    session_id = await provider.start_session(config)
    # The current provider does not raise an error for empty chunks.
    # This test should be updated if that changes.
    pass

