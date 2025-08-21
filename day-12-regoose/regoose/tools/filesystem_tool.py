"""Filesystem operations tool using MCP."""

import os
import asyncio
from pathlib import Path
from typing import Optional
from .base import BaseTool, ToolResult


class FilesystemTool(BaseTool):
    """Filesystem operations tool."""
    
    def __init__(self, base_path: Optional[str] = None):
        self.base_path = Path(base_path or os.getcwd())
    
    def get_name(self) -> str:
        return "filesystem"
    
    def get_description(self) -> str:
        return "Read and write files, create directories, list contents"
    
    async def execute(self, operation: str, **kwargs) -> ToolResult:
        """Execute filesystem operation."""
        try:
            if operation == "read_file":
                return await self._read_file(kwargs.get("path"))
            elif operation == "write_file":
                return await self._write_file(kwargs.get("path"), kwargs.get("content"))
            elif operation == "list_directory":
                return await self._list_directory(kwargs.get("path", "."))
            elif operation == "create_directory":
                return await self._create_directory(kwargs.get("path"))
            else:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Unknown operation: {operation}"
                )
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Filesystem error: {str(e)}"
            )
    
    async def _read_file(self, path: str) -> ToolResult:
        """Read file content."""
        file_path = self.base_path / path
        
        if not file_path.exists():
            return ToolResult(
                success=False,
                output="",
                error=f"File not found: {path}"
            )
        
        content = file_path.read_text(encoding="utf-8")
        return ToolResult(
            success=True,
            output=content,
            metadata={"file_size": len(content), "path": str(file_path)}
        )
    
    async def _write_file(self, path: str, content: str) -> ToolResult:
        """Write content to file."""
        file_path = self.base_path / path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_path.write_text(content, encoding="utf-8")
        
        return ToolResult(
            success=True,
            output=f"File written: {path}",
            metadata={"bytes_written": len(content), "path": str(file_path)}
        )
    
    async def _list_directory(self, path: str) -> ToolResult:
        """List directory contents."""
        dir_path = self.base_path / path
        
        if not dir_path.exists():
            return ToolResult(
                success=False,
                output="",
                error=f"Directory not found: {path}"
            )
        
        items = []
        for item in dir_path.iterdir():
            items.append({
                "name": item.name,
                "type": "directory" if item.is_dir() else "file",
                "size": item.stat().st_size if item.is_file() else None
            })
        
        output = "\n".join([f"{item['type']}: {item['name']}" for item in items])
        
        return ToolResult(
            success=True,
            output=output,
            metadata={"items": items, "count": len(items)}
        )
    
    async def _create_directory(self, path: str) -> ToolResult:
        """Create directory."""
        dir_path = self.base_path / path
        dir_path.mkdir(parents=True, exist_ok=True)
        
        return ToolResult(
            success=True,
            output=f"Directory created: {path}",
            metadata={"path": str(dir_path)}
        )
