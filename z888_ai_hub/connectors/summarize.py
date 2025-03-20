"""
Summarize connector for text summarization using Anthropic Claude.
"""

from typing import Optional
from z888_ai_hub.connectors.anthropic import AnthropicConnector
from z888_ai_hub.connectors.base_connector import BaseConnector
from z888_ai_hub.utils.logging_utils import setup_logger


class SummarizeConnector(BaseConnector):
    """Connector for text summarization using Anthropic Claude."""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None, default_model: Optional[str] = None):
        """
        Initialize SummarizeConnector.
        
        Args:
            api_key: API key for Anthropic API
            base_url: Base URL for Anthropic API
            default_model: Default model to use
        """
        super().__init__(api_key, base_url, default_model)
        self.anthropic = AnthropicConnector(api_key, base_url, default_model)
        self.logger = setup_logger('SummarizeConnector')
        self.logger.info("Initialized Summarize connector")
    
    @property
    def name(self) -> str:
        """Get connector name."""
        return "summarize"
    
    async def call_api(self, payload: dict) -> dict:
        """
        Call Anthropic API for summarization.
        
        Args:
            payload: API request payload
            
        Returns:
            dict: API response
        """
        return await self.anthropic.call_api(payload)
    
    async def generate(self, prompt: str, model: Optional[str] = None) -> str:
        """
        Generate text using Anthropic Claude.
        
        Args:
            prompt: Input prompt
            model: Model to use
            
        Returns:
            str: Generated text
        """
        return await self.anthropic.generate(prompt, model)
    
    async def summarize(self, text: str, max_length: int = 280, model: Optional[str] = None) -> str:
        """
        Summarize text using Anthropic Claude.
        
        Args:
            text: Text to summarize
            max_length: Maximum length of summary
            model: Model to use
            
        Returns:
            str: Summarized text
        """
        return await self.anthropic.summarize(text, max_length, model)
    
    async def generate_summary(self, text: str) -> str:
        """
        Generate summary of text using Anthropic Claude.
        This method implements the ISummaryGenerator interface.
        
        Args:
            text: Text to summarize
            
        Returns:
            str: Generated summary
        """
        return await self.summarize(text, max_length=500)
    
    def classify(self, text: str, labels: list, model: Optional[str] = None) -> str:
        """
        Classify text using Anthropic Claude.
        
        Args:
            text: Text to classify
            labels: List of possible labels
            model: Model to use
            
        Returns:
            str: Predicted label
        """
        return self.anthropic.classify(text, labels, model)
    
    def extract_text(self, image_path: str, model: Optional[str] = None) -> str:
        """
        Extract text from image using Anthropic Claude.
        
        Args:
            image_path: Path to image file
            model: Model to use
            
        Returns:
            str: Extracted text
        """
        return self.anthropic.extract_text(image_path, model)
    
    def transcribe(self, audio_path: str, model: Optional[str] = None) -> str:
        """
        Transcribe audio using Anthropic Claude.
        
        Args:
            audio_path: Path to audio file
            model: Model to use
            
        Returns:
            str: Transcribed text
        """
        return self.anthropic.transcribe(audio_path, model) 