"""
Inference worker for GPU-accelerated tasks.
"""
from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Form, Response
from pydantic import BaseModel
import uuid
import json
import base64
from providers.cpu.provider import CPUProvider
from typing import Dict, Any

app = FastAPI()

# In a real worker, you'd have a pool of models/workers.
# For this example, we'll instantiate a single CPU provider to handle requests.
# This demonstrates the provider contract being used by the worker.
provider = CPUProvider(settings={})


class SessionConfig(BaseModel):
    task_type: str
    mode: str
    reference_audio: str | None = None
    voice_profile_id: str | None = None
    # Add other config fields as needed


@app.get("/health")
async def health():
    # In a real implementation, this would check model/hardware status
    return {"status": "ok"}


@app.get("/capabilities")
async def capabilities():
    # This should be dynamic based on loaded models.
    return await provider.capabilities()


@app.post("/session")
async def start_session(config: SessionConfig):
    config_dict = config.dict(exclude_none=True)

    # Validate config based on task type
    if config.task_type == "convert":
        if not config.reference_audio and not config.voice_profile_id:
            raise HTTPException(
                status_code=400,
                detail="Either reference_audio or voice_profile_id is required for convert tasks.",
            )
        if config.reference_audio and config.voice_profile_id:
            raise HTTPException(
                status_code=400,
                detail="Supply either reference_audio or voice_profile_id, not both.",
            )
    elif config.task_type == "anonymize":
        if config.reference_audio or config.voice_profile_id:
            raise HTTPException(
                status_code=400,
                detail="reference_audio and voice_profile_id are not used for anonymize tasks.",
            )

    if config_dict.get("reference_audio"):
        config_dict["reference_audio"] = base64.b64decode(config_dict["reference_audio"])

    try:
        session_id = await provider.start_session(config_dict)
        return {"session_id": session_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/session/{session_id}/chunk")
async def process_chunk(session_id: str, request: Request):
    audio_chunk = await request.body()

    # In a real implementation, sequence ID would come from the client.
    # For this test setup, we can simulate it based on number of chunks.
    # This is fragile and only for demonstration.
    session = provider.sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    sequence_id = len(session.get("chunks", []))

    try:
        # The CPU provider's process_chunk method returns bytes.
        # We discard them here and return a status dict, as per the worker contract.
        result = await provider.process_chunk(session_id, audio_chunk, sequence_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/process")
async def process_non_streaming(audio_file: UploadFile = File(...), config: str = Form(...)):
    audio_bytes = await audio_file.read()
    config_dict = json.loads(config)

    if config_dict.get("reference_audio"):
        config_dict["reference_audio"] = base64.b64decode(
            config_dict["reference_audio"]
        )

    try:
        # The CPU provider's process method validates and returns bytes, but for the
        # worker contract, we just need to know it succeeded.
        processed_audio = await provider.process(audio_bytes, config_dict)
        return Response(content=processed_audio, media_type="application/octet-stream")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/session/{session_id}/end")
async def end_session(session_id: str):
    try:
        # The CPU provider's end_session method returns bytes.
        # We discard them here and return a status dict, as per the worker contract.
        processed_audio = await provider.end_session(session_id)
        return Response(content=processed_audio, media_type="application/octet-stream")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/session/{session_id}/cancel")
async def cancel_session(session_id: str):
    try:
        await provider.cancel_session(session_id)
        return {"status": "session_cancelled", "session_id": session_id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

