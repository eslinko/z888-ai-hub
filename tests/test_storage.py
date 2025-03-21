"""
Integration tests for storage implementations.
"""

import uuid
import os
import json
from datetime import datetime, timedelta
import pytest
from supabase import create_client, Client
from z888_ai_hub.storage.database import SupabaseStorage, Document, Paragraph
from z888_ai_hub.config.services import supabase_config
from z888_ai_hub.utils.logging_utils import setup_logger
from z888_ai_hub.storage.database.exceptions import (
    DocumentNotFoundError,
    StorageError,
    InvalidDocumentError,
    InvalidPathError,
    InvalidMetadataError
)
import pytest_asyncio
import asyncio

# Инициализируем логгер для тестов
logger = setup_logger('TestStorage')

# Определяем пути для тестов
WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE_PDFS_DIR = os.path.join("tests", "sample_pdfs")
SAMPLE_JSON_DIR = os.path.join("tests", "sample_pdfs", "json")

# Пути к тестовым файлам
test_filename = "Med_6.3.pdf"
test_abs_path = os.path.join(WORKSPACE_ROOT, SAMPLE_PDFS_DIR, test_filename)
test_rel_path = os.path.join(SAMPLE_PDFS_DIR, test_filename).replace('\\', '/')
test_json_path = os.path.join(SAMPLE_JSON_DIR, "Med_6.3.json")

# Проверяем существование файлов при запуске тестов
def check_test_files():
    """Проверяет наличие необходимых тестовых файлов."""
    if not os.path.isfile(test_abs_path):
        raise FileNotFoundError(f"Test PDF file not found: {test_abs_path}")
    if not os.path.isfile(test_json_path):
        raise FileNotFoundError(f"Test JSON file not found: {test_json_path}")

check_test_files()

# Получаем реальный размер файла
file_size = os.path.getsize(test_abs_path)

# Загружаем данные из JSON
with open(test_json_path, 'r', encoding='utf-8') as f:
    json_data = json.load(f)
    logger.debug(f"Loaded JSON data with {len(json_data['paragraphs'])} paragraphs")

