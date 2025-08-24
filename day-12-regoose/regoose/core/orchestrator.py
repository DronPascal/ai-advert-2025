"""Action orchestrator for coordinating scenario execution."""

import asyncio
from datetime import datetime
from typing import Dict, List, Any, Union
from pathlib import Path

from ..providers.base import LLMProvider
from ..actions.base import BaseAction, ActionContext, ActionResult
from ..actions.analyze_code import AnalyzeCodeAction
from ..actions.generate_tests import GenerateTestsAction  
from ..actions.run_tests import RunTestsAction
from ..actions.generate_report import GenerateReportAction
from ..actions.github_read_pr import GitHubReadPRAction
from ..actions.github_analyze_pr import GitHubAnalyzePRAction
from ..actions.github_publish_review import GitHubPublishReviewAction
from ..actions.mcp_pr_review import MCPPRReviewAction


class ExecutionPlan:
    """Plan for executing actions."""
    
    def __init__(self, steps: List[str]):
        self.steps = steps
    
    @classmethod
    def sequential(cls, actions: List[str]) -> 'ExecutionPlan':
        """Create a sequential execution plan."""
        return cls(actions)


class ActionOrchestrator:
    """Orchestrator for executing action plans."""
    
    def __init__(self, llm_provider: LLMProvider, tools: Dict[str, Any]):
        self.llm_provider = llm_provider
        self.tools = tools
        self.actions = self._register_actions()
    
    def _register_actions(self) -> Dict[str, BaseAction]:
        """Register all available actions."""
        return {
            "analyze_code": AnalyzeCodeAction(self.llm_provider, self.tools),
            "generate_tests": GenerateTestsAction(self.llm_provider, self.tools),
            "run_tests": RunTestsAction(self.llm_provider, self.tools),
            "generate_report": GenerateReportAction(self.llm_provider, self.tools),
            "github_read_pr": GitHubReadPRAction(self.llm_provider, self.tools),
            "github_analyze_pr": GitHubAnalyzePRAction(self.llm_provider, self.tools),
            "github_publish_review": GitHubPublishReviewAction(self.llm_provider, self.tools),
            "mcp_pr_review": MCPPRReviewAction(self.llm_provider, self.tools),
        }
    
    async def execute_plan(self, plan: ExecutionPlan, initial_data: Dict[str, Any]) -> ActionContext:
        """Execute an action plan."""
        context = ActionContext(initial_data)
        context.set("timestamp", datetime.now().isoformat())
        
        for step in plan.steps:
            if isinstance(step, str):
                result = await self._execute_action(step, context)
                if not result.success:
                    raise RuntimeError(f"Action '{step}' failed: {result.error}")
                
                # Update context with results
                context.update(result.data)
                context.add_artifacts(result.artifacts)
                context.add_to_history(step, result)
        
        return context
    
    async def _execute_action(self, action_name: str, context: ActionContext) -> ActionResult:
        """Execute a single action."""
        if action_name not in self.actions:
            return ActionResult.error_result(f"Unknown action: {action_name}")
        
        action = self.actions[action_name]
        
        # Validate dependencies (basic check)
        dependencies = action.get_dependencies()
        for dep in dependencies:
            if dep not in [h["action"] for h in context.history if h["success"]]:
                return ActionResult.error_result(f"Missing dependency: {dep}")
        
        # Execute action
        return await action.execute(context)
    
    def register_action(self, name: str, action: BaseAction) -> None:
        """Register a new action."""
        self.actions[name] = action
