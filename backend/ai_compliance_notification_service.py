"""
AI Compliance Notification Service
Handles alerts and notifications for AI Act compliance monitoring
"""

import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)


class AIComplianceNotificationService:
    def __init__(self):
        self.smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.sender_email = os.getenv('SENDER_EMAIL', 'noreply@complyo.tech')
        self.sender_name = os.getenv('SENDER_NAME', 'Complyo AI Compliance')
        self.frontend_url = os.getenv('FRONTEND_URL', 'https://app.complyo.tech')
        self.demo_mode = not all([self.smtp_username, self.smtp_password])
        
        if self.demo_mode:
            logger.info("AI Notification Service running in DEMO MODE")
    
    def _send_email(self, to_email: str, subject: str, html_body: str, text_body: str) -> bool:
        if self.demo_mode:
            logger.info(f"[DEMO] Email to {to_email}: {subject}")
            logger.info(f"[DEMO] Body: {text_body[:200]}...")
            return True
        
        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.sender_name} <{self.sender_email}>"
            message["To"] = to_email
            
            part1 = MIMEText(text_body, "plain")
            part2 = MIMEText(html_body, "html")
            message.attach(part1)
            message.attach(part2)
            
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.smtp_username, self.smtp_password)
                server.sendmail(self.sender_email, to_email, message.as_string())
            
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
    
    async def send_compliance_alert(
        self,
        user_email: str,
        user_name: str,
        system_name: str,
        system_id: str,
        old_score: int,
        new_score: int,
        risk_category: str,
        findings: List[Dict[str, Any]] = None
    ) -> bool:
        """
        Send alert when compliance score drops significantly
        """
        
        score_change = new_score - old_score
        severity = "critical" if score_change <= -20 else "warning" if score_change <= -10 else "info"
        
        subject = f"{'🚨' if severity == 'critical' else '⚠️'} AI Compliance Alert: {system_name}"
        
        system_url = f"{self.frontend_url}/ai-compliance/systems/{system_id}"
        
        findings_html = ""
        if findings:
            findings_html = "<ul style='margin: 10px 0; padding-left: 20px;'>"
            for f in findings[:5]:
                findings_html += f"<li style='margin: 5px 0;'>{f.get('requirement', f.get('title', 'N/A'))}</li>"
            findings_html += "</ul>"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"></head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: {'#dc3545' if severity == 'critical' else '#ffc107'}; color: {'white' if severity == 'critical' else '#333'}; padding: 20px; border-radius: 8px 8px 0 0;">
                <h1 style="margin: 0; font-size: 24px;">AI Compliance Alert</h1>
                <p style="margin: 5px 0 0 0; opacity: 0.9;">Ihr KI-System benötigt Aufmerksamkeit</p>
            </div>
            
            <div style="background: #f8f9fa; padding: 20px; border-radius: 0 0 8px 8px;">
                <p>Hallo {user_name},</p>
                
                <p>Der Compliance-Score Ihres KI-Systems <strong>{system_name}</strong> hat sich verändert:</p>
                
                <div style="background: white; border-radius: 8px; padding: 20px; margin: 20px 0; text-align: center;">
                    <div style="display: inline-block; margin: 0 20px;">
                        <div style="font-size: 14px; color: #666;">Vorher</div>
                        <div style="font-size: 36px; font-weight: bold; color: #666;">{old_score}%</div>
                    </div>
                    <div style="display: inline-block; font-size: 24px; color: #666;">→</div>
                    <div style="display: inline-block; margin: 0 20px;">
                        <div style="font-size: 14px; color: #666;">Aktuell</div>
                        <div style="font-size: 36px; font-weight: bold; color: {'#dc3545' if new_score < 60 else '#ffc107' if new_score < 80 else '#28a745'};">{new_score}%</div>
                    </div>
                </div>
                
                <p><strong>Risikokategorie:</strong> {risk_category.upper()}</p>
                
                {f'<p><strong>Gefundene Probleme:</strong></p>{findings_html}' if findings_html else ''}
                
                <div style="margin-top: 30px; text-align: center;">
                    <a href="{system_url}" style="display: inline-block; background: #6366f1; color: white; padding: 12px 30px; border-radius: 6px; text-decoration: none; font-weight: bold;">
                        System überprüfen
                    </a>
                </div>
                
                <p style="margin-top: 30px; font-size: 12px; color: #666;">
                    Diese E-Mail wurde automatisch von Complyo AI Compliance gesendet.<br>
                    <a href="{self.frontend_url}/profile" style="color: #6366f1;">Benachrichtigungseinstellungen ändern</a>
                </p>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
AI Compliance Alert - {system_name}

Hallo {user_name},

Der Compliance-Score Ihres KI-Systems "{system_name}" hat sich verändert:
- Vorher: {old_score}%
- Aktuell: {new_score}%
- Risikokategorie: {risk_category.upper()}

Bitte überprüfen Sie Ihr System: {system_url}

