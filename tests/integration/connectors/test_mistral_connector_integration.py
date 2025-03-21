"""
Integration tests for Mistral connector.
"""

import os
import pytest
from z888_ai_hub.connectors.mistral import MistralConnector
from z888_ai_hub.utils.logging_utils import setup_logger

logger = setup_logger('TestMistralConnectorIntegration')

@pytest.fixture(scope="session")
def mistral_connector():
    """Создает экземпляр Mistral коннектора для тестов."""
    return MistralConnector(
        api_key=os.getenv("MISTRAL_API_KEY"),
        base_url=os.getenv("MISTRAL_BASE_URL", "https://api.mistral.ai")
    )

@pytest.mark.integration
@pytest.mark.asyncio
async def test_vectorize_text_with_real_api(mistral_connector):
    """Тестирует векторизацию текста с реальным API."""
    test_text = """
    This is a test document that will be vectorized.
    The vector should represent the semantic meaning of the text.
    The embedding should capture the key concepts and relationships.
    """
    
    vector = await mistral_connector.vectorize_text(test_text)
    
    assert vector is not None
    assert isinstance(vector, list)
    assert len(vector) > 0
    assert all(isinstance(x, float) for x in vector)

@pytest.mark.integration
@pytest.mark.asyncio
async def test_vectorize_text_with_long_text(mistral_connector):
    """Тестирует векторизацию длинного текста."""
    test_text = """
    This is a very long test document that contains many paragraphs.
    Each paragraph discusses different aspects of the topic.
    The document includes various details and examples.
    The vector should capture the semantic meaning of the entire text.
    The text is intentionally long to test the API's ability to handle large inputs.
    The document structure includes multiple sections and subsections.
    Each section contains relevant information that should be reflected in the vector.
    The test verifies that the API can process and vectorize long documents effectively.
    """
    
    vector = await mistral_connector.vectorize_text(test_text)
    
    assert vector is not None
    assert isinstance(vector, list)
    assert len(vector) > 0
    assert all(isinstance(x, float) for x in vector)

@pytest.mark.integration
@pytest.mark.asyncio
async def test_vectorize_text_with_special_characters(mistral_connector):
    """Тестирует векторизацию текста со специальными символами."""
    test_text = """
    This is a test document with special characters: !@#$%^&*()
    The text includes various punctuation marks and symbols.
    The vector should still represent the semantic meaning correctly.
    """
    
    vector = await mistral_connector.vectorize_text(test_text)
    
    assert vector is not None
    assert isinstance(vector, list)
    assert len(vector) > 0
    assert all(isinstance(x, float) for x in vector)

@pytest.mark.integration
@pytest.mark.asyncio
async def test_vectorize_text_with_multiple_languages(mistral_connector):
    """Тестирует векторизацию текста на разных языках."""
    test_text = """
    This is a test document in English.
    Ceci est un document de test en français.
    Это тестовый документ на русском языке.
    """
    
    vector = await mistral_connector.vectorize_text(test_text)
    
    assert vector is not None
    assert isinstance(vector, list)
    assert len(vector) > 0
    assert all(isinstance(x, float) for x in vector)

@pytest.mark.integration
@pytest.mark.asyncio
async def test_vectorize_text_with_code_snippets(mistral_connector):
    """Тестирует векторизацию текста с фрагментами кода."""
    test_text = """
    This is a test document that includes code snippets.
    
    def example_function():
        print("Hello, World!")
        
    class ExampleClass:
        def __init__(self):
            self.value = 42
            
    The vector should capture both the natural language and code structure.
    """
    
    vector = await mistral_connector.vectorize_text(test_text)
    
    assert vector is not None
    assert isinstance(vector, list)
    assert len(vector) > 0
    assert all(isinstance(x, float) for x in vector)

@pytest.mark.integration
@pytest.mark.asyncio
async def test_handle_api_rate_limits(mistral_connector):
    """Тестирует обработку ограничений API."""
    test_text = "Test document for rate limiting"
    
    # Делаем несколько запросов подряд
    for _ in range(5):
        vector = await mistral_connector.vectorize_text(test_text)
        assert vector is not None
        assert isinstance(vector, list)
        assert len(vector) > 0
        assert all(isinstance(x, float) for x in vector) 