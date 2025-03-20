"""
Base classes and interfaces for document processors.
"""

import os
import json
import uuid
import datetime
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from z888_ai_hub.client.ai_client import AIClient
from z888_ai_hub.utils.logging_utils import setup_logger


@dataclass
class DocumentContent:
    """Unified structure for document content."""
    text: str
    metadata: Dict[str, Any]
    tables: List[Dict[str, Any]]
    images: List[Dict[str, Any]]
    styles: Dict[str, Any]


@dataclass
class ProcessingResult:
    """Result of document processing."""
    file_id: str
    file_name: str
    content: DocumentContent
    summary: Optional[str] = None
    created_at: str = None
    updated_at: str = None

    def __post_init__(self):
        if not self.created_at:
            now = datetime.datetime.utcnow().isoformat() + "Z"
            self.created_at = now
            self.updated_at = now


class BaseDocumentProcessor(ABC):
    """Base class for all document processors."""

    def __init__(self):
        """Initialize processor with common dependencies."""
        self.ai_client = AIClient()
        self.logger = setup_logger(self.__class__.__name__)

    @abstractmethod
    async def extract_content(self, file_path: str) -> DocumentContent:
        """
        Extract content from document.
        
        Args:
            file_path: Path to document file
            
        Returns:
            DocumentContent with extracted information
            
        Raises:
            ProcessingError: If extraction fails
        """
        pass

    async def generate_summary(self, text: str) -> str:
        """
        Generate summary using AI.
        
        Args:
            text: Text to summarize
            
        Returns:
            Generated summary
        """
        return await self.ai_client.summarize_text(text, max_length=500)

    def split_text_into_paragraphs(self, text: str) -> List[str]:
        """
        Split text into paragraphs.
        
        Args:
            text: Text to split
            
        Returns:
            List of paragraphs
        """
        return [p.strip() for p in text.split("\n\n") if p.strip()]

    async def process_document(self, file_path: str, output_dir: str = "tests/sample_pdfs/json") -> ProcessingResult:
        """
        Process document and save results.
        
        Args:
            file_path: Path to document file
            output_dir: Directory to save results
            
        Returns:
            ProcessingResult with processing details
            
        Raises:
            ProcessingError: If processing fails
        """
        file_name = os.path.basename(file_path)
        self.logger.info(f"Starting processing document: {file_name}")
        
        try:
            # Extract content
            content = await self.extract_content(file_path)
            
            # Generate summary if text is available
            summary = None
            if content.text:
                self.logger.info("Generating document summary...")
                summary = await self.generate_summary(content.text)
                self.logger.debug(f"Summary generated, length: {len(summary)} characters")

            # Create result
            result = ProcessingResult(
                file_id=str(uuid.uuid4()),
                file_name=file_name,
                content=content,
                summary=summary
            )

            # Save results
            os.makedirs(output_dir, exist_ok=True)
            json_path = os.path.join(output_dir, file_name.replace(".", "_") + ".json")
            
            # Convert to JSON-compatible format
            json_data = {
                "file_id": result.file_id,
                "file_name": result.file_name,
                "summary": result.summary,
                "metadata": result.content.metadata,
                "text": result.content.text,
                "tables": result.content.tables,
                "images": result.content.images,
                "styles": result.content.styles,
                "created_at": result.created_at,
                "updated_at": result.updated_at
            }

            with open(json_path, "w", encoding="utf-8") as json_file:
                json.dump(json_data, json_file, indent=4, ensure_ascii=False)

            self.logger.info(f"✅ Successfully processed and saved JSON: {json_path}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing document {file_name}: {str(e)}", exc_info=True)
            raise 