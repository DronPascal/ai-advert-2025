"""Shell command execution tool using MCP."""

import asyncio
import subprocess
from typing import Optional, Dict, Any
from .base import BaseTool, ToolResult


class ShellTool(BaseTool):
    """Shell command execution tool."""
    
    def __init__(self, working_directory: Optional[str] = None):
        self.working_directory = working_directory
    
    def get_name(self) -> str:
        return "shell"
    
    def get_description(self) -> str:
        return "Execute shell commands and capture output"
    
    async def execute(self, command: str, **kwargs) -> ToolResult:
        """Execute shell command."""
        try:
            timeout = kwargs.get("timeout", 30)
            capture_output = kwargs.get("capture_output", True)
            check = kwargs.get("check", False)
            
            result = await self._run_command(
                command=command,
                timeout=timeout,
                capture_output=capture_output,
                check=check
            )
            
            return result
            
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Shell execution error: {str(e)}"
            )
    
    async def _run_command(
        self,
        command: str,
        timeout: int = 30,
        capture_output: bool = True,
        check: bool = False
    ) -> ToolResult:
        """Run shell command asynchronously."""
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                cwd=self.working_directory,
                stdout=asyncio.subprocess.PIPE if capture_output else None,
                stderr=asyncio.subprocess.PIPE if capture_output else None,
                shell=True
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )
            
            stdout_text = stdout.decode("utf-8") if stdout else ""
            stderr_text = stderr.decode("utf-8") if stderr else ""
            
            success = process.returncode == 0
            
            if check and not success:
                raise subprocess.CalledProcessError(
                    process.returncode, command, stdout_text, stderr_text
                )
            
            output = stdout_text
            if stderr_text:
                output += f"\n--- STDERR ---\n{stderr_text}"
            
            return ToolResult(
                success=success,
                output=output,
                error=stderr_text,
                metadata={
                    "command": command,
                    "return_code": process.returncode,
                    "timeout": timeout
                }
            )
            
        except asyncio.TimeoutError:
            return ToolResult(
                success=False,
                output="",
                error=f"Command timed out after {timeout} seconds: {command}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Command execution failed: {str(e)}"
            )
