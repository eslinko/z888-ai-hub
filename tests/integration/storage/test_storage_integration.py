"""
Integration tests for storage.
"""

import os
import pytest
from datetime import datetime
from z888_ai_hub.storage.database import SupabaseStorage
from z888_ai_hub.utils.logging_utils import setup_logger

logger = setup_logger('TestStorageIntegration')

@pytest.fixture(scope="session")
def storage():
    """Создает экземпляр хранилища для тестов."""
    storage = SupabaseStorage()
    # Очищаем тестовые данные перед началом тестов
    storage.cleanup_test_data()
    yield storage
    # Очищаем тестовые данные после завершения тестов
    storage.cleanup_test_data()

@pytest.mark.integration
@pytest.mark.asyncio
async def test_save_and_retrieve_document(storage):
    """Тестирует сохранение и получение документа."""
    # Создаем тестовый документ
    doc = {
        "file_id": "test_integration_file_id",
        "relative_path": "test/path/file.pdf",
        "file_name": "file.pdf",
        "summary": "Test integration summary",
        "metadata": {
            "page_count": 1,
            "author": "Test Author",
            "created_at": datetime.now().isoformat()
        }
    }
    
    # Сохраняем документ
    await storage.save_document(doc)
    
    # Получаем документ
    saved_doc = await storage.get_document(doc["file_id"])
    
    # Проверяем результат
    assert saved_doc is not None, "Document should be saved"
    assert saved_doc["file_id"] == doc["file_id"], "File ID should match"
    assert saved_doc["relative_path"] == doc["relative_path"], "Path should match"
    assert saved_doc["file_name"] == doc["file_name"], "Name should match"
    assert saved_doc["summary"] == doc["summary"], "Summary should match"
    assert saved_doc["metadata"] == doc["metadata"], "Metadata should match"

@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_document(storage):
    """Тестирует обновление документа."""
    # Создаем и сохраняем документ
    doc = {
        "file_id": "test_update_file_id",
        "relative_path": "test/path/file.pdf",
        "file_name": "file.pdf",
        "summary": "Initial summary",
        "metadata": {
            "page_count": 1,
            "author": "Test Author",
            "created_at": datetime.now().isoformat()
        }
    }
    await storage.save_document(doc)
    
    # Обновляем документ
    doc["summary"] = "Updated summary"
    await storage.update_document(doc)
    
    # Получаем обновленный документ
    updated_doc = await storage.get_document(doc["file_id"])
    
    # Проверяем результат
    assert updated_doc is not None, "Document should be updated"
    assert updated_doc["summary"] == "Updated summary", "Summary should be updated"

@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_document(storage):
    """Тестирует удаление документа."""
    # Создаем и сохраняем документ
    doc = {
        "file_id": "test_delete_file_id",
        "relative_path": "test/path/file.pdf",
        "file_name": "file.pdf",
        "summary": "Test summary",
        "metadata": {
            "page_count": 1,
            "author": "Test Author",
            "created_at": datetime.now().isoformat()
        }
    }
    await storage.save_document(doc)
    
    # Удаляем документ
    await storage.delete_document(doc["file_id"])
    
    # Проверяем, что документ удален
    deleted_doc = await storage.get_document(doc["file_id"])
    assert deleted_doc is None, "Document should be deleted"

@pytest.mark.integration
@pytest.mark.asyncio
async def test_save_and_retrieve_paragraphs(storage):
    """Тестирует сохранение и получение параграфов."""
    # Создаем тестовый документ
    doc = {
        "file_id": "test_paragraphs_file_id",
        "relative_path": "test/path/file.pdf",
        "file_name": "file.pdf",
        "summary": "Test summary",
        "metadata": {
            "page_count": 1,
            "author": "Test Author",
            "created_at": datetime.now().isoformat()
        }
    }
    await storage.save_document(doc)
    
    # Создаем параграфы
    paragraphs = [
        {
            "id": "p1",
            "document_id": doc["file_id"],
            "content": "Test paragraph 1",
            "page_number": 1,
            "position": 0
        },
        {
            "id": "p2",
            "document_id": doc["file_id"],
            "content": "Test paragraph 2",
            "page_number": 1,
            "position": 1
        }
    ]
    
    # Сохраняем параграфы
    await storage.save_paragraphs(paragraphs)
    
    # Получаем параграфы
    saved_paragraphs = await storage.get_paragraphs(doc["file_id"])
    
    # Проверяем результат
    assert len(saved_paragraphs) == 2, "Should have 2 paragraphs"
    assert saved_paragraphs[0]["content"] == "Test paragraph 1", "First paragraph should match"
    assert saved_paragraphs[1]["content"] == "Test paragraph 2", "Second paragraph should match"

@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_documents(storage):
    """Тестирует поиск документов."""
    # Создаем тестовые документы
    docs = [
        {
            "file_id": f"test_search_file_id_{i}",
            "relative_path": f"test/path/file_{i}.pdf",
            "file_name": f"file_{i}.pdf",
            "summary": f"Test summary {i}",
            "metadata": {
                "page_count": 1,
                "author": "Test Author",
                "created_at": datetime.now().isoformat()
            }
        }
        for i in range(3)
    ]
    
    for doc in docs:
        await storage.save_document(doc)
    
    # Ищем документы
    search_results = await storage.search_documents("Test summary")
    
    # Проверяем результат
    assert len(search_results) >= 3, "Should find at least 3 documents"
    assert all(doc["file_id"].startswith("test_search_file_id_") for doc in search_results), "Should find test documents" 