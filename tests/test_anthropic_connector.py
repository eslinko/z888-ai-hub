import os
import pytest
from unittest.mock import Mock, patch
from z888_ai_hub.connectors.anthropic import AnthropicConnector
from z888_ai_hub.connectors.base_connector import ConnectorCapability

@pytest.fixture
def mock_anthropic_client():
    """Создает мок для Anthropic клиента."""
    client = Mock()
    client.messages.create.return_value = Mock(
        content=[Mock(text="Test response")]
    )
    return client

@pytest.fixture
def connector(mock_anthropic_client):
    """Создает тестовый экземпляр AnthropicConnector."""
    with patch('anthropic.Anthropic', return_value=mock_anthropic_client):
        connector = AnthropicConnector(
            api_key="test_key",
            base_url="https://api.anthropic.com",
            default_model="claude-3-sonnet-20240229"
        )
        return connector

def test_anthropic_connector_initialization(connector):
    """Тестирует инициализацию коннектора."""
    assert connector.api_key == "test_key"
    assert connector.base_url == "https://api.anthropic.com"
    assert connector.default_model == "claude-3-sonnet-20240229"
    assert connector.client is not None

def test_anthropic_connector_capabilities(connector):
    """Тестирует поддерживаемые возможности коннектора."""
    capabilities = connector.capabilities
    assert ConnectorCapability.SUMMARY in capabilities
    assert ConnectorCapability.TEXT_GENERATION in capabilities
    assert ConnectorCapability.CLASSIFICATION in capabilities

@pytest.mark.asyncio
async def test_anthropic_connector_generate_summary(connector, mock_anthropic_client):
    """Тестирует генерацию краткого содержания."""
    text = "Test text for summarization"
    summary = await connector.generate_summary(text)
    
    assert isinstance(summary, str)
    assert len(summary) > 0
    mock_anthropic_client.messages.create.assert_called_once()

@pytest.mark.asyncio
async def test_anthropic_connector_call_api(connector, mock_anthropic_client):
    """Тестирует вызов API."""
    messages = [{"role": "user", "content": "Hello"}]
    response = await connector.call_api(messages)
    
    assert isinstance(response, dict)
    assert "text" in response
    mock_anthropic_client.messages.create.assert_called_once()

@pytest.mark.asyncio
async def test_anthropic_connector_health_check(connector):
    """Тестирует проверку работоспособности."""
    is_healthy = await connector.health_check()
    assert is_healthy is True

def test_anthropic_connector_with_env_key():
    """Тестирует инициализацию с ключом из переменных окружения."""
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test_env_key"}):
        with patch('anthropic.Anthropic') as mock_anthropic:
            connector = AnthropicConnector()
            assert connector.api_key == "test_env_key"
            mock_anthropic.assert_called_once()

@pytest.mark.asyncio
async def test_anthropic_connector_error_handling(connector, mock_anthropic_client):
    """Тестирует обработку ошибок."""
    mock_anthropic_client.messages.create.side_effect = Exception("API Error")
    
    messages = [{"role": "user", "content": "Hello"}]
    response = await connector.call_api(messages)
    
    assert isinstance(response, dict)
    assert "error" in response
    assert "API Error" in response["error"] 