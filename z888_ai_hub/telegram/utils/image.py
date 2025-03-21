"""
Utilities for processing Telegram chat screenshots.
"""

import os
from pathlib import Path
from typing import List, Optional, Tuple
from PIL import Image
import logging
from ..config import DEFAULT_CONFIG

logger = logging.getLogger(__name__)


def validate_image(image_path: str) -> bool:
    """
    Validate if the file is a valid image.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        bool: True if image is valid, False otherwise
    """
    try:
        with Image.open(image_path) as img:
            img.verify()
        return True
    except Exception as e:
        logger.error(f"Invalid image file {image_path}: {str(e)}")
        return False


def get_image_size(image_path: str) -> Optional[Tuple[int, int]]:
    """
    Get image dimensions.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        tuple: (width, height) or None if error
    """
    try:
        with Image.open(image_path) as img:
            return img.size
    except Exception as e:
        logger.error(f"Error getting image size for {image_path}: {str(e)}")
        return None


def get_images_in_directory(directory: str) -> List[str]:
    """
    Get list of image files in directory, sorted by name.
    
    Args:
        directory: Directory to scan
        
    Returns:
        List[str]: List of image file paths
    """
    image_extensions = DEFAULT_CONFIG['image']['extensions']
    image_files = []
    
    try:
        for file in sorted(os.listdir(directory)):
            if os.path.splitext(file)[1].lower() in image_extensions:
                image_files.append(os.path.join(directory, file))
        return image_files
    except Exception as e:
        logger.error(f"Error scanning directory {directory}: {str(e)}")
        return []


def check_image_requirements(
    image_path: str,
    max_size: Optional[Tuple[int, int]] = None,
    max_file_size: Optional[int] = None
) -> bool:
    """
    Check if image meets size requirements.
    
    Args:
        image_path: Path to the image file
        max_size: Maximum allowed dimensions (width, height)
        max_file_size: Maximum allowed file size in bytes
        
    Returns:
        bool: True if image meets requirements, False otherwise
    """
    # Get default values from config if not provided
    max_size = max_size or DEFAULT_CONFIG['image']['max_size']
    max_file_size = max_file_size or DEFAULT_CONFIG['image']['max_file_size']
    
    # Check file size
    file_size = os.path.getsize(image_path)
    if file_size > max_file_size:
        logger.warning(f"Image {image_path} exceeds maximum file size requirements")
        return False
        
    # Check image dimensions
    size = get_image_size(image_path)
    if not size:
        return False
        
    width, height = size
    max_width, max_height = max_size
    
    if width > max_width or height > max_height:
        logger.warning(f"Image {image_path} exceeds maximum dimensions requirements")
        return False
        
    return True 