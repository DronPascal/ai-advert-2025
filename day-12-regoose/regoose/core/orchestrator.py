"""Action orchestrator for coordinating scenario execution."""

import asyncio
from datetime import datetime
from typing import Dict, List, Any, Union
from pathlib import Path

from ..providers.base import LLMProvider
from .logging import get_logger, timed_operation, operation_context, CorrelationContext, metrics
from ..actions.base import BaseAction, ActionContext, ActionResult
from ..actions.analyze_code import AnalyzeCodeAction
from ..actions.generate_tests import GenerateTestsAction  
from ..actions.run_tests import RunTestsAction
from ..actions.generate_report import GenerateReportAction
from ..actions.github_read_pr import GitHubReadPRAction
from ..actions.github_analyze_pr import GitHubAnalyzePRAction
from ..actions.github_publish_review import GitHubPublishReviewAction
from ..actions.mcp_pr_review import MCPPRReviewAction
from ..actions.analyze_codebase import AnalyzeCodebaseAction
from ..actions.plan_improvements import PlanImprovementsAction
from ..actions.implement_changes import ImplementChangesAction
from ..actions.validate_changes import ValidateChangesAction


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
        self.logger = get_logger("orchestrator")
        self.context_class = ActionContext
    
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
            # Code improvement actions
            "analyze_codebase": AnalyzeCodebaseAction(self.llm_provider, self.tools),
            "plan_improvements": PlanImprovementsAction(self.llm_provider, self.tools),
            "implement_changes": ImplementChangesAction(self.llm_provider, self.tools),
            "validate_changes": ValidateChangesAction(self.llm_provider, self.tools)
        }
    
    @timed_operation("execute_plan", "orchestrator")
    async def execute_plan(self, plan: ExecutionPlan, initial_data: Dict[str, Any]) -> ActionContext:
        """Execute an action plan."""
        with operation_context("execute_plan", "orchestrator") as correlation_id:
            context = ActionContext(initial_data)
            context.set("timestamp", datetime.now().isoformat())
            context.set("correlation_id", correlation_id)
            
            self.logger.info(f"Starting plan execution with {len(plan.steps)} steps",
                           metadata={"plan_steps": plan.steps, "correlation_id": correlation_id})
            
            for i, step in enumerate(plan.steps):
                if isinstance(step, str):
                    self.logger.info(f"Executing step {i+1}/{len(plan.steps)}: {step}")
                    
                    result = await self._execute_action(step, context)
                    if not result.success:
                        self.logger.error(f"Action '{step}' failed: {result.error}",
                                        metadata={"step": i+1, "action": step})
                        metrics.record_counter("action_failure", {"action": step})
                        raise RuntimeError(f"Action '{step}' failed: {result.error}")
                    
                    # Update context with results
                    context.update(result.data)
                    context.add_artifacts(result.artifacts)
                    context.add_to_history(step, result)
                    
                    metrics.record_counter("action_success", {"action": step})
                    self.logger.info(f"Completed step {i+1}/{len(plan.steps)}: {step}")
            
            self.logger.info(f"Plan execution completed successfully",
                           metadata={"steps_completed": len(plan.steps)})
            metrics.record_counter("plan_success")
            
            return context
    
    @timed_operation("execute_action", "orchestrator")
    async def _execute_action(self, action_name: str, context: ActionContext) -> ActionResult:
        """Execute a single action."""
        if action_name not in self.actions:
            self.logger.error(f"Unknown action requested: {action_name}")
            return ActionResult.error_result(f"Unknown action: {action_name}")
        
        action = self.actions[action_name]
        
        # Validate dependencies (basic check)
        dependencies = action.get_dependencies()
        for dep in dependencies:
            if dep not in [h["action"] for h in context.history if h["success"]]:
                self.logger.error(f"Missing dependency for action {action_name}: {dep}")
                return ActionResult.error_result(f"Missing dependency: {dep}")
        
        # Execute action with logging
        self.logger.debug(f"Executing action: {action_name}",
                         metadata={"dependencies": dependencies})
        
        try:
            result = await action.execute(context)
            if result.success:
                self.logger.debug(f"Action {action_name} completed successfully")
            else:
                self.logger.warning(f"Action {action_name} failed: {result.error}")
            return result
        except Exception as e:
            self.logger.error(f"Action {action_name} raised exception: {str(e)}")
            return ActionResult.error_result(f"Action execution error: {str(e)}")
    
    def register_action(self, name: str, action: BaseAction) -> None:
        """Register a new action."""
        self.actions[name] = action
