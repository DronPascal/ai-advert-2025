"""GitHub integration tool using PyGithub."""

import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from github import Github, Repository, PullRequest
from github.GithubException import GithubException

from .base import BaseTool, ToolResult


@dataclass
class GitHubResult:
    """GitHub operation result with structured data."""
    success: bool
    data: Any = None
    error: str = None
    
    @property
    def output(self) -> str:
        """Convert to string for ToolResult compatibility."""
        if self.success:
            return f"Success: {type(self.data).__name__} data available"
        else:
            return f"Error: {self.error}"


class GitHubTool(BaseTool):
    """Tool for GitHub API operations."""
    
    def __init__(self, token: str, repo_owner: str, repo_name: str):
        self.github = Github(token)
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self._repo = None
    
    def get_name(self) -> str:
        """Get tool name."""
        return "github"
    
    def get_description(self) -> str:
        """Get tool description."""
        return f"GitHub API tool for repository {self.repo_owner}/{self.repo_name}"
    
    @property
    def repo(self) -> Repository.Repository:
        """Get repository instance."""
        if self._repo is None:
            self._repo = self.github.get_repo(f"{self.repo_owner}/{self.repo_name}")
        return self._repo
    
    async def execute(self, action: str, **kwargs) -> ToolResult:
        """Execute GitHub operation."""
        try:
            if action == "get_pull_request":
                result = await self._get_pull_request(kwargs.get("pr_number"))
            elif action == "get_pr_files":
                result = await self._get_pr_files(kwargs.get("pr_number"))
            elif action == "create_review_comment":
                result = await self._create_review_comment(
                    kwargs.get("pr_number"),
                    kwargs.get("body"),
                    kwargs.get("commit_sha"),
                    kwargs.get("path"),
                    kwargs.get("position")
                )
            elif action == "create_review":
                result = await self._create_review(
                    kwargs.get("pr_number"),
                    kwargs.get("body"),
                    kwargs.get("event", "COMMENT"),
                    kwargs.get("comments", [])
                )
            else:
                result = GitHubResult(success=False, error=f"Unknown action: {action}")
            
            # Store data in a way that actions can access it
            self._last_result = result
            return ToolResult(success=result.success, output=result.output)
            
        except GithubException as e:
            error_msg = f"GitHub API error: {e.data.get('message', str(e)) if hasattr(e, 'data') else str(e)}"
            self._last_result = GitHubResult(success=False, error=error_msg)
            return ToolResult(success=False, output=error_msg)
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            self._last_result = GitHubResult(success=False, error=error_msg)
            return ToolResult(success=False, output=error_msg)
    
    def get_last_data(self) -> Any:
        """Get the data from the last operation."""
        return getattr(self, '_last_result', GitHubResult(success=False, error="No data")).data
    
    async def _get_pull_request(self, pr_number: int) -> GitHubResult:
        """Get pull request details."""
        pr = self.repo.get_pull(pr_number)
        
        pr_data = {
            "number": pr.number,
            "title": pr.title,
            "body": pr.body,
            "state": pr.state,
            "head_sha": pr.head.sha,
            "base_sha": pr.base.sha,
            "user": pr.user.login,
            "created_at": pr.created_at.isoformat(),
            "updated_at": pr.updated_at.isoformat(),
            "additions": pr.additions,
            "deletions": pr.deletions,
            "changed_files": pr.changed_files
        }
        
        return GitHubResult(success=True, data=pr_data)
    
    async def _get_pr_files(self, pr_number: int) -> GitHubResult:
        """Get files changed in pull request."""
        pr = self.repo.get_pull(pr_number)
        files = []
        
        for file in pr.get_files():
            file_data = {
                "filename": file.filename,
                "status": file.status,
                "additions": file.additions,
                "deletions": file.deletions,
                "changes": file.changes,
                "blob_url": file.blob_url,
                "patch": file.patch,
                "contents_url": file.contents_url
            }
            
            # Get file content if it's a readable text file
            if file.status != "removed" and self._is_text_file(file.filename):
                try:
                    content = self.repo.get_contents(file.filename, ref=pr.head.sha)
                    if hasattr(content, 'decoded_content'):
                        file_data["content"] = content.decoded_content.decode('utf-8')
                except:
                    file_data["content"] = None
            
            files.append(file_data)
        
        return GitHubResult(success=True, data=files)
    
    async def _create_review_comment(
        self, 
        pr_number: int, 
        body: str, 
        commit_sha: str, 
        path: str, 
        position: int
    ) -> GitHubResult:
        """Create a review comment on specific line."""
        pr = self.repo.get_pull(pr_number)
        
        comment = pr.create_review_comment(
            body=body,
            commit=self.repo.get_commit(commit_sha),
            path=path,
            position=position
        )
        
        return GitHubResult(
            success=True,
            data={
                "id": comment.id,
                "body": comment.body,
                "path": comment.path,
                "position": comment.position,
                "created_at": comment.created_at.isoformat()
            }
        )
    
    async def _create_review(
        self,
        pr_number: int,
        body: str,
        event: str = "COMMENT",
        comments: List[Dict[str, Any]] = None
    ) -> GitHubResult:
        """Create a pull request review."""
        pr = self.repo.get_pull(pr_number)
        
        review_comments = []
        if comments:
            for comment in comments:
                review_comments.append({
                    "path": comment["path"],
                    "position": comment["position"],
                    "body": comment["body"]
                })
        
        review = pr.create_review(
            body=body,
            event=event,
            comments=review_comments
        )
        
        return GitHubResult(
            success=True,
            data={
                "id": review.id,
                "body": review.body,
                "state": review.state,
                "created_at": review.submitted_at.isoformat() if review.submitted_at else None
            }
        )
    
    def _is_text_file(self, filename: str) -> bool:
        """Check if file is likely a text file."""
        text_extensions = {
            '.py', '.js', '.ts', '.java', '.c', '.cpp', '.h', '.hpp',
            '.cs', '.go', '.rs', '.php', '.rb', '.swift', '.kt',
            '.html', '.css', '.scss', '.less', '.xml', '.json',
            '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf',
            '.md', '.txt', '.rst', '.tex', '.sql', '.sh', '.bash'
        }
        
        # Get file extension
        _, ext = os.path.splitext(filename.lower())
        return ext in text_extensions or filename.lower() in ['dockerfile', 'makefile', 'readme']
