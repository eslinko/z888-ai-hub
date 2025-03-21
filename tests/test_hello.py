import os
import pytest
from z888_ai_hub.client.ai_client import AIClient
from z888_ai_hub.utils.logging_utils import setup_logger
from z888_ai_hub.utils.env_loader import load_env

# Настройка логгера для тестов
logger = setup_logger('TestHello')

# Константы
SAMPLE_PDFS_DIR = "tests/sample_pdfs"

@pytest.fixture
def ai_client():
    return AIClient()

def test_hello_world():
    """
    Простой тест для проверки инициализации и логирования
    """
    logger.info("Starting hello world test")
    message = "Hello, World!"
    logger.debug(f"Test message: {message}")
    assert message == "Hello, World!", "Basic assertion failed"
    logger.info("Hello world test completed successfully")

def test_api_keys():
    """
    Проверка наличия и валидности API ключей
    """
    logger.info("Starting API keys validation test")
    
    # Проверяем ANTHROPIC_API_KEY
    anthropic_key = load_env("ANTHROPIC_API_KEY")
    logger.debug("Checking ANTHROPIC_API_KEY...")
    assert anthropic_key is not None, "ANTHROPIC_API_KEY not found in environment"
    assert len(anthropic_key) > 0, "ANTHROPIC_API_KEY is empty"
    assert anthropic_key.startswith("sk-"), "ANTHROPIC_API_KEY should start with 'sk-'"
    logger.info("✅ ANTHROPIC_API_KEY is valid")
    
    # Проверяем MISTRAL_API_KEY
    mistral_key = load_env("MISTRAL_API_KEY")
    logger.debug("Checking MISTRAL_API_KEY...")
    assert mistral_key is not None, "MISTRAL_API_KEY not found in environment"
    assert len(mistral_key) > 0, "MISTRAL_API_KEY is empty"
    logger.info("✅ MISTRAL_API_KEY is valid")
    
    logger.info("All API keys are valid")

@pytest.mark.asyncio
async def test_pdf_files():
    """
    Проверка наличия и доступности PDF файлов для тестирования
    """
    logger.info("Starting PDF files check")
    
    # Создаем экземпляр AIClient
    client = AIClient()
    
    # Проверяем существование директории
    assert os.path.exists(SAMPLE_PDFS_DIR), f"Sample PDFs directory not found: {SAMPLE_PDFS_DIR}"
    logger.debug(f"Found sample PDFs directory: {SAMPLE_PDFS_DIR}")
    
    # Получаем список PDF файлов
    pdf_files = [f for f in os.listdir(SAMPLE_PDFS_DIR) if f.endswith(".pdf")]
    assert len(pdf_files) > 0, f"No PDF files found in {SAMPLE_PDFS_DIR}"
    
    logger.info(f"Found {len(pdf_files)} PDF files:")
    for pdf_file in pdf_files:
        pdf_path = os.path.join(SAMPLE_PDFS_DIR, pdf_file)
        # Проверяем доступ к файлу
        assert os.access(pdf_path, os.R_OK), f"Cannot read PDF file: {pdf_path}"
        logger.debug(f"✓ {pdf_file} - readable")
        logger.info("Starting text extraction...")
        extracted_text = await client.extract_text_from_image(pdf_path)
        assert extracted_text is not None and len(extracted_text) > 0, f"Failed to extract text from {pdf_file}"
    
    logger.info("✅ All PDF files are accessible and text extraction successful")