"""GitHub Analyze PR Action."""

import json
from typing import List, Dict, Any
from .base import BaseAction, ActionContext, ActionResult


class GitHubAnalyzePRAction(BaseAction):
    """Action to analyze GitHub PR changes using LLM."""
    
    def get_required_fields(self) -> List[str]:
        """Get required context fields."""
        return ["pr_info", "files"]
    
    def validate_context(self, context: ActionContext) -> bool:
        """Validate context has required fields."""
        return (
            context.get("pr_info") is not None and
            context.get("files") is not None
        )
    
    async def execute(self, context: ActionContext) -> ActionResult:
        """Execute PR analysis using LLM."""
        try:
            if not self.validate_context(context):
                return ActionResult.error_result("Missing required PR data")
            
            pr_info = context.get("pr_info")
            files = context.get("files")
            
            if not files:
                return ActionResult.success_result(
                    data={
                        "review_comments": [],
                        "overall_feedback": "No code changes to review.",
                        "score": 10,
                        "issues_found": 0
                    }
                )
            
            # Build analysis prompt
            analysis_prompt = self._build_analysis_prompt(pr_info, files)
            
            # Get LLM analysis
            messages = [
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": analysis_prompt}
            ]
            
            response = await self.llm.generate(messages)
            
            # Parse response
            review_data = self._parse_review_response(response.content)
            
            return ActionResult.success_result(
                data=review_data
            )
            
        except Exception as e:
            return ActionResult.error_result(f"PR analysis failed: {str(e)}")
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for PR review."""
        return """You are an expert code reviewer AI assistant. Your task is to analyze pull request changes and provide constructive feedback.

**Your responsibilities:**
1. Review code quality, logic, and best practices
2. Identify potential bugs, security issues, or performance problems
3. Suggest improvements for readability and maintainability
4. Check for proper error handling and edge cases
5. Ensure code follows language-specific conventions

**Output format:**
Respond with a JSON object containing:
```json
{
    "overall_feedback": "Brief summary of the PR quality",
    "score": 8,  // 1-10 rating
    "issues_found": 2,
    "review_comments": [
        {
            "filename": "path/to/file.py",
            "line_number": 42,
            "severity": "warning",  // "error", "warning", "suggestion"
            "category": "logic",    // "logic", "style", "performance", "security", "bug"
            "message": "Detailed feedback about this specific line/section",
            "suggestion": "Specific improvement recommendation"
        }
    ],
    "positive_points": [
        "Good test coverage",
        "Clear variable naming"
    ],
    "general_suggestions": [
        "Consider adding input validation",
        "Documentation could be improved"
    ]
}
```

**Review guidelines:**
- Be constructive and specific
- Focus on important issues, not nitpicks
- Suggest concrete improvements
- Consider the context and purpose of the PR
- Balance criticism with positive feedback"""
    
    def _build_analysis_prompt(self, pr_info: Dict[str, Any], files: List[Dict[str, Any]]) -> str:
        """Build analysis prompt with PR data."""
        prompt_parts = []
        
        # PR context
        prompt_parts.append("**Pull Request to Review:**")
        prompt_parts.append(f"**Title:** {pr_info.get('title', 'N/A')}")
        prompt_parts.append(f"**Description:** {pr_info.get('body', 'No description provided')}")
        prompt_parts.append(f"**Author:** {pr_info.get('user', 'Unknown')}")
        prompt_parts.append(f"**Changes:** +{pr_info.get('additions', 0)} -{pr_info.get('deletions', 0)} lines")
        prompt_parts.append("")
        
        # Files analysis
        prompt_parts.append("**Files Changed:**")
        for i, file in enumerate(files[:10]):  # Limit to first 10 files
            prompt_parts.append(f"\n**File {i+1}: {file['filename']}** ({file['status']})")
            prompt_parts.append(f"Changes: +{file['additions']} -{file['deletions']} lines")
            
            if file.get('patch'):
                prompt_parts.append("\n**Diff:**")
                prompt_parts.append("```diff")
                prompt_parts.append(file['patch'][:2000])  # Limit patch size
                if len(file['patch']) > 2000:
                    prompt_parts.append("... (truncated)")
                prompt_parts.append("```")
            
            if file.get('content'):
                prompt_parts.append("\n**Full File Content:**")
                prompt_parts.append("```")
                content = file['content'][:3000]  # Limit content size
                prompt_parts.append(content)
                if len(file['content']) > 3000:
                    prompt_parts.append("... (truncated)")
                prompt_parts.append("```")
            
            prompt_parts.append("")
        
        if len(files) > 10:
            prompt_parts.append(f"... and {len(files) - 10} more files")
        
        prompt_parts.append("\n**Please provide a comprehensive code review in the specified JSON format.**")
        
        return "\n".join(prompt_parts)
    
    def _parse_review_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response to extract review data."""
        try:
            # Try to extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_content = response[json_start:json_end]
                review_data = json.loads(json_content)
                
                # Validate required fields
                if not isinstance(review_data.get("review_comments"), list):
                    review_data["review_comments"] = []
                
                if not isinstance(review_data.get("score"), (int, float)):
                    review_data["score"] = 7  # Default score
                
                return review_data
            else:
                # Fallback: treat response as general feedback
                return {
                    "overall_feedback": response,
                    "score": 7,
                    "issues_found": 0,
                    "review_comments": [],
                    "positive_points": [],
                    "general_suggestions": []
                }
                
        except (json.JSONDecodeError, KeyError):
            # Fallback for malformed JSON
            return {
                "overall_feedback": response,
                "score": 7,
                "issues_found": 0,
                "review_comments": [],
                "positive_points": [],
                "general_suggestions": []
            }
