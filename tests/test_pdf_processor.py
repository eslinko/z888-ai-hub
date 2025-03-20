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

from z888_ai_hub.processors import PdfProcessor
from z888_ai_hub.processors.exceptions import ContentExtractionError
from z888_ai_hub.connectors.mistral import MistralConnector
from z888_ai_hub.utils.logging_utils import setup_logger

# Константы
SAMPLE_PDFS_DIR = "tests/sample_pdfs"
OUTPUT_JSON_DIR = "tests/sample_pdfs/json"

logger = setup_logger('TestPdfProcessor')

# Фикстуры
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

@pytest.fixture
def sample_pdf_path(temp_dir):
    """Создает путь к тестовому PDF файлу."""
    return os.path.join(temp_dir, "test.pdf")

@pytest.fixture
def mock_pdf_reader():
    """Создает мок для PDF reader."""
    reader = Mock()
    reader.pages = [Mock(extract_text=Mock(return_value="Test page content"))]
    reader.metadata = {
        "Author": "Test Author",
        "Title": "Test Document",
        "Subject": "Test Subject",
        "Creator": "Test Creator",
        "Producer": "Test Producer"
    }
    return reader

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
    assert content.metadata["page_count"] == 1, "Should have one page"
    
    # Проверяем стили
    assert content.styles, "Should have some styles"
    assert any("Helvetica" in font for font in content.styles.keys()), "Should have Helvetica font"

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
            assert content.styles, f"Styles should not be empty for {pdf_file} (non-OCR extraction)"

    # Проверяем файл 4.2 -EN - MKD Premium +DHA 132x74mm_Blister.pdf
    pdf_path = os.path.join(SAMPLE_PDFS_DIR, "4.2 -EN - MKD Premium +DHA 132x74mm_Blister.pdf")
    content = await pdf_processor.extract_content(pdf_path)
    
    # Проверяем содержимое
    assert content.text == "MKD Premium +DHA 132x74mm_Blister 240616001\n\n![img-0.jpeg](img-0.jpeg)\n", "Text should be correct"
    assert content.metadata['title'] == "MKD Premium +DHA 132x74mm_Blister 240616001", "Title should be correct"
    assert content.metadata['author'] == "", "Author should be empty"
    assert content.metadata['creator'] == "Adobe Illustrator CS6 (Windows)", "Creator should be correct"
    assert content.metadata['producer'] == "Adobe PDF library 10.01", "Producer should be correct"
    assert content.metadata['created'] == "D:20240808134807+02'00'", "Created date should be correct"
    assert content.metadata['modified'] == "D:20240821191245+02'00'", "Modified date should be correct"
    assert content.metadata['page_count'] == 1, "Page count should be one"
    assert content.metadata['file_size'] == 415261, "File size should be correct"
    assert isinstance(content.tables, list), "Tables should be a list"
    assert isinstance(content.images, list), "Images should be a list"
    assert content.styles == {}, "Styles should be empty"

@pytest.mark.asyncio
async def test_extract_content(pdf_processor, sample_pdf_path, mock_pdf_reader):
    """Тестирует извлечение контента из PDF."""
    with patch('pypdf.PdfReader', return_value=mock_pdf_reader):
        content = await pdf_processor.extract_content(sample_pdf_path)
        
        assert isinstance(content, str)
        assert "Test page content" in content
        mock_pdf_reader.pages[0].extract_text.assert_called_once()

@pytest.mark.asyncio
async def test_get_metadata(pdf_processor, sample_pdf_path, mock_pdf_reader):
    """Тестирует получение метаданных PDF."""
    with patch('pypdf.PdfReader', return_value=mock_pdf_reader):
        metadata = await pdf_processor.get_metadata(sample_pdf_path)
        
        assert isinstance(metadata, dict)
        assert metadata["author"] == "Test Author"
        assert metadata["title"] == "Test Document"
        assert metadata["subject"] == "Test Subject"
        assert metadata["creator"] == "Test Creator"
        assert metadata["producer"] == "Test Producer"

