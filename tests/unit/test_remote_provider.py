"""
Unit tests for the remote provider.
"""
import pytest
import httpx
from unittest.mock import AsyncMock, patch
from providers.remote.provider import RemoteProvider

@pytest.mark.asyncio
async def test_remote_provider_health_success():
    """
    Tests health check with a successful response from the worker.
    """
    mock_request = httpx.Request("GET", "http://test/health")
    mock_response = httpx.Response(200, json={"status": "ok"}, request=mock_request)
    
    with patch('httpx.AsyncClient.get', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        
        provider = RemoteProvider(settings={})
        health = await provider.health()
        
        mock_get.assert_awaited_once_with("/health")
        assert health == {"status": "ok"}

@pytest.mark.asyncio
async def test_remote_provider_health_failure():
    """
    Tests health check when the worker is unreachable.
    """
    with patch('httpx.AsyncClient.get', new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = httpx.RequestError("Connection failed", request=None)

        provider = RemoteProvider(settings={})
        health = await provider.health()

        mock_get.assert_awaited_once_with("/health")
        assert health["status"] == "error"
        assert "Failed to connect to worker" in health["detail"]

@pytest.mark.asyncio
async def test_remote_provider_capabilities_success():
    """
    Tests capabilities fetching with a successful response from the worker.
    """
    expected_caps = {
        "task_types": ["anonymize", "convert"],
        "modes": ["streaming", "non_streaming"],
        "devices": ["remote_gpu"],
    }
    mock_request = httpx.Request("GET", "http://test/capabilities")
    mock_response = httpx.Response(200, json=expected_caps, request=mock_request)
    
    with patch('httpx.AsyncClient.get', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        
        provider = RemoteProvider(settings={})
        caps = await provider.capabilities()
        
        mock_get.assert_awaited_once_with("/capabilities")
        assert caps == expected_caps

@pytest.mark.asyncio
async def test_remote_provider_capabilities_failure():
    """
    Tests capabilities fetching when the worker is unreachable.
    """
    with patch('httpx.AsyncClient.get', new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = httpx.RequestError("Connection failed", request=None)

        provider = RemoteProvider(settings={})
        caps = await provider.capabilities()

        mock_get.assert_awaited_once_with("/capabilities")
        # On failure, the provider should return default capabilities.
        assert caps == {
            "task_types": ["anonymize", "convert"],
            "modes": ["streaming", "non_streaming"],
            "devices": ["remote_gpu"],
        }
