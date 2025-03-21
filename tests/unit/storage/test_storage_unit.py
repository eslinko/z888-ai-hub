"""
Unit tests for storage implementations.
"""

import uuid
from datetime import datetime
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from z888_ai_hub.storage.database import SupabaseStorage, Document, Paragraph
from z888_ai_hub.storage.database.exceptions import (
    DocumentNotFoundError,
    StorageError,
    InvalidDocumentError,
    InvalidPathError,
    InvalidMetadataError
)

class TestSupabaseStorageUnit:
    """Unit test cases for SupabaseStorage class."""

    @pytest.fixture
    def mock_supabase_client(self):
        """Create mock Supabase client."""
        mock_client = MagicMock()
        mock_client.table = MagicMock()
        mock_client.table.return_value.insert = AsyncMock()
        mock_client.table.return_value.select = AsyncMock()
        mock_client.table.return_value.delete = AsyncMock()
        mock_client.table.return_value.update = AsyncMock()
        mock_client.rpc = AsyncMock()
        return mock_client

    @pytest.fixture
    def storage(self, mock_supabase_client):
        """Initialize storage with mock client."""
        with patch('z888_ai_hub.storage.database.client.create_client', return_value=mock_supabase_client):
            return SupabaseStorage()

    @pytest.fixture
    def test_document(self):
        """Create test document."""
        return Document(
            file_id=str(uuid.uuid4()),
            relative_path="test/path/document.pdf",
            file_name="document.pdf",
            summary="Test document summary",
            metadata={
                "size": 1000,
                "page_count": 1,
                "language": "EN",
                "is_test": True
            },
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

    @pytest.fixture
    def test_paragraphs(self, test_document):
        """Create test paragraphs."""
        return [
            Paragraph(
                text="Test paragraph 1",
                file_id=test_document.file_id,
                position_in_file=0,
                metadata={"page_number": 1}
            ),
            Paragraph(
                text="Test paragraph 2",
                file_id=test_document.file_id,
                position_in_file=1,
                metadata={"page_number": 2}
            )
        ]

    def test_document_validation(self, storage, test_document):
        """Test document validation."""
        # Test valid document
        assert storage._validate_document(test_document) is True

        # Test invalid document with empty path
        invalid_doc = Document(
            file_id=str(uuid.uuid4()),
            relative_path="",
            file_name="test.pdf",
            summary="Test",
            metadata={"size": 100},
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        with pytest.raises(InvalidPathError):
            storage._validate_document(invalid_doc)

    def test_paragraph_validation(self, storage, test_document):
        """Test paragraph validation."""
        # Test valid paragraph
        valid_paragraph = Paragraph(
            text="Valid text",
            file_id=test_document.file_id,
            position_in_file=0,
            metadata={}
        )
        assert storage._validate_paragraph(valid_paragraph) is True

        # Test invalid paragraph with empty text
        invalid_paragraph = Paragraph(
            text="",
            file_id=test_document.file_id,
            position_in_file=0,
            metadata={}
        )
        with pytest.raises(InvalidDocumentError):
            storage._validate_paragraph(invalid_paragraph)

    def test_metadata_validation(self, storage, test_document):
        """Test metadata validation."""
        # Test valid metadata
        assert storage._validate_metadata(test_document.metadata) is True

        # Test invalid metadata without required fields
        invalid_metadata = {"size": 100}  # Missing required fields
        with pytest.raises(InvalidMetadataError):
            storage._validate_metadata(invalid_metadata)

    @pytest.mark.asyncio
    async def test_save_document_with_mock(self, storage, test_document, mock_supabase_client):
        """Test document saving with mocked client."""
        # Configure mock response
        mock_supabase_client.table.return_value.insert.return_value = {
            "data": [test_document.dict()],
            "error": None
        }

        # Save document
        await storage.save_document(test_document)

        # Verify mock was called correctly
        mock_supabase_client.table.assert_called_once_with("documents")
        mock_supabase_client.table.return_value.insert.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_document_with_mock(self, storage, test_document, mock_supabase_client):
        """Test document retrieval with mocked client."""
        # Configure mock response
        mock_supabase_client.table.return_value.select.return_value = {
            "data": [test_document.dict()],
            "error": None
        }

        # Get document
        doc = await storage.get_document(test_document.file_id)

        # Verify mock was called correctly
        mock_supabase_client.table.assert_called_once_with("documents")
        mock_supabase_client.table.return_value.select.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_document_with_mock(self, storage, test_document, mock_supabase_client):
        """Test document deletion with mocked client."""
        # Configure mock response
        mock_supabase_client.table.return_value.delete.return_value = {
            "data": None,
            "error": None
        }

        # Delete document
        await storage.delete_document(test_document.file_id)

        # Verify mock was called correctly
        mock_supabase_client.table.assert_called_once_with("documents")
        mock_supabase_client.table.return_value.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_error_handling_with_mock(self, storage, test_document, mock_supabase_client):
        """Test error handling with mocked client."""
        # Configure mock to raise error
        mock_supabase_client.table.return_value.insert.return_value = {
            "data": None,
            "error": {"message": "Test error"}
        }

        # Test error handling
        with pytest.raises(StorageError):
            await storage.save_document(test_document)

    def test_path_normalization(self, storage):
        """Test path normalization."""
        # Test Windows-style path
        windows_path = "test\\path\\document.pdf"
        normalized = storage._normalize_path(windows_path)
        assert normalized == "test/path/document.pdf"

        # Test Unix-style path
        unix_path = "test/path/document.pdf"
        normalized = storage._normalize_path(unix_path)
        assert normalized == "test/path/document.pdf"

    def test_metadata_normalization(self, storage):
        """Test metadata normalization."""
        # Test valid metadata
        valid_metadata = {
            "size": 1000,
            "page_count": 1,
            "language": "EN"
        }
        normalized = storage._normalize_metadata(valid_metadata)
        assert normalized == valid_metadata

        # Test metadata with invalid types
        invalid_metadata = {
            "size": "1000",  # Should be int
            "page_count": "1",  # Should be int
            "language": 123  # Should be str
        }
        with pytest.raises(InvalidMetadataError):
            storage._normalize_metadata(invalid_metadata) 