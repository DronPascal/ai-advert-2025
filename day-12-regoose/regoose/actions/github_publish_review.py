"""GitHub Publish Review Action."""

from typing import List, Dict, Any
from .base import BaseAction, ActionContext, ActionResult


class GitHubPublishReviewAction(BaseAction):
    """Action to publish review comments to GitHub PR."""
    
    def get_required_fields(self) -> List[str]:
        """Get required context fields."""
        return ["pr_info", "review_comments", "overall_feedback"]
    
    def validate_context(self, context: ActionContext) -> bool:
        """Validate context has required fields."""
        return (
            context.get("pr_info") is not None and
            context.get("review_comments") is not None and
            context.get("overall_feedback") is not None
        )
    
    async def execute(self, context: ActionContext) -> ActionResult:
        """Execute review publishing to GitHub."""
        try:
            if not self.validate_context(context):
                return ActionResult.error_result("Missing required review data")
            
            pr_info = context.get("pr_info")
            review_comments = context.get("review_comments", [])
            overall_feedback = context.get("overall_feedback")
            score = context.get("score", 7)
            positive_points = context.get("positive_points", [])
            general_suggestions = context.get("general_suggestions", [])
            
            github_tool = self.tools.get("github")
            if not github_tool:
                return ActionResult.error_result("GitHub tool not available")
            
            # Prepare review body
            review_body = self._build_review_body(
                overall_feedback, score, positive_points, general_suggestions, len(review_comments)
            )
            
            # Prepare line-specific comments for review
            line_comments = []
            for comment in review_comments:
                if self._validate_comment(comment):
                    # Find the position in diff for the comment
                    position = self._find_line_position(
                        comment.get("filename"), 
                        comment.get("line_number"),
                        context.get("files", [])
                    )
                    
                    if position is not None:
                        line_comments.append({
                            "path": comment["filename"],
                            "position": position,
                            "body": self._format_comment_body(comment)
                        })
            
            # Determine review event based on score and issues
            event = self._determine_review_event(score, len(review_comments))
            
            # Create review
            review_result = await github_tool.execute(
                "create_review",
                pr_number=pr_info["number"],
                body=review_body,
                event=event,
                comments=line_comments
            )
            
            if not review_result.success:
                return ActionResult.error_result(f"Failed to create review: {review_result.output}")
            
            review_data = github_tool.get_last_data()
            
            return ActionResult.success_result(
                data={
                    "review_id": review_data.get("id") if review_data else None,
                    "review_body": review_body,
                    "line_comments_count": len(line_comments),
                    "total_comments_attempted": len(review_comments),
                    "event": event,
                    "score": score
                }
            )
            
        except Exception as e:
            return ActionResult.error_result(f"Review publishing failed: {str(e)}")
    
    def _build_review_body(
        self, 
        overall_feedback: str, 
        score: int, 
        positive_points: List[str],
        general_suggestions: List[str],
        comment_count: int
    ) -> str:
        """Build the main review body."""
        
        # Score emoji
        score_emoji = "🟢" if score >= 8 else "🟡" if score >= 6 else "🔴"
        
        parts = [
            f"## 🤖 AI Code Review {score_emoji}",
            f"**Overall Score:** {score}/10",
            "",
            f"**Summary:** {overall_feedback}",
            ""
        ]
        
        if positive_points:
            parts.append("### ✅ Positive Points")
            for point in positive_points:
                parts.append(f"- {point}")
            parts.append("")
        
        if general_suggestions:
            parts.append("### 💡 General Suggestions")
            for suggestion in general_suggestions:
                parts.append(f"- {suggestion}")
            parts.append("")
        
        if comment_count > 0:
            parts.append(f"### 📝 Detailed Comments")
            parts.append(f"I've added {comment_count} specific line comments for your review.")
            parts.append("")
        
        parts.extend([
            "---",
            "*This review was generated by Regoose AI Assistant*"
        ])
        
        return "\n".join(parts)
    
    def _format_comment_body(self, comment: Dict[str, Any]) -> str:
        """Format individual comment body."""
        severity_emoji = {
            "error": "🚨",
            "warning": "⚠️", 
            "suggestion": "💡"
        }
        
        category_emoji = {
            "logic": "🧠",
            "style": "🎨",
            "performance": "⚡",
            "security": "🔒",
            "bug": "🐛"
        }
        
        severity = comment.get("severity", "suggestion")
        category = comment.get("category", "general")
        
        parts = [
            f"{severity_emoji.get(severity, '💬')} **{severity.upper()}** {category_emoji.get(category, '')} *{category}*",
            "",
            comment.get("message", "No message provided")
        ]
        
        if comment.get("suggestion"):
            parts.extend([
                "",
                "**Suggestion:**",
                comment["suggestion"]
            ])
        
        return "\n".join(parts)
    
    def _validate_comment(self, comment: Dict[str, Any]) -> bool:
        """Validate comment has required fields."""
        return (
            isinstance(comment, dict) and
            comment.get("filename") and
            comment.get("line_number") is not None and
            comment.get("message")
        )
    
    def _find_line_position(self, filename: str, line_number: int, files: List[Dict[str, Any]]) -> int:
        """Find the position in diff for a specific line."""
        for file in files:
            if file.get("filename") == filename and file.get("patch"):
                # Parse patch to find line position
                patch_lines = file["patch"].split('\n')
                position = 0
                current_line = 0
                
                for patch_line in patch_lines:
                    if patch_line.startswith('@@'):
                        # Parse hunk header to get starting line
                        try:
                            parts = patch_line.split(' ')
                            for part in parts:
                                if part.startswith('+'):
                                    current_line = int(part.split(',')[0][1:]) - 1
                                    break
                        except:
                            continue
                    elif patch_line.startswith('+'):
                        current_line += 1
                        position += 1
                        if current_line == line_number:
                            return position
                    elif patch_line.startswith('-'):
                        position += 1
                    elif patch_line.startswith(' '):
                        current_line += 1
                        position += 1
                    else:
                        position += 1
        
        return None  # Line not found in diff
    
    def _determine_review_event(self, score: int, issue_count: int) -> str:
        """Determine GitHub review event based on analysis."""
        if score >= 8 and issue_count == 0:
            return "APPROVE"
        elif score < 5 or issue_count > 5:
            return "REQUEST_CHANGES"
        else:
            return "COMMENT"
