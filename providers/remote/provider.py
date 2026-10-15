"""
Client for interacting with a remote inference worker.
"""

import httpx
import json
import base64
from typing import Any, Dict

class Provider:
    async def health(self) -> Dict[str, Any]:
        raise NotImplementedError

    async def capabilities(self) -> Dict[str, Any]:
        raise NotImplementedError

    async def start_session(self, config: Dict[str, Any]) -> str:
        raise NotImplementedError

    async def process_chunk(self, session_id: str, chunk: bytes) -> Dict[str, Any]:
        raise NotImplementedError

    async def process(self, audio_input: bytes, config: Dict[str, Any]) -> bytes:
        raise NotImplementedError

    async def end_session(self, session_id: str) -> bytes:
        raise NotImplementedError

    async def cancel_session(self, session_id: str) -> None:
        raise NotImplementedError


class RemoteProvider(Provider):
    def __init__(self, settings: Dict[str, Any], client: httpx.AsyncClient | None = None):
        if client:
            self.client = client
        else:
            self.worker_url = settings.get("worker_url", "http://localhost:8001")
            self.client = httpx.AsyncClient(base_url=self.worker_url)

    async def health(self) -> Dict[str, Any]:
        try:
            response = await self.client.get("/health")
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            return {"status": "error", "detail": f"Failed to connect to worker: {e}"}

    async def capabilities(self) -> Dict[str, Any]:
        # The remote provider *always* reports its device as remote_gpu.
        # It can optionally fetch task types and modes from the worker.
        worker_caps = {}
        try:
            response = await self.client.get("/capabilities")
            response.raise_for_status()
            worker_caps = response.json()
        except (httpx.RequestError, httpx.HTTPStatusError):
            # If worker is unreachable, use defaults but still report as remote
            pass

        return {
            "task_types": worker_caps.get("task_types", ["anonymize", "convert"]),
            "modes": worker_caps.get("modes", ["streaming", "non_streaming"]),
            "devices": ["remote_gpu"],  # This is the key change
        }

    async def start_session(self, config: Dict[str, Any]) -> Dict[str, Any]:
        # If reference_audio is present and is bytes, base64 encode it.
        if "reference_audio" in config and isinstance(config["reference_audio"], bytes):
            config["reference_audio"] = base64.b64encode(
                config["reference_audio"]
            ).decode("utf-8")

        try:
            response = await self.client.post("/session", json=config)
            if response.status_code >= 400:
                return {
                    "status": "error",
                    "detail": response.json().get("detail", response.text),
                }
            response.raise_for_status()
            return response.json()  # Return the whole dict
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            return {
                "status": "error",
                "detail": f"Failed to start session with worker: {e}",
            }

    async def process_chunk(self, session_id: str, chunk: bytes) -> Dict[str, Any]:
        try:
            response = await self.client.post(
                f"/session/{session_id}/chunk",
                content=chunk,
                headers={"Content-Type": "application/octet-stream"},
            )
            response.raise_for_status()
            return response.json()
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            raise Exception(f"Failed to process chunk with worker: {e}")

    async def process(self, audio_input: bytes, config: Dict[str, Any]) -> Dict[str, Any]:
        if "reference_audio" in config and isinstance(config["reference_audio"], bytes):
            config["reference_audio"] = base64.b64encode(
                config["reference_audio"]
            ).decode("utf-8")

        files = {"audio_file": ("audio.wav", audio_input, "audio/wav")}
        data = {"config": json.dumps(config)}

        try:
            response = await self.client.post("/process", files=files, data=data)
            if response.status_code >= 400:
                return {
                    "status": "error",
                    "detail": response.json().get("detail", response.text),
                }
            response.raise_for_status()
            return response.content
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            return {
                "status": "error",
                "detail": f"Failed to process audio with worker: {e}",
            }

    async def end_session(self, session_id: str) -> Dict[str, Any]:
        try:
            response = await self.client.post(f"/session/{session_id}/end")
            if response.status_code >= 400:
                return {
                    "status": "error",
                    "detail": response.json().get("detail", response.text),
                }
            response.raise_for_status()
            # The worker returns a JSON response, not raw bytes
            return response.content
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            return {"status": "error", "detail": f"Failed to end session with worker: {e}"}

    async def cancel(self, session_id: str) -> Dict[str, Any]:
        try:
            response = await self.client.post(f"/session/{session_id}/cancel")
            if response.status_code >= 400:
                return {
                    "status": "error",
                    "detail": response.json().get("detail", response.text),
                }
            response.raise_for_status()
            return response.json()
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            return {
                "status": "error",
                "detail": f"Failed to cancel session with worker: {e}",
            }
