"""
Utility module for loading environment variables.
"""
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def load_env(key: str) -> Optional[str]:
    """
    Load an environment variable.
    
    Args:
        key: The name of the environment variable to load
        
    Returns:
        The value of the environment variable or None if not found
    """
    return os.getenv(key)
