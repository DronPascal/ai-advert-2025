"""Secure filesystem operations tool for code improvement scenarios."""

import os
import shutil
import ast
from pathlib import Path
from typing import Optional, List, Set
from .base import BaseTool, ToolResult
from ..core.logging import get_logger, timed_operation, metrics

logger = get_logger("secure_filesystem")


class SecurityError(Exception):
    """Security-related filesystem error."""
    pass


class SecureFilesystemTool(BaseTool):
    """Secure filesystem operations tool with sandboxing and validation."""
    
    def __init__(self, base_path: str, allowed_extensions: Optional[List[str]] = None, 
                 max_file_size: int = 1024 * 1024):  # 1MB default
        """Initialize secure filesystem tool.
        
        Args:
            base_path: Root directory for all operations (sandbox)
            allowed_extensions: Allowed file extensions
            max_file_size: Maximum file size in bytes
        """
        self.sandbox_root = Path(base_path).resolve()
        self.allowed_extensions = set(allowed_extensions or [
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.h', '.hpp',
            '.c', '.cs', '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.scala',
            '.md', '.txt', '.json', '.yaml', '.yml', '.toml', '.cfg', '.ini'
        ])
        self.max_file_size = max_file_size
        
        # Ensure sandbox exists
        self.sandbox_root.mkdir(parents=True, exist_ok=True)
        logger.info(f"Initialized secure filesystem with sandbox: {self.sandbox_root}")
    
    def get_name(self) -> str:
        return "secure_filesystem"
    
    def get_description(self) -> str:
        return "Secure filesystem operations with sandboxing and validation"
    
    def _validate_path(self, path: str) -> Path:
        """Validate path is within sandbox and safe to access."""
        try:
            # Convert to Path and resolve
            user_path = Path(path)
            if user_path.is_absolute():
                raise SecurityError(f"Absolute paths not allowed: {path}")
            
            # Resolve within sandbox
            full_path = (self.sandbox_root / user_path).resolve()
            
            # Check it's within sandbox
            if not str(full_path).startswith(str(self.sandbox_root)):
                raise SecurityError(f"Path outside sandbox: {path}")
            
            return full_path
            
        except Exception as e:
            raise SecurityError(f"Invalid path '{path}': {str(e)}")
    
    def _validate_file_extension(self, path: Path) -> bool:
        """Check if file extension is allowed."""
        if path.suffix.lower() not in self.allowed_extensions:
            return False
        return True
    
    def _validate_file_size(self, path: Path) -> bool:
        """Check if file size is within limits."""
        if path.exists() and path.stat().st_size > self.max_file_size:
            return False
        return True
    
    def _create_backup(self, path: Path) -> Optional[Path]:
        """Create backup of existing file."""
        if not path.exists():
            return None
        
        backup_path = path.with_suffix(path.suffix + '.backup')
        counter = 1
        while backup_path.exists():
            backup_path = path.with_suffix(f'{path.suffix}.backup.{counter}')
            counter += 1
        
        shutil.copy2(path, backup_path)
        logger.info(f"Created backup: {backup_path}")
        return backup_path
    
    @timed_operation("secure_read_file", "secure_filesystem")
    async def execute(self, operation: str, **kwargs) -> ToolResult:
        """Execute secure filesystem operation."""
        try:
            if operation == "read_file":
                return await self._read_file(kwargs.get("path"))
            elif operation == "write_file":
                return await self._write_file(kwargs.get("path"), kwargs.get("content"))
            elif operation == "list_directory":
                return await self._list_directory(kwargs.get("path", "."))
            elif operation == "analyze_directory":
                return await self._analyze_directory(kwargs.get("path", "."))
            elif operation == "backup_file":
                return await self._backup_file(kwargs.get("path"))
            elif operation == "get_file_tree":
                return await self._get_file_tree(kwargs.get("path", "."))
            elif operation == "validate_syntax":
                return await self._validate_syntax(kwargs.get("path"))
            else:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Unknown operation: {operation}"
                )
        except SecurityError as e:
            metrics.record_counter("secure_filesystem_security_violation")
            return ToolResult(success=False, output="", error=f"Security error: {str(e)}")
        except Exception as e:
            logger.error(f"Secure filesystem error: {e}", error=str(e))
            return ToolResult(success=False, output="", error=f"Filesystem error: {str(e)}")
    
    async def _read_file(self, path: str) -> ToolResult:
        """Read file content securely."""
        file_path = self._validate_path(path)
        
        if not file_path.exists():
            return ToolResult(success=False, output="", error=f"File not found: {path}")
        
        if not self._validate_file_extension(file_path):
            return ToolResult(success=False, output="", 
                            error=f"File extension not allowed: {file_path.suffix}")
        
        if not self._validate_file_size(file_path):
            return ToolResult(success=False, output="", 
                            error=f"File too large: {file_path.stat().st_size} bytes")
        
        try:
            content = file_path.read_text(encoding="utf-8")
            metrics.record_counter("secure_filesystem_read_success")
            
            return ToolResult(
                success=True,
                output=content,
                metadata={
                    "file_size": len(content),
                    "path": str(file_path.relative_to(self.sandbox_root)),
                    "extension": file_path.suffix
                }
            )
        except UnicodeDecodeError:
            return ToolResult(success=False, output="", error="File is not valid UTF-8 text")
    
    async def _write_file(self, path: str, content: str) -> ToolResult:
        """Write content to file securely."""
        file_path = self._validate_path(path)
        
        if not self._validate_file_extension(file_path):
            return ToolResult(success=False, output="", 
                            error=f"File extension not allowed: {file_path.suffix}")
        
        if len(content.encode('utf-8')) > self.max_file_size:
            return ToolResult(success=False, output="", 
                            error=f"Content too large: {len(content)} characters")
        
        try:
            # Create backup if file exists
            backup_path = None
            if file_path.exists():
                backup_path = self._create_backup(file_path)
            
            # Ensure parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            file_path.write_text(content, encoding="utf-8")
            metrics.record_counter("secure_filesystem_write_success")
            
            metadata = {
                "bytes_written": len(content.encode('utf-8')),
                "path": str(file_path.relative_to(self.sandbox_root))
            }
            if backup_path:
                metadata["backup_created"] = str(backup_path.relative_to(self.sandbox_root))
            
            return ToolResult(
                success=True,
                output=f"File written: {path}",
                metadata=metadata
            )
        except Exception as e:
            return ToolResult(success=False, output="", error=f"Write failed: {str(e)}")
    
    async def _list_directory(self, path: str) -> ToolResult:
        """List directory contents."""
        dir_path = self._validate_path(path)
        
        if not dir_path.exists():
            return ToolResult(success=False, output="", error=f"Directory not found: {path}")
        
        if not dir_path.is_dir():
            return ToolResult(success=False, output="", error=f"Not a directory: {path}")
        
        items = []
        for item in dir_path.iterdir():
            item_info = {
                "name": item.name,
                "type": "directory" if item.is_dir() else "file",
                "path": str(item.relative_to(self.sandbox_root))
            }
            
            if item.is_file():
                item_info.update({
                    "size": item.stat().st_size,
                    "extension": item.suffix,
                    "allowed": self._validate_file_extension(item)
                })
            
            items.append(item_info)
        
        output = "\n".join([
            f"{'📁' if item['type'] == 'directory' else '📄'} {item['name']}"
            for item in items
        ])
        
        return ToolResult(
            success=True,
            output=output,
            metadata={"items": items, "count": len(items)}
        )
    
    async def _analyze_directory(self, path: str) -> ToolResult:
        """Analyze directory structure and code files."""
        dir_path = self._validate_path(path)
        
        if not dir_path.exists() or not dir_path.is_dir():
            return ToolResult(success=False, output="", error=f"Invalid directory: {path}")
        
        analysis = {
            "total_files": 0,
            "code_files": 0,
            "languages": {},
            "file_tree": [],
            "large_files": [],
            "summary": ""
        }
        
        for item in dir_path.rglob("*"):
            if item.is_file():
                analysis["total_files"] += 1
                relative_path = item.relative_to(self.sandbox_root)
                
                if self._validate_file_extension(item):
                    analysis["code_files"] += 1
                    ext = item.suffix.lower()
                    analysis["languages"][ext] = analysis["languages"].get(ext, 0) + 1
                    
                    # Check for large files
                    if item.stat().st_size > self.max_file_size // 2:  # Half of max size
                        analysis["large_files"].append({
                            "path": str(relative_path),
                            "size": item.stat().st_size
                        })
                
                analysis["file_tree"].append({
                    "path": str(relative_path),
                    "type": "file",
                    "extension": item.suffix,
                    "size": item.stat().st_size
                })
        
        # Generate summary
        top_languages = sorted(analysis["languages"].items(), key=lambda x: x[1], reverse=True)[:3]
        lang_summary = ", ".join([f"{ext} ({count})" for ext, count in top_languages])
        
        analysis["summary"] = (
            f"Found {analysis['total_files']} total files, "
            f"{analysis['code_files']} code files. "
            f"Top languages: {lang_summary}"
        )
        
        return ToolResult(
            success=True,
            output=analysis["summary"],
            metadata=analysis
        )
    
    async def _get_file_tree(self, path: str) -> ToolResult:
        """Get hierarchical file tree structure."""
        dir_path = self._validate_path(path)
        
        if not dir_path.exists() or not dir_path.is_dir():
            return ToolResult(success=False, output="", error=f"Invalid directory: {path}")
        
        def build_tree(directory: Path, prefix: str = "") -> List[str]:
            """Build tree representation."""
            items = sorted(directory.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
            tree_lines = []
            
            for i, item in enumerate(items):
                is_last = i == len(items) - 1
                current_prefix = "└── " if is_last else "├── "
                
                if item.is_dir():
                    tree_lines.append(f"{prefix}{current_prefix}📁 {item.name}/")
                    extension = "    " if is_last else "│   "
                    tree_lines.extend(build_tree(item, prefix + extension))
                else:
                    allowed = "✅" if self._validate_file_extension(item) else "❌"
                    tree_lines.append(f"{prefix}{current_prefix}{allowed} {item.name}")
            
            return tree_lines
        
        tree_lines = [f"📁 {dir_path.name}/"]
        tree_lines.extend(build_tree(dir_path))
        
        output = "\n".join(tree_lines)
        
        return ToolResult(
            success=True,
            output=output,
            metadata={"tree_lines": tree_lines}
        )
    
    async def _validate_syntax(self, path: str) -> ToolResult:
        """Validate syntax of a code file."""
        file_path = self._validate_path(path)
        
        if not file_path.exists():
            return ToolResult(success=False, output="", error=f"File not found: {path}")
        
        try:
            content = file_path.read_text(encoding="utf-8")
            
            # Basic syntax validation for Python files
            if file_path.suffix == '.py':
                try:
                    ast.parse(content)
                    return ToolResult(
                        success=True,
                        output="✅ Python syntax is valid",
                        metadata={"language": "python", "valid": True}
                    )
                except SyntaxError as e:
                    return ToolResult(
                        success=False,
                        output=f"❌ Python syntax error: {e}",
                        metadata={"language": "python", "valid": False, "error": str(e)}
                    )
            else:
                # For other languages, just check if it's readable
                return ToolResult(
                    success=True,
                    output="✅ File is readable (syntax validation not available)",
                    metadata={"language": "unknown", "valid": True}
                )
                
        except Exception as e:
            return ToolResult(success=False, output="", error=f"Validation failed: {str(e)}")
    
    async def _backup_file(self, path: str) -> ToolResult:
        """Create backup of a file."""
        file_path = self._validate_path(path)
        
        if not file_path.exists():
            return ToolResult(success=False, output="", error=f"File not found: {path}")
        
        try:
            backup_path = self._create_backup(file_path)
            if backup_path:
                return ToolResult(
                    success=True,
                    output=f"Backup created: {backup_path.relative_to(self.sandbox_root)}",
                    metadata={"backup_path": str(backup_path.relative_to(self.sandbox_root))}
                )
            else:
                return ToolResult(success=False, output="", error="Failed to create backup")
        except Exception as e:
            return ToolResult(success=False, output="", error=f"Backup failed: {str(e)}")
