"""DeepSeek provider implementation."""

import openai
from typing import List, Dict, Any
from .base import LLMProvider, LLMResponse


class DeepSeekProvider(LLMProvider):
    """DeepSeek LLM provider."""
    
    def __init__(self, api_key: str, model: str = "deepseek-chat", max_tokens: int = 4096):
        # DeepSeek API is compatible with OpenAI API
        self.client = openai.OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )
        self.model = model
        self.max_tokens = max_tokens
    
    async def generate(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> LLMResponse:
        """Generate response from DeepSeek."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=kwargs.get('max_tokens', self.max_tokens),
                temperature=kwargs.get('temperature', 0.1),
                stream=False,
                **kwargs
            )
            
            return LLMResponse(
                content=response.choices[0].message.content,
                tokens_used=response.usage.total_tokens if response.usage else None,
                model=response.model,
                metadata={
                    "provider": "deepseek",
                    "finish_reason": response.choices[0].finish_reason,
                    "created": response.created,
                    "id": response.id
                }
            )
        except Exception as e:
            raise RuntimeError(f"DeepSeek API error: {str(e)}")
    
    def get_model_name(self) -> str:
        """Get the DeepSeek model name."""
        return self.model
    
    def get_max_tokens(self) -> int:
        """Get maximum tokens for DeepSeek."""
        return self.max_tokens
