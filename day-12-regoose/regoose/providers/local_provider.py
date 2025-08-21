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
        max_tokens: int = 4096
    ):
        self.endpoint = endpoint.rstrip("/")
        self.model = model
        self.max_tokens = max_tokens
        self.api_url = f"{self.endpoint}/api/chat"
    
    async def generate(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> LLMResponse:
        """Generate response from local LLM."""
        try:
            payload = {
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": {
                    "num_predict": kwargs.get('max_tokens', self.max_tokens),
                    "temperature": kwargs.get('temperature', 0.1),
                }
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
