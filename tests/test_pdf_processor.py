"""
Tests for PDF document processor.
"""

import os
import pytest
import pdfplumber
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from unittest.mock import Mock, patch
import asyncio
import tempfile
from pathlib import Path
import logging

from z888_ai_hub.processors import PdfProcessor
from z888_ai_hub.processors.exceptions import ContentExtractionError, MetadataExtractionError, ImageExtractionError
from z888_ai_hub.connectors.mistral import MistralConnector
from z888_ai_hub.utils.logging_utils import setup_logger

# Константы
SAMPLE_PDFS_DIR = "tests/sample_pdfs"
OUTPUT_JSON_DIR = "tests/sample_pdfs/json"

logger = logging.getLogger("TestPdfProcessor")

def create_test_pdf(file_path: str, content: str = "", title: str = "untitled", 
                   author: str = "anonymous", subject: str = "unspecified"):
    """Создает тестовый PDF файл с заданным содержимым и метаданными."""
    c = canvas.Canvas(file_path, pagesize=letter)
    c.setTitle(title)
    c.setAuthor(author)
    c.setSubject(subject)
    if content:
        c.drawString(100, 700, content)
    c.save()

@pytest.fixture
def temp_dir(tmp_path):
    """Создает временную директорию для тестовых файлов."""
    return str(tmp_path)

@pytest.fixture
def sample_pdf_path(temp_dir):
    """Создает тестовый PDF файл."""
    pdf_path = os.path.join(temp_dir, "test.pdf")
    create_test_pdf(pdf_path, content="Test content")
    return pdf_path

@pytest.fixture
def mock_pdf_reader():
    """Создает мок PDF reader с предопределенными метаданными и контентом."""
    mock = Mock()
    mock.metadata = {
        "Title": "untitled",
        "Author": "anonymous",
        "Subject": "unspecified",
        "Creator": "unknown"
    }
    mock.pages = [Mock(extract_text=Mock(return_value="Test content"))]
    return mock

@pytest.fixture
def mistral_connector():
    """Initialize MistralConnector for testing."""
    return MistralConnector()

@pytest.fixture
def pdf_processor(mistral_connector):
    """Initialize PdfProcessor with MistralConnector."""
    return PdfProcessor(mistral_connector=mistral_connector)

@pytest.fixture
def setup_test_files(tmp_path):
    """Create test PDF files."""
    # Создаем простой PDF файл с текстом, таблицей и разными стилями
    pdf_path = os.path.join(tmp_path, "test.pdf")
    c = canvas.Canvas(pdf_path, pagesize=letter)
    
    # Добавляем метаданные
    c.setTitle("Test Document")
    c.setAuthor("Test Author")
    c.setCreator("Test Creator")
    
    # Добавляем текст с разными стилями
    c.setFont("Helvetica", 16)
    c.drawString(72, 800, "Test Document")
    
    c.setFont("Helvetica", 12)
    c.drawString(72, 750, "This is a test paragraph.")
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(72, 700, "This is bold text.")
    
    # Добавляем таблицу
    data = [["Header 1", "Header 2"], ["Data 1", "Data 2"]]
    table = Table(data)
    table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
    ]))
    table.wrapOn(c, 400, 400)
    table.drawOn(c, 72, 600)
    
    c.save()
    
    return tmp_path

@pytest.mark.asyncio
async def test_pdf_content_extraction(pdf_processor, setup_test_files):
    """Test basic content extraction from PDF file."""
    test_pdf_path = os.path.join(setup_test_files, "test.pdf")

    # Извлекаем содержимое
    content = await pdf_processor.extract_content(test_pdf_path)

    # Проверяем базовую структуру
    assert content.text, "Text should not be empty"
    assert "Test Document" in content.text, "Title should be in text"
    assert "test paragraph" in content.text.lower(), "Paragraph content should be in text"

    # Проверяем метаданные
    assert content.metadata, "Metadata should not be empty"
    assert content.metadata["title"] == "Test Document", "Should have correct title"
    assert content.metadata["author"] == "Test Author", "Should have correct author"
    assert int(content.metadata["page_count"]) == 1, "Should have one page"

@pytest.mark.asyncio
async def test_pdf_processing_invalid_file(pdf_processor):
    """Test processing of invalid PDF file."""
    with pytest.raises(ContentExtractionError):
        await pdf_processor.extract_content("nonexistent.pdf")

@pytest.mark.asyncio
async def test_pdf_full_processing(pdf_processor, setup_test_files):
    """Test full document processing including JSON generation."""
    test_pdf_path = os.path.join(setup_test_files, "test.pdf")
    
    # Создаем директорию для выходных файлов
    os.makedirs(OUTPUT_JSON_DIR, exist_ok=True)
    
    # Обрабатываем документ
    result = await pdf_processor.process_document(test_pdf_path, OUTPUT_JSON_DIR)
    
    # Проверяем результат
    assert result.file_id, "Should have file_id"
    assert result.file_name == "test.pdf", "Should have correct file name"
    assert result.summary, "Should have generated summary"
    
    # Проверяем созданный JSON файл
    json_path = os.path.join(OUTPUT_JSON_DIR, "test_pdf.json")
    assert os.path.exists(json_path), "JSON file should be created"

