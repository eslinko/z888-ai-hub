"""
Integration tests for document processing.
"""

import os
import pytest
from datetime import datetime
from z888_ai_hub.processors.document_processor import DocumentProcessor
from z888_ai_hub.processors.pdf_processor import PdfProcessor
from z888_ai_hub.processors.doc_processor import DocProcessor
from z888_ai_hub.storage.supabase import SupabaseStorage
from z888_ai_hub.connectors.anthropic import AnthropicConnector
from z888_ai_hub.connectors.mistral import MistralConnector
from z888_ai_hub.utils.logging_utils import setup_logger

logger = setup_logger('TestDocumentProcessingIntegration')

@pytest.fixture(scope="session")
def storage():
    """Создает экземпляр Supabase хранилища для тестов."""
    return SupabaseStorage(
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_key=os.getenv("SUPABASE_KEY")
    )

@pytest.fixture(scope="session")
def summary_generator():
    """Создает экземпляр Anthropic коннектора для генерации резюме."""
    return AnthropicConnector(
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        base_url=os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
    )

@pytest.fixture(scope="session")
def vectorizer():
    """Создает экземпляр Mistral коннектора для векторизации."""
    return MistralConnector(
        api_key=os.getenv("MISTRAL_API_KEY"),
        base_url=os.getenv("MISTRAL_BASE_URL", "https://api.mistral.ai")
    )

@pytest.fixture(scope="session")
def pdf_processor():
    """Создает экземпляр PDF процессора."""
    return PdfProcessor()

@pytest.fixture(scope="session")
def doc_processor():
    """Создает экземпляр DOC процессора."""
    return DocProcessor()

@pytest.fixture(scope="session")
def document_processor(storage, summary_generator, vectorizer, pdf_processor, doc_processor):
    """Создает экземпляр DocumentProcessor для тестов."""
    return DocumentProcessor(
        storage=storage,
        summary_generator=summary_generator,
        vectorizer=vectorizer,
        pdf_processor=pdf_processor,
        doc_processor=doc_processor
    )

@pytest.fixture(scope="function")
async def cleanup_test_data(storage):
    """Очищает тестовые данные до и после каждого теста."""
    # Очищаем тестовые данные перед тестом
    await storage.delete_document("test_document_id")
    await storage.delete_document("test_document_id_2")
    
    yield
    
    # Очищаем тестовые данные после теста
    await storage.delete_document("test_document_id")
    await storage.delete_document("test_document_id_2")

@pytest.mark.integration
@pytest.mark.asyncio
async def test_process_pdf_file(document_processor, cleanup_test_data):
    """Тестирует обработку PDF файла."""
    test_file_path = "tests/sample_files/pdfs/test.pdf"
    
    # Обрабатываем файл
    document = await document_processor.process_file(test_file_path)
    
    assert document is not None
    assert document["file_id"] is not None
    assert document["relative_path"] == test_file_path
    assert document["file_name"] == "test.pdf"
    assert document["summary"] is not None
    assert len(document["paragraphs"]) > 0
    assert document["metadata"]["author"] is not None
    assert document["metadata"]["created_at"] is not None
    assert document["metadata"]["updated_at"] is not None

@pytest.mark.integration
@pytest.mark.asyncio
async def test_process_doc_file(document_processor, cleanup_test_data):
    """Тестирует обработку DOC файла."""
    test_file_path = "tests/sample_files/docs/test.docx"
    
    # Обрабатываем файл
    document = await document_processor.process_file(test_file_path)
    
    assert document is not None
    assert document["file_id"] is not None
    assert document["relative_path"] == test_file_path
    assert document["file_name"] == "test.docx"
    assert document["summary"] is not None
    assert len(document["paragraphs"]) > 0
    assert document["metadata"]["author"] is not None
    assert document["metadata"]["created_at"] is not None
    assert document["metadata"]["updated_at"] is not None

@pytest.mark.integration
@pytest.mark.asyncio
async def test_process_multiple_files(document_processor, cleanup_test_data):
    """Тестирует обработку нескольких файлов."""
    test_files = [
        "tests/sample_files/pdfs/test1.pdf",
        "tests/sample_files/pdfs/test2.pdf",
        "tests/sample_files/docs/test1.docx"
    ]
    
    # Обрабатываем файлы
    documents = []
    for file_path in test_files:
        document = await document_processor.process_file(file_path)
        documents.append(document)
    
    assert len(documents) == 3
    for document in documents:
        assert document is not None
        assert document["file_id"] is not None
        assert document["summary"] is not None
        assert len(document["paragraphs"]) > 0

@pytest.mark.integration
@pytest.mark.asyncio
async def test_process_file_with_images(document_processor, cleanup_test_data):
    """Тестирует обработку файла с изображениями."""
    test_file_path = "tests/sample_files/docs/test_with_images.docx"
    
    # Обрабатываем файл
    document = await document_processor.process_file(test_file_path)
    
    assert document is not None
    assert "images" in document["metadata"]
    assert len(document["metadata"]["images"]) > 0
    for image in document["metadata"]["images"]:
        assert "id" in image
        assert "path" in image
        assert "type" in image

@pytest.mark.integration
@pytest.mark.asyncio
async def test_process_file_with_tables(document_processor, cleanup_test_data):
    """Тестирует обработку файла с таблицами."""
    test_file_path = "tests/sample_files/docs/test_with_tables.docx"
    
    # Обрабатываем файл
    document = await document_processor.process_file(test_file_path)
    
    assert document is not None
    assert "tables" in document["metadata"]
    assert len(document["metadata"]["tables"]) > 0
    for table in document["metadata"]["tables"]:
        assert "id" in table
        assert "rows" in table
        assert "columns" in table

@pytest.mark.integration
@pytest.mark.asyncio
async def test_process_file_with_styles(document_processor, cleanup_test_data):
    """Тестирует обработку файла со стилями."""
    test_file_path = "tests/sample_files/docs/test_with_styles.docx"
    
    # Обрабатываем файл
    document = await document_processor.process_file(test_file_path)
    
    assert document is not None
    assert "styles" in document["metadata"]
    assert len(document["metadata"]["styles"]) > 0
    for style in document["metadata"]["styles"]:
        assert "name" in style
        assert "type" in style
        assert "properties" in style

@pytest.mark.integration
@pytest.mark.asyncio
async def test_process_file_with_vectorization(document_processor, cleanup_test_data):
    """Тестирует векторизацию документа."""
    test_file_path = "tests/sample_files/pdfs/test.pdf"
    
    # Обрабатываем файл
    document = await document_processor.process_file(test_file_path)
    
    assert document is not None
    assert "vectors" in document["metadata"]
    assert len(document["metadata"]["vectors"]) > 0
    for vector in document["metadata"]["vectors"]:
        assert "id" in vector
        assert "content" in vector
        assert "embedding" in vector
        assert len(vector["embedding"]) > 0

@pytest.mark.integration
@pytest.mark.asyncio
async def test_process_file_with_summary(document_processor, cleanup_test_data):
    """Тестирует генерацию резюме документа."""
    test_file_path = "tests/sample_files/pdfs/test.pdf"
    
    # Обрабатываем файл
    document = await document_processor.process_file(test_file_path)
    
    assert document is not None
    assert document["summary"] is not None
    assert isinstance(document["summary"], str)
    assert len(document["summary"]) > 0
    assert len(document["summary"]) < len(" ".join(p["content"] for p in document["paragraphs"])) 