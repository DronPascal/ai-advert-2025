"""MCP-based GitHub PR Review scenario."""

from typing import Dict, Any
from .base import BaseScenario, ScenarioResult
from ..core.orchestrator import ExecutionPlan


class MCPGitHubPRReviewScenario(BaseScenario):
    """Scenario for MCP-enabled GitHub Pull Request review."""
    
    async def execute(self, input_data: Dict[str, Any]) -> ScenarioResult:
        """Execute the MCP GitHub PR review scenario."""
        try:
            # Validate required input
            pr_number = input_data.get("pr_number")
            if not pr_number:
                return ScenarioResult.error_result("Missing 'pr_number' in input data")
            
            # Get repo info from input or orchestrator settings
            repo_owner = input_data.get("repo_owner")
            repo_name = input_data.get("repo_name")
            
            # If not provided, try to get from GitHub tool settings
            if not repo_owner or not repo_name:
                github_tool = self.orchestrator.tools.get("github")
                if github_tool:
                    repo_owner = repo_owner or github_tool.repo_owner
                    repo_name = repo_name or github_tool.repo_name
            
            if not repo_owner or not repo_name:
                return ScenarioResult.error_result("Missing repository information (repo_owner/repo_name)")
            
            # Add repo info to input data
            enriched_input = {
                **input_data,
                "repo_owner": repo_owner,
                "repo_name": repo_name
            }
            
            # Create execution plan for MCP PR review (single action)
            plan = ExecutionPlan.sequential([
                "mcp_pr_review"  # Single MCP-enabled action that does everything
            ])
            
            # Execute the plan
            context = await self.orchestrator.execute_plan(plan, enriched_input)
            
            return ScenarioResult.success_result(context)
            
        except Exception as e:
            return ScenarioResult.error_result(f"MCP GitHub PR review scenario failed: {str(e)}")
    
    async def execute_dry_run(self, input_data: Dict[str, Any]) -> ScenarioResult:
        """Execute MCP PR review without publishing (same as normal execution for MCP)."""
        # For MCP approach, the LLM itself decides what to do with GitHub
        # We'll add a flag to indicate it's a dry run
        dry_run_input = {**input_data, "dry_run": True}
        return await self.execute(dry_run_input)
