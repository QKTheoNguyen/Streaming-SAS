import inspect
from typing import Dict, Any
from fastapi import FastAPI, WebSocket, HTTPException, Body, Response
from packages.sas_core.registry import ProviderRegistry
from packages.voice_profiles.router import router as voice_profiles_router

from fastapi.staticfiles import StaticFiles

app = FastAPI()

app.include_router(voice_profiles_router)

@app.get("/health")
async def health_check():
    """ Health check endpoint for monitoring."""
    return {"status": "healthy"}

@app.get("/")
async def root_redirect():
    """ Root redirects client to UI."""
    return {"message": "Navigate to /static/minimal_ui.html for UI."}

# Serve static files
app.mount("/static", StaticFiles(directory="apps/web"), name="static")

# Instantiate the provider registry
provider_registry = ProviderRegistry()

@app.get("/providers")
async def list_providers():
    """
    Endpoint to list all available providers and their capabilities.
    """
    return await provider_registry.list_providers()

@app.post("/sessions/start")
async def start_session(config: Dict[str, Any] = Body(...)):
    """
    Start a session by selecting a provider that matches the requested capabilities.
    :param config: Session configuration including `task_type`, `mode`, and `device`.
    """
    try:
        task_type = config["task_type"]
        mode = config["mode"]
        device = config["device"]
    except KeyError:
        raise HTTPException(
            status_code=400,
            detail="Request body must include 'task_type', 'mode', and 'device'."
        )

    try:
        provider = await provider_registry.get_provider(
            task_type=task_type, mode=mode, device=device
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    session_id = await provider.start_session(config)
    return {"status": "session_started", "session_id": session_id}

@app.post("/sessions/{session_id}/process")
async def process_non_streaming(session_id: str, audio_input: bytes = Body(...)):
    """
    Process non-streaming audio for a given session.
    """
    for provider in provider_registry.providers.values():
        if session_id in getattr(provider, '_sessions', {}):
            result = await provider.process(session_id, audio_input)
            return Response(content=result["audio"], media_type="application/octet-stream")

    raise HTTPException(status_code=404, detail="Session not found in any provider")

@app.post("/sessions/{session_id}/end")
async def end_session(session_id: str):
    """
    End a session.
    """
    for provider in provider_registry.providers.values():
        if session_id in getattr(provider, '_sessions', {}):
            await provider.end_session(session_id)
            return {"status": "session_ended", "session_id": session_id}
    raise HTTPException(status_code=404, detail="Session not found in any provider")

@app.post("/sessions/{session_id}/cancel")
async def cancel_session(session_id: str):
    """
    Cancel a session.
    """
    for provider in provider_registry.providers.values():
        if session_id in getattr(provider, '_sessions', {}):
            if hasattr(provider, 'cancel_session'):
                await provider.cancel_session(session_id)
                return {"status": "session_cancelled", "session_id": session_id}
            else: # Fallback to end_session if cancel is not implemented
                await provider.end_session(session_id)
                return {"status": "session_ended_as_cancel", "session_id": session_id}
    raise HTTPException(status_code=404, detail="Session not found in any provider")

@app.websocket("/sessions/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint to handle streaming audio for a session.

    :param websocket: WebSocket connection
    :param session_id: The session ID for ongoing streaming
    """
    provider = None
    for p in provider_registry.providers.values():
        if session_id in getattr(p, '_sessions', {}):
            provider = p
            break

    if not provider:
        await websocket.close(code=4001, reason="Provider for session not found")
        return

    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            audio_chunk = data["audio"].encode('latin-1')
            sequence_id = data["sequence_id"]
            if hasattr(provider, 'process_chunk') and callable(provider.process_chunk):
                if inspect.iscoroutinefunction(provider.process_chunk):
                    result = await provider.process_chunk(session_id, audio_chunk, sequence_id)
                else:
                    result = provider.process_chunk(session_id, audio_chunk, sequence_id)
                result["audio"] = result["audio"].decode('latin-1')
                await websocket.send_json(result)
            else:
                await websocket.send_json({"status": "error", "message": "Streaming not supported by this provider."})
    except Exception as e:
        await websocket.close(code=4002, reason=str(e))