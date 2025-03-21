import os
import pytest
from unittest.mock import Mock, patch
from z888_ai_hub.connectors.mistral import MistralConnector
from z888_ai_hub.connectors.base_connector import ConnectorCapability

@pytest.fixture
def mock_mistral_client():
    """Создает мок для Mistral клиента."""
    client = Mock()
    client.chat.completions.create.return_value = Mock(
        choices=[Mock(message=Mock(content="Test response"))]
    )
    return client

@pytest.fixture
def connector(mock_mistral_client):
    """Создает тестовый экземпляр MistralConnector."""
    with patch('mistralai.client.MistralClient', return_value=mock_mistral_client):
        connector = MistralConnector(
            api_key="test_key",
            base_url="https://api.mistral.ai",
            default_model="mistral-large"
        )
        return connector

def test_mistral_connector_initialization(connector):
    """Тестирует инициализацию коннектора."""
    assert connector.api_key == "test_key"
    assert connector.base_url == "https://api.mistral.ai"
    assert connector.default_model == "mistral-large"
    assert connector.client is not None

def test_mistral_connector_capabilities(connector):
    """Тестирует поддерживаемые возможности коннектора."""
    capabilities = connector.capabilities
    assert ConnectorCapability.OCR in capabilities
    assert ConnectorCapability.TEXT_GENERATION in capabilities
    assert ConnectorCapability.CLASSIFICATION in capabilities

@pytest.mark.asyncio
async def test_mistral_connector_extract_text(connector, mock_mistral_client):
    """Тестирует извлечение текста из PDF."""
    pdf_path = "test.pdf"
    extracted_text = await connector.extract_text(pdf_path)
    
    assert isinstance(extracted_text, str)
    assert len(extracted_text) > 0
    mock_mistral_client.chat.completions.create.assert_called_once()

@pytest.mark.asyncio
async def test_mistral_connector_upload_pdf(connector, mock_mistral_client):
    """Тестирует загрузку PDF файла."""
    pdf_path = "test.pdf"
    signed_url = await connector.upload_pdf_to_mistral(pdf_path)
    
    assert isinstance(signed_url, str)
    assert signed_url.startswith("https://")
    mock_mistral_client.files.create.assert_called_once()

@pytest.mark.asyncio
async def test_mistral_connector_health_check(connector):
    """Тестирует проверку работоспособности."""
    is_healthy = await connector.health_check()
    assert is_healthy is True

def test_mistral_connector_with_env_key():
    """Тестирует инициализацию с ключом из переменных окружения."""
    with patch.dict(os.environ, {"MISTRAL_API_KEY": "test_env_key"}):
        with patch('mistralai.client.MistralClient') as mock_mistral:
            connector = MistralConnector()
            assert connector.api_key == "test_env_key"
            mock_mistral.assert_called_once()

@pytest.mark.asyncio
async def test_mistral_connector_error_handling(connector, mock_mistral_client):
    """Тестирует обработку ошибок."""
    mock_mistral_client.chat.completions.create.side_effect = Exception("API Error")
    
    pdf_path = "test.pdf"
    with pytest.raises(Exception) as exc_info:
        await connector.extract_text(pdf_path)
    
    assert "API Error" in str(exc_info.value) 