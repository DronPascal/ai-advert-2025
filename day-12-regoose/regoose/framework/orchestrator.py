"""Agent orchestrator for Multi-Agent System coordination."""

import asyncio
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum

from .agent_base import BaseAgent
from .communication import MessageBus, Message


class OrchestrationStrategy(Enum):
    """Orchestration strategies."""
    SEQUENTIAL = "sequential"  # Execute agents one by one
    PARALLEL = "parallel"     # Execute agents in parallel
    PIPELINE = "pipeline"     # Chain agents in pipeline
    GRAPH = "graph"          # Execute based on dependency graph


@dataclass
class ExecutionPlan:
    """Execution plan for agents."""
    strategy: OrchestrationStrategy
    agents: List[str]  # agent IDs
    dependencies: Dict[str, List[str]] = None  # agent_id -> [dependency_agent_ids]
    parameters: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = {}
        if self.parameters is None:
            self.parameters = {}


class AgentOrchestrator:
    """Orchestrator for managing multiple agents.
    
    Inspired by LangGraph's graph execution and Goose's session management.
    """
    
    def __init__(self):
        self.message_bus = MessageBus()
        self.agents: Dict[str, BaseAgent] = {}
        self.execution_history: List[Dict[str, Any]] = []
        
        # Orchestration state
        self.current_plan: Optional[ExecutionPlan] = None
        self.running = False
    
    def register_agent(self, agent: BaseAgent) -> None:
        """Register an agent with the orchestrator."""
        self.agents[agent.agent_id] = agent
        agent.connect_message_bus(self.message_bus)
    
    def unregister_agent(self, agent_id: str) -> None:
        """Unregister an agent."""
        if agent_id in self.agents:
            del self.agents[agent_id]
            self.message_bus.unregister_agent(agent_id)
    
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Get agent by ID."""
        return self.agents.get(agent_id)
    
    def list_agents(self) -> List[BaseAgent]:
        """List all registered agents."""
        return list(self.agents.values())
    
    async def execute_plan(
        self,
        plan: ExecutionPlan,
        input_data: Any = None
    ) -> Dict[str, Any]:
        """Execute an execution plan."""
        self.current_plan = plan
        
        if plan.strategy == OrchestrationStrategy.SEQUENTIAL:
            return await self._execute_sequential(plan, input_data)
        elif plan.strategy == OrchestrationStrategy.PARALLEL:
            return await self._execute_parallel(plan, input_data)
        elif plan.strategy == OrchestrationStrategy.PIPELINE:
            return await self._execute_pipeline(plan, input_data)
        elif plan.strategy == OrchestrationStrategy.GRAPH:
            return await self._execute_graph(plan, input_data)
        else:
            raise ValueError(f"Unknown strategy: {plan.strategy}")
    
    async def _execute_sequential(
        self,
        plan: ExecutionPlan,
        input_data: Any
    ) -> Dict[str, Any]:
        """Execute agents sequentially."""
        results = {}
        current_data = input_data
        
        for agent_id in plan.agents:
            if agent_id not in self.agents:
                raise ValueError(f"Agent {agent_id} not found")
            
            agent = self.agents[agent_id]
            result = await agent.execute(current_data)
            results[agent_id] = result
            current_data = result  # Chain the output
        
        return results
    
    async def _execute_parallel(
        self,
        plan: ExecutionPlan,
        input_data: Any
    ) -> Dict[str, Any]:
        """Execute agents in parallel."""
        tasks = []
        
        for agent_id in plan.agents:
            if agent_id not in self.agents:
                raise ValueError(f"Agent {agent_id} not found")
            
            agent = self.agents[agent_id]
            task = asyncio.create_task(agent.execute(input_data))
            tasks.append((agent_id, task))
        
        results = {}
        for agent_id, task in tasks:
            results[agent_id] = await task
        
        return results
    
    async def _execute_pipeline(
        self,
        plan: ExecutionPlan,
        input_data: Any
    ) -> Dict[str, Any]:
        """Execute agents in pipeline (same as sequential for now)."""
        return await self._execute_sequential(plan, input_data)
    
    async def _execute_graph(
        self,
        plan: ExecutionPlan,
        input_data: Any
    ) -> Dict[str, Any]:
        """Execute agents based on dependency graph."""
        results = {}
        completed = set()
        
        # Topological sort to determine execution order
        execution_order = self._topological_sort(plan.agents, plan.dependencies)
        
        for agent_id in execution_order:
            if agent_id not in self.agents:
                raise ValueError(f"Agent {agent_id} not found")
            
            # Prepare input data from dependencies
            agent_input = input_data
            if agent_id in plan.dependencies:
                dependency_results = {
                    dep_id: results[dep_id]
                    for dep_id in plan.dependencies[agent_id]
                    if dep_id in results
                }
                agent_input = {
                    "original_input": input_data,
                    "dependency_results": dependency_results
                }
            
            agent = self.agents[agent_id]
            results[agent_id] = await agent.execute(agent_input)
            completed.add(agent_id)
        
        return results
    
    def _topological_sort(
        self,
        agents: List[str],
        dependencies: Dict[str, List[str]]
    ) -> List[str]:
        """Perform topological sort on agent dependencies."""
        # Simple topological sort implementation
        in_degree = {agent: 0 for agent in agents}
        
        # Calculate in-degrees
        for agent in agents:
            for dep in dependencies.get(agent, []):
                if dep in in_degree:
                    in_degree[agent] += 1
        
        # Start with agents that have no dependencies
        queue = [agent for agent, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            current = queue.pop(0)
            result.append(current)
            
            # Update in-degrees of dependent agents
            for agent in agents:
                if current in dependencies.get(agent, []):
                    in_degree[agent] -= 1
                    if in_degree[agent] == 0:
                        queue.append(agent)
        
        if len(result) != len(agents):
            raise ValueError("Circular dependency detected in agent graph")
        
        return result
    
    async def start(self) -> None:
        """Start the orchestrator."""
        self.running = True
        # Start message bus processing
        asyncio.create_task(self.message_bus.start())
    
    async def stop(self) -> None:
        """Stop the orchestrator."""
        self.running = False
        await self.message_bus.stop()
    
    def create_execution_plan(
        self,
        strategy: OrchestrationStrategy,
        agents: List[str],
        dependencies: Optional[Dict[str, List[str]]] = None
    ) -> ExecutionPlan:
        """Create an execution plan."""
        return ExecutionPlan(
            strategy=strategy,
            agents=agents,
            dependencies=dependencies or {}
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get orchestrator statistics."""
        return {
            "registered_agents": len(self.agents),
            "execution_history": len(self.execution_history),
            "message_bus_stats": self.message_bus.get_stats(),
            "current_plan": self.current_plan.strategy.value if self.current_plan else None
        }