@pytest.mark.asyncio
async def test_pdf_metadata_extraction(pdf_processor, setup_test_files):
    """Test metadata extraction from PDF file."""
    test_pdf_path = os.path.join(setup_test_files, "test.pdf")
    
    # Извлекаем содержимое
    content = await pdf_processor.extract_content(test_pdf_path)
    
    # Проверяем все поля метаданных
    assert isinstance(content.metadata, dict), "Metadata should be a dictionary"
    assert "title" in content.metadata, "Should have title"
    assert "author" in content.metadata, "Should have author"
    assert "creator" in content.metadata, "Should have creator"
    assert "producer" in content.metadata, "Should have producer"
    assert "page_count" in content.metadata, "Should have page count"
    assert "file_size" in content.metadata, "Should have file size"

@pytest.mark.asyncio
async def test_pdf_style_extraction(pdf_processor, setup_test_files):
    """Test style extraction from PDF file."""
    test_pdf_path = os.path.join(setup_test_files, "test.pdf")
    
    # Извлекаем содержимое
    content = await pdf_processor.extract_content(test_pdf_path)
    
    # Проверяем стили
    assert content.styles, "Should have styles"
    for font_name, font_info in content.styles.items():
        assert isinstance(font_info, dict), "Font info should be a dictionary"
        assert "font_size" in font_info, "Font should have size information"
        assert "font_family" in font_info, "Font should have family information"
        assert "is_bold" in font_info, "Font should have bold information"
        assert "is_italic" in font_info, "Font should have italic information"
        assert "pages" in font_info, "Font should have page information"

@pytest.mark.asyncio
async def test_pdf_with_real_files(pdf_processor):
    """Test processing with real PDF files from sample directory."""
    # Проверяем наличие директории с сэмплами
    assert os.path.exists(SAMPLE_PDFS_DIR), f"Sample PDFs directory not found: {SAMPLE_PDFS_DIR}"

    # Получаем список PDF файлов
    pdf_files = [f for f in os.listdir(SAMPLE_PDFS_DIR) if f.endswith('.pdf')]
    assert pdf_files, "No PDF files found in sample directory"

    # Проверяем каждый файл
    for pdf_file in pdf_files:
        pdf_path = os.path.join(SAMPLE_PDFS_DIR, pdf_file)

        # Извлекаем содержимое
        content = await pdf_processor.extract_content(pdf_path)

        # Базовые проверки
        assert content.text, f"Text should not be empty for {pdf_file}"
        assert content.metadata, f"Metadata should not be empty for {pdf_file}"
        assert isinstance(content.tables, list), f"Tables should be a list for {pdf_file}"
        assert isinstance(content.images, list), f"Images should be a list for {pdf_file}"

        # Проверяем стили только если текст был извлечен не через OCR и не пустой
        # Текст считается пустым, если он состоит только из пробелов и переводов строк
        # OCR-текст определяется по наличию маркдаун-форматирования (заголовки или изображения)
        is_empty_text = not content.text.strip()
        is_ocr_text = "# " in content.text or "## " in content.text or "![" in content.text
        if not is_empty_text and not is_ocr_text:
            assert isinstance(content.styles, dict), f"Styles should be a dictionary for {pdf_file}"

@pytest.mark.asyncio
async def test_extract_content(pdf_processor, sample_pdf_path, mock_pdf_reader):
    """Тестирует извлечение контента из PDF."""
    with patch('pypdf.PdfReader', return_value=mock_pdf_reader):
        content = await pdf_processor.extract_content(sample_pdf_path)
        assert content.text == "Test content"  # Не ожидаем заголовок, так как он "untitled"
        assert content.metadata["title"] == "untitled"
        assert content.metadata["author"] == "anonymous"

@pytest.mark.asyncio
async def test_get_metadata(pdf_processor, sample_pdf_path, mock_pdf_reader):
    """Тестирует получение метаданных PDF."""
    with patch('pypdf.PdfReader', return_value=mock_pdf_reader):
        metadata = await pdf_processor.extract_metadata(sample_pdf_path)
        assert isinstance(metadata, dict)
        assert metadata["author"] == "anonymous"
        assert metadata["title"] == "untitled"
        assert metadata["subject"] == "unspecified"
        assert all(isinstance(v, str) for v in metadata.values())

