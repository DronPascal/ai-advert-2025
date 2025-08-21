"""Tests for the Regoose agent."""

import pytest
from unittest.mock import Mock, AsyncMock
from regoose.core.agent import RegooseAgent
from regoose.core.config import Settings
from regoose.providers.base import LLMProvider, LLMResponse


class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing."""
    
    def __init__(self):
        self.responses = []
    
    async def generate(self, messages, **kwargs):
        return LLMResponse(
            content='{"analysis": "Test analysis", "tests": {"test_example.py": "def test_example(): assert True"}}',
            tokens_used=100,
            model="mock-model"
        )
    
    def get_model_name(self):
        return "mock-model"
    
    def get_max_tokens(self):
        return 4096


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    return Settings(
        openai_api_key="test-key",
        openai_model="gpt-4o-mini",
        container_runtime="podman",
        container_image="python:3.11-slim"
    )


@pytest.fixture
def mock_llm():
    """Mock LLM provider."""
    return MockLLMProvider()


@pytest.fixture
def agent(mock_llm, mock_settings):
    """Regoose agent instance for testing."""
    return RegooseAgent(mock_llm, mock_settings)


def test_agent_initialization(agent):
    """Test agent initialization."""
    assert agent.llm is not None
    assert agent.settings is not None
    assert agent.filesystem is not None
    assert agent.shell is not None
    assert agent.container is not None


def test_create_session(agent):
    """Test session creation."""
    session = agent.create_session()
    assert session is not None
    assert session.id is not None
    assert agent.current_session == session


@pytest.mark.asyncio
async def test_analyze_and_generate_tests(agent):
    """Test code analysis and test generation."""
    code = "def fibonacci(n): return n if n <= 1 else fibonacci(n-1) + fibonacci(n-2)"
    
    tests, analysis = await agent.analyze_and_generate_tests(code)
    
    assert tests is not None
    assert analysis is not None
    assert len(tests) > 0
    assert "test_example.py" in tests


def test_parse_test_response(agent):
    """Test parsing of LLM responses."""
    response = '{"analysis": "Test analysis", "tests": {"test_file.py": "test content"}}'
    tests, analysis = agent._parse_test_response(response)
    
    assert analysis == "Test analysis"
    assert "test_file.py" in tests
    assert tests["test_file.py"] == "test content"


def test_parse_test_response_fallback(agent):
    """Test fallback parsing for malformed responses."""
    response = "Invalid JSON response with test content"
    tests, analysis = agent._parse_test_response(response)
    
    assert "test_generated.py" in tests
    assert tests["test_generated.py"] == response
