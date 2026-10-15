import pytest
from starlette.testclient import TestClient
from apps.api.main import app, provider_registry
from packages.sas_core.registry import ProviderRegistry
from providers.mock_provider import MockProvider

@pytest.fixture
def client(monkeypatch):
    # Isolate the tests by only using the MockProvider
    mock_registry = ProviderRegistry()
    mock_registry.providers = {"mock": MockProvider()}
    monkeypatch.setattr("apps.api.main.provider_registry", mock_registry)
    return TestClient(app)

@pytest.mark.asyncio
async def test_list_providers(client):
    response = client.get("/providers")
    assert response.status_code == 200
    providers = response.json()
    assert "mock" in providers

def test_start_session_and_websocket_streaming(client):
    # Start session
    config = {
        "task_type": "anonymize",
        "mode": "streaming",
        "device": "cpu",
    }
    response = client.post("/sessions/start", json=config)
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "session_started"
    session_id = json_data["session_id"]
    assert session_id

    # Test websocket
    with client.websocket_connect(f"/sessions/{session_id}") as websocket:
        websocket.send_json({"audio": "data", "sequence_id": 0})
        response = websocket.receive_json()
        assert response["status"] == "processed"
        assert response["audio"] == "data"
        assert response["sequence_id"] == 0