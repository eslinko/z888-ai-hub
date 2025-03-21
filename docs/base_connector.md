# Base Connector

The `BaseConnector` class is the foundation for all AI service connectors in the Z888 AI Hub library. It defines a standardized interface for interacting with various AI providers.

## Overview

The `BaseConnector` class provides:
- Standardized interface for AI services
- Common functionality for all connectors
- Capability management
- Configuration handling
- Health checking

## Capabilities

Each connector can support different capabilities defined by the `ConnectorCapability` enum:

```python
class ConnectorCapability(Enum):
    SUMMARY = "summary"
    VECTORIZATION = "vectorization"
    TEXT_GENERATION = "text_generation"
    CLASSIFICATION = "classification"
    OCR = "ocr"
    AUDIO_TRANSCRIPTION = "audio_transcription"
```

## Configuration

Connectors are configured using the `ConnectorConfig` protocol:

```python
class ConnectorConfig(Protocol):
    enabled: bool
    type: str
    api_key: str
    base_url: str
    default_model: Optional[str]
    capabilities: Dict[str, Any]
```

## Basic Usage

```python
from z888_ai_hub.connectors.base_connector import BaseConnector

class CustomConnector(BaseConnector):
    def __init__(self, api_key: str, base_url: str, default_model: Optional[str] = None):
        super().__init__(api_key, base_url, default_model)
        self._capabilities = [
            ConnectorCapability.TEXT_GENERATION,
            ConnectorCapability.SUMMARY
        ]
    
    @property
    def name(self) -> str:
        return "custom"
    
    async def call_api(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        # Implement API call
        pass
    
    async def generate(self, prompt: str, model: Optional[str] = None) -> str:
        # Implement text generation
        pass
    
    async def generate_summary(self, text: str, **kwargs) -> str:
        # Implement text summarization
        pass
```

## Required Methods

### 1. Constructor

```python
def __init__(self, api_key: str, base_url: str, default_model: Optional[str] = None):
    """Initialize the connector.
    
    Args:
        api_key: API key for authentication
        base_url: Base URL for the API endpoint
        default_model: Default model to use if none is specified
    """
    self.api_key = api_key
    self.base_url = base_url
    self.default_model = default_model
    self._capabilities = []
```

### 2. Name Property

```python
@property
@abstractmethod
def name(self) -> str:
    """Return the name of the AI provider."""
    pass
```

### 3. API Call

```python
@abstractmethod
async def call_api(self, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Send a request to the AI API.
    
    Args:
        payload: Request data
        
    Returns:
        API response
    """
    pass
```

### 4. Text Generation

```python
@abstractmethod
async def generate(self, prompt: str, model: Optional[str] = None) -> str:
    """Generate text using the AI model.
    
    Args:
        prompt: Input text
        model: Specific model to use
        
    Returns:
        Generated text
    """
    pass
```

### 5. Text Summarization

```python
@abstractmethod
async def generate_summary(self, text: str, **kwargs) -> str:
    """Generate a summary of the text.
    
    Args:
        text: Text to summarize
        **kwargs: Additional arguments including:
            - max_length: Maximum length of the summary (default: 500)
            - model: Specific model to use
            
    Returns:
        Generated summary
    """
    pass
```

## Optional Methods

### 1. Text Classification

```python
@abstractmethod
def classify(self, text: str, labels: list, model: Optional[str] = None) -> str:
    """Classify text into predefined categories.
    
    Args:
        text: Input text
        labels: List of category labels
        model: Specific model to use
        
    Returns:
        Predicted category label
    """
    pass
```

### 2. OCR (Text Extraction)

```python
@abstractmethod
def extract_text(self, image_path: str, model: Optional[str] = None) -> str:
    """Extract text from an image.
    
    Args:
        image_path: Path to the image file
        model: Specific model to use
        
    Returns:
        Extracted text
    """
    pass
```

### 3. Audio Transcription

```python
@abstractmethod
def transcribe(self, audio_path: str, model: Optional[str] = None) -> str:
    """Convert speech from audio to text.
    
    Args:
        audio_path: Path to the audio file
        model: Specific model to use
        
    Returns:
        Transcribed text
    """
    pass
```

### 4. Vectorization

```python
async def vectorize(self, text: str) -> List[float]:
    """Vectorize a single text.
    
    Args:
        text: Text to vectorize
        
    Returns:
        Vector embedding
    """
    raise NotImplementedError("Vectorization is not supported by this connector")

async def vectorize_batch(self, texts: List[str]) -> List[List[float]]:
    """Vectorize a list of texts.
    
    Args:
        texts: List of texts to vectorize
        
    Returns:
        List of vector embeddings
    """
    raise NotImplementedError("Vectorization is not supported by this connector")
```

