"""
Configuration module.
"""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv
from z888_ai_hub.utils.logging_utils import setup_logger

# Load environment variables
load_dotenv()

# Initialize logger
logger = setup_logger('ServicesConfig')


@dataclass
class ServicesConfig:
    """Configuration for external services."""
    
    def __init__(self):
        """Initialize configuration from environment variables."""
        # Supabase
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')
        
        if not self.supabase_url or not self.supabase_key:
            logger.error("Missing required Supabase environment variables")
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment")
        
        logger.info("Successfully loaded Supabase configuration") 