"""
Demo provider for HuggingFace.
"""

from typing import Any, Dict
from .base import ModelProvider

class HuggingFaceProvider(ModelProvider):
    """Демо-провайдер для HuggingFace"""
    
    async def call_model(self, model_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call HuggingFace model.
        
        Args:
            model_id: Model identifier (e.g., "sentence-transformers/all-MiniLM-L6-v2")
            payload: Input data for the model
            
        Returns:
            Model response
        """
        self.logger.info(f"Calling HuggingFace model: {model_id}")
        
        # Формируем URL для API
        url = f"{self.config.get('base_url', 'https://api-inference.huggingface.co/models')}/{model_id}"
        
        # Добавляем заголовки авторизации
        headers = {
            "Authorization": f"Bearer {self.config.get('api_key')}",
            "Content-Type": "application/json"
        }
        
        return await self._make_request(
            url=url,
            headers=headers,
            json=payload
        ) 