class TestSupabaseStorageIntegration:
    """Integration test cases for SupabaseStorage class."""

    @pytest.fixture
    def test_document(self):
        """Фикстура для создания тестового документа."""
        document = Document(
            file_id=str(uuid.uuid4()),
            relative_path=test_rel_path,
            file_name=test_filename,
            summary=json_data.get("summary", "This is a test document summary"),
            metadata={
                "size": file_size,
                "page_count": json_data["metadata"].get("page_count", 1),
                "language": json_data["metadata"].get("language", "EN"),
                "is_test": True
            },
            created_at=datetime.fromisoformat("2024-03-17T12:00:00"),
            updated_at=datetime.fromisoformat("2024-03-17T12:00:00")
        )
        logger.debug(f"Created test document with ID: {document.file_id}")
        return document

    @pytest.fixture
    def test_paragraphs(self, test_document):
        """Фикстура для создания тестовых параграфов."""
        paragraphs = [
            Paragraph(
                text=p["text"],
                file_id=test_document.file_id,
                position_in_file=i,
                metadata={"page_number": p.get("page_number")}
            )
            for i, p in enumerate(json_data["paragraphs"])
        ]
        logger.debug(f"Created {len(paragraphs)} test paragraphs")
        test_document.paragraphs = paragraphs
        return paragraphs

    @pytest_asyncio.fixture
    async def storage(self):
        """Фикстура для создания тестового хранилища."""
        storage = SupabaseStorage()
        yield storage
        # Очистка после тестов
        try:
            await storage.delete_document(test_document.file_id)
        except:
            pass

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_save_and_retrieve_document(self, storage, test_document):
        """Integration test for document saving and retrieval."""
        # Сохраняем документ
        await storage.save_document(test_document)

        # Получаем документ
        retrieved_doc = await storage.get_document(test_document.file_id)

        # Проверяем корректность сохранения и получения
        assert retrieved_doc is not None, "Document should be retrieved"
        assert retrieved_doc.file_id == test_document.file_id, "Document ID should match"
        assert retrieved_doc.relative_path == test_document.relative_path, "Document path should match"
        assert retrieved_doc.file_name == test_document.file_name, "Document name should match"
        assert retrieved_doc.summary == test_document.summary, "Document summary should match"
        assert retrieved_doc.metadata == test_document.metadata, "Document metadata should match"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_document_operations(self, storage, test_document):
        """Integration test for document operations."""
        # Сохраняем документ
        await storage.save_document(test_document)

        # Обновляем метаданные
        test_document.metadata["updated"] = True
        await storage.update_document(test_document)

        # Проверяем обновление
        updated_doc = await storage.get_document(test_document.file_id)
        assert updated_doc.metadata["updated"] is True, "Document should be updated"

        # Удаляем документ
        await storage.delete_document(test_document.file_id)

        # Проверяем удаление
        deleted_doc = await storage.get_document(test_document.file_id)
        assert deleted_doc is None, "Document should be deleted"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_paragraph_operations(self, storage, test_document, test_paragraphs):
        """Integration test for paragraph operations."""
        # Сохраняем документ с параграфами
        test_document.paragraphs = test_paragraphs
        await storage.save_document(test_document)

        # Получаем документ
        retrieved_doc = await storage.get_document(test_document.file_id)

        # Проверяем параграфы
        assert len(retrieved_doc.paragraphs) == len(test_paragraphs), "Number of paragraphs should match"
        for saved_p, test_p in zip(retrieved_doc.paragraphs, test_paragraphs):
            assert saved_p.text == test_p.text, "Paragraph text should match"
            assert saved_p.file_id == test_p.file_id, "Paragraph file_id should match"
            assert saved_p.position_in_file == test_p.position_in_file, "Paragraph position should match"
            assert saved_p.metadata == test_p.metadata, "Paragraph metadata should match"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_document_search(self, storage, test_document):
        """Integration test for document search."""
        # Сохраняем документ
        await storage.save_document(test_document)

        # Ищем документ по различным критериям
        by_id = await storage.search_documents({"file_id": test_document.file_id})
        assert len(by_id) == 1, "Should find document by ID"
        assert by_id[0].file_id == test_document.file_id, "Found document should match"

        by_name = await storage.search_documents({"file_name": test_document.file_name})
        assert len(by_name) > 0, "Should find document by name"
        assert any(doc.file_name == test_document.file_name for doc in by_name), "Found document should match"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_document_filtering(self, storage, test_document):
        """Integration test for document filtering."""
        # Сохраняем документ
        await storage.save_document(test_document)

        # Фильтруем документы
        filtered = await storage.filter_documents({
            "metadata": {"is_test": True}
        })
        assert len(filtered) > 0, "Should find test documents"
        assert all(doc.metadata.get("is_test") is True for doc in filtered), "All documents should be test documents"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_document_pagination(self, storage, test_document):
        """Integration test for document pagination."""
        # Создаем несколько тестовых документов
        documents = []
        for i in range(5):
            doc = Document(
                file_id=str(uuid.uuid4()),
                relative_path=f"test/path/doc_{i}.pdf",
                file_name=f"doc_{i}.pdf",
                summary=f"Test document {i}",
                metadata={"size": 1000, "page_count": 1, "language": "EN"},
                created_at=datetime.now() + timedelta(days=i),
                updated_at=datetime.now() + timedelta(days=i)
            )
            documents.append(doc)
            await storage.save_document(doc)

        # Тестируем пагинацию
        page1 = await storage.get_documents(page=1, per_page=2)
        assert len(page1) == 2, "First page should have 2 documents"

        page2 = await storage.get_documents(page=2, per_page=2)
        assert len(page2) == 2, "Second page should have 2 documents"

        # Очищаем тестовые документы
        for doc in documents:
            await storage.delete_document(doc.file_id)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, storage, test_document):
        """Integration test for concurrent operations."""
        # Сохраняем документ
        await storage.save_document(test_document)

        # Создаем задачи для параллельного обновления
        async def update_document():
            doc = await storage.get_document(test_document.file_id)
            doc.metadata["concurrent_update"] = True
            await storage.update_document(doc)

        # Запускаем параллельные обновления
        tasks = [update_document() for _ in range(3)]
        await asyncio.gather(*tasks)

        # Проверяем результат
        final_doc = await storage.get_document(test_document.file_id)
        assert final_doc.metadata.get("concurrent_update") is True, "Document should be updated"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_document_versioning(self, storage, test_document):
        """Integration test for document versioning."""
        # Сохраняем начальную версию
        await storage.save_document(test_document)

        # Обновляем документ
        test_document.summary = "Updated summary"
        await storage.update_document(test_document)

        # Проверяем версионирование
        versions = await storage.get_document_versions(test_document.file_id)
        assert len(versions) >= 2, "Should have at least 2 versions"
        assert versions[0].summary == "Updated summary", "Latest version should have updated summary"
        assert versions[-1].summary == "This is a test document summary", "Oldest version should have original summary"

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_document_cleanup(self, storage, test_document):
        """Integration test for document cleanup."""
        # Сохраняем документ
        await storage.save_document(test_document)

        # Создаем временные данные
        temp_data = {"temp": "data"}
        await storage.save_temp_data(test_document.file_id, temp_data)

        # Запускаем очистку
        await storage.cleanup_document(test_document.file_id)

        # Проверяем, что все данные удалены
        doc = await storage.get_document(test_document.file_id)
        assert doc is None, "Document should be deleted"
        temp = await storage.get_temp_data(test_document.file_id)
        assert temp is None, "Temporary data should be deleted"
