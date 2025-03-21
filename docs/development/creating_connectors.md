# Creating Custom Connectors and Providers

This guide explains how to create custom connectors and providers for the Z888 AI Hub library.

## Overview

A connector is a class that implements the communication with a specific AI service. Each connector must inherit from the `BaseConnector` class and implement its abstract methods.

A provider is a class that manages a collection of related connectors and provides a unified interface for working with them. Each provider must inherit from the `BaseProvider` class.

## Basic Structure

Here's a basic template for creating a new connector:

```python
from typing import Any, Dict, List, Optional
from z888_ai_hub.connectors.base import BaseConnector
from z888_ai_hub.connectors.base import ConnectorCapabilities

class CustomConnector(BaseConnector):
    """Custom connector for AI service."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the connector.
        
        Args:
            config: Configuration dictionary containing API settings
        """
        super().__init__(config)
        self.api_key = config.get("api_key")
        self.model = config.get("model", "default-model")
        self.max_tokens = config.get("max_tokens", 1000)
        self.temperature = config.get("temperature", 0.7)
    
    @property
    def capabilities(self) -> List[ConnectorCapabilities]:
        """Get list of supported capabilities.
        
        Returns:
            List of supported capabilities
        """
        return [
            ConnectorCapabilities.TEXT_GENERATION,
            ConnectorCapabilities.TEXT_SUMMARIZATION
        ]
    
    async def generate_text(
        self,
        prompt: str,
        **kwargs: Any
    ) -> str:
        """Generate text using the AI service.
        
        Args:
            prompt: Input prompt text
            **kwargs: Additional parameters for the AI model
            
        Returns:
            Generated text as string
        """
        # Implement API call here
        pass
    
    async def summarize_text(
        self,
        text: str,
        **kwargs: Any
    ) -> str:
        """Summarize text using the AI service.
        
        Args:
            text: Text to summarize
            **kwargs: Additional parameters for the AI model
            
        Returns:
            Summarized text as string
        """
        # Implement API call here
        pass
```

## Required Methods

### 1. Constructor

```python
def __init__(self, config: Dict[str, Any]):
    """Initialize the connector.
    
    Args:
        config: Configuration dictionary containing API settings
    """
    super().__init__(config)
    # Initialize your connector-specific settings
```

### 2. Capabilities

```python
@property
def capabilities(self) -> List[ConnectorCapabilities]:
    """Get list of supported capabilities.
    
    Returns:
        List of supported capabilities
    """
    return [
        ConnectorCapabilities.TEXT_GENERATION,
        ConnectorCapabilities.TEXT_SUMMARIZATION,
        ConnectorCapabilities.TEXT_CLASSIFICATION,
        ConnectorCapabilities.OCR
    ]
```

### 3. Text Generation

```python
async def generate_text(
    self,
    prompt: str,
    **kwargs: Any
) -> str:
    """Generate text using the AI service.
    
    Args:
        prompt: Input prompt text
        **kwargs: Additional parameters for the AI model
        
    Returns:
        Generated text as string
    """
    # Implement API call here
    pass
```

### 4. Text Summarization

```python
async def summarize_text(
    self,
    text: str,
    **kwargs: Any
) -> str:
    """Summarize text using the AI service.
    
    Args:
        text: Text to summarize
        **kwargs: Additional parameters for the AI model
        
    Returns:
        Summarized text as string
    """
    # Implement API call here
    pass
```

### 5. Text Classification

```python
async def classify_text(
    self,
    text: str,
    categories: List[str],
    **kwargs: Any
) -> str:
    """Classify text using the AI service.
    
    Args:
        text: Text to classify
        categories: List of possible categories
        **kwargs: Additional parameters for the AI model
        
    Returns:
        Determined category as string
    """
    # Implement API call here
    pass
```

### 6. OCR

```python
async def extract_text_from_image(
    self,
    image_path: str,
    **kwargs: Any
) -> str:
    """Extract text from image using OCR.
    
    Args:
        image_path: Path to the image file
        **kwargs: Additional parameters for the AI model
        
    Returns:
        Extracted text as string
    """
    # Implement API call here
    pass
```

## Error Handling

Your connector should handle errors appropriately:

```python
from z888_ai_hub.exceptions import ConnectorError

async def generate_text(self, prompt: str, **kwargs: Any) -> str:
    try:
        # Make API call
        response = await self._make_api_call(prompt, **kwargs)
        return response
    except Exception as e:
        raise ConnectorError(f"Failed to generate text: {str(e)}")
```

## Configuration

Add your connector's configuration to `config.yaml`:

