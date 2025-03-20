"""
CLI interface for document processing.
"""

import asyncio
import argparse
import yaml
from pathlib import Path
from typing import Optional
from z888_ai_hub.processors.document_processor import DocumentProcessor
from z888_ai_hub.processors.factory import DocumentProcessorFactory
from z888_ai_hub.utils.logging_utils import setup_logger


async def process_directory(
    directory: str,
    config_path: Optional[str] = None,
    output_dir: Optional[str] = None,
    batch_size: int = 10
) -> None:
    """
    Process all documents in the directory.
    
    Args:
        directory: Directory to process
        config_path: Path to configuration file (optional)
        output_dir: Directory for output files (optional)
        batch_size: Number of files to process in parallel
    """
    logger = setup_logger('CLI')
    
    try:
        # Проверяем директорию
        dir_path = Path(directory)
        if not dir_path.exists():
            raise ValueError(f"Directory {directory} does not exist")
        
        logger.info(f"Starting processing of directory: {directory}")
        
        # Загружаем конфигурацию
        if config_path:
            config_path = Path(config_path)
            if not config_path.exists():
                raise ValueError(f"Configuration file {config_path} does not exist")
            with open(config_path) as f:
                config = yaml.safe_load(f)
        else:
            # Используем базовую конфигурацию
            config_path = Path(__file__).parent / "configs" / "base_config.yaml"
            with open(config_path) as f:
                config = yaml.safe_load(f)
        
        # Создаем процессор
        processor = await DocumentProcessorFactory.create_default(str(dir_path), config)
        
        # Запускаем обработку
        stats = await processor.process_directory(str(dir_path))
        
        # Выводим статистику
        logger.info("Processing completed. Statistics:")
        logger.info(f"Total files: {stats['total_files']}")
        logger.info(f"Processed files: {stats['processed_files']}")
        logger.info(f"Failed files: {len(stats['failed_files'])}")
        logger.info(f"File types: {stats['file_types']}")
        
        if stats['failed_files']:
            logger.warning("Failed files:")
            for failed in stats['failed_files']:
                logger.warning(f"- {failed['path']}: {failed['error']}")
        
    except Exception as e:
        logger.error(f"Error processing directory: {str(e)}")
        raise


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description='Process documents in directory')
    parser.add_argument('directory', help='Directory to process')
    parser.add_argument('--config', '-c', help='Path to configuration file (optional)')
    parser.add_argument('--output', '-o', help='Output directory (optional)')
    parser.add_argument('--batch-size', '-b', type=int, default=10,
                      help='Number of files to process in parallel')
    
    args = parser.parse_args()
    
    # Запускаем асинхронную обработку
    asyncio.run(process_directory(
        args.directory,
        args.config,
        args.output,
        args.batch_size
    ))


if __name__ == '__main__':
    main() 