"""
Integration tests for Supabase storage.
"""

import os
import pytest
from datetime import datetime
from z888_ai_hub.storage.supabase import SupabaseStorage
from z888_ai_hub.utils.logging_utils import setup_logger

logger = setup_logger('TestSupabaseStorageIntegration')

@pytest.fixture(scope="session")
def storage():
    """Создает экземпляр Supabase хранилища для тестов."""
    return SupabaseStorage(
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_key=os.getenv("SUPABASE_KEY")
    )

@pytest.fixture(scope="function")
async def cleanup_test_data(storage):
    """Очищает тестовые данные до и после каждого теста."""
    # Очищаем тестовые данные перед тестом
    await storage.delete_document("test_document_id")
    await storage.delete_document("test_document_id_2")
    
    yield
    
    # Очищаем тестовые данные после теста
    await storage.delete_document("test_document_id")
    await storage.delete_document("test_document_id_2")

@pytest.mark.integration
@pytest.mark.asyncio
async def test_save_and_retrieve_document(storage, cleanup_test_data):
    """Тестирует сохранение и получение документа."""
    test_document = {
        "id": "test_document_id",
        "file_id": "test_file_id",
        "relative_path": "test/path/document.pdf",
        "file_name": "document.pdf",
        "summary": "Test document summary",
        "paragraphs": [
            {
                "id": "test_paragraph_id",
                "document_id": "test_document_id",
                "content": "Test paragraph content",
                "order": 1
            }
        ],
        "metadata": {
            "author": "Test Author",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    }
    
    # Сохраняем документ
    await storage.save_document(test_document)
    
    # Получаем документ
    retrieved_document = await storage.get_document("test_document_id")
    
    assert retrieved_document is not None
    assert retrieved_document["id"] == test_document["id"]
    assert retrieved_document["file_id"] == test_document["file_id"]
    assert retrieved_document["relative_path"] == test_document["relative_path"]
    assert retrieved_document["file_name"] == test_document["file_name"]
    assert retrieved_document["summary"] == test_document["summary"]
    assert len(retrieved_document["paragraphs"]) == 1
    assert retrieved_document["paragraphs"][0]["content"] == "Test paragraph content"
    assert retrieved_document["metadata"]["author"] == "Test Author"

@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_document(storage, cleanup_test_data):
    """Тестирует обновление документа."""
    test_document = {
        "id": "test_document_id",
        "file_id": "test_file_id",
        "relative_path": "test/path/document.pdf",
        "file_name": "document.pdf",
        "summary": "Initial summary",
        "paragraphs": [],
        "metadata": {
            "author": "Test Author",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    }
    
    # Сохраняем документ
    await storage.save_document(test_document)
    
    # Обновляем документ
    updated_document = test_document.copy()
    updated_document["summary"] = "Updated summary"
    updated_document["metadata"]["author"] = "Updated Author"
    await storage.update_document(updated_document)
    
    # Получаем обновленный документ
    retrieved_document = await storage.get_document("test_document_id")
    
    assert retrieved_document["summary"] == "Updated summary"
    assert retrieved_document["metadata"]["author"] == "Updated Author"

@pytest.mark.integration
@pytest.mark.asyncio
async def test_delete_document(storage, cleanup_test_data):
    """Тестирует удаление документа."""
    test_document = {
        "id": "test_document_id",
        "file_id": "test_file_id",
        "relative_path": "test/path/document.pdf",
        "file_name": "document.pdf",
        "summary": "Test summary",
        "paragraphs": [],
        "metadata": {
            "author": "Test Author",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    }
    
    # Сохраняем документ
    await storage.save_document(test_document)
    
    # Удаляем документ
    await storage.delete_document("test_document_id")
    
    # Проверяем, что документ удален
    retrieved_document = await storage.get_document("test_document_id")
    assert retrieved_document is None

@pytest.mark.integration
@pytest.mark.asyncio
async def test_save_and_retrieve_paragraphs(storage, cleanup_test_data):
    """Тестирует сохранение и получение параграфов."""
    test_document = {
        "id": "test_document_id",
        "file_id": "test_file_id",
        "relative_path": "test/path/document.pdf",
        "file_name": "document.pdf",
        "summary": "Test summary",
        "paragraphs": [],
        "metadata": {
            "author": "Test Author",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    }
    
    # Сохраняем документ
    await storage.save_document(test_document)
    
    # Сохраняем параграфы
    test_paragraphs = [
        {
            "id": "test_paragraph_id_1",
            "document_id": "test_document_id",
            "content": "First paragraph",
            "order": 1
        },
        {
            "id": "test_paragraph_id_2",
            "document_id": "test_document_id",
            "content": "Second paragraph",
            "order": 2
        }
    ]
    
    await storage.save_paragraphs(test_paragraphs)
    
    # Получаем документ с параграфами
    retrieved_document = await storage.get_document("test_document_id")
    
    assert len(retrieved_document["paragraphs"]) == 2
    assert retrieved_document["paragraphs"][0]["content"] == "First paragraph"
    assert retrieved_document["paragraphs"][1]["content"] == "Second paragraph"

@pytest.mark.integration
@pytest.mark.asyncio
async def test_search_documents(storage, cleanup_test_data):
    """Тестирует поиск документов."""
    # Создаем тестовые документы
    test_documents = [
        {
            "id": "test_document_id_1",
            "file_id": "test_file_id_1",
            "relative_path": "test/path/document1.pdf",
            "file_name": "document1.pdf",
            "summary": "First test document",
            "paragraphs": [],
            "metadata": {
                "author": "Test Author 1",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
        },
        {
            "id": "test_document_id_2",
            "file_id": "test_file_id_2",
            "relative_path": "test/path/document2.pdf",
            "file_name": "document2.pdf",
            "summary": "Second test document",
            "paragraphs": [],
            "metadata": {
                "author": "Test Author 2",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
        }
    ]
    
    # Сохраняем документы
    for doc in test_documents:
        await storage.save_document(doc)
    
    # Ищем документы
    search_results = await storage.search_documents("test document")
    
    assert len(search_results) == 2
    assert any(doc["id"] == "test_document_id_1" for doc in search_results)
    assert any(doc["id"] == "test_document_id_2" for doc in search_results)

@pytest.mark.integration
@pytest.mark.asyncio
async def test_filter_documents_by_metadata(storage, cleanup_test_data):
    """Тестирует фильтрацию документов по метаданным."""
    # Создаем тестовые документы
    test_documents = [
        {
            "id": "test_document_id_1",
            "file_id": "test_file_id_1",
            "relative_path": "test/path/document1.pdf",
            "file_name": "document1.pdf",
            "summary": "First test document",
            "paragraphs": [],
            "metadata": {
                "author": "Test Author 1",
                "category": "test",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
        },
        {
            "id": "test_document_id_2",
            "file_id": "test_file_id_2",
            "relative_path": "test/path/document2.pdf",
            "file_name": "document2.pdf",
            "summary": "Second test document",
            "paragraphs": [],
            "metadata": {
                "author": "Test Author 2",
                "category": "production",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
        }
    ]
    
    # Сохраняем документы
    for doc in test_documents:
        await storage.save_document(doc)
    
    # Фильтруем документы по категории
    filtered_documents = await storage.filter_documents({"metadata": {"category": "test"}})
    
    assert len(filtered_documents) == 1
    assert filtered_documents[0]["id"] == "test_document_id_1"
    assert filtered_documents[0]["metadata"]["category"] == "test" 