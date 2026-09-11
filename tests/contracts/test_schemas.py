# Test Cases for Contract Schemas
import pytest
from jsonschema import validate, ValidationError, RefResolver
import yaml

# Load schema files
with open("packages/contracts/schemas.yaml", "r") as schemas_file:
    schemas = yaml.safe_load(schemas_file.read())

    # Adjust schema $ref definitions to $defs for compatibility
    if "definitions" in schemas:
        schemas = {"$defs": schemas["definitions"], **schemas}

with open("packages/contracts/provider_capabilities.yaml", "r") as capabilities_file:
    capabilities = yaml.safe_load(capabilities_file.read())
    # Include capabilities in schemas for compatibility
    schemas.update({"ProviderCapabilities": capabilities["ProviderCapabilities"]})

with open("packages/contracts/streaming_schemas.yaml", "r") as streaming_file:
    streaming_schemas = yaml.safe_load(streaming_file.read())

with open("packages/contracts/error_format.yaml", "r") as error_format_file:
    error_format = yaml.safe_load(error_format_file.read())

# Valid Task Configurations for Testing
valid_anonymize_config = {
    "task_type": "anonymize",
    "mode": "streaming",
    "anonymization_parameters": {
        "pitch_shift": 3,
        "voice_cloning_level": 2,
        "noise_injection": 0.05
    }
}

valid_convert_config = {
    "task_type": "convert",
    "mode": "non_streaming",
    "reference_audio": {
        "audio_data": "base64encodedstring",
        "sample_rate": 16000
    }
}

# Invalid Configurations
invalid_convert_config_missing_audio = {
    "task_type": "convert",
    "mode": "streaming"
}  # reference_audio missing

@pytest.mark.parametrize("config, is_valid", [
    (valid_anonymize_config, True),
    (valid_convert_config, True),
    (invalid_convert_config_missing_audio, False),
])
def test_run_config_schema(config, is_valid):
    """Test the RunConfig schema for valid/invalid configurations"""
    schema = schemas['schemas']['RunConfig']
    resolver = RefResolver.from_schema(schemas)  # Explicitly set resolver for $refs
    if is_valid:
        validate(instance=config, schema=schema, resolver=resolver)
    else:
        with pytest.raises(ValidationError):
            validate(instance=config, schema=schema, resolver=resolver)

@pytest.mark.parametrize("capabilities, is_valid", [
    ({
        "supported_task_types": ["anonymize", "convert"],
        "supported_modes": ["streaming", "non_streaming"],
        "supported_devices": ["cpu", "remote_gpu"],
        "meta": {
            "sample_rate": 16000,
            "codecs": ["pcm", "wav"],
            "chunk_size": 1024,
            "latency": 12.5,
            "device_info": "CPU-based reference implementation"
        }
    }, True),
    ({  # Invalid capability, missing meta
        "supported_task_types": ["anonymize"],
        "supported_modes": ["streaming"],
        "supported_devices": ["cpu"]
    }, False)
])
def test_provider_capabilities_schema(capabilities, is_valid):
    """Test the ProviderCapabilities schema."""
    schema = schemas['ProviderCapabilities']
    if is_valid:
        validate(instance=capabilities, schema=schema)
    else:
        with pytest.raises(ValidationError):
            validate(instance=capabilities, schema=schema)

def test_streaming_schema():
    """Test streaming-related schema."""
    schema = streaming_schemas['StreamingSchemas']
    valid_streaming_config = {
        "session_id": "abc123",
        "chunk_sequence": [1, 2, 3],
        "processing_states": ["received", "processing", "completed"],
        "buffer_constraints": {"max_chunks_in_buffer": 10, "max_latency_ms": 500}
    }
    validate(instance=valid_streaming_config, schema=schema)

def test_error_format_schema():
    """Test the error format schema."""
    schema = error_format['ErrorFormat']
    valid_error_config = {
        "error_code": "ERR001",
        "message": "Invalid configuration provided.",
        "details": {"field": "task_type", "reason": "Missing field"}
    }
    validate(instance=valid_error_config, schema=schema)

    invalid_error_config = {
        "message": "Missing error code"
    }  # Missing error_code

    with pytest.raises(ValidationError):
        validate(instance=invalid_error_config, schema=schema)