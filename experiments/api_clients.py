# experiments/api_clients.py
"""
API client wrappers for different LLM providers.
"""
from typing import Any, Optional, Tuple
from abc import ABC, abstractmethod
import os
from google import genai as google_genai
from mistralai import Mistral


class LLMClient(ABC):
    """Base class for LLM API clients."""
    
    @abstractmethod
    def call(self, prompt: str, model_name: str) -> Tuple[Any, bool]:
        """
        Call the LLM API.
        
        Returns:
            (raw_response, success_bool)
        """
        pass
    
    @abstractmethod
    def extract_text(self, response: Any) -> Optional[str]:
        """Extract text from API response."""
        pass


class GeminiClient(LLMClient):
    """Google Gemini API client."""
    
    def __init__(self, api_key: str):
        self.client = google_genai.Client(api_key=api_key)
    
    def call(self, prompt: str, model_name: str) -> Tuple[Any, bool]:
        try:
            response = self.client.models.generate_content(
                model=model_name,
                contents=prompt
            )
            return response, True
        except Exception:
            return None, False
    
    def extract_text(self, response: Any) -> Optional[str]:
        try:
            if hasattr(response, 'text'):
                return response.text
            elif hasattr(response, 'parts'):
                return "".join(part.text for part in response.parts if hasattr(part, 'text'))
            elif (hasattr(response, 'candidates') and response.candidates and 
                  response.candidates[0].content and response.candidates[0].content.parts):
                return response.candidates[0].content.parts[0].text
        except Exception:
            pass
        return None


class MistralClient(LLMClient):
    """Mistral API client."""
    
    def __init__(self, api_key: str):
        self.client = Mistral(api_key=api_key)
    
    def call(self, prompt: str, model_name: str) -> Tuple[Any, bool]:
        try:
            messages = [{"role": "user", "content": prompt}]
            response = self.client.chat.complete(
                model=model_name,
                messages=messages
            )
            return response, True
        except Exception:
            return None, False
    
    def extract_text(self, response: Any) -> Optional[str]:
        try:
            if response.choices:
                return response.choices[0].message.content
        except Exception:
            pass
        return None


class APIClientFactory:
    """Factory for creating API clients."""
    
    @staticmethod
    def create(model_family: str) -> Optional[LLMClient]:
        """Create appropriate API client based on model family."""
        if model_family.lower() == 'gemini':
            api_key = os.getenv("GOOGLE_API_KEY")
            if api_key:
                return GeminiClient(api_key)
        elif model_family.lower() == 'mistral':
            api_key = os.getenv("MISTRAL_API_KEY")
            if api_key:
                return MistralClient(api_key)
        return None

