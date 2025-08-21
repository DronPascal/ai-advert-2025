"""Base agent class for Multi-Agent System framework."""

import asyncio
import uuid
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

from .communication import Message, MessageBus


class AgentState(Enum):
    """Agent execution states."""
    IDLE = "idle"
    WORKING = "working"
    WAITING = "waiting"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class AgentCapability:
    """Definition of agent capability."""
    name: str
    description: str
    input_types: List[str]
    output_types: List[str]
    parameters: Dict[str, Any] = field(default_factory=dict)


class BaseAgent(ABC):
    """Base class for agents in Multi-Agent System.
    
    Inspired by LangGraph patterns and Goose architecture.
    """
    
    def __init__(
        self,
        agent_id: Optional[str] = None,
        name: Optional[str] = None,
        capabilities: Optional[List[AgentCapability]] = None
    ):
        self.agent_id = agent_id or str(uuid.uuid4())
        self.name = name or self.__class__.__name__
        self.capabilities = capabilities or []
        self.state = AgentState.IDLE
        self.message_bus: Optional[MessageBus] = None
        
        # Agent metadata
        self.metadata: Dict[str, Any] = {}
        
        # Message handlers
        self.message_handlers: Dict[str, Callable] = {}
        
        # Setup default handlers
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup default message handlers."""
        self.message_handlers.update({
            "execute": self._handle_execute,
            "status": self._handle_status,
            "stop": self._handle_stop,
            "reset": self._handle_reset
        })
    
    @abstractmethod
    async def execute(self, input_data: Any, **kwargs) -> Any:
        """Execute the agent's main functionality."""
        pass
    
    def get_capabilities(self) -> List[AgentCapability]:
        """Get agent capabilities."""
        return self.capabilities
    
    def can_handle(self, input_type: str) -> bool:
        """Check if agent can handle given input type."""
        return any(
            input_type in cap.input_types 
            for cap in self.capabilities
        )
    
    async def send_message(self, to_agent: str, message_type: str, content: Any) -> None:
        """Send message to another agent."""
        if not self.message_bus:
            raise RuntimeError("Message bus not connected")
        
        message = Message(
            id=str(uuid.uuid4()),
            from_agent=self.agent_id,
            to_agent=to_agent,
            message_type=message_type,
            content=content
        )
        
        await self.message_bus.send_message(message)
    
    async def broadcast_message(self, message_type: str, content: Any) -> None:
        """Broadcast message to all agents."""
        await self.send_message("*", message_type, content)
    
    async def handle_message(self, message: Message) -> Optional[Any]:
        """Handle incoming message."""
        handler = self.message_handlers.get(message.message_type)
        if handler:
            return await handler(message)
        else:
            return await self._handle_unknown_message(message)
    
    async def _handle_execute(self, message: Message) -> Any:
        """Handle execute message."""
        self.state = AgentState.WORKING
        try:
            result = await self.execute(message.content)
            self.state = AgentState.COMPLETED
            return result
        except Exception as e:
            self.state = AgentState.ERROR
            raise e
    
    async def _handle_status(self, message: Message) -> Dict[str, Any]:
        """Handle status request."""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "state": self.state.value,
            "capabilities": [cap.name for cap in self.capabilities],
            "metadata": self.metadata
        }
    
    async def _handle_stop(self, message: Message) -> None:
        """Handle stop message."""
        self.state = AgentState.IDLE
    
    async def _handle_reset(self, message: Message) -> None:
        """Handle reset message."""
        self.state = AgentState.IDLE
        self.metadata.clear()
    
    async def _handle_unknown_message(self, message: Message) -> None:
        """Handle unknown message types."""
        print(f"Agent {self.name} received unknown message type: {message.message_type}")
    
    def connect_message_bus(self, message_bus: MessageBus) -> None:
        """Connect to message bus."""
        self.message_bus = message_bus
        message_bus.register_agent(self)
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={self.agent_id}, name={self.name}, state={self.state.value})>"
