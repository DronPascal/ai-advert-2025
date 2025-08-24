"""
Regoose - AI Test Generation Agent

An AI-powered test generation agent with Action/Scenario architecture.
Automatically generates, runs, and validates tests for your code.
"""

__version__ = "0.2.0"
__author__ = "AI Assistant"

from .core.config import Settings
from .core.session import Session
from .core.orchestrator import ActionOrchestrator
from .scenarios.test_generation import TestGenerationScenario

__all__ = ["Settings", "Session", "ActionOrchestrator", "TestGenerationScenario"]