---
Complyo AI Compliance
        """
        
        return self._send_email(user_email, subject, html_body, text_body)
    
    async def send_scan_reminder(
        self,
        user_email: str,
        user_name: str,
        systems: List[Dict[str, Any]]
    ) -> bool:
        """
        Send reminder for systems that haven't been scanned recently
        """
        
        subject = "🔍 AI Compliance: Scan-Erinnerung für Ihre KI-Systeme"
        
        systems_html = "<ul style='margin: 10px 0; padding-left: 20px;'>"
        for s in systems:
            last_scan = s.get('last_assessment_date', 'Nie')
            if last_scan and last_scan != 'Nie':
                try:
                    last_scan = datetime.fromisoformat(str(last_scan).replace('Z', '+00:00')).strftime('%d.%m.%Y')
                except:
                    pass
            systems_html += f"""
            <li style='margin: 10px 0;'>
                <strong>{s.get('name', 'Unbekannt')}</strong><br>
                <span style='color: #666; font-size: 13px;'>Letzter Scan: {last_scan}</span>
            </li>
            """
        systems_html += "</ul>"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"></head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: #6366f1; color: white; padding: 20px; border-radius: 8px 8px 0 0;">
                <h1 style="margin: 0; font-size: 24px;">Scan-Erinnerung</h1>
                <p style="margin: 5px 0 0 0; opacity: 0.9;">EU AI Act Compliance Monitoring</p>
            </div>
            
            <div style="background: #f8f9fa; padding: 20px; border-radius: 0 0 8px 8px;">
                <p>Hallo {user_name},</p>
                
                <p>Folgende KI-Systeme wurden länger nicht auf Compliance geprüft:</p>
                
                {systems_html}
                
                <p>Regelmäßige Scans sind wichtig, um die kontinuierliche Einhaltung des EU AI Acts sicherzustellen.</p>
                
                <div style="margin-top: 30px; text-align: center;">
                    <a href="{self.frontend_url}/ai-compliance" style="display: inline-block; background: #6366f1; color: white; padding: 12px 30px; border-radius: 6px; text-decoration: none; font-weight: bold;">
                        Jetzt Scans durchführen
                    </a>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
Scan-Erinnerung - EU AI Act Compliance

Hallo {user_name},

Folgende KI-Systeme wurden länger nicht auf Compliance geprüft:

{chr(10).join([f"- {s.get('name', 'Unbekannt')}" for s in systems])}

Regelmäßige Scans sind wichtig für die EU AI Act Compliance.

Dashboard: {self.frontend_url}/ai-compliance

---
Complyo AI Compliance
        """
        
        return self._send_email(user_email, subject, html_body, text_body)
    
    async def send_high_risk_alert(
        self,
        user_email: str,
        user_name: str,
        system_name: str,
        system_id: str,
        risk_category: str,
        risk_reasoning: str
    ) -> bool:
        """
        Send alert when a system is classified as high-risk or prohibited
        """
        
        is_prohibited = risk_category == 'prohibited'
        subject = f"{'🚫' if is_prohibited else '⚠️'} {'VERBOTENES' if is_prohibited else 'Hochrisiko'} KI-System erkannt: {system_name}"
        
        system_url = f"{self.frontend_url}/ai-compliance/systems/{system_id}"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"></head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: {'#dc3545' if is_prohibited else '#fd7e14'}; color: white; padding: 20px; border-radius: 8px 8px 0 0;">
                <h1 style="margin: 0; font-size: 24px;">
                    {'🚫 Verbotenes System' if is_prohibited else '⚠️ Hochrisiko-System'} erkannt
                </h1>
            </div>
            
            <div style="background: #f8f9fa; padding: 20px; border-radius: 0 0 8px 8px;">
                <p>Hallo {user_name},</p>
                
                <p>Ihr KI-System <strong>{system_name}</strong> wurde als <strong style="color: {'#dc3545' if is_prohibited else '#fd7e14'};">{risk_category.upper()}</strong> klassifiziert.</p>
                
                <div style="background: white; border: 1px solid #ddd; border-radius: 8px; padding: 15px; margin: 20px 0;">
                    <strong>Begründung:</strong>
                    <p style="margin: 10px 0 0 0; color: #555;">{risk_reasoning}</p>
                </div>
                
                {'<div style="background: #dc3545; color: white; padding: 15px; border-radius: 8px; margin: 20px 0;"><strong>ACHTUNG:</strong> Verbotene KI-Systeme dürfen in der EU nicht betrieben werden. Sofortige Maßnahmen erforderlich!</div>' if is_prohibited else ''}
                
                <div style="margin-top: 30px; text-align: center;">
                    <a href="{system_url}" style="display: inline-block; background: #6366f1; color: white; padding: 12px 30px; border-radius: 6px; text-decoration: none; font-weight: bold;">
                        Details ansehen
                    </a>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
{'VERBOTENES' if is_prohibited else 'Hochrisiko'} KI-System erkannt

Hallo {user_name},

Ihr KI-System "{system_name}" wurde als {risk_category.upper()} klassifiziert.

Begründung: {risk_reasoning}

{'ACHTUNG: Verbotene KI-Systeme dürfen in der EU nicht betrieben werden!' if is_prohibited else ''}

Details: {system_url}

---
Complyo AI Compliance
        """
        
        return self._send_email(user_email, subject, html_body, text_body)


ai_compliance_notification_service = AIComplianceNotificationService()
