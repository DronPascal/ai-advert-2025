"""Communication system for Multi-Agent System."""

import asyncio
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class Message:
    """Message between agents."""
    id: str
    from_agent: str
    to_agent: str  # "*" for broadcast
    message_type: str
    content: Any
    timestamp: datetime = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metadata is None:
            self.metadata = {}


class MessageBus:
    """Message bus for agent communication.
    
    Supports both direct messaging and pub/sub patterns.
    Inspired by LangGraph's message passing.
    """
    
    def __init__(self):
        self.agents: Dict[str, Any] = {}  # agent_id -> agent
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.subscribers: Dict[str, List[str]] = defaultdict(list)  # message_type -> [agent_ids]
        self.message_history: List[Message] = []
        self.running = False
        
        # Statistics
        self.stats = {
            "messages_sent": 0,
            "messages_delivered": 0,
            "errors": 0
        }
    
    def register_agent(self, agent) -> None:
        """Register an agent with the message bus."""
        self.agents[agent.agent_id] = agent
    
    def unregister_agent(self, agent_id: str) -> None:
        """Unregister an agent."""
        if agent_id in self.agents:
            del self.agents[agent_id]
    
    def subscribe(self, agent_id: str, message_type: str) -> None:
        """Subscribe agent to specific message type."""
        if message_type not in self.subscribers:
            self.subscribers[message_type] = []
        if agent_id not in self.subscribers[message_type]:
            self.subscribers[message_type].append(agent_id)
    
    def unsubscribe(self, agent_id: str, message_type: str) -> None:
        """Unsubscribe agent from message type."""
        if message_type in self.subscribers:
            if agent_id in self.subscribers[message_type]:
                self.subscribers[message_type].remove(agent_id)
    
    async def send_message(self, message: Message) -> None:
        """Send message through the bus."""
        await self.message_queue.put(message)
        self.stats["messages_sent"] += 1
    
    async def start(self) -> None:
        """Start the message bus."""
        self.running = True
        await self._process_messages()
    
    async def stop(self) -> None:
        """Stop the message bus."""
        self.running = False
    
    async def _process_messages(self) -> None:
        """Process messages from the queue."""
        while self.running:
            try:
                # Wait for message with timeout
                message = await asyncio.wait_for(
                    self.message_queue.get(),
                    timeout=1.0
                )
                
                await self._deliver_message(message)
                self.message_history.append(message)
                
            except asyncio.TimeoutError:
                # Continue processing
                continue
            except Exception as e:
                print(f"Error processing message: {e}")
                self.stats["errors"] += 1
    
    async def _deliver_message(self, message: Message) -> None:
        """Deliver message to target agent(s)."""
        if message.to_agent == "*":
            # Broadcast to all agents
            for agent_id, agent in self.agents.items():
                if agent_id != message.from_agent:  # Don't send to sender
                    try:
                        await agent.handle_message(message)
                        self.stats["messages_delivered"] += 1
                    except Exception as e:
                        print(f"Error delivering message to {agent_id}: {e}")
                        self.stats["errors"] += 1
        else:
            # Direct message
            if message.to_agent in self.agents:
                try:
                    agent = self.agents[message.to_agent]
                    await agent.handle_message(message)
                    self.stats["messages_delivered"] += 1
                except Exception as e:
                    print(f"Error delivering message to {message.to_agent}: {e}")
                    self.stats["errors"] += 1
            else:
                print(f"Agent {message.to_agent} not found")
                self.stats["errors"] += 1
        
        # Also deliver to subscribers
        subscribers = self.subscribers.get(message.message_type, [])
        for agent_id in subscribers:
            if agent_id in self.agents and agent_id != message.from_agent:
                try:
                    agent = self.agents[agent_id]
                    await agent.handle_message(message)
                    self.stats["messages_delivered"] += 1
                except Exception as e:
                    print(f"Error delivering to subscriber {agent_id}: {e}")
                    self.stats["errors"] += 1
    
    def get_message_history(
        self,
        agent_id: Optional[str] = None,
        message_type: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Message]:
        """Get message history with optional filtering."""
        messages = self.message_history
        
        if agent_id:
            messages = [
                msg for msg in messages
                if msg.from_agent == agent_id or msg.to_agent == agent_id
            ]
        
        if message_type:
            messages = [
                msg for msg in messages
                if msg.message_type == message_type
            ]
        
        if limit:
            messages = messages[-limit:]
        
        return messages
    
    def get_stats(self) -> Dict[str, Any]:
        """Get message bus statistics."""
        return {
            **self.stats,
            "registered_agents": len(self.agents),
            "message_history_size": len(self.message_history),
            "subscribers": dict(self.subscribers)
        }
