"""
Base classes for model providers.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import aiohttp
import logging

logger = logging.getLogger(__name__)

class ModelProvider(ABC):
    """Базовый класс для провайдеров моделей"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize provider with configuration.
        
        Args:
            config: Provider-specific configuration
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    async def call_model(self, model_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call model with given payload.
        
        Args:
            model_id: Identifier of the model to use
            payload: Input data for the model
            
        Returns:
            Model response
        """
        pass
    
    async def _make_request(
        self,
        url: str,
        method: str = "POST",
        headers: Optional[Dict[str, str]] = None,
        json: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request to API endpoint.
        
        Args:
            url: Endpoint URL
            method: HTTP method
            headers: Request headers
            json: Request body
            
        Returns:
            API response
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method,
                    url,
                    headers=headers or {},
                    json=json
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        self.logger.error(f"API request failed: {error_text}")
                        raise Exception(f"API request failed: {error_text}")
                    
                    return await response.json()
                    
        except Exception as e:
            self.logger.error(f"Error during API request: {str(e)}")
            raise 