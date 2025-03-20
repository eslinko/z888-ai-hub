"""
MixAPI connector for working with different AI models via their APIs.
Supports various tasks like vectorization, text generation, etc.
"""

import os
from typing import Any, Dict, List, Optional, Union
from z888_ai_hub.connectors.base_connector import (
    BaseConnector,
    ConnectorCapability,
    ConnectorConfig,
    ISummaryCapable,
    IVectorizationCapable
)
from z888_ai_hub.connectors.providers.registry import ProviderRegistry
from z888_ai_hub.utils.env_loader import load_env
from z888_ai_hub.utils.logging_utils import setup_logger


class MixAPIConnector(BaseConnector, ISummaryCapable, IVectorizationCapable):
    """
    Connector for working with different AI models via their APIs.
    Supports various tasks and can be configured to use different models for different tasks.
    """

    def __init__(
        self,
        provider_configs: Dict[str, Dict[str, Any]],
        task_configs: Optional[Dict[str, Dict[str, Any]]] = None
    ):
        """
        Initialize MixAPIConnector.
        
        Args:
            provider_configs: Configuration for providers, e.g.:
                {
                    "supabase_edge": {
                        "api_key": "your-api-key"
                    },
                    "huggingface": {
                        "api_key": "your-hf-key",
                        "base_url": "https://api-inference.huggingface.co/models"
                    }
                }
            task_configs: Configuration for tasks, e.g.:
                {
                    "vectorization": {
                        "provider": "supabase_edge",
                        "model": "https://xhppqnkewoqhcglccgkq.supabase.co/functions/v1/victorize"
                    }
                }
        """
        super().__init__()
        self.logger = setup_logger('MixAPIConnector')
        self.logger.info("Initializing MixAPIConnector")
        
        # Инициализируем провайдеры
        self.providers = {}
        for provider_name, config in provider_configs.items():
            provider_class = ProviderRegistry.get_provider(provider_name)
            self.providers[provider_name] = provider_class(config)
            self.logger.info(f"Initialized provider: {provider_name}")
        
        # Конфигурация для разных задач
        self.task_configs = task_configs or {}
        
        # Определяем поддерживаемые возможности на основе конфигурации
        self._capabilities = []
        if "vectorization" in self.task_configs:
            self._capabilities.append(ConnectorCapability.VECTORIZATION)
        if "summarization" in self.task_configs:
            self._capabilities.append(ConnectorCapability.SUMMARY)
        if "generation" in self.task_configs:
            self._capabilities.append(ConnectorCapability.TEXT_GENERATION)
            
        self.logger.info(f"Initialized with capabilities: {self.capabilities}")

    @property
    def name(self) -> str:
        """Get connector name."""
        return "mix_api"

    async def initialize(self, config: ConnectorConfig) -> None:
        """
        Initializes the connector with configuration.
        
        :param config: Connector configuration
        """
        await super().initialize(config)
        self.logger.info(f"Initialized MixAPIConnector with capabilities: {self.capabilities}")

    async def validate_config(self, config: ConnectorConfig) -> bool:
        """
        Validates the connector configuration.
        
        :param config: Connector configuration
        :return: True if configuration is valid
        """
        if not await super().validate_config(config):
            return False
            
        # Проверяем конфигурацию для каждой задачи
        for task_name, task_config in self.task_configs.items():
            provider_name = task_config.get("provider")
            if not provider_name or provider_name not in self.providers:
                self.logger.error(f"Invalid provider {provider_name} for task {task_name}")
                return False
                
        return True

    async def health_check(self) -> bool:
        """
        Checks if the connector is healthy and can be used.
        
        :return: True if connector is healthy
        """
        try:
            # Проверяем каждую задачу
            for task_name, task_config in self.task_configs.items():
                provider_name = task_config["provider"]
                provider = self.providers[provider_name]
                
                # Делаем тестовый запрос
                test_payload = {"test": True}
                await provider.call_model(task_config["model"], test_payload)
                
            return True
        except Exception as e:
            self.logger.error(f"Health check failed: {str(e)}")
            return False

    async def _call_task(self, task_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call appropriate provider for the given task.
        
        Args:
            task_name: Name of the task
            payload: Input data
            
        Returns:
            Provider response
        """
        if task_name not in self.task_configs:
            raise ValueError(f"Task {task_name} not configured")
            
        task_config = self.task_configs[task_name]
        provider_name = task_config["provider"]
        provider = self.providers[provider_name]
        
        return await provider.call_model(task_config["model"], payload)

    async def vectorize(self, text: str) -> List[float]:
        """
        Create vector embedding for text using configured model.
        
        :param text: Text to vectorize
        :return: Vector embedding
        """
        if ConnectorCapability.VECTORIZATION not in self.capabilities:
            raise NotImplementedError("Vectorization not configured")
            
        try:
            self.logger.info(f"Starting vectorization for text of length {len(text)}")
            
            payload = {"text": text}
            response = await self._call_task("vectorization", payload)
            
            # Обрабатываем ответ в зависимости от провайдера
            embedding = response.get("embedding")
            if not embedding:
                raise ValueError("No embedding in response")
                
            self.logger.info(f"Successfully created embedding, dimension: {len(embedding)}")
            return embedding
            
        except Exception as e:
            self.logger.error(f"Error creating embedding: {str(e)}")
            raise

    async def vectorize_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Create vector embeddings for multiple texts.
        
        :param texts: List of texts to vectorize
        :return: List of vector embeddings
        """
        if ConnectorCapability.VECTORIZATION not in self.capabilities:
            raise NotImplementedError("Vectorization not configured")
            
        try:
            self.logger.info(f"Starting batch vectorization for {len(texts)} texts")
            
            payload = {"texts": texts}
            response = await self._call_task("vectorization", payload)
            
            # Обрабатываем ответ в зависимости от провайдера
            embeddings = response.get("embeddings", [])
            if not embeddings:
                raise ValueError("No embeddings in response")
                
            self.logger.info(f"Successfully created {len(embeddings)} embeddings")
            return embeddings
            
        except Exception as e:
            self.logger.error(f"Error creating batch embeddings: {str(e)}")
            raise

    async def generate_summary(self, text: str, **kwargs) -> str:
        """
        Generate a summary of the text using configured model.
        
        :param text: Text to summarize
        :param kwargs: Additional arguments including:
            - max_length: Maximum length of the summary
            - model: Specific model to use
        :return: Generated summary
        """
        if ConnectorCapability.SUMMARY not in self.capabilities:
            raise NotImplementedError("Summarization not configured")
            
        try:
            max_length = kwargs.get('max_length', 280)
            self.logger.info(f"Starting summarization (max length: {max_length})")
            
            payload = {
                "text": text,
                "max_length": max_length
            }
            
            response = await self._call_task("summarization", payload)
            
            # Обрабатываем ответ в зависимости от провайдера
            summary = response.get("summary", "")
            if not summary:
                raise ValueError("No summary in response")
                
            # Обрезаем, если превышает максимальную длину
            if len(summary) > max_length:
                summary = summary[:max_length-3] + "..."
                
            self.logger.info(f"Successfully generated summary, length: {len(summary)}")
            return summary
            
        except Exception as e:
            self.logger.error(f"Error generating summary: {str(e)}")
            raise

    async def generate(self, prompt: str, model: Optional[str] = None) -> str:
        """
        Generate text using configured model.
        
        :param prompt: Input prompt
        :param model: Specific model to use
        :return: Generated text
        """
        if ConnectorCapability.TEXT_GENERATION not in self.capabilities:
            raise NotImplementedError("Text generation not configured")
            
        try:
            self.logger.info("Starting text generation")
            
            payload = {
                "prompt": prompt,
                "model": model
            }
            
            response = await self._call_task("generation", payload)
            
            # Обрабатываем ответ в зависимости от провайдера
            generated_text = response.get("generated_text", "")
            if not generated_text:
                raise ValueError("No generated text in response")
                
            self.logger.info(f"Successfully generated text, length: {len(generated_text)}")
            return generated_text
            
        except Exception as e:
            self.logger.error(f"Error generating text: {str(e)}")
            raise 