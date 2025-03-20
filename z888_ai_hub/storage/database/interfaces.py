"""
Storage interfaces.
"""

from abc import ABC, abstractmethod
from typing import List
from z888_ai_hub.storage.database.models import Document


class IStorage(ABC):
    """Interface for document storage."""
    
    @abstractmethod
    async def save_document(self, document: Document) -> str:
        """
        Save document to storage.
        
        Args:
            document: Document to save
            
        Returns:
            str: Document ID
        """
        pass
    
    @abstractmethod
    async def save_embeddings(
        self,
        file_id: str,
        summary_embedding: List[float],
        paragraph_embeddings: List[List[float]]
    ) -> None:
        """
        Save embeddings for document and its paragraphs.
        
        Args:
            file_id: Document ID
            summary_embedding: Document summary embedding
            paragraph_embeddings: List of paragraph embeddings
        """
        pass 