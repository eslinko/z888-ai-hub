"""
Main document processor for handling files and their processing pipeline.
"""

import os
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from z888_ai_hub.utils.file_collector import FileCollector, FileInfo
from z888_ai_hub.processors.pdf_processor import PdfProcessor
from z888_ai_hub.processors.doc_processor import DocProcessor
from z888_ai_hub.utils.logging_utils import setup_logger
from z888_ai_hub.storage.database.models import Document, Paragraph
from z888_ai_hub.storage.database.exceptions import StorageError
from z888_ai_hub.storage.json.exceptions import JsonStorageException
from z888_ai_hub.connectors.base_connector import BaseConnector, ConnectorCapability
from .base import DocumentContent
from .interfaces import IStorage


class DocumentProcessor:
    """Main processor for handling document processing pipeline."""
    
    def __init__(
        self,
        storage: IStorage,
        summary_generator: BaseConnector,
        vectorizer: BaseConnector,
        file_collector: FileCollector,
        pdf_processor: PdfProcessor,
        doc_processor: DocProcessor
    ):
        """
        Initialize document processor with all required components.
        
        Args:
            storage: Storage implementation
            summary_generator: Connector for summary generation
            vectorizer: Connector for text vectorization
            file_collector: File collection utility
            pdf_processor: PDF processing service
            doc_processor: Document processing service
            
        Raises:
            ValueError: If connectors don't have required capabilities
        """
        self.logger = setup_logger('DocumentProcessor')
        
        # Проверяем возможности коннекторов
        if ConnectorCapability.SUMMARY not in summary_generator.capabilities:
            raise ValueError("Summary generator connector must have SUMMARY capability")
        if ConnectorCapability.VECTORIZATION not in vectorizer.capabilities:
            raise ValueError("Vectorizer connector must have VECTORIZATION capability")
            
        self.storage = storage
        self.summary_generator = summary_generator
        self.vectorizer = vectorizer
        self.file_collector = file_collector
        self.pdf_processor = pdf_processor
        self.doc_processor = doc_processor
        
        self.logger.info("DocumentProcessor initialized with all components")
    
    async def process_directory(self, root_dir: str) -> Dict[str, Any]:
        """
        Process all files in the directory recursively.
        
        Args:
            root_dir: Root directory to process
            
        Returns:
            Dict with processing statistics
        """
        self.logger.info(f"Starting directory processing: {root_dir}")
        
        # Собираем файлы
        files = list(self.file_collector.collect_files())
        self.logger.info(f"Found {len(files)} files to process")
        
        # Статистика
        stats = {
            'total_files': len(files),
            'processed_files': 0,
            'failed_files': [],
            'file_types': {},
            'start_time': datetime.now().isoformat(),
            'end_time': None
        }
        
        for file_info in files:
            try:
                self.logger.info(f"Processing file: {file_info.absolute_path}")
                
                # Обработка файла
                doc = await self._process_file(file_info)
                
                # Получение summary через коннектор
                try:
                    summary = await self.summary_generator.generate_summary(doc.content.text)
                    doc.summary = summary
                except Exception as e:
                    self.logger.error(f"Failed to generate summary for {file_info.absolute_path}: {str(e)}")
                    raise
                
                # Векторизация summary и параграфов через коннектор
                try:
                    summary_embedding = await self.vectorizer.vectorize(summary)
                    paragraph_embeddings = await self.vectorizer.vectorize_batch(
                        [p.text for p in doc.paragraphs]
                    )
                except Exception as e:
                    self.logger.error(f"Failed to vectorize content for {file_info.absolute_path}: {str(e)}")
                    raise
                
                # Сохранение в базу
                try:
                    await self.storage.save_document(doc)
                    await self.storage.save_embeddings(
                        doc.file_id,
                        summary_embedding,
                        paragraph_embeddings
                    )
                except (StorageError, JsonStorageException) as e:
                    self.logger.error(f"Failed to save document {file_info.absolute_path}: {str(e)}")
                    raise
                
                # Обновление статистики
                stats['processed_files'] += 1
                stats['file_types'][file_info.extension] = stats['file_types'].get(
                    file_info.extension, 0
                ) + 1
                
                self.logger.info(f"Successfully processed file: {file_info.absolute_path}")
                
            except Exception as e:
                self.logger.error(f"Failed to process file {file_info.absolute_path}: {str(e)}")
                stats['failed_files'].append({
                    'path': file_info.absolute_path,
                    'error': str(e)
                })
        
        # Завершаем статистику
        stats['end_time'] = datetime.now().isoformat()
        self.logger.info(f"Directory processing completed. Stats: {stats}")
        
        return stats
    
    async def _process_file(self, file_info: FileInfo) -> Document:
        """
        Process single file and extract its content.
        
        Args:
            file_info: File information
            
        Returns:
            Document instance with extracted content
            
        Raises:
            Exception: If file processing fails
        """
        # Определяем процессор в зависимости от типа файла
        if file_info.extension.lower() == '.pdf':
            processor = self.pdf_processor
        else:
            processor = self.doc_processor
        
        # Извлекаем контент
        content = await processor.extract_content(file_info.absolute_path)
        
        # Разбиваем на параграфы
        paragraphs_text = self.doc_processor.split_text_into_paragraphs(content.text)
        
        # Создаем документ
        doc = Document(
            file_id=file_info.file_id,
            relative_path=file_info.relative_path,
            file_name=file_info.file_name,
            summary="",  # Будет заполнено позже
            metadata={
                'size': file_info.size,
                'extension': file_info.extension,
                'created_at': file_info.created_at.isoformat(),
                'modified_at': file_info.modified_at.isoformat(),
                'page_count': content.metadata.get('page_count'),
                'language': content.metadata.get('language', 'EN'),
                'tables': content.tables,
                'images': content.images,
                'styles': content.styles,
                'original_path': file_info.absolute_path
            },
            paragraphs=[
                Paragraph(
                    text=p,
                    file_id=file_info.file_id,
                    position_in_file=i,
                    metadata={
                        'page_number': None,
                        'style': content.styles.get(str(i), {})
                    }
                )
                for i, p in enumerate(paragraphs_text)
            ],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Сохраняем контент
        doc.content = content
        
        return doc

