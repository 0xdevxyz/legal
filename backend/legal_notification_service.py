"""
Legal News Notification Service
Versendet E-Mail-Benachrichtigungen bei wichtigen Gesetzesänderungen
mit Nutzer-Bestätigungsflow (Double-Opt-In für Aktionen)
"""

import asyncio
import asyncpg
import secrets
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import ssl
import os
import logging
from jinja2 import Template

logger = logging.getLogger(__name__)


class LegalNewsNotificationService:
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
        self.smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.sender_email = os.getenv('SENDER_EMAIL', 'noreply@complyo.tech')
        self.sender_name = os.getenv('SENDER_NAME', 'Complyo Legal Updates')
        self.frontend_url = os.getenv('FRONTEND_URL', 'https://app.complyo.tech')
        self.demo_mode = not all([self.smtp_username, self.smtp_password])
        
    async def process_new_legal_changes(self) -> Dict[str, Any]:
        """
        Verarbeitet neue Gesetzesänderungen und versendet Benachrichtigungen
        Wird vom Cronjob aufgerufen
        """
        results = {
            "processed": 0,
            "notifications_created": 0,
            "emails_sent": 0,
            "errors": []
        }
        
        try:
            async with self.db_pool.acquire() as conn:
                unprocessed_news = await conn.fetch("""
                    SELECT ln.* FROM legal_news ln
                    LEFT JOIN legal_change_notifications lcn ON ln.id = lcn.legal_news_id
                    WHERE lcn.id IS NULL
                    AND ln.is_active = TRUE
                    AND ln.published_date >= CURRENT_TIMESTAMP - INTERVAL '7 days'
                    AND ln.severity IN ('critical', 'warning')
                    ORDER BY ln.severity DESC, ln.published_date DESC
                    LIMIT 50
                """)
                
                for news in unprocessed_news:
                    results["processed"] += 1
                    
                    affected_users = await self._get_affected_users(conn, news)
                    
                    for user in affected_users:
                        try:
                            notification_id = await self._create_notification(
                                conn, user, news
                            )
                            results["notifications_created"] += 1
                            
                            if await self._should_send_instant(user, news):
                                sent = await self._send_notification_email(
                                    conn, notification_id, user, news
                                )
                                if sent:
                                    results["emails_sent"] += 1
                                    
                        except Exception as e:
                            error_msg = f"Error notifying user {user['id']}: {str(e)}"
                            logger.error(error_msg)
                            results["errors"].append(error_msg)
                            
        except Exception as e:
            logger.error(f"Error in process_new_legal_changes: {e}")
            results["errors"].append(str(e))
            
        return results
    
    async def _get_affected_users(
        self, 
        conn: asyncpg.Connection, 
        news: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Ermittelt alle Nutzer, die von dieser Änderung betroffen sein könnten"""
        users = await conn.fetch("""
            SELECT 
                u.id, u.email, u.firebase_uid,
                COALESCE(ulns.email_enabled, TRUE) as email_enabled,
                COALESCE(ulns.min_severity, 'medium') as min_severity,
                COALESCE(ulns.notify_areas, ARRAY['dsgvo', 'ttdsg', 'cookie', 'impressum', 'barrierefreiheit', 'ai_act']) as notify_areas,
                COALESCE(ulns.instant_for_critical, TRUE) as instant_for_critical,
                COALESCE(ulns.digest_frequency, 'daily') as digest_frequency
            FROM users u
            LEFT JOIN user_legal_notification_settings ulns ON u.id = ulns.user_id
            WHERE u.email_verified = TRUE
            AND u.is_active = TRUE
            AND COALESCE(ulns.email_enabled, TRUE) = TRUE
        """)
        
        severity_order = {'critical': 4, 'warning': 3, 'high': 2, 'medium': 1, 'low': 0, 'info': 0}
        news_severity = severity_order.get(news['severity'], 0)
        
        affected = []
        for user in users:
            user_min_severity = severity_order.get(user['min_severity'], 1)
            if news_severity >= user_min_severity:
                affected.append(dict(user))
                
        return affected
    
    async def _should_send_instant(
        self, 
        user: Dict[str, Any], 
        news: Dict[str, Any]
    ) -> bool:
        """Prüft ob sofortige Benachrichtigung gesendet werden soll"""
        if news['severity'] == 'critical' and user.get('instant_for_critical', True):
            return True
        if user.get('digest_frequency') == 'instant':
            return True
        return False
    
    async def _create_notification(
        self, 
        conn: asyncpg.Connection,
        user: Dict[str, Any],
        news: Dict[str, Any]
    ) -> int:
        """Erstellt einen Notification-Eintrag in der Datenbank"""
        confirmation_token = secrets.token_urlsafe(32)
        
        action_deadline = None
        if news['severity'] == 'critical':
            action_deadline = datetime.now() + timedelta(days=7)
        elif news['severity'] == 'warning':
            action_deadline = datetime.now() + timedelta(days=14)
        
        notification_id = await conn.fetchval("""
            INSERT INTO legal_change_notifications (
                user_id, legal_news_id, notification_type, severity,
                status, confirmation_token, action_required, action_deadline
            ) VALUES ($1, $2, 'email', $3, 'pending', $4, $5, $6)
            RETURNING id
        """, 
            user['id'], 
            news['id'], 
            news['severity'],
            confirmation_token,
            news['severity'] in ('critical', 'warning'),
            action_deadline
        )
        
        return notification_id
    
    async def _send_notification_email(
        self,
        conn: asyncpg.Connection,
        notification_id: int,
        user: Dict[str, Any],
        news: Dict[str, Any]
    ) -> bool:
        """Versendet die E-Mail-Benachrichtigung"""
        try:
            notification = await conn.fetchrow(
                "SELECT * FROM legal_change_notifications WHERE id = $1",
                notification_id
            )
            
            confirm_url = f"{self.frontend_url}/legal/confirm/{notification['confirmation_token']}"
            dismiss_url = f"{self.frontend_url}/legal/dismiss/{notification['confirmation_token']}"
            
            subject = self._get_email_subject(news)
            html_body = self._get_notification_email_template(user, news, confirm_url, dismiss_url)
            text_body = self._get_notification_email_text(user, news, confirm_url, dismiss_url)
            
            sent = await self._send_email(user['email'], subject, html_body, text_body)
            
            if sent:
                await conn.execute("""
                    UPDATE legal_change_notifications
                    SET status = 'sent', sent_at = CURRENT_TIMESTAMP
                    WHERE id = $1
                """, notification_id)
                
            return sent
            
        except Exception as e:
            logger.error(f"Error sending notification email: {e}")
            return False
    
    def _get_email_subject(self, news: Dict[str, Any]) -> str:
        """Generiert den E-Mail-Betreff basierend auf Severity"""
        severity_prefix = {
            'critical': '[DRINGEND]',
            'warning': '[WICHTIG]',
            'high': '[Wichtig]',
            'medium': '[Info]',
            'low': '[Info]',
            'info': ''
        }
        prefix = severity_prefix.get(news['severity'], '')
        return f"{prefix} Gesetzesänderung: {news['title'][:60]}..."
    
    def _get_notification_email_template(
        self, 
        user: Dict[str, Any], 
        news: Dict[str, Any],
        confirm_url: str,
        dismiss_url: str
    ) -> str:
        """HTML-Template für Legal News Benachrichtigung"""
        severity_colors = {
            'critical': '#dc3545',
            'warning': '#fd7e14',
            'high': '#ffc107',
            'medium': '#17a2b8',
            'low': '#6c757d',
            'info': '#6c757d'
        }
        
        severity_labels = {
            'critical': 'KRITISCH - Sofortiger Handlungsbedarf',
            'warning': 'WARNUNG - Handlungsbedarf',
            'high': 'Wichtig',
            'medium': 'Information',
            'low': 'Hinweis',
            'info': 'Information'
        }
        
        color = severity_colors.get(news['severity'], '#6c757d')
        label = severity_labels.get(news['severity'], 'Information')
        
        template = Template("""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gesetzesänderung - Complyo</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f5f5f5;">
    <div style="background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
        <div style="background: {{ color }}; color: white; padding: 20px; text-align: center;">
            <h1 style="margin: 0; font-size: 24px;">Complyo Legal Update</h1>
            <p style="margin: 10px 0 0 0; font-size: 14px; opacity: 0.9;">{{ severity_label }}</p>
        </div>
        
        <div style="padding: 30px;">
            <h2 style="color: #333; margin-top: 0; font-size: 20px;">{{ title }}</h2>
            
            <div style="background: #f8f9fa; border-left: 4px solid {{ color }}; padding: 15px; margin: 20px 0; border-radius: 0 4px 4px 0;">
                <p style="margin: 0; font-size: 14px;">{{ summary }}</p>
            </div>
            
            <div style="margin: 20px 0;">
                <p style="margin: 0 0 5px 0; font-size: 12px; color: #666;">
                    <strong>Quelle:</strong> {{ source }}
                </p>
                <p style="margin: 0 0 5px 0; font-size: 12px; color: #666;">
                    <strong>Veröffentlicht:</strong> {{ published_date }}
                </p>
                {% if url %}
                <p style="margin: 0; font-size: 12px;">
                    <a href="{{ url }}" style="color: #667eea;">Originalartikel lesen</a>
                </p>
                {% endif %}
            </div>
            
            <div style="background: #fff3cd; border: 1px solid #ffc107; padding: 15px; border-radius: 4px; margin: 20px 0;">
                <h4 style="margin: 0 0 10px 0; color: #856404;">Was bedeutet das für Sie?</h4>
                <p style="margin: 0; font-size: 14px; color: #856404;">
                    Diese Änderung könnte Auswirkungen auf Ihre Website-Compliance haben. 
                    Bitte prüfen Sie, ob Handlungsbedarf besteht.
                </p>
            </div>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{{ confirm_url }}" 
                   style="background: {{ color }}; 
                          color: white; 
                          text-decoration: none; 
                          padding: 15px 30px; 
                          border-radius: 25px; 
                          font-weight: bold; 
                          display: inline-block;
                          margin: 5px;">
                    Zur Kenntnis genommen
                </a>
                <br><br>
                <a href="{{ dismiss_url }}" 
                   style="color: #666; 
                          text-decoration: underline; 
                          font-size: 12px;">
                    Nicht relevant für mich
                </a>
            </div>
            
            <div style="background: #e3f2fd; border-radius: 4px; padding: 15px; margin-top: 20px;">
                <h4 style="margin: 0 0 10px 0; color: #1976d2;">Benötigen Sie Unterstützung?</h4>
                <p style="margin: 0; font-size: 14px;">
                    Mit Complyo Pro können Sie Compliance-Änderungen automatisch analysieren 
                    und mit KI-Unterstützung umsetzen lassen.
                </p>
                <a href="{{ frontend_url }}/upgrade" style="color: #1976d2; font-weight: bold;">
                    Mehr erfahren
                </a>
            </div>
        </div>
        
        <div style="background: #f8f9fa; padding: 20px; text-align: center; font-size: 12px; color: #666;">
            <p style="margin: 0 0 10px 0;">
                <a href="{{ frontend_url }}/settings/notifications" style="color: #667eea;">
                    Benachrichtigungseinstellungen ändern
                </a>
            </p>
            <p style="margin: 0;">
                Complyo GmbH | 
                <a href="mailto:datenschutz@complyo.tech" style="color: #667eea;">datenschutz@complyo.tech</a>
            </p>
        </div>
    </div>
</body>
</html>
        """)
        
        return template.render(
            color=color,
            severity_label=label,
            title=news['title'],
            summary=news['summary'] or news['content'][:300] + '...',
            source=news['source'],
            published_date=news['published_date'].strftime('%d.%m.%Y'),
            url=news.get('url', ''),
            confirm_url=confirm_url,
            dismiss_url=dismiss_url,
            frontend_url=self.frontend_url
        )
    
    def _get_notification_email_text(
        self, 
        user: Dict[str, Any], 
        news: Dict[str, Any],
        confirm_url: str,
        dismiss_url: str
    ) -> str:
        """Plain-Text Version der Benachrichtigung"""
        severity_labels = {
            'critical': 'KRITISCH - Sofortiger Handlungsbedarf',
            'warning': 'WARNUNG - Handlungsbedarf',
            'high': 'Wichtig',
            'medium': 'Information',
            'low': 'Hinweis',
            'info': 'Information'
        }
        
        return f"""
COMPLYO LEGAL UPDATE
====================
{severity_labels.get(news['severity'], 'Information')}

{news['title']}

{news['summary'] or news['content'][:500]}

Quelle: {news['source']}
Veröffentlicht: {news['published_date'].strftime('%d.%m.%Y')}
{f"Originalartikel: {news['url']}" if news.get('url') else ""}

---

WAS BEDEUTET DAS FÜR SIE?
Diese Änderung könnte Auswirkungen auf Ihre Website-Compliance haben.
Bitte prüfen Sie, ob Handlungsbedarf besteht.

Zur Kenntnis genommen: {confirm_url}
Nicht relevant für mich: {dismiss_url}

---

Benachrichtigungseinstellungen: {self.frontend_url}/settings/notifications

Complyo GmbH | datenschutz@complyo.tech
        """
    
    async def _send_email(
        self, 
        to_email: str, 
        subject: str, 
        html_body: str, 
        text_body: str
    ) -> bool:
        """Sendet E-Mail"""
        if self.demo_mode:
            logger.info(f"[DEMO] Would send email to {to_email}: {subject}")
            return True
            
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.sender_name} <{self.sender_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(text_body, 'plain', 'utf-8'))
            msg.attach(MIMEText(html_body, 'html', 'utf-8'))
            
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.smtp_username, self.smtp_password)
                server.sendmail(self.sender_email, to_email, msg.as_string())
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"SMTP error sending email to {to_email}: {str(e)}")
            return False
    
    async def confirm_notification(self, token: str) -> Dict[str, Any]:
        """Bestätigt eine Benachrichtigung (User hat zur Kenntnis genommen)"""
        try:
            async with self.db_pool.acquire() as conn:
                notification = await conn.fetchrow("""
                    UPDATE legal_change_notifications
                    SET status = 'confirmed', confirmed_at = CURRENT_TIMESTAMP
                    WHERE confirmation_token = $1
                    AND status IN ('pending', 'sent')
                    RETURNING id, user_id, legal_news_id
                """, token)
                
                if not notification:
                    return {"success": False, "error": "Token ungültig oder bereits verwendet"}
                
                news = await conn.fetchrow(
                    "SELECT * FROM legal_news WHERE id = $1",
                    notification['legal_news_id']
                )
                
                return {
                    "success": True,
                    "message": "Benachrichtigung bestätigt",
                    "news_title": news['title'] if news else None
                }
                
        except Exception as e:
            logger.error(f"Error confirming notification: {e}")
            return {"success": False, "error": str(e)}
    
    async def dismiss_notification(self, token: str) -> Dict[str, Any]:
        """Markiert Benachrichtigung als nicht relevant"""
        try:
            async with self.db_pool.acquire() as conn:
                notification = await conn.fetchrow("""
                    UPDATE legal_change_notifications
                    SET status = 'dismissed', confirmed_at = CURRENT_TIMESTAMP
                    WHERE confirmation_token = $1
                    AND status IN ('pending', 'sent')
                    RETURNING id, user_id, legal_news_id
                """, token)
                
                if not notification:
                    return {"success": False, "error": "Token ungültig oder bereits verwendet"}
                
                return {
                    "success": True,
                    "message": "Als nicht relevant markiert"
                }
                
        except Exception as e:
            logger.error(f"Error dismissing notification: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_pending_notifications(self, user_id: int) -> List[Dict[str, Any]]:
        """Holt alle ausstehenden Benachrichtigungen für einen User"""
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT 
                        lcn.id,
                        lcn.severity,
                        lcn.status,
                        lcn.action_required,
                        lcn.action_deadline,
                        lcn.sent_at,
                        ln.title,
                        ln.summary,
                        ln.source,
                        ln.url,
                        ln.published_date
                    FROM legal_change_notifications lcn
                    JOIN legal_news ln ON lcn.legal_news_id = ln.id
                    WHERE lcn.user_id = $1
                    AND lcn.status IN ('pending', 'sent')
                    ORDER BY 
                        CASE lcn.severity 
                            WHEN 'critical' THEN 1 
                            WHEN 'warning' THEN 2 
                            ELSE 3 
                        END,
                        lcn.sent_at DESC
                """, user_id)
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Error getting pending notifications: {e}")
            return []
    
    async def send_daily_digest(self) -> Dict[str, Any]:
        """Versendet tägliche Digest-E-Mails"""
        results = {"users_processed": 0, "emails_sent": 0, "errors": []}
        
        try:
            async with self.db_pool.acquire() as conn:
                users = await conn.fetch("""
                    SELECT DISTINCT u.id, u.email
                    FROM users u
                    JOIN user_legal_notification_settings ulns ON u.id = ulns.user_id
                    WHERE ulns.digest_frequency = 'daily'
                    AND ulns.email_enabled = TRUE
                    AND u.is_active = TRUE
                """)
                
                for user in users:
                    pending = await self.get_pending_notifications(user['id'])
                    if pending:
                        results["users_processed"] += 1
                        
        except Exception as e:
            logger.error(f"Error in send_daily_digest: {e}")
            results["errors"].append(str(e))
            
        return results


legal_notification_service: Optional[LegalNewsNotificationService] = None

def init_legal_notification_service(db_pool: asyncpg.Pool):
    """Initialisiert den Legal Notification Service"""
    global legal_notification_service
    legal_notification_service = LegalNewsNotificationService(db_pool)
    return legal_notification_service
