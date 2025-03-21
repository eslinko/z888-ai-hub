"""
Integration tests for FileValidator class.
"""

import os
import pytest
from pathlib import Path
from z888_ai_hub.utils.file_validator import FileValidator, FileType
from z888_ai_hub.utils.logging_utils import setup_logger

logger = setup_logger('TestFileValidator')

# Пути к тестовым файлам
SAMPLE_PDFS_DIR = "tests/sample_pdfs"
TEST_PDF_FILE = "Med_6.3.pdf"
TEST_PDF_PATH = os.path.join(SAMPLE_PDFS_DIR, TEST_PDF_FILE)

class TestFileValidatorIntegration:
    """Integration test cases for FileValidator class."""

    @pytest.fixture
    def validator(self):
        """Create FileValidator instance."""
        return FileValidator()

    @pytest.fixture
    def temp_dir(tmp_path):
        """Create temporary directory."""
        return tmp_path

    @pytest.fixture
    def sample_files(temp_dir):
        """Create sample files for testing."""
        files = {
            'valid_pdf': temp_dir / "valid.pdf",
            'invalid_pdf': temp_dir / "invalid.pdf",
            'valid_doc': temp_dir / "valid.docx",
            'invalid_doc': temp_dir / "invalid.doc",
            'unknown': temp_dir / "unknown.txt",
            'valid.txt': temp_dir / "valid.txt",
            'invalid.exe': temp_dir / "invalid.exe",
            'large.pdf': temp_dir / "large.pdf",
            'small.txt': temp_dir / "small.txt"
        }
        
        # Copy real PDF file
        with open(TEST_PDF_PATH, 'rb') as src, open(files['valid_pdf'], 'wb') as dst:
            dst.write(src.read())
        
        # Create invalid PDF
        files['invalid_pdf'].write_text("This is not a PDF file")
        
        # Create valid DOC
        files['valid_doc'].write_text("This is a test document")
        
        # Create valid TXT
        files['valid.txt'].write_text("A" * 200)  # Long enough text
        
        # Create small TXT
        files['small.txt'].write_text("A" * 50)  # Too short text
        
        # Create large PDF
        files['large.pdf'].write_bytes(b"X" * (11 * 1024 * 1024))  # 11MB
        
        # Create invalid DOC
        files['invalid_doc'].write_text("This is not a DOC file")
        
        # Create invalid EXE
        files['invalid.exe'].write_bytes(b"Invalid content")
        
        # Create unknown file
        files['unknown'].write_text("This is a text file")
        
        return files

    @pytest.mark.integration
    def test_validate_pdf_file(self, validator, sample_files):
        """Integration test for PDF file validation."""
        # Test valid PDF
        result = validator.validate_file_sync(str(sample_files['valid_pdf']))
        assert result.is_valid is True
        assert result.file_type == FileType.PDF
        assert result.mime_type == 'application/pdf'
        assert result.is_readable is True
        assert result.metadata is not None
        assert result.metadata['page_count'] > 0
        
        # Test invalid PDF
        result = validator.validate_file_sync(str(sample_files['invalid_pdf']))
        assert result.is_valid is False
        assert result.file_type == FileType.PDF
        assert result.is_readable is False
        assert result.error_message is not None

    @pytest.mark.integration
    def test_validate_doc_file(self, validator, sample_files):
        """Integration test for DOC file validation."""
        # Test valid DOC
        result = validator.validate_file_sync(str(sample_files['valid_doc']))
        assert result.file_type == FileType.DOC
        
        # Test invalid DOC
        result = validator.validate_file_sync(str(sample_files['invalid_doc']))
        assert result.is_valid is False
        assert result.file_type == FileType.DOC
        assert result.is_readable is False
        assert result.error_message is not None

    @pytest.mark.integration
    def test_validate_unknown_file(self, validator, sample_files):
        """Integration test for unknown file validation."""
        result = validator.validate_file_sync(str(sample_files['unknown']))
        assert result.is_valid is False
        assert result.file_type == FileType.UNKNOWN
        assert result.is_readable is False
        assert result.error_message == "Unsupported file type"

    @pytest.mark.integration
    def test_pdf_metadata(self, validator):
        """Integration test for PDF metadata extraction."""
        result = validator.validate_file_sync(TEST_PDF_PATH)
        assert result.is_valid is True
        assert result.metadata is not None
        assert 'page_count' in result.metadata
        assert result.metadata['page_count'] > 0
        assert 'is_encrypted' in result.metadata
        assert 'pdf_version' in result.metadata

    @pytest.mark.integration
    def test_multiple_pdf_files(self, validator):
        """Integration test for validation of multiple PDF files."""
        pdf_files = [
            f for f in os.listdir(SAMPLE_PDFS_DIR)
            if f.endswith('.pdf')
        ]
        
        for pdf_file in pdf_files:
            pdf_path = os.path.join(SAMPLE_PDFS_DIR, pdf_file)
            result = validator.validate_file_sync(pdf_path)
            
            assert result.is_valid is True, f"Failed to validate {pdf_file}"
            assert result.file_type == FileType.PDF
            assert result.mime_type == 'application/pdf'
            assert result.is_readable is True
            assert result.metadata['page_count'] > 0

    @pytest.mark.integration
    def test_file_size_limits(self, validator, sample_files):
        """Integration test for file size limits."""
        # Test file within size limit
        result = validator.validate_file_sync(str(sample_files['valid_pdf']))
        assert result.is_valid is True
        
        # Test file exceeding size limit
        result = validator.validate_file_sync(str(sample_files['large.pdf']))
        assert result.is_valid is False
        assert "File size exceeds maximum limit" in result.error_message

    @pytest.mark.integration
    def test_text_length_validation(self, validator, sample_files):
        """Integration test for text length validation."""
        # Test text within length limits
        result = validator.validate_file_sync(str(sample_files['valid.txt']))
        assert result.is_valid is True
        
        # Test text below minimum length
        result = validator.validate_file_sync(str(sample_files['small.txt']))
        assert result.is_valid is False
        assert "Text length is below minimum" in result.error_message

    @pytest.mark.integration
    def test_file_permissions(self, validator, temp_dir):
        """Integration test for file permissions handling."""
        if os.name != 'nt':  # Skip on Windows
            # Create file without read permissions
            no_access_file = temp_dir / "no_access.pdf"
            no_access_file.write_text("Test content")
            os.chmod(no_access_file, 0)
            
            result = validator.validate_file_sync(str(no_access_file))
            assert result.is_valid is False
            assert "Permission denied" in result.error_message
            
            # Cleanup
            os.chmod(no_access_file, 0o644) 