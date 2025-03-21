"""
Main parser for Telegram chat screenshots.
"""

import time
import logging
import re
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

from .models import TelegramMessage, TelegramChat, ProcessingResult
from .config import DEFAULT_CONFIG
from .utils.image import (
    validate_image,
    get_images_in_directory,
    check_image_requirements
)


logger = logging.getLogger(__name__)


class TelegramChatParser:
    """
    Parser for Telegram chat screenshots.
    Uses OCR to extract text and structures it into chat messages.
    """
    
    def __init__(self, ocr_connector, config: Optional[Dict[str, Any]] = None):
        """
        Initialize parser.
        
        Args:
            ocr_connector: OCR connector instance
            config: Optional configuration dictionary
        """
        self.ocr_connector = ocr_connector
        self.config = config or DEFAULT_CONFIG
        self.logger = logging.getLogger(__name__)
        
        # Regular expressions for parsing
        self.time_pattern = re.compile(r'(\d{1,2}:\d{2}(?::\d{2})?)')
        self.sender_pattern = re.compile(r'^([^:]+):')
        self.link_pattern = re.compile(r'https?://[^\s<>"]+|www\.[^\s<>"]+')
    
    async def process_directory(self, directory: str) -> ProcessingResult:
        """
        Process all screenshots in directory.
        
        Args:
            directory: Directory containing screenshots
            
        Returns:
            ProcessingResult: Result of processing
        """
        start_time = time.time()
        result = ProcessingResult(success=False)
        
        try:
            # Get list of images
            image_files = get_images_in_directory(directory)
            result.total_images = len(image_files)
            
            if not image_files:
                result.error = "No valid images found in directory"
                return result
            
            # Process each image
            messages = []
            for idx, image_path in enumerate(image_files):
                try:
                    if not self._validate_and_process_image(image_path):
                        result.failed_images += 1
                        continue
                        
                    # Process image and extract messages
                    image_messages = await self._process_single_image(image_path, idx)
                    messages.extend(image_messages)
                    
                    result.processed_images += 1
                except Exception as e:
                    self.logger.error(f"Error processing image {image_path}: {str(e)}")
                    result.failed_images += 1
            
            # Create chat object
            result.chat = TelegramChat(
                messages=messages,
                metadata={
                    "source_directory": directory,
                    "total_images": result.total_images,
                    "processed_images": result.processed_images,
                    "failed_images": result.failed_images
                }
            )
            
            result.success = True
            
        except Exception as e:
            result.error = str(e)
            self.logger.error(f"Error processing directory: {str(e)}")
        
        finally:
            result.processing_time = time.time() - start_time
            
        return result
    
    def _validate_and_process_image(self, image_path: str) -> bool:
        """
        Validate and prepare image for processing.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            bool: True if image is valid and ready for processing
        """
        if not validate_image(image_path):
            return False
            
        max_file_size = self.config.get('processing', {}).get('max_file_size')
        max_dimensions = tuple(self.config.get('processing', {}).get('max_dimensions'))
        
        if not check_image_requirements(image_path, max_size=max_dimensions, max_file_size=max_file_size):
            return False
            
        return True

    async def _process_single_image(self, image_path: str, image_order: int) -> List[TelegramMessage]:
        """
        Process single image using OCR and extract messages.
        
        Args:
            image_path: Path to the image file
            image_order: Order of image in sequence
            
        Returns:
            List[TelegramMessage]: List of extracted messages
        """
        try:
            # Get text through OCR
            raw_text = await self.ocr_connector.extract_text(image_path)
            
            # Split text into messages
            messages = []
            current_message = []
            
            for line in raw_text.split('\n'):
                # If line starts with sender name, it's a new message
                if self.sender_pattern.match(line):
                    if current_message:
                        # Process previous message
                        message_text = '\n'.join(current_message)
                        parsed_data = self._parse_message_text(message_text)
                        
                        messages.append(TelegramMessage(
                            timestamp=parsed_data.get('timestamp'),
                            sender=parsed_data.get('sender'),
                            text=parsed_data.get('text', ''),
                            links=parsed_data.get('links', []),
                            image_order=image_order,
                            position_in_image=len(messages)
                        ))
                    
                    # Start new message
                    current_message = [line]
                else:
                    # Continue current message
                    current_message.append(line)
            
            # Process last message
            if current_message:
                message_text = '\n'.join(current_message)
                parsed_data = self._parse_message_text(message_text)
                
                messages.append(TelegramMessage(
                    timestamp=parsed_data.get('timestamp'),
                    sender=parsed_data.get('sender'),
                    text=parsed_data.get('text', ''),
                    links=parsed_data.get('links', []),
                    image_order=image_order,
                    position_in_image=len(messages)
                ))
            
            self.logger.info(f"Processed image {image_path}: extracted {len(messages)} messages")
            return messages
            
        except Exception as e:
            self.logger.error(f"Error processing image {image_path}: {str(e)}")
            raise

    def _parse_message_text(self, text: str) -> Dict[str, Any]:
        """
        Parse raw text into message components.
        
        Args:
            text: Raw text from OCR
            
        Returns:
            Dict[str, Any]: Parsed message components
        """
        # Extract metadata
        metadata = self._extract_metadata(text)
        
        # Extract links
        links = self._extract_links(text)
        
        # Clean text from metadata and links
        clean_text = text
        if metadata.get('sender'):
            clean_text = clean_text.replace(f"{metadata['sender']}:", "").strip()
        
        return {
            'timestamp': metadata.get('timestamp'),
            'sender': metadata.get('sender'),
            'text': clean_text,
            'links': links
        }

    def _extract_metadata(self, text: str) -> Dict[str, Any]:
        """Extract metadata from message text."""
        metadata = {}
        
        # Extract timestamp
        time_match = self.time_pattern.search(text)
        if time_match:
            try:
                time_str = time_match.group(1)
                metadata['timestamp'] = datetime.strptime(time_str, '%H:%M:%S')
            except ValueError:
                pass
        
        # Extract sender
        sender_match = self.sender_pattern.match(text)
        if sender_match:
            metadata['sender'] = sender_match.group(1)
        
        return metadata

    def _extract_links(self, text: str) -> List[str]:
        """Extract links from message text."""
        return self.link_pattern.findall(text) 