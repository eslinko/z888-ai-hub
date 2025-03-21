"""
Integration tests for Telegram image processing utilities.
"""

import os
import pytest
from PIL import Image
from z888_ai_hub.telegram.utils.image import validate_image

class TestTelegramImageUtilsIntegration:
    """Integration test cases for Telegram image processing utilities."""

    @pytest.fixture
    def temp_dir(tmp_path):
        """Create temporary directory for test files."""
        return tmp_path

    @pytest.fixture
    def sample_images(self, temp_dir):
        """Create sample image files for testing."""
        images = {
            'valid_png': temp_dir / "valid.png",
            'valid_jpg': temp_dir / "valid.jpg",
            'invalid_png': temp_dir / "invalid.png",
            'large_png': temp_dir / "large.png",
            'corrupted_png': temp_dir / "corrupted.png"
        }
        
        # Create valid PNG image
        img = Image.new('RGB', (100, 100), color='red')
        img.save(images['valid_png'])
        
        # Create valid JPG image
        img = Image.new('RGB', (100, 100), color='blue')
        img.save(images['valid_jpg'])
        
        # Create invalid PNG image
        with open(images['invalid_png'], 'wb') as f:
            f.write(b'This is not an image')
        
        # Create large image
        img = Image.new('RGB', (5000, 5000), color='green')
        img.save(images['large_png'])
        
        # Create corrupted image
        with open(images['corrupted_png'], 'wb') as f:
            f.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x00\x00\x02\x00\x01\xe2\x21\xbc\x33\x00\x00\x00\x00IEND\xaeB`\x82')
        
        return images

    def test_validate_valid_png(self, sample_images):
        """Test validation of valid PNG image."""
        is_valid = validate_image(str(sample_images['valid_png']))
        assert is_valid

    def test_validate_valid_jpg(self, sample_images):
        """Test validation of valid JPG image."""
        is_valid = validate_image(str(sample_images['valid_jpg']))
        assert is_valid

    def test_validate_invalid_png(self, sample_images):
        """Test validation of invalid PNG image."""
        is_valid = validate_image(str(sample_images['invalid_png']))
        assert not is_valid

    def test_validate_large_png(self, sample_images):
        """Test validation of large PNG image."""
        is_valid = validate_image(str(sample_images['large_png']))
        assert is_valid

    def test_validate_corrupted_png(self, sample_images):
        """Test validation of corrupted PNG image."""
        is_valid = validate_image(str(sample_images['corrupted_png']))
        assert not is_valid

    def test_validate_nonexistent_image(self):
        """Test validation of nonexistent image."""
        is_valid = validate_image('/nonexistent/image.png')
        assert not is_valid

    def test_validate_no_permission(self, temp_dir):
        """Test validation of image without read permission."""
        if os.name != 'nt':  # Skip on Windows
            # Create image without read permission
            img_path = temp_dir / "no_permission.png"
            img = Image.new('RGB', (100, 100), color='red')
            img.save(img_path)
            os.chmod(img_path, 0)
            
            is_valid = validate_image(str(img_path))
            assert not is_valid
            
            # Restore permissions
            os.chmod(img_path, 0o644)

    def test_validate_real_telegram_screenshot(self):
        """Test validation of real Telegram screenshot."""
        # Path to test Telegram screenshot
        screenshot_path = "tests/sample_files/images/telegram_screenshot.png"
        
        # Check if file exists
        if os.path.exists(screenshot_path):
            is_valid = validate_image(screenshot_path)
            assert is_valid
        else:
            pytest.skip("Telegram screenshot not found")

    def test_validate_multiple_images(self, sample_images):
        """Test validation of multiple images."""
        # Validate all test images
        results = {
            'valid_png': validate_image(str(sample_images['valid_png'])),
            'valid_jpg': validate_image(str(sample_images['valid_jpg'])),
            'invalid_png': validate_image(str(sample_images['invalid_png'])),
            'large_png': validate_image(str(sample_images['large_png'])),
            'corrupted_png': validate_image(str(sample_images['corrupted_png']))
        }
        
        # Check results
        assert results['valid_png']
        assert results['valid_jpg']
        assert not results['invalid_png']
        assert results['large_png']
        assert not results['corrupted_png'] 