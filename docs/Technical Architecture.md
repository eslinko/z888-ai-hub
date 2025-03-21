# Technical Architecture

## Project Structure

```
z888-ai-hub/
├── src/
│   └── z888_ai_hub/
│       ├── __init__.py
│       ├── client.py
│       ├── config/
│       │   ├── __init__.py
│       │   └── config_loader.py
│       ├── connectors/
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── mistral.py
│       │   └── anthropic.py
│       └── processors/
│           ├── __init__.py
│           └── text_generation.py
├── tests/
│   ├── __init__.py
│   ├── test_client.py
│   ├── test_config.py
│   ├── test_connectors.py
│   └── test_processors.py
├── config/
│   ├── base_config.yaml
│   └── prod_config.yaml
├── docs/
│   ├── api.md
│   ├── configuration.md
│   └── installation.md
├── requirements.txt
├── requirements-dev.txt
└── setup.py
```

## Components

### Connectors

#### Mistral Connector
- Handles communication with Mistral AI API
- Supports text generation and OCR capabilities
- Configuration through environment variables and YAML

#### Anthropic Connector
- Manages communication with Anthropic API
- Supports text generation and summarization
- Configuration through environment variables and YAML

### Processors

#### Text Generation Processor
- Handles text generation tasks
- Configurable through YAML
- Supports multiple providers

### Configuration

#### ConfigLoader
- Loads and validates YAML configurations
- Supports environment-specific configs
- Handles environment variable substitution

## Configuration Files

### services.yaml
```yaml
api:
  base_url: "https://api.mistral.ai/v1"
  timeout: 30
  max_retries: 3
```

### connectors.yaml
```yaml
connectors:
  mistral:
    type: "mistral"
    api_key: "${MISTRAL_API_KEY}"
    base_url: "${MISTRAL_BASE_URL}"
    default_model: "mistral-large"
    capabilities:
      text_generation:
        enabled: true
      ocr:
        enabled: true
  
  anthropic:
    type: "anthropic"
    api_key: "${ANTHROPIC_API_KEY}"
    base_url: "${ANTHROPIC_BASE_URL}"
    default_model: "claude-3-opus"
    capabilities:
      text_generation:
        enabled: true
      summarization:
        enabled: true
```

### tasks.yaml
```yaml
tasks:
  text_generation:
    provider: "anthropic"
    model: "claude-3-opus"
    parameters:
      max_tokens: 1000
      temperature: 0.7
  
  summarization:
    provider: "mistral"
    model: "mistral-large"
    parameters:
      max_length: 500
```

## Error Handling

### Exception Hierarchy
```
AIError
├── ConfigError
├── ConnectorError
└── ValidationError
```

### Error Types

1. **ConfigError**
   - Invalid YAML format
   - Missing required fields
   - Invalid parameter values

2. **ConnectorError**
   - API connection issues
   - Authentication failures
   - Rate limiting

3. **ValidationError**
   - Invalid input data
   - Unsupported capabilities
   - Missing dependencies

## Logging

### Log Levels
- DEBUG: Detailed information
- INFO: General information
- WARNING: Potential issues
- ERROR: Error conditions
- CRITICAL: Critical failures

### Log Format
```
%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

## Testing

### Test Structure
- Unit tests for each component
- Integration tests for API interactions
- Configuration validation tests

### Test Coverage
- Core functionality: 100%
- Error handling: 100%
- Configuration: 100%
- API interactions: 90%

## Development Guidelines

### Code Style
- Follow PEP 8
- Use type hints
- Document all public APIs
- Write unit tests

### Git Workflow
- Feature branches
- Pull request reviews
- Semantic versioning
- Changelog updates

### Documentation
- Keep docs up to date
- Include code examples
- Document breaking changes
- Update API reference

## Known Issues

1. **Rate Limiting**
   - Mistral API has strict rate limits
   - Implement exponential backoff
   - Monitor usage carefully

2. **Configuration Validation**
   - Some edge cases not covered
   - Need more validation rules
   - Better error messages needed

3. **Error Recovery**
   - Limited retry mechanisms
   - Need better fallback options
   - Improve error reporting

## Future Improvements

1. **Performance**
   - Implement caching
   - Add connection pooling
   - Optimize API calls

2. **Features**
   - Add more AI providers
   - Support batch processing
   - Add streaming responses

3. **Monitoring**
   - Add metrics collection
   - Implement health checks
   - Add performance monitoring 