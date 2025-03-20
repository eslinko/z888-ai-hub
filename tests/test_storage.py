"""
Tests for storage implementations.
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
from unittest.mock import patch
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


@pytest.fixture
def test_document():
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
            "is_test": True  # Помечаем документ как тестовый
        },
        created_at=datetime.fromisoformat("2024-03-17T12:00:00"),
        updated_at=datetime.fromisoformat("2024-03-17T12:00:00")
    )
    logger.debug(f"Created test document with ID: {document.file_id}")
    return document


@pytest.fixture
def test_paragraphs(test_document):
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
    
    # Добавляем параграфы к документу
    test_document.paragraphs = paragraphs
    
    return paragraphs


@pytest_asyncio.fixture
async def storage(request):
    """
    Фикстура для создания экземпляра SupabaseStorage.
    """
    logger.debug("Initializing Supabase client and storage")
    client = create_client(supabase_config.url, supabase_config.api_key)
    storage = SupabaseStorage(client)

    # Очищаем тестовые данные перед каждым тестом
    async def cleanup():
        """Очищаем тестовые данные."""
        logger.debug("Running pre-test cleanup")
        try:
            # Получаем все тестовые документы
            response = client.table('source_files').select('id').execute()
            if hasattr(response, 'error') and response.error is not None:
                logger.warning(f"Error during cleanup: {response.error}")
                return

            # Удаляем каждый документ
            for doc in response.data:
                try:
                    # Удаляем параграфы
                    paragraphs_response = client.table('paragraphs').delete().eq(
                        'id', doc['id']
                    ).execute()
                    if hasattr(paragraphs_response, 'error') and paragraphs_response.error is not None:
                        logger.warning(f"Error deleting paragraphs: {paragraphs_response.error}")

                    # Удаляем документ
                    doc_response = client.table('source_files').delete().eq(
                        'id', doc['id']
                    ).execute()
                    if hasattr(doc_response, 'error') and doc_response.error is not None:
                        logger.warning(f"Error deleting document: {doc_response.error}")

                except Exception as e:
                    logger.warning(f"Error during document cleanup: {str(e)}")
                    continue

        except Exception as e:
            logger.warning(f"Error during cleanup: {str(e)}")

    # Очищаем данные перед тестом
    await cleanup()

    yield storage

    # Очищаем данные после теста
    logger.debug(f"Cleaning up test data")
    await cleanup()
    logger.debug(f"Finished cleanup for test: {request.node.name}")


class TestSupabaseStorage:
    """
    Тесты для SupabaseStorage.
    """

    @pytest.mark.asyncio
    async def test_save_document(self, storage: SupabaseStorage, test_document: Document):
        """Тест сохранения документа."""
        logger.info("Testing document saving")

        # Сохраняем документ
        await storage.save_document(test_document)

        # Получаем сохраненный документ
        saved_doc = await storage.get_document(test_document.file_id)

        # Проверяем, что документ сохранен корректно
        assert saved_doc is not None, "Document should be saved"
        assert saved_doc.file_id == test_document.file_id, "Document ID should match"
        assert saved_doc.relative_path == test_document.relative_path, "Document path should match"
        assert saved_doc.file_name == test_document.file_name, "Document name should match"
        assert saved_doc.summary == test_document.summary, "Document summary should match"
        assert saved_doc.metadata == test_document.metadata, "Document metadata should match"

    @pytest.mark.asyncio
    async def test_get_document(self, storage: SupabaseStorage, test_document: Document):
        """Тест получения документа."""
        logger.info("Testing document retrieval")

        # Сохраняем документ
        await storage.save_document(test_document)

        # Получаем документ
        doc = await storage.get_document(test_document.file_id)

        # Проверяем, что документ получен корректно
        assert doc is not None, "Document should be retrieved"
        assert doc.file_id == test_document.file_id, "Document ID should match"
        assert doc.relative_path == test_document.relative_path, "Document path should match"
        assert doc.file_name == test_document.file_name, "Document name should match"
        assert doc.summary == test_document.summary, "Document summary should match"
        assert doc.metadata == test_document.metadata, "Document metadata should match"

    @pytest.mark.asyncio
    async def test_delete_document(self, storage: SupabaseStorage, test_document: Document):
        """Тест удаления документа."""
        logger.info("Testing document deletion")

        # Сохраняем документ
        await storage.save_document(test_document)

        # Удаляем документ
        await storage.delete_document(test_document.file_id)

        # Проверяем, что документ удален
        doc = await storage.get_document(test_document.file_id)
        assert doc is None, "Document should be deleted"

    @pytest.mark.asyncio
    async def test_document_metadata(self, storage: SupabaseStorage, test_document: Document):
        """Тест метаданных документа."""
        logger.info("Testing document metadata")

        # Сохраняем документ
        await storage.save_document(test_document)

        # Получаем документ
        doc = await storage.get_document(test_document.file_id)

        # Проверяем метаданные
        assert doc.metadata == test_document.metadata, "Document metadata should match"
        assert doc.metadata['size'] == file_size, "Document size should match"
        assert doc.metadata['is_test'] is True, "Document should be marked as test"

    @pytest.mark.asyncio
    async def test_document_paragraphs(self, storage: SupabaseStorage, test_document: Document):
        """Тест параграфов документа."""
        logger.info("Testing document paragraphs")

        # Сохраняем документ
        await storage.save_document(test_document)

        # Получаем документ
        doc = await storage.get_document(test_document.file_id)

        # Проверяем параграфы
        assert len(doc.paragraphs) == len(test_document.paragraphs), "Number of paragraphs should match"
        for saved_p, test_p in zip(doc.paragraphs, test_document.paragraphs):
            assert saved_p.text == test_p.text, "Paragraph text should match"
            assert saved_p.file_id == test_p.file_id, "Paragraph file_id should match"
            assert saved_p.position_in_file == test_p.position_in_file, "Paragraph position should match"
            assert saved_p.metadata == test_p.metadata, "Paragraph metadata should match"

    @pytest.mark.asyncio
    async def test_save_invalid_document(self, storage: SupabaseStorage):
        """Тест сохранения невалидного документа."""
        logger.info("Testing invalid document handling")

        # Создаем документ с пустым путем
        with pytest.raises(InvalidPathError):
            doc = Document(
                file_id=str(uuid.uuid4()),
                relative_path="",  # Пустой путь
                file_name="test.pdf",
                summary="Test document",
                metadata={"size": 100},
                paragraphs=[],
                created_at=datetime.now(),
                updated_at=datetime.now()
            )

    @pytest.mark.asyncio
    async def test_save_document_with_invalid_paragraphs(self, storage: SupabaseStorage):
        """Тест сохранения документа с невалидными параграфами."""
        logger.info("Testing invalid paragraphs handling")

        # Создаем документ с пустым текстом в параграфе
        with pytest.raises(InvalidDocumentError) as exc_info:
            doc = Document(
                file_id=str(uuid.uuid4()),
                relative_path=test_rel_path,
                file_name=test_filename,
                summary="Test document",
                metadata={"size": 100},
                paragraphs=[
                    Paragraph(
                        text="",  # Пустой текст
                        file_id=str(uuid.uuid4()),
                        position_in_file=0,
                        metadata={}
                    )
                ],
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        assert str(exc_info.value) == "Paragraph text cannot be empty"

    @pytest.mark.asyncio
    async def test_save_document_with_mismatched_file_ids(self, storage: SupabaseStorage):
        """Тест сохранения документа с несовпадающими file_id."""
        logger.info("Testing mismatched file_ids handling")

        # Создаем документ с несовпадающими file_id
        with pytest.raises(InvalidDocumentError) as exc_info:
            doc = Document(
                file_id=str(uuid.uuid4()),
                relative_path=test_rel_path,
                file_name=test_filename,
                summary="Test document",
                metadata={"size": 100},
                paragraphs=[
                    Paragraph(
                        text="Test text",
                        file_id=str(uuid.uuid4()),  # Другой file_id
                        position_in_file=0,
                        metadata={}
                    )
                ],
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        assert str(exc_info.value) == "Paragraph file_id must match document file_id"

    @pytest.mark.asyncio
    async def test_save_document_with_duplicate_positions(self, storage: SupabaseStorage):
        """Тест сохранения документа с дублирующимися позициями параграфов."""
        logger.info("Testing duplicate paragraph positions handling")

        # Создаем документ с дублирующимися позициями
        doc_id = str(uuid.uuid4())
        with pytest.raises(InvalidDocumentError) as exc_info:
            doc = Document(
                file_id=doc_id,
                relative_path=test_rel_path,
                file_name=test_filename,
                summary="Test document",
                metadata={"size": 100},
                paragraphs=[
                    Paragraph(
                        text="Test text 1",
                        file_id=doc_id,
                        position_in_file=0,  # Одинаковые позиции
                        metadata={}
                    ),
                    Paragraph(
                        text="Test text 2",
                        file_id=doc_id,
                        position_in_file=0,  # Одинаковые позиции
                        metadata={}
                    )
                ],
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        assert str(exc_info.value) == "Duplicate paragraph positions are not allowed"

    @pytest.mark.asyncio
    async def test_invalid_path_characters(self, storage: SupabaseStorage):
        """Тест обработки недопустимых символов в пути."""
        logger.info("Testing invalid path characters handling")

        invalid_paths = [
            "test?.pdf",  # Знак вопроса
            "test*.pdf",  # Звездочка
            "test<>.pdf",  # Угловые скобки
            'test".pdf',  # Кавычки
            "test|.pdf",  # Вертикальная черта
        ]

        for path in invalid_paths:
            with pytest.raises(InvalidPathError):
                doc = Document(
                    file_id=str(uuid.uuid4()),
                    relative_path=path,
                    file_name=path,
                    summary="Test document",
                    metadata={"size": 100},
                    paragraphs=[],
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )

    @pytest.mark.asyncio
    async def test_empty_path_components(self, storage: SupabaseStorage):
        """Тест обработки пустых компонентов пути."""
        logger.info("Testing empty path components handling")

        invalid_paths = [
            "//document.pdf",  # Двойной слеш
            "test//document.pdf",  # Двойной слеш в середине
            "test/./document.pdf",  # Текущая директория
            "test/../document.pdf",  # Родительская директория
        ]

        for path in invalid_paths:
            with pytest.raises(InvalidPathError):
                doc = Document(
                    file_id=str(uuid.uuid4()),
                    relative_path=path,
                    file_name="document.pdf",
                    summary="Test document",
                    metadata={"size": 100},
                    paragraphs=[],
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )

    @pytest.mark.asyncio
    async def test_normalize_path_separators(self, storage: SupabaseStorage, test_document: Document):
        """Тест нормализации разделителей в путях."""
        logger.info("Testing path separators normalization")

        # Создаем документ с Windows-стиль путем
        doc_with_windows_path = Document(
            file_id=str(uuid.uuid4()),
            relative_path="sample_pdfs\\document.pdf",  # Windows path
            file_name="document.pdf",
            summary="Test document with Windows path",
            metadata=test_document.metadata.copy(),
            paragraphs=[],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        # Сохраняем документ
        await storage.save_document(doc_with_windows_path)

        # Получаем сохраненный документ
        saved_doc = await storage.get_document(doc_with_windows_path.file_id)

        # Проверяем, что путь нормализован
        assert '\\' not in saved_doc.relative_path, "Path should not contain backslashes"
        assert saved_doc.relative_path == "sample_pdfs/document.pdf", "Path should be normalized"

    @pytest.mark.asyncio
    async def test_metadata_required_fields(self, storage: SupabaseStorage, test_document: Document):
        """Тест обязательных полей метаданных."""
        logger.info("Testing required metadata fields")

        # Создаем документ без обязательных полей в метаданных
        with pytest.raises(InvalidMetadataError) as exc_info:
            doc_without_required = Document(
                file_id=str(uuid.uuid4()),
                relative_path=test_rel_path,
                file_name=test_filename,
                summary="Test document without required metadata",
                metadata={
                    # Отсутствует size
                    "optional_field": "value"
                },
                paragraphs=[],
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        assert str(exc_info.value) == "Metadata must contain 'size' field"

    @pytest.mark.asyncio
    async def test_metadata_types(self, storage: SupabaseStorage, test_document: Document):
        """Тест типов данных в метаданных."""
        logger.info("Testing metadata field types")

        invalid_metadata_cases = [
            {
                "size": "not_a_number",  # Строка вместо числа
            },
            {
                "size": -100,  # Отрицательный размер
            },
            {
                "size": file_size,
                "page_count": "not_a_number"  # Строка вместо числа
            }
        ]

        for invalid_metadata in invalid_metadata_cases:
            with pytest.raises(InvalidMetadataError) as exc_info:
                Document(
                    file_id=str(uuid.uuid4()),
                    relative_path=test_rel_path,
                    file_name=test_filename,
                    summary="Test document with invalid metadata types",
                    metadata=invalid_metadata,
                    paragraphs=[],
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )

    @pytest.mark.asyncio
    async def test_metadata_preservation(self, storage: SupabaseStorage, test_document: Document):
        """Тест сохранения всех метаданных при операциях с документом."""
        logger.info("Testing metadata preservation")

        # Добавляем дополнительные метаданные
        test_document.metadata.update({
            "custom_field": "custom_value",
            "nested_data": {
                "key1": "value1",
                "key2": 42
            },
            "tags": ["tag1", "tag2", "tag3"]
        })

        # Сохраняем документ
        await storage.save_document(test_document)

        # Получаем сохраненный документ
        saved_doc = await storage.get_document(test_document.file_id)

        # Проверяем, что все метаданные сохранены
        assert saved_doc.metadata == test_document.metadata, "All metadata should be preserved"
        assert saved_doc.metadata["custom_field"] == "custom_value", "Custom field should be preserved"
        assert saved_doc.metadata["nested_data"]["key1"] == "value1", "Nested data should be preserved"
        assert saved_doc.metadata["tags"] == ["tag1", "tag2", "tag3"], "Lists should be preserved"

    @pytest.mark.asyncio
    async def test_metadata_update(self, storage: SupabaseStorage, test_document: Document):
        """Тест обновления метаданных документа."""
        logger.info("Testing metadata update")

        # Сначала сохраняем документ
        await storage.save_document(test_document)

        # Обновляем метаданные
        test_document.metadata.update({
            "new_field": "new_value",
            "updated_at": datetime.now().isoformat()
        })

        # Сохраняем обновленный документ
        await storage.save_document(test_document)

        # Получаем обновленный документ
        updated_doc = await storage.get_document(test_document.file_id)

        # Проверяем, что метаданные обновлены
        assert updated_doc.metadata == test_document.metadata, "Metadata should be updated"
        assert "new_field" in updated_doc.metadata, "New field should be added"
        assert updated_doc.metadata["new_field"] == "new_value", "New field value should match"

    @pytest.mark.asyncio
    async def test_metadata_size_validation(self, storage: SupabaseStorage, test_document: Document):
        """Тест валидации размера метаданных."""
        logger.info("Testing metadata size validation")

        # Создаем документ с очень большими метаданными
        large_metadata = {
            "size": file_size,
            "large_field": "x" * 1000000  # Очень большое поле
        }

        with pytest.raises(InvalidMetadataError) as exc_info:
            doc_with_large_metadata = Document(
                file_id=str(uuid.uuid4()),
                relative_path=test_rel_path,
                file_name=test_filename,
                summary="Test document with large metadata",
                metadata=large_metadata,
                paragraphs=[],
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        assert "Metadata size" in str(exc_info.value) and "exceeds limit" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_paragraph_operations(self, storage: SupabaseStorage, test_document: Document):
        """Тест операций с параграфами."""
        logger.info("Testing paragraph operations")

        # Сохраняем документ с параграфами
        await storage.save_document(test_document)

        # Получаем документ
        doc = await storage.get_document(test_document.file_id)

        # Проверяем операции с параграфами
        assert len(doc.paragraphs) > 0, "Document should have paragraphs"
        
        # Проверяем сортировку параграфов
        positions = [p.position_in_file for p in doc.paragraphs]
        assert positions == sorted(positions), "Paragraphs should be sorted by position"

        # Проверяем уникальность позиций
        assert len(positions) == len(set(positions)), "Paragraph positions should be unique"

    @pytest.mark.asyncio
    async def test_batch_operations(self, storage: SupabaseStorage):
        """Тест пакетных операций с документами."""
        logger.info("Testing batch operations")

        # Создаем несколько тестовых документов
        documents = []
        for i in range(3):
            doc = Document(
                file_id=str(uuid.uuid4()),
                relative_path=f"test_{i}.pdf",
                file_name=f"test_{i}.pdf",
                summary=f"Test document {i}",
                metadata={"size": 100, "batch_test": True},
                paragraphs=[
                    Paragraph(
                        text=f"Test paragraph {i}",
                        file_id=str(uuid.uuid4()),
                        position_in_file=0,
                        metadata={"page_number": 1}
                    )
                ],
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            documents.append(doc)

        # Сохраняем документы
        for doc in documents:
            await storage.save_document(doc)

        # Проверяем, что все документы сохранены
        for doc in documents:
            saved_doc = await storage.get_document(doc.file_id)
            assert saved_doc is not None, f"Document {doc.file_id} should be saved"
            assert saved_doc.metadata["batch_test"] is True, "Batch test flag should be preserved"

    @pytest.mark.asyncio
    async def test_document_search(self, storage: SupabaseStorage):
        """Тест поиска документов."""
        logger.info("Testing document search")

        # Создаем тестовые документы с разными метаданными
        test_docs = [
            Document(
                file_id=str(uuid.uuid4()),
                relative_path=f"search_test_{i}.pdf",
                file_name=f"search_test_{i}.pdf",
                summary=f"Test document {i}",
                metadata={
                    "size": 100,
                    "category": "test",
                    "tags": ["tag1", "tag2"],
                    "search_test": True
                },
                paragraphs=[],
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            for i in range(3)
        ]

        # Сохраняем документы
        for doc in test_docs:
            await storage.save_document(doc)

        # Тестируем поиск по метаданным
        search_results = await storage.search_documents({"category": "test"})
        assert len(search_results) == 3, "Should find all test documents"

        # Тестируем поиск по тегам
        tag_results = await storage.search_documents({"tags": ["tag1"]})
        assert len(tag_results) == 3, "Should find documents with tag1"

        # Тестируем поиск по нескольким критериям
        multi_results = await storage.search_documents({
            "category": "test",
            "tags": ["tag1"]
        })
        assert len(multi_results) == 3, "Should find documents matching all criteria"

    @pytest.mark.asyncio
    async def test_document_filtering(self, storage: SupabaseStorage):
        """Тест фильтрации документов."""
        logger.info("Testing document filtering")

        # Создаем тестовые документы с разными датами
        now = datetime.now()
        test_docs = [
            Document(
                file_id=str(uuid.uuid4()),
                relative_path=f"filter_test_{i}.pdf",
                file_name=f"filter_test_{i}.pdf",
                summary=f"Test document {i}",
                metadata={
                    "size": 100,
                    "filter_test": True,
                    "created_date": (now - timedelta(days=i)).isoformat()
                },
                paragraphs=[],
                created_at=now - timedelta(days=i),
                updated_at=now - timedelta(days=i)
            )
            for i in range(3)
        ]

        # Сохраняем документы
        for doc in test_docs:
            await storage.save_document(doc)

        # Тестируем фильтрацию по дате
        recent_docs = await storage.filter_documents({
            "created_at": {
                "gte": (now - timedelta(days=1)).isoformat()
            }
        })
        assert len(recent_docs) == 2, "Should find documents created in last 2 days"

        # Тестируем фильтрацию по размеру
        large_docs = await storage.filter_documents({
            "metadata": {
                "size": {
                    "gt": 50
                }
            }
        })
        assert len(large_docs) == 3, "Should find all documents larger than 50 bytes"

    @pytest.mark.asyncio
    async def test_document_pagination(self, storage: SupabaseStorage):
        """Тест пагинации документов."""
        logger.info("Testing document pagination")

        # Создаем множество тестовых документов
        test_docs = [
            Document(
                file_id=str(uuid.uuid4()),
                relative_path=f"page_test_{i}.pdf",
                file_name=f"page_test_{i}.pdf",
                summary=f"Test document {i}",
                metadata={
                    "size": 100,
                    "pagination_test": True,
                    "order": i
                },
                paragraphs=[],
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            for i in range(10)
        ]

        # Сохраняем документы
        for doc in test_docs:
            await storage.save_document(doc)

        # Тестируем пагинацию
        page1 = await storage.get_documents(page=1, page_size=3)
        assert len(page1) == 3, "First page should contain 3 documents"

        page2 = await storage.get_documents(page=2, page_size=3)
        assert len(page2) == 3, "Second page should contain 3 documents"

        page3 = await storage.get_documents(page=3, page_size=3)
        assert len(page3) == 3, "Third page should contain 3 documents"

        page4 = await storage.get_documents(page=4, page_size=3)
        assert len(page4) == 1, "Fourth page should contain 1 document"

        # Проверяем порядок документов
        for i in range(len(page1)):
            assert page1[i].metadata["order"] == i, "Documents should be in correct order"

    @pytest.mark.asyncio
    async def test_document_relationships(self, storage: SupabaseStorage):
        """Тест связей между документами."""
        logger.info("Testing document relationships")

        # Создаем основной документ
        main_doc = Document(
            file_id=str(uuid.uuid4()),
            relative_path="main_doc.pdf",
            file_name="main_doc.pdf",
            summary="Main document",
            metadata={
                "size": 100,
                "relationship_test": True,
                "type": "main"
            },
            paragraphs=[],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        # Создаем связанный документ
        related_doc = Document(
            file_id=str(uuid.uuid4()),
            relative_path="related_doc.pdf",
            file_name="related_doc.pdf",
            summary="Related document",
            metadata={
                "size": 100,
                "relationship_test": True,
                "type": "related",
                "related_to": main_doc.file_id
            },
            paragraphs=[],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        # Сохраняем документы
        await storage.save_document(main_doc)
        await storage.save_document(related_doc)

        # Проверяем связи
        related_docs = await storage.get_related_documents(main_doc.file_id)
        assert len(related_docs) == 1, "Should find one related document"
        assert related_docs[0].file_id == related_doc.file_id, "Should find correct related document"

        # Проверяем обратную связь
        main_docs = await storage.get_related_documents(related_doc.file_id)
        assert len(main_docs) == 1, "Should find one main document"
        assert main_docs[0].file_id == main_doc.file_id, "Should find correct main document"

    @pytest.mark.asyncio
    async def test_network_error_handling(self, storage: SupabaseStorage, test_document: Document):
        """Тест обработки сетевых ошибок."""
        logger.info("Testing network error handling")

        # Мокаем клиент Supabase для симуляции сетевых ошибок
        with patch.object(storage.client, 'table') as mock_table:
            # Симулируем ошибку сети при сохранении
            mock_table.return_value.insert.return_value.execute.side_effect = Exception("Network error")
            
            with pytest.raises(StorageError) as exc_info:
                await storage.save_document(test_document)
            assert "Network error" in str(exc_info.value)

            # Симулируем ошибку сети при получении
            mock_table.return_value.select.return_value.execute.side_effect = Exception("Network error")
            
            with pytest.raises(StorageError) as exc_info:
                await storage.get_document(test_document.file_id)
            assert "Network error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, storage: SupabaseStorage):
        """Тест конкурентных операций с документами."""
        logger.info("Testing concurrent operations")

        # Создаем тестовый документ
        doc = Document(
            file_id=str(uuid.uuid4()),
            relative_path="concurrent_test.pdf",
            file_name="concurrent_test.pdf",
            summary="Test document for concurrent operations",
            metadata={"size": 100, "concurrent_test": True},
            paragraphs=[],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        # Сохраняем документ
        await storage.save_document(doc)

        # Создаем несколько асинхронных задач для одновременного доступа
        async def update_document():
            doc.metadata["updated_count"] = doc.metadata.get("updated_count", 0) + 1
            await storage.save_document(doc)

        # Запускаем несколько одновременных обновлений
        tasks = [update_document() for _ in range(5)]
        await asyncio.gather(*tasks)

        # Получаем обновленный документ
        updated_doc = await storage.get_document(doc.file_id)
        assert updated_doc.metadata["updated_count"] == 5, "All concurrent updates should be applied"

    @pytest.mark.asyncio
    async def test_document_versioning(self, storage: SupabaseStorage):
        """Тест версионирования документов."""
        logger.info("Testing document versioning")

        # Создаем начальную версию документа
        doc = Document(
            file_id=str(uuid.uuid4()),
            relative_path="version_test.pdf",
            file_name="version_test.pdf",
            summary="Initial version",
            metadata={"size": 100, "version": 1},
            paragraphs=[],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        # Сохраняем начальную версию
        await storage.save_document(doc)

        # Создаем новую версию
        doc.summary = "Updated version"
        doc.metadata["version"] = 2
        doc.updated_at = datetime.now()
        await storage.save_document(doc)

        # Получаем последнюю версию
        latest_doc = await storage.get_document(doc.file_id)
        assert latest_doc.summary == "Updated version", "Latest version should be retrieved"
        assert latest_doc.metadata["version"] == 2, "Version number should be updated"

    @pytest.mark.asyncio
    async def test_document_cleanup(self, storage: SupabaseStorage):
        """Тест очистки устаревших документов."""
        logger.info("Testing document cleanup")

        # Создаем тестовые документы с разными датами
        now = datetime.now()
        old_docs = [
            Document(
                file_id=str(uuid.uuid4()),
                relative_path=f"old_doc_{i}.pdf",
                file_name=f"old_doc_{i}.pdf",
                summary=f"Old document {i}",
                metadata={
                    "size": 100,
                    "cleanup_test": True,
                    "created_date": (now - timedelta(days=30)).isoformat()
                },
                paragraphs=[],
                created_at=now - timedelta(days=30),
                updated_at=now - timedelta(days=30)
            )
            for i in range(3)
        ]

        # Сохраняем старые документы
        for doc in old_docs:
            await storage.save_document(doc)

        # Запускаем очистку старых документов
        await storage.cleanup_old_documents(days=15)

        # Проверяем, что старые документы удалены
        for doc in old_docs:
            with pytest.raises(DocumentNotFoundError):
                await storage.get_document(doc.file_id)
