"""
DOC/DOCX document processor implementation.
"""

from typing import List, Dict, Any, Tuple
from docx import Document
from docx.document import Document as _Document
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import _Cell, Table, _Row
from docx.text.paragraph import Paragraph

from .base import BaseDocumentProcessor, DocumentContent
from .exceptions import (
    ContentExtractionError,
    MetadataExtractionError,
    TableExtractionError,
    ImageExtractionError,
    StyleExtractionError
)


class DocProcessor(BaseDocumentProcessor):
    """Processor for DOC/DOCX files."""

    async def extract_content(self, file_path: str) -> DocumentContent:
        """
        Extract content from DOC/DOCX file.
        
        Args:
            file_path: Path to DOC/DOCX file
            
        Returns:
            DocumentContent with extracted information
            
        Raises:
            ContentExtractionError: If extraction fails
        """
        try:
            doc = Document(file_path)
            
            # Извлекаем метаданные
            metadata = self._extract_metadata(doc)
            
            # Извлекаем текст, сохраняя структуру
            text = self._extract_text(doc)
            
            # Извлекаем таблицы
            tables = self._extract_tables(doc)
            
            # Извлекаем изображения
            images = self._extract_images(doc)
            
            # Извлекаем стили
            styles = self._extract_styles(doc)
            
            return DocumentContent(
                text=text,
                metadata=metadata,
                tables=tables,
                images=images,
                styles=styles
            )
            
        except Exception as e:
            raise ContentExtractionError(f"Failed to extract content from {file_path}: {str(e)}")

    def _extract_metadata(self, doc: _Document) -> Dict[str, Any]:
        """Extract document metadata."""
        try:
            core_properties = doc.core_properties
            return {
                "title": core_properties.title or "",
                "author": core_properties.author or "",
                "created": core_properties.created.isoformat() if core_properties.created else None,
                "modified": core_properties.modified.isoformat() if core_properties.modified else None,
                "last_modified_by": core_properties.last_modified_by or "",
                "revision": core_properties.revision,
                "paragraph_count": len(doc.paragraphs),
                "section_count": len(doc.sections),
                "page_count": len(doc.sections)  # Приблизительно
            }
        except Exception as e:
            raise MetadataExtractionError(f"Failed to extract metadata: {str(e)}")

    def _extract_text(self, doc: _Document) -> str:
        """Extract text content preserving structure."""
        try:
            text_parts = []
            
            for element in self._iter_block_items(doc):
                if isinstance(element, Paragraph):
                    # Добавляем текст параграфа
                    text = element.text.strip()
                    if text:
                        text_parts.append(text)
                        
            return "\n\n".join(text_parts)
        except Exception as e:
            raise ContentExtractionError(f"Failed to extract text: {str(e)}")

    def _extract_tables(self, doc: _Document) -> List[Dict[str, Any]]:
        """Extract tables with their structure."""
        try:
            tables = []
            for table in doc.tables:
                table_data = []
                for row in table.rows:
                    row_data = []
                    for cell in row.cells:
                        # Получаем текст из ячейки
                        cell_text = cell.text.strip()
                        # Получаем информацию о объединении ячеек
                        colspan = 1  # TODO: Добавить определение colspan
                        rowspan = 1  # TODO: Добавить определение rowspan
                        
                        row_data.append({
                            "text": cell_text,
                            "colspan": colspan,
                            "rowspan": rowspan
                        })
                    table_data.append(row_data)
                
                tables.append({
                    "data": table_data,
                    "row_count": len(table.rows),
                    "column_count": len(table.columns)
                })
            
            return tables
        except Exception as e:
            raise TableExtractionError(f"Failed to extract tables: {str(e)}")

    def _extract_images(self, doc: _Document) -> List[Dict[str, Any]]:
        """Extract images and their properties."""
        try:
            images = []
            rels = doc.part.rels
            for rel in rels.values():
                if "image" in rel.reltype:
                    image_data = {
                        "filename": rel.target_ref,
                        "content_type": rel.target_part.content_type,
                        "width": None,  # TODO: Добавить извлечение размеров
                        "height": None
                    }
                    images.append(image_data)
            return images
        except Exception as e:
            raise ImageExtractionError(f"Failed to extract images: {str(e)}")

    def _extract_styles(self, doc: _Document) -> Dict[str, Any]:
        """Extract style information."""
        try:
            styles = {}
            for style in doc.styles:
                if style.type == 1:  # Paragraph style
                    styles[style.name] = {
                        "font": style.font.name if style.font else None,
                        "size": style.font.size if style.font else None,
                        "bold": style.font.bold if style.font else None,
                        "italic": style.font.italic if style.font else None
                    }
            return styles
        except Exception as e:
            raise StyleExtractionError(f"Failed to extract styles: {str(e)}")

    def _iter_block_items(self, doc: _Document):
        """Iterate through all block items (paragraphs and tables)."""
        if not doc.element.body:
            return
            
        for child in doc.element.body:
            if isinstance(child, CT_P):
                yield Paragraph(child, doc)
            elif isinstance(child, CT_Tbl):
                yield Table(child, doc) 