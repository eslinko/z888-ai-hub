import os
import pytest
import tempfile
from typing import Generator
from unittest.mock import Mock
from z888_ai_hub.connectors.base_connector import BaseConnector
from z888_ai_hub.processors.document_processor import DocumentProcessor
from z888_ai_hub.storage.database.models import Document
from z888_ai_hub.utils.logging_utils import setup_logger

logger = setup_logger('TestFixtures')

@pytest.fixture
def temp_dir() -> Generator[str, None, None]:
    """Создает временную директорию для тестов."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield tmp_dir

@pytest.fixture
def mock_connector() -> BaseConnector:
    """Создает мок для AI коннектора."""
    connector = Mock(spec=BaseConnector)
    connector.generate_summary.return_value = "Test summary"
    connector.vectorize.return_value = [0.1] * 1536
    connector.vectorize_batch.return_value = [[0.1] * 1536]
    return connector

@pytest.fixture
def mock_document() -> Document:
    """Создает тестовый документ."""
    return Document(
        file_id="test_id",
        relative_path="test.pdf",
        file_name="test.pdf",
        summary="Test summary",
        metadata={},
        paragraphs=[]
    )

@pytest.fixture
def sample_config() -> dict:
    """Возвращает тестовую конфигурацию."""
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

@pytest.fixture
def document_processor(mock_connector, temp_dir) -> DocumentProcessor:
    """Создает процессор документов с моками."""
    processor = DocumentProcessor(
        storage=Mock(),
        summary_generator=mock_connector,
        vectorizer=mock_connector,
        file_collector=Mock(),
        pdf_processor=Mock(),
        doc_processor=Mock()
    )
    return processor
