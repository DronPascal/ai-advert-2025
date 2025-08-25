"""DeepSeek provider implementation."""

import openai
from typing import List, Dict, Any, Optional
from .base import LLMProvider, LLMResponse


class DeepSeekProvider(LLMProvider):
    """DeepSeek LLM provider."""
    
    def __init__(
        self, 
        api_key: str, 
        model: str = "deepseek-chat", 
        max_tokens: int = 4096,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        frequency_penalty: Optional[float] = None
    ):
        # DeepSeek API is compatible with OpenAI API
        self.client = openai.OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.presence_penalty = presence_penalty
        self.frequency_penalty = frequency_penalty
    
    async def generate(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> LLMResponse:
        """Generate response from DeepSeek."""
        try:
            # Merge instance defaults with runtime kwargs
            params = {
                "model": self.model,
                "messages": messages,
                "max_tokens": kwargs.get('max_tokens', self.max_tokens),
                "temperature": kwargs.get('temperature', self.temperature or 0.1),
                "top_p": kwargs.get('top_p', self.top_p),
                "presence_penalty": kwargs.get('presence_penalty', self.presence_penalty),
                "frequency_penalty": kwargs.get('frequency_penalty', self.frequency_penalty),
                "stream": False
            }
            
            # Filter out None values
            params = {k: v for k, v in params.items() if v is not None}
            
            # Add any other kwargs that aren't None
            for k, v in kwargs.items():
                if k not in params and v is not None:
                    params[k] = v
            
            response = self.client.chat.completions.create(**params)
            
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
