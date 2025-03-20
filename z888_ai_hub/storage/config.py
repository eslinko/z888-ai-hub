"""
Configuration classes for different storage types.
"""

from dataclasses import dataclass
from typing import Optional
from enum import Enum, auto


class StorageType(Enum):
    """Supported storage types."""
    JSON = auto()
    DATABASE = auto()


@dataclass
class StorageConfig:
    """Base configuration for storage."""
    storage_type: StorageType
    
    def validate(self) -> None:
        """
        Validate configuration.
        
        Raises:
            ValueError: If configuration is invalid
        """
        if not isinstance(self.storage_type, StorageType):
            raise ValueError(f"Invalid storage type: {self.storage_type}")


@dataclass
class JsonStorageConfig(StorageConfig):
    """Configuration for JSON file storage."""
    base_path: str
    create_dirs: bool = True
    
    def validate(self) -> None:
        """
        Validate JSON storage configuration.
        
        Raises:
            ValueError: If configuration is invalid
        """
        super().validate()
        if not self.base_path:
            raise ValueError("base_path must not be empty")


@dataclass
class DatabaseConfig(StorageConfig):
    """Configuration for database storage."""
    url: str
    api_key: str
    schema: str = 'public'
    
    def validate(self) -> None:
        """
        Validate database configuration.
        
        Raises:
            ValueError: If configuration is invalid
        """
        super().validate()
        if not self.url:
            raise ValueError("url must not be empty")
        if not self.api_key:
            raise ValueError("api_key must not be empty") 