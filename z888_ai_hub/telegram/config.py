"""
Configuration for Telegram chat processing.
"""

DEFAULT_CONFIG = {
    'image': {
        'extensions': {'.png', '.jpg', '.jpeg', '.webp'},
        'max_size': (1920, 1080),
        'max_file_size': 52428800  # 50MB
    },
    'processing': {
        'batch_size': 10,
        'timeout': 30,
        'max_retries': 3
    },
    'ocr': {
        'provider': 'mistral',
        'fallback_providers': [],
        'max_retries': 1,
        'timeout': 5
    }
} 