"""
Tests for FileCollector class.
"""

import os
import shutil
import pytest
from datetime import datetime
from pathlib import Path
from z888_ai_hub.utils.file_collector import FileCollector, FileInfo, FileCollectorError, PathValidationError
from z888_ai_hub.utils.file_validator import FileType
import tempfile
import stat

# Пути к тестовым файлам
SAMPLE_PDFS_DIR = "tests/sample_pdfs"


def create_test_file(path: str, content: str = "test content", mode: int = 0o644) -> None:
    """Create a test file with given content and permissions."""
    with open(path, 'w') as f:
        f.write(content)
    os.chmod(path, mode)


class TestFileCollector:
    """Test cases for FileCollector class."""

    @pytest.fixture
    def test_dir(self):
        """Create a temporary directory with test files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Copy sample PDFs to temp directory
            sample_pdfs = [f for f in os.listdir(SAMPLE_PDFS_DIR) if f.endswith('.pdf')]
            assert len(sample_pdfs) > 0, "No PDF files found in sample directory"
            
            print("\nSample PDFs:", sample_pdfs)  # Debug output
            
            # Копируем первый PDF файл как test1.pdf
            src = os.path.join(SAMPLE_PDFS_DIR, sample_pdfs[0])
            dst = os.path.join(temp_dir, "test1.pdf")
            shutil.copy2(src, dst)
            
            # Create test DOC files
            create_test_file(os.path.join(temp_dir, "test2.doc"))
            create_test_file(os.path.join(temp_dir, "test3.docx"))
            create_test_file(os.path.join(temp_dir, "test4.txt"))
            
            # Create nested directory
            nested_dir = os.path.join(temp_dir, "nested")
            os.makedirs(nested_dir)
            
            # Копируем второй PDF файл в nested директорию
            if len(sample_pdfs) > 1:
                src = os.path.join(SAMPLE_PDFS_DIR, sample_pdfs[1])
            else:
                src = os.path.join(SAMPLE_PDFS_DIR, sample_pdfs[0])
            dst = os.path.join(nested_dir, "nested1.pdf")
            shutil.copy2(src, dst)
            
            create_test_file(os.path.join(nested_dir, "nested2.doc"))
            
            # Debug output
            print("\nTemp dir contents:", os.listdir(temp_dir))
            print("Nested dir contents:", os.listdir(nested_dir))
            
            # Debug: проверяем размер файлов
            for f in os.listdir(temp_dir):
                if f.endswith('.pdf'):
                    size = os.path.getsize(os.path.join(temp_dir, f))
                    print(f"PDF file {f} size: {size} bytes")
            
            yield temp_dir

    def test_validate_path_valid_directory(self, test_dir):
        """Test path validation with valid directory."""
        collector = FileCollector(test_dir)
        is_valid, error = collector.validate_path(test_dir)
        assert is_valid
        assert error is None

    def test_validate_path_nonexistent(self):
        """Test path validation with nonexistent directory."""
        collector = FileCollector("/tmp")  # Using /tmp as it should exist
        is_valid, error = collector.validate_path("/nonexistent/path")
        assert not is_valid
        assert "does not exist" in error

    def test_validate_path_not_directory(self, test_dir):
        """Test path validation with file instead of directory."""
        file_path = os.path.join(test_dir, "test1.pdf")
        collector = FileCollector(test_dir)
        is_valid, error = collector.validate_path(file_path)
        assert not is_valid
        assert "not a directory" in error

    def test_validate_path_no_permissions(self, test_dir):
        """Test path validation with directory without permissions."""
        if os.name != 'nt':  # Skip on Windows
            no_access_dir = os.path.join(test_dir, "no_access")
            os.makedirs(no_access_dir)
            os.chmod(no_access_dir, 0)
            
            collector = FileCollector(test_dir)
            is_valid, error = collector.validate_path(no_access_dir)
            assert not is_valid
            assert "permission" in error
            
            # Cleanup
            os.chmod(no_access_dir, 0o755)

    def test_check_file_access_valid_file(self, test_dir):
        """Test file access check with valid file."""
        file_path = os.path.join(test_dir, "test1.pdf")
        collector = FileCollector(test_dir)
        is_accessible, error = collector.check_file_access(file_path)
        assert is_accessible
        assert error is None

    def test_check_file_access_nonexistent(self, test_dir):
        """Test file access check with nonexistent file."""
        collector = FileCollector(test_dir)
        is_accessible, error = collector.check_file_access(
            os.path.join(test_dir, "nonexistent.pdf")
        )
        assert not is_accessible
        assert "does not exist" in error

    def test_check_file_access_directory(self, test_dir):
        """Test file access check with directory instead of file."""
        collector = FileCollector(test_dir)
        is_accessible, error = collector.check_file_access(test_dir)
        assert not is_accessible
        assert "not a file" in error

    def test_check_file_access_no_permissions(self, test_dir):
        """Test file access check with file without read permissions."""
        if os.name != 'nt':  # Skip on Windows
            file_path = os.path.join(test_dir, "no_access.pdf")
            create_test_file(file_path, mode=0)
            
            collector = FileCollector(test_dir)
            is_accessible, error = collector.check_file_access(file_path)
            assert not is_accessible
            assert "permission" in error
            
            # Cleanup
            os.chmod(file_path, 0o644)

    def test_file_size_constraints(self, test_dir):
        """Test file size constraints."""
        # Create files with different sizes
        small_file = os.path.join(test_dir, "small.pdf")
        large_file = os.path.join(test_dir, "large.pdf")
        
        create_test_file(small_file, "small")  # 5 bytes
        create_test_file(large_file, "large" * 1000)  # 5000 bytes
        
        # Test minimum size constraint
        collector = FileCollector(test_dir, min_file_size=10)
        is_accessible, error = collector.check_file_access(small_file)
        assert not is_accessible
        assert "less than minimum" in error
        
        # Test maximum size constraint
        collector = FileCollector(test_dir, max_file_size=100)
        is_accessible, error = collector.check_file_access(large_file)
        assert not is_accessible
        assert "greater than maximum" in error

    def test_invalid_root_path(self):
        """Test FileCollector initialization with invalid root path."""
        with pytest.raises(PathValidationError) as exc_info:
            FileCollector("/nonexistent/path")
        assert "does not exist" in str(exc_info.value)

    def test_file_collection_with_validation(self, test_dir):
        """Test file collection with content validation."""
        collector = FileCollector(test_dir, validate_content=True)
        files = list(collector.collect_files())
        
        # Check that only valid files were collected
        assert len(files) > 0
        for file_info in files:
            assert isinstance(file_info, FileInfo)
            assert file_info.validation_result is not None
            assert file_info.is_accessible

    def test_nested_directories(self, test_dir):
        """Test file collection from nested directories."""
        collector = FileCollector(test_dir)
        files = list(collector.collect_files())
        
        # Check that files from nested directories were collected
        nested_files = [f for f in files if "nested" in f.relative_path]
        assert len(nested_files) > 0

    def test_custom_extensions(self, test_dir):
        """Test file collection with custom extensions."""
        collector = FileCollector(test_dir, allowed_extensions={'.txt'})
        files = list(collector.collect_files())
        
        # Check that only .txt files were collected
        assert all(f.extension == '.txt' for f in files)

    def test_statistics_tracking(self, test_dir):
        """Test statistics tracking during file collection."""
        collector = FileCollector(test_dir, validate_content=True)
        list(collector.collect_files())  # Collect files to update statistics
        
        stats = collector.get_statistics()
        assert stats['total_files'] > 0
        assert stats['processed_files'] > 0
        assert 'file_types' in stats

    def test_file_collector_initialization(self, test_dir):
        """Test FileCollector initialization."""
        collector = FileCollector(test_dir)
        assert collector.root_path == os.path.abspath(test_dir)
        assert collector.allowed_extensions == {'.pdf', '.doc', '.docx'}
        assert collector.validate_content is True
        assert collector.skip_unreadable is False
    
        # Test invalid path
        with pytest.raises(PathValidationError) as exc_info:
            FileCollector("/nonexistent/path")
        assert "does not exist" in str(exc_info.value)

    def test_file_collection_with_validation(self, test_dir):
        """Test file collection process with content validation."""
        collector = FileCollector(test_dir, validate_content=True)
        files = list(collector.collect_files())  # Convert generator to list
        
        # Should find valid PDF and DOC files
        assert len(files) > 0
        for file_info in files:
            assert isinstance(file_info, FileInfo)
            if collector.validate_content:
                assert file_info.validation_result is not None

    def test_file_type_statistics(self, test_dir):
        """Test file type statistics collection."""
        collector = FileCollector(test_dir, validate_content=True)
        list(collector.collect_files())  # Consume generator to update statistics
        
        stats = collector.get_statistics()
        
        # Проверяем общую статистику
        assert stats['total_files'] > 0
        assert stats['processed_files'] > 0
        assert stats['skipped_files'] >= 0
        assert stats['error_count'] >= 0
        
        # Проверяем статистику по типам файлов
        file_types = stats.get('file_types', {})
        assert len(file_types) > 0
        
        # Проверяем что есть статистика хотя бы для одного типа файлов
        has_file_type_stats = False
        for type_stats in file_types.values():
            if type_stats.get('total', 0) > 0:
                has_file_type_stats = True
                break
        assert has_file_type_stats, "No file type statistics found"

    def test_custom_extensions(self, test_dir):
        """Test custom file extensions."""
        # Создаем тестовый txt файл
        txt_file = os.path.join(test_dir, "test.txt")
        create_test_file(txt_file, "test content")
        
        collector = FileCollector(
            test_dir,
            allowed_extensions={'.txt'},
            validate_content=False  # Отключаем валидацию для .txt
        )
        files = list(collector.collect_files())  # Convert generator to list
        
        # Should only find .txt files
        assert len(files) > 0
        assert all(f.extension == '.txt' for f in files)

    def test_statistics_accuracy(self, test_dir):
        """Test accuracy of collection statistics."""
        collector = FileCollector(test_dir, validate_content=True)
        files = list(collector.collect_files())  # Convert generator to list
        
        stats = collector.get_statistics()
        
        # Basic statistics
        assert stats['total_files'] > 0
        assert stats['processed_files'] == len(files)
        assert stats['total_files'] >= stats['processed_files']
        assert stats['total_files'] == stats['processed_files'] + stats['skipped_files']


@pytest.fixture
def temp_dir():
    """Create a temporary directory with test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Copy sample PDFs to temp directory
        sample_pdfs = [f for f in os.listdir(SAMPLE_PDFS_DIR) if f.endswith('.pdf')]
        assert len(sample_pdfs) > 0, "No PDF files found in sample directory"
        
        # Копируем первый PDF файл как test1.pdf
        src = os.path.join(SAMPLE_PDFS_DIR, sample_pdfs[0])
        dst = os.path.join(temp_dir, "test1.pdf")
        shutil.copy2(src, dst)
        
        # Create test DOC files
        create_test_file(os.path.join(temp_dir, "test2.doc"), "test content")
        create_test_file(os.path.join(temp_dir, "test3.docx"), "test content")
        create_test_file(os.path.join(temp_dir, "test4.txt"), "test content")
        
        # Create nested directory
        nested_dir = os.path.join(temp_dir, "nested")
        os.makedirs(nested_dir)
        
        # Копируем второй PDF файл в nested директорию
        if len(sample_pdfs) > 1:
            src = os.path.join(SAMPLE_PDFS_DIR, sample_pdfs[1])
        else:
            src = os.path.join(SAMPLE_PDFS_DIR, sample_pdfs[0])
        dst = os.path.join(nested_dir, "nested1.pdf")
        shutil.copy2(src, dst)
        
        create_test_file(os.path.join(nested_dir, "nested2.doc"), "test content")
        
        yield temp_dir


