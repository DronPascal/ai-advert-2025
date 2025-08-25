"""OpenAI provider implementation."""

import openai
from typing import List, Dict, Any, Optional
from .base import LLMProvider, LLMResponse


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider."""
    
    def __init__(
        self, 
        api_key: str, 
        model: str = "gpt-4o-mini", 
        max_tokens: int = 4096,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        frequency_penalty: Optional[float] = None
    ):
        self.client = openai.OpenAI(api_key=api_key)
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
        """Generate response from OpenAI."""
        try:
            # Merge instance defaults with runtime kwargs
            params = {
                "model": self.model,
                "messages": messages,
                "max_tokens": kwargs.get('max_tokens', self.max_tokens),
                "temperature": kwargs.get('temperature', self.temperature or 0.1),
                "top_p": kwargs.get('top_p', self.top_p),
                "presence_penalty": kwargs.get('presence_penalty', self.presence_penalty),
                "frequency_penalty": kwargs.get('frequency_penalty', self.frequency_penalty)
            }
            
            # Filter out None values
            params = {k: v for k, v in params.items() if v is not None}
            
            # Add any other kwargs that aren't None
            for k, v in kwargs.items():
                if k not in params and v is not None:
                    params[k] = v
            
            response = self.client.chat.completions.create(**params)
            
            choice = response.choices[0]
            message = choice.message
            
            # Handle tool calls
            tool_calls = getattr(message, 'tool_calls', None)
            content = message.content or ""  # Handle None content when tool calls are present
            
            response_obj = LLMResponse(
                content=content,
                tokens_used=response.usage.total_tokens if response.usage else None,
                model=response.model,
                metadata={
                    "finish_reason": choice.finish_reason,
                    "created": response.created,
                    "id": response.id
                }
            )
            
            # Add tool calls to response if they exist
            if tool_calls:
                response_obj.tool_calls = tool_calls
                
            return response_obj
        except Exception as e:
            raise RuntimeError(f"OpenAI API error: {str(e)}")
    
    def get_model_name(self) -> str:
        """Get the OpenAI model name."""
        return self.model
    
    def get_max_tokens(self) -> int:
        """Get maximum tokens for OpenAI."""
        return self.max_tokens
