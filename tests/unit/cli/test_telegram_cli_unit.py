"""
Unit tests for Telegram chat parser CLI.
"""

import os
import pytest
import yaml
from unittest.mock import Mock, patch
from pathlib import Path
from telegram_chat_parser import process_chat, main, load_config
from z888_ai_hub.utils.logging_utils import setup_logger

logger = setup_logger('TestTelegramCLIUnit')

@pytest.fixture
def temp_config(temp_dir):
    """Создает временный конфигурационный файл."""
    config = {
        "connectors": {
            "mistral": {
                "type": "mistral",
                "api_key": "test_key",
                "base_url": "https://api.mistral.ai",
                "default_model": "mistral-tiny",
                "capabilities": ["ocr"]
            }
        },
        "ocr": {
            "provider": "mistral",
            "fallback_providers": [],
            "max_retries": 1,
            "timeout": 5
        },
        "parsing": {
            "image_types": [".png", ".jpg", ".jpeg"],
            "max_image_size": 1048576,
            "batch_size": 2
        }
    }
    
    config_path = os.path.join(temp_dir, "test_config.yaml")
    with open(config_path, "w") as f:
        yaml.dump(config, f)
    return config_path

@pytest.fixture
def temp_images(temp_dir):
    """Создает тестовые изображения."""
    images = {
        "chat1.png": b"Test image content 1",
        "chat2.png": b"Test image content 2",
        "chat3.jpg": b"Test image content 3"
    }
    
    for name, content in images.items():
        path = os.path.join(temp_dir, name)
        with open(path, "wb") as f:
            f.write(content)
    
    return temp_dir

@pytest.mark.unit
@pytest.mark.asyncio
async def test_process_chat_with_config(temp_images, temp_config):
    """Тестирует обработку чата с конфигурационным файлом."""
    mock_parser = Mock()
    mock_parser.process_directory.return_value = {
        "total_images": 3,
        "processed_images": 2,
        "failed_images": [{"path": "chat3.jpg", "error": "Unsupported image type"}],
        "image_types": {".png": 2, ".jpg": 1}
    }
    
    with patch('telegram_chat_parser.TelegramChatParser', return_value=mock_parser):
        await process_chat(temp_images, temp_config)
        
        mock_parser.process_directory.assert_called_once_with(temp_images)
        assert mock_parser.process_directory.call_count == 1

@pytest.mark.unit
@pytest.mark.asyncio
async def test_process_chat_without_config(temp_images):
    """Тестирует обработку чата без конфигурационного файла."""
    mock_parser = Mock()
    mock_parser.process_directory.return_value = {
        "total_images": 3,
        "processed_images": 2,
        "failed_images": [{"path": "chat3.jpg", "error": "Unsupported image type"}],
        "image_types": {".png": 2, ".jpg": 1}
    }
    
    with patch('telegram_chat_parser.TelegramChatParser', return_value=mock_parser):
        await process_chat(temp_images)
        
        mock_parser.process_directory.assert_called_once_with(temp_images)
        assert mock_parser.process_directory.call_count == 1

@pytest.mark.unit
@pytest.mark.asyncio
async def test_process_chat_nonexistent():
    """Тестирует обработку несуществующей директории."""
    with pytest.raises(ValueError) as exc_info:
        await process_chat("/nonexistent/directory")
    assert "Directory /nonexistent/directory does not exist" in str(exc_info.value)

@pytest.mark.unit
@pytest.mark.asyncio
async def test_process_chat_with_invalid_config(temp_images):
    """Тестирует обработку чата с некорректным конфигурационным файлом."""
    invalid_config = "/nonexistent/config.yaml"
    
    with pytest.raises(ValueError) as exc_info:
        await process_chat(temp_images, invalid_config)
    assert "Configuration file /nonexistent/config.yaml does not exist" in str(exc_info.value)

@pytest.mark.unit
@pytest.mark.asyncio
async def test_process_chat_with_output_path(temp_images, temp_config):
    """Тестирует обработку чата с указанием пути для сохранения результатов."""
    output_path = os.path.join(temp_images, "output.json")
    
    mock_parser = Mock()
    mock_parser.process_directory.return_value = {
        "total_images": 3,
        "processed_images": 2,
        "failed_images": [{"path": "chat3.jpg", "error": "Unsupported image type"}],
        "image_types": {".png": 2, ".jpg": 1}
    }
    
    with patch('telegram_chat_parser.TelegramChatParser', return_value=mock_parser):
        await process_chat(temp_images, temp_config, output_path)
        
        mock_parser.process_directory.assert_called_once_with(temp_images)
        assert mock_parser.process_directory.call_count == 1

@pytest.mark.unit
@pytest.mark.asyncio
async def test_process_chat_error_handling(temp_images, temp_config):
    """Тестирует обработку ошибок при обработке чата."""
    mock_parser = Mock()
    mock_parser.process_directory.side_effect = Exception("Processing error")
    
    with patch('telegram_chat_parser.TelegramChatParser', return_value=mock_parser):
        with pytest.raises(Exception) as exc_info:
            await process_chat(temp_images, temp_config)
        assert "Processing error" in str(exc_info.value)

@pytest.mark.unit
def test_load_config_with_custom_path(temp_config):
    """Тестирует загрузку конфигурации из пользовательского файла."""
    config = load_config(temp_config)
    
    assert config is not None
    assert "connectors" in config
    assert "mistral" in config["connectors"]
    assert "ocr" in config
    assert "parsing" in config

@pytest.mark.unit
def test_load_config_with_default_path():
    """Тестирует загрузку конфигурации из файла по умолчанию."""
    with patch('telegram_chat_parser.pkg_resources.resource_string') as mock_resource:
        mock_resource.return_value = b"""
        tasks:
          ocr:
            provider: mistral
            fallback_providers: []
            max_retries: 1
            timeout: 5
        """
        
        config = load_config()
        
        assert config is not None
        assert "tasks" in config
        assert "ocr" in config["tasks"]

@pytest.mark.unit
def test_load_config_with_invalid_path():
    """Тестирует загрузку конфигурации из несуществующего файла."""
    with pytest.raises(ValueError) as exc_info:
        load_config("/nonexistent/config.yaml")
    assert "Configuration file /nonexistent/config.yaml does not exist" in str(exc_info.value)

@pytest.mark.unit
def test_main_cli_arguments():
    """Тестирует обработку аргументов командной строки."""
    with patch('telegram_chat_parser.process_chat') as mock_process:
        with patch('sys.argv', ['telegram_chat_parser.py', 'test_dir', '--config', 'config.yaml', '--output', 'output.json']):
            main()
            
            mock_process.assert_called_once()
            args = mock_process.call_args[0]
            assert args[0] == 'test_dir'
            assert args[1] == 'config.yaml'
            assert args[2] == 'output.json'

@pytest.mark.unit
def test_main_cli_minimal_arguments():
    """Тестирует обработку минимального набора аргументов командной строки."""
    with patch('telegram_chat_parser.process_chat') as mock_process:
        with patch('sys.argv', ['telegram_chat_parser.py', 'test_dir']):
            main()
            
            mock_process.assert_called_once()
            args = mock_process.call_args[0]
            assert args[0] == 'test_dir'
            assert args[1] is None
            assert args[2] is None 