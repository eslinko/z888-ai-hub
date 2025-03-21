"""
Unit tests for Telegram image processing utilities.
"""

import os
import pytest
from unittest.mock import Mock, patch
from PIL import Image
from z888_ai_hub.telegram.utils.image import validate_image

class TestTelegramImageUtilsUnit:
    """Unit test cases for Telegram image processing utilities."""

    @pytest.fixture
    def mock_image(self):
        """Create a mock PIL Image."""
        mock = Mock(spec=Image.Image)
        mock.verify.return_value = None
        return mock

    def test_validate_image_valid(self, mock_image):
        """Test validation of valid image."""
        with patch('PIL.Image.open', return_value=mock_image):
            is_valid = validate_image('/test/valid.png')
            assert is_valid

    def test_validate_image_invalid(self):
        """Test validation of invalid image."""
        with patch('PIL.Image.open', side_effect=Exception('Invalid image')):
            is_valid = validate_image('/test/invalid.png')
            assert not is_valid

    def test_validate_image_nonexistent(self):
        """Test validation of nonexistent image."""
        with patch('PIL.Image.open', side_effect=FileNotFoundError('File not found')):
            is_valid = validate_image('/test/nonexistent.png')
            assert not is_valid

    def test_validate_image_permission_error(self):
        """Test validation of image with permission error."""
        with patch('PIL.Image.open', side_effect=PermissionError('Permission denied')):
            is_valid = validate_image('/test/no_permission.png')
            assert not is_valid

    def test_validate_image_verify_error(self, mock_image):
        """Test validation of image that fails verification."""
        mock_image.verify.side_effect = Exception('Verification failed')
        with patch('PIL.Image.open', return_value=mock_image):
            is_valid = validate_image('/test/corrupted.png')
            assert not is_valid

    def test_validate_image_context_manager(self, mock_image):
        """Test that image is properly closed after validation."""
        with patch('PIL.Image.open', return_value=mock_image) as mock_open:
            validate_image('/test/valid.png')
            mock_open.assert_called_once_with('/test/valid.png')
            mock_image.close.assert_called_once() 