"""
Tests for FileValidator class.
"""

import os
import pytest
from pathlib import Path
from z888_ai_hub.utils.file_validator import FileValidator, FileType, ValidationResult
from unittest.mock import Mock, patch
from z888_ai_hub.utils.logging_utils import setup_logger

logger = setup_logger('TestFileValidator')

# Пути к тестовым файлам
SAMPLE_PDFS_DIR = "tests/sample_pdfs"
TEST_PDF_FILE = "Med_6.3.pdf"
TEST_PDF_PATH = os.path.join(SAMPLE_PDFS_DIR, TEST_PDF_FILE)


@pytest.fixture
def validator():
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
    
    # Копируем реальный PDF файл
    with open(TEST_PDF_PATH, 'rb') as src, open(files['valid_pdf'], 'wb') as dst:
        dst.write(src.read())
    
    # Create invalid PDF
    files['invalid_pdf'].write_text("This is not a PDF file")
    
    # Create valid DOC
    files['valid_doc'].write_text("This is a test document")
    
    # Create valid TXT
    files['valid.txt'].write_text("A" * 200)  # Достаточно длинный текст
    
    # Create small TXT
    files['small.txt'].write_text("A" * 50)  # Слишком короткий текст
    
    # Create large PDF
    files['large.pdf'].write_bytes(b"X" * (11 * 1024 * 1024))  # 11MB
    
    # Create invalid DOC
    files['invalid_doc'].write_text("This is not a DOC file")
    
    # Create invalid EXE
    files['invalid.exe'].write_bytes(b"Invalid content")
    
    # Create unknown file
    files['unknown'].write_text("This is a text file")
    
    return files


def test_file_type_from_extension():
    """Test FileType.from_extension method."""
    assert FileType.from_extension('.pdf') == FileType.PDF
    assert FileType.from_extension('pdf') == FileType.PDF
    assert FileType.from_extension('.doc') == FileType.DOC
    assert FileType.from_extension('.docx') == FileType.DOC
    assert FileType.from_extension('.txt') == FileType.UNKNOWN


def test_validation_result_initialization():
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


def test_validate_pdf_file(validator, sample_files):
    """Test PDF file validation."""
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


def test_validate_doc_file(validator, sample_files):
    """Test DOC file validation."""
    # Test valid DOC
    result = validator.validate_file_sync(str(sample_files['valid_doc']))
    assert result.file_type == FileType.DOC
    
    # Test invalid DOC
    result = validator.validate_file_sync(str(sample_files['invalid_doc']))
    assert result.is_valid is False
    assert result.file_type == FileType.DOC
    assert result.is_readable is False
    assert result.error_message is not None


def test_validate_unknown_file(validator, sample_files):
    """Test unknown file validation."""
    result = validator.validate_file_sync(str(sample_files['unknown']))
    assert result.is_valid is False
    assert result.file_type == FileType.UNKNOWN
    assert result.is_readable is False
    assert result.error_message == "Unsupported file type"


def test_validate_nonexistent_file(validator):
    """Test validation of nonexistent file."""
    result = validator.validate_file_sync("/nonexistent/file.pdf")
    assert result.is_valid is False
    assert result.error_message is not None


def test_pdf_metadata(validator):
    """Test PDF metadata extraction."""
    result = validator.validate_file_sync(TEST_PDF_PATH)
    assert result.is_valid is True
    assert result.metadata is not None
    assert 'page_count' in result.metadata
    assert result.metadata['page_count'] > 0
    assert 'is_encrypted' in result.metadata
    assert 'pdf_version' in result.metadata


def test_multiple_pdf_files(validator):
    """Test validation of multiple PDF files."""
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


@pytest.fixture
def file_validator():
    """Создает экземпляр FileValidator с тестовыми настройками."""
    config = {
        "max_file_size_mb": 10,
        "supported_extensions": [".pdf", ".txt", ".doc"],
        "min_text_length": 100,
        "max_text_length": 1000000
    }
    return FileValidator(config)


@pytest.mark.asyncio
async def test_validate_file_type(file_validator, sample_files):
    """Тестирует валидацию типа файла."""
    # Проверяем поддерживаемые типы
    assert await file_validator.validate_file_type(str(sample_files["valid_pdf"]))
    assert await file_validator.validate_file_type(str(sample_files["valid.txt"]))
    
    # Проверяем неподдерживаемый тип
    assert not await file_validator.validate_file_type(str(sample_files["invalid.exe"]))


@pytest.mark.asyncio
async def test_validate_file_size(file_validator, sample_files):
    """Тестирует валидацию размера файла."""
    # Проверяем файл допустимого размера
    assert await file_validator.validate_file_size(str(sample_files["valid_pdf"]))
    
    # Проверяем слишком большой файл
    assert not await file_validator.validate_file_size(str(sample_files["large.pdf"]))


@pytest.mark.asyncio
async def test_validate_text_length(file_validator, sample_files):
    """Тестирует валидацию длины текста."""
    # Проверяем текст допустимой длины
    assert await file_validator.validate_text_length(str(sample_files["valid.txt"]))
    
    # Проверяем слишком короткий текст
    assert not await file_validator.validate_text_length(str(sample_files["small.txt"]))


@pytest.mark.asyncio
async def test_validate_file(file_validator, sample_files):
    """Тестирует полную валидацию файла."""
    # Проверяем валидный файл
    result = await file_validator.validate_file(str(sample_files["valid.txt"]))
    assert result["is_valid"]
    assert not result["errors"]
    
    # Проверяем невалидный файл
    result = await file_validator.validate_file(str(sample_files["invalid.exe"]))
    assert not result["is_valid"]
    assert "Unsupported file type" in result["errors"]


@pytest.mark.asyncio
async def test_error_handling(file_validator, temp_dir):
    """Тестирует обработку ошибок."""
    # Тест на несуществующий файл
    result = await file_validator.validate_file("nonexistent.pdf")
    assert not result["is_valid"]
    assert "File does not exist: nonexistent.pdf" in result["errors"]
    
    # Создаем тестовый файл для проверки прав доступа
    test_file = temp_dir / "test.pdf"
    test_file.write_text("Test content")
    
    # Тест на ошибку доступа к файлу
    with patch('os.access', return_value=False):
        result = await file_validator.validate_file(str(test_file))
        assert not result["is_valid"]
        assert "No read permission" in result["errors"]


@pytest.mark.asyncio
async def test_custom_validation_rules(temp_dir):
    """Тестирует пользовательские правила валидации."""
    # Создаем файл для тестирования
    test_file = temp_dir / "test.txt"
    test_file.write_text("A" * 50)  # 50 символов
    
    # Тестируем с разными настройками
    config = {
        "max_file_size_mb": 1,
        "supported_extensions": [".txt"],
        "min_text_length": 100,
        "max_text_length": 200
    }
    validator = FileValidator(config)
    
    result = await validator.validate_file(str(test_file))
    assert not result["is_valid"]
    assert "Text length is outside allowed range" in result["errors"]
    
    # Меняем настройки
    config["min_text_length"] = 10
    validator = FileValidator(config)
    
    result = await validator.validate_file(str(test_file))
    assert result["is_valid"]
    assert not result["errors"] 