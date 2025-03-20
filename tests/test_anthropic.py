import pytest
from z888_ai_hub.client.ai_client import AIClient
from z888_ai_hub.utils.logging_utils import setup_logger

@pytest.fixture
def ai_client():
    """Fixture to initialize AIClient for testing."""
    return AIClient()

def test_anthropic_generate_text(ai_client):
    """Tests text generation using AnthropicConnector."""
    prompt = "What is the circle of life?"
    response = ai_client.generate_text(prompt)
    
    assert isinstance(response, str), "Response should be a string"
    assert len(response) > 0, "Response should not be empty"

def test_anthropic_summarize_text(ai_client):
    """Tests summarization using AnthropicConnector."""
    logger = setup_logger('TestAnthropic')
    
    text = "Представь, что глобус – это настоящий шарик, а карта – плоский лист бумаги. На шарике всё расположено так, как на Земле: Гренландия маленькая, как и должна быть. Но когда мы переносим этот шарик на плоскую бумагу, приходится немного «растягивать» и «сжимать» разные части, чтобы всё уместилось. Один из способов сделать карту называется проекция Меркатора, и он немного увеличивает размеры мест, которые находятся далеко от экватора, как Гренландия. Поэтому на карте Гренландия выглядит намного больше, чем на глобусе, хотя на самом деле она меньше, чем Индия."
    summary = ai_client.summarize_text(text, max_length=50)
    
    logger.info(f"Generated summary: {summary}")
    logger.info(f"Summary length: {len(summary)} characters")
    logger.info(f"Summary: {summary}")
    
    assert isinstance(summary, str), "Summary should be a string"
    assert len(summary) <= 50, "Summary should not exceed max_length"