```yaml
services:
  custom_service:
    api_key: ${CUSTOM_API_KEY}
    model: custom-model
    max_tokens: 1000
    temperature: 0.7

connectors:
  custom:
    enabled: true
    capabilities:
      - text_generation
      - text_summarization
    default_model: custom-model
```

## Testing

Create tests for your connector:

```python
import pytest
from z888_ai_hub.connectors.custom import CustomConnector

@pytest.fixture
def connector():
    config = {
        "api_key": "test-key",
        "model": "test-model",
        "max_tokens": 1000,
        "temperature": 0.7
    }
    return CustomConnector(config)

@pytest.mark.asyncio
async def test_generate_text(connector):
    text = await connector.generate_text("Test prompt")
    assert isinstance(text, str)
    assert len(text) > 0

@pytest.mark.asyncio
async def test_summarize_text(connector):
    summary = await connector.summarize_text("Long test text...")
    assert isinstance(summary, str)
    assert len(summary) > 0
```

## Best Practices

1. **Documentation**
   - Write clear docstrings for all methods
   - Include type hints
   - Document all parameters and return values

2. **Error Handling**
   - Use specific exception types
   - Provide meaningful error messages
   - Handle API rate limits

3. **Testing**
   - Write unit tests for all methods
   - Include integration tests
   - Mock external API calls

4. **Configuration**
   - Use environment variables for sensitive data
   - Validate configuration values
   - Provide default values where appropriate

## Example Implementation

Here's a complete example of a custom connector:

```python
import aiohttp
from typing import Any, Dict, List, Optional
from z888_ai_hub.connectors.base import BaseConnector
from z888_ai_hub.connectors.base import ConnectorCapabilities
from z888_ai_hub.exceptions import ConnectorError

class CustomConnector(BaseConnector):
    """Custom connector for AI service."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the connector.
        
        Args:
            config: Configuration dictionary containing API settings
        """
        super().__init__(config)
        self.api_key = config.get("api_key")
        self.model = config.get("model", "default-model")
        self.max_tokens = config.get("max_tokens", 1000)
        self.temperature = config.get("temperature", 0.7)
        self.base_url = "https://api.custom-service.com/v1"
    
    @property
    def capabilities(self) -> List[ConnectorCapabilities]:
        """Get list of supported capabilities.
        
        Returns:
            List of supported capabilities
        """
        return [
            ConnectorCapabilities.TEXT_GENERATION,
            ConnectorCapabilities.TEXT_SUMMARIZATION
        ]
    
    async def _make_api_call(
        self,
        endpoint: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Make API call to the service.
        
        Args:
            endpoint: API endpoint
            data: Request data
            
        Returns:
            API response
            
        Raises:
            ConnectorError: If API call fails
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/{endpoint}",
                    headers=headers,
                    json=data
                ) as response:
                    if response.status != 200:
                        raise ConnectorError(
                            f"API call failed with status {response.status}"
                        )
                    return await response.json()
        except Exception as e:
            raise ConnectorError(f"Failed to make API call: {str(e)}")
    
    async def generate_text(
        self,
        prompt: str,
        **kwargs: Any
    ) -> str:
        """Generate text using the AI service.
        
        Args:
            prompt: Input prompt text
            **kwargs: Additional parameters for the AI model
            
        Returns:
            Generated text as string
            
        Raises:
            ConnectorError: If text generation fails
        """
        data = {
            "prompt": prompt,
            "model": self.model,
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "temperature": kwargs.get("temperature", self.temperature)
        }
        
        try:
            response = await self._make_api_call("generate", data)
            return response["text"]
        except Exception as e:
            raise ConnectorError(f"Failed to generate text: {str(e)}")
    
    async def summarize_text(
        self,
        text: str,
        **kwargs: Any
    ) -> str:
        """Summarize text using the AI service.
        
        Args:
            text: Text to summarize
            **kwargs: Additional parameters for the AI model
            
        Returns:
            Summarized text as string
            
        Raises:
            ConnectorError: If text summarization fails
        """
        data = {
            "text": text,
            "model": self.model,
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "temperature": kwargs.get("temperature", self.temperature)
        }
        
        try:
            response = await self._make_api_call("summarize", data)
            return response["summary"]
        except Exception as e:
            raise ConnectorError(f"Failed to summarize text: {str(e)}")
```

## Creating Providers

### Basic Structure

Here's a basic template for creating a new provider:

