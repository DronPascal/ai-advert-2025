"""Configuration management for Regoose."""

import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # OpenAI Configuration
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_model: str = Field("gpt-4o-mini", env="OPENAI_MODEL")
    openai_max_tokens: int = Field(4096, env="OPENAI_MAX_TOKENS")
    
    # Local LLM Configuration (optional)
    local_llm_endpoint: Optional[str] = Field(None, env="LOCAL_LLM_ENDPOINT")
    local_llm_model: Optional[str] = Field(None, env="LOCAL_LLM_MODEL")
    
    # Container Configuration
    container_runtime: str = Field("podman", env="CONTAINER_RUNTIME")
    container_image: str = Field("python:3.11-slim", env="CONTAINER_IMAGE")
    
    # MCP Configuration
    mcp_filesystem_server: str = Field("stdio://filesystem", env="MCP_FILESYSTEM_SERVER")
    mcp_shell_server: str = Field("stdio://shell", env="MCP_SHELL_SERVER")
    
    # Debug settings
    debug: bool = Field(False, env="DEBUG")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def get_settings() -> Settings:
    """Get application settings instance."""
    return Settings()
