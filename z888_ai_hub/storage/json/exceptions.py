"""
Exceptions specific to JSON storage implementation.
"""

from ..base import StorageException


class JsonStorageException(StorageException):
    """Base exception for JSON storage errors."""
    pass


class JsonValidationError(JsonStorageException):
    """Raised when document validation fails."""
    pass


class JsonFileError(JsonStorageException):
    """Raised when file operations fail."""
    pass 