def test_file_info_creation(temp_dir):
    """Test FileInfo creation from path."""
    file_path = os.path.join(temp_dir, "test1.pdf")
    file_info = FileInfo.from_path(temp_dir, file_path)
    
    # На macOS пути могут начинаться с /private
    expected_path = os.path.abspath(file_path)
    if os.path.exists('/private' + expected_path):
        expected_path = '/private' + expected_path
    
    assert file_info.absolute_path == expected_path
    assert file_info.relative_path == "test1.pdf"
    assert file_info.extension == ".pdf"
    assert file_info.size > 0
    assert isinstance(file_info.last_modified, datetime)
    assert file_info.is_accessible


def test_file_collector_initialization(temp_dir):
    """Test FileCollector initialization."""
    collector = FileCollector(str(temp_dir))
    assert collector.root_path == os.path.abspath(temp_dir)
    assert collector.allowed_extensions == {'.pdf', '.doc', '.docx'}
    assert collector.validate_content is True
    assert collector.skip_unreadable is False

    # Test invalid path
    with pytest.raises(PathValidationError) as exc_info:
        FileCollector("/nonexistent/path")
    assert "does not exist" in str(exc_info.value)


def test_file_collection_with_validation(temp_dir):
    """Test file collection process with content validation."""
    collector = FileCollector(str(temp_dir), validate_content=True)
    files = list(collector.collect_files())  # Convert generator to list
    
    # Should find valid PDF and DOC files
    assert len(files) > 0
    for file_info in files:
        assert isinstance(file_info, FileInfo)
        if collector.validate_content:
            assert file_info.validation_result is not None


