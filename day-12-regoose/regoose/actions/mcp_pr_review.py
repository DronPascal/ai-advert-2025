"""MCP-based PR Review Action."""

import json
from typing import List, Dict, Any
from .base import BaseAction, ActionContext, ActionResult


class MCPPRReviewAction(BaseAction):
    """Action to review PR using MCP GitHub tools directly."""
    
    def get_required_fields(self) -> List[str]:
        """Get required context fields."""
        return ["pr_number", "repo_owner", "repo_name"]
    
    def validate_context(self, context: ActionContext) -> bool:
        """Validate context has required fields."""
        return (
            context.get("pr_number") is not None and
            context.get("repo_owner") is not None and
            context.get("repo_name") is not None
        )
    
    async def execute(self, context: ActionContext) -> ActionResult:
        """Execute MCP-based PR review."""
        try:
            if not self.validate_context(context):
                return ActionResult.error_result("Missing required fields: pr_number, repo_owner, repo_name")
            
            pr_number = context.get("pr_number")
            repo_owner = context.get("repo_owner")
            repo_name = context.get("repo_name")
            
            # Check if LLM provider supports MCP
            if not hasattr(self.llm, 'analyze_pr_with_mcp'):
                return ActionResult.error_result("LLM provider does not support MCP integration")
            
            # Use MCP-enabled analysis
            messages = []  # MCP provider will handle the messaging
            
            # Check for dry-run mode
            dry_run = context.get("dry_run", False)
            
            response = await self.llm.analyze_pr_with_mcp(
                pr_number=pr_number,
                repo_owner=repo_owner,
                repo_name=repo_name,
                messages=messages,
                dry_run=dry_run
            )
            
            # Parse response
            review_data = self._parse_mcp_response(response)
            
            return ActionResult.success_result(data=review_data)
            
        except Exception as e:
            return ActionResult.error_result(f"MCP PR review failed: {str(e)}")
    
    def _parse_mcp_response(self, response) -> Dict[str, Any]:
        """Parse MCP response to extract review data."""
        try:
            # Response should be LLMResponse object
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Try to extract JSON from response
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_content = content[json_start:json_end]
                review_data = json.loads(json_content)
                
                # Validate required fields
                if not isinstance(review_data.get("review_comments"), list):
                    review_data["review_comments"] = []
                
                if not isinstance(review_data.get("score"), (int, float)):
                    review_data["score"] = 7  # Default score
                
                # Add MCP metadata
                review_data["mcp_enabled"] = True
                review_data["review_method"] = "MCP GitHub Tools"
                
                return review_data
            else:
                # Fallback: treat response as general feedback
                return {
                    "overall_feedback": content,
                    "score": 7,
                    "issues_found": 0,
                    "review_comments": [],
                    "positive_points": [],
                    "general_suggestions": [],
                    "mcp_enabled": True,
                    "review_method": "MCP GitHub Tools"
                }
                
        except (json.JSONDecodeError, KeyError, AttributeError) as e:
            # Fallback for malformed response
            return {
                "overall_feedback": f"MCP review completed but response parsing failed: {str(e)}",
                "score": 5,
                "issues_found": 0,
                "review_comments": [],
                "positive_points": [],
                "general_suggestions": [],
                "mcp_enabled": True,
                "review_method": "MCP GitHub Tools (with parsing issues)"
            }
