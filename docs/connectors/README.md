# Connectors Guide

## Overview

Connectors in Z888 AI Hub are responsible for interacting with various AI service providers. Each connector implements a common interface while providing provider-specific functionality.

## Available Connectors

### Mistral Connector

```python
from z888_ai_hub import AIClient

client = AIClient(
    connector_name="mistral",
    api_key="your-mistral-api-key"
)
```

Features:
- Text generation
- Code generation
- Context management
- Temperature control
- Token limit management

### Anthropic Connector

```python
from z888_ai_hub import AIClient

client = AIClient(
    connector_name="anthropic",
    api_key="your-anthropic-api-key"
)
```

Features:
- Text generation
- Code generation
- Context management
- Temperature control
- Token limit management

## Creating New Connectors

### Base Connector Interface

```python
from z888_ai_hub import BaseConnector

class CustomConnector(BaseConnector):
    async def process_request(
        self,
        prompt: str,
        model: Optional[str] = None,
        **kwargs
    ) -> str:
        # Implement request processing
        pass

    def validate_config(self, config: Dict[str, Any]) -> None:
        # Implement configuration validation
        pass
```

Required methods:
- `process_request`: Process a single request
- `validate_config`: Validate connector configuration
- `batch_process`: Process multiple requests (optional)

### Provider-Specific Features

#### HuggingFace Integration

```python
class HuggingFaceConnector(BaseConnector):
    async def process_request(
        self,
        prompt: str,
        model: str = "gpt2",
        **kwargs
    ) -> str:
        # Implement HuggingFace API integration
        pass
```

#### Kaggle Integration

```python
class KaggleConnector(BaseConnector):
    async def process_request(
        self,
        prompt: str,
        model: str = "default",
        **kwargs
    ) -> str:
        # Implement Kaggle API integration
        pass
```

## Best Practices

### Error Handling

```python
try:
    response = await connector.process_request(prompt)
except AIError as e:
    logger.error(f"AI service error: {e}")
    raise
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise
```

### Configuration

```python
def validate_config(self, config: Dict[str, Any]) -> None:
    required_fields = ["api_key", "base_url"]
    for field in required_fields:
        if field not in config:
            raise ValueError(f"Missing required field: {field}")
```

### Performance

- Use connection pooling
- Implement request caching
- Handle rate limits
- Use async/await properly

### Testing

```python
@pytest.mark.asyncio
async def test_custom_connector():
    connector = CustomConnector(
        api_key="test-key",
        base_url="http://test-api"
    )
    
    response = await connector.process_request(
        prompt="Test prompt"
    )
    assert response is not None
```

## Contributing New Connectors

1. Create a new branch
2. Implement the connector
3. Add tests
4. Update documentation
5. Submit a pull request

### Pull Request Checklist

- [ ] Connector implements BaseConnector interface
- [ ] Configuration validation is implemented
- [ ] Error handling is comprehensive
- [ ] Tests are added and passing
- [ ] Documentation is updated
- [ ] Code follows project style guide 