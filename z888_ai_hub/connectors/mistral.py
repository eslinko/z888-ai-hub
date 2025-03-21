import os
import json
import asyncio
import aiohttp
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage
from typing import Any, Dict, Optional, List
from z888_ai_hub.connectors.base_connector import (
    BaseConnector,
    ConnectorConfig,
    ConnectorCapability,
    ISummaryCapable,
    IVectorizationCapable
)
from z888_ai_hub.utils.env_loader import load_env
from z888_ai_hub.utils.logging_utils import setup_logger
from base64 import b64encode


class MistralConnector(BaseConnector, ISummaryCapable):
    """
    AI Connector for Mistral AI.
    Supports text generation, summarization, OCR, and classification.
    """

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, default_model: Optional[str] = None):
        """
        Initializes the MistralConnector with API key and settings.

        :param api_key: API key for Mistral API.
        :param base_url: API endpoint (default: Mistral API URL).
        :param default_model: Default AI model to use.
        """
        api_key = api_key or load_env("MISTRAL_API_KEY")
        base_url = base_url or "https://api.mistral.ai"
        default_model = default_model or "mistral-large-latest"

        super().__init__(api_key, base_url, default_model)
        self.client = MistralClient(api_key=self.api_key)
        self.logger = setup_logger('MistralConnector', log_to_file=True)
        self.logger.info(f"Initialized Mistral connector with model: {default_model}")
        
        # Устанавливаем поддерживаемые возможности
        self._capabilities = [
            ConnectorCapability.SUMMARY,
            ConnectorCapability.TEXT_GENERATION,
            ConnectorCapability.CLASSIFICATION,
            ConnectorCapability.OCR
        ]

        self.last_request_time = 0
        self.min_request_interval = 1  # минимальный интервал между запросами в секундах

    @property
    def name(self) -> str:
        """Returns the name of the provider."""
        return "Mistral"

    async def initialize(self, config: ConnectorConfig) -> None:
        """
        Initializes the connector with configuration.
        
        :param config: Connector configuration
        """
        await super().initialize(config)
        self.logger.info(f"Initialized Mistral connector with capabilities: {self.capabilities}")

    async def validate_config(self, config: ConnectorConfig) -> bool:
        """
        Validates the connector configuration.
        
        :param config: Connector configuration
        :return: True if configuration is valid
        """
        if not await super().validate_config(config):
            return False
            
        # Проверяем специфичные для Mistral параметры
        if not config.api_key:
            self.logger.error("Mistral API key is required")
            return False
            
        return True

    async def health_check(self) -> bool:
        """
        Checks if the connector is healthy and can be used.
        
        :return: True if connector is healthy
        """
        try:
            # Простой тест генерации для проверки работоспособности
            payload = {
                "model": self.default_model,
                "temperature": 0.0,
                "messages": [{"role": "user", "content": "test"}]
            }
            response = await self.call_api(payload)
            return "error" not in response
        except Exception as e:
            self.logger.error(f"Health check failed: {str(e)}")
            return False

    async def call_api(self, payload: dict) -> dict:
        try:
            # Если это OCR запрос с изображением
            if any(isinstance(msg.get("content"), list) for msg in payload["messages"]):
                response = self.client.chat(
                    model=self.default_model,
                    messages=payload["messages"],
                    temperature=0.1  # Lower temperature for more accurate OCR
                )
            else:
                # Для обычных текстовых запросов
                messages = [ChatMessage(role=msg["role"], content=msg["content"]) 
                          for msg in payload["messages"]]
                response = self.client.chat(
                    model=self.default_model,
                    messages=messages,
                    temperature=payload.get("temperature", 0.7)
                )
            
            return {"text": response.choices[0].message.content}
        except Exception as e:
            self.logger.error(f"Error calling Mistral API: {str(e)}")
            return {"error": str(e)}

    async def generate(self, prompt: str, model: Optional[str] = None) -> str:
        """
        Generates text using Mistral LLM.

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
        response = await self.call_api(payload)
        result = response.get("text", "")
        
        self.logger.info(f"Successfully generated text, length: {len(result)} characters")
        return result

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
        model = kwargs.get('model', self.default_model)
        
        self.logger.info(f"Starting text summarization (max length: {max_length})")
        self.logger.debug(f"Input text length: {len(text)} characters")

        payload = {
            "model": model,
            "temperature": 0.0,
            "messages": [
                {"role": "user", "content": f"Summarize the complaint in {max_length} characters or less: {text}"}
            ]
        }
        response = await self.call_api(payload)
        summary = response.get("text", "")

        if len(summary) > max_length:
            self.logger.warning(f"Summary exceeded max length ({len(summary)} > {max_length}), trimming...")
            summary = summary[:max_length-3] + "..."

        self.logger.info(f"Successfully generated summary, length: {len(summary)} characters")
        return summary

    async def _wait_for_rate_limit(self):
        """
        Ожидает необходимое время между запросами для соблюдения ограничений API
        """
        current_time = asyncio.get_event_loop().time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.min_request_interval:
            await asyncio.sleep(self.min_request_interval - time_since_last_request)
        self.last_request_time = asyncio.get_event_loop().time()

    async def upload_pdf_to_mistral(self, file_path: str) -> Optional[str]:
        """
        Uploads a PDF file to Mistral and returns the signed URL for OCR processing.

        :param file_path: Path to the PDF file to upload.
        :return: Signed URL to access the uploaded document.
        """
        await self._wait_for_rate_limit()
        
        if not os.path.exists(file_path):
            self.logger.error(f"File not found: {file_path}")
            return None

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}"
            }

            # Upload file
            self.logger.debug(f"Uploading file to {self.base_url}/v1/files")
            async with aiohttp.ClientSession() as session:
                # Step 1: Upload PDF
                form = aiohttp.FormData()
                form.add_field(
                    'file',
                    open(file_path, 'rb'),
                    filename=os.path.basename(file_path),
                    content_type='application/pdf'
                )
                form.add_field('purpose', 'ocr')

                async with session.post(
                    f"{self.base_url}/v1/files",
                    data=form,
                    headers=headers
                ) as response:
                    response_text = await response.text()
                    self.logger.debug(f"Upload response: {response_text}")
                    
                    if response.status != 200:
                        self.logger.error(f"Error uploading PDF: {response_text}")
                        return None

                    response_json = json.loads(response_text)
                    file_id = response_json.get("id")
                    if not file_id:
                        self.logger.error("Error: No file ID returned from upload")
                        return None

                    # Step 2: Get signed URL
                    signed_url_endpoint = f"{self.base_url}/v1/files/{file_id}/url"
                    self.logger.debug(f"Getting signed URL from {signed_url_endpoint}")
                    
                    async with session.get(signed_url_endpoint, headers=headers) as response:
                        response_text = await response.text()
                        self.logger.debug(f"Signed URL response: {response_text}")
                        
                        if response.status != 200:
                            self.logger.error(f"Error getting signed URL: {response_text}")
                            return None

                        response_json = json.loads(response_text)
                        return response_json.get("url")

        except Exception as e:
            self.logger.error(f"Error during PDF upload: {str(e)}", exc_info=True)
            return None

    async def process_image(self, image_url: str, model: Optional[str] = None) -> str:
        """
        Обрабатывает изображение через Mistral API.
        
        :param image_url: URL изображения
        :param model: Модель для обработки
        :return: Извлеченный текст
        """
        model = model or self.default_model
        self.logger.info(f"Обработка изображения с моделью {model}")
        
        try:
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Extract all text from this Telegram chat screenshot, including timestamps, sender names, and message content. Format the output as a list of messages, where each message has a timestamp, sender, and text content."
                            },
                            {
                                "type": "image_url",
                                "image_url": image_url
                            }
                        ]
                    }
                ],
                "temperature": 0.1  # Lower temperature for more accurate OCR
            }
            
            response = await self.call_api(payload)
            
            if "error" in response:
                raise Exception(f"Ошибка обработки изображения: {response['error']}")
                
            return response.get("text", "")
            
        except Exception as e:
            self.logger.error(f"Ошибка при обработке изображения: {str(e)}")
            raise

    async def extract_text(self, image_path: str, model: Optional[str] = None) -> str:
        """
        Извлекает текст из изображения с помощью OCR.
        
        :param image_path: Путь к файлу изображения
        :param model: Опциональная модель для OCR
        :return: Извлеченный текст
        """
        model = model or self.default_model
        self.logger.info(f"Начинаю OCR обработку файла: {image_path} с моделью {model}")
        
        try:
            # Шаг 1: Загрузка файла и получение signed URL
            self.logger.info("Шаг 1: Загрузка файла и получение signed URL...")
            signed_url = await self.upload_pdf_to_mistral(image_path)
            if not signed_url:
                raise Exception("Failed to get signed URL")
            self.logger.info(f"Получен signed URL: {signed_url}...")
            
            # Шаг 2: Обработка изображения
            self.logger.info("Шаг 2: Обработка изображения...")
            return await self.process_image(signed_url, model)
            
        except Exception as e:
            self.logger.error(f"Ошибка при OCR обработке: {str(e)}")
            raise

    def classify(self, text: str, labels: list, model: Optional[str] = None) -> str:
        """
        Classifies text into predefined categories using Mistral.

        :param text: Input text to classify.
        :param labels: List of category labels.
        :param model: AI model to use (defaults to self.default_model).
        :return: Predicted category label.
        """
        self.logger.info("Starting text classification")
        self.logger.debug(f"Input text length: {len(text)} characters, Labels: {labels}")

        model = model or self.default_model
        labels_str = ", ".join(labels)
        
        payload = {
            "model": model,
            "temperature": 0.0,
            "messages": [
                {
                    "role": "user",
                    "content": f"Classify the following text into one of these categories: {labels_str}. Only respond with the category name.\n\nText: {text}"
                }
            ]
        }
        
        response = self.call_api(payload)
        classification = response.get("text", "").strip()
        
        if classification not in labels:
            self.logger.warning(f"Classification result '{classification}' not in provided labels")
            classification = labels[0]  # Default to first label if result is invalid
            
        self.logger.info(f"Successfully classified text as: {classification}")
        return classification

    def transcribe(self, audio_path: str, model: Optional[str] = None) -> str:
        """
        Converts speech from an audio file to text.
        Note: Mistral currently doesn't support direct audio transcription, so this is a placeholder.

        :param audio_path: Path to the audio file.
        :param model: Specific AI model to use.
        :return: Transcribed text.
        """
        self.logger.error("Audio transcription not supported by Mistral")
        raise NotImplementedError("Audio transcription is not supported by Mistral")

