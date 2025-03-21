"""
Unit tests for Anthropic connector.
"""

import pytest
from unittest.mock import Mock, patch
from z888_ai_hub.connectors.anthropic import AnthropicConnector
from z888_ai_hub.connectors.base_connector import ConnectorCapability
from z888_ai_hub.utils.logging_utils import setup_logger

logger = setup_logger('TestAnthropicConnectorUnit')

@pytest.mark.unit
@pytest.mark.asyncio
async def test_anthropic_connector_initialization():
    """Тестирует инициализацию Anthropic коннектора."""
    connector = AnthropicConnector(
        api_key="test_key",
        base_url="https://test.api.anthropic.com"
    )
    
    assert connector.api_key == "test_key"
    assert connector.base_url == "https://test.api.anthropic.com"
    assert connector.default_model == "claude-3-sonnet-20240229"
    assert ConnectorCapability.SUMMARY in connector.capabilities
    assert ConnectorCapability.VECTORIZATION in connector.capabilities

@pytest.mark.unit
@pytest.mark.asyncio
async def test_generate_summary(mock_anthropic_connector):
    """Тестирует генерацию резюме."""
    test_text = "Test document content"
    expected_summary = "Test summary"
    
    mock_anthropic_connector.generate_summary.return_value = expected_summary
    
    summary = await mock_anthropic_connector.generate_summary(test_text)
    
    assert summary == expected_summary
    mock_anthropic_connector.generate_summary.assert_called_once_with(test_text)

@pytest.mark.unit
@pytest.mark.asyncio
async def test_vectorize_text(mock_anthropic_connector):
    """Тестирует векторизацию текста."""
    test_text = "Test document content"
    expected_vector = [0.1, 0.2, 0.3]
    
    mock_anthropic_connector.vectorize_text.return_value = expected_vector
    
    vector = await mock_anthropic_connector.vectorize_text(test_text)
    
    assert vector == expected_vector
    mock_anthropic_connector.vectorize_text.assert_called_once_with(test_text)

@pytest.mark.unit
@pytest.mark.asyncio
async def test_handle_error(mock_anthropic_connector):
    """Тестирует обработку ошибок."""
    test_text = "Test document content"
    mock_anthropic_connector.generate_summary.side_effect = Exception("Test error")
    
    with pytest.raises(Exception) as exc_info:
        await mock_anthropic_connector.generate_summary(test_text)
    
    assert str(exc_info.value) == "Test error"

@pytest.mark.unit
@pytest.mark.asyncio
async def test_validate_capabilities():
    """Тестирует валидацию возможностей коннектора."""
    connector = AnthropicConnector(
        api_key="test_key",
        base_url="https://test.api.anthropic.com"
    )
    
    assert connector.has_capability(ConnectorCapability.SUMMARY)
    assert connector.has_capability(ConnectorCapability.VECTORIZATION)
    assert not connector.has_capability(ConnectorCapability.IMAGE_PROCESSING)

@pytest.mark.unit
@pytest.mark.asyncio
async def test_validate_configuration():
    """Тестирует валидацию конфигурации."""
    with pytest.raises(ValueError) as exc_info:
        AnthropicConnector(
            api_key="",
            base_url="https://test.api.anthropic.com"
        )
    assert "API key is required" in str(exc_info.value)
    
    with pytest.raises(ValueError) as exc_info:
        AnthropicConnector(
            api_key="test_key",
            base_url=""
        )
    assert "Base URL is required" in str(exc_info.value) 