@pytest.mark.asyncio
async def test_extract_images(pdf_processor, sample_pdf_path, mock_pdf_reader):
    """Тестирует извлечение изображений из PDF."""
    # Настраиваем мок для извлечения изображений
    mock_page = Mock()
    mock_page.images = [
        {"name": "image1.jpg", "data": b"test_image_data"},
        {"name": "image2.png", "data": b"test_image_data"}
    ]
    mock_pdf_reader.pages = [mock_page]
    
    with patch('pypdf.PdfReader', return_value=mock_pdf_reader):
        images = await pdf_processor.extract_images(sample_pdf_path)
        
        assert isinstance(images, list)
        assert len(images) == 2
        assert all(isinstance(img, dict) for img in images)
        assert all("name" in img and "data" in img for img in images)

@pytest.mark.asyncio
async def test_error_handling(pdf_processor, sample_pdf_path):
    """Тестирует обработку ошибок при работе с PDF."""
    # Тест на несуществующий файл
    with pytest.raises(FileNotFoundError):
        await pdf_processor.extract_content("nonexistent.pdf")
    
    # Тест на некорректный PDF
    with patch('pypdf.PdfReader', side_effect=Exception("Invalid PDF")):
        with pytest.raises(Exception) as exc_info:
            await pdf_processor.extract_content(sample_pdf_path)
        assert "Invalid PDF" in str(exc_info.value)

@pytest.mark.asyncio
async def test_large_pdf_handling(pdf_processor, sample_pdf_path, mock_pdf_reader):
    """Тестирует обработку больших PDF файлов."""
    # Создаем много страниц для теста
    mock_pdf_reader.pages = [
        Mock(extract_text=Mock(return_value=f"Page {i} content"))
        for i in range(100)
    ]
    
    with patch('pypdf.PdfReader', return_value=mock_pdf_reader):
        content = await pdf_processor.extract_content(sample_pdf_path)
        
        assert isinstance(content, str)
        assert len(content) > 0
        assert "Page 0 content" in content
        assert "Page 99 content" in content 

@pytest.mark.asyncio
async def test_pdf_processor_error_handling(pdf_processor: PdfProcessor):
    """Тест обработки ошибок в PDF процессоре."""
    logger.info("Testing PDF processor error handling")

    # Тест на поврежденный PDF
    with pytest.raises(Exception) as exc_info:
        await pdf_processor.extract_content("corrupted.pdf")
    assert "Invalid PDF" in str(exc_info.value)

    # Тест на защищенный PDF
    with pytest.raises(Exception) as exc_info:
        await pdf_processor.extract_content("password_protected.pdf")
    assert "Password protected" in str(exc_info.value)

    # Тест на пустой PDF
    with pytest.raises(Exception) as exc_info:
        await pdf_processor.extract_content("empty.pdf")
    assert "Empty PDF" in str(exc_info.value)

@pytest.mark.asyncio
async def test_pdf_processor_memory_handling(pdf_processor: PdfProcessor):
    """Тест обработки памяти в PDF процессоре."""
    logger.info("Testing PDF processor memory handling")

    # Создаем большой PDF файл
    large_pdf = "large.pdf"
    with open(large_pdf, "wb") as f:
        f.write(b"PDF content" * 1000000)  # ~10MB

    # Проверяем обработку большого файла
    try:
        content = await pdf_processor.extract_content(large_pdf)
        assert content is not None, "Should handle large PDF"
    finally:
        # Очищаем тестовый файл
        os.remove(large_pdf)

@pytest.mark.asyncio
async def test_pdf_processor_concurrent_processing(pdf_processor: PdfProcessor):
    """Тест конкурентной обработки PDF файлов."""
    logger.info("Testing PDF processor concurrent processing")

    # Создаем несколько тестовых PDF файлов
    test_files = []
    for i in range(3):
        filename = f"test_{i}.pdf"
        with open(filename, "wb") as f:
            f.write(b"Test PDF content")
        test_files.append(filename)

    try:
        # Запускаем параллельную обработку
        tasks = [pdf_processor.extract_content(f) for f in test_files]
        results = await asyncio.gather(*tasks)
        
        # Проверяем результаты
        assert len(results) == 3, "Should process all files"
        assert all(r is not None for r in results), "All files should be processed successfully"
    finally:
        # Очищаем тестовые файлы
        for f in test_files:
            os.remove(f)

