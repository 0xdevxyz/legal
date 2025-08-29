"""
Complyo Comprehensive Monitoring & Logging System
Advanced monitoring, structured logging, and security event tracking
"""

import logging
import sys
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from contextlib import asynccontextmanager
from dataclasses import dataclass, asdict
import traceback
from pathlib import Path
import asyncio
from enum import Enum

from config import settings

class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class SecurityEventType(Enum):
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    INVALID_TOKEN = "invalid_token"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    DATA_BREACH_ATTEMPT = "data_breach_attempt"

@dataclass
class SecurityEvent:
    """Security event for monitoring and alerting"""
    event_type: SecurityEventType
    user_id: Optional[str]
    ip_address: str
    user_agent: str
    endpoint: str
    details: Dict[str, Any]
    timestamp: datetime
    severity: str = "medium"

@dataclass
class PerformanceMetric:
    """Performance tracking metric"""
    metric_name: str
    value: float
    unit: str
    tags: Dict[str, str]
    timestamp: datetime

class StructuredLogger:
    """
    Structured logging with JSON output and security event tracking
    """
    
    def __init__(self):
        self.setup_logging()
        self.security_events: List[SecurityEvent] = []
        self.performance_metrics: List[PerformanceMetric] = []
        
    def setup_logging(self):
        """
        Configure structured logging with multiple handlers
        """
        # Create custom logger
        self.logger = logging.getLogger("complyo")
        self.logger.setLevel(getattr(logging, settings.log_level))
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # JSON Formatter for structured logs
        class JSONFormatter(logging.Formatter):
            def format(self, record):
                log_entry = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "level": record.levelname,
                    "logger": record.name,
                    "message": record.getMessage(),
                    "module": record.module,
                    "function": record.funcName,
                    "line": record.lineno
                }
                
                # Add exception info if present
                if record.exc_info:
                    log_entry["exception"] = {
                        "type": record.exc_info[0].__name__,
                        "message": str(record.exc_info[1]),
                        "traceback": traceback.format_exception(*record.exc_info)
                    }
                
                # Add extra fields
                for key, value in record.__dict__.items():
                    if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                                   'filename', 'module', 'lineno', 'funcName', 'created', 
                                   'msecs', 'relativeCreated', 'thread', 'threadName', 
                                   'processName', 'process', 'getMessage', 'exc_info', 'exc_text', 'stack_info']:
                        log_entry[key] = value
                
                return json.dumps(log_entry, default=str)
        
        # Console Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(JSONFormatter())
        self.logger.addHandler(console_handler)
        
        # File Handler (if configured)
        if settings.log_file_path and not settings.is_development():
            try:
                # Ensure log directory exists
                Path(settings.log_file_path).parent.mkdir(parents=True, exist_ok=True)
                
                file_handler = logging.FileHandler(settings.log_file_path)
                file_handler.setFormatter(JSONFormatter())
                self.logger.addHandler(file_handler)
            except Exception as e:
                self.logger.warning(f"Failed to setup file logging: {e}")
        
        # Set up other loggers to use our handler
        logging.getLogger("uvicorn").handlers = []
        logging.getLogger("fastapi").handlers = []
    
    def log_security_event(
        self, 
        event_type: SecurityEventType, 
        ip_address: str,
        endpoint: str = "",
        user_id: Optional[str] = None,
        user_agent: str = "",
        details: Dict[str, Any] = None,
        severity: str = "medium"
    ):
        """
        Log security event for monitoring and alerting
        """
        event = SecurityEvent(
            event_type=event_type,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            endpoint=endpoint,
            details=details or {},
            timestamp=datetime.utcnow(),
            severity=severity
        )
        
        self.security_events.append(event)
        
        # Log with structured data
        self.logger.warning(
            f"Security Event: {event_type.value}",
            extra={
                "event_type": "security",
                "security_event": asdict(event),
                "user_id": user_id,
                "ip_address": ip_address,
                "severity": severity
            }
        )
        
        # Alert on critical events
        if severity in ["high", "critical"]:
            self._send_security_alert(event)
    
    def log_performance_metric(
        self, 
        metric_name: str, 
        value: float, 
        unit: str = "ms",
        tags: Dict[str, str] = None
    ):
        """
        Log performance metric
        """
        metric = PerformanceMetric(
            metric_name=metric_name,
            value=value,
            unit=unit,
            tags=tags or {},
            timestamp=datetime.utcnow()
        )
        
        self.performance_metrics.append(metric)
        
        # Log metric
        self.logger.info(
            f"Performance Metric: {metric_name} = {value}{unit}",
            extra={
                "event_type": "performance",
                "metric": asdict(metric)
            }
        )
        
        # Keep only recent metrics in memory
        cutoff = datetime.utcnow() - timedelta(hours=1)
        self.performance_metrics = [
            m for m in self.performance_metrics 
            if m.timestamp > cutoff
        ]
    
    def _send_security_alert(self, event: SecurityEvent):
        """
        Send security alert (placeholder for integration with alerting system)
        """
        # In production, integrate with:
        # - Slack/Teams notifications
        # - Email alerts
        # - PagerDuty/OpsGenie
        # - SIEM systems
        
        alert_message = f"""
        🚨 SECURITY ALERT 🚨
        
        Event: {event.event_type.value}
        Severity: {event.severity.upper()}
        Time: {event.timestamp.isoformat()}
        IP: {event.ip_address}
        User: {event.user_id or 'Anonymous'}
        Endpoint: {event.endpoint}
        
        Details: {json.dumps(event.details, indent=2)}
        """
        
        self.logger.critical(
            "Security Alert Generated",
            extra={
                "event_type": "security_alert",
                "alert_message": alert_message
            }
        )
    
    def get_security_summary(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get security events summary for the last N hours
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        recent_events = [e for e in self.security_events if e.timestamp > cutoff]
        
        # Count events by type
        event_counts = {}
        for event in recent_events:
            event_type = event.event_type.value
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        # Count by severity
        severity_counts = {}
        for event in recent_events:
            severity_counts[event.severity] = severity_counts.get(event.severity, 0) + 1
        
        return {
            "time_range_hours": hours,
            "total_events": len(recent_events),
            "events_by_type": event_counts,
            "events_by_severity": severity_counts,
            "recent_events": [asdict(e) for e in recent_events[-10:]]  # Last 10 events
        }
    
    def get_performance_summary(self, hours: int = 1) -> Dict[str, Any]:
        """
        Get performance metrics summary
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        recent_metrics = [m for m in self.performance_metrics if m.timestamp > cutoff]
        
        if not recent_metrics:
            return {"message": "No performance metrics available"}
        
        # Group by metric name
        metrics_by_name = {}
        for metric in recent_metrics:
            name = metric.metric_name
            if name not in metrics_by_name:
                metrics_by_name[name] = []
            metrics_by_name[name].append(metric.value)
        
        # Calculate statistics
        summary = {}
        for name, values in metrics_by_name.items():
            summary[name] = {
                "count": len(values),
                "avg": sum(values) / len(values),
                "min": min(values),
                "max": max(values),
                "unit": recent_metrics[0].unit  # Assume same unit
            }
        
        return {
            "time_range_hours": hours,
            "metrics_summary": summary,
            "total_measurements": len(recent_metrics)
        }

class RequestMonitor:
    """
    HTTP request monitoring and analytics
    """
    
    def __init__(self, logger: StructuredLogger):
        self.logger = logger
        self.active_requests: Dict[str, datetime] = {}
    
    @asynccontextmanager
    async def monitor_request(self, request_id: str, endpoint: str, method: str):
        """
        Context manager for monitoring request performance
        """
        start_time = time.time()
        self.active_requests[request_id] = datetime.utcnow()
        
        try:
            yield
        finally:
            # Calculate request duration
            duration = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            # Log performance metric
            self.logger.log_performance_metric(
                "request_duration",
                duration,
                "ms",
                {"endpoint": endpoint, "method": method}
            )
            
            # Clean up
            self.active_requests.pop(request_id, None)
    
    def get_active_requests_count(self) -> int:
        """
        Get number of currently active requests
        """
        return len(self.active_requests)

class HealthMonitor:
    """
    Application health monitoring
    """
    
    def __init__(self):
        self.start_time = datetime.utcnow()
        self.health_checks: Dict[str, Dict[str, Any]] = {}
    
    async def check_database_health(self, db_service) -> Dict[str, Any]:
        """
        Check database connectivity and performance
        """
        try:
            health_data = await db_service.health_check()
            self.health_checks["database"] = health_data
            return health_data
        except Exception as e:
            health_data = {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
            self.health_checks["database"] = health_data
            return health_data
    
    def get_system_health(self) -> Dict[str, Any]:
        """
        Get overall system health status
        """
        uptime = datetime.utcnow() - self.start_time
        
        return {
            "status": "healthy",
            "uptime": str(uptime),
            "start_time": self.start_time.isoformat(),
            "timestamp": datetime.utcnow().isoformat(),
            "components": self.health_checks
        }

# Global monitoring instances
structured_logger = StructuredLogger()
request_monitor = RequestMonitor(structured_logger)
health_monitor = HealthMonitor()

# Convenience functions
def log_info(message: str, **kwargs):
    structured_logger.logger.info(message, extra=kwargs)

def log_warning(message: str, **kwargs):
    structured_logger.logger.warning(message, extra=kwargs)

def log_error(message: str, **kwargs):
    structured_logger.logger.error(message, extra=kwargs)

def log_critical(message: str, **kwargs):
    structured_logger.logger.critical(message, extra=kwargs)

def log_security_event(event_type: SecurityEventType, **kwargs):
    structured_logger.log_security_event(event_type, **kwargs)

def log_performance(metric_name: str, value: float, **kwargs):
    structured_logger.log_performance_metric(metric_name, value, **kwargs)