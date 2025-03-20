"""
Tests for connector integration with document processor.
"""

import os
import pytest
from unittest.mock import Mock, AsyncMock, patch
from z888_ai_hub.processors.document_processor import DocumentProcessor
from z888_ai_hub.processors.factory import DocumentProcessorFactory
from z888_ai_hub.connectors.base_connector import BaseConnector, ConnectorCapability
from z888_ai_hub.storage.database.client import SupabaseStorage
from z888_ai_hub.utils.file_collector import FileCollector
from z888_ai_hub.processors.pdf_processor import PdfProcessor
from z888_ai_hub.processors.doc_processor import DocProcessor
import asyncio

# Фикстуры
@pytest.fixture
def mock_summary_connector():
    connector = Mock(spec=BaseConnector)
    connector.capabilities = {ConnectorCapability.SUMMARY}
    connector.generate_summary = AsyncMock(return_value="Test summary")
    return connector

@pytest.fixture
def mock_vectorizer_connector():
    connector = Mock(spec=BaseConnector)
    connector.capabilities = {ConnectorCapability.VECTORIZATION}
    connector.vectorize = AsyncMock(return_value=[0.1, 0.2, 0.3])
    connector.vectorize_batch = AsyncMock(return_value=[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])
    return connector

@pytest.fixture
def mock_storage():
    storage = Mock(spec=SupabaseStorage)
    storage.save_document = AsyncMock()
    storage.save_embeddings = AsyncMock()
    return storage

@pytest.fixture
def mock_file_collector():
    collector = Mock(spec=FileCollector)
    return collector

@pytest.fixture
def document_processor(mock_summary_connector, mock_vectorizer_connector, mock_storage, mock_file_collector):
    return DocumentProcessor(
        storage=mock_storage,
        summary_generator=mock_summary_connector,
        vectorizer=mock_vectorizer_connector,
        file_collector=mock_file_collector,
        pdf_processor=Mock(spec=PdfProcessor),
        doc_processor=Mock(spec=DocProcessor)
    )

# Тесты для DocumentProcessor
@pytest.mark.asyncio
async def test_document_processor_initialization():
    """Test document processor initialization with valid connectors."""
    mock_summary = Mock(spec=BaseConnector)
    mock_summary.capabilities = {ConnectorCapability.SUMMARY}
    
    mock_vectorizer = Mock(spec=BaseConnector)
    mock_vectorizer.capabilities = {ConnectorCapability.VECTORIZATION}
    
    processor = DocumentProcessor(
        storage=Mock(),
        summary_generator=mock_summary,
        vectorizer=mock_vectorizer,
        file_collector=Mock(),
        pdf_processor=Mock(),
        doc_processor=Mock()
    )
    
    assert processor.summary_generator == mock_summary
    assert processor.vectorizer == mock_vectorizer

@pytest.mark.asyncio
async def test_document_processor_invalid_connectors():
    """Test document processor initialization with invalid connectors."""
    mock_summary = Mock(spec=BaseConnector)
    mock_summary.capabilities = {ConnectorCapability.VECTORIZATION}  # Wrong capability
    
    mock_vectorizer = Mock(spec=BaseConnector)
    mock_vectorizer.capabilities = {ConnectorCapability.SUMMARY}  # Wrong capability
    
    with pytest.raises(ValueError, match="Summary generator connector must have SUMMARY capability"):
        DocumentProcessor(
            storage=Mock(),
            summary_generator=mock_summary,
            vectorizer=mock_vectorizer,
            file_collector=Mock(),
            pdf_processor=Mock(),
            doc_processor=Mock()
        )

@pytest.mark.asyncio
async def test_document_processor_summary_generation(document_processor, mock_summary_connector):
    """Test summary generation using connector."""
    doc = Mock()
    doc.content.text = "Test content"
    
    summary = await document_processor.summary_generator.generate_summary(doc.content.text)
    
    assert summary == "Test summary"
    mock_summary_connector.generate_summary.assert_called_once_with("Test content")