def test_file_collection_without_validation(temp_dir):
    """Test file collection process without content validation."""
    collector = FileCollector(str(temp_dir), validate_content=False)
    files = list(collector.collect_files())  # Convert generator to list
    
    # Should find all files with allowed extensions
    assert len(files) > 0
    for file_info in files:
        assert isinstance(file_info, FileInfo)
        assert file_info.validation_result is None


def test_unreadable_files(temp_dir):
    """Test handling of unreadable files."""
    if os.name != 'nt':  # Skip on Windows
        # Create an unreadable file
        file_path = os.path.join(temp_dir, "unreadable.pdf")
        create_test_file(file_path, mode=0)
        
        # Test with skip_unreadable=True
        collector = FileCollector(str(temp_dir), skip_unreadable=True)
        files = list(collector.collect_files())  # Convert generator to list
        assert not any(f.absolute_path == file_path for f in files)
        
        # Test with skip_unreadable=False
        collector = FileCollector(str(temp_dir), skip_unreadable=False)
        files = list(collector.collect_files())  # Convert generator to list
        unreadable_files = [f for f in files if f.absolute_path == file_path]
        assert len(unreadable_files) == 0  # Файл не должен быть собран, так как недоступен
        
        # Cleanup
        os.chmod(file_path, 0o644)