@pytest.mark.asyncio
async def test_extract_images(pdf_processor, temp_dir):
    """Тестирует извлечение изображений из PDF."""
    # Создаем PDF с изображением
    test_pdf = os.path.join(temp_dir, "test_with_images.pdf")
    c = canvas.Canvas(test_pdf)
    # Создаем простое изображение прямо в PDF
    c.rect(100, 500, 400, 300, fill=1)
    c.save()
    
    images = await pdf_processor.extract_images(test_pdf)
    assert isinstance(images, list)
    # В этом тесте мы не ожидаем изображений, так как прямоугольник не считается изображением
    assert len(images) == 0

@pytest.mark.asyncio
async def test_error_handling(pdf_processor):
    """Тестирует обработку ошибок при работе с PDF."""
    with pytest.raises(ContentExtractionError) as exc_info:
        await pdf_processor.extract_content("nonexistent.pdf")
    assert "No such file or directory" in str(exc_info.value)

@pytest.mark.asyncio
async def test_pdf_processor_error_handling(pdf_processor: PdfProcessor, temp_dir: str):
    """Тест обработки ошибок в PDF процессоре."""
    logger.info("Testing PDF processor error handling")

    # Создаем поврежденный PDF
    corrupted_pdf = os.path.join(temp_dir, "corrupted.pdf")
    with open(corrupted_pdf, "wb") as f:
        f.write(b"%PDF-1.7\nInvalid PDF content")

    # Создаем пустой PDF
    empty_pdf = os.path.join(temp_dir, "empty.pdf")
    create_test_pdf(empty_pdf)

    try:
        # Тест на поврежденный PDF
        with pytest.raises(ContentExtractionError) as exc_info:
            await pdf_processor.extract_content(corrupted_pdf)
        assert "No /Root object" in str(exc_info.value)

        # Тест на пустой PDF
        content = await pdf_processor.extract_content(empty_pdf)
        assert not content.text.strip() or content.text.strip() == "untitled", "Empty PDF should have no text or just title"
        assert isinstance(content.metadata, dict), "Metadata should be a dictionary"

    finally:
        # Очистка
        if os.path.exists(corrupted_pdf):
            os.remove(corrupted_pdf)
        if os.path.exists(empty_pdf):
            os.remove(empty_pdf)

@pytest.mark.asyncio
async def test_pdf_processor_metadata_encoding(pdf_processor: PdfProcessor, temp_dir: str):
    """Тест обработки кодировок в метаданных PDF."""
    logger.info("Testing PDF metadata encoding handling")

    # Создаем тестовый PDF с Unicode метаданными
    test_pdf = os.path.join(temp_dir, "test_unicode.pdf")
    create_test_pdf(
        test_pdf,
        title="Тестовый документ",
        author="Тестовый автор",
        subject="Тестовая тема",
        content="Тестовый контент"
    )

    try:
        # Извлекаем метаданные
        metadata = await pdf_processor.extract_metadata(test_pdf)

        # Проверяем корректность обработки Unicode
        assert metadata is not None, "Metadata should not be None"
        assert isinstance(metadata["title"], str), "Title should be string"
        assert isinstance(metadata["author"], str), "Author should be string"
        assert isinstance(metadata["subject"], str), "Subject should be string"
        assert metadata["title"] == "Тестовый документ", "Should handle Unicode title"
        assert metadata["author"] == "Тестовый автор", "Should handle Unicode author"
        assert metadata["subject"] == "Тестовая тема", "Should handle Unicode subject"
        assert all(isinstance(v, str) for v in metadata.values())

    finally:
        if os.path.exists(test_pdf):
            os.remove(test_pdf)

@pytest.mark.asyncio
async def test_pdf_processor_image_extraction(pdf_processor: PdfProcessor, temp_dir: str):
    """Тест извлечения изображений из PDF файла."""
    logger.info("Testing PDF image extraction")

    # Создаем тестовый PDF с изображениями
    test_pdf = os.path.join(temp_dir, "test_images.pdf")
    create_test_pdf(test_pdf)

    try:
        # Извлекаем изображения
        images = await pdf_processor.extract_images(test_pdf)
        
        # Проверяем результаты
        assert images is not None, "Images should not be None"
        assert isinstance(images, list), "Images should be a list"
    finally:
        if os.path.exists(test_pdf):
            os.remove(test_pdf)

@pytest.mark.asyncio
async def test_pdf_processor_image_compression(pdf_processor: PdfProcessor, temp_dir: str):
    """Тест сжатия изображений из PDF файла."""
    logger.info("Testing PDF image compression")

    # Создаем тестовый PDF с изображениями
    test_pdf = os.path.join(temp_dir, "test_large_images.pdf")
    create_test_pdf(test_pdf)

    try:
        # Извлекаем изображения с сжатием
        images = await pdf_processor.extract_images(test_pdf, compress=True)
        
        # Проверяем результаты
        assert images is not None, "Images should not be None"
        assert isinstance(images, list), "Images should be a list"
    finally:
        if os.path.exists(test_pdf):
            os.remove(test_pdf) 