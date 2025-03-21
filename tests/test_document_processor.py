import os
import json
import pytest
from z888_ai_hub.processors.document_processor import DocumentProcessor
from z888_ai_hub.client.ai_client import AIClient
from z888_ai_hub.utils.logging_utils import setup_logger
from z888_ai_hub.utils.env_loader import load_env
from unittest.mock import Mock, patch, AsyncMock
from z888_ai_hub.storage.database.models import Document, Paragraph
from datetime import datetime
from z888_ai_hub.connectors.base_connector import ConnectorCapability
from z888_ai_hub.utils.file_collector import FileInfo
from z888_ai_hub.processors.base import DocumentContent

# Настройка логгера для тестов
logger = setup_logger('TestDocumentProcessor')

# Проверка наличия API ключей
def check_api_keys():
    mistral_key = load_env("MISTRAL_API_KEY")
    anthropic_key = load_env("ANTHROPIC_API_KEY")
    
    if not mistral_key:
        logger.error("MISTRAL_API_KEY not found in environment!")
        return False
    if not anthropic_key:
        logger.error("ANTHROPIC_API_KEY not found in environment!")
        return False
    
    logger.info("All required API keys are present")
    return True

# Фикстуры
@pytest.fixture
def document_processor():
    return DocumentProcessor()

@pytest.fixture
def ai_client():
    return AIClient()

@pytest.fixture
def mock_storage():
    storage = AsyncMock()
    storage.save_document = AsyncMock(return_value="test_id")
    storage.save_embeddings = AsyncMock()
    return storage

@pytest.fixture
def mock_summary_generator():
    connector = Mock()
    connector.capabilities = {ConnectorCapability.SUMMARY}
    connector.generate_summary = AsyncMock(return_value="Test summary")
    return connector

@pytest.fixture
def mock_vectorizer():
    connector = Mock()
    connector.capabilities = {ConnectorCapability.VECTORIZATION}
    connector.vectorize = AsyncMock(return_value=[0.1, 0.2, 0.3])
    connector.vectorize_batch = AsyncMock(return_value=[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])
    return connector

@pytest.fixture
def mock_file_collector():
    collector = Mock()
    collector.collect_files = Mock(return_value=[
        FileInfo(
            file_id="test_id",
            file_name="test.pdf",
            relative_path="test.pdf",
            absolute_path="/tmp/test.pdf",
            extension=".pdf",
            size=1000,
            created_at=datetime.now(),
            modified_at=datetime.now()
        )
    ])
    return collector

@pytest.fixture
def mock_pdf_processor():
    processor = Mock()
    processor.extract_content = AsyncMock(return_value=DocumentContent(
        text="Test content",
        metadata={"page_count": 1},
        tables=[],
        images=[],
        styles={}
    ))
    return processor

@pytest.fixture
def mock_doc_processor():
    processor = Mock()
    processor.extract_content = AsyncMock(return_value=DocumentContent(
        text="Test content",
        metadata={"page_count": 1},
        tables=[],
        images=[],
        styles={}
    ))
    processor.split_text_into_paragraphs = Mock(return_value=["Paragraph 1", "Paragraph 2"])
    return processor

@pytest.fixture
def document_processor(
    mock_storage,
    mock_summary_generator,
    mock_vectorizer,
    mock_file_collector,
    mock_pdf_processor,
    mock_doc_processor
):
    return DocumentProcessor(
        storage=mock_storage,
        summary_generator=mock_summary_generator,
        vectorizer=mock_vectorizer,
        file_collector=mock_file_collector,
        pdf_processor=mock_pdf_processor,
        doc_processor=mock_doc_processor
    )

# Константы
SAMPLE_PDFS_DIR = "tests/sample_pdfs"
OUTPUT_JSON_DIR = os.path.join(SAMPLE_PDFS_DIR, "json")