@pytest.mark.asyncio
async def test_pdf_processor_metadata_extraction(pdf_processor: PdfProcessor):
    """Тест извлечения метаданных из PDF файла."""
    logger.info("Testing PDF metadata extraction")

    # Создаем тестовый PDF с метаданными
    test_pdf = "test_metadata.pdf"
    with open(test_pdf, "wb") as f:
        f.write(b"Test PDF content")

    try:
        # Извлекаем метаданные
        metadata = await pdf_processor.extract_metadata(test_pdf)
        
        # Проверяем основные поля метаданных
        assert metadata is not None, "Metadata should not be None"
        assert "title" in metadata, "Should contain title"
        assert "author" in metadata, "Should contain author"
        assert "creation_date" in metadata, "Should contain creation date"
        assert "modification_date" in metadata, "Should contain modification date"
        
        # Проверяем типы данных
        assert isinstance(metadata["title"], str), "Title should be string"
        assert isinstance(metadata["author"], str), "Author should be string"
        assert isinstance(metadata["creation_date"], str), "Creation date should be string"
        assert isinstance(metadata["modification_date"], str), "Modification date should be string"
    finally:
        os.remove(test_pdf)

@pytest.mark.asyncio
async def test_pdf_processor_metadata_encoding(pdf_processor: PdfProcessor):
    """Тест обработки кодировок в метаданных PDF."""
    logger.info("Testing PDF metadata encoding handling")

    # Создаем тестовый PDF с Unicode метаданными
    test_pdf = "test_unicode.pdf"
    with open(test_pdf, "wb") as f:
        f.write(b"Test PDF content")

    try:
        # Извлекаем метаданные
        metadata = await pdf_processor.extract_metadata(test_pdf)
        
        # Проверяем корректность обработки Unicode
        assert metadata is not None, "Metadata should not be None"
        assert all(isinstance(v, str) for v in metadata.values()), "All metadata values should be strings"
        assert all(not any(c < 32 for c in v.encode('utf-8')) for v in metadata.values()), "No control characters in metadata"
    finally:
        os.remove(test_pdf)

@pytest.mark.asyncio
async def test_pdf_processor_image_extraction(pdf_processor: PdfProcessor):
    """Тест извлечения изображений из PDF файла."""
    logger.info("Testing PDF image extraction")

    # Создаем тестовый PDF с изображениями
    test_pdf = "test_images.pdf"
    with open(test_pdf, "wb") as f:
        f.write(b"Test PDF content")

    try:
        # Извлекаем изображения
        images = await pdf_processor.extract_images(test_pdf)
        
        # Проверяем результаты
        assert images is not None, "Images should not be None"
        assert isinstance(images, list), "Images should be a list"
        
        # Проверяем каждое изображение
        for image in images:
            assert "data" in image, "Image should contain data"
            assert "format" in image, "Image should contain format"
            assert "width" in image, "Image should contain width"
            assert "height" in image, "Image should contain height"
            
            # Проверяем типы данных
            assert isinstance(image["data"], bytes), "Image data should be bytes"
            assert isinstance(image["format"], str), "Image format should be string"
            assert isinstance(image["width"], int), "Image width should be integer"
            assert isinstance(image["height"], int), "Image height should be integer"
    finally:
        os.remove(test_pdf)

@pytest.mark.asyncio
async def test_pdf_processor_image_compression(pdf_processor: PdfProcessor):
    """Тест сжатия изображений из PDF файла."""
    logger.info("Testing PDF image compression")

    # Создаем тестовый PDF с большими изображениями
    test_pdf = "test_large_images.pdf"
    with open(test_pdf, "wb") as f:
        f.write(b"Test PDF content")

    try:
        # Извлекаем изображения с сжатием
        images = await pdf_processor.extract_images(test_pdf, compress=True)
        
        # Проверяем результаты
        assert images is not None, "Images should not be None"
        assert isinstance(images, list), "Images should be a list"
        
        # Проверяем сжатие
        for image in images:
            assert "data" in image, "Image should contain data"
            assert "compressed_size" in image, "Image should contain compressed size"
            assert image["compressed_size"] <= len(image["data"]), "Compressed size should not exceed original"
    finally:
        os.remove(test_pdf) 