def test_file_type_statistics(temp_dir):
    """Test file type statistics collection."""
    collector = FileCollector(str(temp_dir), validate_content=True)
    list(collector.collect_files())  # Consume generator to update statistics
    
    stats = collector.get_statistics()
    
    # Проверяем общую статистику
    assert stats['total_files'] > 0
    assert stats['processed_files'] > 0
    assert stats['skipped_files'] >= 0
    assert stats['error_count'] >= 0
    
    # Проверяем статистику по типам файлов
    file_types = stats.get('file_types', {})
    assert len(file_types) > 0
    
    # Проверяем что есть статистика хотя бы для одного типа файлов
    has_file_type_stats = False
    for type_stats in file_types.values():
        if type_stats.get('total', 0) > 0:
            has_file_type_stats = True
            break
    assert has_file_type_stats, "No file type statistics found"


def test_nested_directories(temp_dir):
    """Test file collection from nested directories."""
    collector = FileCollector(str(temp_dir))
    files = list(collector.collect_files())  # Convert generator to list
    
    # Check that files from nested directories were collected
    nested_files = [f for f in files if "nested" in f.relative_path]
    assert len(nested_files) > 0


def test_custom_extensions(temp_dir):
    """Test custom file extensions."""
    # Create a test txt file
    txt_file = os.path.join(temp_dir, "test.txt")
    create_test_file(txt_file, "test content")
    
    collector = FileCollector(
        str(temp_dir),
        allowed_extensions={'.txt'},
        validate_content=False  # Disable validation for .txt
    )
    files = list(collector.collect_files())  # Convert generator to list
    
    # Should only find .txt files
    assert len(files) > 0
    assert all(f.extension == '.txt' for f in files)


