"""
Base interfaces and exceptions for storage implementations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Any


class StorageException(Exception):
    """Base exception class for storage-related errors."""
    pass


class DocumentStorage(ABC):
    """Base interface for all document storage implementations."""
    
    @abstractmethod
    async def save_document(self, document_data: Dict[str, Any]) -> str:
        """
        Save document data to storage.
        
        Args:
            document_data: Dictionary containing document data
            
        Returns:
            str: Document ID
            
        Raises:
            StorageException: If saving fails
        """
        pass
    
    @abstractmethod
    async def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve document data by ID.
        
        Args:
            document_id: Unique identifier of the document
            
        Returns:
            Optional[Dict[str, Any]]: Document data if found, None otherwise
            
        Raises:
            StorageException: If retrieval fails
        """
        pass
    
    @abstractmethod
    async def delete_document(self, document_id: str) -> bool:
        """
        Delete document by ID.
        
        Args:
            document_id: Unique identifier of the document
            
        Returns:
            bool: True if document was deleted, False if document was not found
            
        Raises:
            StorageException: If deletion fails
        """
        pass 