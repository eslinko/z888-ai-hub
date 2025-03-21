"""
Base configuration for integration tests.
"""

import os
import pytest
from datetime import datetime
from z888_ai_hub.utils.logging_utils import setup_logger

logger = setup_logger('IntegrationTests')

def pytest_configure(config):
    """Настраивает pytest для интеграционных тестов."""
    # Проверяем наличие необходимых переменных окружения
    required_env_vars = [
        "ANTHROPIC_API_KEY",
        "MISTRAL_API_KEY",
        "SUPABASE_URL",
        "SUPABASE_KEY"
    ]
    
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        pytest.exit(f"Missing required environment variables: {', '.join(missing_vars)}")

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Настраивает тестовое окружение."""
    # Создаем временные директории для тестов
    test_dirs = [
        "tests/temp",
        "tests/temp/pdfs",
        "tests/temp/docs",
        "tests/temp/images",
        "tests/temp/json"
    ]
    
    for dir_path in test_dirs:
        os.makedirs(dir_path, exist_ok=True)
    
    yield
    
    # Очищаем временные директории после тестов
    for dir_path in test_dirs:
        if os.path.exists(dir_path):
            for file in os.listdir(dir_path):
                os.remove(os.path.join(dir_path, file))
            os.rmdir(dir_path)
        if os.path.exists(dir_path):
            os.rmdir(dir_path)

@pytest.fixture(scope="session")
def test_start_time():
    """Возвращает время начала тестов."""
    return datetime.now()

@pytest.fixture(scope="session")
def test_files_dir():
    """Возвращает путь к директории с тестовыми файлами."""
    return "tests/sample_files"

@pytest.fixture(scope="session")
def temp_dir():
    """Возвращает путь к временной директории для тестов."""
    return "tests/temp" 