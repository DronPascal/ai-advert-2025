"""GitHub PR Review scenario."""

from typing import Dict, Any
from .base import BaseScenario, ScenarioResult
from ..core.orchestrator import ExecutionPlan


class GitHubPRReviewScenario(BaseScenario):
    """Scenario for comprehensive GitHub Pull Request review."""
    
    async def execute(self, input_data: Dict[str, Any]) -> ScenarioResult:
        """Execute the GitHub PR review scenario."""
        try:
            # Validate required input
            pr_number = input_data.get("pr_number")
            if not pr_number:
                return ScenarioResult.error_result("Missing 'pr_number' in input data")
            
            # Create execution plan for PR review
            plan = ExecutionPlan.sequential([
                "github_read_pr",       # Read PR data and files
                "github_analyze_pr",    # Analyze changes with LLM
                "github_publish_review" # Publish review to GitHub
            ])
            
            # Execute the plan
            context = await self.orchestrator.execute_plan(plan, input_data)
            
            return ScenarioResult.success_result(context)
            
        except Exception as e:
            return ScenarioResult.error_result(f"GitHub PR review scenario failed: {str(e)}")
    
    async def execute_dry_run(self, input_data: Dict[str, Any]) -> ScenarioResult:
        """Execute PR review without publishing (dry run)."""
        try:
            # Validate required input
            pr_number = input_data.get("pr_number")
            if not pr_number:
                return ScenarioResult.error_result("Missing 'pr_number' in input data")
            
            # Create dry run execution plan (without publishing)
            plan = ExecutionPlan.sequential([
                "github_read_pr",       # Read PR data and files
                "github_analyze_pr"     # Analyze changes with LLM only
            ])
            
            # Execute the plan
            context = await self.orchestrator.execute_plan(plan, input_data)
            
            return ScenarioResult.success_result(context)
            
        except Exception as e:
            return ScenarioResult.error_result(f"GitHub PR review dry run failed: {str(e)}")
