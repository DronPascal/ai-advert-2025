"""OpenAI provider implementation."""

import openai
from typing import List, Dict, Any
from .base import LLMProvider, LLMResponse


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider."""
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini", max_tokens: int = 4096):
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model
        self.max_tokens = max_tokens
    
    async def generate(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> LLMResponse:
        """Generate response from OpenAI."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=kwargs.get('max_tokens', self.max_tokens),
                temperature=kwargs.get('temperature', 0.1),
                **kwargs
            )
            
            return LLMResponse(
                content=response.choices[0].message.content,
                tokens_used=response.usage.total_tokens if response.usage else None,
                model=response.model,
                metadata={
                    "finish_reason": response.choices[0].finish_reason,
                    "created": response.created,
                    "id": response.id
                }
            )
        except Exception as e:
            raise RuntimeError(f"OpenAI API error: {str(e)}")
    
    def get_model_name(self) -> str:
        """Get the OpenAI model name."""
        return self.model
    
    def get_max_tokens(self) -> int:
        """Get maximum tokens for OpenAI."""
        return self.max_tokens