## Utility Methods

### 1. Health Check

```python
async def health_check(self) -> bool:
    """Check if the connector is healthy.
    
    Returns:
        True if connector is healthy
    """
    try:
        await self.call_api({"ping": True})
        return True
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return False
```

### 2. Configuration Validation

```python
async def validate_config(self, config: ConnectorConfig) -> bool:
    """Validate connector configuration.
    
    Args:
        config: Connector configuration
        
    Returns:
        True if configuration is valid
    """
    if not config.api_key or not config.base_url:
        return False
    return True
```

### 3. Capability Parsing

```python
def _parse_capabilities(self, capabilities_config: Dict[str, Any]) -> List[ConnectorCapability]:
    """Parse capabilities from configuration.
    
    Args:
        capabilities_config: Capabilities configuration
        
    Returns:
        List of supported capabilities
    """
    capabilities = []
    for capability in ConnectorCapability:
        if capabilities_config.get(capability.value, {}).get('enabled', False):
            capabilities.append(capability)
    return capabilities
```

## Best Practices

1. **Error Handling**
   - Use specific exceptions
   - Provide meaningful error messages
   - Log errors appropriately

2. **Configuration**
   - Validate all required parameters
   - Use environment variables for sensitive data
   - Provide reasonable defaults

3. **Capabilities**
   - Only declare supported capabilities
   - Implement all required methods
   - Raise NotImplementedError for unsupported features

4. **Testing**
   - Write unit tests for all methods
   - Test error handling
   - Mock external API calls

## Example Implementation

Here's a complete example of a custom connector:

```python
import aiohttp
from typing import Any, Dict, List, Optional
from z888_ai_hub.connectors.base_connector import BaseConnector, ConnectorCapability
from z888_ai_hub.exceptions import ConnectorError

class CustomConnector(BaseConnector):
    """Custom connector for AI service."""
    
    def __init__(self, api_key: str, base_url: str, default_model: Optional[str] = None):
        super().__init__(api_key, base_url, default_model)
        self._capabilities = [
            ConnectorCapability.TEXT_GENERATION,
            ConnectorCapability.SUMMARY
        ]
        self.session = None
    
    @property
    def name(self) -> str:
        return "custom"
    
    async def _ensure_session(self):
        """Ensure aiohttp session is created."""
        if self.session is None:
            self.session = aiohttp.ClientSession()
    
    async def call_api(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Send request to API.
        
        Args:
            payload: Request data
            
        Returns:
            API response
            
        Raises:
            ConnectorError: If API call fails
        """
        await self._ensure_session()
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            async with self.session.post(
                f"{self.base_url}/v1/completions",
                headers=headers,
                json=payload
            ) as response:
                if response.status != 200:
                    raise ConnectorError(f"API call failed with status {response.status}")
                return await response.json()
        except Exception as e:
            raise ConnectorError(f"Failed to make API call: {str(e)}")
    
    async def generate(self, prompt: str, model: Optional[str] = None) -> str:
        """Generate text.
        
        Args:
            prompt: Input text
            model: Specific model to use
            
        Returns:
            Generated text
            
        Raises:
            ConnectorError: If generation fails
        """
        model = model or self.default_model
        
        payload = {
            "model": model,
            "prompt": prompt,
            "max_tokens": 1000,
            "temperature": 0.7
        }
        
        try:
            response = await self.call_api(payload)
            return response["choices"][0]["text"]
        except Exception as e:
            raise ConnectorError(f"Failed to generate text: {str(e)}")
    
    async def generate_summary(self, text: str, **kwargs) -> str:
        """Generate text summary.
        
        Args:
            text: Text to summarize
            **kwargs: Additional arguments
            
        Returns:
            Generated summary
            
        Raises:
            ConnectorError: If summarization fails
        """
        max_length = kwargs.get("max_length", 500)
        model = kwargs.get("model", self.default_model)
        
        prompt = f"Summarize the following text in {max_length} characters:\n\n{text}"
        
        try:
            return await self.generate(prompt, model)
        except Exception as e:
            raise ConnectorError(f"Failed to generate summary: {str(e)}")
    
    async def close(self):
        """Close aiohttp session."""
        if self.session:
            await self.session.close()
            self.session = None