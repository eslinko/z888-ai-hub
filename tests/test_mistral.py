import pytest
import os
from z888_ai_hub.client.ai_client import AIClient
from z888_ai_hub.utils.logging_utils import setup_logger
from z888_ai_hub.connectors.mistral import MistralConnector

@pytest.fixture
def ai_client():
    """Fixture to initialize AIClient for testing."""
    return AIClient()

@pytest.fixture
def mistral_connector():
    """Fixture to initialize MistralConnector for testing."""
    return MistralConnector()

@pytest.fixture
def logger():
    """Fixture to provide configured logger."""
    return setup_logger('TestMistral', log_to_file=True)

@pytest.fixture
def pdf_samples_dir():
    """Fixture to provide path to sample PDFs directory."""
    return "tests/sample_pdfs"

@pytest.mark.asyncio
@pytest.mark.parametrize("pdf_file", [
    "2.1 - EN - MKD Plus leaflet black 240809001.pdf",
    "3.1 - EN- MKD Premium 30 leaflet black 240809001.pdf",
    "4.2 -EN - MKD Premium +DHA 132x74mm_Blister.pdf",
    "Math.pdf",
    "Med_6.3.pdf"
])
async def test_mistral_ocr(mistral_connector, logger, pdf_samples_dir, pdf_file):
    """
    Tests OCR text extraction from multiple PDFs using MistralConnector.
    """
    pdf_path = os.path.join(pdf_samples_dir, pdf_file)
    assert os.path.exists(pdf_path), f"Test file {pdf_path} not found!"

    # Step 1: Upload PDF and get signed URL
    logger.info(f"Uploading PDF file: {pdf_file}")

    # Step 2: Extract text using OCR
    logger.info(f"Starting OCR extraction for {pdf_file}")
    extracted_text = await mistral_connector.extract_text(pdf_path)
    
    assert isinstance(extracted_text, str), "OCR output should be a string"
    assert len(extracted_text) > 0, "OCR output should not be empty"

    # Добавляем подробную статистику
    total_chars = len(extracted_text)
    total_lines = len(extracted_text.splitlines())
    logger.info(f"OCR статистика для {pdf_file}:")
    logger.info(f"- Всего символов: {total_chars}")
    logger.info(f"- Всего строк: {total_lines}")
    logger.info(f"- Первые 500 символов: {extracted_text[:500]}...")
    logger.info(f"- Последние 500 символов: {extracted_text[-500:] if len(extracted_text) > 500 else extracted_text}")

@pytest.mark.asyncio
async def test_upload_pdf_to_mistral(mistral_connector, logger, pdf_samples_dir):
    """
    Tests PDF upload functionality to Mistral API.
    """
    pdf_file = "Med_6.3.pdf"
    pdf_path = os.path.join(pdf_samples_dir, pdf_file)
    
    assert os.path.exists(pdf_path), f"Test file {pdf_path} not found!"

    logger.info(f"Testing PDF upload for: {pdf_file}")
    signed_url = await mistral_connector.upload_pdf_to_mistral(pdf_path)
    
    assert signed_url is not None, "Failed to get signed URL"
    assert isinstance(signed_url, str), "Signed URL should be a string"
    assert signed_url.startswith("https://"), "Signed URL should be a valid HTTPS URL"
    
    logger.info(f"Successfully got signed URL for {pdf_file}: {signed_url}")
