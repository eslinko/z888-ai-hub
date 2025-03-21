"""
Unit tests for PDFProcessor class.
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path
from z888_ai_hub.processors import PdfProcessor
from z888_ai_hub.processors.exceptions import ContentExtractionError, MetadataExtractionError, ImageExtractionError
from z888_ai_hub.connectors.mistral import MistralConnector

class TestPdfProcessorUnit:
    """Unit test cases for PDFProcessor class."""

    @pytest.fixture
    def mock_pdf_reader(self):
        """Create mock PDF reader with predefined metadata and content."""
        mock = Mock()
        mock.metadata = {
            "Title": "Test Title",
            "Author": "Test Author",
            "Subject": "Test Subject",
            "Creator": "Test Creator"
        }
        mock.pages = [Mock(extract_text=Mock(return_value="Test content"))]
        return mock

    @pytest.fixture
    def mock_mistral_connector(self):
        """Create mock MistralConnector."""
        return Mock(spec=MistralConnector)

    @pytest.fixture
    def pdf_processor(self, mock_mistral_connector):
        """Initialize PdfProcessor with mock MistralConnector."""
        return PdfProcessor(mistral_connector=mock_mistral_connector)

    def test_pdf_processor_initialization(self, pdf_processor):
        """Test PDFProcessor initialization."""
        assert pdf_processor.mistral_connector is not None
        assert isinstance(pdf_processor.mistral_connector, Mock)

    @pytest.mark.asyncio
    async def test_extract_content_with_mock(self, pdf_processor, mock_pdf_reader):
        """Test content extraction with mocked PDF reader."""
        with patch('pypdf.PdfReader', return_value=mock_pdf_reader):
            content = await pdf_processor.extract_content("test.pdf")
            assert content.text == "Test content"
            assert content.metadata["title"] == "Test Title"
            assert content.metadata["author"] == "Test Author"

    @pytest.mark.asyncio
    async def test_extract_metadata_with_mock(self, pdf_processor, mock_pdf_reader):
        """Test metadata extraction with mocked PDF reader."""
        with patch('pypdf.PdfReader', return_value=mock_pdf_reader):
            metadata = await pdf_processor.extract_metadata("test.pdf")
            assert isinstance(metadata, dict)
            assert metadata["title"] == "Test Title"
            assert metadata["author"] == "Test Author"
            assert all(isinstance(v, str) for v in metadata.values())

    @pytest.mark.asyncio
    async def test_error_handling_with_mock(self, pdf_processor):
        """Test error handling with mocked file operations."""
        with patch('pypdf.PdfReader', side_effect=Exception("Test error")):
            with pytest.raises(ContentExtractionError):
                await pdf_processor.extract_content("test.pdf")

    @pytest.mark.asyncio
    async def test_metadata_encoding_with_mock(self, pdf_processor, mock_pdf_reader):
        """Test metadata encoding handling with mocked PDF reader."""
        # Создаем мок с метаданными, содержащими специальные символы
        mock_pdf_reader.metadata = {
            "Title": "Test Title with special chars: äöü",
            "Author": "Test Author with special chars: éèê"
        }
        
        with patch('pypdf.PdfReader', return_value=mock_pdf_reader):
            metadata = await pdf_processor.extract_metadata("test.pdf")
            assert isinstance(metadata["title"], str)
            assert isinstance(metadata["author"], str)
            assert "äöü" in metadata["title"]
            assert "éèê" in metadata["author"]

    @pytest.mark.asyncio
    async def test_image_extraction_with_mock(self, pdf_processor):
        """Test image extraction with mocked PDF reader."""
        mock_page = Mock()
        mock_page.images = [{"stream": Mock(), "width": 100, "height": 100}]
        mock_pdf_reader = Mock()
        mock_pdf_reader.pages = [mock_page]
        
        with patch('pypdf.PdfReader', return_value=mock_pdf_reader):
            content = await pdf_processor.extract_content("test.pdf")
            assert isinstance(content.images, list)
            assert len(content.images) == 1
            assert all(isinstance(img, dict) for img in content.images)

    @pytest.mark.asyncio
    async def test_style_extraction_with_mock(self, pdf_processor):
        """Test style extraction with mocked PDF reader."""
        mock_page = Mock()
        mock_page.extract_text.return_value = "Test content"
        mock_pdf_reader = Mock()
        mock_pdf_reader.pages = [mock_page]
        
        with patch('pypdf.PdfReader', return_value=mock_pdf_reader):
            content = await pdf_processor.extract_content("test.pdf")
            assert isinstance(content.styles, dict)
            assert "font_size" in content.styles
            assert "font_family" in content.styles
            assert "is_bold" in content.styles
            assert "is_italic" in content.styles 