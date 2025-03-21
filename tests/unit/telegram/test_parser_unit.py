"""
Unit tests for Telegram chat parser.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from z888_ai_hub.telegram.parser import TelegramChatParser
from z888_ai_hub.telegram.models import TelegramMessage, TelegramChat, ProcessingResult

class TestTelegramParserUnit:
    """Unit test cases for Telegram chat parser."""

    @pytest.fixture
    def mock_ocr_connector(self):
        """Create a mock OCR connector."""
        mock = Mock()
        mock.extract_text.return_value = "John: Hello! 12:34\nJane: Hi there! 12:35"
        return mock

    @pytest.fixture
    def parser(self, mock_ocr_connector):
        """Create parser instance with mock OCR connector."""
        return TelegramChatParser(mock_ocr_connector)

    @pytest.mark.asyncio
    async def test_process_directory_empty(self, parser):
        """Test processing empty directory."""
        result = await parser.process_directory("/empty/dir")
        assert not result.success
        assert result.error == "No valid images found in directory"
        assert result.total_images == 0
        assert result.processed_images == 0
        assert result.failed_images == 0

    @pytest.mark.asyncio
    async def test_process_directory_with_images(self, parser, mock_ocr_connector):
        """Test processing directory with valid images."""
        with patch('z888_ai_hub.telegram.utils.image.get_images_in_directory') as mock_get_images:
            mock_get_images.return_value = ["image1.png", "image2.png"]
            
            result = await parser.process_directory("/test/dir")
            
            assert result.success
            assert result.total_images == 2
            assert result.processed_images == 2
            assert result.failed_images == 0
            assert isinstance(result.chat, TelegramChat)
            assert len(result.chat.messages) == 4  # 2 messages per image

    @pytest.mark.asyncio
    async def test_process_directory_with_failed_images(self, parser, mock_ocr_connector):
        """Test processing directory with some failed images."""
        with patch('z888_ai_hub.telegram.utils.image.get_images_in_directory') as mock_get_images:
            mock_get_images.return_value = ["image1.png", "image2.png", "image3.png"]
            mock_ocr_connector.extract_text.side_effect = [
                "John: Hello! 12:34\nJane: Hi there! 12:35",
                Exception("OCR failed"),
                "John: Back! 12:36"
            ]
            
            result = await parser.process_directory("/test/dir")
            
            assert result.success
            assert result.total_images == 3
            assert result.processed_images == 2
            assert result.failed_images == 1
            assert isinstance(result.chat, TelegramChat)
            assert len(result.chat.messages) == 3  # 2 messages from first image + 1 from third

    def test_parse_message_text(self, parser):
        """Test parsing message text."""
        text = "John: Hello! 12:34 https://example.com"
        parsed = parser._parse_message_text(text)
        
        assert parsed['sender'] == "John"
        assert parsed['text'] == "Hello! 12:34"
        assert parsed['links'] == ["https://example.com"]
        assert isinstance(parsed['timestamp'], datetime)

    def test_extract_metadata(self, parser):
        """Test extracting metadata from message text."""
        text = "John: Hello! 12:34"
        metadata = parser._extract_metadata(text)
        
        assert metadata['sender'] == "John"
        assert isinstance(metadata['timestamp'], datetime)

    def test_extract_links(self, parser):
        """Test extracting links from message text."""
        text = "Check https://example.com and www.test.com"
        links = parser._extract_links(text)
        
        assert len(links) == 2
        assert "https://example.com" in links
        assert "www.test.com" in links

    @pytest.mark.asyncio
    async def test_process_single_image(self, parser, mock_ocr_connector):
        """Test processing single image."""
        messages = await parser._process_single_image("test.png", 0)
        
        assert len(messages) == 2
        assert all(isinstance(msg, TelegramMessage) for msg in messages)
        assert all(msg.image_order == 0 for msg in messages)
        assert messages[0].sender == "John"
        assert messages[1].sender == "Jane" 