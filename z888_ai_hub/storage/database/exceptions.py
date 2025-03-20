"""
Database-specific exceptions.
"""

from ..base import StorageException
from z888_ai_hub.utils.logging_utils import setup_logger

# Инициализируем логгер
logger = setup_logger('DatabaseExceptions', log_to_file=True)


class DatabaseError(StorageException):
    """Base exception for database operations."""
    pass


class ConnectionError(DatabaseError):
    """Raised when database connection fails."""
    pass


class ValidationError(Exception):
    """Raised when data validation fails."""
    def __init__(self, message: str):
        logger.error(f"Validation error: {message}")
        super().__init__(message)


class TransactionError(Exception):
    """Raised when database transaction fails."""
    def __init__(self, message: str):
        logger.error(f"Transaction error: {message}")
        super().__init__(message)


class QueryError(DatabaseError):
    """Raised when database query fails."""
    pass


class StorageError(DatabaseError):
    """Base exception for storage operations."""
    def __init__(self, message: str):
        logger.error(f"Storage error: {message}")
        super().__init__(message)


class DocumentNotFoundError(StorageError):
    """Raised when a document is not found in storage."""
    def __init__(self, file_id: str):
        message = f"Document with ID {file_id} not found"
        logger.error(message)
        super().__init__(message)


class InvalidDocumentError(StorageError):
    """Raised when document validation fails."""
    def __init__(self, message: str):
        logger.error(f"Invalid document: {message}")
        super().__init__(message)


class InvalidPathError(StorageError):
    """Raised when a path validation fails."""
    def __init__(self, reason: str):
        """
        Initialize the exception.

        Args:
            reason: The reason why the path is invalid
        """
        message = f"Invalid path: {reason}"
        logger.error(message)
        super().__init__(message)
        self.reason = reason


class InvalidMetadataError(StorageError):
    """Raised when metadata validation fails."""
    def __init__(self, message: str):
        logger.error(f"Invalid metadata: {message}")
        super().__init__(message) 