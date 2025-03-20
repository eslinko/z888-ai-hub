#!/bin/bash

# Проверка на sudo
if [[ $EUID -ne 0 ]]; then
   echo "Запусти этот скрипт с sudo!" 
   exit 1
fi

# Определение корневой папки
PROJECT_DIR="z888-ai-hub"

# Создание корневой папки
mkdir -p $PROJECT_DIR
cd $PROJECT_DIR

# Создание папок
mkdir -p connectors interfaces registry config utils examples tests scripts docs

# Создание пустых Python-файлов (init-файлы для пакетов)
touch connectors/__init__.py
touch interfaces/__init__.py
touch registry/__init__.py
touch utils/__init__.py

# Создание файлов коннекторов
touch connectors/openai.py
touch connectors/huggingface.py
touch connectors/mistral.py
touch connectors/tesseract.py
touch connectors/google_vision.py
touch connectors/whisper.py

# Базовые интерфейсы
touch interfaces/base_connector.py

# Реестр API
touch registry/connector_registry.py

# Конфиги
touch config/ai_tasks_mapping.yaml
touch config/settings.yaml

# Утилиты
touch utils/logging_utils.py
touch utils/validation.py

# Примеры
touch examples/process_text.py
touch examples/process_image.py
touch examples/process_audio.py

# Тесты
touch tests/test_connectors.py
touch tests/test_registry.py

# Скрипты
touch scripts/ai_processor.py

# Документация
touch docs/getting_started.md
touch docs/api_reference.md

# Корневые файлы
touch setup.py
touch pyproject.toml
touch requirements.txt
touch README.md
touch .gitignore
touch LICENSE

# Устанавливаем права доступа (только для важных файлов)
chmod 644 setup.py pyproject.toml requirements.txt README.md LICENSE
chmod 755 scripts/ai_processor.py

echo "✅ Структура проекта успешно создана в папке $PROJECT_DIR"
