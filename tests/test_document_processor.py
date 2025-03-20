import os
import json
import pytest
from z888_ai_hub.processors.document_processor import DocumentProcessor
from z888_ai_hub.client.ai_client import AIClient
from z888_ai_hub.utils.logging_utils import setup_logger
from z888_ai_hub.utils.env_loader import load_env
from unittest.mock import Mock, patch
from z888_ai_hub.storage.database.models import Document, Paragraph
from datetime import datetime

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
async def test_single_document_processing(document_processor, ai_client):
    """
    Детальное тестирование обработки одного PDF документа
    """
    # Проверяем API ключи
    assert check_api_keys(), "Missing required API keys!"
    
    # Проверяем существование директории с сэмплами
    assert os.path.exists(SAMPLE_PDFS_DIR), f"Sample PDFs directory not found: {SAMPLE_PDFS_DIR}"
    
    # Получаем первый PDF файл для тестирования
    pdf_files = [f for f in os.listdir(SAMPLE_PDFS_DIR) if f.endswith(".pdf")]
    assert len(pdf_files) > 0, f"No PDF files found in {SAMPLE_PDFS_DIR}"
    
    test_file = pdf_files[0]
    logger.info(f"Testing single file processing with: {test_file}")
    
    # Подготовка директории для выходных файлов
    setup_output_directory()
    
    # Обработка тестового файла
    pdf_path = os.path.join(SAMPLE_PDFS_DIR, test_file)
    json_path = os.path.join(OUTPUT_JSON_DIR, test_file.replace(".pdf", ".json"))

    # Проверяем доступ к PDF файлу
    assert os.access(pdf_path, os.R_OK), f"Cannot read PDF file: {pdf_path}"
    
    # Извлекаем текст
    logger.info("Starting text extraction...")
    extracted_text = await ai_client.extract_text_from_image(pdf_path)
    
    # Проверяем качество извлеченного текста
    assert isinstance(extracted_text, str), f"OCR output must be a string"
    assert len(extracted_text) > 0, f"OCR output should not be empty"
    
    logger.debug(f"Successfully extracted text, length: {len(extracted_text)} characters")

    # Запускаем обработку документа
    await document_processor.process_document(pdf_path, extracted_text, OUTPUT_JSON_DIR)

    # Проверяем результаты
    assert os.path.exists(json_path), f"JSON file was not created!"
    assert validate_json_output(json_path), "JSON validation failed"
    
    logger.info(f"✅ Successfully processed single document test")

@pytest.mark.asyncio
async def test_batch_document_processing(document_processor, ai_client):
    """
    Тестирование массовой обработки всех PDF файлов в директории
    """
    # Проверяем API ключи
    assert check_api_keys(), "Missing required API keys!"
    
    # Проверяем существование директории с сэмплами
    assert os.path.exists(SAMPLE_PDFS_DIR), f"Sample PDFs directory not found: {SAMPLE_PDFS_DIR}"
    
    # Получаем список всех PDF файлов
    pdf_files = [f for f in os.listdir(SAMPLE_PDFS_DIR) if f.endswith(".pdf")]
    assert len(pdf_files) > 0, f"No PDF files found in {SAMPLE_PDFS_DIR}"
    
    logger.info(f"Found {len(pdf_files)} PDF files to process")
    
    # Подготовка директории для выходных файлов
    setup_output_directory()

    processed_files = []
    failed_files = []

    # Обрабатываем каждый PDF файл
    for pdf_file in pdf_files:
        try:
            logger.info(f"Processing file: {pdf_file}")
            pdf_path = os.path.join(SAMPLE_PDFS_DIR, pdf_file)
            json_path = os.path.join(OUTPUT_JSON_DIR, pdf_file.replace(".pdf", ".json"))

            # Проверяем доступ к PDF файлу
            assert os.access(pdf_path, os.R_OK), f"Cannot read PDF file: {pdf_path}"
            
            # Извлекаем текст
            extracted_text = await ai_client.extract_text_from_image(pdf_path)
            assert len(extracted_text) > 0, f"OCR output should not be empty for {pdf_file}"
            
            # Запускаем обработку документа
            await document_processor.process_document(pdf_path, extracted_text, OUTPUT_JSON_DIR)

            # Проверяем результаты
            assert os.path.exists(json_path), f"JSON file was not created for {pdf_file}!"
            assert validate_json_output(json_path), f"JSON validation failed for {pdf_file}"
                
            processed_files.append(pdf_file)
            logger.info(f"✅ Successfully processed {pdf_file}")

        except Exception as e:
            logger.error(f"❌ Failed to process {pdf_file}: {str(e)}", exc_info=True)
            failed_files.append((pdf_file, str(e)))
            continue

    # Выводим итоговую статистику
    logger.info(f"\nBatch processing completed!")
    logger.info(f"Successfully processed: {len(processed_files)} files")
    
    if failed_files:
        logger.error(f"Failed to process {len(failed_files)} files:")
        for failed_file, error in failed_files:
            logger.error(f"- {failed_file}: {error}")
        raise AssertionError(f"Some files failed to process: {', '.join(f[0] for f in failed_files)}")
    
    logger.info("Batch test completed successfully!")

