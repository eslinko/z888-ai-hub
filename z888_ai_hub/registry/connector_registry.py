from z888_ai_hub.connectors.anthropic import AnthropicConnector
from z888_ai_hub.connectors.mistral import MistralConnector
from z888_ai_hub.utils.env_loader import load_env
from z888_ai_hub.utils.logging_utils import setup_logger


class ConnectorRegistry:
    """
    Manages available AI connectors.
    Provides a unified interface to register and access AI models.
    """

    def __init__(self):
        self.connectors = {}
        self.logger = setup_logger('ConnectorRegistry')
        self.logger.info("Initializing AI Connector Registry")

    def register(self, name: str, connector_instance):
        """Registers a new AI connector."""
        self.logger.info(f"Registering connector: {name}")
        self.connectors[name] = connector_instance
        self.logger.debug(f"Successfully registered connector: {name}")

    def get(self, name: str):
        """Retrieves a registered AI connector by name."""
        connector = self.connectors.get(name)
        if connector is None:
            self.logger.warning(f"Requested connector not found: {name}")
        else:
            self.logger.debug(f"Retrieved connector: {name}")
        return connector

    def initialize_default_connectors(self):
        """Registers default connectors."""
        self.logger.info("Initializing default connectors")
        
        anthropic_key = load_env("ANTHROPIC_API_KEY")
        mistral_key = load_env("MISTRAL_API_KEY")
        
        self.register("anthropic", AnthropicConnector(api_key=anthropic_key))
        self.register("mistral", MistralConnector(api_key=mistral_key))
        
        self.logger.info("Default connectors initialized successfully")


# Global registry instance
registry = ConnectorRegistry()
registry.initialize_default_connectors()
