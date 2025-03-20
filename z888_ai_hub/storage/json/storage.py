"""
JSON file storage implementation.
"""

import os
import json
from typing import Dict, Optional, Any
from ..base import DocumentStorage
from ..config import JsonStorageConfig, StorageType
from .exceptions import JsonFileError, JsonValidationError
from .validator import validate_document
from z888_ai_hub.utils.logging_utils import setup_logger


class JsonStorage(DocumentStorage):
    """Implementation of document storage using JSON files."""
    
    def __init__(self, config: JsonStorageConfig):
        """
        Initialize JSON storage.
        
        Args:
            config: Storage configuration
        """
        self.logger = setup_logger('JsonStorage')
        self.config = config
        self.config.validate()
        
        if config.storage_type != StorageType.JSON:
            raise ValueError("Invalid storage type for JsonStorage")
        
        if config.create_dirs:
            os.makedirs(config.base_path, exist_ok=True)
            self.logger.debug(f"Ensured base directory exists: {config.base_path}")

    def _get_file_path(self, file_id: str) -> str:
        """Get full path for document file."""
        return os.path.join(self.config.base_path, f"{file_id}.json")

    async def save_document(self, document_data: Dict[str, Any]) -> str:
        """
        Save document to JSON file.
        
        Args:
            document_data: Document data to save
            
        Returns:
            str: Document ID (file_id from document_data)
            
        Raises:
            JsonValidationError: If document validation fails
            JsonFileError: If file operations fail
        """
        try:
            # Валидация документа
            validate_document(document_data)
            
            file_id = document_data['file_id']
            file_path = self._get_file_path(file_id)
            
            # Сохранение файла
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(document_data, f, indent=4, ensure_ascii=False)
                self.logger.info(f"Document saved: {file_path}")
                return file_id
            except (IOError, OSError) as e:
                raise JsonFileError(f"Failed to save document: {str(e)}")
                
        except Exception as e:
            self.logger.error(f"Error saving document: {str(e)}")
            raise

    async def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve document from JSON file.
        
        Args:
            document_id: Document ID (file_id)
            
        Returns:
            Optional[Dict[str, Any]]: Document data if found, None otherwise
            
        Raises:
            JsonFileError: If file operations fail
        """
        file_path = self._get_file_path(document_id)
        
        if not os.path.exists(file_path):
            self.logger.debug(f"Document not found: {file_path}")
            return None
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.logger.debug(f"Document loaded: {file_path}")
            return data
        except (IOError, OSError, json.JSONDecodeError) as e:
            raise JsonFileError(f"Failed to read document: {str(e)}")

    async def delete_document(self, document_id: str) -> bool:
        """
        Delete document JSON file.
        
        Args:
            document_id: Document ID (file_id)
            
        Returns:
            bool: True if document was deleted, False if document was not found
            
        Raises:
            JsonFileError: If file operations fail
        """
        file_path = self._get_file_path(document_id)
        
        if not os.path.exists(file_path):
            self.logger.debug(f"Document not found for deletion: {file_path}")
            return False
            
        try:
            os.remove(file_path)
            self.logger.info(f"Document deleted: {file_path}")
            return True
        except (IOError, OSError) as e:
            raise JsonFileError(f"Failed to delete document: {str(e)}") 