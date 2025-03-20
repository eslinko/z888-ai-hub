import anthropic
import os
from typing import Any, Dict, Optional, List
from z888_ai_hub.connectors.base_connector import (
    BaseConnector,
    ConnectorCapability,
    ConnectorConfig,
    ISummaryCapable,
    IVectorizationCapable
)
from z888_ai_hub.utils.logging_utils import setup_logger


class AnthropicConnector(BaseConnector, ISummaryCapable):
    """
    AI Connector for Anthropic Claude models.
    Supports text generation, summarization, and classification.
    """

    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.anthropic.com", default_model: str = "claude-3-7-sonnet-20250219"):
        """
        Initializes the AnthropicConnector with API key and settings.

        :param api_key: API key for Anthropic API. If not provided, will try to get from ANTHROPIC_API_KEY environment variable.
        :param base_url: API endpoint (default: Anthropic API URL).
        :param default_model: Default AI model to use.
        """
        api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("API key must be provided either through constructor or ANTHROPIC_API_KEY environment variable")
            
        super().__init__(api_key, base_url, default_model)
        self.logger = setup_logger('AnthropicConnector')
        self.logger.info(f"API Key: {api_key}")
        self.client = anthropic.Anthropic(api_key=api_key)
        self.logger.info(f"Initialized Anthropic connector with model: {default_model}")
        
        # Устанавливаем поддерживаемые возможности
        self._capabilities = [
            ConnectorCapability.SUMMARY,
            ConnectorCapability.TEXT_GENERATION,
            ConnectorCapability.CLASSIFICATION
        ]

    @property
    def name(self) -> str:
        """Returns the name of the provider."""
        return "Anthropic"

    async def initialize(self, config: ConnectorConfig) -> None:
        """
        Initializes the connector with configuration.
        
        :param config: Connector configuration
        """
        await super().initialize(config)
        self.logger.info(f"Initialized Anthropic connector with capabilities: {self.capabilities}")

    async def validate_config(self, config: ConnectorConfig) -> bool:
        """
        Validates the connector configuration.
        
        :param config: Connector configuration
        :return: True if configuration is valid
        """
        if not await super().validate_config(config):
            return False
            
        # Проверяем специфичные для Anthropic параметры
        if not config.api_key or not config.api_key.startswith("sk-"):
            self.logger.error("Invalid Anthropic API key format")
            return False
            
        return True

    async def health_check(self) -> bool:
        """
        Checks if the connector is healthy and can be used.
        
        :return: True if connector is healthy
        """
        try:
            # Простой тест генерации для проверки работоспособности
            response = await self.call_api(
                messages=[{"role": "user", "content": "test"}],
                max_tokens=10
            )
            return "error" not in response
        except Exception as e:
            self.logger.error(f"Health check failed: {str(e)}")
            return False

    async def call_api(self, messages: list, model: Optional[str] = None, max_tokens: int = 1024) -> Dict[str, Any]:
        """
        Makes a request to the Anthropic API.

        :param messages: List of message dictionaries.
        :param model: Model to use.
        :param max_tokens: Maximum tokens in response.
        :return: API response as a dictionary.
        """
        try:
            self.logger.debug(f"Making API call to Anthropic with model: {model}")
            response = self.client.messages.create(
                messages=messages,
                model=model or self.default_model,
                max_tokens=max_tokens
            )
            self.logger.debug("Successfully received response from Anthropic API")
            return {"text": response.content[0].text}
        except Exception as e:
            error_msg = f"Anthropic API Error: {e}"
            self.logger.error(error_msg, exc_info=True)
            return {"error": str(e)}

    async def generate(self, prompt: str, model: Optional[str] = None) -> str:
        """
        Generates text using Anthropic Claude.

        :param prompt: Input text to generate a response from.
        :param model: AI model to use (defaults to self.default_model).
        :return: Generated text.
        """
        self.logger.info("Starting text generation")
        self.logger.debug(f"Input prompt length: {len(prompt)} characters")

        response = await self.call_api(
            messages=[{"role": "user", "content": prompt}],
            model=model
        )
        generated_text = response.get("text", "")
        
        self.logger.info(f"Successfully generated text, length: {len(generated_text)} characters")
        return generated_text

    async def generate_summary(self, text: str, **kwargs) -> str:
        """
        Generates a summary of the given text.
        
        :param text: The input text to summarize.
        :param kwargs: Additional arguments including:
            - max_length: Maximum length of the summary (default: 280)
            - model: Specific model to use
        :return: Summarized text.
        """
        max_length = kwargs.get('max_length', 280)
        model = kwargs.get('model')
        
        self.logger.info(f"Starting text summarization (max length: {max_length})")
        self.logger.debug(f"Input text length: {len(text)} characters")

        response = await self.call_api(
            messages=[{
                "role": "user",
                "content": f"Summarize the following text in {max_length} characters or less. Focus on key points: {text}"
            }],
            model=model
        )
        summary = response.get("text", "")

        # Trim summary if it exceeds max_length
        if len(summary) > max_length:
            self.logger.warning(f"Summary exceeded max length ({len(summary)} > {max_length}), trimming...")
            summary = summary[:max_length-3] + "..."

        self.logger.info(f"Successfully generated summary, length: {len(summary)} characters")
        return summary

    def classify(self, text: str, labels: list, model: Optional[str] = None) -> str:
        """
        Classifies text into predefined categories using Anthropic Claude.

        :param text: Input text to classify.
        :param labels: List of category labels.
        :param model: AI model to use (defaults to self.default_model).
        :return: Predicted category label.
        """
        self.logger.info("Starting text classification")
        self.logger.debug(f"Input text length: {len(text)} characters, Labels: {labels}")

        labels_str = ", ".join(labels)
        response = self.call_api(
            messages=[{
                "role": "user",
                "content": f"Classify the following text into one of these categories: {labels_str}. Only respond with the category name.\n\nText: {text}"
            }],
            model=model
        )
        classification = response.get("text", "").strip()
        
        if classification not in labels:
            self.logger.warning(f"Classification result '{classification}' not in provided labels")
            classification = labels[0]  # Default to first label if result is invalid
            
        self.logger.info(f"Successfully classified text as: {classification}")
        return classification

    def extract_text(self, image_path: str, model: Optional[str] = None) -> str:
        """
        Extracts text from an image (OCR functionality).
        Note: Anthropic currently doesn't support direct OCR, so this is a placeholder.

        :param image_path: Path to the image file.
        :param model: Specific AI model to use.
        :return: Extracted text.
        """
        self.logger.error("OCR functionality not supported by Anthropic")
        raise NotImplementedError("OCR functionality is not supported by Anthropic")

    def transcribe(self, audio_path: str, model: Optional[str] = None) -> str:
        """
        Converts speech from an audio file to text.
        Note: Anthropic currently doesn't support direct audio transcription, so this is a placeholder.

        :param audio_path: Path to the audio file.
        :param model: Specific AI model to use.
        :return: Transcribed text.
        """
        self.logger.error("Audio transcription not supported by Anthropic")
        raise NotImplementedError("Audio transcription is not supported by Anthropic")
