"""
CPU-based provider for speech anonymization and voice conversion.
"""

import asyncio
import logging
import time
from typing import Any, Dict
import uuid

logger = logging.getLogger(__name__)

# A simple, deterministic transformation for testing purposes
def reverse_bytes(audio: bytes) -> bytes:
    return audio[::-1]

# A simple, deterministic transformation for testing purposes
def xor_bytes(audio1: bytes, audio2: bytes) -> bytes:
    length = min(len(audio1), len(audio2))
    return bytes(a ^ b for a, b in zip(audio1[:length], audio2[:length]))


class CPUProvider:
    """
    CPU-based provider that performs simple, deterministic audio transformations for testing.
    """

    def __init__(self, settings: Dict[str, Any]):
        # The settings parameter is unused for now but is part of the provider contract
        self.sessions = {}

    async def health(self) -> Dict[str, Any]:
        return {"status": "ok", "engine": "cpu"}

    async def capabilities(self) -> Dict[str, Any]:
        return {
            "task_types": ["anonymize", "convert"],
            "modes": ["non_streaming", "streaming"],
            "device": "cpu",
        }

    async def process(self, audio_input: bytes, config: Dict[str, Any]) -> bytes:
        """
        Processes audio using a simple, deterministic transformation.
        """
        task_type = config.get("task_type")
        if task_type == "anonymize":
            # Reverse the audio bytes for a simple, verifiable transformation
            return reverse_bytes(audio_input)
        elif task_type == "convert":
            reference_audio = config.get("reference_audio")
            if not reference_audio:
                raise ValueError("Reference audio is required for voice conversion.")
            # XOR the audio with the reference audio for a simple, verifiable transformation
            return xor_bytes(audio_input, reference_audio)
        else:
            raise ValueError(f"Unsupported task type: {task_type}")

    async def start_session(self, config: Dict[str, Any]) -> str:
        """Starts a new streaming session."""
        if "task_type" not in config:
            raise ValueError("`task_type` is required.")
        task_type = config.get("task_type")
        if task_type not in ["anonymize", "convert"]:
            raise ValueError(f"Unsupported task_type: {task_type}")
        if task_type == "convert" and "reference_audio" not in config:
            raise ValueError("`reference_audio` is required for 'convert' task type.")
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            "config": config,
            "chunks": [],
            "status": "started",
        }
        logger.info(f"Started session {session_id}")
        return session_id

    async def process_chunk(self, session_id: str, chunk: bytes, sequence_id: int) -> Dict[str, Any]:
        """Processes a single chunk of audio for a session."""
        if session_id not in self.sessions:
            raise ValueError(f"Session not found: {session_id}")
        
        self.sessions[session_id]["chunks"].append(chunk)
        # In this simple provider, we collect all chunks and process them in end_session.
        # A more advanced provider would process and return partial results here.
        return {"status": "chunk_received", "sequence_id": sequence_id}

    async def end_session(self, session_id: str) -> bytes:
        """Ends a streaming session, processes the audio, and returns the result."""
        if session_id not in self.sessions:
            raise ValueError(f"Session not found: {session_id}")

        session = self.sessions.pop(session_id)
        config = session["config"]
        all_audio = b"".join(session["chunks"])

        logger.info(f"Ending session {session_id}, processing {len(all_audio)} bytes.")
        
        # Reuse the non-streaming process method to perform the transformation
        processed_audio = await self.process(all_audio, config)
        return processed_audio

    async def cancel_session(self, session_id: str) -> None:
        """Cancels a streaming session."""
        if session_id not in self.sessions:
            raise ValueError(f"Session not found: {session_id}")
        self.sessions.pop(session_id)
        logger.info(f"Cancelled session {session_id}")
