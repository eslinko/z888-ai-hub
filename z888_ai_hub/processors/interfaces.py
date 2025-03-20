"""
Interfaces for document processing.
"""

from abc import ABC, abstractmethod
from typing import List
from z888_ai_hub.storage.database.models import Document
from z888_ai_hub.storage.database.interfaces import IStorage


class ISummaryGenerator(ABC):
    """Interface for summary generation."""
    
    @abstractmethod
    async def generate_summary(self, text: str) -> str:
        """
        Generate summary from text.
        
        Args:
            text: Text to summarize
            
        Returns:
            str: Generated summary
        """
        pass


class IVectorizer(ABC):
    """Interface for text vectorization."""
    
    @abstractmethod
    async def vectorize(self, text: str) -> List[float]:
        """
        Create vector embedding from text.
        
        Args:
            text: Text to vectorize
            
        Returns:
            List[float]: Vector embedding
        """
        pass
    
    @abstractmethod
    async def vectorize_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Create vector embeddings for multiple texts.
        
        Args:
            texts: List of texts to vectorize
            
        Returns:
            List[List[float]]: List of vector embeddings
        """
        pass 