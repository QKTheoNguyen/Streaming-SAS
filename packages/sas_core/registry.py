from providers.mock_provider import MockProvider
from providers.cpu.provider import CPUProvider
from providers.remote.provider import RemoteProvider

class ProviderRegistry:
    """
    A registry to manage available providers for task execution.
    """
    def __init__(self):
        self.providers = {
            "mock": MockProvider(),
            "cpu": CPUProvider(settings={}),
            "remote": RemoteProvider(settings={})
        }

    async def get_provider(self, task_type: str, mode: str, device: str):
        """
        Retrieve a provider that matches the required capabilities.
        :param task_type: The type of task (e.g., "anonymize", "convert").
        :param mode: The processing mode (e.g., "streaming", "non_streaming").
        :param device: The target device (e.g., "cpu", "remote_gpu").
        :return: A provider instance that supports the requested capabilities.
        :raises ValueError: If no suitable provider is found.
        """
        for provider in self.providers.values():
            caps = await provider.capabilities()
            if (task_type in caps.get("task_types", []) and
                    mode in caps.get("modes", []) and
                    device == caps.get("device")):
                return provider
        raise ValueError(f"No provider found for task_type='{task_type}', mode='{mode}', device='{device}'")

    async def list_providers(self):
        """
        List all available providers.

        :return: Dictionary of provider names and their capabilities
        """
        capabilities = {}
        for name, provider in self.providers.items():
            capabilities[name] = await provider.capabilities()
        return capabilities