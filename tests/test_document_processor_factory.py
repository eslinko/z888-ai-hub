import os
import pytest
from unittest.mock import Mock, patch
from z888_ai_hub.processors.factory import DocumentProcessorFactory
from z888_ai_hub.utils.logging_utils import setup_logger

logger = setup_logger('TestDocumentProcessorFactory')

@pytest.fixture
def sample_config():
    """Создает тестовую конфигурацию."""
    return {
        "connectors": {
            "anthropic": {
                "type": "anthropic",
                "api_key": "test_key",
                "base_url": "https://api.anthropic.com",
                "default_model": "claude-3-sonnet-20240229",
                "capabilities": ["summary", "vectorization"]
            }
        },
        "tasks": {
            "summary": {
                "provider": "anthropic",
                "fallback_providers": [],
                "max_retries": 1,
                "timeout": 5
            },
            "vectorization": {
                "provider": "anthropic",
                "fallback_providers": [],
                "max_retries": 1,
                "timeout": 5
            }
        },
        "processing": {
            "file_types": [".pdf", ".txt"],
            "max_file_size": 1048576,
            "batch_size": 2
        }
    }

@pytest.mark.asyncio
async def test_create_default(sample_config):
    """Тестирует создание процессора по умолчанию."""
    mock_storage = Mock()
    mock_summary_generator = Mock()
    mock_vectorizer = Mock()
    mock_file_collector = Mock()
    mock_pdf_processor = Mock()
    mock_doc_processor = Mock()
    
    with patch('z888_ai_hub.processors.factory.Storage') as mock_storage_class, \
         patch('z888_ai_hub.processors.factory.AnthropicConnector') as mock_anthropic, \
         patch('z888_ai_hub.processors.factory.FileCollector') as mock_collector, \
         patch('z888_ai_hub.processors.factory.PdfProcessor') as mock_pdf, \
         patch('z888_ai_hub.processors.factory.DocProcessor') as mock_doc:
        
        # Настраиваем моки
        mock_storage_class.return_value = mock_storage
        mock_anthropic.return_value = mock_summary_generator
        mock_anthropic.return_value = mock_vectorizer
        mock_collector.return_value = mock_file_collector
        mock_pdf.return_value = mock_pdf_processor
        mock_doc.return_value = mock_doc_processor
        
        # Создаем процессор
        processor = await DocumentProcessorFactory.create_default("test_dir", sample_config)
        
        # Проверяем создание компонентов
        assert processor.storage == mock_storage
        assert processor.summary_generator == mock_summary_generator
        assert processor.vectorizer == mock_vectorizer
        assert processor.file_collector == mock_file_collector
        assert processor.pdf_processor == mock_pdf_processor
        assert processor.doc_processor == mock_doc_processor

@pytest.mark.asyncio
async def test_create_default_with_fallback_providers(sample_config):
    """Тестирует создание процессора с резервными провайдерами."""
    sample_config["tasks"]["summary"]["fallback_providers"] = ["mistral"]
    
    mock_storage = Mock()
    mock_summary_generator = Mock()
    mock_vectorizer = Mock()
    mock_file_collector = Mock()
    mock_pdf_processor = Mock()
    mock_doc_processor = Mock()
    
    with patch('z888_ai_hub.processors.factory.Storage') as mock_storage_class, \
         patch('z888_ai_hub.processors.factory.AnthropicConnector') as mock_anthropic, \
         patch('z888_ai_hub.processors.factory.MistralConnector') as mock_mistral, \
         patch('z888_ai_hub.processors.factory.FileCollector') as mock_collector, \
         patch('z888_ai_hub.processors.factory.PdfProcessor') as mock_pdf, \
         patch('z888_ai_hub.processors.factory.DocProcessor') as mock_doc:
        
        # Настраиваем моки
        mock_storage_class.return_value = mock_storage
        mock_anthropic.return_value = mock_summary_generator
        mock_mistral.return_value = Mock()
        mock_anthropic.return_value = mock_vectorizer
        mock_collector.return_value = mock_file_collector
        mock_pdf.return_value = mock_pdf_processor
        mock_doc.return_value = mock_doc_processor
        
        # Создаем процессор
        processor = await DocumentProcessorFactory.create_default("test_dir", sample_config)
        
        # Проверяем создание компонентов
        assert processor.storage == mock_storage
        assert processor.summary_generator == mock_summary_generator
        assert processor.vectorizer == mock_vectorizer
        assert processor.file_collector == mock_file_collector
        assert processor.pdf_processor == mock_pdf_processor
        assert processor.doc_processor == mock_doc_processor

@pytest.mark.asyncio
async def test_create_default_with_invalid_config():
    """Тестирует создание процессора с некорректной конфигурацией."""
    invalid_config = {
        "connectors": {},
        "tasks": {},
        "processing": {}
    }
    
    with pytest.raises(ValueError) as exc_info:
        await DocumentProcessorFactory.create_default("test_dir", invalid_config)
    assert "Invalid configuration" in str(exc_info.value)

@pytest.mark.asyncio
async def test_create_default_with_missing_provider(sample_config):
    """Тестирует создание процессора с отсутствующим провайдером."""
    sample_config["tasks"]["summary"]["provider"] = "nonexistent"
    
    with pytest.raises(ValueError) as exc_info:
        await DocumentProcessorFactory.create_default("test_dir", sample_config)
    assert "Provider 'nonexistent' not found" in str(exc_info.value)

@pytest.mark.asyncio
async def test_create_default_with_invalid_connector_type(sample_config):
    """Тестирует создание процессора с некорректным типом коннектора."""
    sample_config["connectors"]["anthropic"]["type"] = "invalid"
    
    with pytest.raises(ValueError) as exc_info:
        await DocumentProcessorFactory.create_default("test_dir", sample_config)
    assert "Invalid connector type" in str(exc_info.value)

@pytest.mark.asyncio
async def test_create_default_with_missing_required_fields(sample_config):
    """Тестирует создание процессора с отсутствующими обязательными полями."""
    del sample_config["connectors"]["anthropic"]["api_key"]
    
    with pytest.raises(ValueError) as exc_info:
        await DocumentProcessorFactory.create_default("test_dir", sample_config)
    assert "Missing required field" in str(exc_info.value) 