@pytest.mark.asyncio
async def test_document_processor_vectorization(document_processor, mock_vectorizer_connector):
    """Test text vectorization using connector."""
    text = "Test text"
    texts = ["Text 1", "Text 2"]
    
    vector = await document_processor.vectorizer.vectorize(text)
    vectors = await document_processor.vectorizer.vectorize_batch(texts)
    
    assert vector == [0.1, 0.2, 0.3]
    assert vectors == [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
    
    mock_vectorizer_connector.vectorize.assert_called_once_with(text)
    mock_vectorizer_connector.vectorize_batch.assert_called_once_with(texts)

# Тесты для DocumentProcessorFactory
@pytest.mark.asyncio
async def test_factory_create_processor(mock_file_collector):
    """Test factory creating processor with valid configuration."""
    connector_config = {
        "connectors": {
            "summary": {
                "type": "anthropic",
                "enabled": True,
                "capabilities": ["summary"]
            },
            "vectorizer": {
                "type": "mix_api",
                "enabled": True,
                "capabilities": ["vectorization"]
            }
        }
    }
    
    # Создаем моки с правильными возможностями
    mock_summary = Mock(spec=BaseConnector)
    mock_summary.capabilities = {ConnectorCapability.SUMMARY}
    
    mock_vectorizer = Mock(spec=BaseConnector)
    mock_vectorizer.capabilities = {ConnectorCapability.VECTORIZATION}
    
    # Настраиваем моки для классов
    mock_collector_class = Mock(return_value=mock_file_collector)
    mock_storage_class = Mock(return_value=Mock(spec=SupabaseStorage))
    
    # Устанавливаем моки в фабрику
    DocumentProcessorFactory.set_file_collector_class(mock_collector_class)
    DocumentProcessorFactory.set_storage_class(mock_storage_class)
    
    with patch('z888_ai_hub.connectors.factory.ConnectorFactory.create_connectors_for_tasks') as mock_create:
        mock_create.return_value = {
            "summary": mock_summary,
            "vectorizer": mock_vectorizer
        }
        
        processor = await DocumentProcessorFactory.create_processor(
            root_path="/test",
            connector_config=connector_config
        )
        
        assert isinstance(processor, DocumentProcessor)
        mock_create.assert_called_once()
        mock_collector_class.assert_called_once_with("/test")
        mock_storage_class.assert_called_once()

@pytest.mark.asyncio
async def test_factory_create_processor_missing_capabilities(mock_file_collector):
    """Test factory creating processor with missing capabilities."""
    connector_config = {
        "connectors": {
            "summary": {
                "type": "anthropic",
                "enabled": True,
                "capabilities": ["summary"]  # Correct capability
            },
            "vectorizer": {
                "type": "mix_api",
                "enabled": True,
                "capabilities": ["vectorization"]  # Correct capability
            }
        }
    }
    
    # Создаем моки с неправильными возможностями
    mock_summary = Mock(spec=BaseConnector)
    mock_summary.capabilities = {ConnectorCapability.VECTORIZATION}  # Wrong capability
    
    mock_vectorizer = Mock(spec=BaseConnector)
    mock_vectorizer.capabilities = {ConnectorCapability.SUMMARY}  # Wrong capability
    
    # Настраиваем моки для классов
    mock_collector_class = Mock(return_value=mock_file_collector)
    mock_storage_class = Mock(return_value=Mock(spec=SupabaseStorage))
    
    # Устанавливаем моки в фабрику
    DocumentProcessorFactory.set_file_collector_class(mock_collector_class)
    DocumentProcessorFactory.set_storage_class(mock_storage_class)
    
    with patch('z888_ai_hub.connectors.factory.ConnectorFactory.create_connector') as mock_create:
        mock_create.side_effect = [None, None]  # Возвращаем None для обоих коннекторов
        
        with pytest.raises(ValueError, match="Required connectors not found"):
            await DocumentProcessorFactory.create_processor(
                root_path="/test",
                connector_config=connector_config
            )

@pytest.mark.asyncio
async def test_factory_create_processor_invalid_config():
    """Test factory creating processor with invalid configuration."""
    connector_config = {
        "connectors": {
            "summary": {
                "enabled": True  # Missing type
            }
        }
    }
    
    with pytest.raises(ValueError, match="Missing 'type' field"):
        await DocumentProcessorFactory.create_processor(
            root_path="/test",
            connector_config=connector_config
        )

@pytest.mark.asyncio
async def test_connector_network_error_handling(self, ai_client: AIClient):
    """Тест обработки сетевых ошибок коннекторов."""
    logger.info("Testing connector network error handling")

    # Мокаем клиент Anthropic для симуляции сетевых ошибок
    with patch('anthropic.AsyncAnthropic') as mock_anthropic:
        # Симулируем ошибку сети
        mock_anthropic.return_value.messages.create.side_effect = Exception("Network error")
        
        # Проверяем обработку ошибки при генерации резюме
        with pytest.raises(Exception) as exc_info:
            await ai_client.generate_summary("Test content")
        assert "Network error" in str(exc_info.value)

        # Проверяем обработку ошибки при векторизации
        with pytest.raises(Exception) as exc_info:
            await ai_client.vectorize_text("Test content")
        assert "Network error" in str(exc_info.value)

@pytest.mark.asyncio
async def test_connector_rate_limiting(self, ai_client: AIClient):
    """Тест обработки ограничений частоты запросов."""
    logger.info("Testing connector rate limiting")

    # Мокаем клиент Anthropic для симуляции rate limiting
    with patch('anthropic.AsyncAnthropic') as mock_anthropic:
        # Симулируем rate limit error
        mock_anthropic.return_value.messages.create.side_effect = Exception("Rate limit exceeded")
        
        # Проверяем обработку rate limit
        with pytest.raises(Exception) as exc_info:
            await ai_client.generate_summary("Test content")
        assert "Rate limit exceeded" in str(exc_info.value)

@pytest.mark.asyncio
async def test_connector_timeout_handling(self, ai_client: AIClient):
    """Тест обработки таймаутов коннекторов."""
    logger.info("Testing connector timeout handling")

    # Мокаем клиент Anthropic для симуляции таймаута
    with patch('anthropic.AsyncAnthropic') as mock_anthropic:
        # Симулируем таймаут
        mock_anthropic.return_value.messages.create.side_effect = asyncio.TimeoutError()
        
        # Проверяем обработку таймаута
        with pytest.raises(asyncio.TimeoutError):
            await ai_client.generate_summary("Test content") 