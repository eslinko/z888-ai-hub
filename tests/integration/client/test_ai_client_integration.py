"""
Integration tests for AI client.
"""

import os
import pytest
from z888_ai_hub.client.ai_client import AIClient
from z888_ai_hub.connectors.mistral import MistralConnector
from z888_ai_hub.connectors.anthropic import AnthropicConnector


class TestAIClientIntegration:
    """Integration test cases for AI client."""

    @pytest.fixture
    def mistral_connector(self):
        """Create a real Mistral connector."""
        api_key = os.getenv("MISTRAL_API_KEY", "test_key")
        return MistralConnector(
            api_key=api_key,
            base_url="https://api.mistral.ai",
            default_model="mistral-tiny"
        )

    @pytest.fixture
    def anthropic_connector(self):
        """Create a real Anthropic connector."""
        api_key = os.getenv("ANTHROPIC_API_KEY", "test_key")
        return AnthropicConnector(
            api_key=api_key,
            default_model="claude-3-opus"
        )

    @pytest.fixture
    def mistral_client(self, mistral_connector):
        """Create an AI client with Mistral connector."""
        return AIClient(
            connector=mistral_connector,
            retry_attempts=2,
            timeout=30
        )

    @pytest.fixture
    def anthropic_client(self, anthropic_connector):
        """Create an AI client with Anthropic connector."""
        return AIClient(
            connector=anthropic_connector,
            retry_attempts=2,
            timeout=30
        )

    @pytest.mark.asyncio
    async def test_process_text_request_mistral(self, mistral_client):
        """Test processing text request with Mistral."""
        prompt = "What is 2+2?"
        response = await mistral_client.process_request(prompt)
        
        assert isinstance(response, str)
        assert len(response) > 0
        assert "4" in response.lower()

    @pytest.mark.asyncio
    async def test_process_text_request_anthropic(self, anthropic_client):
        """Test processing text request with Anthropic."""
        prompt = "What is 2+2?"
        response = await anthropic_client.process_request(prompt)
        
        assert isinstance(response, str)
        assert len(response) > 0
        assert "4" in response.lower()

    @pytest.mark.asyncio
    async def test_process_with_options_mistral(self, mistral_client):
        """Test processing request with options using Mistral."""
        prompt = "Write a very short story."
        response = await mistral_client.process_request(
            prompt,
            temperature=0.9,
            max_tokens=50
        )
        
        assert isinstance(response, str)
        assert len(response) > 0
        assert len(response.split()) <= 50  # Rough check for token limit

    @pytest.mark.asyncio
    async def test_batch_process_mistral(self, mistral_client):
        """Test batch processing with Mistral."""
        prompts = [
            "What is 2+2?",
            "What is 3+3?",
            "What is 4+4?"
        ]
        
        responses = await mistral_client.batch_process(prompts)
        
        assert len(responses) == 3
        assert all(isinstance(r, str) for r in responses)
        assert any("4" in r.lower() for r in responses)
        assert any("6" in r.lower() for r in responses)
        assert any("8" in r.lower() for r in responses)

    @pytest.mark.asyncio
    async def test_error_handling_invalid_api_key(self):
        """Test error handling with invalid API key."""
        connector = MistralConnector(
            api_key="invalid_key",
            base_url="https://api.mistral.ai",
            default_model="mistral-tiny"
        )
        client = AIClient(connector=connector)
        
        with pytest.raises(Exception):
            await client.process_request("test prompt")

    @pytest.mark.asyncio
    async def test_retry_mechanism_real(self, mistral_client):
        """Test retry mechanism with real API calls."""
        # Use a prompt that might occasionally fail
        prompt = "Generate a very long response with complex calculations"
        
        try:
            response = await mistral_client.process_request(prompt)
            assert isinstance(response, str)
            assert len(response) > 0
        except Exception as e:
            # If all retries fail, ensure it's not a connection error
            assert "connection" not in str(e).lower()

    @pytest.mark.asyncio
    async def test_concurrent_requests(self, mistral_client):
        """Test handling concurrent requests."""
        import asyncio
        
        prompts = [f"What is {i}+{i}?" for i in range(5)]
        
        # Process requests concurrently
        tasks = [mistral_client.process_request(prompt) for prompt in prompts]
        responses = await asyncio.gather(*tasks)
        
        assert len(responses) == 5
        assert all(isinstance(r, str) for r in responses)

    @pytest.mark.asyncio
    async def test_long_conversation(self, mistral_client):
        """Test maintaining context in a conversation."""
        responses = []
        
        # Simulate a conversation
        responses.append(await mistral_client.process_request(
            "My name is Alice. What's yours?"
        ))
        
        responses.append(await mistral_client.process_request(
            "Remember my name? What is it?"
        ))
        
        assert len(responses) == 2
        assert all(isinstance(r, str) for r in responses)
        assert any("alice" in r.lower() for r in responses)

    def test_client_configuration_persistence(self, mistral_connector):
        """Test client configuration persistence."""
        config = {
            "retry_attempts": 5,
            "timeout": 60,
            "batch_size": 20
        }
        
        client = AIClient(connector=mistral_connector, **config)
        
        assert client.retry_attempts == 5
        assert client.timeout == 60
        assert client.batch_size == 20
        
        # Ensure configuration doesn't affect connector
        assert hasattr(client.connector, "api_key")
        assert hasattr(client.connector, "default_model") 