def test_statistics_accuracy(temp_dir):
    """Test accuracy of collection statistics."""
    collector = FileCollector(str(temp_dir), validate_content=True)
    files = list(collector.collect_files())  # Convert generator to list
    
    stats = collector.get_statistics()
    
    # Basic statistics
    assert stats['total_files'] > 0
    assert stats['processed_files'] == len(files)
    assert stats['total_files'] >= stats['processed_files']
    assert stats['total_files'] == stats['processed_files'] + stats['skipped_files']


def test_real_pdf_collection(temp_dir):
    """Test collection of real PDF files."""
    # Copy sample PDFs to temp directory
    sample_pdfs = [f for f in os.listdir(SAMPLE_PDFS_DIR) if f.endswith('.pdf')]
    assert len(sample_pdfs) > 0, "No PDF files found in sample directory"
    
    # Копируем первый PDF файл как test1.pdf
    src = os.path.join(SAMPLE_PDFS_DIR, sample_pdfs[0])
    dst = os.path.join(temp_dir, "test1.pdf")
    shutil.copy2(src, dst)
    
    # Проверяем что файл скопировался
    assert os.path.exists(dst), "PDF file was not copied to temp directory"
    assert os.path.getsize(dst) > 0, "Copied PDF file is empty"
    
    collector = FileCollector(str(temp_dir), validate_content=True)
    files = list(collector.collect_files())  # Convert generator to list
    
    # Check that PDFs were collected and validated
    pdf_files = [f for f in files if f.extension == '.pdf']
    assert len(pdf_files) > 0, "No PDF files were collected"
    
    for file_info in pdf_files:
        assert file_info.validation_result is not None, \
            f"No validation result for {file_info.relative_path}"
        assert file_info.validation_result.is_readable, \
            f"PDF file {file_info.relative_path} is not readable: {file_info.validation_result.error_message}"
        assert file_info.validation_result.is_valid, \
            f"PDF file {file_info.relative_path} is not valid: {file_info.validation_result.error_message}"
        assert file_info.validation_result.file_type == FileType.PDF, \
            f"Wrong file type for {file_info.relative_path}: {file_info.validation_result.file_type}"
        assert file_info.validation_result.mime_type == 'application/pdf', \
            f"Wrong MIME type for {file_info.relative_path}: {file_info.validation_result.mime_type}"
        assert file_info.validation_result.metadata.get('page_count', 0) > 0, \
            f"No pages found in {file_info.relative_path}"


