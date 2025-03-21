"""
Integration tests for document processing pipeline.
"""

import os
import pytest
from datetime import datetime
from z888_ai_hub.processors import DocumentProcessor
from z888_ai_hub.storage.database import SupabaseStorage
from z888_ai_hub.connectors.anthropic import AnthropicConnector
from z888_ai_hub.connectors.mistral import MistralConnector
from z888_ai_hub.utils.file_collector import FileCollector
from z888_ai_hub.processors.pdf_processor import PdfProcessor
from z888_ai_hub.processors.doc_processor import DocProcessor
from z888_ai_hub.utils.logging_utils import setup_logger

logger = setup_logger('TestDocumentProcessing')

# Константы
SAMPLE_PDFS_DIR = "tests/sample_pdfs"
SAMPLE_DOCS_DIR = "tests/sample_docs"
OUTPUT_JSON_DIR = "tests/sample_pdfs/json"

@pytest.fixture(scope="session")
def storage():
    """Создает экземпляр хранилища для тестов."""
    # Используем реальное подключение к Supabase
    storage = SupabaseStorage()
    # Очищаем тестовые данные перед началом тестов
    storage.cleanup_test_data()
    yield storage
    # Очищаем тестовые данные после завершения тестов
    storage.cleanup_test_data()

@pytest.fixture(scope="session")
def summary_generator():
    """Создает экземпляр генератора резюме."""
    # Используем реальное подключение к Anthropic
    return AnthropicConnector(
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        base_url=os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
    )

@pytest.fixture(scope="session")
def vectorizer():
    """Создает экземпляр векторизатора."""
    # Используем реальное подключение к Mistral
    return MistralConnector(
        api_key=os.getenv("MISTRAL_API_KEY"),
        base_url=os.getenv("MISTRAL_BASE_URL", "https://api.mistral.ai")
    )

@pytest.fixture(scope="session")
def file_collector():
    """Создает экземпляр коллектора файлов."""
    return FileCollector(SAMPLE_PDFS_DIR)

@pytest.fixture(scope="session")
def pdf_processor():
    """Создает экземпляр PDF процессора."""
    return PdfProcessor()

@pytest.fixture(scope="session")
def doc_processor():
    """Создает экземпляр DOC процессора."""
    return DocProcessor()

@pytest.fixture(scope="session")
def document_processor(
    storage,
    summary_generator,
    vectorizer,
    file_collector,
    pdf_processor,
    doc_processor
):
    """Создает экземпляр DocumentProcessor с реальными компонентами."""
    return DocumentProcessor(
        storage=storage,
        summary_generator=summary_generator,
        vectorizer=vectorizer,
        file_collector=file_collector,
        pdf_processor=pdf_processor,
        doc_processor=doc_processor
    )

@pytest.mark.integration
@pytest.mark.asyncio
async def test_process_pdf_file(document_processor):
    """Тестирует полный процесс обработки PDF файла."""
    # Получаем список файлов
    files = document_processor.file_collector.collect_files()
    assert len(files) > 0, "Should find test files"
    
    # Обрабатываем первый PDF файл
    pdf_file = next(f for f in files if f.extension == ".pdf")
    doc = await document_processor._process_file(pdf_file)
    
    # Проверяем результат
    assert doc is not None, "Document should be processed"
    assert doc.file_id == pdf_file.file_id, "File ID should match"
    assert doc.relative_path == pdf_file.relative_path, "Path should match"
    assert doc.file_name == pdf_file.file_name, "Name should match"
    assert doc.summary is not None, "Summary should be generated"
    assert len(doc.paragraphs) > 0, "Should have paragraphs"
    assert "page_count" in doc.metadata, "Should have page count"
    
    # Проверяем сохранение в хранилище
    saved_doc = await document_processor.storage.get_document(doc.file_id)
    assert saved_doc is not None, "Document should be saved"
    assert saved_doc.file_id == doc.file_id, "Saved document should match"

