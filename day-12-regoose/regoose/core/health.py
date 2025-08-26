"""Health checks for Regoose components."""

import asyncio
import subprocess
from typing import Dict, Any, Optional
from ..core.logging import get_logger, health_checker, StructuredLogger
from ..core.config import get_settings


class ComponentHealthChecks:
    """Health checks for system components."""
    
    def __init__(self):
        self.logger = get_logger("health")
        self.settings = get_settings()
        self._register_checks()
    
    def _register_checks(self) -> None:
        """Register all health checks."""
        health_checker.register_health_check("container_runtime", self.check_container_runtime)
        health_checker.register_health_check("openai_connectivity", self.check_openai_connectivity)
        health_checker.register_health_check("deepseek_connectivity", self.check_deepseek_connectivity)
        health_checker.register_health_check("github_connectivity", self.check_github_connectivity)
        health_checker.register_health_check("system_resources", self.check_system_resources)
    
    async def check_container_runtime(self) -> Dict[str, Any]:
        """Check if container runtime is available."""
        try:
            runtime = self.settings.container_runtime
            result = await asyncio.create_subprocess_exec(
                runtime, "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                version = stdout.decode().strip().split('\n')[0]
                return {
                    "status": "healthy",
                    "message": f"{runtime} is available: {version}",
                    "metadata": {"runtime": runtime, "version": version}
                }
            else:
                return {
                    "status": "unhealthy",
                    "message": f"{runtime} not available: {stderr.decode()}",
                    "metadata": {"runtime": runtime, "error": stderr.decode()}
                }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to check container runtime: {str(e)}",
                "metadata": {"runtime": self.settings.container_runtime}
            }
    
    async def check_openai_connectivity(self) -> Dict[str, Any]:
        """Check OpenAI API connectivity."""
        if not self.settings.openai_api_key:
            return {
                "status": "disabled",
                "message": "OpenAI API key not configured"
            }
        
        try:
            from ..providers.openai_provider import OpenAIProvider
            provider = OpenAIProvider(
                api_key=self.settings.openai_api_key,
                model=self.settings.openai_model
            )
            
            # Simple test request
            response = await provider.generate([
                {"role": "user", "content": "Hello"}
            ])
            
            return {
                "status": "healthy",
                "message": "OpenAI API is accessible",
                "metadata": {
                    "model": self.settings.openai_model,
                    "tokens_used": response.tokens_used
                }
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"OpenAI API connectivity failed: {str(e)}",
                "metadata": {"model": self.settings.openai_model}
            }
    
    async def check_deepseek_connectivity(self) -> Dict[str, Any]:
        """Check DeepSeek API connectivity."""
        if not self.settings.deepseek_api_key:
            return {
                "status": "disabled",
                "message": "DeepSeek API key not configured"
            }
        
        try:
            from ..providers.deepseek_provider import DeepSeekProvider
            provider = DeepSeekProvider(
                api_key=self.settings.deepseek_api_key,
                model=self.settings.deepseek_model
            )
            
            # Simple test request
            response = await provider.generate([
                {"role": "user", "content": "Hello"}
            ])
            
            return {
                "status": "healthy",
                "message": "DeepSeek API is accessible",
                "metadata": {
                    "model": self.settings.deepseek_model,
                    "tokens_used": response.tokens_used
                }
            }
        except Exception as e:
            return {
                "status": "unhealthy", 
                "message": f"DeepSeek API connectivity failed: {str(e)}",
                "metadata": {"model": self.settings.deepseek_model}
            }
    
    async def check_github_connectivity(self) -> Dict[str, Any]:
        """Check GitHub API connectivity."""
        if not self.settings.github_token:
            return {
                "status": "disabled",
                "message": "GitHub token not configured"
            }
        
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.github.com/user",
                    headers={"Authorization": f"token {self.settings.github_token}"}
                )
                
                if response.status_code == 200:
                    user_data = response.json()
                    return {
                        "status": "healthy",
                        "message": "GitHub API is accessible",
                        "metadata": {
                            "user": user_data.get("login"),
                            "rate_limit_remaining": response.headers.get("X-RateLimit-Remaining")
                        }
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "message": f"GitHub API error: {response.status_code}",
                        "metadata": {"status_code": response.status_code}
                    }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"GitHub API connectivity failed: {str(e)}"
            }
    
    async def check_system_resources(self) -> Dict[str, Any]:
        """Check system resource availability."""
        try:
            import psutil
            import shutil
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk usage
            disk = shutil.disk_usage("/")
            disk_percent = (disk.used / disk.total) * 100
            
            # Determine overall health
            status = "healthy"
            warnings = []
            
            if cpu_percent > 80:
                warnings.append(f"High CPU usage: {cpu_percent}%")
                status = "warning"
            
            if memory_percent > 85:
                warnings.append(f"High memory usage: {memory_percent}%")
                status = "warning"
            
            if disk_percent > 90:
                warnings.append(f"High disk usage: {disk_percent}%")
                status = "warning"
            
            message = "System resources are healthy"
            if warnings:
                message = f"System resources warning: {'; '.join(warnings)}"
            
            return {
                "status": status,
                "message": message,
                "metadata": {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory_percent,
                    "disk_percent": disk_percent,
                    "memory_available_gb": memory.available / (1024**3),
                    "disk_free_gb": disk.free / (1024**3)
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to check system resources: {str(e)}"
            }


# Global instance
component_health = ComponentHealthChecks()


async def run_health_checks() -> Dict[str, Any]:
    """Run all health checks and return results."""
    logger = get_logger("health")
    logger.info("Running system health checks")
    
    try:
        results = await health_checker.check_health()
        logger.info(f"Health check completed: {results['overall_status']}")
        return results
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "overall_status": "error",
            "checks": {},
            "error": str(e),
            "timestamp": asyncio.get_event_loop().time()
        }


async def run_single_health_check(check_name: str) -> Dict[str, Any]:
    """Run a single health check."""
    logger = get_logger("health")
    logger.info(f"Running health check: {check_name}")
    
    try:
        results = await health_checker.check_health(check_name)
        logger.info(f"Health check {check_name} completed")
        return results
    except Exception as e:
        logger.error(f"Health check {check_name} failed: {str(e)}")
        return {
            "overall_status": "error",
            "checks": {check_name: {"status": "error", "message": str(e)}},
            "timestamp": asyncio.get_event_loop().time()
        }
