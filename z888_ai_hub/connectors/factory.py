"""
Factory for creating connectors.
"""

from typing import Dict, List, Optional, Type, Any, Tuple
from z888_ai_hub.connectors.base_connector import BaseConnector, ConnectorCapability
from z888_ai_hub.connectors.anthropic import AnthropicConnector
from z888_ai_hub.connectors.mistral import MistralConnector
from z888_ai_hub.connectors.mix_api import MixAPIConnector
from z888_ai_hub.utils.logging_utils import setup_logger

logger = setup_logger('ConnectorFactory')

class ConnectorFactory:
    """Factory for creating connectors."""
    
    _connector_types: Dict[str, Type[BaseConnector]] = {
        "anthropic": AnthropicConnector,
        "mistral": MistralConnector,
        "mix_api": MixAPIConnector
    }
    
    # Обязательные поля для разных типов коннекторов
    _required_fields: Dict[str, List[str]] = {
        "anthropic": ["api_key", "base_url", "default_model"],
        "mistral": ["api_key", "base_url", "default_model"],
        "mix_api": ["providers", "tasks"]
    }
    
    @classmethod
    def register_connector(cls, name: str, connector_class: Type[BaseConnector], required_fields: List[str]):
        """
        Register new connector type.
        
        Args:
            name: Connector type name
            connector_class: Connector class
            required_fields: List of required configuration fields
        """
        cls._connector_types[name] = connector_class
        cls._required_fields[name] = required_fields
    
    @classmethod
    def _validate_config(cls, connector_type: str, config: Dict[str, Any]) -> bool:
        """
        Validate connector configuration.
        
        Args:
            connector_type: Type of connector
            config: Configuration to validate
            
        Returns:
            True if configuration is valid
        """
        required_fields = cls._required_fields.get(connector_type, [])
        missing_fields = [field for field in required_fields if field not in config]
        
        if missing_fields:
            logger.error(f"Missing required fields for {connector_type}: {missing_fields}")
            return False
            
        return True
    
    @classmethod
    async def create_connector(cls, config: Dict[str, Any]) -> Optional[BaseConnector]:
        """
        Create connector from configuration.
        
        Args:
            config: Connector configuration
            
        Returns:
            Created connector or None if disabled
        """
        if not config.get("enabled", True):
            logger.info(f"Connector {config.get('type')} is disabled")
            return None
            
        connector_type = config.get("type")
        if not connector_type or connector_type not in cls._connector_types:
            logger.error(f"Unknown connector type: {connector_type}")
            return None
            
        try:
            # Валидируем конфигурацию
            if not cls._validate_config(connector_type, config):
                return None
                
            connector_class = cls._connector_types[connector_type]
            
            # Специальная обработка для MixAPI
            if connector_type == "mix_api":
                # Преобразуем конфигурацию в формат для MixAPI
                provider_configs = {}
                task_configs = {}
                
                # Обрабатываем провайдеры
                for provider_name, provider_config in config.get("providers", {}).items():
                    provider_configs[provider_name] = provider_config
                
                # Обрабатываем задачи
                for task_name, task_config in config.get("tasks", {}).items():
                    task_configs[task_name] = {
                        "provider": task_config["provider"],
                        "model": task_config["model"]
                    }
                
                connector = connector_class(
                    provider_configs=provider_configs,
                    task_configs=task_configs
                )
            else:
                # Стандартная обработка для других коннекторов
                connector = connector_class(**config)
            
            # Инициализируем коннектор
            await connector.initialize(config)
            
            # Проверяем работоспособность
            if not await connector.health_check():
                logger.error(f"Health check failed for connector {connector_type}")
                return None
                
            # Проверяем соответствие возможностей конфигурации
            if "capabilities" in config:
                required_capabilities = set(config["capabilities"])
                actual_capabilities = connector.capabilities
                if not required_capabilities.issubset(actual_capabilities):
                    logger.error(
                        f"Connector {connector_type} doesn't have required capabilities. "
                        f"Required: {required_capabilities}, Actual: {actual_capabilities}"
                    )
                    return None
                
            logger.info(f"Successfully created connector: {connector_type}")
            return connector
            
        except Exception as e:
            logger.error(f"Error creating connector {connector_type}: {str(e)}")
            return None
    
    @classmethod
    def _get_task_config(cls, config: Dict[str, Any], task_name: str) -> Tuple[Optional[str], List[str], int, int]:
        """
        Get task configuration including fallback providers and retry settings.
        
        Args:
            config: Full configuration
            task_name: Name of the task
            
        Returns:
            Tuple of (main_provider, fallback_providers, max_retries, timeout)
        """
        tasks_config = config.get("tasks", {})
        task_config = tasks_config.get(task_name, {})
        
        return (
            task_config.get("provider"),
            task_config.get("fallback_providers", []),
            task_config.get("max_retries", 3),
            task_config.get("timeout", 30)
        )
    
    @classmethod
    async def create_connectors_for_tasks(
        cls,
        config: Dict[str, Any],
        required_capabilities: Optional[List[ConnectorCapability]] = None
    ) -> Dict[str, BaseConnector]:
        """
        Create connectors based on required capabilities.
        
        Args:
            config: Connectors configuration
            required_capabilities: List of required capabilities
            
        Returns:
            Dictionary of created connectors
            
        Raises:
            ValueError: If required capabilities are not found
        """
        if required_capabilities is None:
            required_capabilities = [
                ConnectorCapability.SUMMARY,
                ConnectorCapability.VECTORIZATION
            ]
            
        connectors = {}
        connectors_config = config.get("connectors", {})
        
        # Создаем коннекторы
        for name, connector_config in connectors_config.items():
            connector = await cls.create_connector(connector_config)
            if connector:
                connectors[name] = connector
                
        # Проверяем наличие необходимых возможностей
        available_capabilities = set()
        for connector in connectors.values():
            available_capabilities.update(connector.capabilities)
            
        missing_capabilities = set(required_capabilities) - available_capabilities
        if missing_capabilities:
            raise ValueError(
                f"Missing required capabilities: {missing_capabilities}. "
                f"Available capabilities: {available_capabilities}"
            )
            
        # Проверяем, что каждый коннектор имеет правильные возможности
        for name, connector in connectors.items():
            config = connectors_config[name]
            if "capabilities" in config:
                required = set(config["capabilities"])
                actual = connector.capabilities
                if not required.issubset(actual):
                    raise ValueError(
                        f"Connector {name} doesn't have required capabilities. "
                        f"Required: {required}, Actual: {actual}"
                    )
            
        # Добавляем информацию о fallback провайдерах и настройках retry
        for capability in required_capabilities:
            task_name = capability.name.lower()
            main_provider, fallback_providers, max_retries, timeout = cls._get_task_config(config, task_name)
            
            if main_provider and main_provider in connectors:
                connector = connectors[main_provider]
                connector.max_retries = max_retries
                connector.timeout = timeout
                connector.fallback_providers = [
                    connectors[provider] for provider in fallback_providers
                    if provider in connectors
                ]
            
        return connectors 