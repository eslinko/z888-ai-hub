# Configuration Guide

## Overview

The Z888 AI Hub uses a flexible configuration system that allows you to:
- Connect to various AI services (Mistral, Anthropic, etc.)
- Configure service-specific parameters and capabilities
- Set up logging and error handling
- Define task-specific settings and fallback providers

## Configuration Files

### Base Configuration

File `config/base_config.yaml`:

```yaml
api:
  base_url: "https://api.mistral.ai/v1"
  version: "v1"
  timeout: 30
  max_retries: 3

connectors:
  mistral:
    enabled: true
    type: "mistral"
    api_key: "${MISTRAL_API_KEY}"
    base_url: "${MISTRAL_BASE_URL}"
    default_model: "mistral-tiny"
    capabilities:
      text_generation:
        enabled: true
      ocr:
        enabled: true
  
  anthropic:
    enabled: true
    type: "anthropic"
    api_key: "${ANTHROPIC_API_KEY}"
    base_url: "${ANTHROPIC_BASE_URL}"
    default_model: "claude-3-opus"
    capabilities:
      text_generation:
        enabled: true
      summarization:
        enabled: true

tasks:
  text_generation:
    provider: "anthropic"
    fallback_providers: ["mistral"]
    max_retries: 3
    timeout: 30
    parameters:
      max_tokens: 1000
      temperature: 0.7
  
  summarization:
    provider: "mistral"
    fallback_providers: []
    max_retries: 2
    timeout: 20
    parameters:
      max_length: 500
```

### Environment-Specific Configuration

File `config/prod_config.yaml`:

```yaml
api:
  timeout: 60
  max_retries: 5

connectors:
  mistral:
    default_model: "mistral-large"
  
  anthropic:
    default_model: "claude-3-opus"
```

## Loading Configuration

```python
from z888_ai_hub.config import load_config, merge_configs, validate_config

# Load base configuration
config = load_config("config/base_config.yaml")

# Load environment-specific configuration
base_config = load_config("config/base_config.yaml")
env_config = load_config("config/prod_config.yaml")
merged_config = merge_configs(base_config, env_config)

# Validate configuration
validate_config(merged_config)
```

## Configuration Parameters

### API Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| base_url | str | - | Base URL for API requests |
| version | str | "v1" | API version |
| timeout | int | 30 | Request timeout in seconds |
| max_retries | int | 3 | Maximum number of retry attempts |

### Connector Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| enabled | bool | true | Whether the connector is enabled |
| type | str | - | Connector type (mistral, anthropic, etc.) |
| api_key | str | - | Service API key |
| base_url | str | - | Service base URL |
| default_model | str | - | Default model to use |
| capabilities | dict | - | Available capabilities and their settings |

### Task Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| provider | str | - | Primary provider for the task |
| fallback_providers | list | [] | List of fallback providers |
| max_retries | int | 3 | Maximum number of retry attempts |
| timeout | int | 30 | Task timeout in seconds |
| parameters | dict | - | Task-specific parameters |

## Advanced Configuration

### Environment Variables

The configuration system supports environment variable substitution:

```yaml
connectors:
  mistral:
    api_key: "${MISTRAL_API_KEY}"
    base_url: "${MISTRAL_BASE_URL}"
```

### Capabilities

Each connector can support different capabilities:

```yaml
capabilities:
  text_generation:
    enabled: true
  summarization:
    enabled: true
  ocr:
    enabled: true
  classification:
    enabled: true
  audio_transcription:
    enabled: true
```

### Fallback Providers

Tasks can be configured with fallback providers:

```yaml
tasks:
  text_generation:
    provider: "anthropic"
    fallback_providers: ["mistral"]
```

## Best Practices

1. **Security**
   - Store API keys in environment variables
   - Don't commit configuration files with secrets
   - Use different keys for development and production

2. **Organization**
   - Separate configuration by environment
   - Use base configuration for common settings
   - Override only necessary parameters

3. **Validation**
   - Validate configuration on startup
   - Use type hints for parameters
   - Document required parameters

4. **Error Handling**
   - Configure appropriate timeouts
   - Set up fallback providers
   - Define retry policies

## Troubleshooting

### Common Issues

1. **Missing API Key**
   ```yaml
   # Incorrect
   api_key: "your-key"
   
   # Correct
   api_key: "${MISTRAL_API_KEY}"
   ```

2. **Invalid Model Name**
   ```yaml
   # Incorrect
   model: "gpt-4"
   
   # Correct
   model: "mistral-tiny"
   ```

3. **Incorrect Capabilities**
   ```yaml
   # Incorrect
   capabilities:
     code_generation: true
   
   # Correct
   capabilities:
     text_generation:
       enabled: true
     ocr:
       enabled: true
   ```

### Getting Help

- Check [GitHub Issues](https://github.com/yourusername/z888-ai-hub/issues)
- Create a new issue with:
  - Configuration file contents
  - Error message
  - Steps to reproduce 