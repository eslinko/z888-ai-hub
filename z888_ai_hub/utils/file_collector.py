"""
File collector module for recursively finding and validating files in directories.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Set, List, Generator, Optional, Dict, Tuple, Iterator
from collections import defaultdict
import os
from pathlib import Path

from z888_ai_hub.utils.logging_utils import setup_logger
from z888_ai_hub.utils.file_validator import FileValidator, FileType, ValidationResult


class FileCollectorError(Exception):
    """Base exception for FileCollector errors."""
    pass


class PathValidationError(FileCollectorError):
    """Exception for path validation errors."""
    pass


@dataclass
class FileInfo:
    """Data class for storing file information."""
    absolute_path: str
    relative_path: str
    extension: str
    size: int
    last_modified: datetime
    is_accessible: bool
    validation_result: Optional[ValidationResult] = None
    file_id: str = ""
    file_name: str = ""
    created_at: datetime = None
    modified_at: datetime = None

    @classmethod
    def from_path(cls, root_path: str, file_path: str) -> 'FileInfo':
        """
        Create FileInfo instance from file path.

        Args:
            root_path: Root directory path
            file_path: Absolute path to the file

        Returns:
            FileInfo instance
        """
        try:
            abs_path = str(Path(file_path).resolve())
            root_path = str(Path(root_path).resolve())
            rel_path = os.path.relpath(abs_path, root_path)
            stats = os.stat(abs_path)
            
            return cls(
                absolute_path=abs_path,
                relative_path=rel_path,
                extension=os.path.splitext(file_path)[1].lower(),
                size=stats.st_size,
                last_modified=datetime.fromtimestamp(stats.st_mtime),
                is_accessible=os.access(abs_path, os.R_OK),
                file_id=rel_path,
                file_name=os.path.basename(file_path),
                created_at=datetime.fromtimestamp(stats.st_ctime),
                modified_at=datetime.fromtimestamp(stats.st_mtime)
            )
        except (OSError, ValueError) as e:
            return cls(
                absolute_path=file_path,
                relative_path=file_path,
                extension=os.path.splitext(file_path)[1].lower(),
                size=0,
                last_modified=datetime.min,
                is_accessible=False,
                file_name=os.path.basename(file_path),
                created_at=datetime.min,
                modified_at=datetime.min
            )


class FileCollector:
    """Class for recursively collecting files from directories."""

    def __init__(
        self,
        root_path: str,
        allowed_extensions: Set[str] = {'.pdf', '.doc', '.docx'},
        min_file_size: Optional[int] = None,
        max_file_size: Optional[int] = None,
        validate_content: bool = True,
        skip_unreadable: bool = False
    ):
        """
        Initialize FileCollector.

        Args:
            root_path: Root directory to start collection from
            allowed_extensions: Set of allowed file extensions (lowercase)
            min_file_size: Minimum file size in bytes (optional)
            max_file_size: Maximum file size in bytes (optional)
            validate_content: Whether to validate file content
            skip_unreadable: Whether to skip unreadable files
        
        Raises:
            PathValidationError: If root_path is invalid or inaccessible
            FileCollectorError: If initialization fails
        """
        self.logger = setup_logger('FileCollector')
        
        # Проверяем и нормализуем корневой путь
        is_valid, error_message = self.validate_path(root_path)
        if not is_valid:
            raise PathValidationError(error_message)
        
        self.root_path = os.path.abspath(root_path)
        self.allowed_extensions = {ext.lower() for ext in allowed_extensions}
        self.min_file_size = min_file_size
        self.max_file_size = max_file_size
        self.validate_content = validate_content
        self.skip_unreadable = skip_unreadable
        self.validator = FileValidator()
        
        # Statistics
        self.total_files = 0
        self.processed_files = 0
        self.skipped_files = 0
        self.error_count = 0
        self.file_type_stats = defaultdict(lambda: defaultdict(int))

    def validate_path(self, path: str) -> Tuple[bool, Optional[str]]:
        """
        Validate if path exists and is accessible.

        Args:
            path: Path to validate

        Returns:
            Tuple[bool, Optional[str]]: (валиден ли путь, сообщение об ошибке)
        """
        try:
            path = os.path.abspath(path)
            
            # Проверяем существование пути
            if not os.path.exists(path):
                return False, f"Path does not exist: {path}"
            
            # Проверяем что это директория
            if not os.path.isdir(path):
                return False, f"Path is not a directory: {path}"
            
            # Проверяем права на чтение
            if not os.access(path, os.R_OK):
                return False, f"No read permission for directory: {path}"
            
            # Проверяем права на выполнение (для возможности просмотра содержимого директории)
            if not os.access(path, os.X_OK):
                return False, f"No execute permission for directory: {path}"
            
            return True, None
            
        except Exception as e:
            self.logger.error(f"Path validation error for {path}: {str(e)}")
            return False, f"Error validating path: {str(e)}"

    def check_file_access(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """
        Check if file is accessible for reading.

        Args:
            file_path: Path to file

        Returns:
            Tuple[bool, Optional[str]]: (доступен ли файл, сообщение об ошибке)
        """
        try:
            # Проверяем абсолютный путь
            abs_path = os.path.abspath(file_path)
            
            # Проверяем существование файла
            if not os.path.exists(abs_path):
                return False, f"File does not exist: {file_path}"
            
            # Проверяем что это файл, а не директория
            if not os.path.isfile(abs_path):
                return False, f"Path is not a file: {file_path}"
            
            # Проверяем права на чтение
            if not os.access(abs_path, os.R_OK):
                return False, f"No read permission for file: {file_path}"
            
            # Проверяем размер файла
            if self.min_file_size is not None or self.max_file_size is not None:
                try:
                    size = os.path.getsize(abs_path)
                    if self.min_file_size is not None and size < self.min_file_size:
                        return False, f"File size {size} is less than minimum {self.min_file_size}"
                    if self.max_file_size is not None and size > self.max_file_size:
                        return False, f"File size {size} is greater than maximum {self.max_file_size}"
                except OSError as e:
                    return False, f"Error getting file size: {str(e)}"
            
            return True, None
            
        except Exception as e:
            self.logger.error(f"File access check error for {file_path}: {str(e)}")
            return False, f"Error checking file access: {str(e)}"

    def _should_process_file(self, file_info: FileInfo) -> bool:
        """
        Check if file should be processed based on extension and access.

        Args:
            file_info: FileInfo instance

        Returns:
            bool: True if file should be processed
        """
        # Проверяем расширение файла
        if file_info.extension.lower() not in self.allowed_extensions:
            self.logger.debug(f"Skipping file with unsupported extension: {file_info.absolute_path}")
            return False

        # Проверяем доступность файла
        is_accessible, error = self.check_file_access(file_info.absolute_path)
        if not is_accessible:
            self.logger.warning(f"Skipping inaccessible file: {file_info.absolute_path}. Error: {error}")
            return False

        return True

    def collect_files(self) -> Generator[FileInfo, None, None]:
        """
        Recursively collect files from root_path.

        Yields:
            FileInfo: Information about each file found
        """
        try:
            # Проверяем доступность корневой директории
            is_valid, error = self.validate_path(self.root_path)
            if not is_valid:
                self.logger.error(f"Root path validation failed: {error}")
                return

            for dirpath, dirnames, filenames in os.walk(self.root_path):
                # Проверяем доступность текущей директории
                is_valid, error = self.validate_path(dirpath)
                if not is_valid:
                    self.logger.warning(f"Skipping inaccessible directory: {dirpath}. Error: {error}")
                    continue

                for filename in filenames:
                    self.total_files += 1
                    file_path = os.path.join(dirpath, filename)
                    
                    try:
                        file_info = FileInfo.from_path(self.root_path, file_path)
                        
                        if not self._should_process_file(file_info):
                            self.skipped_files += 1
                            continue

                        if self.validate_content:
                            validation_result = self.validator.validate_file(file_path)
                            file_info.validation_result = validation_result
                            
                            if not validation_result.is_readable and self.skip_unreadable:
                                self.skipped_files += 1
                                continue
                                
                            # Обновляем статистику по типам файлов
                            file_type = validation_result.file_type or FileType.UNKNOWN
                            self.file_type_stats[file_type]['total'] += 1
                            if validation_result.is_readable:
                                self.file_type_stats[file_type]['readable'] += 1
                            else:
                                self.file_type_stats[file_type]['unreadable'] += 1

                        self.processed_files += 1
                        yield file_info

                    except Exception as e:
                        self.logger.error(f"Error processing file {file_path}: {str(e)}")
                        self.error_count += 1
                        continue

        except Exception as e:
            self.logger.error(f"Error collecting files: {str(e)}")
            self.error_count += 1

    def get_statistics(self) -> dict:
        """
        Get collection statistics.

        Returns:
            dict: Collection statistics
        """
        stats = {
            "total_files": self.total_files,
            "processed_files": self.processed_files,
            "skipped_files": self.skipped_files,
            "error_count": self.error_count,
            "file_types": {}
        }
        
        # Добавляем статистику по типам файлов
        for file_type, type_stats in self.file_type_stats.items():
            stats["file_types"][file_type.value] = dict(type_stats)
            
        return stats 