@pytest.mark.integration
@pytest.mark.asyncio
async def test_process_doc_file(document_processor):
    """Тестирует полный процесс обработки DOC файла."""
    # Получаем список файлов
    files = document_processor.file_collector.collect_files()
    assert len(files) > 0, "Should find test files"
    
    # Обрабатываем первый DOC файл
    doc_file = next(f for f in files if f.extension in [".doc", ".docx"])
    doc = await document_processor._process_file(doc_file)
    
    # Проверяем результат
    assert doc is not None, "Document should be processed"
    assert doc.file_id == doc_file.file_id, "File ID should match"
    assert doc.relative_path == doc_file.relative_path, "Path should match"
    assert doc.file_name == doc_file.file_name, "Name should match"
    assert doc.summary is not None, "Summary should be generated"
    assert len(doc.paragraphs) > 0, "Should have paragraphs"
    assert "page_count" in doc.metadata, "Should have page count"
    
    # Проверяем сохранение в хранилище
    saved_doc = await document_processor.storage.get_document(doc.file_id)
    assert saved_doc is not None, "Document should be saved"
    assert saved_doc.file_id == doc.file_id, "Saved document should match"

@pytest.mark.integration
@pytest.mark.asyncio
async def test_process_multiple_files(document_processor):
    """Тестирует обработку нескольких файлов."""
    # Получаем список файлов
    files = document_processor.file_collector.collect_files()
    assert len(files) > 0, "Should find test files"
    
    # Обрабатываем первые 3 файла
    processed_files = []
    for file in files[:3]:
        doc = await document_processor._process_file(file)
        processed_files.append(doc)
    
    # Проверяем результаты
    assert len(processed_files) == 3, "Should process 3 files"
    for doc in processed_files:
        assert doc is not None, "Document should be processed"
        assert doc.summary is not None, "Summary should be generated"
        assert len(doc.paragraphs) > 0, "Should have paragraphs"
        
        # Проверяем сохранение
        saved_doc = await document_processor.storage.get_document(doc.file_id)
        assert saved_doc is not None, "Document should be saved"
        assert saved_doc.file_id == doc.file_id, "Saved document should match"

@pytest.mark.integration
@pytest.mark.asyncio
async def test_process_file_with_images(document_processor):
    """Тестирует обработку файла с изображениями."""
    # Получаем список файлов
    files = document_processor.file_collector.collect_files()
    assert len(files) > 0, "Should find test files"
    
    # Обрабатываем файл с изображениями
    file_with_images = next(f for f in files if f.extension == ".pdf")
    doc = await document_processor._process_file(file_with_images)
    
    # Проверяем результат
    assert doc is not None, "Document should be processed"
    assert "images" in doc.metadata, "Should have images metadata"
    assert len(doc.metadata["images"]) > 0, "Should have extracted images"

@pytest.mark.integration
@pytest.mark.asyncio
async def test_process_file_with_tables(document_processor):
    """Тестирует обработку файла с таблицами."""
    # Получаем список файлов
    files = document_processor.file_collector.collect_files()
    assert len(files) > 0, "Should find test files"
    
    # Обрабатываем файл с таблицами
    file_with_tables = next(f for f in files if f.extension == ".docx")
    doc = await document_processor._process_file(file_with_tables)
    
    # Проверяем результат
    assert doc is not None, "Document should be processed"
    assert "tables" in doc.metadata, "Should have tables metadata"
    assert len(doc.metadata["tables"]) > 0, "Should have extracted tables"

@pytest.mark.integration
@pytest.mark.asyncio
async def test_process_file_with_styles(document_processor):
    """Тестирует обработку файла со стилями."""
    # Получаем список файлов
    files = document_processor.file_collector.collect_files()
    assert len(files) > 0, "Should find test files"
    
    # Обрабатываем файл со стилями
    file_with_styles = next(f for f in files if f.extension == ".docx")
    doc = await document_processor._process_file(file_with_styles)
    
    # Проверяем результат
    assert doc is not None, "Document should be processed"
    assert "styles" in doc.metadata, "Should have styles metadata"
    assert "paragraphs" in doc.metadata["styles"], "Should have paragraph styles"

@pytest.mark.integration
@pytest.mark.asyncio
async def test_process_file_with_vectorization(document_processor):
    """Тестирует векторизацию документа."""
    # Получаем список файлов
    files = document_processor.file_collector.collect_files()
    assert len(files) > 0, "Should find test files"
    
    # Обрабатываем файл
    file = next(f for f in files if f.extension == ".pdf")
    doc = await document_processor._process_file(file)
    
    # Проверяем результат
    assert doc is not None, "Document should be processed"
    assert "vectors" in doc.metadata, "Should have vectors metadata"
    assert len(doc.metadata["vectors"]) > 0, "Should have generated vectors"
    assert len(doc.metadata["vectors"][0]) > 0, "Vectors should have dimensions"

