import os
from datetime import datetime
from typing import Optional

class FileInfo:
    """
    Класс для хранения информации о файле
    """
    def __init__(self, 
                 path: str,
                 file_id: Optional[str] = None,
                 file_name: Optional[str] = None,
                 relative_path: Optional[str] = None,
                 absolute_path: Optional[str] = None,
                 extension: Optional[str] = None,
                 last_modified: Optional[datetime] = None,
                 is_accessible: Optional[bool] = None,
                 size: Optional[int] = None,
                 mime_type: Optional[str] = None):
        """
        Инициализирует объект FileInfo

        Args:
            path: Путь к файлу
            file_id: Уникальный идентификатор файла
            file_name: Имя файла
            relative_path: Относительный путь к файлу
            absolute_path: Абсолютный путь к файлу
            extension: Расширение файла
            last_modified: Время последнего изменения файла
            is_accessible: Доступен ли файл для чтения
            size: Размер файла в байтах
            mime_type: MIME-тип файла
        """
        self.path = path
        self.file_id = file_id or os.path.basename(path)
        self.file_name = file_name or os.path.basename(path)
        self.relative_path = relative_path or path
        self.absolute_path = absolute_path or os.path.abspath(path)
        self.extension = extension or os.path.splitext(path)[1]
        
        self._last_modified = last_modified
        self._is_accessible = is_accessible
        self._size = size
        self._mime_type = mime_type
        
    @property
    def last_modified(self) -> datetime:
        """Время последнего изменения файла"""
        if self._last_modified is None:
            self._last_modified = datetime.fromtimestamp(os.path.getmtime(self.path))
        return self._last_modified
        
    @property
    def is_accessible(self) -> bool:
        """Доступен ли файл для чтения"""
        if self._is_accessible is None:
            self._is_accessible = os.access(self.path, os.R_OK)
        return self._is_accessible
        
    @property
    def size(self) -> int:
        """Размер файла в байтах"""
        if self._size is None:
            self._size = os.path.getsize(self.path)
        return self._size
        
    @property
    def mime_type(self) -> Optional[str]:
        """MIME-тип файла"""
        return self._mime_type
        
    @mime_type.setter
    def mime_type(self, value: str):
        """Устанавливает MIME-тип файла"""
        self._mime_type = value
        
    def __str__(self) -> str:
        return f"FileInfo(path='{self.path}', last_modified='{self.last_modified}', size={self.size}, mime_type='{self.mime_type}')"
        
    def __repr__(self) -> str:
        return self.__str__() 