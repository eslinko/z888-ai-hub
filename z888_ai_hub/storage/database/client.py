"""
Supabase storage client implementation.
"""

import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import logging
from supabase import create_client, Client

from z888_ai_hub.storage.database.models import Document, Paragraph
from z888_ai_hub.storage.database.exceptions import StorageError
from z888_ai_hub.storage.database.interfaces import IStorage
from z888_ai_hub.utils.logging_utils import setup_logger
from z888_ai_hub.config import ServicesConfig


class SupabaseStorage(IStorage):
    """Supabase storage implementation."""
    
    def __init__(self):
        """Initialize Supabase client."""
        self.logger = setup_logger('SupabaseStorage')
        
        # Load configuration
        config = ServicesConfig()
        self.supabase: Client = create_client(
            config.supabase_url,
            config.supabase_key
        )
        self.logger.info("Successfully initialized Supabase client")
    
    async def save_document(self, document: Document) -> str:
        """
        Save document to Supabase.
        
        Args:
            document: Document to save
            
        Returns:
            str: Document ID
            
        Raises:
            StorageError: If save fails
        """
        try:
            # Prepare document data
            doc_data = {
                "file_id": document.file_id,
                "file_name": document.file_name,
                "file_path": document.file_path,
                "file_size": document.file_size,
                "file_type": document.file_type,
                "summary": document.summary,
                "metadata": document.metadata,
                "created_at": document.created_at.isoformat(),
                "updated_at": document.updated_at.isoformat()
            }
            
            # Save document
            result = self.supabase.table("documents").insert(doc_data).execute()
            if not result.data:
                raise StorageError("Failed to save document")
            
            document_id = result.data[0]["id"]
            self.logger.info(f"Successfully saved document {document.file_name} with ID {document_id}")
            
            # Save paragraphs
            await self._save_paragraphs(document.paragraphs)
            
            return document_id
            
        except Exception as e:
            self.logger.error(f"Error saving document {document.file_name}: {str(e)}")
            raise StorageError(f"Failed to save document: {str(e)}")
    
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
            
        Raises:
            StorageError: If save fails
        """
        try:
            # Save summary embedding
            summary_data = {
                "file_id": file_id,
                "embedding": summary_embedding,
                "type": "summary"
            }
            result = self.supabase.table("embeddings").insert(summary_data).execute()
            if not result.data:
                raise StorageError("Failed to save summary embedding")
            
            # Save paragraph embeddings
            for i, embedding in enumerate(paragraph_embeddings):
                para_data = {
                    "file_id": file_id,
                    "embedding": embedding,
                    "type": "paragraph",
                    "paragraph_index": i
                }
                result = self.supabase.table("embeddings").insert(para_data).execute()
                if not result.data:
                    raise StorageError(f"Failed to save paragraph embedding {i}")
            
            self.logger.info(f"Successfully saved embeddings for document {file_id}")
            
        except Exception as e:
            self.logger.error(f"Error saving embeddings for document {file_id}: {str(e)}")
            raise StorageError(f"Failed to save embeddings: {str(e)}")
    
    async def _save_paragraphs(self, paragraphs: List[Paragraph]) -> List[Paragraph]:
        """
        Save paragraphs in batch.
        
        Args:
            paragraphs: List of paragraphs to save
            
        Returns:
            List[Paragraph]: List of saved paragraphs with IDs
            
        Raises:
            StorageError: If save fails
        """
        try:
            # Prepare paragraph data
            para_data = []
            for para in paragraphs:
                para_data.append({
                    "document_id": para.document_id,
                    "text": para.text,
                    "position_in_file": para.position_in_file,
                    "metadata": para.metadata
                })
            
            # Save paragraphs
            result = self.supabase.table("paragraphs").insert(para_data).execute()
            if not result.data:
                raise StorageError("Failed to save paragraphs")
            
            # Update paragraph IDs
            for i, saved_para in enumerate(result.data):
                paragraphs[i].id = saved_para["id"]
            
            self.logger.info(f"Successfully saved {len(paragraphs)} paragraphs")
            return paragraphs
            
        except Exception as e:
            self.logger.error(f"Error saving paragraphs: {str(e)}")
            raise StorageError(f"Failed to save paragraphs: {str(e)}")
    
    async def get_document(self, file_id: str) -> Optional[Document]:
        """
        Get document by file ID.
        
        Args:
            file_id: Document file ID
            
        Returns:
            Document or None if not found
            
        Raises:
            StorageError: If retrieval fails
        """
        try:
            result = self.supabase.table("documents").select("*").eq("file_id", file_id).execute()
            if not result.data:
                return None
            
            doc_data = result.data[0]
            
            # Get paragraphs
            para_result = self.supabase.table("paragraphs").select("*").eq("document_id", doc_data["id"]).execute()
            paragraphs = []
            if para_result.data:
                for para_data in para_result.data:
                    paragraphs.append(Paragraph(
                        id=para_data["id"],
                        document_id=para_data["document_id"],
                        text=para_data["text"],
                        position_in_file=para_data["position_in_file"],
                        metadata=para_data["metadata"]
                    ))
            
            # Create document
            document = Document(
                file_id=doc_data["file_id"],
                file_name=doc_data["file_name"],
                file_path=doc_data["file_path"],
                file_size=doc_data["file_size"],
                file_type=doc_data["file_type"],
                summary=doc_data["summary"],
                metadata=doc_data["metadata"],
                paragraphs=paragraphs,
                created_at=datetime.fromisoformat(doc_data["created_at"]),
                updated_at=datetime.fromisoformat(doc_data["updated_at"])
            )
            
            return document
            
        except Exception as e:
            self.logger.error(f"Error getting document {file_id}: {str(e)}")
            raise StorageError(f"Failed to get document: {str(e)}")
    
    async def delete_document(self, file_id: str) -> bool:
        """
        Delete document by file ID.
        
        Args:
            file_id: Document file ID
            
        Returns:
            bool: True if deleted, False if not found
            
        Raises:
            StorageError: If deletion fails
        """
        try:
            # Get document ID
            result = self.supabase.table("documents").select("id").eq("file_id", file_id).execute()
            if not result.data:
                return False
            
            document_id = result.data[0]["id"]
            
            # Delete paragraphs
            self.supabase.table("paragraphs").delete().eq("document_id", document_id).execute()
            
            # Delete embeddings
            self.supabase.table("embeddings").delete().eq("file_id", file_id).execute()
            
            # Delete document
            self.supabase.table("documents").delete().eq("file_id", file_id).execute()
            
            self.logger.info(f"Successfully deleted document {file_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting document {file_id}: {str(e)}")
            raise StorageError(f"Failed to delete document: {str(e)}") 