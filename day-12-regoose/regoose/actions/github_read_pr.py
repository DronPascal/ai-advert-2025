"""GitHub Read PR Action."""

from typing import List
from .base import BaseAction, ActionContext, ActionResult


class GitHubReadPRAction(BaseAction):
    """Action to read GitHub Pull Request data and changes."""
    
    def get_required_fields(self) -> List[str]:
        """Get required context fields."""
        return ["pr_number"]
    
    def validate_context(self, context: ActionContext) -> bool:
        """Validate context has required fields."""
        pr_number = context.get("pr_number")
        return pr_number is not None and isinstance(pr_number, int)
    
    async def execute(self, context: ActionContext) -> ActionResult:
        """Execute GitHub PR reading."""
        try:
            if not self.validate_context(context):
                return ActionResult.error_result("Missing or invalid 'pr_number' field")
            
            pr_number = context.get("pr_number")
            github_tool = self.tools.get("github")
            
            if not github_tool:
                return ActionResult.error_result("GitHub tool not available")
            
            # Get PR details
            pr_result = await github_tool.execute("get_pull_request", pr_number=pr_number)
            if not pr_result.success:
                return ActionResult.error_result(f"Failed to get PR details: {pr_result.output}")
            
            pr_data = github_tool.get_last_data()
            
            # Get PR files
            files_result = await github_tool.execute("get_pr_files", pr_number=pr_number)
            if not files_result.success:
                return ActionResult.error_result(f"Failed to get PR files: {files_result.output}")
            
            files_data = github_tool.get_last_data()
            
            # Filter only relevant files (code files, not images/binaries)
            code_files = []
            for file in files_data:
                if file.get("patch") and file.get("content"):  # Has changes and readable content
                    code_files.append({
                        "filename": file["filename"],
                        "status": file["status"],
                        "additions": file["additions"],
                        "deletions": file["deletions"],
                        "patch": file["patch"],
                        "content": file["content"]
                    })
            
            return ActionResult.success_result(
                data={
                    "pr_info": pr_data,
                    "files": code_files,
                    "total_files": len(files_data),
                    "code_files": len(code_files),
                    "total_additions": pr_data.get("additions", 0),
                    "total_deletions": pr_data.get("deletions", 0)
                }
            )
            
        except Exception as e:
            return ActionResult.error_result(f"GitHub PR reading failed: {str(e)}")
