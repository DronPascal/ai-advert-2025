"""Session management inspired by Goose architecture."""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class Message(BaseModel):
    """A message in the conversation."""
    role: str  # 'user', 'assistant', 'system'
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TestResult(BaseModel):
    """Result of test execution."""
    test_file: str
    passed: int
    failed: int
    errors: int
    duration: float
    details: List[Dict[str, Any]] = Field(default_factory=list)


class Session(BaseModel):
    """Session state tracking inspired by Goose."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    # Conversation history
    messages: List[Message] = Field(default_factory=list)
    
    # Code and test tracking
    original_code: Optional[str] = None
    generated_tests: Dict[str, str] = Field(default_factory=dict)  # filename -> content
    test_results: List[TestResult] = Field(default_factory=list)
    
    # Session metadata
    language: Optional[str] = None
    framework: Optional[str] = None
    container_id: Optional[str] = None
    
    def add_message(self, role: str, content: str, **metadata) -> None:
        """Add a message to the session."""
        message = Message(role=role, content=content, metadata=metadata)
        self.messages.append(message)
        self.updated_at = datetime.now()
    
    def add_test_result(self, result: TestResult) -> None:
        """Add test execution result."""
        self.test_results.append(result)
        self.updated_at = datetime.now()
    
    def get_conversation_context(self, max_messages: int = 10) -> str:
        """Get formatted conversation context for LLM."""
        recent_messages = self.messages[-max_messages:]
        context_parts = []
        
        for msg in recent_messages:
            context_parts.append(f"{msg.role.upper()}: {msg.content}")
        
        return "\n\n".join(context_parts)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary."""
        return self.dict()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Session":
        """Create session from dictionary."""
        return cls(**data)
