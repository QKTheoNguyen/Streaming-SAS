# Providers

This document outlines the provider contract and details the available providers.

## Provider Contract

Every provider must implement the following methods:

- `health()`: Returns the health status of the provider.
- `capabilities()`: Returns the capabilities of the provider, including supported task types, modes, and models.
- `start_session(config)`: Starts a new session for a given task.
- `process(session_id, audio_input)`: Processes non-streaming audio.
- `end_session(session_id)`: Ends a session.

## Available Providers

### Mock Provider

- **Name**: `mock`
- **Description**: A mock provider that returns the input audio without any processing. Useful for testing the API and UI.

### CPU Provider

- **Name**: `cpu`
- **Description**: A CPU-based provider that performs speech anonymization and voice conversion. This is the default provider for local development.
- **Limitations**: This provider is not optimized for performance and may have high latency.

### Remote Provider

- **Name**: `remote`
- **Description**: A provider that offloads inference to a remote worker, typically for GPU-intensive tasks.
- **Details**: This provider acts as a client, sending requests to a separate inference worker application. This is ideal for production environments or when local compute resources are insufficient.
