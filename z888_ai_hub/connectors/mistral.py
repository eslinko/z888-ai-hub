import os
import json
import asyncio
import aiohttp
from mistralai import Mistral
from typing import Any, Dict, Optional, List
from z888_ai_hub.connectors.base_connector import (
    BaseConnector,
    ConnectorCapability,
    ConnectorConfig,
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
        self.client = Mistral(api_key=self.api_key)
        self.logger = setup_logger('MistralConnector', log_to_file=True)
        self.logger.info(f"Initialized Mistral connector with model: {default_model}")
        
        # Устанавливаем поддерживаемые возможности
        self._capabilities = [
            ConnectorCapability.SUMMARY,
            ConnectorCapability.TEXT_GENERATION,
            ConnectorCapability.CLASSIFICATION,
            ConnectorCapability.OCR
        ]

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
        if not config.api_key or not config.api_key.startswith("mistral-"):
            self.logger.error("Invalid Mistral API key format")
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

    async def call_api(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Makes a request to the Mistral API.

        :param payload: Dictionary with request parameters.
        :return: API response as a dictionary.
        """
        try:
            self.logger.debug(f"Making API call to Mistral with model: {payload.get('model')}")
            response = await self.client.chat.completions.create(
                model=payload["model"],
                messages=payload["messages"],
                temperature=payload.get("temperature", 0.0),
                stream=False
            )
            self.logger.debug("Successfully received response from Mistral API")
            return {"text": response.choices[0].message.content}
        except Exception as e:
            error_msg = f"Mistral API Error: {e}"
            self.logger.error(error_msg, exc_info=True)
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

    async def upload_pdf_to_mistral(self, file_path: str) -> Optional[str]:
        """
        Uploads a PDF file to Mistral and returns the signed URL for OCR processing.

        :param file_path: Path to the PDF file to upload.
        :return: Signed URL to access the uploaded document.
        """
        UPLOAD_URL = "https://api.mistral.ai/v1/files"
        SIGNED_URL_ENDPOINT = "https://api.mistral.ai/v1/files/{file_id}/url"
        
        if not os.path.exists(file_path):
            self.logger.error(f"File not found: {file_path}")
            return None

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}"
            }

            # Upload file
            self.logger.debug(f"Uploading file to {UPLOAD_URL}")
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

                async with session.post(UPLOAD_URL, data=form, headers=headers) as response:
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
                    signed_url_endpoint = SIGNED_URL_ENDPOINT.format(file_id=file_id)
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

    async def extract_text(self, file_path: str, model: Optional[str] = None) -> str:
        """
        Извлекает текст из файла используя Mistral OCR.
        
        :param file_path: Путь к файлу
        :param model: AI модель для использования (по умолчанию mistral-ocr-latest)
        :return: Извлеченный текст
        """
        async def progress_indicator():
            seconds = 0
            while True:
                seconds += 1
                print(f"Обработка... прошло {seconds} секунд", flush=True)
                await asyncio.sleep(1)

        try:
            # Создаем и запускаем индикатор прогресса
            progress_task = asyncio.create_task(progress_indicator())
            
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Файл не найден: {file_path}")
            
            model = model or "mistral-ocr-latest"
            self.logger.info(f"Начинаю OCR обработку файла: {file_path} с моделью {model}")
            
            # Загружаем файл и получаем signed URL
            self.logger.info("Шаг 1: Загрузка файла и получение signed URL...")
            signed_url = await self.upload_pdf_to_mistral(file_path)
            if not signed_url:
                raise Exception("Не удалось загрузить файл и получить signed URL")
            self.logger.info(f"Получен signed URL: {signed_url[:100]}...")
            
            # Подготавливаем payload для OCR запроса
            self.logger.info("Шаг 2: Подготовка OCR запроса...")
            payload = {
                "model": model,
                "document": {
                    "type": "document_url",
                    "document_url": signed_url,
                    "document_name": os.path.basename(file_path)
                },
                "pages": None,
                "include_image_base64": False,
                "image_limit": None,
                "image_min_size": None
            }
            self.logger.debug(f"Подготовлен payload для OCR: {json.dumps(payload, indent=2)}")

            # Выполняем OCR запрос
            self.logger.info("Шаг 3: Отправка OCR запроса...")
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/v1/ocr",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json=payload
                ) as response:
                    response_json = await response.json()
                    self.logger.debug(f"Получен ответ от OCR API: {json.dumps(response_json, indent=2)}")
                    
                    if response.status != 200:
                        raise Exception(f"Ошибка OCR API: {response_json.get('detail', 'Unknown error')}")
                    
                    # Извлекаем текст из всех страниц
                    self.logger.info("Шаг 4: Обработка результатов OCR...")
                    pages = response_json.get("pages", [])
                    extracted_text = ""
                    
                    for i, page in enumerate(pages, 1):
                        page_text = page.get("text", "")
                        extracted_text += f"Страница {i}:\n{page_text}\n\n"
                    
                    self.logger.info(f"Успешно извлечен текст из {len(pages)} страниц")
                    return extracted_text.strip()
                    
        except Exception as e:
            self.logger.error(f"Ошибка при OCR обработке: {str(e)}", exc_info=True)
            raise
        finally:
            # Отменяем индикатор прогресса
            if 'progress_task' in locals():
                progress_task.cancel()

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

