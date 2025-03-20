import yaml
import os
import pkg_resources
from typing import List, Dict, Optional
from z888_ai_hub.registry.connector_registry import registry
from z888_ai_hub.utils.logging_utils import setup_logger


class AIClient:
    """
    High-level AI client for handling functional tasks across multiple AI providers.
    """

    DEFAULT_CONFIG_PATH = "config/ai_tasks_mapping.yaml"

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize AI client.
        
        Args:
            config_path: Optional path to custom config file. If not provided,
                       will use the default config from the package.
        """
        self.logger = setup_logger('AIClient')
        self.task_mapping = self._load_config(config_path)
        self.logger.debug("Successfully loaded AI tasks mapping configuration")

    def _load_config(self, custom_config_path: Optional[str] = None) -> Dict:
        """
        Load configuration from file.
        
        Args:
            custom_config_path: Optional path to custom config file
            
        Returns:
            Dict with tasks configuration
            
        Raises:
            FileNotFoundError: If neither default nor custom config can be found
        """
        try:
            # Try custom config first if provided
            if custom_config_path:
                with open(custom_config_path, 'r') as f:
                    return yaml.safe_load(f)["tasks"]

            # Otherwise load default config from package
            default_config = pkg_resources.resource_string(
                "z888_ai_hub", 
                self.DEFAULT_CONFIG_PATH
            ).decode('utf-8')
            return yaml.safe_load(default_config)["tasks"]

        except Exception as e:
            self.logger.error(f"Failed to load AI tasks mapping: {str(e)}", exc_info=True)
            raise

    def _get_connector(self, task_name: str):
        """
        Determines the correct AI connector for a given task.
        """
        self.logger.debug(f"Getting connector for task: {task_name}")
        provider = self.task_mapping.get(task_name, {}).get("default")
        
        if not provider:
            error_msg = f"No provider configured for task: {task_name}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
            
        try:
            connector = registry.get(provider)
            self.logger.debug(f"Successfully got connector: {provider} for task: {task_name}")
            return connector
        except Exception as e:
            self.logger.error(f"Failed to get connector for {provider}: {str(e)}", exc_info=True)
            raise

    async def generate_text(self, prompt: str) -> str:
        """Generates text using the default AI model."""
        self.logger.info("Starting text generation")
        try:
            connector = self._get_connector("text_generation")
            result = await connector.generate(prompt)
            self.logger.debug(f"Successfully generated text, length: {len(result)} characters")
            return result
        except Exception as e:
            self.logger.error(f"Text generation failed: {str(e)}", exc_info=True)
            raise

    async def summarize_text(self, text: str, max_length: int = 280) -> str:
        """Summarizes text with a default AI provider."""
        self.logger.info(f"Starting text summarization (max length: {max_length})")
        try:
            connector = self._get_connector("summarization")
            summary = await connector.summarize(text, max_length)
            self.logger.debug(f"Successfully generated summary, length: {len(summary)} characters")
            return summary
        except Exception as e:
            self.logger.error(f"Text summarization failed: {str(e)}", exc_info=True)
            raise

    def classify_text(self, text: str, labels: List[str]) -> str:
        """Classifies text into predefined categories."""
        self.logger.info(f"Starting text classification with {len(labels)} labels")
        try:
            connector = self._get_connector("classification")
            result = connector.classify(text, labels)
            self.logger.debug(f"Successfully classified text as: {result}")
            return result
        except Exception as e:
            self.logger.error(f"Text classification failed: {str(e)}", exc_info=True)
            raise

    async def extract_text_from_image(self, image_path: str) -> str:
        """Extracts text from an image using OCR."""
        self.logger.info(f"Starting OCR for image: {os.path.basename(image_path)}")

        if not os.path.exists(image_path):
            error_msg = f"Image file not found: {image_path}"
            self.logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        try:
            connector = self._get_connector("ocr")
            extracted_text = await connector.extract_text(image_path)
            self.logger.debug(f"Successfully extracted text from image, length: {len(extracted_text)} characters")
            return extracted_text
        except Exception as e:
            error_msg = f"OCR extraction failed for {image_path}: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise
