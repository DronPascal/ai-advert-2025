"""Structured logging and observability system for Regoose."""

import logging
import json
import time
import uuid
import threading
from datetime import datetime
from typing import Dict, Any, Optional, List
from contextlib import contextmanager
from functools import wraps
from dataclasses import dataclass, asdict
from enum import Enum

# Thread-local storage for correlation ID
_local = threading.local()


class LogLevel(Enum):
    """Log levels for different components."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class MetricEvent:
    """Structured metric event."""
    name: str
    value: float
    unit: str
    labels: Dict[str, str]
    timestamp: float
    correlation_id: Optional[str] = None


@dataclass 
class LogEvent:
    """Structured log event."""
    level: str
    message: str
    component: str
    timestamp: float
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = None
    duration_ms: Optional[float] = None
    error: Optional[str] = None


class CorrelationContext:
    """Manages correlation IDs for request tracing."""
    
    @staticmethod
    def get_correlation_id() -> Optional[str]:
        """Get current correlation ID."""
        return getattr(_local, 'correlation_id', None)
    
    @staticmethod
    def set_correlation_id(correlation_id: str) -> None:
        """Set correlation ID for current thread."""
        _local.correlation_id = correlation_id
    
    @staticmethod
    def generate_correlation_id() -> str:
        """Generate new correlation ID."""
        return str(uuid.uuid4())
    
    @staticmethod
    @contextmanager
    def with_correlation_id(correlation_id: Optional[str] = None):
        """Context manager for correlation ID scope."""
        if correlation_id is None:
            correlation_id = CorrelationContext.generate_correlation_id()
        
        old_id = CorrelationContext.get_correlation_id()
        CorrelationContext.set_correlation_id(correlation_id)
        try:
            yield correlation_id
        finally:
            if old_id:
                CorrelationContext.set_correlation_id(old_id)
            else:
                _local.correlation_id = None


class StructuredLogger:
    """Structured logger with correlation ID support."""
    
    def __init__(self, component: str, level: LogLevel = LogLevel.INFO):
        self.component = component
        self.logger = logging.getLogger(f"regoose.{component}")
        self.logger.setLevel(getattr(logging, level.value))
        
        # Add JSON formatter if not already configured
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = JsonLogFormatter()
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def _log(self, level: str, message: str, **kwargs) -> None:
        """Internal logging method with structured format."""
        event = LogEvent(
            level=level,
            message=message,
            component=self.component,
            timestamp=time.time(),
            correlation_id=CorrelationContext.get_correlation_id(),
            metadata=kwargs.get('metadata', {}),
            duration_ms=kwargs.get('duration_ms'),
            error=kwargs.get('error')
        )
        
        log_level = getattr(logging, level)
        self.logger.log(log_level, json.dumps(asdict(event), default=str))
    
    def debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        self._log("DEBUG", message, **kwargs)
    
    def info(self, message: str, **kwargs) -> None:
        """Log info message."""
        self._log("INFO", message, **kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        self._log("WARNING", message, **kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        """Log error message."""
        self._log("ERROR", message, **kwargs)
    
    def critical(self, message: str, **kwargs) -> None:
        """Log critical message."""
        self._log("CRITICAL", message, **kwargs)


class JsonLogFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        try:
            # If already JSON, return as-is
            return record.getMessage()
        except:
            # Fallback to basic JSON structure
            return json.dumps({
                "level": record.levelname,
                "message": record.getMessage(),
                "timestamp": time.time(),
                "logger": record.name
            })


class MetricsCollector:
    """Collects and manages metrics for observability."""
    
    def __init__(self):
        self.metrics: List[MetricEvent] = []
        self.logger = StructuredLogger("metrics")
    
    def record_metric(
        self,
        name: str,
        value: float,
        unit: str = "count",
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a metric event."""
        event = MetricEvent(
            name=name,
            value=value,
            unit=unit,
            labels=labels or {},
            timestamp=time.time(),
            correlation_id=CorrelationContext.get_correlation_id()
        )
        
        self.metrics.append(event)
        self.logger.info(f"Metric recorded: {name}={value}{unit}", 
                        metadata={"metric": asdict(event)})
    
    def record_duration(self, name: str, duration_ms: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Record duration metric."""
        self.record_metric(f"{name}_duration", duration_ms, "ms", labels)
    
    def record_counter(self, name: str, labels: Optional[Dict[str, str]] = None) -> None:
        """Record counter increment."""
        self.record_metric(f"{name}_total", 1, "count", labels)
    
    def record_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Record gauge value."""
        self.record_metric(name, value, "gauge", labels)
    
    def get_metrics(self, since: Optional[float] = None) -> List[MetricEvent]:
        """Get metrics since timestamp."""
        if since is None:
            return self.metrics.copy()
        return [m for m in self.metrics if m.timestamp >= since]
    
    def clear_metrics(self) -> None:
        """Clear stored metrics."""
        self.metrics.clear()


# Global metrics collector instance
metrics = MetricsCollector()


def timed_operation(operation_name: Optional[str] = None, component: Optional[str] = None):
    """Decorator to measure operation duration."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            comp_name = component or func.__module__.split('.')[-1]
            
            logger = StructuredLogger(comp_name)
            logger.info(f"Starting operation: {op_name}")
            
            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                metrics.record_duration(op_name, duration_ms, {"status": "success"})
                metrics.record_counter(f"{op_name}_success")
                
                logger.info(f"Completed operation: {op_name}", 
                           duration_ms=duration_ms,
                           metadata={"status": "success"})
                
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                
                metrics.record_duration(op_name, duration_ms, {"status": "error"})
                metrics.record_counter(f"{op_name}_error")
                
                logger.error(f"Failed operation: {op_name}",
                           duration_ms=duration_ms,
                           error=str(e),
                           metadata={"status": "error", "error_type": type(e).__name__})
                
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            comp_name = component or func.__module__.split('.')[-1]
            
            logger = StructuredLogger(comp_name)
            logger.info(f"Starting operation: {op_name}")
            
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                metrics.record_duration(op_name, duration_ms, {"status": "success"})
                metrics.record_counter(f"{op_name}_success")
                
                logger.info(f"Completed operation: {op_name}",
                           duration_ms=duration_ms, 
                           metadata={"status": "success"})
                
                return result
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                
                metrics.record_duration(op_name, duration_ms, {"status": "error"})
                metrics.record_counter(f"{op_name}_error")
                
                logger.error(f"Failed operation: {op_name}",
                           duration_ms=duration_ms,
                           error=str(e),
                           metadata={"status": "error", "error_type": type(e).__name__})
                
                raise
        
        # Return appropriate wrapper based on function type
        if hasattr(func, '__code__') and func.__code__.co_flags & 0x80:  # CO_COROUTINE
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


@contextmanager
def operation_context(operation_name: str, component: str = "unknown"):
    """Context manager for tracking operations."""
    correlation_id = CorrelationContext.generate_correlation_id()
    with CorrelationContext.with_correlation_id(correlation_id):
        logger = StructuredLogger(component)
        start_time = time.time()
        
        logger.info(f"Starting operation context: {operation_name}")
        
        try:
            yield correlation_id
            duration_ms = (time.time() - start_time) * 1000
            metrics.record_duration(f"{operation_name}_context", duration_ms, {"status": "success"})
            logger.info(f"Completed operation context: {operation_name}", duration_ms=duration_ms)
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            metrics.record_duration(f"{operation_name}_context", duration_ms, {"status": "error"})
            logger.error(f"Failed operation context: {operation_name}", 
                        duration_ms=duration_ms, error=str(e))
            raise


class HealthChecker:
    """Health checking system for components."""
    
    def __init__(self):
        self.logger = StructuredLogger("health")
        self.checks: Dict[str, callable] = {}
    
    def register_health_check(self, name: str, check_func: callable) -> None:
        """Register a health check function."""
        self.checks[name] = check_func
        self.logger.info(f"Registered health check: {name}")
    
    async def check_health(self, check_name: Optional[str] = None) -> Dict[str, Any]:
        """Run health checks."""
        results = {}
        checks_to_run = {check_name: self.checks[check_name]} if check_name else self.checks
        
        for name, check_func in checks_to_run.items():
            try:
                start_time = time.time()
                if hasattr(check_func, '__call__'):
                    if hasattr(check_func, '__code__') and check_func.__code__.co_flags & 0x80:
                        result = await check_func()
                    else:
                        result = check_func()
                else:
                    result = {"status": "unknown", "message": "Invalid check function"}
                
                duration_ms = (time.time() - start_time) * 1000
                
                results[name] = {
                    "status": result.get("status", "unknown"),
                    "message": result.get("message", ""),
                    "duration_ms": duration_ms,
                    "timestamp": time.time()
                }
                
                metrics.record_duration(f"health_check_{name}", duration_ms)
                self.logger.debug(f"Health check completed: {name}", 
                                 metadata={"result": results[name]})
                
            except Exception as e:
                results[name] = {
                    "status": "error",
                    "message": str(e),
                    "timestamp": time.time()
                }
                self.logger.error(f"Health check failed: {name}", error=str(e))
        
        overall_status = "healthy" if all(r["status"] == "healthy" for r in results.values()) else "unhealthy"
        self.logger.info(f"Health check summary: {overall_status}", 
                        metadata={"results": results})
        
        return {
            "overall_status": overall_status,
            "checks": results,
            "timestamp": time.time()
        }


# Global health checker instance
health_checker = HealthChecker()


def setup_logging(level: LogLevel = LogLevel.INFO, components: Optional[List[str]] = None) -> None:
    """Setup structured logging for specified components."""
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, level.value),
        format='%(message)s',  # JSON formatter handles the format
        handlers=[]
    )
    
    # Disable other loggers to avoid duplication
    logging.getLogger('openai').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    logger = StructuredLogger("logging")
    logger.info("Structured logging initialized", 
               metadata={"level": level.value, "components": components})


# Convenience function to get logger for a component
def get_logger(component: str) -> StructuredLogger:
    """Get structured logger for component."""
    return StructuredLogger(component)