class TestFileCollectorIntegration:
    """Integration test cases for FileCollector class."""

    @pytest.fixture
    def test_dir(self):
        """Create a temporary directory with test files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Copy sample PDFs to temp directory
            sample_pdfs = [f for f in os.listdir(SAMPLE_PDFS_DIR) if f.endswith('.pdf')]
            assert len(sample_pdfs) > 0, "No PDF files found in sample directory"
            
            # Copy first PDF file as test1.pdf
            src = os.path.join(SAMPLE_PDFS_DIR, sample_pdfs[0])
            dst = os.path.join(temp_dir, "test1.pdf")
            shutil.copy2(src, dst)
            
            # Create test DOC files
            create_test_file(os.path.join(temp_dir, "test2.doc"))
            create_test_file(os.path.join(temp_dir, "test3.docx"))
            create_test_file(os.path.join(temp_dir, "test4.txt"))
            
            # Create nested directory
            nested_dir = os.path.join(temp_dir, "nested")
            os.makedirs(nested_dir)
            
            # Copy second PDF file to nested directory
            if len(sample_pdfs) > 1:
                src = os.path.join(SAMPLE_PDFS_DIR, sample_pdfs[1])
            else:
                src = os.path.join(SAMPLE_PDFS_DIR, sample_pdfs[0])
            dst = os.path.join(nested_dir, "nested1.pdf")
            shutil.copy2(src, dst)
            
            create_test_file(os.path.join(nested_dir, "nested2.doc"))
            
            yield temp_dir

    @pytest.mark.integration
    def test_file_collection_with_validation(self, test_dir):
        """Integration test for file collection with content validation."""
        collector = FileCollector(test_dir, validate_content=True)
        files = list(collector.collect_files())
        
        # Check that only valid files were collected
        assert len(files) > 0
        for file_info in files:
            assert isinstance(file_info, FileInfo)
            assert file_info.validation_result is not None
            assert file_info.is_accessible

    @pytest.mark.integration
    def test_nested_directories(self, test_dir):
        """Integration test for file collection from nested directories."""
        collector = FileCollector(test_dir)
        files = list(collector.collect_files())
        
        # Check that files from nested directories were collected
        nested_files = [f for f in files if "nested" in f.relative_path]
        assert len(nested_files) > 0

    @pytest.mark.integration
    def test_file_type_statistics(self, test_dir):
        """Integration test for file type statistics collection."""
        collector = FileCollector(test_dir, validate_content=True)
        list(collector.collect_files())  # Consume generator to update statistics
        
        stats = collector.get_statistics()
        
        # Check general statistics
        assert stats['total_files'] > 0
        assert stats['processed_files'] > 0
        assert 'file_types' in stats
        
        # Check file type distribution
        file_types = stats['file_types']
        assert '.pdf' in file_types
        assert '.doc' in file_types
        assert '.docx' in file_types

    @pytest.mark.integration
    def test_file_permissions(self, test_dir):
        """Integration test for file permissions handling."""
        if os.name != 'nt':  # Skip on Windows
            # Create file without read permissions
            no_access_file = os.path.join(test_dir, "no_access.pdf")
            create_test_file(no_access_file, mode=0)
            
            collector = FileCollector(test_dir)
            files = list(collector.collect_files())
            
            # Check that file without permissions is not included
            assert not any(f.path == no_access_file for f in files)
            
            # Cleanup
            os.chmod(no_access_file, 0o644)

    @pytest.mark.integration
    def test_large_file_handling(self, test_dir):
        """Integration test for handling large files."""
        # Create a large file
        large_file = os.path.join(test_dir, "large.pdf")
        with open(large_file, 'wb') as f:
            f.write(b'0' * (1024 * 1024 * 10))  # 10MB file
        
        collector = FileCollector(test_dir, max_file_size=1024 * 1024)  # 1MB limit
        files = list(collector.collect_files())
        
        # Check that large file is not included
        assert not any(f.path == large_file for f in files)

    @pytest.mark.integration
    def test_file_collection_with_custom_extensions(self, test_dir):
        """Integration test for file collection with custom extensions."""
        collector = FileCollector(test_dir, allowed_extensions={'.txt'})
        files = list(collector.collect_files())
        
        # Check that only .txt files were collected
        assert all(f.extension == '.txt' for f in files)
        assert len(files) > 0

    @pytest.mark.integration
    def test_file_collection_with_skip_unreadable(self, test_dir):
        """Integration test for file collection with skip_unreadable option."""
        if os.name != 'nt':  # Skip on Windows
            # Create unreadable file
            unreadable_file = os.path.join(test_dir, "unreadable.pdf")
            create_test_file(unreadable_file, mode=0)
            
            collector = FileCollector(test_dir, skip_unreadable=True)
            files = list(collector.collect_files())
            
            # Check that unreadable file is skipped
            assert not any(f.path == unreadable_file for f in files)
            
            # Cleanup
            os.chmod(unreadable_file, 0o644) 