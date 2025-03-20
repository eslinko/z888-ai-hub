"""
Registry for model providers.
"""

from typing import Dict, Type
from .base import ModelProvider
from .supabase_edge import SupabaseEdgeFunctionProvider
from .huggingface import HuggingFaceProvider

class ProviderRegistry:
    """Реестр доступных провайдеров"""
    
    _providers: Dict[str, Type[ModelProvider]] = {
        "supabase_edge": SupabaseEdgeFunctionProvider,
        "huggingface": HuggingFaceProvider
    }
    
    @classmethod
    def register(cls, name: str, provider_class: Type[ModelProvider]):
        """
        Register new provider.
        
        Args:
            name: Provider name
            provider_class: Provider class
        """
        cls._providers[name] = provider_class
    
    @classmethod
    def get_provider(cls, name: str) -> Type[ModelProvider]:
        """
        Get provider class by name.
        
        Args:
            name: Provider name
            
        Returns:
            Provider class
            
        Raises:
            ValueError: If provider not found
        """
        if name not in cls._providers:
            raise ValueError(f"Provider {name} not found")
        return cls._providers[name] 