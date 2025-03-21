"""
CLI script for parsing Telegram chat screenshots.
"""

import asyncio
import argparse
import json
import yaml
import os
from pathlib import Path
from typing import Optional

from z888_ai_hub.telegram.parser import TelegramChatParser
from z888_ai_hub.utils.logging_utils import setup_logger
from z888_ai_hub.utils.env_loader import load_dotenv
from z888_ai_hub.connectors.factory import ConnectorFactory
from z888_ai_hub.connectors.base_connector import ConnectorCapability
from z888_ai_hub.connectors.mistral import MistralConnector


def load_config(config_path: Optional[str] = None) -> dict:
    """
    Load and process configuration file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        dict: Processed configuration
    """
    logger = setup_logger('ConfigLoader')
    
    # Загружаем переменные окружения
    load_dotenv()
    
    # Загружаем конфигурацию
    if config_path:
        config_path = Path(config_path)
        if not config_path.exists():
            raise ValueError(f"Configuration file {config_path} does not exist")
    else:
        config_path = Path(__file__).parent / "configs" / "ocr_config.yaml"
        
    logger.info(f"Loading configuration from {config_path}")
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    # Заменяем переменные окружения в конфигурации
    def replace_env_vars(obj):
        if isinstance(obj, dict):
            return {k: replace_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [replace_env_vars(v) for v in obj]
        elif isinstance(obj, str) and obj.startswith("${") and obj.endswith("}"):
            env_var = obj[2:-1]
            return os.getenv(env_var, obj)
        return obj
    
    processed_config = replace_env_vars(config)
    logger.info(f"Configuration loaded: {json.dumps(processed_config, indent=2)}")
    return processed_config


async def process_chat(
    directory: str,
    config_path: Optional[str] = None,
    output_path: Optional[str] = None
) -> None:
    """
    Process Telegram chat screenshots.
    
    Args:
        directory: Directory containing screenshots
        config_path: Path to configuration file
        output_path: Path to save results
    """
    logger = setup_logger('TelegramChatParser')
    
    try:
        # Проверяем директорию
        dir_path = Path(directory)
        if not dir_path.exists():
            raise ValueError(f"Directory {directory} does not exist")
        
        logger.info(f"Starting processing of directory: {directory}")
        
        # Загружаем конфигурацию
        config = load_config(config_path)
        
        # Создаем OCR коннектор
        mistral_config = config.get("connectors", {}).get("mistral", {})
        ocr_connector = MistralConnector(
            api_key=mistral_config.get("api_key"),
            base_url=mistral_config.get("base_url"),
            default_model=mistral_config.get("default_model")
        )
        
        # Создаем парсер
        parser = TelegramChatParser(ocr_connector, config)
        
        # Обрабатываем директорию
        result = await parser.process_directory(str(dir_path))
        
        # Сохраняем результат
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Конвертируем результат в JSON
            output_data = {
                'success': result.success,
                'processing_time': result.processing_time,
                'total_images': result.total_images,
                'processed_images': result.processed_images,
                'failed_images': result.failed_images,
                'error': result.error,
                'chat': {
                    'messages': [
                        {
                            'timestamp': msg.timestamp.isoformat() if msg.timestamp else None,
                            'sender': msg.sender,
                            'text': msg.text,
                            'links': msg.links,
                            'image_order': msg.image_order,
                            'position_in_image': msg.position_in_image
                        }
                        for msg in result.chat.messages
                    ] if result.chat else [],
                    'metadata': result.chat.metadata if result.chat else {}
                }
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Results saved to {output_path}")
        
        # Выводим статистику
        logger.info("Processing completed. Statistics:")
        logger.info(f"Total images: {result.total_images}")
        logger.info(f"Processed images: {result.processed_images}")
        logger.info(f"Failed images: {result.failed_images}")
        logger.info(f"Processing time: {result.processing_time:.2f} seconds")
        
        if result.error:
            logger.error(f"Error: {result.error}")
        
    except Exception as e:
        logger.error(f"Error processing chat: {str(e)}")
        raise


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description='Process Telegram chat screenshots')
    parser.add_argument('directory', help='Directory containing screenshots')
    parser.add_argument('--config', '-c', help='Path to configuration file (optional)')
    parser.add_argument('--output', '-o', help='Path to save results (optional)')
    
    args = parser.parse_args()
    
    # Запускаем асинхронную обработку
    asyncio.run(process_chat(
        args.directory,
        args.config,
        args.output
    ))


if __name__ == '__main__':
    main() 