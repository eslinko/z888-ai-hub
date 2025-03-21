"""
Unit tests for FileCollector class.
"""

import os
import pytest
from unittest.mock import Mock, patch
from pathlib import Path
from z888_ai_hub.utils.file_collector import FileCollector, FileInfo, FileCollectorError, PathValidationError
from z888_ai_hub.utils.file_validator import FileType

class TestFileCollectorUnit:
    """Unit test cases for FileCollector class."""

    @pytest.fixture
    def mock_path(self):
        """Create a mock path for testing."""
        return "/test/path"

    @pytest.fixture
    def collector(self, mock_path):
        """Create a FileCollector instance with mocked path."""
        with patch('os.path.exists', return_value=True):
            with patch('os.path.isdir', return_value=True):
                return FileCollector(mock_path)

    def test_validate_path_valid_directory(self, collector, mock_path):
        """Test path validation with valid directory."""
        with patch('os.path.exists', return_value=True):
            with patch('os.path.isdir', return_value=True):
                is_valid, error = collector.validate_path(mock_path)
                assert is_valid
                assert error is None

    def test_validate_path_nonexistent(self, collector):
        """Test path validation with nonexistent directory."""
        with patch('os.path.exists', return_value=False):
            is_valid, error = collector.validate_path("/nonexistent/path")
            assert not is_valid
            assert "does not exist" in error

    def test_validate_path_not_directory(self, collector):
        """Test path validation with file instead of directory."""
        with patch('os.path.exists', return_value=True):
            with patch('os.path.isdir', return_value=False):
                is_valid, error = collector.validate_path("/test/file.txt")
                assert not is_valid
                assert "not a directory" in error

    def test_check_file_access_valid_file(self, collector):
        """Test file access check with valid file."""
        with patch('os.path.exists', return_value=True):
            with patch('os.path.isfile', return_value=True):
                with patch('os.access', return_value=True):
                    is_accessible, error = collector.check_file_access("/test/file.txt")
                    assert is_accessible
                    assert error is None

    def test_check_file_access_nonexistent(self, collector):
        """Test file access check with nonexistent file."""
        with patch('os.path.exists', return_value=False):
            is_accessible, error = collector.check_file_access("/test/nonexistent.txt")
            assert not is_accessible
            assert "does not exist" in error

    def test_check_file_access_directory(self, collector):
        """Test file access check with directory instead of file."""
        with patch('os.path.exists', return_value=True):
            with patch('os.path.isfile', return_value=False):
                is_accessible, error = collector.check_file_access("/test/dir")
                assert not is_accessible
                assert "not a file" in error

    def test_file_size_constraints(self, collector):
        """Test file size constraints."""
        with patch('os.path.getsize', return_value=5):
            is_accessible, error = collector.check_file_access("/test/small.txt")
            assert not is_accessible
            assert "less than minimum" in error

        with patch('os.path.getsize', return_value=5000):
            is_accessible, error = collector.check_file_access("/test/large.txt")
            assert not is_accessible
            assert "greater than maximum" in error

    def test_file_collector_initialization(self, mock_path):
        """Test FileCollector initialization."""
        with patch('os.path.exists', return_value=True):
            with patch('os.path.isdir', return_value=True):
                collector = FileCollector(mock_path)
                assert collector.root_path == os.path.abspath(mock_path)
                assert collector.allowed_extensions == {'.pdf', '.doc', '.docx'}
                assert collector.validate_content is True
                assert collector.skip_unreadable is False

    def test_file_info_creation(self):
        """Test FileInfo object creation."""
        file_info = FileInfo(
            path="/test/file.pdf",
            size=1000,
            extension=".pdf",
            file_type=FileType.PDF,
            is_accessible=True
        )
        assert file_info.path == "/test/file.pdf"
        assert file_info.size == 1000
        assert file_info.extension == ".pdf"
        assert file_info.file_type == FileType.PDF
        assert file_info.is_accessible is True

    def test_statistics_tracking(self, collector):
        """Test statistics tracking."""
        collector._stats['total_files'] = 10
        collector._stats['processed_files'] = 8
        collector._stats['file_types'] = {'.pdf': 5, '.doc': 3}
        
        stats = collector.get_statistics()
        assert stats['total_files'] == 10
        assert stats['processed_files'] == 8
        assert stats['file_types'] == {'.pdf': 5, '.doc': 3}

    def test_custom_extensions(self, mock_path):
        """Test custom extensions configuration."""
        with patch('os.path.exists', return_value=True):
            with patch('os.path.isdir', return_value=True):
                collector = FileCollector(mock_path, allowed_extensions={'.txt'})
                assert collector.allowed_extensions == {'.txt'}

    def test_invalid_root_path(self):
        """Test FileCollector initialization with invalid root path."""
        with patch('os.path.exists', return_value=False):
            with pytest.raises(PathValidationError) as exc_info:
                FileCollector("/nonexistent/path")
            assert "does not exist" in str(exc_info.value) 