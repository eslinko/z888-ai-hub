"""
Vectorize connector for text embeddings using edge function.
"""

import os
from typing import List, Optional
import numpy as np
from z888_ai_hub.processors.interfaces import IVectorizer
from z888_ai_hub.utils.env_loader import load_env
from z888_ai_hub.utils.logging_utils import setup_logger


class VectorizeConnector(IVectorizer):
    """Connector for text vectorization using edge function."""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize VectorizeConnector.
        
        Args:
            api_key: API key for edge function
            base_url: Base URL for edge function
        """
        self.api_key = api_key or load_env("SUPABASE_SERVICE_KEY")
        if not self.api_key:
            raise ValueError("SUPABASE_SERVICE_KEY not found in environment variables")
            
        self.base_url = base_url or "https://xhppqnkewoqhcglccgkq.supabase.co/functions/v1/victorize"
        self.logger = setup_logger('VectorizeConnector')
        self.logger.info(f"Initialized Vectorize connector with edge function at {self.base_url}")
        self.logger.debug(f"API Key length: {len(self.api_key)} characters")
    
    @property
    def name(self) -> str:
        """Get connector name."""
        return "vectorize"
    
    async def call_api(self, payload: dict) -> dict:
        """
        Call edge function for embeddings.
        
        Args:
            payload: API request payload
            
        Returns:
            dict: API response
        """
        try:
            import aiohttp
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            self.logger.debug(f"Preparing API call to {self.base_url}")
            self.logger.debug(f"Request payload: {payload}")
            self.logger.debug(f"Headers: {headers}")
            
            async with aiohttp.ClientSession() as session:
                self.logger.debug("Created aiohttp session")
                async with session.post(
                    self.base_url,
                    headers=headers,
                    json=payload
                ) as response:
                    self.logger.debug(f"Response status: {response.status}")
                    if response.status != 200:
                        error_text = await response.text()
                        self.logger.error(f"Edge function call failed with status {response.status}")
                        self.logger.error(f"Error response: {error_text}")
                        raise Exception(f"Edge function call failed: {error_text}")
                    
                    response_json = await response.json()
                    self.logger.debug(f"Response received: {response_json}")
                    return response_json
                    
        except aiohttp.ClientError as e:
            self.logger.error(f"Network error during API call: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during API call: {str(e)}")
            raise
    
    async def vectorize(self, text: str) -> List[float]:
        """
        Create vector embedding for text.
        
        Args:
            text: Text to vectorize
            
        Returns:
            List[float]: Vector embedding
        """
        try:
            self.logger.info(f"Starting vectorization for text of length {len(text)}")
            
            payload = {
                "text": text
            }
            
            response = await self.call_api(payload)
            
            if "embedding" not in response:
                self.logger.error(f"Unexpected response format: {response}")
                raise ValueError("Response missing 'embedding' field")
                
            embedding = response["embedding"]
            self.logger.info(f"Successfully created embedding, dimension: {len(embedding)}")
            return embedding
            
        except Exception as e:
            self.logger.error(f"Error creating embedding: {str(e)}")
            raise
    
    async def vectorize_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Create vector embeddings for multiple texts.
        
        Args:
            texts: List of texts to vectorize
            
        Returns:
            List[List[float]]: List of vector embeddings
        """
        try:
            self.logger.info(f"Starting batch vectorization for {len(texts)} texts")
            self.logger.debug(f"Text lengths: {[len(text) for text in texts]}")
            
            payload = {
                "texts": texts
            }
            
            response = await self.call_api(payload)
            
            if "embeddings" not in response:
                self.logger.error(f"Unexpected response format: {response}")
                raise ValueError("Response missing 'embeddings' field")
                
            embeddings = response["embeddings"]
            self.logger.info(f"Successfully created {len(embeddings)} embeddings")
            self.logger.debug(f"Embedding dimensions: {[len(emb) for emb in embeddings]}")
            return embeddings
            
        except Exception as e:
            self.logger.error(f"Error creating batch embeddings: {str(e)}")
            raise
    
    async def generate(self, prompt: str, model: Optional[str] = None) -> str:
        """Not implemented for vectorization connector."""
        raise NotImplementedError("Text generation not supported by vectorization connector")
    
    async def summarize(self, text: str, model: Optional[str] = None) -> str:
        """Not implemented for vectorization connector."""
        raise NotImplementedError("Text summarization not supported by vectorization connector") 