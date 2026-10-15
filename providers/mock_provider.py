import uuid

class MockProvider:
    """
    A mock provider that supports both `anonymize` and `convert` tasks for the SAS platform.
    """
    def __init__(self):
        self._sessions = {}

    async def health(self):
        return {"status": "healthy", "details": "Mock provider is operational"}

    async def capabilities(self):
        return {
            "task_types": ["anonymize", "convert"],
            "modes": ["streaming", "non_streaming"],
            "device": "cpu"
        }

    async def start_session(self, config):
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = {
            "task_type": config.get("task_type"),
            "details": config
        }
        return session_id

    async def process_chunk(self, session_id: str, chunk: bytes, sequence_id: int):
        session = self._sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}

        # Simulate processing by returning the chunk
        return {"audio": chunk, "sequence_id": sequence_id, "status": "processed"}

    async def process(self, session_id, audio_input):
        session = self._sessions.get(session_id)
        if not session:
            raise ValueError("Session not found")
        
        # Simulate processing by returning the input
        return {"audio": audio_input}

    async def end_session(self, session_id):
        if session_id in self._sessions:
            del self._sessions[session_id]