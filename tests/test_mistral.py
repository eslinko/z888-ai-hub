import pytest
import os
from z888_ai_hub.client.ai_client import AIClient
from z888_ai_hub.utils.logging_utils import setup_logger

@pytest.fixture
def ai_client():
    """Fixture to initialize AIClient for testing."""
    return AIClient()

@pytest.fixture
def logger():
    """Fixture to provide configured logger."""
    return setup_logger('TestMistral', log_to_file=True)

@pytest.fixture
def pdf_samples_dir():
    """Fixture to provide path to sample PDFs directory."""
    return "tests/sample_pdfs"

@pytest.mark.integration
@pytest.mark.parametrize("pdf_file", [
    "2.1 - EN - MKD Plus leaflet black 240809001.pdf",
    "3.1 - EN- MKD Premium 30 leaflet black 240809001.pdf",
    "4.2 -EN - MKD Premium +DHA 132x74mm_Blister.pdf",
    "Math.pdf",
    "Med_6.3.pdf"
])
async def test_mistral_ocr_integration(ai_client, logger, pdf_samples_dir, pdf_file):
    """
    Integration test for OCR text extraction from multiple PDFs using Mistral.
    Tests the full pipeline from file upload to text extraction.
    """
    pdf_path = os.path.join(pdf_samples_dir, pdf_file)
    assert os.path.exists(pdf_path), f"Test file {pdf_path} not found!"

    logger.info(f"Starting OCR integration test for: {pdf_file}")
    
    # Extract text using OCR through AIClient
    extracted_text = await ai_client.extract_text_from_pdf(pdf_path)
    
    # Validate results
    assert isinstance(extracted_text, str), "OCR output should be a string"
    assert len(extracted_text) > 0, "OCR output should not be empty"

    # Log detailed statistics
    total_chars = len(extracted_text)
    total_lines = len(extracted_text.splitlines())
    logger.info(f"OCR statistics for {pdf_file}:")
    logger.info(f"- Total characters: {total_chars}")
    logger.info(f"- Total lines: {total_lines}")
    logger.info(f"- First 500 chars: {extracted_text[:500]}...")
    logger.info(f"- Last 500 chars: {extracted_text[-500:] if len(extracted_text) > 500 else extracted_text}")

@pytest.mark.integration
async def test_mistral_pdf_upload_integration(ai_client, logger, pdf_samples_dir):
    """
    Integration test for PDF upload functionality.
    Tests the complete upload process through AIClient.
    """
    pdf_file = "Med_6.3.pdf"
    pdf_path = os.path.join(pdf_samples_dir, pdf_file)
    
    assert os.path.exists(pdf_path), f"Test file {pdf_path} not found!"

    logger.info(f"Testing PDF upload integration for: {pdf_file}")
    
    # Upload PDF through AIClient
    signed_url = await ai_client.upload_pdf(pdf_path)
    
    # Validate results
    assert signed_url is not None, "Failed to get signed URL"
    assert isinstance(signed_url, str), "Signed URL should be a string"
    assert signed_url.startswith("https://"), "Signed URL should be a valid HTTPS URL"
    
    logger.info(f"Successfully uploaded PDF and got signed URL: {signed_url}")

@pytest.mark.integration
async def test_mistral_text_generation_integration(ai_client, logger):
    """
    Integration test for text generation using Mistral.
    Tests the complete text generation pipeline through AIClient.
    """
    prompt = "Explain the concept of quantum computing in simple terms."
    
    logger.info("Testing text generation integration")
    
    # Generate text through AIClient
    generated_text = await ai_client.generate_text(prompt)
    
    # Validate results
    assert isinstance(generated_text, str), "Generated text should be a string"
    assert len(generated_text) > 0, "Generated text should not be empty"
    
    logger.info(f"Successfully generated text of length: {len(generated_text)}")
