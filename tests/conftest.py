"""
Common configuration for all tests.
"""

import os
import pytest
import tempfile
from typing import Generator
from unittest.mock import Mock
from z888_ai_hub.connectors.base_connector import BaseConnector
from z888_ai_hub.processors.document_processor import DocumentProcessor
from z888_ai_hub.storage.database.models import Document
from z888_ai_hub.utils.logging_utils import setup_logger
from datetime import datetime

logger = setup_logger('Tests')

def pytest_configure(config):
    """Настраивает pytest для всех тестов."""
    # Добавляем маркеры
    config.addinivalue_line(
        "markers",
        "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers",
        "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers",
        "asyncio: mark test as an async test"
    )

@pytest.fixture(scope="session")
def test_root():
    """Возвращает корневую директорию тестов."""
    return os.path.dirname(os.path.abspath(__file__))

@pytest.fixture(scope="session")
def sample_files_dir(test_root):
    """Возвращает путь к директории с тестовыми файлами."""
    return os.path.join(test_root, "sample_files")

@pytest.fixture(scope="session")
def temp_dir(test_root):
    """Возвращает путь к временной директории для тестов."""
    return os.path.join(test_root, "temp")

@pytest.fixture(scope="session")
def test_start_time():
    """Возвращает время начала тестов."""
    return datetime.now()

@pytest.fixture(scope="session")
def test_id():
    """Генерирует уникальный идентификатор для тестов."""
    return f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

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
