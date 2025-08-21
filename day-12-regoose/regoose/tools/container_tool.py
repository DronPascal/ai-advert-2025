"""Container operations tool for Podman/Docker."""

import asyncio
import json
from typing import Optional, Dict, Any, List
from .base import BaseTool, ToolResult
from .shell_tool import ShellTool


class ContainerTool(BaseTool):
    """Container operations using Podman/Docker."""
    
    def __init__(self, runtime: str = "podman", base_image: str = "python:3.11-slim"):
        self.runtime = runtime
        self.base_image = base_image
        self.shell = ShellTool()
    
    def get_name(self) -> str:
        return "container"
    
    def get_description(self) -> str:
        return f"Manage {self.runtime} containers for isolated code execution"
    
    async def execute(self, operation: str, **kwargs) -> ToolResult:
        """Execute container operation."""
        try:
            if operation == "run":
                return await self._run_container(**kwargs)
            elif operation == "build":
                return await self._build_image(**kwargs)
            elif operation == "cleanup":
                return await self._cleanup_containers(**kwargs)
            elif operation == "list":
                return await self._list_containers()
            else:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Unknown container operation: {operation}"
                )
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Container error: {str(e)}"
            )
    
    async def _run_container(
        self,
        command: str,
        volumes: Optional[Dict[str, str]] = None,
        environment: Optional[Dict[str, str]] = None,
        working_dir: Optional[str] = None,
        image: Optional[str] = None,
        **kwargs
    ) -> ToolResult:
        """Run command in container."""
        container_image = image or self.base_image
        
        cmd_parts = [
            self.runtime, "run", "--rm",
            "--security-opt", "no-new-privileges",
            "--cap-drop", "ALL"
        ]
        
        # Add volumes
        if volumes:
            for host_path, container_path in volumes.items():
                cmd_parts.extend(["-v", f"{host_path}:{container_path}"])
        
        # Add environment variables
        if environment:
            for key, value in environment.items():
                cmd_parts.extend(["-e", f"{key}={value}"])
        
        # Add working directory
        if working_dir:
            cmd_parts.extend(["-w", working_dir])
        
        # Add image and command - let shell handle everything
        cmd_parts.extend([container_image, "bash", "-c", f"'{command}'"])
        
        full_command = " ".join(cmd_parts)
        
        return await self.shell.execute(
            command=full_command,
            timeout=kwargs.get("timeout", 60)
        )
    
    async def _build_image(
        self,
        dockerfile_content: str,
        tag: str,
        context_dir: str = "."
    ) -> ToolResult:
        """Build container image from Dockerfile."""
        # Write Dockerfile to temporary location
        dockerfile_path = f"{context_dir}/Dockerfile.regoose"
        
        # Create Dockerfile
        with open(dockerfile_path, "w") as f:
            f.write(dockerfile_content)
        
        try:
            command = f"{self.runtime} build -t {tag} -f {dockerfile_path} {context_dir}"
            result = await self.shell.execute(command, timeout=300)
            
            return result
        finally:
            # Cleanup temporary Dockerfile
            try:
                import os
                os.remove(dockerfile_path)
            except:
                pass
    
    async def _cleanup_containers(self, pattern: Optional[str] = None) -> ToolResult:
        """Cleanup stopped containers."""
        if pattern:
            command = f"{self.runtime} ps -a --filter 'name={pattern}' --format json"
        else:
            command = f"{self.runtime} ps -a --filter 'status=exited' --format json"
        
        list_result = await self.shell.execute(command)
        
        if not list_result.success:
            return list_result
        
        cleanup_commands = []
        if list_result.output.strip():
            # Parse container IDs and remove them
            lines = list_result.output.strip().split("\n")
            for line in lines:
                try:
                    container_info = json.loads(line)
                    container_id = container_info.get("Id", "")
                    if container_id:
                        cleanup_commands.append(f"{self.runtime} rm {container_id}")
                except json.JSONDecodeError:
                    continue
        
        if cleanup_commands:
            cleanup_command = " && ".join(cleanup_commands)
            return await self.shell.execute(cleanup_command)
        else:
            return ToolResult(
                success=True,
                output="No containers to cleanup",
                metadata={"cleaned": 0}
            )
    
    async def _list_containers(self) -> ToolResult:
        """List all containers."""
        command = f"{self.runtime} ps -a --format json"
        return await self.shell.execute(command)