```python
from typing import Any, Dict, List, Optional
from z888_ai_hub.providers.base import BaseProvider
from z888_ai_hub.connectors.base import BaseConnector

class CustomProvider(BaseProvider):
    """Provider for managing custom AI service connectors."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the provider.
        
        Args:
            config: Configuration dictionary containing provider settings
        """
        super().__init__(config)
        self.connectors: Dict[str, BaseConnector] = {}
        self._initialize_connectors()
    
    def _initialize_connectors(self) -> None:
        """Initialize connectors based on configuration."""
        for name, connector_config in self.config.get("connectors", {}).items():
            connector_class = self._get_connector_class(name)
            self.connectors[name] = connector_class(connector_config)
    
    def _get_connector_class(self, name: str) -> type[BaseConnector]:
        """Get connector class by name.
        
        Args:
            name: Connector name
            
        Returns:
            Connector class
            
        Raises:
            ValueError: If connector class not found
        """
        # Implement connector class lookup logic
        pass
    
    async def generate_text(
        self,
        prompt: str,
        connector_name: Optional[str] = None,
        **kwargs: Any
    ) -> str:
        """Generate text using the specified connector.
        
        Args:
            prompt: Input prompt text
            connector_name: Name of the connector to use
            **kwargs: Additional parameters for the AI model
            
        Returns:
            Generated text as string
            
        Raises:
            ValueError: If connector not found
            ConnectorError: If text generation fails
        """
        connector = self._get_connector(connector_name)
        return await connector.generate_text(prompt, **kwargs)
    
    async def summarize_text(
        self,
        text: str,
        connector_name: Optional[str] = None,
        **kwargs: Any
    ) -> str:
        """Summarize text using the specified connector.
        
        Args:
            text: Text to summarize
            connector_name: Name of the connector to use
            **kwargs: Additional parameters for the AI model
            
        Returns:
            Summarized text as string
            
        Raises:
            ValueError: If connector not found
            ConnectorError: If text summarization fails
        """
        connector = self._get_connector(connector_name)
        return await connector.summarize_text(text, **kwargs)
    
    def _get_connector(self, name: Optional[str] = None) -> BaseConnector:
        """Get connector by name or default connector.
        
        Args:
            name: Connector name
            
        Returns:
            Connector instance
            
        Raises:
            ValueError: If connector not found
        """
        if name is None:
            name = self.config.get("default_connector")
        
        if name not in self.connectors:
            raise ValueError(f"Connector '{name}' not found")
        
        return self.connectors[name]

### Configuration

Add your provider's configuration to `config.yaml`:

```yaml
providers:
  custom:
    enabled: true
    default_connector: custom_connector_1
    connectors:
      custom_connector_1:
        api_key: ${CUSTOM_API_KEY_1}
        model: custom-model-1
        max_tokens: 1000
        temperature: 0.7
      custom_connector_2:
        api_key: ${CUSTOM_API_KEY_2}
        model: custom-model-2
        max_tokens: 2000
        temperature: 0.5
```

### Testing

Create tests for your provider:

```python
import pytest
from z888_ai_hub.providers.custom import CustomProvider

@pytest.fixture
def provider():
    config = {
        "default_connector": "connector1",
        "connectors": {
            "connector1": {
                "api_key": "test-key-1",
                "model": "test-model-1",
                "max_tokens": 1000,
                "temperature": 0.7
            },
            "connector2": {
                "api_key": "test-key-2",
                "model": "test-model-2",
                "max_tokens": 2000,
                "temperature": 0.5
            }
        }
    }
    return CustomProvider(config)

@pytest.mark.asyncio
async def test_generate_text(provider):
    # Test with default connector
    text = await provider.generate_text("Test prompt")
    assert isinstance(text, str)
    assert len(text) > 0
    
    # Test with specific connector
    text = await provider.generate_text(
        "Test prompt",
        connector_name="connector2"
    )
    assert isinstance(text, str)
    assert len(text) > 0

@pytest.mark.asyncio
async def test_summarize_text(provider):
    # Test with default connector
    summary = await provider.summarize_text("Long test text...")
    assert isinstance(summary, str)
    assert len(summary) > 0
    
    # Test with specific connector
    summary = await provider.summarize_text(
        "Long test text...",
        connector_name="connector2"
    )
    assert isinstance(summary, str)
    assert len(summary) > 0
```

### Best Practices for Providers

1. **Connector Management**
   - Initialize connectors lazily
   - Cache connector instances
   - Handle connector lifecycle

2. **Error Handling**
   - Provide fallback connectors
   - Handle connector failures gracefully
   - Log connector errors

3. **Configuration**
   - Validate provider configuration
   - Support environment variables
   - Provide default values

4. **Testing**
   - Test with multiple connectors
   - Test fallback behavior
   - Mock connector responses