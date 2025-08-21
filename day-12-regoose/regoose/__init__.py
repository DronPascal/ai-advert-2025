"""
Regoose - AI Test Generation Agent

An AI-powered test generation agent inspired by Goose architecture.
Automatically generates, runs, and validates tests for your code.
"""

__version__ = "0.1.0"
__author__ = "AI Assistant"

from .core.agent import RegooseAgent
from .core.config import Settings
from .core.session import Session

__all__ = ["RegooseAgent", "Settings", "Session"]
