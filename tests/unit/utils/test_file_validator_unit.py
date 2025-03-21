"""
Unit tests for FileValidator class.
"""

import os
import pytest
from unittest.mock import Mock, patch
from pathlib import Path
from z888_ai_hub.utils.file_validator import FileValidator, FileType, ValidationResult, FileValidatorError

class TestFileValidatorUnit:
    """Unit test cases for FileValidator class."""

    @pytest.fixture
    def validator(self):
        """Create a FileValidator instance."""
        return FileValidator()

    def test_validate_file_type_pdf(self, validator):
        """Test PDF file type validation."""
        with patch('os.path.splitext', return_value=('test', '.pdf')):
            is_valid = validator.validate_file_type('test.pdf')
            assert is_valid

    def test_validate_file_type_doc(self, validator):
        """Test DOC file type validation."""
        with patch('os.path.splitext', return_value=('test', '.doc')):
            is_valid = validator.validate_file_type('test.doc')
            assert is_valid

    def test_validate_file_type_unsupported(self, validator):
        """Test unsupported file type validation."""
        with patch('os.path.splitext', return_value=('test', '.txt')):
            is_valid = validator.validate_file_type('test.txt')
            assert not is_valid

    def test_check_file_access_valid(self, validator):
        """Test file access check with valid file."""
        with patch('os.path.exists', return_value=True):
            with patch('os.path.isfile', return_value=True):
                with patch('os.access', return_value=True):
                    is_accessible, error = validator.check_file_access('/test/file.pdf')
                    assert is_accessible
                    assert error is None

    def test_check_file_access_nonexistent(self, validator):
        """Test file access check with nonexistent file."""
        with patch('os.path.exists', return_value=False):
            is_accessible, error = validator.check_file_access('/test/nonexistent.pdf')
            assert not is_accessible
            assert "does not exist" in error

    def test_check_file_access_directory(self, validator):
        """Test file access check with directory instead of file."""
        with patch('os.path.exists', return_value=True):
            with patch('os.path.isfile', return_value=False):
                is_accessible, error = validator.check_file_access('/test/dir')
                assert not is_accessible
                assert "not a file" in error

    def test_check_file_access_no_permission(self, validator):
        """Test file access check with no read permission."""
        with patch('os.path.exists', return_value=True):
            with patch('os.path.isfile', return_value=True):
                with patch('os.access', return_value=False):
                    is_accessible, error = validator.check_file_access('/test/file.pdf')
                    assert not is_accessible
                    assert "No read permission" in error

    def test_validate_file_sync_pdf(self, validator):
        """Test synchronous PDF file validation."""
        with patch('os.path.exists', return_value=True):
            with patch('os.path.isfile', return_value=True):
                with patch('os.access', return_value=True):
                    with patch('magic.from_file', return_value='application/pdf'):
                        with patch('pypdf.PdfReader') as mock_pdf:
                            mock_pdf.return_value.pages = [Mock()]
                            result = validator.validate_file_sync('/test/file.pdf')
                            assert result.is_valid
                            assert result.file_type == FileType.PDF
                            assert result.mime_type == 'application/pdf'
                            assert result.is_readable

    def test_validate_file_sync_doc(self, validator):
        """Test synchronous DOC file validation."""
        with patch('os.path.exists', return_value=True):
            with patch('os.path.isfile', return_value=True):
                with patch('os.access', return_value=True):
                    with patch('magic.from_file', return_value='application/msword'):
                        with patch('docx.Document') as mock_doc:
                            mock_doc.return_value.paragraphs = [Mock()]
                            result = validator.validate_file_sync('/test/file.doc')
                            assert result.is_valid
                            assert result.file_type == FileType.DOC
                            assert result.mime_type == 'application/msword'
                            assert result.is_readable

    def test_validate_file_sync_invalid_pdf(self, validator):
        """Test synchronous validation of invalid PDF file."""
        with patch('os.path.exists', return_value=True):
            with patch('os.path.isfile', return_value=True):
                with patch('os.access', return_value=True):
                    with patch('magic.from_file', return_value='application/pdf'):
                        with patch('pypdf.PdfReader', side_effect=Exception('Invalid PDF')):
                            result = validator.validate_file_sync('/test/invalid.pdf')
                            assert not result.is_valid
                            assert result.file_type == FileType.PDF
                            assert result.mime_type == 'application/pdf'
                            assert not result.is_readable
                            assert "Invalid PDF" in result.error_message

    def test_validate_file_sync_invalid_doc(self, validator):
        """Test synchronous validation of invalid DOC file."""
        with patch('os.path.exists', return_value=True):
            with patch('os.path.isfile', return_value=True):
                with patch('os.access', return_value=True):
                    with patch('magic.from_file', return_value='application/msword'):
                        with patch('docx.Document', side_effect=Exception('Invalid DOC')):
                            result = validator.validate_file_sync('/test/invalid.doc')
                            assert not result.is_valid
                            assert result.file_type == FileType.DOC
                            assert result.mime_type == 'application/msword'
                            assert not result.is_readable
                            assert "Invalid DOC" in result.error_message

    def test_validate_file_sync_unknown_type(self, validator):
        """Test synchronous validation of file with unknown type."""
        with patch('os.path.exists', return_value=True):
            with patch('os.path.isfile', return_value=True):
                with patch('os.access', return_value=True):
                    with patch('magic.from_file', return_value='unknown/type'):
                        result = validator.validate_file_sync('/test/unknown.file')
                        assert not result.is_valid
                        assert result.file_type == FileType.UNKNOWN
                        assert result.mime_type == 'unknown/type'
                        assert not result.is_readable
                        assert "Unsupported file type" in result.error_message

    def test_validate_file_sync_nonexistent(self, validator):
        """Test synchronous validation of nonexistent file."""
        with patch('os.path.exists', return_value=False):
            result = validator.validate_file_sync('/test/nonexistent.pdf')
            assert not result.is_valid
            assert result.file_type == FileType.UNKNOWN
            assert result.mime_type == 'unknown'
            assert not result.is_readable
            assert "does not exist" in result.error_message

    def test_validate_file_sync_no_permission(self, validator):
        """Test synchronous validation of file without read permission."""
        with patch('os.path.exists', return_value=True):
            with patch('os.path.isfile', return_value=True):
                with patch('os.access', return_value=False):
                    result = validator.validate_file_sync('/test/no_permission.pdf')
                    assert not result.is_valid
                    assert result.file_type == FileType.UNKNOWN
                    assert result.mime_type == 'unknown'
                    assert not result.is_readable
                    assert "No read permission" in result.error_message

    def test_file_type_from_extension(self):
        """Test FileType.from_extension method."""
        assert FileType.from_extension('.pdf') == FileType.PDF
        assert FileType.from_extension('pdf') == FileType.PDF
        assert FileType.from_extension('.doc') == FileType.DOC
        assert FileType.from_extension('.docx') == FileType.DOC
        assert FileType.from_extension('.txt') == FileType.UNKNOWN

    def test_validation_result_initialization(self):
        """Test ValidationResult initialization."""
        result = ValidationResult(
            is_valid=True,
            file_type=FileType.PDF,
            mime_type='application/pdf',
            is_readable=True
        )
        
        assert result.is_valid is True
        assert result.file_type == FileType.PDF
        assert result.mime_type == 'application/pdf'
        assert result.is_readable is True
        assert result.error_message is None
        assert isinstance(result.metadata, dict)
        assert len(result.metadata) == 0

    def test_validation_result_with_error(self):
        """Test ValidationResult with error message."""
        result = ValidationResult(
            is_valid=False,
            file_type=FileType.PDF,
            mime_type='application/pdf',
            is_readable=False,
            error_message="Test error"
        )
        
        assert result.is_valid is False
        assert result.error_message == "Test error"

    def test_validation_result_with_metadata(self):
        """Test ValidationResult with metadata."""
        metadata = {'page_count': 5, 'is_encrypted': False}
        result = ValidationResult(
            is_valid=True,
            file_type=FileType.PDF,
            mime_type='application/pdf',
            is_readable=True,
            metadata=metadata
        )
        
        assert result.metadata == metadata
        assert result.metadata['page_count'] == 5
        assert result.metadata['is_encrypted'] is False

    def test_file_validator_initialization(self):
        """Test FileValidator initialization with different configs."""
        # Test default config
        validator = FileValidator()
        assert validator.max_file_size_mb == 10
        assert '.pdf' in validator.supported_extensions
        assert '.doc' in validator.supported_extensions
        
        # Test custom config
        config = {
            "max_file_size_mb": 20,
            "supported_extensions": [".txt", ".md"],
            "min_text_length": 200,
            "max_text_length": 2000000
        }
        validator = FileValidator(config)
        assert validator.max_file_size_mb == 20
        assert validator.supported_extensions == [".txt", ".md"]
        assert validator.min_text_length == 200
        assert validator.max_text_length == 2000000

    @pytest.mark.asyncio
    async def test_validate_file_type_with_mock(self, validator):
        """Test file type validation with mocked file."""
        with patch('os.path.exists', return_value=True):
            with patch('os.path.isfile', return_value=True):
                # Test supported extension
                assert await validator.validate_file_type("test.pdf")
                # Test unsupported extension
                assert not await validator.validate_file_type("test.exe")

    @pytest.mark.asyncio
    async def test_validate_file_size_with_mock(self, validator):
        """Test file size validation with mocked file."""
        with patch('os.path.getsize', return_value=5 * 1024 * 1024):  # 5MB
            assert await validator.validate_file_size("test.pdf")
        
        with patch('os.path.getsize', return_value=15 * 1024 * 1024):  # 15MB
            assert not await validator.validate_file_size("test.pdf")

    @pytest.mark.asyncio
    async def test_validate_text_length_with_mock(self, validator):
        """Test text length validation with mocked file."""
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = "A" * 150
            assert await validator.validate_text_length("test.txt")
            
            mock_open.return_value.__enter__.return_value.read.return_value = "A" * 50
            assert not await validator.validate_text_length("test.txt")

    def test_error_handling_with_mock(self, validator):
        """Test error handling with mocked file operations."""
        with patch('os.path.exists', return_value=False):
            result = validator.validate_file_sync("nonexistent.pdf")
            assert not result.is_valid
            assert "File does not exist" in result.error_message

        with patch('os.path.exists', return_value=True):
            with patch('os.access', return_value=False):
                result = validator.validate_file_sync("no_access.pdf")
                assert not result.is_valid
                assert "Permission denied" in result.error_message

    def test_metadata_handling(self, validator):
        """Test metadata handling with mocked PDF."""
        mock_metadata = {
            'page_count': 5,
            'is_encrypted': False,
            'pdf_version': '1.7'
        }
        
        with patch('z888_ai_hub.utils.file_validator.FileValidator._extract_pdf_metadata', 
                  return_value=mock_metadata):
            result = validator.validate_file_sync("test.pdf")
            assert result.metadata == mock_metadata
            assert result.metadata['page_count'] == 5
            assert result.metadata['is_encrypted'] is False
            assert result.metadata['pdf_version'] == '1.7' 