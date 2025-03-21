"""
Data models for Telegram chat processing.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any


@dataclass
class TelegramMessage:
    """Represents a single message from Telegram chat."""
    timestamp: Optional[datetime] = None
    sender: Optional[str] = None
    text: str = ""
    links: List[str] = None
    image_order: int = 0
    position_in_image: int = 0

    def __post_init__(self):
        if self.links is None:
            self.links = []


@dataclass
class TelegramChat:
    """Represents a Telegram chat with messages."""
    messages: List[TelegramMessage]
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ProcessingResult:
    """Result of processing Telegram chat screenshots."""
    success: bool
    chat: Optional[TelegramChat] = None
    error: Optional[str] = None
    processing_time: Optional[float] = None
    total_images: int = 0
    processed_images: int = 0
    failed_images: int = 0 