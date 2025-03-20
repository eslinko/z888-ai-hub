import os
from openai import OpenAI
from typing import Any, Dict, Optional
from connectors.base_connector import BaseConnector
from utils.env_loader import load_env
from utils.logging_utils import setup_logger
from base64 import b64encode


class OpenAIConnector(BaseConnector):
    """
    AI Connector for OpenAI.
    Supports text generation, summarization, and vision tasks.
    """

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, default_model: Optional[str] = None):
        """
        Initializes the OpenAIConnector with API key and settings.

        :param api_key: API key for OpenAI API.
        :param base_url: API endpoint (default: OpenAI API URL).
        :param default_model: Default AI model to use.
        """
        api_key = api_key or load_env("OPENAI_API_KEY")
        base_url = base_url or "https://api.openai.com/v1"
        default_model = default_model or "gpt-4-turbo-preview"

        super().__init__(api_key, base_url, default_model)
        self.client = OpenAI(api_key=self.api_key)
        self.logger = setup_logger('OpenAIConnector')
        self.logger.info(f"Initialized OpenAI connector with model: {default_model}")

    @property
    def name(self) -> str:
        """Returns the name of the provider."""
        return "OpenAI"

    def call_api(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Makes a request to the OpenAI API.

        :param payload: Dictionary with request parameters.
        :return: API response as a dictionary.
        """
        try:
            self.logger.debug(f"Making API call to OpenAI with model: {payload.get('model')}")
            response = self.client.chat.completions.create(**payload)
            self.logger.debug("Successfully received response from OpenAI API")
            return {"text": response.choices[0].message.content}
        except Exception as e:
            error_msg = f"OpenAI API Error: {e}"
            self.logger.error(error_msg, exc_info=True)
            return {"error": str(e)}

    def generate(self, prompt: str, model: Optional[str] = None) -> str:
        """
        Generates text using OpenAI model.

        :param prompt: The input prompt.
        :param model: AI model to use (defaults to self.default_model).
        :return: Generated text.
        """
        model = model or self.default_model
        self.logger.info("Starting text generation")
        self.logger.debug(f"Using model: {model}")

        payload = {
            "model": model,
            "temperature": 0.0,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        response = self.call_api(payload)
        result = response.get("text", "")
        
        self.logger.info(f"Successfully generated text, length: {len(result)} characters")
        return result

    def summarize(self, text: str, max_length: int = 280, model: Optional[str] = None) -> str:
        """
        Summarizes the given text.

        :param text: The input text to summarize.
        :param max_length: Maximum length of the summary.
        :param model: AI model to use (defaults to self.default_model).
        :return: Summarized text.
        """
        model = model or self.default_model
        self.logger.info(f"Starting text summarization (max length: {max_length})")
        self.logger.debug(f"Input text length: {len(text)} characters")

        payload = {
            "model": model,
            "temperature": 0.0,
            "messages": [
                {"role": "user", "content": f"Summarize the following text in {max_length} characters or less: {text}"}
            ]
        }
        response = self.call_api(payload)
        summary = response.get("text", "")

        if len(summary) > max_length:
            self.logger.warning(f"Summary exceeded max length ({len(summary)} > {max_length}), trimming...")
            summary = summary[:max_length-3] + "..."

        self.logger.info(f"Successfully generated summary, length: {len(summary)} characters")
        return summary

    async def extract_text(self, image_path: str, model: Optional[str] = None) -> str:
        """
        Performs OCR/image analysis using GPT-4 Vision.

        :param image_path: Path to the image file.
        :param model: AI model to use (defaults to GPT-4 Vision).
        :return: Extracted text from the image.
        """
        model = model or "gpt-4-vision-preview"
        self.logger.info(f"Starting image analysis for: {os.path.basename(image_path)}")
        
        if not os.path.exists(image_path):
            error_msg = f"Image file not found: {image_path}"
            self.logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        try:
            with open(image_path, "rb") as img_file:
                image_b64 = b64encode(img_file.read()).decode("utf-8")
                self.logger.debug("Successfully encoded image to base64")

            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Please extract and describe all the text visible in this image."},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}}
                        ]
                    }
                ],
                "max_tokens": 1000
            }

            response = self.call_api(payload)
            extracted_text = response.get("text", "")
            self.logger.info(f"Successfully analyzed image, extracted text length: {len(extracted_text)} characters")
            return extracted_text
            
        except Exception as e:
            self.logger.error(f"Failed to process image {image_path}: {str(e)}", exc_info=True)
            raise