def setup_output_directory():
    """Подготовка директории для выходных файлов"""
    if not os.path.exists(OUTPUT_JSON_DIR):
        os.makedirs(OUTPUT_JSON_DIR)
        logger.info(f"Created output directory: {OUTPUT_JSON_DIR}")

    # Проверяем права на запись
    test_file = os.path.join(OUTPUT_JSON_DIR, "test_write.tmp")
    try:
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
        logger.info("Write permissions OK")
    except Exception as e:
        logger.error(f"Write permission test failed: {str(e)}")
        raise

def validate_json_output(json_path: str):
    """Проверка корректности созданного JSON файла"""
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        # Проверяем структуру JSON
        assert "file_id" in data, "Missing file_id in JSON"
        assert "paragraphs" in data, "Missing paragraphs in JSON"
        assert "summary" in data, "Missing summary in JSON"
        assert len(data["paragraphs"]) > 0, "No paragraphs extracted"
    return True

@pytest.mark.asyncio
async def test_single_document_processing(document_processor):
    """Тестирует обработку одного документа."""
    file_info = FileInfo(
        file_id="test_id",
        file_name="test.pdf",
        relative_path="test.pdf",
        absolute_path="/tmp/test.pdf",
        extension=".pdf",
        size=1000,
        created_at=datetime.now(),
        modified_at=datetime.now()
    )
    
    doc = await document_processor._process_file(file_info)
    assert isinstance(doc, Document)
    assert doc.file_id == "test_id"
    assert len(doc.paragraphs) == 2

@pytest.mark.asyncio
async def test_batch_document_processing(document_processor):
    """Тестирует пакетную обработку документов."""
    stats = await document_processor.process_directory("/tmp")
    assert stats["total_files"] == 1
    assert stats["processed_files"] == 1
    assert len(stats["failed_files"]) == 0

@pytest.mark.asyncio
async def test_process_document(document_processor):
    """Тестирует полный процесс обработки документа."""
    file_info = FileInfo(
        file_id="test_id",
        file_name="test.pdf",
        relative_path="test.pdf",
        absolute_path="/tmp/test.pdf",
        extension=".pdf",
        size=1000,
        created_at=datetime.now(),
        modified_at=datetime.now()
    )
    
    doc = await document_processor._process_file(file_info)
    assert doc.content is not None
    assert doc.metadata["page_count"] == 1
    assert len(doc.paragraphs) == 2

@pytest.mark.asyncio
async def test_process_directory(document_processor):
    """Тестирует обработку директории."""
    stats = await document_processor.process_directory("/tmp")
    assert "total_files" in stats
    assert "processed_files" in stats
    assert "failed_files" in stats
    assert "file_types" in stats
    assert "start_time" in stats
    assert "end_time" in stats

@pytest.mark.asyncio
async def test_error_handling(document_processor, mock_pdf_processor):
    """Тестирует обработку ошибок."""
    mock_pdf_processor.extract_content.side_effect = Exception("Test error")
    
    stats = await document_processor.process_directory("/tmp")
    assert len(stats["failed_files"]) == 1
    assert stats["failed_files"][0]["error"] == "Test error"

@pytest.mark.asyncio
async def test_batch_processing(document_processor):
    """Тестирует пакетную обработку."""
    stats = await document_processor.process_directory("/tmp")
    assert stats["processed_files"] == 1
    assert ".pdf" in stats["file_types"]

@pytest.mark.asyncio
async def test_document_metadata(document_processor):
    """Тестирует сохранение метаданных документа."""
    file_info = FileInfo(
        file_id="test_id",
        file_name="test.pdf",
        relative_path="test.pdf",
        absolute_path="/tmp/test.pdf",
        extension=".pdf",
        size=1000,
        created_at=datetime.now(),
        modified_at=datetime.now()
    )
    
    doc = await document_processor._process_file(file_info)
    assert doc.metadata["size"] == 1000
    assert doc.metadata["extension"] == ".pdf"
    assert doc.metadata["page_count"] == 1
    assert doc.metadata["language"] == "EN"
