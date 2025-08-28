"""
24/7 Website Monitoring System für Complyo
Continuous compliance monitoring with change detection and alerting
"""
import asyncio
import aiohttp
import schedule
import time
import threading
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from pydantic import BaseModel
from dataclasses import dataclass
import hashlib
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class MonitoringTarget(BaseModel):
    id: str
    url: str
    user_id: str
    website_name: str
    monitoring_frequency: str = "daily"  # hourly, daily, weekly
    enabled: bool = True
    last_scan: Optional[datetime] = None
    notifications_enabled: bool = True
    email_notifications: bool = True
    compliance_threshold: int = 80  # Alert if score drops below this

class ComplianceChange(BaseModel):
    target_id: str
    change_type: str  # "improvement", "degradation", "new_issue", "resolved_issue"
    category: str  # "gdpr", "impressum", "cookies", "accessibility"
    old_score: Optional[int] = None
    new_score: int
    description: str
    severity: str  # "low", "medium", "high", "critical"
    detected_at: datetime
    change_details: Dict[str, Any] = {}

class MonitoringAlert(BaseModel):
    id: str
    target_id: str
    alert_type: str  # "compliance_drop", "new_violation", "scan_failed", "certificate_expiry"
    severity: str
    title: str
    description: str
    created_at: datetime
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    notification_sent: bool = False

@dataclass
class ScanSnapshot:
    """Snapshot of a compliance scan for change detection"""
    scan_id: str
    target_id: str
    timestamp: datetime
    overall_score: float
    category_scores: Dict[str, int]
    issues_hash: str
    content_hash: str
    ssl_info: Dict[str, Any]
    page_load_time: float
    raw_scan_data: Dict[str, Any]

