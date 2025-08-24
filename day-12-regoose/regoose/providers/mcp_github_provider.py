"""MCP GitHub Provider for AI-powered PR reviews."""

import os
from typing import List, Dict, Any
from .mcp_provider import MCPProvider
from .factory import LLMProviderFactory


class MCPGitHubProvider(MCPProvider):
    """LLM Provider with GitHub MCP server integration."""
    
    def __init__(self, base_provider_type: str, settings):
        # Create base LLM provider
        base_provider = LLMProviderFactory.create_provider(base_provider_type, settings)
        
        # GitHub MCP server configuration
        mcp_command = "npx"
        mcp_args = ["@modelcontextprotocol/server-github"]
        
        # Ensure GitHub token is available in environment for MCP server
        if settings.github_token:
            # GitHub MCP server expects GITHUB_PERSONAL_ACCESS_TOKEN
            os.environ["GITHUB_PERSONAL_ACCESS_TOKEN"] = settings.github_token
            print(f"🔑 GitHub token configured for MCP server (length: {len(settings.github_token)})")
        else:
            print("⚠️ No GitHub token provided in settings")
        
        super().__init__(base_provider, mcp_command, mcp_args)
        self.settings = settings
    
    async def initialize(self) -> bool:
        """Initialize GitHub MCP provider."""
        success = await self.initialize_mcp()
        if success:
            print(f"✅ GitHub MCP initialized with {len(self.available_tools)} tools")
            for tool in self.available_tools:
                print(f"  - {tool.name}: {tool.description}")
        else:
            print("❌ Failed to initialize GitHub MCP")
        return success
    
    def get_github_tools_summary(self) -> str:
        """Get summary of available GitHub tools for prompt context."""
        if not self.available_tools:
            return "No GitHub MCP tools available"
        
        tools_info = []
        for tool in self.available_tools:
            tools_info.append(f"- {tool.name}: {tool.description}")
        
        return f"Available GitHub MCP tools:\n" + "\n".join(tools_info)
    
    async def analyze_pr_with_mcp(
        self,
        pr_number: int,
        repo_owner: str,
        repo_name: str,
        messages: List[Dict[str, str]],
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """Analyze PR using MCP tools."""
        
        # Enhanced system prompt with MCP context
        system_prompt = f"""You are an expert AI code reviewer with access to GitHub MCP tools.
        
Repository: {repo_owner}/{repo_name}
PR Number: {pr_number}

{self.get_github_tools_summary()}

Your task is to:
1. Use GitHub MCP tools to gather PR information and file changes
2. Analyze the code changes for quality, logic, style, performance, and security  
3. Provide constructive feedback with specific suggestions
{f"4. ANALYSIS ONLY: Do NOT publish review (dry-run mode)" if dry_run else "4. MANDATORY: MUST call create_pull_request_review_comment tool for EACH issue found"}

MANDATORY WORKFLOW:
1. CALL get_pull_request(owner="{repo_owner}", repo="{repo_name}", pull_number={pr_number})
2. CALL get_pull_request_files(owner="{repo_owner}", repo="{repo_name}", pull_number={pr_number})
3. Analyze the code changes
{"4. SKIP tool calls (dry-run mode)" if dry_run else f"4. For EACH issue found, CALL create_pull_request_review_comment with exact line position"}

CRITICAL: {f"Stop after analysis in dry-run mode" if dry_run else "You MUST call create_pull_request_review_comment for EACH issue to place comments directly in files"}!

Respond with a JSON object:
{{
    "overall_feedback": "Brief summary of the PR quality",
    "score": 8,  // 1-10 rating
    "issues_found": 2,
    "review_comments": [
        {{
            "filename": "path/to/file.py",
            "line_number": 42,
            "severity": "warning",  // "error", "warning", "suggestion"
            "category": "logic",    // "logic", "style", "performance", "security", "bug"
            "message": "Detailed feedback about this specific line/section",
            "suggestion": "Specific improvement recommendation"
        }}
    ],
    "positive_points": [
        "Good test coverage",
        "Clear variable naming"
    ],
    "general_suggestions": [
        "Consider adding input validation",
        "Documentation could be improved"
    ]
        }}

IMPORTANT: Use create_pull_request_review_comment tool for each issue to place comments directly in the code files, not in the general PR description."""
        
        # Create enhanced messages with system prompt
        enhanced_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Please analyze Pull Request #{pr_number} in {repo_owner}/{repo_name}. Use the GitHub MCP tools to gather all necessary information first, then provide a comprehensive code review."}
        ]
        
        # Generate with MCP tool support
        response = await self.generate(enhanced_messages)
        
        # If not dry-run, ensure we publish line-specific comments
        if not dry_run and response.content:
            try:
                # Try to extract review comments from AI response
                import json
                import re
                
                # Look for JSON in the response
                json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
                if json_match:
                    review_data = json.loads(json_match.group())
                    review_comments = review_data.get("review_comments", [])
                    
                    if review_comments:
                        print(f"📝 Creating {len(review_comments)} line-specific comments...")
                        
                        # Prepare comments for review
                        review_comments_data = []
                        for i, comment in enumerate(review_comments, 1):
                            filename = comment.get("filename", "")
                            line_number = comment.get("line_number", 1)
                            message = comment.get("message", "")
                            suggestion = comment.get("suggestion", "")
                            
                            # Combine message and suggestion
                            comment_body = f"AI Review Comment #{i}:\n\n{message}"
                            if suggestion:
                                comment_body += f"\n\n💡 Suggestion: {suggestion}"
                            
                            # Add comment data for review
                            review_comments_data.append({
                                "path": filename,
                                "line": line_number,
                                "body": comment_body
                            })
                        
                        # Create review with all line-specific comments
                        review_body = f"AI Code Review for PR #{pr_number}\n\nFound {len(review_comments)} issues that need attention."
                        
                        review_result = await self.call_mcp_tool("create_pull_request_review", {
                            "owner": repo_owner,
                            "repo": repo_name,
                            "pull_number": pr_number,
                            "body": review_body,
                            "event": "COMMENT",
                            "comments": review_comments_data
                        })
                        
                        if review_result.get("error"):
                            print(f"❌ Failed to create review with comments: {review_result['error']}")
                        else:
                            print(f"✅ Created review with {len(review_comments)} line-specific comments")
                            print(f"🚀 Review published: {review_result}")
                    else:
                        print("⚠️ No specific issues found for line comments")
                        
                else:
                    print("⚠️ Could not parse review data for line-specific comments")
                    
            except Exception as e:
                print(f"❌ Error creating line-specific comments: {e}")
                print("💡 Falling back to general review...")
                
                # Fallback: create general review
                review_body = f"AI Code Review for PR #{pr_number}\n\n{response.content}"
                publish_result = await self.call_mcp_tool("create_pull_request_review", {
                    "owner": repo_owner,
                    "repo": repo_name,
                    "pull_number": pr_number,
                    "body": review_body,
                    "event": "COMMENT"
                })
                
                if publish_result.get("error"):
                    print(f"❌ Failed to publish fallback review: {publish_result['error']}")
                elif publish_result:
                    print(f"🚀 Published fallback review: {publish_result}")
            
        return response
    
    def cleanup(self):
        """Cleanup with GitHub-specific cleanup."""
        super().cleanup()
        # Remove GitHub token from environment if we set it
        if "GITHUB_TOKEN" in os.environ and self.settings.github_token:
            # Only remove if we set it (basic check)
            if os.environ["GITHUB_TOKEN"] == self.settings.github_token:
                del os.environ["GITHUB_TOKEN"]
