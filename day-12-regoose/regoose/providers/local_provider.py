"""Local LLM provider for Regoose (Ollama, etc)."""

import asyncio
import aiohttp
import json
from typing import List, Dict, Any, Optional
from .base import LLMProvider, LLMResponse


class LocalLLMProvider(LLMProvider):
    """Local LLM provider (Ollama, LM Studio, etc)."""
    
    def __init__(
        self,
        endpoint: str = "http://localhost:11434",
        model: str = "llama3.2",
        max_tokens: int = 4096,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        frequency_penalty: Optional[float] = None
    ):
        self.endpoint = endpoint.rstrip("/")
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.presence_penalty = presence_penalty
        self.frequency_penalty = frequency_penalty
        self.api_url = f"{self.endpoint}/api/chat"
    
    async def generate(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> LLMResponse:
        """Generate response from local LLM."""
        try:
            # Build Ollama options
            options = {
                "num_predict": kwargs.get('max_tokens', self.max_tokens),
                "temperature": kwargs.get('temperature', self.temperature or 0.1),
            }
            
            # Add Ollama-specific parameters if provided
            if kwargs.get('top_p', self.top_p) is not None:
                options["top_p"] = kwargs.get('top_p', self.top_p)
            if kwargs.get('presence_penalty', self.presence_penalty) is not None:
                options["presence_penalty"] = kwargs.get('presence_penalty', self.presence_penalty)
            if kwargs.get('frequency_penalty', self.frequency_penalty) is not None:
                options["frequency_penalty"] = kwargs.get('frequency_penalty', self.frequency_penalty)
            
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": options
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as response:
                    if response.status != 200:
                        raise RuntimeError(f"Local LLM API error: {response.status}")
                    
                    result = await response.json()
                    
                    content = result.get("message", {}).get("content", "")
                    
                    return LLMResponse(
                        content=content,
                        tokens_used=result.get("eval_count"),
                        model=self.model,
                        metadata={
                            "provider": "local",
                            "endpoint": self.endpoint,
                            "prompt_eval_count": result.get("prompt_eval_count"),
                            "eval_duration": result.get("eval_duration")
                        }
                    )
                    
        except aiohttp.ClientError as e:
            raise RuntimeError(f"Local LLM connection error: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Local LLM error: {str(e)}")
    
    def get_model_name(self) -> str:
        """Get the local model name."""
        return f"{self.model}@{self.endpoint}"
    
    def get_max_tokens(self) -> int:
        """Get maximum tokens for local LLM."""
        return self.max_tokens
    
    async def health_check(self) -> bool:
        """Check if local LLM is available."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.endpoint}/api/tags",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    return response.status == 200
        except:
            return False
