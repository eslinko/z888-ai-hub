"""
Unit tests for main document processor.
"""

import os
from datetime import datetime
import pytest
from unittest.mock import Mock, AsyncMock, patch
from z888_ai_hub.processors import DocumentProcessor
from z888_ai_hub.utils.file_collector import FileInfo
from z888_ai_hub.storage.database.models import Document, Paragraph
from z888_ai_hub.connectors.base_connector import ConnectorCapability
from z888_ai_hub.processors.base import DocumentContent

@pytest.fixture
def mock_storage():
    """Создает мок для хранилища."""
    storage = Mock()
    storage.save_document = AsyncMock()
    storage.get_document = AsyncMock()
    storage.delete_document = AsyncMock()
    return storage

@pytest.fixture
def mock_summary_generator():
    """Создает мок для генератора резюме."""
    connector = Mock()
    connector.capabilities = {ConnectorCapability.SUMMARY}
    connector.generate_summary = AsyncMock(return_value="Test summary")
    return connector

@pytest.fixture
def mock_vectorizer():
    """Создает мок для векторизатора."""
    connector = Mock()
    connector.capabilities = {ConnectorCapability.VECTORIZATION}
    connector.vectorize = AsyncMock(return_value=[0.1, 0.2, 0.3])
    connector.vectorize_batch = AsyncMock(return_value=[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])
    return connector

@pytest.fixture
def mock_file_collector():
    """Создает мок для коллектора файлов."""
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
    """Создает мок для PDF процессора."""
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
    """Создает мок для DOC процессора."""
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
def document_processor(
    mock_storage,
    mock_summary_generator,
    mock_vectorizer,
    mock_file_collector,
    mock_pdf_processor,
    mock_doc_processor
):
    """Создает экземпляр DocumentProcessor с моками."""
    return DocumentProcessor(
        storage=mock_storage,
        summary_generator=mock_summary_generator,
        vectorizer=mock_vectorizer,
        file_collector=mock_file_collector,
        pdf_processor=mock_pdf_processor,
        doc_processor=mock_doc_processor
    )

@pytest.mark.asyncio
async def test_process_file_pdf(document_processor, mock_pdf_processor):
    """Тестирует обработку PDF файла."""
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
    assert doc.relative_path == "test.pdf"
    assert doc.file_name == "test.pdf"
    assert doc.summary == "Test summary"
    assert doc.metadata["page_count"] == 1
    assert len(doc.paragraphs) > 0
    
    mock_pdf_processor.extract_content.assert_called_once_with("/tmp/test.pdf")

@pytest.mark.asyncio
async def test_process_file_doc(document_processor, mock_doc_processor):
    """Тестирует обработку DOC файла."""
    file_info = FileInfo(
        file_id="test_id",
        file_name="test.doc",
        relative_path="test.doc",
        absolute_path="/tmp/test.doc",
        extension=".doc",
        size=1000,
        created_at=datetime.now(),
        modified_at=datetime.now()
    )
    
    doc = await document_processor._process_file(file_info)
    
    assert isinstance(doc, Document)
    assert doc.file_id == "test_id"
    assert doc.relative_path == "test.doc"
    assert doc.file_name == "test.doc"
    assert doc.summary == "Test summary"
    assert doc.metadata["page_count"] == 1
    assert len(doc.paragraphs) > 0
    
    mock_doc_processor.extract_content.assert_called_once_with("/tmp/test.doc")

@pytest.mark.asyncio
async def test_process_file_unknown_type(document_processor):
    """Тестирует обработку файла неизвестного типа."""
    file_info = FileInfo(
        file_id="test_id",
        file_name="test.unknown",
        relative_path="test.unknown",
        absolute_path="/tmp/test.unknown",
        extension=".unknown",
        size=1000,
        created_at=datetime.now(),
        modified_at=datetime.now()
    )
    
    with pytest.raises(ValueError, match="Unsupported file type"):
        await document_processor._process_file(file_info)

@pytest.mark.asyncio
async def test_process_file_with_error(document_processor, mock_pdf_processor):
    """Тестирует обработку ошибок при обработке файла."""
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
    
    mock_pdf_processor.extract_content.side_effect = Exception("Test error")
    
    with pytest.raises(Exception, match="Test error"):
        await document_processor._process_file(file_info)

@pytest.mark.asyncio
async def test_process_file_with_storage_error(document_processor, mock_storage):
    """Тестирует обработку ошибок хранилища."""
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
    
    mock_storage.save_document.side_effect = Exception("Storage error")
    
    with pytest.raises(Exception, match="Storage error"):
        await document_processor._process_file(file_info)

@pytest.mark.asyncio
async def test_process_file_with_vectorization_error(document_processor, mock_vectorizer):
    """Тестирует обработку ошибок векторизации."""
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
    
    mock_vectorizer.vectorize_batch.side_effect = Exception("Vectorization error")
    
    with pytest.raises(Exception, match="Vectorization error"):
        await document_processor._process_file(file_info)

@pytest.mark.asyncio
async def test_process_file_with_summary_error(document_processor, mock_summary_generator):
    """Тестирует обработку ошибок генерации резюме."""
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
    
    mock_summary_generator.generate_summary.side_effect = Exception("Summary error")
    
    with pytest.raises(Exception, match="Summary error"):
        await document_processor._process_file(file_info)

@pytest.mark.asyncio
async def test_process_file_with_paragraphs(document_processor, mock_pdf_processor):
    """Тестирует обработку файла с параграфами."""
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
    
    mock_pdf_processor.extract_content.return_value = DocumentContent(
        text="Paragraph 1\n\nParagraph 2",
        metadata={"page_count": 1},
        tables=[],
        images=[],
        styles={}
    )
    
    doc = await document_processor._process_file(file_info)
    
    assert len(doc.paragraphs) == 2
    assert doc.paragraphs[0].text == "Paragraph 1"
    assert doc.paragraphs[1].text == "Paragraph 2"
    assert doc.paragraphs[0].position_in_file == 0
    assert doc.paragraphs[1].position_in_file == 1 