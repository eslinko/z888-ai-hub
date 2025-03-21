"""
Integration tests for PDFProcessor class.
"""

import os
import pytest
import pdfplumber
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
import asyncio
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

class TestPdfProcessorIntegration:
    """Integration test cases for PDFProcessor class."""

    @pytest.fixture
    def temp_dir(self, tmp_path):
        """Создает временную директорию для тестовых файлов."""
        return str(tmp_path)

    @pytest.fixture
    def sample_pdf_path(self, temp_dir):
        """Создает тестовый PDF файл."""
        pdf_path = os.path.join(temp_dir, "test.pdf")
        create_test_pdf(pdf_path, content="Test content")
        return pdf_path

    @pytest.fixture
    def mistral_connector(self):
        """Initialize MistralConnector for testing."""
        return MistralConnector()

    @pytest.fixture
    def pdf_processor(self, mistral_connector):
        """Initialize PdfProcessor with MistralConnector."""
        return PdfProcessor(mistral_connector=mistral_connector)

    @pytest.fixture
    def setup_test_files(self, tmp_path):
        """Create test PDF files with various content."""
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

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_pdf_content_extraction(self, pdf_processor, setup_test_files):
        """Integration test for basic content extraction from PDF file."""
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

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_pdf_processing_invalid_file(self, pdf_processor):
        """Integration test for processing of invalid PDF file."""
        with pytest.raises(ContentExtractionError):
            await pdf_processor.extract_content("nonexistent.pdf")

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_pdf_full_processing(self, pdf_processor, setup_test_files):
        """Integration test for full document processing including JSON generation."""
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

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_pdf_metadata_extraction(self, pdf_processor, setup_test_files):
        """Integration test for metadata extraction from PDF file."""
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

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_pdf_style_extraction(self, pdf_processor, setup_test_files):
        """Integration test for style extraction from PDF file."""
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

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_pdf_with_real_files(self, pdf_processor):
        """Integration test for processing with real PDF files from sample directory."""
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
            is_empty_text = not content.text.strip()
            is_ocr_text = "# " in content.text or "## " in content.text or "![" in content.text
            if not is_empty_text and not is_ocr_text:
                assert isinstance(content.styles, dict), f"Styles should be a dictionary for {pdf_file}"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_pdf_processor_image_extraction(self, pdf_processor, temp_dir):
        """Integration test for image extraction from PDF."""
        # Создаем PDF с изображением
        test_pdf = os.path.join(temp_dir, "test_with_images.pdf")
        c = canvas.Canvas(test_pdf)
        # Создаем простое изображение прямо в PDF
        c.rect(100, 500, 400, 300, fill=1)
        c.save()

        # Извлекаем содержимое
        content = await pdf_processor.extract_content(test_pdf)
        
        # Проверяем извлечение изображений
        assert isinstance(content.images, list), "Images should be a list"
        assert len(content.images) > 0, "Should have at least one image"
        for img in content.images:
            assert isinstance(img, dict), "Each image should be a dictionary"
            assert "width" in img, "Image should have width"
            assert "height" in img, "Image should have height"
            assert "data" in img, "Image should have data"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_pdf_processor_image_compression(self, pdf_processor, temp_dir):
        """Integration test for image compression in PDF."""
        # Создаем PDF с большим изображением
        test_pdf = os.path.join(temp_dir, "test_with_large_image.pdf")
        c = canvas.Canvas(test_pdf)
        # Создаем большое изображение
        c.rect(0, 0, 1000, 1000, fill=1)
        c.save()

        # Извлекаем содержимое
        content = await pdf_processor.extract_content(test_pdf)
        
        # Проверяем сжатие изображений
        for img in content.images:
            assert img["width"] <= 1000, "Image width should not exceed maximum"
            assert img["height"] <= 1000, "Image height should not exceed maximum"
            assert len(img["data"]) < 1000 * 1000 * 4, "Image data should be compressed" 