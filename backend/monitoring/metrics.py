"""
Advanced Metrics Collection and Analysis System
Complementary metrics system that works with existing Complyo monitoring_system.py
Provides enhanced performance metrics, business intelligence, and system health monitoring.
"""

import time
import json
import asyncio
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from concurrent.futures import ThreadPoolExecutor
import aioredis
import numpy as np
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

# Import existing monitoring system for compatibility
try:
    from ..monitoring_system import ComplianceMonitoringSystem
    from ..database_models import db_manager
except ImportError:
    ComplianceMonitoringSystem = None
    db_manager = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MetricType(Enum):
    """Types of metrics collected"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"

class SeverityLevel(Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class MetricPoint:
    """Individual metric data point"""
    name: str
    value: float
    timestamp: datetime
    tags: Dict[str, str]
    metric_type: MetricType

@dataclass
class SystemMetrics:
    """System performance metrics"""
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, int]
    active_connections: int
    response_time: float

@dataclass
class ComplianceMetrics:
    """Compliance-specific metrics"""
    scans_completed: int
    scans_failed: int
    gdpr_violations: int
    accessibility_issues: int
    avg_compliance_score: float
    total_websites_analyzed: int

@dataclass
class BusinessMetrics:
    """Business intelligence metrics"""
    daily_active_users: int
    new_subscriptions: int
    revenue_today: float
    customer_retention_rate: float
    avg_session_duration: float
    feature_usage: Dict[str, int]

class MetricsCollector:
    """Advanced metrics collection and analysis system"""
    
    def __init__(self, redis_client: Optional[aioredis.Redis] = None):
        self.redis = redis_client
        self.metrics_buffer = deque(maxlen=10000)  # In-memory buffer
        self.aggregated_metrics = defaultdict(list)
        self.alert_thresholds = self._setup_alert_thresholds()
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Performance tracking
        self.request_times = deque(maxlen=1000)
        self.error_counts = defaultdict(int)
        self.feature_usage_counts = defaultdict(int)
        
        # Business metrics cache
        self._business_metrics_cache = {}
        self._cache_expiry = {}
        
    def _setup_alert_thresholds(self) -> Dict[str, Dict[str, float]]:
        """Setup alert thresholds for various metrics"""
        return {
            "cpu_usage": {"high": 80.0, "critical": 95.0},
            "memory_usage": {"high": 85.0, "critical": 95.0},
            "disk_usage": {"high": 90.0, "critical": 98.0},
            "response_time": {"high": 2000.0, "critical": 5000.0},  # milliseconds
            "error_rate": {"high": 5.0, "critical": 10.0},  # percentage
            "compliance_score": {"low": 70.0, "critical": 50.0},  # minimum acceptable
        }
    
    async def collect_metric(self, name: str, value: float, 
                           metric_type: MetricType = MetricType.GAUGE,
                           tags: Optional[Dict[str, str]] = None) -> None:
        """Collect a single metric point"""
        try:
            tags = tags or {}
            metric_point = MetricPoint(
                name=name,
                value=value,
                timestamp=datetime.utcnow(),
                tags=tags,
                metric_type=metric_type
            )
            
            # Add to buffer
            self.metrics_buffer.append(metric_point)
            
            # Store in Redis if available
            if self.redis:
                await self._store_metric_redis(metric_point)
            
            # Check for alerts
            await self._check_alert_conditions(name, value, tags)
            
            logger.debug(f"Collected metric: {name}={value} {tags}")
            
        except Exception as e:
            logger.error(f"Error collecting metric {name}: {e}")
    
    async def _store_metric_redis(self, metric: MetricPoint) -> None:
        """Store metric in Redis with appropriate TTL"""
        try:
            key = f"metrics:{metric.name}:{metric.timestamp.strftime('%Y-%m-%d-%H')}"
            data = {
                "value": metric.value,
                "timestamp": metric.timestamp.isoformat(),
                "tags": json.dumps(metric.tags),
                "type": metric.metric_type.value
            }
            
            await self.redis.hset(key, mapping=data)
            await self.redis.expire(key, 86400 * 7)  # 7 days retention
            
        except Exception as e:
            logger.error(f"Error storing metric in Redis: {e}")
    
    async def collect_system_metrics(self) -> SystemMetrics:
        """Collect comprehensive system performance metrics"""
        try:
            # CPU usage
            cpu_usage = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_usage = (disk.used / disk.total) * 100
            
            # Network I/O
            network_io = psutil.net_io_counters()._asdict()
            
            # Active connections (approximate)
            active_connections = len(psutil.net_connections())
            
            # Average response time from recent requests
            avg_response_time = np.mean(self.request_times) if self.request_times else 0.0
            
            metrics = SystemMetrics(
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                disk_usage=disk_usage,
                network_io=network_io,
                active_connections=active_connections,
                response_time=avg_response_time
            )
            
            # Store individual metrics
            await self.collect_metric("system.cpu_usage", cpu_usage, MetricType.GAUGE)
            await self.collect_metric("system.memory_usage", memory_usage, MetricType.GAUGE)
            await self.collect_metric("system.disk_usage", disk_usage, MetricType.GAUGE)
            await self.collect_metric("system.active_connections", active_connections, MetricType.GAUGE)
            await self.collect_metric("system.response_time", avg_response_time, MetricType.GAUGE)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return SystemMetrics(0, 0, 0, {}, 0, 0)
    
    async def collect_compliance_metrics(self, db_session: AsyncSession) -> ComplianceMetrics:
        """Collect compliance-specific metrics from database"""
        try:
            # This would query your actual database tables
            # Placeholder implementation - adjust table names as needed
            
            today = datetime.utcnow().date()
            
            # Scans completed today (placeholder query)
            scans_completed = 150  # Replace with actual query
            scans_failed = 5       # Replace with actual query
            
            # Compliance violations
            gdpr_violations = 23        # Replace with actual query
            accessibility_issues = 45   # Replace with actual query
            
            # Average compliance score
            avg_compliance_score = 78.5  # Replace with actual query
            
            # Total websites analyzed
            total_websites_analyzed = 1250  # Replace with actual query
            
            metrics = ComplianceMetrics(
                scans_completed=scans_completed,
                scans_failed=scans_failed,
                gdpr_violations=gdpr_violations,
                accessibility_issues=accessibility_issues,
                avg_compliance_score=avg_compliance_score,
                total_websites_analyzed=total_websites_analyzed
            )
            
            # Store individual metrics
            await self.collect_metric("compliance.scans_completed", scans_completed, MetricType.COUNTER)
            await self.collect_metric("compliance.scans_failed", scans_failed, MetricType.COUNTER)
            await self.collect_metric("compliance.gdpr_violations", gdpr_violations, MetricType.GAUGE)
            await self.collect_metric("compliance.accessibility_issues", accessibility_issues, MetricType.GAUGE)
            await self.collect_metric("compliance.avg_score", avg_compliance_score, MetricType.GAUGE)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting compliance metrics: {e}")
            return ComplianceMetrics(0, 0, 0, 0, 0.0, 0)
    
    async def collect_business_metrics(self, db_session: AsyncSession) -> BusinessMetrics:
        """Collect business intelligence metrics"""
        try:
            # Check cache first
            cache_key = f"business_metrics_{datetime.utcnow().date()}"
            if (cache_key in self._business_metrics_cache and 
                self._cache_expiry.get(cache_key, datetime.min) > datetime.utcnow()):
                return self._business_metrics_cache[cache_key]
            
            # Collect fresh metrics (placeholder queries - replace with actual)
            daily_active_users = 450      # Replace with actual query
            new_subscriptions = 12        # Replace with actual query
            revenue_today = 2450.75      # Replace with actual query
            customer_retention_rate = 85.3  # Replace with actual query
            avg_session_duration = 18.5   # minutes
            
            feature_usage = dict(self.feature_usage_counts)
            
            metrics = BusinessMetrics(
                daily_active_users=daily_active_users,
                new_subscriptions=new_subscriptions,
                revenue_today=revenue_today,
                customer_retention_rate=customer_retention_rate,
                avg_session_duration=avg_session_duration,
                feature_usage=feature_usage
            )
            
            # Cache for 1 hour
            self._business_metrics_cache[cache_key] = metrics
            self._cache_expiry[cache_key] = datetime.utcnow() + timedelta(hours=1)
            
            # Store individual metrics
            await self.collect_metric("business.daily_active_users", daily_active_users, MetricType.GAUGE)
            await self.collect_metric("business.new_subscriptions", new_subscriptions, MetricType.COUNTER)
            await self.collect_metric("business.revenue_today", revenue_today, MetricType.GAUGE)
            await self.collect_metric("business.retention_rate", customer_retention_rate, MetricType.GAUGE)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting business metrics: {e}")
            return BusinessMetrics(0, 0, 0.0, 0.0, 0.0, {})
    
    async def track_request(self, duration_ms: float, endpoint: str, 
                          status_code: int, user_id: Optional[str] = None) -> None:
        """Track individual request metrics"""
        try:
            self.request_times.append(duration_ms)
            
            # Track errors
            if status_code >= 400:
                self.error_counts[f"{status_code}"] += 1
            
            # Collect metrics
            await self.collect_metric("http.request_duration", duration_ms, 
                                    MetricType.TIMER, {"endpoint": endpoint})
            await self.collect_metric("http.requests_total", 1, 
                                    MetricType.COUNTER, {"endpoint": endpoint, "status": str(status_code)})
            
            # Track feature usage
            if user_id:
                self.feature_usage_counts[endpoint] += 1
                
        except Exception as e:
            logger.error(f"Error tracking request: {e}")
    
    async def track_compliance_scan(self, website_url: str, scan_duration: float,
                                  gdpr_score: float, accessibility_score: float,
                                  success: bool) -> None:
        """Track compliance scan metrics"""
        try:
            tags = {
                "website": website_url,
                "success": str(success).lower()
            }
            
            await self.collect_metric("compliance.scan_duration", scan_duration, 
                                    MetricType.TIMER, tags)
            await self.collect_metric("compliance.gdpr_score", gdpr_score, 
                                    MetricType.GAUGE, tags)
            await self.collect_metric("compliance.accessibility_score", accessibility_score, 
                                    MetricType.GAUGE, tags)
            
            if success:
                await self.collect_metric("compliance.scans_successful", 1, 
                                        MetricType.COUNTER, tags)
            else:
                await self.collect_metric("compliance.scans_failed", 1, 
                                        MetricType.COUNTER, tags)
                
        except Exception as e:
            logger.error(f"Error tracking compliance scan: {e}")
    
    async def _check_alert_conditions(self, metric_name: str, value: float, 
                                    tags: Dict[str, str]) -> None:
        """Check if metric value triggers any alerts"""
        try:
            # Extract base metric name for threshold lookup
            base_name = metric_name.split('.')[-1] if '.' in metric_name else metric_name
            
            if base_name not in self.alert_thresholds:
                return
            
            thresholds = self.alert_thresholds[base_name]
            severity = None
            
            # Determine severity based on thresholds
            if "critical" in thresholds and value >= thresholds["critical"]:
                severity = SeverityLevel.CRITICAL
            elif "high" in thresholds and value >= thresholds["high"]:
                severity = SeverityLevel.HIGH
            elif "low" in thresholds and value <= thresholds.get("low", float('inf')):
                severity = SeverityLevel.LOW
            
            if severity:
                await self._trigger_alert(metric_name, value, severity, tags)
                
        except Exception as e:
            logger.error(f"Error checking alert conditions: {e}")
    
    async def _trigger_alert(self, metric_name: str, value: float, 
                           severity: SeverityLevel, tags: Dict[str, str]) -> None:
        """Trigger an alert for critical metric values"""
        try:
            alert_data = {
                "metric": metric_name,
                "value": value,
                "severity": severity.value,
                "timestamp": datetime.utcnow().isoformat(),
                "tags": tags,
                "message": f"Alert: {metric_name} = {value} ({severity.value})"
            }
            
            # Store alert in Redis if available
            if self.redis:
                alert_key = f"alerts:{severity.value}:{int(time.time())}"
                await self.redis.set(alert_key, json.dumps(alert_data), ex=86400)
            
            # Log alert
            logger.warning(f"ALERT [{severity.value.upper()}]: {alert_data['message']}")
            
            # Here you could integrate with external alerting systems
            # (e.g., Slack, PagerDuty, email notifications)
            
        except Exception as e:
            logger.error(f"Error triggering alert: {e}")
    
    async def get_metrics_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get comprehensive metrics summary for specified time period"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            # Filter recent metrics
            recent_metrics = [m for m in self.metrics_buffer 
                            if m.timestamp >= cutoff_time]
            
            # Group by metric name
            grouped_metrics = defaultdict(list)
            for metric in recent_metrics:
                grouped_metrics[metric.name].append(metric.value)
            
            # Calculate statistics
            summary = {}
            for name, values in grouped_metrics.items():
                if values:
                    summary[name] = {
                        "count": len(values),
                        "min": min(values),
                        "max": max(values),
                        "avg": sum(values) / len(values),
                        "latest": values[-1] if values else None
                    }
            
            return {
                "period_hours": hours,
                "metrics_collected": len(recent_metrics),
                "unique_metrics": len(grouped_metrics),
                "summary": summary,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting metrics summary: {e}")
            return {"error": str(e)}
    
    async def get_real_time_dashboard_data(self, db_session: AsyncSession) -> Dict[str, Any]:
        """Get real-time dashboard data combining all metric types"""
        try:
            # Collect all metric types concurrently
            system_metrics, compliance_metrics, business_metrics = await asyncio.gather(
                self.collect_system_metrics(),
                self.collect_compliance_metrics(db_session),
                self.collect_business_metrics(db_session),
                return_exceptions=True
            )
            
            # Calculate derived metrics
            error_rate = self._calculate_error_rate()
            throughput = self._calculate_throughput()
            
            dashboard_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "system": asdict(system_metrics) if isinstance(system_metrics, SystemMetrics) else {},
                "compliance": asdict(compliance_metrics) if isinstance(compliance_metrics, ComplianceMetrics) else {},
                "business": asdict(business_metrics) if isinstance(business_metrics, BusinessMetrics) else {},
                "derived": {
                    "error_rate": error_rate,
                    "throughput": throughput,
                    "health_score": self._calculate_health_score(system_metrics, compliance_metrics)
                },
                "alerts": await self._get_recent_alerts()
            }
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            return {"error": str(e), "timestamp": datetime.utcnow().isoformat()}
    
    def _calculate_error_rate(self) -> float:
        """Calculate current error rate percentage"""
        try:
            total_errors = sum(self.error_counts.values())
            total_requests = len(self.request_times)
            
            if total_requests == 0:
                return 0.0
                
            return (total_errors / total_requests) * 100
            
        except Exception:
            return 0.0
    
    def _calculate_throughput(self) -> float:
        """Calculate requests per minute"""
        try:
            if not self.request_times:
                return 0.0
                
            # Count requests in last minute
            cutoff = time.time() - 60
            recent_requests = len([t for t in self.request_times if t >= cutoff])
            
            return recent_requests
            
        except Exception:
            return 0.0
    
    def _calculate_health_score(self, system_metrics: SystemMetrics, 
                              compliance_metrics: ComplianceMetrics) -> float:
        """Calculate overall system health score (0-100)"""
        try:
            if not isinstance(system_metrics, SystemMetrics) or not isinstance(compliance_metrics, ComplianceMetrics):
                return 50.0  # Default middle score
                
            # Weight different factors
            cpu_score = max(0, 100 - system_metrics.cpu_usage)
            memory_score = max(0, 100 - system_metrics.memory_usage)
            disk_score = max(0, 100 - system_metrics.disk_usage)
            
            # Response time score (assuming good < 1000ms, bad > 5000ms)
            response_score = max(0, min(100, (5000 - system_metrics.response_time) / 50))
            
            # Compliance score
            compliance_score = compliance_metrics.avg_compliance_score
            
            # Error rate score
            error_rate = self._calculate_error_rate()
            error_score = max(0, 100 - (error_rate * 10))  # 10% error = 0 score
            
            # Weighted average
            health_score = (
                cpu_score * 0.2 +
                memory_score * 0.2 +
                disk_score * 0.1 +
                response_score * 0.2 +
                compliance_score * 0.2 +
                error_score * 0.1
            )
            
            return round(health_score, 2)
            
        except Exception as e:
            logger.error(f"Error calculating health score: {e}")
            return 50.0
    
    async def _get_recent_alerts(self) -> List[Dict[str, Any]]:
        """Get recent alerts from Redis"""
        try:
            if not self.redis:
                return []
                
            # Get alert keys from last 24 hours
            pattern = "alerts:*"
            keys = await self.redis.keys(pattern)
            
            alerts = []
            for key in keys[-10:]:  # Last 10 alerts
                alert_data = await self.redis.get(key)
                if alert_data:
                    alerts.append(json.loads(alert_data))
            
            return sorted(alerts, key=lambda x: x['timestamp'], reverse=True)
            
        except Exception as e:
            logger.error(f"Error getting recent alerts: {e}")
            return []
    
    async def export_metrics(self, start_time: datetime, end_time: datetime,
                           format: str = "json") -> str:
        """Export metrics for specified time range"""
        try:
            # Filter metrics by time range
            filtered_metrics = [
                m for m in self.metrics_buffer 
                if start_time <= m.timestamp <= end_time
            ]
            
            if format.lower() == "json":
                data = [
                    {
                        "name": m.name,
                        "value": m.value,
                        "timestamp": m.timestamp.isoformat(),
                        "tags": m.tags,
                        "type": m.metric_type.value
                    }
                    for m in filtered_metrics
                ]
                return json.dumps(data, indent=2)
                
            elif format.lower() == "csv":
                import csv
                import io
                
                output = io.StringIO()
                writer = csv.writer(output)
                writer.writerow(["name", "value", "timestamp", "tags", "type"])
                
                for m in filtered_metrics:
                    writer.writerow([
                        m.name, m.value, m.timestamp.isoformat(),
                        json.dumps(m.tags), m.metric_type.value
                    ])
                
                return output.getvalue()
            
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            logger.error(f"Error exporting metrics: {e}")
            return f"Error: {e}"

# Global metrics collector instance
metrics_collector = MetricsCollector()

# Decorator for timing functions
def timed_operation(operation_name: str):
    """Decorator to time function execution"""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = (time.time() - start_time) * 1000  # Convert to milliseconds
                await metrics_collector.collect_metric(
                    f"operation.{operation_name}.duration", 
                    duration, 
                    MetricType.TIMER
                )
                await metrics_collector.collect_metric(
                    f"operation.{operation_name}.success", 
                    1, 
                    MetricType.COUNTER
                )
                return result
            except Exception as e:
                duration = (time.time() - start_time) * 1000
                await metrics_collector.collect_metric(
                    f"operation.{operation_name}.duration", 
                    duration, 
                    MetricType.TIMER
                )
                await metrics_collector.collect_metric(
                    f"operation.{operation_name}.error", 
                    1, 
                    MetricType.COUNTER
                )
                raise
                
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = (time.time() - start_time) * 1000
                # Note: sync version can't await, would need background task
                return result
            except Exception as e:
                duration = (time.time() - start_time) * 1000
                raise
                
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator

if __name__ == "__main__":
    # Example usage
    async def example_usage():
        collector = MetricsCollector()
        
        # Collect some sample metrics
        await collector.collect_metric("test.counter", 1, MetricType.COUNTER)
        await collector.collect_metric("test.gauge", 75.5, MetricType.GAUGE)
        
        # Get summary
        summary = await collector.get_metrics_summary(hours=1)
        print(json.dumps(summary, indent=2))
    
    asyncio.run(example_usage())