"""
Unit tests for main CLI interface.
"""

import os
import pytest
import yaml
from unittest.mock import Mock, patch
from pathlib import Path
from z888_ai_hub.cli import process_directory, main
from z888_ai_hub.utils.logging_utils import setup_logger

logger = setup_logger('TestMainCLIUnit')

@pytest.fixture
def temp_config(temp_dir):
    """Создает временный конфигурационный файл."""
    config = {
        "connectors": {
            "anthropic": {
                "type": "anthropic",
                "api_key": "test_key",
                "base_url": "https://api.anthropic.com",
                "default_model": "claude-3-sonnet-20240229",
                "capabilities": ["summary", "vectorization"]
            }
        },
        "tasks": {
            "summary": {
                "provider": "anthropic",
                "fallback_providers": [],
                "max_retries": 1,
                "timeout": 5
            }
        },
        "processing": {
            "file_types": [".pdf", ".txt"],
            "max_file_size": 1048576,
            "batch_size": 2
        }
    }
    
    config_path = os.path.join(temp_dir, "test_config.yaml")
    with open(config_path, "w") as f:
        yaml.dump(config, f)
    return config_path

@pytest.fixture
def temp_docs(temp_dir):
    """Создает тестовые документы."""
    docs = {
        "test1.pdf": b"Test PDF content 1",
        "test2.pdf": b"Test PDF content 2",
        "test3.txt": b"Test text content 3"
    }
    
    for name, content in docs.items():
        path = os.path.join(temp_dir, name)
        with open(path, "wb") as f:
            f.write(content)
    
    return temp_dir

@pytest.mark.unit
@pytest.mark.asyncio
async def test_process_directory_with_config(temp_docs, temp_config):
    """Тестирует обработку директории с конфигурационным файлом."""
    mock_processor = Mock()
    mock_processor.process_directory.return_value = {
        "total_files": 3,
        "processed_files": 2,
        "failed_files": [{"path": "test3.txt", "error": "Unsupported file type"}],
        "file_types": {".pdf": 2, ".txt": 1}
    }
    
    with patch('z888_ai_hub.cli.DocumentProcessorFactory.create_default', return_value=mock_processor):
        await process_directory(temp_docs, temp_config)
        
        mock_processor.process_directory.assert_called_once_with(temp_docs)
        assert mock_processor.process_directory.call_count == 1

@pytest.mark.unit
@pytest.mark.asyncio
async def test_process_directory_without_config(temp_docs):
    """Тестирует обработку директории без конфигурационного файла."""
    mock_processor = Mock()
    mock_processor.process_directory.return_value = {
        "total_files": 3,
        "processed_files": 2,
        "failed_files": [{"path": "test3.txt", "error": "Unsupported file type"}],
        "file_types": {".pdf": 2, ".txt": 1}
    }
    
    with patch('z888_ai_hub.cli.DocumentProcessorFactory.create_default', return_value=mock_processor):
        await process_directory(temp_docs)
        
        mock_processor.process_directory.assert_called_once_with(temp_docs)
        assert mock_processor.process_directory.call_count == 1

@pytest.mark.unit
@pytest.mark.asyncio
async def test_process_directory_nonexistent():
    """Тестирует обработку несуществующей директории."""
    with pytest.raises(ValueError) as exc_info:
        await process_directory("/nonexistent/directory")
    assert "Directory /nonexistent/directory does not exist" in str(exc_info.value)

@pytest.mark.unit
@pytest.mark.asyncio
async def test_process_directory_with_invalid_config(temp_docs):
    """Тестирует обработку директории с некорректным конфигурационным файлом."""
    invalid_config = "/nonexistent/config.yaml"
    
    with pytest.raises(ValueError) as exc_info:
        await process_directory(temp_docs, invalid_config)
    assert "Configuration file /nonexistent/config.yaml does not exist" in str(exc_info.value)

@pytest.mark.unit
@pytest.mark.asyncio
async def test_process_directory_with_custom_batch_size(temp_docs, temp_config):
    """Тестирует обработку директории с пользовательским размером пакета."""
    mock_processor = Mock()
    mock_processor.process_directory.return_value = {
        "total_files": 3,
        "processed_files": 2,
        "failed_files": [{"path": "test3.txt", "error": "Unsupported file type"}],
        "file_types": {".pdf": 2, ".txt": 1}
    }
    
    with patch('z888_ai_hub.cli.DocumentProcessorFactory.create_default', return_value=mock_processor):
        await process_directory(temp_docs, temp_config, batch_size=5)
        
        mock_processor.process_directory.assert_called_once_with(temp_docs)
        assert mock_processor.process_directory.call_count == 1

@pytest.mark.unit
@pytest.mark.asyncio
async def test_process_directory_with_output_dir(temp_docs, temp_config):
    """Тестирует обработку директории с указанием выходной директории."""
    output_dir = os.path.join(temp_docs, "output")
    os.makedirs(output_dir, exist_ok=True)
    
    mock_processor = Mock()
    mock_processor.process_directory.return_value = {
        "total_files": 3,
        "processed_files": 2,
        "failed_files": [{"path": "test3.txt", "error": "Unsupported file type"}],
        "file_types": {".pdf": 2, ".txt": 1}
    }
    
    with patch('z888_ai_hub.cli.DocumentProcessorFactory.create_default', return_value=mock_processor):
        await process_directory(temp_docs, temp_config, output_dir=output_dir)
        
        mock_processor.process_directory.assert_called_once_with(temp_docs)
        assert mock_processor.process_directory.call_count == 1

@pytest.mark.unit
@pytest.mark.asyncio
async def test_process_directory_error_handling(temp_docs, temp_config):
    """Тестирует обработку ошибок при обработке директории."""
    mock_processor = Mock()
    mock_processor.process_directory.side_effect = Exception("Processing error")
    
    with patch('z888_ai_hub.cli.DocumentProcessorFactory.create_default', return_value=mock_processor):
        with pytest.raises(Exception) as exc_info:
            await process_directory(temp_docs, temp_config)
        assert "Processing error" in str(exc_info.value)

@pytest.mark.unit
def test_main_cli_arguments():
    """Тестирует обработку аргументов командной строки."""
    with patch('z888_ai_hub.cli.process_directory') as mock_process:
        with patch('sys.argv', ['cli.py', 'test_dir', '--config', 'config.yaml', '--output', 'output_dir', '--batch-size', '5']):
            main()
            
            mock_process.assert_called_once()
            args = mock_process.call_args[0]
            assert args[0] == 'test_dir'
            assert args[1] == 'config.yaml'
            assert args[2] == 'output_dir'
            assert args[3] == 5

@pytest.mark.unit
def test_main_cli_minimal_arguments():
    """Тестирует обработку минимального набора аргументов командной строки."""
    with patch('z888_ai_hub.cli.process_directory') as mock_process:
        with patch('sys.argv', ['cli.py', 'test_dir']):
            main()
            
            mock_process.assert_called_once()
            args = mock_process.call_args[0]
            assert args[0] == 'test_dir'
            assert args[1] is None
            assert args[2] is None
            assert args[3] == 10  # default batch size 