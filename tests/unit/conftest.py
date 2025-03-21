"""
Base configuration for unit tests.
"""

import os
import pytest
from unittest.mock import Mock, patch
from z888_ai_hub.utils.logging_utils import setup_logger

logger = setup_logger('UnitTests')

@pytest.fixture(scope="session", autouse=True)
def setup_unit_test_environment():
    """Настраивает окружение для unit-тестов."""
    # Создаем временную директорию для тестов
    test_dir = "tests/temp/unit"
    os.makedirs(test_dir, exist_ok=True)
    
    yield
    
    # Очищаем временную директорию после тестов
    if os.path.exists(test_dir):
        for file in os.listdir(test_dir):
            os.remove(os.path.join(test_dir, file))
        os.rmdir(test_dir)

@pytest.fixture
def mock_storage():
    """Создает мок для хранилища."""
    storage = Mock()
    storage.get_document = Mock()
    storage.save_document = Mock()
    storage.update_document = Mock()
    storage.delete_document = Mock()
    return storage

@pytest.fixture
def mock_anthropic_connector():
    """Создает мок для Anthropic коннектора."""
    connector = Mock()
    connector.generate_summary = Mock()
    connector.vectorize_text = Mock()
    return connector

@pytest.fixture
def mock_mistral_connector():
    """Создает мок для Mistral коннектора."""
    connector = Mock()
    connector.generate_summary = Mock()
    connector.vectorize_text = Mock()
    return connector

@pytest.fixture
def mock_file_collector():
    """Создает мок для коллектора файлов."""
    collector = Mock()
    collector.collect_files = Mock()
    return collector

@pytest.fixture
def mock_pdf_processor():
    """Создает мок для PDF процессора."""
    processor = Mock()
    processor.extract_content = Mock()
    processor.extract_metadata = Mock()
    processor.extract_images = Mock()
    return processor

@pytest.fixture
def mock_doc_processor():
    """Создает мок для DOC процессора."""
    processor = Mock()
    processor.extract_content = Mock()
    processor.extract_metadata = Mock()
    processor.extract_images = Mock()
    return processor

@pytest.fixture
def sample_document():
    """Создает тестовый документ."""
    return {
        "file_id": "test_file_id",
        "relative_path": "test/path/file.pdf",
        "file_name": "file.pdf",
        "summary": "Test summary",
        "metadata": {
            "page_count": 1,
            "author": "Test Author",
            "created_at": "2024-03-21T00:00:00"
        }
    }

@pytest.fixture
def sample_paragraphs():
    """Создает тестовые параграфы."""
    return [
        {
            "id": "p1",
            "content": "Test paragraph 1",
            "page_number": 1,
            "position": 0
        },
        {
            "id": "p2",
            "content": "Test paragraph 2",
            "page_number": 1,
            "position": 1
        }
    ] 