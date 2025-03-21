"""
Integration tests for Anthropic connector.
"""

import os
import pytest
from z888_ai_hub.connectors.anthropic import AnthropicConnector
from z888_ai_hub.utils.logging_utils import setup_logger

logger = setup_logger('TestAnthropicConnectorIntegration')

@pytest.fixture(scope="session")
def anthropic_connector():
    """Создает экземпляр Anthropic коннектора для тестов."""
    return AnthropicConnector(
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        base_url=os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
    )

@pytest.mark.integration
@pytest.mark.asyncio
async def test_generate_summary_with_real_api(anthropic_connector):
    """Тестирует генерацию резюме с реальным API."""
    test_text = """
    This is a test document that contains multiple paragraphs.
    The document discusses various topics and should be summarized.
    The summary should capture the main points and key information.
    """
    
    summary = await anthropic_connector.generate_summary(test_text)
    
    assert summary is not None
    assert isinstance(summary, str)
    assert len(summary) > 0
    assert len(summary) < len(test_text)

@pytest.mark.integration
@pytest.mark.asyncio
async def test_vectorize_text_with_real_api(anthropic_connector):
    """Тестирует векторизацию текста с реальным API."""
    test_text = """
    This is a test document that will be vectorized.
    The vector should represent the semantic meaning of the text.
    """
    
    vector = await anthropic_connector.vectorize_text(test_text)
    
    assert vector is not None
    assert isinstance(vector, list)
    assert len(vector) > 0
    assert all(isinstance(x, float) for x in vector)

@pytest.mark.integration
@pytest.mark.asyncio
async def test_generate_summary_with_long_text(anthropic_connector):
    """Тестирует генерацию резюме для длинного текста."""
    test_text = """
    This is a very long test document that contains many paragraphs.
    Each paragraph discusses different aspects of the topic.
    The document includes various details and examples.
    The summary should capture the main points and key information.
    The text is intentionally long to test the API's ability to handle large inputs.
    The document structure includes multiple sections and subsections.
    Each section contains relevant information that should be included in the summary.
    The test verifies that the API can process and summarize long documents effectively.
    """
    
    summary = await anthropic_connector.generate_summary(test_text)
    
    assert summary is not None
    assert isinstance(summary, str)
    assert len(summary) > 0
    assert len(summary) < len(test_text)

@pytest.mark.integration
@pytest.mark.asyncio
async def test_vectorize_text_with_special_characters(anthropic_connector):
    """Тестирует векторизацию текста со специальными символами."""
    test_text = """
    This is a test document with special characters: !@#$%^&*()
    The text includes various punctuation marks and symbols.
    The vector should still represent the semantic meaning correctly.
    """
    
    vector = await anthropic_connector.vectorize_text(test_text)
    
    assert vector is not None
    assert isinstance(vector, list)
    assert len(vector) > 0
    assert all(isinstance(x, float) for x in vector)

@pytest.mark.integration
@pytest.mark.asyncio
async def test_generate_summary_with_multiple_languages(anthropic_connector):
    """Тестирует генерацию резюме для текста на разных языках."""
    test_text = """
    This is a test document in English.
    Ceci est un document de test en français.
    Это тестовый документ на русском языке.
    """
    
    summary = await anthropic_connector.generate_summary(test_text)
    
    assert summary is not None
    assert isinstance(summary, str)
    assert len(summary) > 0
    assert len(summary) < len(test_text)

@pytest.mark.integration
@pytest.mark.asyncio
async def test_handle_api_rate_limits(anthropic_connector):
    """Тестирует обработку ограничений API."""
    test_text = "Test document for rate limiting"
    
    # Делаем несколько запросов подряд
    for _ in range(5):
        summary = await anthropic_connector.generate_summary(test_text)
        assert summary is not None
        assert isinstance(summary, str)
        assert len(summary) > 0 