@pytest.mark.integration
@pytest.mark.asyncio
async def test_process_file_with_summary(document_processor):
    """Тестирует генерацию резюме документа."""
    # Получаем список файлов
    files = document_processor.file_collector.collect_files()
    assert len(files) > 0, "Should find test files"
    
    # Обрабатываем файл
    file = next(f for f in files if f.extension == ".pdf")
    doc = await document_processor._process_file(file)
    
    # Проверяем результат
    assert doc is not None, "Document should be processed"
    assert doc.summary is not None, "Summary should be generated"
    assert len(doc.summary) > 0, "Summary should not be empty"
    assert isinstance(doc.summary, str), "Summary should be a string"

@pytest.mark.integration
@pytest.mark.asyncio
async def test_process_pdf_file_with_real_services(document_processor):
    """Тестирует полный процесс обработки PDF файла с реальными сервисами."""
    # Получаем список файлов
    files = document_processor.file_collector.collect_files()
    assert len(files) > 0, "Should find test files"
    
    # Обрабатываем первый PDF файл
    pdf_file = next(f for f in files if f.extension == ".pdf")
    doc = await document_processor._process_file(pdf_file)
    
    # Проверяем результат
    assert doc is not None, "Document should be processed"
    assert doc.file_id == pdf_file.file_id, "File ID should match"
    assert doc.relative_path == pdf_file.relative_path, "Path should match"
    assert doc.file_name == pdf_file.file_name, "Name should match"
    
    # Проверяем интеграцию с Anthropic (генерация резюме)
    assert doc.summary is not None, "Summary should be generated"
    assert len(doc.summary) > 0, "Summary should not be empty"
    assert isinstance(doc.summary, str), "Summary should be a string"
    
    # Проверяем интеграцию с Mistral (векторизация)
    assert "vectors" in doc.metadata, "Should have vectors metadata"
    assert len(doc.metadata["vectors"]) > 0, "Should have generated vectors"
    assert len(doc.metadata["vectors"][0]) > 0, "Vectors should have dimensions"
    
    # Проверяем интеграцию с Supabase (сохранение)
    saved_doc = await document_processor.storage.get_document(doc.file_id)
    assert saved_doc is not None, "Document should be saved"
    assert saved_doc.file_id == doc.file_id, "Saved document should match"
    assert saved_doc.summary == doc.summary, "Saved summary should match"
    assert saved_doc.metadata == doc.metadata, "Saved metadata should match"

@pytest.mark.integration
@pytest.mark.asyncio
async def test_process_doc_file_with_real_services(document_processor):
    """Тестирует полный процесс обработки DOC файла с реальными сервисами."""
    # Получаем список файлов
    files = document_processor.file_collector.collect_files()
    assert len(files) > 0, "Should find test files"
    
    # Обрабатываем первый DOC файл
    doc_file = next(f for f in files if f.extension in [".doc", ".docx"])
    doc = await document_processor._process_file(doc_file)
    
    # Проверяем результат
    assert doc is not None, "Document should be processed"
    assert doc.file_id == doc_file.file_id, "File ID should match"
    assert doc.relative_path == doc_file.relative_path, "Path should match"
    assert doc.file_name == doc_file.file_name, "Name should match"
    
    # Проверяем интеграцию с Anthropic (генерация резюме)
    assert doc.summary is not None, "Summary should be generated"
    assert len(doc.summary) > 0, "Summary should not be empty"
    assert isinstance(doc.summary, str), "Summary should be a string"
    
    # Проверяем интеграцию с Mistral (векторизация)
    assert "vectors" in doc.metadata, "Should have vectors metadata"
    assert len(doc.metadata["vectors"]) > 0, "Should have generated vectors"
    assert len(doc.metadata["vectors"][0]) > 0, "Vectors should have dimensions"
    
    # Проверяем интеграцию с Supabase (сохранение)
    saved_doc = await document_processor.storage.get_document(doc.file_id)
    assert saved_doc is not None, "Document should be saved"
    assert saved_doc.file_id == doc.file_id, "Saved document should match"
    assert saved_doc.summary == doc.summary, "Saved summary should match"
    assert saved_doc.metadata == doc.metadata, "Saved metadata should match"