@pytest.mark.asyncio
async def test_process_document(document_processor, mock_connector, temp_dir, mock_document):
    """Тестирует обработку одного документа."""
    # Подготовка тестовых данных
    test_text = "This is a test document content."
    test_file = os.path.join(temp_dir, "test.pdf")
    
    # Настройка моков
    document_processor.pdf_processor.extract_content.return_value = test_text
    document_processor.storage.save_document.return_value = mock_document
    
    # Вызов тестируемого метода
    result = await document_processor.process_document(test_file)
    
    # Проверки
    assert isinstance(result, Document)
    assert result.summary == "Test summary"
    assert len(result.paragraphs) >= 0
    
    # Проверка вызовов моков
    document_processor.pdf_processor.extract_content.assert_called_once_with(test_file)
    mock_connector.generate_summary.assert_called_once()
    document_processor.storage.save_document.assert_called_once()

@pytest.mark.asyncio
async def test_process_directory(document_processor, mock_connector, temp_dir):
    """Тестирует обработку директории с документами."""
    # Подготовка тестовых файлов
    test_files = [
        os.path.join(temp_dir, "test1.pdf"),
        os.path.join(temp_dir, "test2.pdf"),
        os.path.join(temp_dir, "test3.txt")
    ]
    
    # Настройка моков
    document_processor.file_collector.collect_files.return_value = [
        Mock(absolute_path=f, relative_path=os.path.basename(f))
        for f in test_files
    ]
    
    # Вызов тестируемого метода
    stats = await document_processor.process_directory(temp_dir)
    
    # Проверки
    assert isinstance(stats, dict)
    assert stats["total_files"] == len(test_files)
    assert stats["processed_files"] >= 0
    assert "failed_files" in stats
    
    # Проверка вызовов моков
    document_processor.file_collector.collect_files.assert_called_once()

@pytest.mark.asyncio
async def test_error_handling(document_processor, mock_connector, temp_dir):
    """Тестирует обработку ошибок."""
    # Подготовка тестового файла
    test_file = os.path.join(temp_dir, "test.pdf")
    
    # Настройка мока для генерации ошибки
    document_processor.pdf_processor.extract_content.side_effect = Exception("Test error")
    
    # Вызов тестируемого метода и проверка обработки ошибки
    with pytest.raises(Exception) as exc_info:
        await document_processor.process_document(test_file)
    
    assert "Test error" in str(exc_info.value)

@pytest.mark.asyncio
async def test_batch_processing(document_processor, mock_connector, temp_dir):
    """Тестирует пакетную обработку документов."""
    # Подготовка тестовых файлов
    test_files = [
        os.path.join(temp_dir, f"test{i}.pdf")
        for i in range(5)
    ]
    
    # Настройка моков
    document_processor.file_collector.collect_files.return_value = [
        Mock(absolute_path=f, relative_path=os.path.basename(f))
        for f in test_files
    ]
    
    # Вызов тестируемого метода
    stats = await document_processor.process_directory(temp_dir, batch_size=2)
    
    # Проверки
    assert isinstance(stats, dict)
    assert stats["total_files"] == len(test_files)
    assert "batches_processed" in stats
    
    # Проверка вызовов моков
    document_processor.file_collector.collect_files.assert_called_once()

@pytest.mark.asyncio
async def test_document_metadata(document_processor, mock_connector, temp_dir):
    """Тестирует сохранение метаданных документа."""
    # Подготовка тестового файла
    test_file = os.path.join(temp_dir, "test.pdf")
    test_text = "Test content"
    
    # Настройка моков
    document_processor.pdf_processor.extract_content.return_value = test_text
    document_processor.pdf_processor.get_metadata.return_value = {
        "pages": 1,
        "author": "Test Author",
        "created": datetime.now().isoformat()
    }
    
    # Вызов тестируемого метода
    result = await document_processor.process_document(test_file)
    
    # Проверки
    assert isinstance(result, Document)
    assert "metadata" in result.__dict__
    assert result.metadata.get("pages") == 1
    assert result.metadata.get("author") == "Test Author"
    
    # Проверка вызовов моков
    document_processor.pdf_processor.get_metadata.assert_called_once_with(test_file)
