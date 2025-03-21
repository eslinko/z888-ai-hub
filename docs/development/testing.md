# Testing Guide

This guide explains how to write and run tests for the Z888 AI Hub library.

## Project Structure

The test suite is organized as follows:

```
tests/
├── conftest.py              # Common test configuration and fixtures
├── unit/                    # Unit tests
├── integration/            # Integration tests
├── sample_files/          # Test data files
├── sample_images/         # Test image files
├── sample_docs/           # Test document files
├── sample_pdfs/           # Test PDF files
└── temp/                  # Temporary test files
```

## Test Configuration

The `conftest.py` file contains common test configuration and fixtures:

```python
def pytest_configure(config):
    """Configure pytest for all tests."""
    # Add markers
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "asyncio: mark test as an async test")

# Common fixtures
@pytest.fixture(scope="session")
def test_root():
    """Return test root directory."""
    return os.path.dirname(os.path.abspath(__file__))

@pytest.fixture(scope="session")
def sample_files_dir(test_root):
    """Return path to sample files directory."""
    return os.path.join(test_root, "sample_files")

@pytest.fixture(scope="session")
def temp_dir(test_root):
    """Return path to temporary directory."""
    return os.path.join(test_root, "temp")
```

## Writing Tests

### Unit Tests

Unit tests should be placed in the `tests/unit/` directory. Here's an example of a unit test for a connector:

```python
import pytest
from unittest.mock import Mock, patch
from z888_ai_hub.connectors.mistral import MistralConnector

@pytest.fixture
def mock_mistral_client():
    """Create mock for Mistral client."""
    client = Mock()
    client.chat.completions.create.return_value = Mock(
        choices=[Mock(message=Mock(content="Test response"))]
    )
    return client

@pytest.fixture
def connector(mock_mistral_client):
    """Create test instance of MistralConnector."""
    with patch('mistralai.client.MistralClient', return_value=mock_mistral_client):
        return MistralConnector(
            api_key="test_key",
            base_url="https://api.mistral.ai",
            default_model="mistral-large"
        )

def test_connector_initialization(connector):
    """Test connector initialization."""
    assert connector.api_key == "test_key"
    assert connector.base_url == "https://api.mistral.ai"
    assert connector.default_model == "mistral-large"

@pytest.mark.asyncio
async def test_connector_capabilities(connector):
    """Test connector capabilities."""
    capabilities = connector.capabilities
    assert "text_generation" in capabilities
    assert "text_summarization" in capabilities
```

### Integration Tests

Integration tests should be placed in the `tests/integration/` directory. Here's an example:

```python
import pytest
from z888_ai_hub import AIClient
from z888_ai_hub.config import load_config

@pytest.mark.integration
@pytest.mark.asyncio
async def test_text_generation():
    """Test text generation with real API."""
    config = load_config("config.yaml")
    client = AIClient(config)
    
    text = await client.generate_text("Write a short poem")
    assert isinstance(text, str)
    assert len(text) > 0

@pytest.mark.integration
@pytest.mark.asyncio
async def test_text_summarization():
    """Test text summarization with real API."""
    config = load_config("config.yaml")
    client = AIClient(config)
    
    summary = await client.summarize_text("Long text to summarize...")
    assert isinstance(summary, str)
    assert len(summary) > 0
```

### Test Fixtures

Common test fixtures are defined in `conftest.py`:

```python
@pytest.fixture
def mock_connector():
    """Create mock for AI connector."""
    connector = Mock(spec=BaseConnector)
    connector.generate_text.return_value = "Test response"
    connector.summarize_text.return_value = "Test summary"
    return connector

@pytest.fixture
def sample_config():
    """Return sample configuration."""
    return {
        "connectors": {
            "anthropic": {
                "type": "anthropic",
                "api_key": "test_key",
                "base_url": "https://api.anthropic.com",
                "default_model": "claude-3-sonnet-20240229"
            }
        }
    }
```

## Running Tests

### Running All Tests

```bash
pytest
```

### Running Specific Test Types

```bash
# Run unit tests only
pytest -m unit

# Run integration tests only
pytest -m integration

# Run async tests only
pytest -m asyncio
```

### Running Tests with Coverage

```bash
pytest --cov=z888_ai_hub
```

## Best Practices

1. **Test Organization**
   - Place unit tests in `tests/unit/`
   - Place integration tests in `tests/integration/`
   - Use appropriate test markers

2. **Fixtures**
   - Create reusable fixtures in `conftest.py`
   - Use appropriate fixture scopes
   - Mock external dependencies

3. **Async Testing**
   - Use `@pytest.mark.asyncio` for async tests
   - Mock async functions appropriately
   - Handle async context managers

4. **Test Data**
   - Use sample files from appropriate directories
   - Clean up temporary files after tests
   - Use realistic test data

5. **Error Handling**
   - Test error cases
   - Verify error messages
   - Test edge cases

## Example Test Files

### Connector Test

```python
# tests/test_mistral_connector.py
import pytest
from unittest.mock import Mock, patch
from z888_ai_hub.connectors.mistral import MistralConnector

@pytest.fixture
def connector():
    """Create test connector."""
    return MistralConnector(
        api_key="test_key",
        base_url="https://api.mistral.ai"
    )

@pytest.mark.asyncio
async def test_generate_text(connector):
    """Test text generation."""
    text = await connector.generate_text("Test prompt")
    assert isinstance(text, str)
    assert len(text) > 0

@pytest.mark.asyncio
async def test_error_handling(connector):
    """Test error handling."""
    with pytest.raises(Exception) as exc_info:
        await connector.generate_text("")
    assert "Invalid prompt" in str(exc_info.value)
```

### Document Processor Test

```python
# tests/test_document_processor.py
import pytest
from z888_ai_hub.processors.document_processor import DocumentProcessor

@pytest.fixture
def processor(mock_connector):
    """Create test processor."""
    return DocumentProcessor(
        connector=mock_connector,
        config={"max_tokens": 1000}
    )

@pytest.mark.asyncio
async def test_process_document(processor):
    """Test document processing."""
    result = await processor.process("test.pdf")
    assert result["summary"] is not None
    assert result["metadata"] is not None

@pytest.mark.asyncio
async def test_invalid_document(processor):
    """Test invalid document handling."""
    with pytest.raises(ValueError):
        await processor.process("invalid.pdf")
``` 