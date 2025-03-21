"""
Integration tests for Telegram chat parser.
"""

import os
import pytest
from PIL import Image
from z888_ai_hub.telegram.parser import TelegramChatParser
from z888_ai_hub.telegram.models import TelegramMessage, TelegramChat, ProcessingResult
from z888_ai_hub.connectors.mistral import MistralConnector

class TestTelegramParserIntegration:
    """Integration test cases for Telegram chat parser."""

    @pytest.fixture
    def temp_dir(tmp_path):
        """Create temporary directory for test files."""
        return tmp_path

    @pytest.fixture
    def sample_images(self, temp_dir):
        """Create sample image files for testing."""
        images = {
            'chat1.png': temp_dir / "chat1.png",
            'chat2.png': temp_dir / "chat2.png",
            'chat3.png': temp_dir / "chat3.png"
        }
        
        # Create test images with text
        for name, path in images.items():
            img = Image.new('RGB', (800, 600), color='white')
            img.save(path)
        
        return images

    @pytest.fixture
    def ocr_connector(self):
        """Create OCR connector for testing."""
        return MistralConnector(
            api_key=os.getenv('MISTRAL_API_KEY', 'test_key'),
            base_url=os.getenv('MISTRAL_BASE_URL', 'https://api.mistral.ai'),
            default_model="mistral-tiny"
        )

    @pytest.fixture
    def parser(self, ocr_connector):
        """Create parser instance with OCR connector."""
        return TelegramChatParser(ocr_connector)

    @pytest.mark.asyncio
    async def test_process_directory_with_real_images(self, parser, sample_images):
        """Test processing directory with real images."""
        result = await parser.process_directory(str(sample_images['chat1.png'].parent))
        
        assert result.success
        assert result.total_images == 3
        assert result.processed_images > 0
        assert isinstance(result.chat, TelegramChat)
        assert len(result.chat.messages) > 0

    @pytest.mark.asyncio
    async def test_process_single_image_with_real_ocr(self, parser, sample_images):
        """Test processing single image with real OCR."""
        messages = await parser._process_single_image(str(sample_images['chat1.png']), 0)
        
        assert len(messages) > 0
        assert all(isinstance(msg, TelegramMessage) for msg in messages)
        assert all(msg.image_order == 0 for msg in messages)

    @pytest.mark.asyncio
    async def test_parse_real_telegram_screenshot(self, parser):
        """Test parsing real Telegram screenshot."""
        screenshot_path = "tests/sample_files/images/telegram_screenshot.png"
        
        if os.path.exists(screenshot_path):
            messages = await parser._process_single_image(screenshot_path, 0)
            
            assert len(messages) > 0
            assert all(isinstance(msg, TelegramMessage) for msg in messages)
            assert all(msg.sender for msg in messages)
            assert all(msg.text for msg in messages)
        else:
            pytest.skip("Telegram screenshot not found")

    @pytest.mark.asyncio
    async def test_process_directory_with_large_images(self, parser, temp_dir):
        """Test processing directory with large images."""
        # Create large test image
        large_image = temp_dir / "large.png"
        img = Image.new('RGB', (4000, 3000), color='white')
        img.save(large_image)
        
        result = await parser.process_directory(str(temp_dir))
        
        assert result.success
        assert result.total_images == 1
        assert result.processed_images > 0
        assert isinstance(result.chat, TelegramChat)

    @pytest.mark.asyncio
    async def test_process_directory_with_mixed_images(self, parser, sample_images, temp_dir):
        """Test processing directory with mixed image types."""
        # Create invalid image
        invalid_image = temp_dir / "invalid.png"
        with open(invalid_image, 'wb') as f:
            f.write(b'This is not an image')
        
        result = await parser.process_directory(str(temp_dir))
        
        assert result.success
        assert result.total_images == 4  # 3 valid + 1 invalid
        assert result.processed_images > 0
        assert result.failed_images > 0
        assert isinstance(result.chat, TelegramChat) 