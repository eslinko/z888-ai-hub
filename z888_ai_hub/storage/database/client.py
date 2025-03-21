"""
Supabase storage client implementation.
"""

import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import logging
import asyncio
from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions

from z888_ai_hub.storage.database.models import Document, Paragraph
from z888_ai_hub.storage.database.exceptions import StorageError
from z888_ai_hub.storage.database.interfaces import IStorage
from z888_ai_hub.utils.logging_utils import setup_logger
from z888_ai_hub.config import ServicesConfig


class SupabaseStorage(IStorage):
    """Supabase storage implementation."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Supabase client.
        
        Args:
            config: Optional configuration dictionary. If not provided, will use ServicesConfig.
                   Expected keys:
                   - supabase_url: Supabase project URL
                   - supabase_key: Supabase API key
        """
        self.logger = setup_logger('SupabaseStorage')
        
        # Load configuration
        if config:
            supabase_url = config.get('supabase_url')
            supabase_key = config.get('supabase_key')
            if not supabase_url or not supabase_key:
                raise ValueError("Config must contain 'supabase_url' and 'supabase_key'")
        else:
            services_config = ServicesConfig()
            supabase_url = services_config.supabase_url
            supabase_key = services_config.supabase_key
            
        options = ClientOptions(
            schema='public',
            headers={},
            auto_refresh_token=True,
            persist_session=True,
            postgrest_client_timeout=10
        )
        
        self.supabase: Client = create_client(
            supabase_url,
            supabase_key,
            options=options
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
            result = await self.supabase.table("documents").insert(doc_data).execute()
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
            result = await self.supabase.table("embeddings").insert(summary_data).execute()
            if not result.data:
                raise StorageError("Failed to save summary embedding")
            
            # Save paragraph embeddings in batches
            batch_size = 100
            for i in range(0, len(paragraph_embeddings), batch_size):
                batch = paragraph_embeddings[i:i + batch_size]
                para_data = []
                for j, embedding in enumerate(batch):
                    para_data.append({
                        "file_id": file_id,
                        "embedding": embedding,
                        "type": "paragraph",
                        "paragraph_index": i + j
                    })
                result = await self.supabase.table("embeddings").insert(para_data).execute()
                if not result.data:
                    raise StorageError(f"Failed to save paragraph embeddings batch {i//batch_size}")
            
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
            # Save paragraphs in batches
            batch_size = 100
            saved_paragraphs = []
            
            for i in range(0, len(paragraphs), batch_size):
                batch = paragraphs[i:i + batch_size]
                para_data = []
                for para in batch:
                    para_data.append({
                        "document_id": para.document_id,
                        "text": para.text,
                        "position_in_file": para.position_in_file,
                        "metadata": para.metadata
                    })
                
                result = await self.supabase.table("paragraphs").insert(para_data).execute()
                if not result.data:
                    raise StorageError(f"Failed to save paragraphs batch {i//batch_size}")
                
                # Update paragraph IDs
                for j, saved_para in enumerate(result.data):
                    batch[j].id = saved_para["id"]
                    saved_paragraphs.append(batch[j])
            
            self.logger.info(f"Successfully saved {len(saved_paragraphs)} paragraphs")
            return saved_paragraphs
            
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
            result = await self.supabase.table("documents").select("*").eq("file_id", file_id).execute()
            if not result.data:
                return None
            
            doc_data = result.data[0]
            
            # Get paragraphs
            para_result = await self.supabase.table("paragraphs").select("*").eq("document_id", doc_data["id"]).execute()
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
            result = await self.supabase.table("documents").select("id").eq("file_id", file_id).execute()
            if not result.data:
                return False
            
            document_id = result.data[0]["id"]
            
            # Delete paragraphs
            await self.supabase.table("paragraphs").delete().eq("document_id", document_id).execute()
            
            # Delete embeddings
            await self.supabase.table("embeddings").delete().eq("file_id", file_id).execute()
            
            # Delete document
            await self.supabase.table("documents").delete().eq("file_id", file_id).execute()
            
            self.logger.info(f"Successfully deleted document {file_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting document {file_id}: {str(e)}")
            raise StorageError(f"Failed to delete document: {str(e)}")
            
    async def get_document_by_path(self, file_path: str) -> Optional[Document]:
        """
        Get document by file path.
        
        Args:
            file_path: Document file path
            
        Returns:
            Document or None if not found
            
        Raises:
            StorageError: If retrieval fails
        """
        try:
            result = await self.supabase.table("documents").select("*").eq("file_path", file_path).execute()
            if not result.data:
                return None
                
            return await self.get_document(result.data[0]["file_id"])
            
        except Exception as e:
            self.logger.error(f"Error getting document by path {file_path}: {str(e)}")
            raise StorageError(f"Failed to get document by path: {str(e)}")
            
    async def get_documents(self, limit: int = 100, offset: int = 0) -> List[Document]:
        """
        Get list of documents with pagination.
        
        Args:
            limit: Maximum number of documents to return
            offset: Number of documents to skip
            
        Returns:
            List[Document]: List of documents
            
        Raises:
            StorageError: If retrieval fails
        """
        try:
            result = await self.supabase.table("documents").select("*").range(offset, offset + limit - 1).execute()
            if not result.data:
                return []
                
            documents = []
            for doc_data in result.data:
                doc = await self.get_document(doc_data["file_id"])
                if doc:
                    documents.append(doc)
                    
            return documents
            
        except Exception as e:
            self.logger.error(f"Error getting documents: {str(e)}")
            raise StorageError(f"Failed to get documents: {str(e)}")
            
    async def search_documents(self, query: str, limit: int = 10) -> List[Document]:
        """
        Search documents by text query.
        
        Args:
            query: Search query
            limit: Maximum number of documents to return
            
        Returns:
            List[Document]: List of matching documents
            
        Raises:
            StorageError: If search fails
        """
        try:
            # Use full text search on summary and paragraphs
            result = await self.supabase.rpc(
                'search_documents',
                {'search_query': query, 'result_limit': limit}
            ).execute()
            
            if not result.data:
                return []
                
            documents = []
            for doc_data in result.data:
                doc = await self.get_document(doc_data["file_id"])
                if doc:
                    documents.append(doc)
                    
            return documents
            
        except Exception as e:
            self.logger.error(f"Error searching documents: {str(e)}")
            raise StorageError(f"Failed to search documents: {str(e)}") 