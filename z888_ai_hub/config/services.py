"""
Configuration for external services.
"""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv
from z888_ai_hub.utils.logging_utils import setup_logger

# Инициализируем логгер
logger = setup_logger('ServicesConfig', log_to_file=True)

# Загружаем переменные окружения при импорте модуля
load_dotenv()


@dataclass
class SupabaseConfig:
    """Configuration for Supabase service."""
    url: str
    api_key: str
    schema: str = 'public'
    
    @classmethod
    def from_env(cls) -> 'SupabaseConfig':
        """Create config from environment variables."""
        url = os.getenv('SUPABASE_URL')
        api_key = os.getenv('SUPABASE_KEY')
        
        if not url or not api_key:
            logger.error("Missing required Supabase environment variables")
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment")
            
        logger.debug(f"Initialized Supabase config with URL: {url[:20]}...")
        return cls(
            url=url,
            api_key=api_key
        )


# Глобальный конфиг, инициализируется при импорте
try:
    supabase_config = SupabaseConfig.from_env()
    logger.info("Successfully loaded Supabase configuration")
except Exception as e:
    logger.error(f"Failed to load Supabase configuration: {str(e)}")
    raise 