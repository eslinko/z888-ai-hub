"""
Provider for Supabase Edge Functions.
"""

from typing import Any, Dict
from .base import ModelProvider

class SupabaseEdgeFunctionProvider(ModelProvider):
    """Провайдер для Supabase Edge Functions"""
    
    async def call_model(self, model_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call Supabase Edge Function.
        
        Args:
            model_id: URL of the Edge Function
            payload: Input data for the function
            
        Returns:
            Function response
        """
        self.logger.info(f"Calling Supabase Edge Function at {model_id}")
        
        # Добавляем заголовки авторизации
        headers = {
            "Authorization": f"Bearer {self.config.get('api_key')}",
            "Content-Type": "application/json"
        }
        
        return await self._make_request(
            url=model_id,
            headers=headers,
            json=payload
        ) 