@pytest.mark.integration
@pytest.mark.asyncio
async def test_process_multiple_files_with_real_services(document_processor):
    """Тестирует обработку нескольких файлов с реальными сервисами."""
    # Получаем список файлов
    files = document_processor.file_collector.collect_files()
    assert len(files) > 0, "Should find test files"
    
    # Обрабатываем первые 3 файла
    processed_files = []
    for file in files[:3]:
        doc = await document_processor._process_file(file)
        processed_files.append(doc)
    
    # Проверяем результаты
    assert len(processed_files) == 3, "Should process 3 files"
    for doc in processed_files:
        # Проверяем интеграцию с Anthropic
        assert doc.summary is not None, "Summary should be generated"
        assert len(doc.summary) > 0, "Summary should not be empty"
        
        # Проверяем интеграцию с Mistral
        assert "vectors" in doc.metadata, "Should have vectors metadata"
        assert len(doc.metadata["vectors"]) > 0, "Should have generated vectors"
        
        # Проверяем интеграцию с Supabase
        saved_doc = await document_processor.storage.get_document(doc.file_id)
        assert saved_doc is not None, "Document should be saved"
        assert saved_doc.file_id == doc.file_id, "Saved document should match"
        assert saved_doc.summary == doc.summary, "Saved summary should match"
        assert saved_doc.metadata == doc.metadata, "Saved metadata should match"

@pytest.mark.integration
@pytest.mark.asyncio
async def test_process_file_with_real_vectorization(document_processor):
    """Тестирует реальную векторизацию документа."""
    # Получаем список файлов
    files = document_processor.file_collector.collect_files()
    assert len(files) > 0, "Should find test files"
    
    # Обрабатываем файл
    file = next(f for f in files if f.extension == ".pdf")
    doc = await document_processor._process_file(file)
    
    # Проверяем результат векторизации
    assert "vectors" in doc.metadata, "Should have vectors metadata"
    assert len(doc.metadata["vectors"]) > 0, "Should have generated vectors"
    assert len(doc.metadata["vectors"][0]) > 0, "Vectors should have dimensions"
    
    # Проверяем сохранение векторов в Supabase
    saved_doc = await document_processor.storage.get_document(doc.file_id)
    assert saved_doc is not None, "Document should be saved"
    assert "vectors" in saved_doc.metadata, "Saved document should have vectors"
    assert saved_doc.metadata["vectors"] == doc.metadata["vectors"], "Saved vectors should match"

@pytest.mark.integration
@pytest.mark.asyncio
async def test_process_file_with_real_summary(document_processor):
    """Тестирует реальную генерацию резюме документа."""
    # Получаем список файлов
    files = document_processor.file_collector.collect_files()
    assert len(files) > 0, "Should find test files"
    
    # Обрабатываем файл
    file = next(f for f in files if f.extension == ".pdf")
    doc = await document_processor._process_file(file)
    
    # Проверяем результат генерации резюме
    assert doc.summary is not None, "Summary should be generated"
    assert len(doc.summary) > 0, "Summary should not be empty"
    assert isinstance(doc.summary, str), "Summary should be a string"
    
    # Проверяем сохранение резюме в Supabase
    saved_doc = await document_processor.storage.get_document(doc.file_id)
    assert saved_doc is not None, "Document should be saved"
    assert saved_doc.summary == doc.summary, "Saved summary should match"

@pytest.mark.integration
@pytest.mark.asyncio
async def test_process_file_with_real_storage_operations(document_processor):
    """Тестирует реальные операции с хранилищем."""
    # Получаем список файлов
    files = document_processor.file_collector.collect_files()
    assert len(files) > 0, "Should find test files"
    
    # Обрабатываем файл
    file = next(f for f in files if f.extension == ".pdf")
    doc = await document_processor._process_file(file)
    
    # Проверяем сохранение
    saved_doc = await document_processor.storage.get_document(doc.file_id)
    assert saved_doc is not None, "Document should be saved"
    assert saved_doc.file_id == doc.file_id, "Saved document should match"
    
    # Проверяем обновление
    doc.summary = "Updated summary"
    await document_processor.storage.update_document(doc)
    updated_doc = await document_processor.storage.get_document(doc.file_id)
    assert updated_doc.summary == "Updated summary", "Document should be updated"
    
    # Проверяем удаление
    await document_processor.storage.delete_document(doc.file_id)
    deleted_doc = await document_processor.storage.get_document(doc.file_id)
    assert deleted_doc is None, "Document should be deleted" 