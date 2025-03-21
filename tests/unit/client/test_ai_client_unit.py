"""
Unit tests for AI client.
"""

import pytest
from unittest.mock import Mock, patch
from z888_ai_hub.client.ai_client import AIClient
from z888_ai_hub.connectors.base_connector import BaseConnector, ConnectorCapability


class TestAIClientUnit:
    """Unit test cases for AI client."""

    @pytest.fixture
    def mock_connector(self):
        """Create a mock connector."""
        mock = Mock(spec=BaseConnector)
        mock.capabilities = [ConnectorCapability.TEXT]
        mock.process.return_value = "test response"
        return mock

    @pytest.fixture
    def client(self, mock_connector):
        """Create an AI client with mock connector."""
        return AIClient(connector=mock_connector)

    @pytest.mark.asyncio
    async def test_process_request(self, client, mock_connector):
        """Test processing a simple request."""
        response = await client.process_request("test prompt")
        assert response == "test response"
        mock_connector.process.assert_called_once_with("test prompt")

    @pytest.mark.asyncio
    async def test_process_request_with_options(self, client, mock_connector):
        """Test processing request with additional options."""
        options = {"temperature": 0.7, "max_tokens": 100}
        await client.process_request("test prompt", **options)
        mock_connector.process.assert_called_once_with("test prompt", temperature=0.7, max_tokens=100)

    @pytest.mark.asyncio
    async def test_process_request_with_error(self, client, mock_connector):
        """Test handling connector errors."""
        mock_connector.process.side_effect = Exception("API Error")
        
        with pytest.raises(Exception, match="API Error"):
            await client.process_request("test prompt")

    def test_validate_connector(self):
        """Test connector validation during client initialization."""
        invalid_connector = Mock()  # Not a BaseConnector
        
        with pytest.raises(TypeError, match="Connector must be an instance of BaseConnector"):
            AIClient(connector=invalid_connector)

    def test_validate_connector_capabilities(self, mock_connector):
        """Test validation of connector capabilities."""
        # Remove TEXT capability
        mock_connector.capabilities = [ConnectorCapability.OCR]
        
        with pytest.raises(ValueError, match="Connector must support TEXT capability"):
            AIClient(connector=mock_connector)

    @pytest.mark.asyncio
    async def test_batch_process(self, client, mock_connector):
        """Test processing multiple requests in batch."""
        prompts = ["prompt1", "prompt2", "prompt3"]
        mock_connector.process.side_effect = [f"response{i}" for i in range(1, 4)]
        
        responses = await client.batch_process(prompts)
        assert len(responses) == 3
        assert responses == ["response1", "response2", "response3"]
        assert mock_connector.process.call_count == 3

    @pytest.mark.asyncio
    async def test_batch_process_with_errors(self, client, mock_connector):
        """Test batch processing with some failed requests."""
        prompts = ["prompt1", "prompt2", "prompt3"]
        mock_connector.process.side_effect = [
            "response1",
            Exception("API Error"),
            "response3"
        ]
        
        with pytest.raises(Exception, match="Some batch requests failed"):
            await client.batch_process(prompts)

    def test_client_configuration(self, mock_connector):
        """Test client configuration options."""
        config = {
            "retry_attempts": 3,
            "timeout": 30,
            "batch_size": 10
        }
        
        client = AIClient(connector=mock_connector, **config)
        assert client.retry_attempts == 3
        assert client.timeout == 30
        assert client.batch_size == 10

    @pytest.mark.asyncio
    async def test_process_with_retry(self, mock_connector):
        """Test request retry mechanism."""
        mock_connector.process.side_effect = [
            Exception("Temporary error"),
            Exception("Temporary error"),
            "success"
        ]
        
        client = AIClient(connector=mock_connector, retry_attempts=3)
        response = await client.process_request("test prompt")
        
        assert response == "success"
        assert mock_connector.process.call_count == 3

    @pytest.mark.asyncio
    async def test_process_with_retry_exhausted(self, mock_connector):
        """Test when all retry attempts are exhausted."""
        mock_connector.process.side_effect = Exception("Persistent error")
        
        client = AIClient(connector=mock_connector, retry_attempts=3)
        
        with pytest.raises(Exception, match="All retry attempts failed"):
            await client.process_request("test prompt")
        
        assert mock_connector.process.call_count == 3 