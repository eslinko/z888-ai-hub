from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List, Protocol
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class ConnectorCapability(Enum):
    """Перечисление всех возможных возможностей коннектора"""
    SUMMARY = "summary"
    VECTORIZATION = "vectorization"
    TEXT_GENERATION = "text_generation"
    CLASSIFICATION = "classification"
    OCR = "ocr"
    AUDIO_TRANSCRIPTION = "audio_transcription"

class ConnectorConfig(Protocol):
    """Протокол для конфигурации коннектора"""
    enabled: bool
    type: str
    api_key: str
    base_url: str
    default_model: Optional[str]
    capabilities: Dict[str, Any]

class ISummaryCapable:
    """Интерфейс для коннекторов, поддерживающих генерацию summary"""
    @abstractmethod
    async def generate_summary(self, text: str, **kwargs) -> str:
        """Генерация summary"""
        pass

class IVectorizationCapable:
    """Интерфейс для коннекторов, поддерживающих векторизацию"""
    @abstractmethod
    async def vectorize(self, text: str) -> List[float]:
        """Векторизация текста"""
        pass

    @abstractmethod
    async def vectorize_batch(self, texts: List[str]) -> List[List[float]]:
        """Векторизация списка текстов"""
        pass

class BaseConnector(ABC, ISummaryCapable, IVectorizationCapable):
    """
    Abstract base class for AI connectors.
    Defines a standardized interface for all AI providers.
    """

    def __init__(self, api_key: str, base_url: str, default_model: Optional[str] = None):
        """
        Initializes the connector with basic API configurations.
        
        :param api_key: API key for authentication.
        :param base_url: Base URL for the API endpoint.
        :param default_model: Default model to use if none is specified.
        """
        self.api_key = api_key
        self.base_url = base_url
        self.default_model = default_model
        self._capabilities: List[ConnectorCapability] = []

    @property
    def connector_type(self) -> str:
        """
        Returns the type of the connector.
        """
        return self.name

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Returns the name of the AI provider.
        """
        pass

    @property
    def capabilities(self) -> List[ConnectorCapability]:
        """
        Returns the list of supported capabilities.
        """
        return self._capabilities

    async def initialize(self, config: ConnectorConfig) -> None:
        """
        Initializes the connector with configuration.
        
        :param config: Connector configuration
        """
        self.api_key = config.api_key
        self.base_url = config.base_url
        self.default_model = config.default_model
        self._capabilities = self._parse_capabilities(config.capabilities)

    async def validate_config(self, config: ConnectorConfig) -> bool:
        """
        Validates the connector configuration.
        
        :param config: Connector configuration
        :return: True if configuration is valid
        """
        if not config.api_key or not config.base_url:
            return False
        return True

    async def health_check(self) -> bool:
        """
        Checks if the connector is healthy and can be used.
        
        :return: True if connector is healthy
        """
        try:
            # Простой пинг API для проверки работоспособности
            await self.call_api({"ping": True})
            return True
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return False

    def _parse_capabilities(self, capabilities_config: Dict[str, Any]) -> List[ConnectorCapability]:
        """
        Parses capabilities from configuration.
        
        :param capabilities_config: Capabilities configuration
        :return: List of supported capabilities
        """
        capabilities = []
        for capability in ConnectorCapability:
            if capabilities_config.get(capability.value, {}).get('enabled', False):
                capabilities.append(capability)
        return capabilities

    @abstractmethod
    async def call_api(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sends a request to the AI API and returns the response.
        
        :param payload: Dictionary containing request data.
        :return: API response as a dictionary.
        """
        pass

    @abstractmethod
    async def generate(self, prompt: str, model: Optional[str] = None) -> str:
        """
        Generates text using the AI model.
        
        :param prompt: Input text to generate a response from.
        :param model: Specific AI model to use.
        :return: Generated text.
        """
        pass

    @abstractmethod
    async def generate_summary(self, text: str, **kwargs) -> str:
        """
        Generates a summary of the text.
        This is the main method for text summarization.
        
        :param text: Text to summarize
        :param kwargs: Additional arguments including:
            - max_length: Maximum length of the summary (default: 500)
            - model: Specific model to use
        :return: Generated summary
        """
        pass

    async def summarize(self, text: str, max_length: int = 500, model: Optional[str] = None) -> str:
        """
        Alias for generate_summary for backward compatibility.
        Will be deprecated in future versions.
        
        :param text: Input text to summarize
        :param max_length: Maximum length of the summary
        :param model: Specific model to use
        :return: Summarized text
        """
        import warnings
        warnings.warn(
            "Method 'summarize' is deprecated. Use 'generate_summary' instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return await self.generate_summary(text, max_length=max_length, model=model)

    @abstractmethod
    def classify(self, text: str, labels: list, model: Optional[str] = None) -> str:
        """
        Classifies text into predefined categories.
        
        :param text: Input text to classify.
        :param labels: List of category labels.
        :param model: Specific AI model to use.
        :return: Predicted category label.
        """
        pass

    @abstractmethod
    def extract_text(self, image_path: str, model: Optional[str] = None) -> str:
        """
        Extracts text from an image (OCR functionality).
        
        :param image_path: Path to the image file.
        :param model: Specific AI model to use.
        :return: Extracted text.
        """
        pass

    @abstractmethod
    def transcribe(self, audio_path: str, model: Optional[str] = None) -> str:
        """
        Converts speech from an audio file to text.
        
        :param audio_path: Path to the audio file.
        :param model: Specific AI model to use.
        :return: Transcribed text.
        """
        pass

    async def vectorize(self, text: str) -> List[float]:
        """
        Vectorizes a single text.
        Must be implemented by connectors that support vectorization.
        
        :param text: Text to vectorize
        :return: Vector embedding
        """
        raise NotImplementedError("Vectorization is not supported by this connector")

    async def vectorize_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Vectorizes a batch of texts.
        Must be implemented by connectors that support vectorization.
        
        :param texts: List of texts to vectorize
        :return: List of vector embeddings
        """
        raise NotImplementedError("Batch vectorization is not supported by this connector")
