"""PDF document processor implementation using pdfplumber and PyMuPDF."""

import os
from typing import List, Dict, Any, Optional
import pdfplumber
import fitz  # PyMuPDF
from pdfplumber.page import Page
from pdfplumber.table import Table
import logging
from PIL import Image
import io

from .base import BaseDocumentProcessor, DocumentContent
from .exceptions import (
    ContentExtractionError,
    MetadataExtractionError,
    TableExtractionError,
    ImageExtractionError,
    StyleExtractionError
)
from ..connectors.mistral import MistralConnector


class PdfProcessor(BaseDocumentProcessor):
    """Processor for PDF files."""

    def __init__(self, mistral_connector: Optional[MistralConnector] = None):
        """
        Initialize PDF processor.
        
        Args:
            mistral_connector: Optional Mistral connector for OCR
        """
        super().__init__()
        self.mistral = mistral_connector or MistralConnector()

    async def extract_content(self, file_path: str) -> DocumentContent:
        """
        Extract content from PDF file.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            DocumentContent with extracted information
            
        Raises:
            ContentExtractionError: If extraction fails
        """
        try:
            # Открываем PDF для извлечения метаданных и стилей
            with pdfplumber.open(file_path) as pdf:
                metadata = self._extract_metadata(pdf)
                styles = self._extract_styles(pdf)
                tables = self._extract_tables(pdf)
                images = self._extract_images(pdf)

                # Сначала пробуем извлечь текст с помощью PyMuPDF
                text = self._extract_text_with_pymupdf(file_path)
                
                # Если PyMuPDF не смог извлечь текст, пробуем pdfplumber
                if not text:
                    logging.debug("PyMuPDF failed to extract text, trying pdfplumber")
                    text = self._extract_text_with_pdfplumber(pdf)
                    
                    # Если и pdfplumber не смог извлечь текст, пробуем Mistral OCR
                    if not text:
                        logging.debug("pdfplumber failed to extract text, trying Mistral OCR")
                        text = await self.mistral.extract_text(file_path)
                        if text:
                            logging.debug(f"Successfully extracted text using Mistral OCR, length: {len(text)}")
                            # Для OCR-текста не нужно добавлять заголовок
                            return DocumentContent(
                                text=text,
                                metadata=metadata,
                                tables=tables,
                                images=images,
                                styles={}  # OCR-текст не имеет стилей
                            )
                        else:
                            logging.debug("Mistral OCR failed to extract text")
                
                # Добавляем заголовок из метаданных в начало текста, если он есть и не пустой
                title = metadata.get("title")
                if title and title != "untitled" and title not in text:
                    text = f"{title}\n\n{text}"
                
                return DocumentContent(
                    text=text,
                    metadata=metadata,
                    tables=tables,
                    images=images,
                    styles=styles
                )
                
        except Exception as e:
            logging.error(f"Error extracting content: {str(e)}")
            raise ContentExtractionError(f"Failed to extract content from {file_path}: {str(e)}")

    def _extract_text_with_pymupdf(self, file_path: str) -> str:
        """Extract text using PyMuPDF."""
        try:
            doc = fitz.open(file_path)
            text_content = []
            
            for page in doc:
                # Пробуем разные методы извлечения текста
                text = page.get_text()
                if not text:
                    # Пробуем извлечь текст с другими параметрами
                    text = page.get_text("text", flags=fitz.TEXT_PRESERVE_LIGATURES | fitz.TEXT_PRESERVE_WHITESPACE)
                
                if not text:
                    # Пробуем извлечь текст как HTML
                    text = page.get_text("html")
                    if text:
                        # Удаляем HTML теги
                        from bs4 import BeautifulSoup
                        soup = BeautifulSoup(text, 'html.parser')
                        text = soup.get_text()
                
                if text:
                    text_content.append(text.strip())
                    logging.debug(f"Successfully extracted text from page {page.number + 1} using PyMuPDF")
                else:
                    logging.debug(f"No text found on page {page.number + 1} using PyMuPDF")
            
            doc.close()
            final_text = "\n\n".join(text_content)
            logging.debug(f"Total extracted text length (PyMuPDF): {len(final_text)}")
            return final_text
        except Exception as e:
            logging.error(f"PyMuPDF text extraction failed: {str(e)}")
            return ""

    def _extract_text_with_pdfplumber(self, pdf: pdfplumber.PDF) -> str:
        """Extract text using pdfplumber."""
        try:
            text_content = []
            for page in pdf.pages:
                logging.debug(f"Processing page {page.page_number} with pdfplumber")
                
                # Проверяем, есть ли вообще текстовые объекты на странице
                if not page.chars:
                    logging.debug(f"No text objects found on page {page.page_number}")
                    continue

                # Пробуем разные методы извлечения текста с более мягкими параметрами
                text = page.extract_text(x_tolerance=3, y_tolerance=3)
                if not text:
                    logging.debug(f"Standard text extraction failed on page {page.page_number}, trying word extraction")
                    # Пробуем извлечь текст из слов с более мягкими параметрами
                    words = page.extract_words(
                        x_tolerance=3,
                        y_tolerance=3,
                        keep_blank_chars=True,
                        use_text_flow=True
                    )
                    if words:
                        logging.debug(f"Found {len(words)} words on page {page.page_number}")
                        text = " ".join(word["text"] for word in words)
                    else:
                        logging.debug(f"Word extraction failed on page {page.page_number}, trying character extraction")
                        # Если и это не помогло, пробуем извлечь текст напрямую из объектов страницы
                        chars = []
                        for obj in page.chars:
                            if obj.get("text"):
                                chars.append(obj["text"])
                        text = "".join(chars)
                        if text:
                            logging.debug(f"Found {len(chars)} characters on page {page.page_number}")
                        else:
                            logging.debug(f"Character extraction failed on page {page.page_number}")
                            # Дополнительная отладочная информация
                            logging.debug(f"Page objects: {page.objects}")
                            logging.debug(f"Page chars count: {len(page.chars)}")
                            logging.debug(f"First few chars: {page.chars[:5] if page.chars else 'None'}")

                if text:
                    logging.debug(f"Successfully extracted text from page {page.page_number}")
                    text_content.append(text.strip())
                else:
                    logging.warning(f"Failed to extract text from page {page.page_number}")

            final_text = "\n\n".join(text_content)
            logging.debug(f"Total extracted text length (pdfplumber): {len(final_text)}")
            return final_text
        except Exception as e:
            logging.error(f"Error extracting text with pdfplumber: {str(e)}")
            raise ContentExtractionError(f"Failed to extract text: {str(e)}")

    def _extract_metadata(self, pdf) -> Dict[str, str]:
        """
        Extract metadata from PDF file.
        
        Args:
            pdf: PDF file object
            
        Returns:
            Dictionary with metadata
        """
        metadata = {}
        
        # Извлекаем базовые метаданные
        info = pdf.metadata
        if info:
            metadata["title"] = str(info.get("Title", "untitled"))
            metadata["author"] = str(info.get("Author", "anonymous"))
            metadata["creator"] = str(info.get("Creator", "unknown"))
            metadata["producer"] = str(info.get("Producer", "unknown"))
            metadata["subject"] = str(info.get("Subject", "unspecified"))
            metadata["created"] = str(info.get("CreationDate", ""))
            metadata["modified"] = str(info.get("ModDate", ""))
        
        # Добавляем дополнительную информацию
        metadata["page_count"] = str(len(pdf.pages))
        metadata["file_size"] = str(os.path.getsize(pdf.stream.name))
        
        return metadata

    def _extract_tables(self, pdf: pdfplumber.PDF) -> List[Dict[str, Any]]:
        """Extract tables with their structure."""
        try:
            tables = []
            for page_num, page in enumerate(pdf.pages):
                page_tables = page.find_tables()
                
                for table in page_tables:
                    table_data = []
                    for row in table.extract():
                        row_data = []
                        for cell in row:
                            cell_text = cell.strip() if cell else ""
                            row_data.append({
                                "text": cell_text,
                                "colspan": 1,  # pdfplumber не предоставляет информацию о colspan
                                "rowspan": 1   # pdfplumber не предоставляет информацию о rowspan
                            })
                        table_data.append(row_data)
                    
                    # Добавляем информацию о таблице
                    tables.append({
                        "data": table_data,
                        "page_number": page_num + 1,
                        "row_count": len(table_data),
                        "column_count": len(table_data[0]) if table_data else 0,
                        "bbox": list(table.bbox),  # Координаты таблицы на странице
                    })
            
            return tables
        except Exception as e:
            raise TableExtractionError(f"Failed to extract tables: {str(e)}")

    def _extract_images(self, pdf: pdfplumber.PDF) -> List[Dict[str, Any]]:
        """Extract images and their properties."""
        try:
            images = []
            for page_num, page in enumerate(pdf.pages):
                # Получаем все изображения на странице
                page_images = page.images
                
                for img in page_images:
                    # Создаем базовые данные об изображении
                    image_data = {
                        "page_number": page_num + 1,
                        "bbox": list(img.get("bbox", [0, 0, 0, 0])),  # Используем пустые координаты если bbox отсутствует
                        "width": img.get("width", 0),  # Используем 0 если ширина отсутствует
                        "height": img.get("height", 0),  # Используем 0 если высота отсутствует
                        "type": img.get("type", "unknown"),  # Используем "unknown" если тип отсутствует
                        "name": img.get("name", ""),
                    }
                    images.append(image_data)
            
            return images
        except Exception as e:
            logging.warning(f"Failed to extract images: {str(e)}")
            return []  # Возвращаем пустой список вместо выбрасывания исключения

    def _extract_styles(self, pdf: pdfplumber.PDF) -> Dict[str, Any]:
        """Extract font styles and their properties."""
        try:
            styles = {}
            for page in pdf.pages:
                # Извлекаем слова со страницы
                words = page.extract_words(extra_attrs=["fontname", "size", "non_stroking_color"])
                for word in words:
                    font_name = word.get("fontname", "")
                    if font_name and font_name not in styles:
                        styles[font_name] = {
                            "font_name": font_name,
                            "font_family": font_name.split("+")[-1] if "+" in font_name else font_name,
                            "font_size": word.get("size", 0),
                            "is_bold": "bold" in font_name.lower(),
                            "is_italic": "italic" in font_name.lower(),
                            "color": word.get("non_stroking_color", ""),
                            "pages": [page.page_number]
                        }
                    elif font_name and page.page_number not in styles[font_name]["pages"]:
                        styles[font_name]["pages"].append(page.page_number)
            return styles
        except Exception as e:
            raise StyleExtractionError(f"Failed to extract styles: {str(e)}")

    def _get_page_layout(self, page: Page) -> Dict[str, Any]:
        """Extract page layout information."""
        try:
            return {
                "width": page.width,
                "height": page.height,
                "crop_box": list(page.cropbox),
                "media_box": list(page.mediabox),
                "rotation": page.rotation or 0
            }
        except Exception as e:
            self.logger.warning(f"Failed to extract page layout: {str(e)}")
            return {}

    async def extract_metadata(self, file_path: str) -> Dict[str, str]:
        """
        Extract metadata from PDF file.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Dictionary with metadata
            
        Raises:
            MetadataExtractionError: If extraction fails
        """
        try:
            with pdfplumber.open(file_path) as pdf:
                return self._extract_metadata(pdf)
        except Exception as e:
            logging.error(f"Error extracting metadata: {str(e)}")
            raise MetadataExtractionError(f"Failed to extract metadata from {file_path}: {str(e)}")

    async def extract_images(self, file_path: str, compress: bool = False) -> List[Dict[str, Any]]:
        """
        Extract images from PDF file.
        
        Args:
            file_path: Path to PDF file
            compress: Whether to compress images
            
        Returns:
            List of dictionaries with image data
            
        Raises:
            ImageExtractionError: If extraction fails
        """
        try:
            with pdfplumber.open(file_path) as pdf:
                images = self._extract_images(pdf)
                if compress:
                    for image in images:
                        if "data" in image:
                            # Сжимаем изображение
                            img = Image.open(io.BytesIO(image["data"]))
                            output = io.BytesIO()
                            img.save(output, format=image["format"], optimize=True, quality=85)
                            image["data"] = output.getvalue()
                            image["compressed_size"] = len(image["data"])
                return images
        except Exception as e:
            logging.error(f"Error extracting images: {str(e)}")
            raise ImageExtractionError(f"Failed to extract images from {file_path}: {str(e)}")

    # Алиас для обратной совместимости
    get_metadata = extract_metadata