class ComplianceMonitoringSystem:
    """
    24/7 Compliance Monitoring with Change Detection
    """
    
    def __init__(self):
        self.targets: Dict[str, MonitoringTarget] = {}
        self.scan_history: Dict[str, List[ScanSnapshot]] = {}
        self.alerts: Dict[str, MonitoringAlert] = {}
        self.changes: Dict[str, List[ComplianceChange]] = {}
        self.notification_handlers: List[Callable] = []
        self.monitoring_active = False
        self.scheduler_thread = None
        
        # Email configuration
        self.smtp_config = {
            "host": "smtp.gmail.com",
            "port": 587,
            "username": "alerts@complyo.tech",
            "password": "demo_password",  # In production: use environment variables
            "from_email": "alerts@complyo.tech"
        }
    
    def add_monitoring_target(self, target_data: Dict[str, Any]) -> MonitoringTarget:
        """Add a new website for monitoring"""
        
        target_id = target_data.get("id") or hashlib.md5(
            f"{target_data['url']}_{target_data['user_id']}".encode()
        ).hexdigest()[:12]
        
        target = MonitoringTarget(
            id=target_id,
            url=target_data["url"],
            user_id=target_data["user_id"],
            website_name=target_data.get("website_name", target_data["url"]),
            monitoring_frequency=target_data.get("monitoring_frequency", "daily"),
            enabled=target_data.get("enabled", True),
            notifications_enabled=target_data.get("notifications_enabled", True),
            email_notifications=target_data.get("email_notifications", True),
            compliance_threshold=target_data.get("compliance_threshold", 80)
        )
        
        self.targets[target_id] = target
        self.scan_history[target_id] = []
        self.changes[target_id] = []
        
        return target
    
    def remove_monitoring_target(self, target_id: str) -> bool:
        """Remove a monitoring target"""
        
        if target_id in self.targets:
            del self.targets[target_id]
            if target_id in self.scan_history:
                del self.scan_history[target_id]
            if target_id in self.changes:
                del self.changes[target_id]
            return True
        return False
    
    async def perform_monitoring_scan(self, target: MonitoringTarget) -> Optional[ScanSnapshot]:
        """Perform a compliance scan for monitoring"""
        
        try:
            # Import scanner (avoid circular imports)
            from website_scanner import WebsiteScanner
            
            async with WebsiteScanner() as scanner:
                scan_result = await scanner.scan_website(target.url)
            
            if scan_result.get('status') == 'failed':
                await self._create_alert(
                    target.id,
                    "scan_failed",
                    "high",
                    "Website-Scan fehlgeschlagen",
                    f"Der Compliance-Scan für {target.website_name} ist fehlgeschlagen: {scan_result.get('error', 'Unbekannter Fehler')}"
                )
                return None
            
            # Create snapshot for change detection
            snapshot = ScanSnapshot(
                scan_id=scan_result.get("scan_id", scan_result.get("id")),
                target_id=target.id,
                timestamp=datetime.now(),
                overall_score=scan_result.get("overall_score", 0),
                category_scores={
                    result.get("category", "unknown"): result.get("score", 0)
                    for result in scan_result.get("results", [])
                },
                issues_hash=self._calculate_issues_hash(scan_result.get("results", [])),
                content_hash=hashlib.md5(str(scan_result).encode()).hexdigest()[:16],
                ssl_info=scan_result.get("technical_analysis", {}).get("ssl", {}),
                page_load_time=scan_result.get("technical_analysis", {}).get("load_time", 0),
                raw_scan_data=scan_result
            )
            
            # Store snapshot
            self.scan_history[target.id].append(snapshot)
            
            # Keep only last 30 scans per target
            if len(self.scan_history[target.id]) > 30:
                self.scan_history[target.id] = self.scan_history[target.id][-30:]
            
            # Update target's last scan time
            target.last_scan = datetime.now()
            
            return snapshot
            
        except Exception as e:
            await self._create_alert(
                target.id,
                "scan_failed",
                "high", 
                "Monitoring-Fehler",
                f"Fehler beim Monitoring von {target.website_name}: {str(e)}"
            )
            return None
    
    async def detect_changes(self, target_id: str, new_snapshot: ScanSnapshot) -> List[ComplianceChange]:
        """Detect changes between current and previous scan"""
        
        changes = []
        history = self.scan_history.get(target_id, [])
        
        if len(history) < 2:
            return changes  # Need at least 2 scans to detect changes
        
        previous_snapshot = history[-2]  # Previous scan (before current)
        
        # Overall score change
        score_diff = new_snapshot.overall_score - previous_snapshot.overall_score
        
        if abs(score_diff) >= 5:  # Significant change threshold
            change_type = "improvement" if score_diff > 0 else "degradation"
            severity = "high" if abs(score_diff) >= 20 else "medium" if abs(score_diff) >= 10 else "low"
            
            changes.append(ComplianceChange(
                target_id=target_id,
                change_type=change_type,
                category="overall",
                old_score=int(previous_snapshot.overall_score),
                new_score=int(new_snapshot.overall_score),
                description=f"Gesamtscore hat sich um {score_diff:+.1f} Punkte verändert",
                severity=severity,
                detected_at=datetime.now(),
                change_details={
                    "score_change": score_diff,
                    "previous_score": previous_snapshot.overall_score,
                    "current_score": new_snapshot.overall_score
                }
            ))
        
        # Category-specific changes
        for category, new_score in new_snapshot.category_scores.items():
            old_score = previous_snapshot.category_scores.get(category, 0)
            category_diff = new_score - old_score
            
            if abs(category_diff) >= 10:  # Category change threshold
                change_type = "improvement" if category_diff > 0 else "degradation"
                severity = "high" if abs(category_diff) >= 30 else "medium"
                
                changes.append(ComplianceChange(
                    target_id=target_id,
                    change_type=change_type,
                    category=category.lower().replace(" ", "_"),
                    old_score=old_score,
                    new_score=new_score,
                    description=f"{category}: {category_diff:+d} Punkte",
                    severity=severity,
                    detected_at=datetime.now(),
                    change_details={
                        "category": category,
                        "score_change": category_diff
                    }
                ))
        
        # New issues detection
        if new_snapshot.issues_hash != previous_snapshot.issues_hash:
            changes.append(ComplianceChange(
                target_id=target_id,
                change_type="content_change",
                category="technical",
                new_score=0,  # Not score-related
                description="Änderungen in Compliance-Problemen erkannt",
                severity="medium",
                detected_at=datetime.now(),
                change_details={
                    "previous_hash": previous_snapshot.issues_hash,
                    "current_hash": new_snapshot.issues_hash
                }
            ))
        
        # Performance changes
        load_time_diff = new_snapshot.page_load_time - previous_snapshot.page_load_time
        if abs(load_time_diff) >= 1.0:  # 1 second threshold
            severity = "high" if load_time_diff > 3.0 else "medium"
            
            changes.append(ComplianceChange(
                target_id=target_id,
                change_type="performance_change",
                category="technical",
                new_score=0,
                description=f"Ladezeit: {load_time_diff:+.2f}s verändert",
                severity=severity,
                detected_at=datetime.now(),
                change_details={
                    "load_time_change": load_time_diff,
                    "previous_load_time": previous_snapshot.page_load_time,
                    "current_load_time": new_snapshot.page_load_time
                }
            ))
        
        # Store detected changes
        self.changes[target_id].extend(changes)
        
        return changes
    
    async def _create_alert(self, target_id: str, alert_type: str, severity: str, title: str, description: str) -> MonitoringAlert:
        """Create a new monitoring alert"""
        
        alert_id = hashlib.md5(f"{target_id}_{alert_type}_{datetime.now().isoformat()}".encode()).hexdigest()[:12]
        
        alert = MonitoringAlert(
            id=alert_id,
            target_id=target_id,
            alert_type=alert_type,
            severity=severity,
            title=title,
            description=description,
            created_at=datetime.now()
        )
        
        self.alerts[alert_id] = alert
        
        # Send notifications if enabled
        target = self.targets.get(target_id)
        if target and target.notifications_enabled:
            await self._send_notifications(alert)
        
        return alert
    
    async def _send_notifications(self, alert: MonitoringAlert):
        """Send alert notifications"""
        
        target = self.targets.get(alert.target_id)
        if not target:
            return
        
        # Email notification
        if target.email_notifications:
            await self._send_email_notification(alert, target)
        
        # Call custom notification handlers
        for handler in self.notification_handlers:
            try:
                await handler(alert, target)
            except Exception as e:
                print(f"Notification handler error: {e}")
        
        # Mark as sent
        alert.notification_sent = True
    
    async def _send_email_notification(self, alert: MonitoringAlert, target: MonitoringTarget):
        """Send email notification"""
        
        try:
            # In production, get user email from database
            user_email = f"user_{target.user_id}@example.com"  # Demo email
            
            subject = f"🚨 Complyo Alert: {alert.title}"
            
            body = f"""
Hallo,

es gibt eine wichtige Meldung für Ihre überwachte Website:

Website: {target.website_name} ({target.url})
Alert-Typ: {alert.alert_type}
Schweregrad: {alert.severity.upper()}
Zeitpunkt: {alert.created_at.strftime('%d.%m.%Y %H:%M')}

Beschreibung:
{alert.description}

Bitte loggen Sie sich in Ihr Complyo Dashboard ein, um weitere Details zu sehen:
https://3010-iqtxqhmde36ooi6emqnp2.e2b.dev/

Mit freundlichen Grüßen,
Ihr Complyo Monitoring Team
            """.strip()
            
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = self.smtp_config['from_email']
            msg['To'] = user_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # In demo mode, just log the email
            print(f"📧 Email notification (demo): {subject} -> {user_email}")
            print(f"Body: {body[:200]}...")
            
            # In production, send real email:
            # with smtplib.SMTP(self.smtp_config['host'], self.smtp_config['port']) as server:
            #     server.starttls()
            #     server.login(self.smtp_config['username'], self.smtp_config['password'])
            #     server.send_message(msg)
            
        except Exception as e:
            print(f"Email notification error: {e}")
    
    def _calculate_issues_hash(self, results: List[Dict]) -> str:
        """Calculate hash of current issues for change detection"""
        
        issues_summary = []
        for result in results:
            if result.get("status") in ["fail", "warning"]:
                issues_summary.append({
                    "category": result.get("category"),
                    "status": result.get("status"),
                    "score": result.get("score"),
                    "issues": result.get("issues", [])
                })
        
        issues_str = json.dumps(issues_summary, sort_keys=True)
        return hashlib.md5(issues_str.encode()).hexdigest()[:16]
    
    def start_monitoring(self):
        """Start the monitoring scheduler"""
        
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        
        # Schedule monitoring tasks
        schedule.clear()
        
        # Hourly monitoring
        schedule.every().hour.at(":00").do(self._run_hourly_monitoring)
        
        # Daily monitoring  
        schedule.every().day.at("06:00").do(self._run_daily_monitoring)
        
        # Weekly monitoring
        schedule.every().monday.at("06:00").do(self._run_weekly_monitoring)
        
        # Cleanup old data
        schedule.every().day.at("02:00").do(self._cleanup_old_data)
        
        # Start scheduler in background thread
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        print("🔄 24/7 Monitoring System started")
    
    def stop_monitoring(self):
        """Stop the monitoring scheduler"""
        
        self.monitoring_active = False
        schedule.clear()
        print("⏹️ 24/7 Monitoring System stopped")
    
    def _run_scheduler(self):
        """Run the schedule in background thread"""
        
        while self.monitoring_active:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def _run_hourly_monitoring(self):
        """Run hourly monitoring tasks"""
        
        hourly_targets = [t for t in self.targets.values() 
                         if t.enabled and t.monitoring_frequency == "hourly"]
        
        if hourly_targets:
            asyncio.create_task(self._monitor_targets(hourly_targets))
    
    def _run_daily_monitoring(self):
        """Run daily monitoring tasks"""
        
        daily_targets = [t for t in self.targets.values() 
                        if t.enabled and t.monitoring_frequency == "daily"]
        
        if daily_targets:
            asyncio.create_task(self._monitor_targets(daily_targets))
    
    def _run_weekly_monitoring(self):
        """Run weekly monitoring tasks"""
        
        weekly_targets = [t for t in self.targets.values() 
                         if t.enabled and t.monitoring_frequency == "weekly"]
        
        if weekly_targets:
            asyncio.create_task(self._monitor_targets(weekly_targets))
    
    async def _monitor_targets(self, targets: List[MonitoringTarget]):
        """Monitor a list of targets"""
        
        for target in targets:
            try:
                # Perform scan
                snapshot = await self.perform_monitoring_scan(target)
                
                if snapshot:
                    # Detect changes
                    changes = await self.detect_changes(target.id, snapshot)
                    
                    # Check for alerts
                    await self._check_for_alerts(target, snapshot, changes)
                
                # Small delay between scans
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"Monitoring error for {target.url}: {e}")
    
    async def _check_for_alerts(self, target: MonitoringTarget, snapshot: ScanSnapshot, changes: List[ComplianceChange]):
        """Check if alerts should be created based on scan results"""
        
        # Score drop below threshold
        if snapshot.overall_score < target.compliance_threshold:
            await self._create_alert(
                target.id,
                "compliance_drop",
                "high",
                "Compliance-Score gefallen",
                f"{target.website_name}: Score auf {snapshot.overall_score:.1f}% gesunken (Schwelle: {target.compliance_threshold}%)"
            )
        
        # Critical changes
        critical_changes = [c for c in changes if c.severity == "critical"]
        if critical_changes:
            await self._create_alert(
                target.id,
                "critical_change",
                "critical",
                "Kritische Compliance-Änderung",
                f"{len(critical_changes)} kritische Änderungen in {target.website_name} erkannt"
            )
        
        # SSL certificate issues
        ssl_info = snapshot.ssl_info
        if not ssl_info.get("https_enabled"):
            await self._create_alert(
                target.id,
                "ssl_issue",
                "high",
                "SSL-Zertifikat Problem",
                f"{target.website_name}: HTTPS nicht aktiviert oder Zertifikat ungültig"
            )
        
        # Performance issues
        if snapshot.page_load_time > 5.0:
            await self._create_alert(
                target.id,
                "performance_issue",
                "medium",
                "Performance-Problem",
                f"{target.website_name}: Ladezeit {snapshot.page_load_time:.1f}s (über 5s Grenze)"
            )
    
    def _cleanup_old_data(self):
        """Clean up old monitoring data"""
        
        cutoff_date = datetime.now() - timedelta(days=90)
        
        # Clean old alerts
        old_alerts = [alert_id for alert_id, alert in self.alerts.items() 
                     if alert.created_at < cutoff_date and alert.resolved_at]
        
        for alert_id in old_alerts:
            del self.alerts[alert_id]
        
        # Clean old changes
        for target_id in self.changes:
            self.changes[target_id] = [
                change for change in self.changes[target_id]
                if change.detected_at >= cutoff_date
            ]
        
        print(f"🧹 Cleaned up {len(old_alerts)} old alerts")
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring system status"""
        
        active_targets = len([t for t in self.targets.values() if t.enabled])
        total_scans = sum(len(history) for history in self.scan_history.values())
        open_alerts = len([a for a in self.alerts.values() if not a.resolved_at])
        
        return {
            "monitoring_active": self.monitoring_active,
            "total_targets": len(self.targets),
            "active_targets": active_targets,
            "total_scans_performed": total_scans,
            "open_alerts": open_alerts,
            "total_alerts": len(self.alerts),
            "scheduler_running": self.scheduler_thread and self.scheduler_thread.is_alive() if self.scheduler_thread else False
        }
    
    def get_target_statistics(self, target_id: str) -> Dict[str, Any]:
        """Get statistics for a specific monitoring target"""
        
        if target_id not in self.targets:
            return {}
        
        target = self.targets[target_id]
        history = self.scan_history.get(target_id, [])
        changes = self.changes.get(target_id, [])
        target_alerts = [a for a in self.alerts.values() if a.target_id == target_id]
        
        # Calculate trends
        scores = [s.overall_score for s in history]
        avg_score = sum(scores) / len(scores) if scores else 0
        
        recent_scores = scores[-7:] if len(scores) >= 7 else scores
        recent_avg = sum(recent_scores) / len(recent_scores) if recent_scores else 0
        
        trend = "stable"
        if len(scores) >= 2:
            if recent_avg > avg_score + 5:
                trend = "improving"
            elif recent_avg < avg_score - 5:
                trend = "declining"
        
        return {
            "target": target.dict(),
            "total_scans": len(history),
            "average_score": round(avg_score, 1),
            "recent_average_score": round(recent_avg, 1),
            "trend": trend,
            "total_changes": len(changes),
            "total_alerts": len(target_alerts),
            "open_alerts": len([a for a in target_alerts if not a.resolved_at]),
            "last_scan": target.last_scan.isoformat() if target.last_scan else None,
            "uptime_percentage": 100.0  # Simplified - could calculate from scan failures
        }
    
    async def get_user_targets(self, user_id: str) -> List[Dict]:
        """Get all monitoring targets for a specific user"""
        user_targets = []
        
        for target_id, target in self.monitoring_targets.items():
            if target.get("user_id") == user_id:
                user_targets.append({
                    "target_id": target_id,
                    "website_url": target["website_url"],
                    "website_name": target["website_name"],
                    "monitoring_frequency": target["monitoring_frequency"],
                    "created_at": target["created_at"],
                    "last_scan": target.get("last_scan_time"),
                    "status": target["status"],
                    "alert_thresholds": target["alert_thresholds"],
                    "notification_preferences": target["notification_preferences"]
                })
        
        return user_targets
    
    async def get_target_by_id(self, target_id: str) -> Dict:
        """Get monitoring target by ID"""
        return self.monitoring_targets.get(target_id)
    
    async def remove_monitoring_target(self, target_id: str, user_id: str) -> bool:
        """Remove monitoring target if owned by user"""
        target = self.monitoring_targets.get(target_id)
        
        if target and target.get("user_id") == user_id:
            # Stop monitoring for this target
            target["status"] = "inactive"
            del self.monitoring_targets[target_id]
            
            # Remove from scan results  
            self.scan_results = [scan for scan in self.scan_results if scan.target_id != target_id]
            self.compliance_snapshots = [snap for snap in self.compliance_snapshots if snap.target_id != target_id]
            
            return True
        
        return False
    
    async def get_scan_history(self, target_id: str, limit: int = 10) -> List[Dict]:
        """Get scan history for a target"""
        target_scans = [
            {
                "scan_id": scan.scan_id,
                "target_id": scan.target_id,
                "timestamp": scan.timestamp,
                "status": scan.status,
                "compliance_score": scan.compliance_score,
                "issues_detected": scan.issues_detected,
                "changes_detected": [change.to_dict() for change in scan.changes_detected],
                "alerts_triggered": [alert.to_dict() for alert in scan.alerts_triggered]
            }
            for scan in self.scan_results 
            if scan.target_id == target_id
        ]
        
        # Sort by timestamp descending and limit
        target_scans.sort(key=lambda x: x["timestamp"], reverse=True)
        return target_scans[:limit]
    
    async def get_user_alerts(self, user_id: str, limit: int = 20) -> List[Dict]:
        """Get recent alerts for user's targets"""
        user_target_ids = {
            target_id for target_id, target in self.monitoring_targets.items()
            if target.get("user_id") == user_id
        }
        
        user_alerts = []
        for scan in self.scan_results:
            if scan.target_id in user_target_ids:
                for alert in scan.alerts_triggered:
                    user_alerts.append({
                        "alert_id": alert.alert_id,
                        "target_id": scan.target_id,
                        "website_url": self.monitoring_targets[scan.target_id]["website_url"],
                        "alert_type": alert.alert_type,
                        "severity": alert.severity,
                        "message": alert.message,
                        "triggered_at": alert.triggered_at.isoformat(),
                        "scan_id": scan.scan_id
                    })
        
        # Sort by triggered_at descending and limit
        user_alerts.sort(key=lambda x: x["triggered_at"], reverse=True)
        return user_alerts[:limit]
    
    async def generate_monitoring_report(self, target_id: str, start_date: datetime, end_date: datetime) -> Dict:
        """Generate comprehensive monitoring report"""
        target = self.monitoring_targets.get(target_id)
        if not target:
            raise ValueError(f"Target {target_id} not found")
        
        # Get scans in date range
        relevant_scans = [
            scan for scan in self.scan_results
            if scan.target_id == target_id and start_date <= scan.timestamp <= end_date
        ]
        
        if not relevant_scans:
            return {
                "summary": "No scans found in the specified period",
                "total_scans": 0,
                "period_days": (end_date - start_date).days
            }
        
        # Calculate statistics
        total_scans = len(relevant_scans)
        avg_score = sum(scan.compliance_score for scan in relevant_scans) / total_scans
        total_issues = sum(scan.issues_detected for scan in relevant_scans)
        total_changes = sum(len(scan.changes_detected) for scan in relevant_scans)
        total_alerts = sum(len(scan.alerts_triggered) for scan in relevant_scans)
        
        # Score trend
        scores = [scan.compliance_score for scan in sorted(relevant_scans, key=lambda x: x.timestamp)]
        score_trend = "stable"
        if len(scores) >= 2:
            trend_diff = scores[-1] - scores[0]
            if trend_diff > 5:
                score_trend = "improving"
            elif trend_diff < -5:
                score_trend = "declining"
        
        # Recent issues
        recent_issues = []
        for scan in relevant_scans[-5:]:  # Last 5 scans
            for change in scan.changes_detected:
                if change.change_type == "degradation":
                    recent_issues.append({
                        "category": change.category,
                        "description": change.description,
                        "severity": change.severity,
                        "detected_at": change.detected_at.isoformat()
                    })
        
        return {
            "target_info": {
                "target_id": target_id,
                "website_url": target["website_url"],
                "website_name": target["website_name"],
                "monitoring_frequency": target["monitoring_frequency"]
            },
            "period_summary": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "total_days": (end_date - start_date).days,
                "total_scans": total_scans
            },
            "compliance_metrics": {
                "average_score": round(avg_score, 1),
                "current_score": relevant_scans[-1].compliance_score if relevant_scans else 0,
                "score_trend": score_trend,
                "total_issues_detected": total_issues,
                "total_changes": total_changes,
                "total_alerts": total_alerts
            },
            "recent_issues": recent_issues[:10],  # Top 10 recent issues
            "recommendations": self._generate_report_recommendations(avg_score, total_issues, score_trend)
        }
    
    def _generate_report_recommendations(self, avg_score: float, total_issues: int, trend: str) -> List[str]:
        """Generate actionable recommendations based on report data"""
        recommendations = []
        
        if avg_score < 60:
            recommendations.append("🚨 Kritische Compliance-Probleme beheben - Durchschnittsscore unter 60%")
        elif avg_score < 80:
            recommendations.append("⚠️ Compliance-Score verbessern - Zielwert über 80% anstreben")
        
        if trend == "declining":
            recommendations.append("📉 Verschlechternder Trend - Sofortige Maßnahmen erforderlich")
        elif trend == "stable" and avg_score >= 80:
            recommendations.append("✅ Stabile Compliance - Weiterhin regelmäßig überwachen")
        
        if total_issues > 10:
            recommendations.append("🔧 Viele Probleme erkannt - Systematische Überarbeitung empfohlen")
        
        recommendations.extend([
            "📊 Regelmäßige Berichte generieren für Trend-Analyse",
            "🔔 Alert-Schwellenwerte bei Bedarf anpassen",
            "⚡ Bei kritischen Problemen Expert Service nutzen"
        ])
        
        return recommendations
    
    async def get_user_dashboard(self, user_id: str) -> Dict:
        """Get monitoring dashboard data for user"""
        user_targets = await self.get_user_targets(user_id)
        
        if not user_targets:
            return {
                "total_targets": 0,
                "message": "No monitoring targets configured"
            }
        
        # Get recent scans for user targets
        user_target_ids = {target["target_id"] for target in user_targets}
        recent_scans = [
            scan for scan in self.scan_results
            if scan.target_id in user_target_ids
        ]
        
        # Calculate dashboard metrics
        total_targets = len(user_targets)
        active_targets = len([t for t in user_targets if t["status"] == "active"])
        
        if recent_scans:
            avg_score = sum(scan.compliance_score for scan in recent_scans) / len(recent_scans)
            total_alerts = sum(len(scan.alerts_triggered) for scan in recent_scans)
            last_scan = max(scan.timestamp for scan in recent_scans)
        else:
            avg_score = 0
            total_alerts = 0
            last_scan = None
        
        # Target health summary
        target_health = []
        for target in user_targets:
            target_scans = [s for s in recent_scans if s.target_id == target["target_id"]]
            if target_scans:
                latest_scan = max(target_scans, key=lambda x: x.timestamp)
                health_status = "healthy" if latest_scan.compliance_score >= 80 else "warning" if latest_scan.compliance_score >= 60 else "critical"
            else:
                health_status = "unknown"
                
            target_health.append({
                "target_id": target["target_id"],
                "website_name": target["website_name"],
                "website_url": target["website_url"],
                "health_status": health_status,
                "last_score": target_scans[-1].compliance_score if target_scans else None,
                "last_scan": target["last_scan"].isoformat() if target["last_scan"] else None
            })
        
        return {
            "total_targets": total_targets,
            "active_targets": active_targets,
            "average_compliance_score": round(avg_score, 1),
            "total_alerts": total_alerts,
            "last_scan": last_scan.isoformat() if last_scan else None,
            "target_health": target_health,
            "system_status": "operational" if active_targets > 0 else "inactive"
        }
    
    async def update_monitoring_target(self, target_id: str, updates: Dict[str, Any]) -> bool:
        """Update monitoring target configuration"""
        target = self.monitoring_targets.get(target_id)
        
        if not target:
            return False
        
        # Update allowed fields
        allowed_fields = ["website_name", "monitoring_frequency", "alert_thresholds", "notification_preferences"]
        
        for field, value in updates.items():
            if field in allowed_fields:
                target[field] = value
        
        target["updated_at"] = datetime.now()
        return True
    
    async def get_user_statistics(self, user_id: str) -> Dict:
        """Get comprehensive monitoring statistics for user"""
        user_targets = await self.get_user_targets(user_id)
        user_target_ids = {target["target_id"] for target in user_targets}
        
        # Get all scans for user targets
        user_scans = [
            scan for scan in self.scan_results
            if scan.target_id in user_target_ids
        ]
        
        if not user_scans:
            return {
                "total_scans": 0,
                "message": "No scan data available"
            }
        
        # Calculate statistics
        total_scans = len(user_scans)
        avg_score = sum(scan.compliance_score for scan in user_scans) / total_scans
        total_issues = sum(scan.issues_detected for scan in user_scans)
        total_changes = sum(len(scan.changes_detected) for scan in user_scans)
        
        # Score distribution
        score_ranges = {"0-40": 0, "41-60": 0, "61-80": 0, "81-100": 0}
        for scan in user_scans:
            if scan.compliance_score <= 40:
                score_ranges["0-40"] += 1
            elif scan.compliance_score <= 60:
                score_ranges["41-60"] += 1
            elif scan.compliance_score <= 80:
                score_ranges["61-80"] += 1
            else:
                score_ranges["81-100"] += 1
        
        # Monthly trend (last 12 months)
        monthly_data = {}
        for scan in user_scans:
            month_key = scan.timestamp.strftime("%Y-%m")
            if month_key not in monthly_data:
                monthly_data[month_key] = {"scans": 0, "avg_score": 0, "scores": []}
            monthly_data[month_key]["scans"] += 1
            monthly_data[month_key]["scores"].append(scan.compliance_score)
        
        # Calculate monthly averages
        for month_data in monthly_data.values():
            month_data["avg_score"] = sum(month_data["scores"]) / len(month_data["scores"])
            del month_data["scores"]  # Remove raw scores to save space
        
        return {
            "user_id": user_id,
            "total_targets": len(user_targets),
            "total_scans": total_scans,
            "average_compliance_score": round(avg_score, 1),
            "total_issues_detected": total_issues,
            "total_changes_detected": total_changes,
            "score_distribution": score_ranges,
            "monthly_trends": monthly_data,
            "period_covered": {
                "first_scan": min(scan.timestamp for scan in user_scans).isoformat(),
                "last_scan": max(scan.timestamp for scan in user_scans).isoformat()
            }
        }

# Global monitoring system instance
compliance_monitoring = ComplianceMonitoringSystem()