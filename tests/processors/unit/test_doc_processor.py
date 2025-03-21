"""
Unit tests for DOC/DOCX document processor.
"""

import os
import pytest
from unittest.mock import Mock, patch
from docx import Document
from z888_ai_hub.processors import DocProcessor
from z888_ai_hub.processors.exceptions import (
    ContentExtractionError,
    MetadataExtractionError,
    TableExtractionError,
    ImageExtractionError,
    StyleExtractionError
)
from z888_ai_hub.processors.base import DocumentContent

# Константы
SAMPLE_DOCS_DIR = "tests/sample_docs"
OUTPUT_JSON_DIR = "tests/sample_docs/json"

@pytest.fixture
def doc_processor():
    """Создает экземпляр DocProcessor для тестирования."""
    return DocProcessor()

@pytest.fixture
def sample_doc_path():
    """Возвращает путь к тестовому DOC файлу."""
    return os.path.join(SAMPLE_DOCS_DIR, "test.docx")

@pytest.fixture
def mock_docx_document():
    """Создает мок для docx.Document."""
    mock = Mock(spec=Document)
    mock.paragraphs = [
        Mock(text="Test paragraph 1"),
        Mock(text="Test paragraph 2")
    ]
    mock.tables = [
        Mock(rows=[
            Mock(cells=[Mock(text="Cell 1"), Mock(text="Cell 2")]),
            Mock(cells=[Mock(text="Cell 3"), Mock(text="Cell 4")])
        ])
    ]
    mock.core_properties = Mock(
        author="Test Author",
        created=Mock(isoformat=lambda: "2024-03-17T12:00:00"),
        modified=Mock(isoformat=lambda: "2024-03-17T12:00:00")
    )
    return mock

@pytest.mark.asyncio
async def test_extract_content(doc_processor, mock_docx_document):
    """Тестирует извлечение контента из DOC файла."""
    with patch('docx.Document', return_value=mock_docx_document):
        content = await doc_processor.extract_content("test.docx")
        
        assert isinstance(content, DocumentContent)
        assert content.text == "Test paragraph 1\nTest paragraph 2"
        assert len(content.tables) == 1
        assert len(content.tables[0]) == 2
        assert content.metadata["author"] == "Test Author"

@pytest.mark.asyncio
async def test_extract_metadata(doc_processor, mock_docx_document):
    """Тестирует извлечение метаданных из DOC файла."""
    with patch('docx.Document', return_value=mock_docx_document):
        content = await doc_processor.extract_content("test.docx")
        
        assert content.metadata["author"] == "Test Author"
        assert content.metadata["created_at"] == "2024-03-17T12:00:00"
        assert content.metadata["modified_at"] == "2024-03-17T12:00:00"

@pytest.mark.asyncio
async def test_extract_tables(doc_processor, mock_docx_document):
    """Тестирует извлечение таблиц из DOC файла."""
    with patch('docx.Document', return_value=mock_docx_document):
        content = await doc_processor.extract_content("test.docx")
        
        assert len(content.tables) == 1
        assert len(content.tables[0]) == 2
        assert content.tables[0][0] == ["Cell 1", "Cell 2"]
        assert content.tables[0][1] == ["Cell 3", "Cell 4"]

@pytest.mark.asyncio
async def test_extract_styles(doc_processor, mock_docx_document):
    """Тестирует извлечение стилей из DOC файла."""
    mock_docx_document.paragraphs[0].style = Mock(name="Heading 1")
    mock_docx_document.paragraphs[1].style = Mock(name="Normal")
    
    with patch('docx.Document', return_value=mock_docx_document):
        content = await doc_processor.extract_content("test.docx")
        
        assert "styles" in content.metadata
        assert content.metadata["styles"]["paragraphs"][0] == "Heading 1"
        assert content.metadata["styles"]["paragraphs"][1] == "Normal"

@pytest.mark.asyncio
async def test_extract_content_invalid_file(doc_processor):
    """Тестирует обработку несуществующего файла."""
    with pytest.raises(ContentExtractionError):
        await doc_processor.extract_content("nonexistent.doc")

@pytest.mark.asyncio
async def test_extract_content_empty_file(doc_processor, mock_docx_document):
    """Тестирует обработку пустого файла."""
    mock_docx_document.paragraphs = []
    mock_docx_document.tables = []
    
    with patch('docx.Document', return_value=mock_docx_document):
        content = await doc_processor.extract_content("empty.docx")
        
        assert isinstance(content, DocumentContent)
        assert content.text == ""
        assert len(content.tables) == 0
        assert content.metadata == {}

@pytest.mark.asyncio
async def test_extract_content_with_images(doc_processor, mock_docx_document):
    """Тестирует извлечение изображений из DOC файла."""
    mock_image = Mock()
    mock_image._inline.graphic.graphicData.pic.blipFill.blip.embed = "rId1"
    mock_docx_document.inline_shapes = [mock_image]
    
    with patch('docx.Document', return_value=mock_docx_document):
        content = await doc_processor.extract_content("test.docx")
        
        assert len(content.images) == 1
        assert content.images[0]["id"] == "rId1"

@pytest.mark.asyncio
async def test_extract_content_with_complex_styles(doc_processor, mock_docx_document):
    """Тестирует извлечение сложных стилей из DOC файла."""
    mock_docx_document.paragraphs[0].style = Mock(
        name="Heading 1",
        font=Mock(name="Arial", size=16, bold=True),
        paragraph_format=Mock(alignment=1, line_spacing=1.5)
    )
    
    with patch('docx.Document', return_value=mock_docx_document):
        content = await doc_processor.extract_content("test.docx")
        
        assert "styles" in content.metadata
        style = content.metadata["styles"]["paragraphs"][0]
        assert style["name"] == "Heading 1"
        assert style["font"]["name"] == "Arial"
        assert style["font"]["size"] == 16
        assert style["font"]["bold"] is True
        assert style["paragraph_format"]["alignment"] == 1
        assert style["paragraph_format"]["line_spacing"] == 1.5 