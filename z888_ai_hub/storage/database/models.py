"""
Database models and data validation.
"""

from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
import os
from .exceptions import ValidationError, InvalidMetadataError, InvalidPathError
from z888_ai_hub.utils.logging_utils import setup_logger
from z888_ai_hub.storage.database.exceptions import (
    InvalidPathError,
    InvalidMetadataError,
    InvalidDocumentError
)
from z888_ai_hub.processors.base import DocumentContent

# Инициализируем логгер
logger = setup_logger('DatabaseModels', log_to_file=True)

# Допустимые типы для значений метаданных
VALID_METADATA_TYPES = (str, int, float, bool, type(None), list, dict)

@dataclass
class Paragraph:
    """Model for paragraph data."""
    text: str
    file_id: str
    position_in_file: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], file_id: str, position: int) -> 'Paragraph':
        """Create Paragraph instance from dictionary data."""
        try:
            paragraph = cls(
                text=data['text'],
                file_id=file_id,
                position_in_file=position,
                metadata={'page_number': data.get('page_number')}
            )
            logger.debug(f"Created paragraph {position} for file {file_id}")
            return paragraph
        except KeyError as e:
            logger.error(f"Failed to create paragraph: missing key {e}")
            raise ValidationError(f"Missing required field: {e}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage."""
        return {
            'text': self.text,
            'file_id': self.file_id,
            'position_in_file': self.position_in_file,
            'metadata': self.metadata
        }


@dataclass
class Document:
    """Model for document data."""
    file_id: str
    relative_path: str  # Относительный путь к файлу
    file_name: str
    summary: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    paragraphs: List[Paragraph] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    content: Optional[DocumentContent] = None  # Добавляем поле для хранения контента
    
    def __post_init__(self):
        """Validate document data after initialization."""
        self.validate_path()
        self.validate_metadata()
        self.validate_paragraphs()
        self.validate_content()
    
    def validate_content(self):
        """
        Validate document content.
        
        Raises:
            InvalidDocumentError: If content validation fails
        """
        if self.content is not None and not isinstance(self.content, DocumentContent):
            raise InvalidDocumentError("Content must be a DocumentContent instance")
    
    def validate_path(self):
        """
        Validate and normalize the relative path.
        
        Raises:
            InvalidPathError: If path validation fails
        """
        if not self.relative_path:
            raise InvalidPathError("Path cannot be empty")
            
        # Проверяем на недопустимые символы
        invalid_chars = '<>:"|?*'
        for char in invalid_chars:
            if char in self.relative_path:
                raise InvalidPathError(f"Path contains invalid character: {char}")
            
        # Проверяем компоненты пути
        components = self.relative_path.split('/')
        for component in components:
            if not component:
                raise InvalidPathError("Path contains empty components")
            if component in ('.', '..'):
                raise InvalidPathError("Path contains invalid components (. or ..)")
            
        # Нормализуем путь
        self.relative_path = self.relative_path.replace('\\', '/')
    
    def validate_metadata(self):
        """
        Validate metadata types and structure.
        
        Raises:
            InvalidMetadataError: If metadata validation fails
        """
        if not isinstance(self.metadata, dict):
            raise InvalidMetadataError("Metadata must be a dictionary")
            
        # Проверяем обязательные поля
        if 'size' not in self.metadata:
            raise InvalidMetadataError("Metadata must contain 'size' field")
            
        # Проверяем типы данных для числовых полей
        numeric_fields = ['size', 'page_count']
        for field in numeric_fields:
            if field in self.metadata and self.metadata[field] is not None:
                value = self.metadata[field]
                if not isinstance(value, (int, float)):
                    raise InvalidMetadataError(f"{field} must be a number")
                if field == 'size' and value < 0:
                    raise InvalidMetadataError("Size must be a non-negative number")
                if field == 'page_count' and value < 0:
                    raise InvalidMetadataError("Page count must be a non-negative number")
            
        # Проверяем размер метаданных
        metadata_size = len(str(self.metadata))
        if metadata_size > 10000:  # 10KB limit
            raise InvalidMetadataError(f"Metadata size ({metadata_size} bytes) exceeds limit (10000 bytes)")
            
        # Проверяем типы значений
        for key, value in self.metadata.items():
            if not isinstance(key, str):
                raise InvalidMetadataError("Metadata keys must be strings")
            if not isinstance(value, VALID_METADATA_TYPES):
                raise InvalidMetadataError(f"Invalid metadata value type for key '{key}': {type(value)}")
            
            # Рекурсивно проверяем вложенные структуры
            if isinstance(value, (list, dict)):
                self._validate_nested_metadata(value)
    
    def _validate_nested_metadata(self, value: Any, depth: int = 0):
        """
        Validate nested metadata structures.

        Args:
            value: Value to validate
            depth: Current nesting depth

        Raises:
            InvalidMetadataError: If validation fails
        """
        # Ограничиваем глубину вложенности
        if depth > 5:
            raise InvalidMetadataError("Metadata nesting depth exceeds limit (5)")

        if isinstance(value, dict):
            for k, v in value.items():
                if not isinstance(k, str):
                    raise InvalidMetadataError("Nested metadata keys must be strings")
                if not isinstance(v, VALID_METADATA_TYPES):
                    raise InvalidMetadataError(
                        f"Invalid nested metadata value type: {type(v)}"
                    )
                if isinstance(v, (list, dict)):
                    self._validate_nested_metadata(v, depth + 1)

        elif isinstance(value, list):
            for item in value:
                if not isinstance(item, VALID_METADATA_TYPES):
                    raise InvalidMetadataError(
                        f"Invalid metadata list item type: {type(item)}"
                    )
                if isinstance(item, (list, dict)):
                    self._validate_nested_metadata(item, depth + 1)
    
    def validate_paragraphs(self):
        """
        Validate document paragraphs.

        Raises:
            InvalidDocumentError: If paragraphs are invalid
        """
        if not isinstance(self.paragraphs, list):
            raise InvalidDocumentError("Paragraphs must be a list")
            
        # Проверяем каждый параграф
        positions = set()
        for p in self.paragraphs:
            if not isinstance(p, Paragraph):
                raise InvalidDocumentError("Each paragraph must be a Paragraph instance")
            
            if not p.text:
                raise InvalidDocumentError("Paragraph text cannot be empty")
            
            if p.file_id != self.file_id:
                raise InvalidDocumentError("Paragraph file_id must match document file_id")
            
            if p.position_in_file < 0:
                raise InvalidDocumentError("Paragraph position must be non-negative")
            
            if p.position_in_file in positions:
                raise InvalidDocumentError("Duplicate paragraph positions are not allowed")
            
            positions.add(p.position_in_file)
    
    @staticmethod
    def make_relative_path(absolute_path: str, root_dir: str) -> str:
        """
        Преобразует абсолютный путь в относительный от корня обработки.
        
        Args:
            absolute_path: Абсолютный путь к файлу
            root_dir: Корневая директория обработки
            
        Returns:
            str: Относительный путь
            
        Raises:
            ValidationError: If path conversion fails
        """
        try:
            rel_path = os.path.relpath(absolute_path, root_dir)
            # Нормализуем разделители путей
            rel_path = rel_path.replace('\\', '/')
            logger.debug(f"Converted absolute path '{absolute_path}' to relative '{rel_path}'")
            return rel_path
        except ValueError as e:
            logger.error(f"Failed to make relative path: {str(e)}")
            raise ValidationError(f"Cannot make relative path: {str(e)}")
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], root_dir: Optional[str] = None) -> 'Document':
        """
        Create Document instance from dictionary data.
        
        Args:
            data: Raw document data
            root_dir: Optional root directory for path conversion
            
        Returns:
            Document: New Document instance
            
        Raises:
            ValidationError: If required fields are missing
        """
        try:
            logger.debug(f"Creating document from data: {data['file_id']}")
            
            # Создаем параграфы
            paragraphs = [
                Paragraph.from_dict(p, data['file_id'], i)
                for i, p in enumerate(data['paragraphs'])
            ]
            logger.debug(f"Created {len(paragraphs)} paragraphs")
            
            # Парсим даты
            created_at = datetime.fromisoformat(data['created_at'].rstrip('Z'))
            updated_at = datetime.fromisoformat(data['updated_at'].rstrip('Z'))
            
            # Получаем путь к файлу
            if root_dir and 'original_path' in data['metadata']:
                # Если есть абсолютный путь и корневая директория, конвертируем в относительный
                relative_path = cls.make_relative_path(data['metadata']['original_path'], root_dir)
            elif 'relative_path' in data:
                # Если уже есть относительный путь, используем его
                relative_path = data['relative_path']
            else:
                raise ValidationError("Missing path information")
            
            document = cls(
                file_id=data['file_id'],
                relative_path=relative_path,
                file_name=data['file_name'],
                summary=data['summary'],
                metadata=data['metadata'],
                paragraphs=paragraphs,
                created_at=created_at,
                updated_at=updated_at
            )
            
            logger.info(f"Successfully created document model for {data['file_id']}")
            return document
            
        except (KeyError, ValueError) as e:
            logger.error(f"Failed to create document: {str(e)}")
            raise ValidationError(f"Invalid document data: {str(e)}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database storage."""
        return {
            'file_id': self.file_id,
            'relative_path': self.relative_path,
            'file_name': self.file_name,
            'summary': self.summary,
            'metadata': self.metadata,
            'paragraphs': [p.to_dict() for p in self.paragraphs],
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        } 