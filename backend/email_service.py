"""
Complyo Email Service - Comprehensive Email Management System
Handles notifications, alerts, marketing emails, and report delivery
"""

import asyncio
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.utils import formataddr
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import os
import json
import uuid
import hashlib
from dataclasses import dataclass, asdict
from jinja2 import Environment, FileSystemLoader, Template
import aiosmtplib
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class EmailAddress:
    """Email address with optional display name"""
    email: str
    name: Optional[str] = None
    
    def __str__(self):
        if self.name:
            return formataddr((self.name, self.email))
        return self.email

@dataclass
class EmailAttachment:
    """Email attachment"""
    filename: str
    content: bytes
    content_type: str = "application/octet-stream"

@dataclass
class EmailTemplate:
    """Email template configuration"""
    template_id: str
    name: str
    subject_template: str
    html_template: str
    text_template: Optional[str] = None
    category: str = "general"
    variables: List[str] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.variables is None:
            self.variables = []

@dataclass
class EmailMessage:
    """Email message"""
    message_id: str
    to_addresses: List[EmailAddress]
    subject: str
    html_content: str
    text_content: Optional[str] = None
    from_address: Optional[EmailAddress] = None
    reply_to: Optional[EmailAddress] = None
    cc_addresses: Optional[List[EmailAddress]] = None
    bcc_addresses: Optional[List[EmailAddress]] = None
    attachments: Optional[List[EmailAttachment]] = None
    template_id: Optional[str] = None
    template_variables: Optional[Dict[str, Any]] = None
    priority: str = "normal"  # low, normal, high, urgent
    send_at: Optional[datetime] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.message_id is None:
            self.message_id = str(uuid.uuid4())

@dataclass
class EmailDeliveryResult:
    """Email delivery result"""
    message_id: str
    status: str  # pending, sent, delivered, failed, bounced
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    error_message: Optional[str] = None
    recipient_responses: Dict[str, str] = None
    
    def __post_init__(self):
        if self.recipient_responses is None:
            self.recipient_responses = {}

class EmailService:
    """Comprehensive email service for Complyo platform"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize email service with configuration"""
        
        self.config = config or self._get_default_config()
        
        # Email templates storage
        self.templates: Dict[str, EmailTemplate] = {}
        
        # Message queue and delivery tracking
        self.message_queue: List[EmailMessage] = []
        self.delivery_results: Dict[str, EmailDeliveryResult] = {}
        
        # Initialize Jinja2 template environment
        self.jinja_env = Environment(
            loader=FileSystemLoader('templates/email') if os.path.exists('templates/email') else None,
            autoescape=True
        )
        
        # Load default templates
        self._load_default_templates()
        
        # Rate limiting
        self.rate_limit_window = timedelta(minutes=1)
        self.rate_limit_max = 60  # Max emails per minute
        self.sent_times: List[datetime] = []
        
        logger.info("✉️ Email Service initialized")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default email configuration"""
        
        return {
            "smtp": {
                "host": os.environ.get("SMTP_HOST", "smtp.gmail.com"),
                "port": int(os.environ.get("SMTP_PORT", "587")),
                "use_tls": True,
                "username": os.environ.get("SMTP_USERNAME", "noreply@complyo.tech"),
                "password": os.environ.get("SMTP_PASSWORD", "demo_password"),
                "timeout": 30
            },
            "sender": {
                "default_from": EmailAddress("noreply@complyo.tech", "Complyo Platform"),
                "support_email": EmailAddress("support@complyo.tech", "Complyo Support"),
                "alerts_email": EmailAddress("alerts@complyo.tech", "Complyo Alerts"),
                "reports_email": EmailAddress("reports@complyo.tech", "Complyo Reports")
            },
            "settings": {
                "max_recipients": 50,
                "max_attachment_size": 25 * 1024 * 1024,  # 25MB
                "retry_attempts": 3,
                "retry_delay": 300,  # 5 minutes
                "enable_tracking": True,
                "enable_analytics": True
            }
        }
    
    def _load_default_templates(self):
        """Load default email templates"""
        
        # Welcome email template
        self.templates["welcome"] = EmailTemplate(
            template_id="welcome",
            name="Welcome Email",
            subject_template="Willkommen bei Complyo - Ihre Website-Compliance-Lösung! 🚀",
            html_template="""
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                    .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                    .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
                    .content { background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; }
                    .button { display: inline-block; padding: 12px 24px; background: #28a745; color: white; text-decoration: none; border-radius: 5px; font-weight: bold; }
                    .footer { text-align: center; margin-top: 30px; color: #666; font-size: 12px; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🛡️ Willkommen bei Complyo!</h1>
                        <p>Ihre professionelle Website-Compliance-Plattform</p>
                    </div>
                    <div class="content">
                        <h2>Hallo {{ user_name }}! 👋</h2>
                        <p>Vielen Dank für Ihre Registrierung bei Complyo. Wir freuen uns, Sie bei der Einhaltung aller deutschen Compliance-Anforderungen zu unterstützen.</p>
                        
                        <h3>Ihre nächsten Schritte:</h3>
                        <ul>
                            <li>✅ <strong>Erste Website scannen:</strong> Lassen Sie Ihre Website kostenlos prüfen</li>
                            <li>🤖 <strong>AI-Automatisierung nutzen:</strong> Automatische Fixes für Compliance-Probleme</li>
                            <li>📊 <strong>24/7 Monitoring:</strong> Kontinuierliche Überwachung Ihrer Compliance</li>
                            <li>📞 <strong>Expert Service:</strong> Professionelle Rechtsberatung bei Bedarf</li>
                        </ul>
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="{{ dashboard_url }}" class="button">🚀 Zum Dashboard</a>
                        </div>
                        
                        <p><strong>Ihr 7-Tage kostenloses Trial ist bereits aktiv!</strong></p>
                        
                        <div style="background: #e3f2fd; padding: 20px; border-radius: 5px; margin: 20px 0;">
                            <h4>💡 Wussten Sie schon?</h4>
                            <p>DSGVO-Verstöße können bis zu 4% des Jahresumsatzes oder 20 Millionen Euro kosten. Mit Complyo sind Sie auf der sicheren Seite!</p>
                        </div>
                    </div>
                    <div class="footer">
                        <p>Bei Fragen stehen wir Ihnen gerne zur Verfügung: <a href="mailto:support@complyo.tech">support@complyo.tech</a></p>
                        <p>© 2024 Complyo - Professionelle Website-Compliance</p>
                    </div>
                </div>
            </body>
            </html>
            """,
            category="onboarding",
            variables=["user_name", "dashboard_url", "trial_expires"]
        )
        
        # Compliance alert template
        self.templates["compliance_alert"] = EmailTemplate(
            template_id="compliance_alert",
            name="Compliance Alert",
            subject_template="🚨 Compliance-Problem erkannt: {{ website_name }}",
            html_template="""
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                    .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                    .alert-header { background: #dc3545; color: white; padding: 20px; text-align: center; border-radius: 5px; }
                    .content { background: #fff; padding: 30px; border: 1px solid #ddd; }
                    .critical { background: #f8d7da; padding: 15px; border: 1px solid #f5c6cb; border-radius: 5px; margin: 20px 0; }
                    .button { display: inline-block; padding: 12px 24px; background: #dc3545; color: white; text-decoration: none; border-radius: 5px; font-weight: bold; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="alert-header">
                        <h1>⚠️ Compliance-Alert</h1>
                        <p>Sofortige Aufmerksamkeit erforderlich</p>
                    </div>
                    <div class="content">
                        <h2>Website: {{ website_name }}</h2>
                        <p><strong>URL:</strong> {{ website_url }}</p>
                        
                        <div class="critical">
                            <h3>🚨 Kritisches Problem erkannt:</h3>
                            <p><strong>{{ alert_title }}</strong></p>
                            <p>{{ alert_description }}</p>
                            <p><strong>Compliance-Score:</strong> {{ compliance_score }}% (Schwelle: {{ threshold }}%)</p>
                        </div>
                        
                        <h3>Sofortige Maßnahmen:</h3>
                        <ul>
                            {% for action in recommended_actions %}
                            <li>{{ action }}</li>
                            {% endfor %}
                        </ul>
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="{{ fix_url }}" class="button">🔧 Problem beheben</a>
                        </div>
                        
                        <p><strong>Erkannt am:</strong> {{ detected_at }}</p>
                    </div>
                </div>
            </body>
            </html>
            """,
            category="alerts",
            variables=["website_name", "website_url", "alert_title", "alert_description", "compliance_score", "threshold", "recommended_actions", "fix_url", "detected_at"]
        )
        
        # Monthly report template
        self.templates["monthly_report"] = EmailTemplate(
            template_id="monthly_report",
            name="Monthly Compliance Report",
            subject_template="📊 Ihr Complyo Monatsbericht - {{ month_name }} {{ year }}",
            html_template="""
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                    .container { max-width: 700px; margin: 0 auto; padding: 20px; }
                    .header { background: linear-gradient(135deg, #28a745 0%, #20c997 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
                    .content { background: #f8f9fa; padding: 30px; }
                    .metrics { display: flex; justify-content: space-around; margin: 20px 0; }
                    .metric { text-align: center; padding: 20px; background: white; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                    .metric-value { font-size: 2em; font-weight: bold; color: #28a745; }
                    .target-list { background: white; padding: 20px; border-radius: 10px; margin: 20px 0; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>📊 Compliance Monatsbericht</h1>
                        <p>{{ month_name }} {{ year }}</p>
                    </div>
                    <div class="content">
                        <h2>Hallo {{ user_name }}! 👋</h2>
                        
                        <p>Hier ist Ihr monatlicher Compliance-Überblick:</p>
                        
                        <div class="metrics">
                            <div class="metric">
                                <div class="metric-value">{{ total_targets }}</div>
                                <div>Überwachte Websites</div>
                            </div>
                            <div class="metric">
                                <div class="metric-value">{{ avg_score }}%</div>
                                <div>Durchschn. Score</div>
                            </div>
                            <div class="metric">
                                <div class="metric-value">{{ total_scans }}</div>
                                <div>Scans durchgeführt</div>
                            </div>
                            <div class="metric">
                                <div class="metric-value">{{ issues_fixed }}</div>
                                <div>Probleme behoben</div>
                            </div>
                        </div>
                        
                        <div class="target-list">
                            <h3>📈 Website-Performance:</h3>
                            {% for target in targets %}
                            <div style="padding: 10px; border-bottom: 1px solid #eee;">
                                <strong>{{ target.name }}</strong> ({{ target.url }})
                                <br>Score: {{ target.score }}% 
                                <span style="color: {% if target.trend == 'improving' %}green{% elif target.trend == 'declining' %}red{% else %}orange{% endif %};">
                                    {{ target.trend_icon }} {{ target.trend }}
                                </span>
                            </div>
                            {% endfor %}
                        </div>
                        
                        <h3>🎯 Empfehlungen für {{ next_month }}:</h3>
                        <ul>
                            {% for recommendation in recommendations %}
                            <li>{{ recommendation }}</li>
                            {% endfor %}
                        </ul>
                    </div>
                </div>
            </body>
            </html>
            """,
            category="reports",
            variables=["user_name", "month_name", "year", "next_month", "total_targets", "avg_score", "total_scans", "issues_fixed", "targets", "recommendations"]
        )
        
        # Expert consultation email template
        self.templates["expert_consultation"] = EmailTemplate(
            template_id="expert_consultation",
            name="Expert Consultation Scheduled",
            subject_template="👨‍💼 Ihr Expert Service Termin wurde bestätigt",
            html_template="""
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                    .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                    .header { background: #6f42c1; color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
                    .content { background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; }
                    .appointment { background: white; padding: 20px; border-radius: 10px; border-left: 5px solid #6f42c1; margin: 20px 0; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>👨‍💼 Expert Service</h1>
                        <p>Ihr Beratungstermin wurde bestätigt</p>
                    </div>
                    <div class="content">
                        <h2>Hallo {{ client_name }}! 👋</h2>
                        
                        <p>Vielen Dank für Ihr Vertrauen in unseren Expert Service. Ihr Beratungstermin wurde bestätigt:</p>
                        
                        <div class="appointment">
                            <h3>📅 Termindetails:</h3>
                            <p><strong>Datum:</strong> {{ appointment_date }}</p>
                            <p><strong>Uhrzeit:</strong> {{ appointment_time }}</p>
                            <p><strong>Dauer:</strong> {{ duration }} Minuten</p>
                            <p><strong>Expert:</strong> {{ expert_name }} ({{ expert_title }})</p>
                            <p><strong>Thema:</strong> {{ consultation_topic }}</p>
                        </div>
                        
                        <h3>🔗 Zugangslink:</h3>
                        <p><a href="{{ meeting_link }}" style="color: #6f42c1; font-weight: bold;">{{ meeting_link }}</a></p>
                        
                        <h3>📋 Vorbereitung:</h3>
                        <ul>
                            <li>Halten Sie Ihre Website-URLs bereit</li>
                            <li>Liste spezifischer Compliance-Fragen</li>
                            <li>Aktuelle Scan-Berichte (falls vorhanden)</li>
                        </ul>
                        
                        <p><strong>Kontakt bei Fragen:</strong> <a href="mailto:{{ expert_email }}">{{ expert_email }}</a></p>
                    </div>
                </div>
            </body>
            </html>
            """,
            category="expert_service",
            variables=["client_name", "appointment_date", "appointment_time", "duration", "expert_name", "expert_title", "consultation_topic", "meeting_link", "expert_email"]
        )
        
        logger.info(f"📧 Loaded {len(self.templates)} default email templates")
    
    async def send_email(self, message: EmailMessage) -> EmailDeliveryResult:
        """Send individual email message"""
        
        try:
            # Rate limiting check
            if not self._check_rate_limit():
                return EmailDeliveryResult(
                    message_id=message.message_id,
                    status="failed",
                    error_message="Rate limit exceeded"
                )
            
            # Validate message
            validation_result = self._validate_message(message)
            if not validation_result["valid"]:
                return EmailDeliveryResult(
                    message_id=message.message_id,
                    status="failed",
                    error_message=validation_result["error"]
                )
            
            # Process template if specified
            if message.template_id and message.template_variables:
                processed_message = await self._process_template(message)
                if processed_message:
                    message = processed_message
            
            # Create MIME message
            mime_message = self._create_mime_message(message)
            
            # Send email
            if os.environ.get("DEMO_MODE", "true").lower() == "true":
                # Demo mode - simulate sending
                result = self._simulate_email_sending(message)
            else:
                # Real email sending
                result = await self._send_smtp_email(mime_message, message)
            
            # Track delivery
            self.delivery_results[message.message_id] = result
            self.sent_times.append(datetime.now())
            
            return result
            
        except Exception as e:
            logger.error(f"Email sending failed: {str(e)}")
            return EmailDeliveryResult(
                message_id=message.message_id,
                status="failed",
                error_message=str(e)
            )
    
    async def send_bulk_emails(self, messages: List[EmailMessage]) -> Dict[str, EmailDeliveryResult]:
        """Send multiple emails in batch"""
        
        results = {}
        
        # Process emails in batches to respect rate limits
        batch_size = min(10, self.rate_limit_max // 6)  # Conservative batching
        
        for i in range(0, len(messages), batch_size):
            batch = messages[i:i + batch_size]
            
            # Send batch concurrently
            tasks = [self.send_email(message) for message in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Collect results
            for message, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    results[message.message_id] = EmailDeliveryResult(
                        message_id=message.message_id,
                        status="failed",
                        error_message=str(result)
                    )
                else:
                    results[message.message_id] = result
            
            # Rate limiting delay between batches
            if i + batch_size < len(messages):
                await asyncio.sleep(2)
        
        logger.info(f"📧 Bulk email completed: {len(results)} messages processed")
        return results
    
    async def send_template_email(self, template_id: str, to_email: str, variables: Dict[str, Any], **kwargs) -> EmailDeliveryResult:
        """Send email using template"""
        
        if template_id not in self.templates:
            return EmailDeliveryResult(
                message_id=str(uuid.uuid4()),
                status="failed",
                error_message=f"Template '{template_id}' not found"
            )
        
        template = self.templates[template_id]
        
        # Create message from template
        message = EmailMessage(
            message_id=str(uuid.uuid4()),
            to_addresses=[EmailAddress(to_email)],
            subject="",  # Will be filled by template processing
            html_content="",  # Will be filled by template processing
            template_id=template_id,
            template_variables=variables,
            **kwargs
        )
        
        return await self.send_email(message)
    
    def _check_rate_limit(self) -> bool:
        """Check if rate limit allows sending email"""
        
        now = datetime.now()
        cutoff = now - self.rate_limit_window
        
        # Remove old entries
        self.sent_times = [t for t in self.sent_times if t > cutoff]
        
        return len(self.sent_times) < self.rate_limit_max
    
    def _validate_message(self, message: EmailMessage) -> Dict[str, Any]:
        """Validate email message"""
        
        if not message.to_addresses:
            return {"valid": False, "error": "No recipients specified"}
        
        if len(message.to_addresses) > self.config["settings"]["max_recipients"]:
            return {"valid": False, "error": "Too many recipients"}
        
        if not message.subject and not message.template_id:
            return {"valid": False, "error": "No subject specified"}
        
        if not message.html_content and not message.text_content and not message.template_id:
            return {"valid": False, "error": "No content specified"}
        
        # Validate attachment sizes
        if message.attachments:
            total_size = sum(len(att.content) for att in message.attachments)
            if total_size > self.config["settings"]["max_attachment_size"]:
                return {"valid": False, "error": "Attachments too large"}
        
        return {"valid": True}
    
    async def _process_template(self, message: EmailMessage) -> Optional[EmailMessage]:
        """Process email template with variables"""
        
        template = self.templates.get(message.template_id)
        if not template:
            return None
        
        try:
            # Process subject
            subject_template = Template(template.subject_template)
            message.subject = subject_template.render(message.template_variables)
            
            # Process HTML content
            html_template = Template(template.html_template)
            message.html_content = html_template.render(message.template_variables)
            
            # Process text content if available
            if template.text_template:
                text_template = Template(template.text_template)
                message.text_content = text_template.render(message.template_variables)
            
            return message
            
        except Exception as e:
            logger.error(f"Template processing failed: {str(e)}")
            return None
    
    def _create_mime_message(self, message: EmailMessage) -> MIMEMultipart:
        """Create MIME message for SMTP sending"""
        
        mime_message = MIMEMultipart('alternative')
        
        # Set headers
        mime_message['Subject'] = message.subject
        mime_message['From'] = str(message.from_address or self.config["sender"]["default_from"])
        mime_message['To'] = ', '.join(str(addr) for addr in message.to_addresses)
        
        if message.reply_to:
            mime_message['Reply-To'] = str(message.reply_to)
        
        if message.cc_addresses:
            mime_message['Cc'] = ', '.join(str(addr) for addr in message.cc_addresses)
        
        # Set priority
        if message.priority == "high":
            mime_message['X-Priority'] = '2'
        elif message.priority == "urgent":
            mime_message['X-Priority'] = '1'
        
        # Add content
        if message.text_content:
            text_part = MIMEText(message.text_content, 'plain', 'utf-8')
            mime_message.attach(text_part)
        
        if message.html_content:
            html_part = MIMEText(message.html_content, 'html', 'utf-8')
            mime_message.attach(html_part)
        
        # Add attachments
        if message.attachments:
            for attachment in message.attachments:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.content)
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {attachment.filename}'
                )
                mime_message.attach(part)
        
        return mime_message
    
    async def _send_smtp_email(self, mime_message: MIMEMultipart, message: EmailMessage) -> EmailDeliveryResult:
        """Send email via SMTP"""
        
        try:
            smtp_config = self.config["smtp"]
            
            # Create SMTP connection
            smtp = aiosmtplib.SMTP(
                hostname=smtp_config["host"],
                port=smtp_config["port"],
                timeout=smtp_config["timeout"]
            )
            
            await smtp.connect()
            
            if smtp_config["use_tls"]:
                await smtp.starttls()
            
            if smtp_config["username"] and smtp_config["password"]:
                await smtp.login(smtp_config["username"], smtp_config["password"])
            
            # Send message
            from_addr = str(message.from_address or self.config["sender"]["default_from"])
            to_addrs = [addr.email for addr in message.to_addresses]
            
            if message.cc_addresses:
                to_addrs.extend([addr.email for addr in message.cc_addresses])
            
            if message.bcc_addresses:
                to_addrs.extend([addr.email for addr in message.bcc_addresses])
            
            await smtp.send_message(mime_message, from_addr=from_addr, to_addrs=to_addrs)
            await smtp.quit()
            
            return EmailDeliveryResult(
                message_id=message.message_id,
                status="sent",
                sent_at=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"SMTP sending failed: {str(e)}")
            return EmailDeliveryResult(
                message_id=message.message_id,
                status="failed",
                error_message=str(e)
            )
    
    def _simulate_email_sending(self, message: EmailMessage) -> EmailDeliveryResult:
        """Simulate email sending for demo mode"""
        
        logger.info(f"📧 [DEMO] Email simulated: {message.subject} -> {[str(addr) for addr in message.to_addresses]}")
        
        # Simulate delivery time
        import time
        time.sleep(0.1)
        
        return EmailDeliveryResult(
            message_id=message.message_id,
            status="sent",
            sent_at=datetime.now(),
            delivered_at=datetime.now()
        )
    
    def get_delivery_status(self, message_id: str) -> Optional[EmailDeliveryResult]:
        """Get delivery status for message"""
        return self.delivery_results.get(message_id)
    
    def get_template(self, template_id: str) -> Optional[EmailTemplate]:
        """Get email template by ID"""
        return self.templates.get(template_id)
    
    def list_templates(self, category: str = None) -> List[EmailTemplate]:
        """List available email templates"""
        
        templates = list(self.templates.values())
        
        if category:
            templates = [t for t in templates if t.category == category]
        
        return templates
    
    def add_template(self, template: EmailTemplate) -> bool:
        """Add new email template"""
        
        try:
            # Validate template
            if not template.template_id or not template.subject_template or not template.html_template:
                return False
            
            self.templates[template.template_id] = template
            logger.info(f"📧 Email template added: {template.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add template: {str(e)}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get email service statistics"""
        
        total_sent = len(self.delivery_results)
        successful = len([r for r in self.delivery_results.values() if r.status in ["sent", "delivered"]])
        failed = len([r for r in self.delivery_results.values() if r.status == "failed"])
        
        # Recent activity (last 24 hours)
        recent_cutoff = datetime.now() - timedelta(hours=24)
        recent_sent = len([r for r in self.delivery_results.values() if r.sent_at and r.sent_at > recent_cutoff])
        
        return {
            "total_emails_sent": total_sent,
            "successful_deliveries": successful,
            "failed_deliveries": failed,
            "success_rate": (successful / total_sent * 100) if total_sent > 0 else 0,
            "recent_24h": recent_sent,
            "templates_available": len(self.templates),
            "rate_limit_status": {
                "current_rate": len(self.sent_times),
                "max_rate": self.rate_limit_max,
                "window_minutes": self.rate_limit_window.total_seconds() / 60
            }
        }

# Global email service instance
email_service = EmailService()

# Convenience functions for common email types
async def send_welcome_email(user_email: str, user_name: str, dashboard_url: str) -> EmailDeliveryResult:
    """Send welcome email to new user"""
    
    return await email_service.send_template_email(
        template_id="welcome",
        to_email=user_email,
        variables={
            "user_name": user_name,
            "dashboard_url": dashboard_url,
            "trial_expires": (datetime.now() + timedelta(days=7)).strftime("%d.%m.%Y")
        }
    )

async def send_compliance_alert(user_email: str, website_name: str, website_url: str, alert_data: Dict[str, Any]) -> EmailDeliveryResult:
    """Send compliance alert email"""
    
    return await email_service.send_template_email(
        template_id="compliance_alert",
        to_email=user_email,
        variables={
            "website_name": website_name,
            "website_url": website_url,
            "alert_title": alert_data.get("title", "Compliance-Problem erkannt"),
            "alert_description": alert_data.get("description", ""),
            "compliance_score": alert_data.get("score", 0),
            "threshold": alert_data.get("threshold", 70),
            "recommended_actions": alert_data.get("actions", []),
            "fix_url": alert_data.get("fix_url", ""),
            "detected_at": datetime.now().strftime("%d.%m.%Y %H:%M")
        },
        priority="high"
    )

async def send_monthly_report(user_email: str, user_name: str, report_data: Dict[str, Any]) -> EmailDeliveryResult:
    """Send monthly compliance report"""
    
    now = datetime.now()
    
    return await email_service.send_template_email(
        template_id="monthly_report",
        to_email=user_email,
        variables={
            "user_name": user_name,
            "month_name": now.strftime("%B"),
            "year": now.year,
            "next_month": (now.replace(day=1) + timedelta(days=32)).strftime("%B"),
            **report_data
        }
    )

async def send_expert_consultation_confirmation(client_email: str, appointment_data: Dict[str, Any]) -> EmailDeliveryResult:
    """Send expert consultation confirmation email"""
    
    return await email_service.send_template_email(
        template_id="expert_consultation",
        to_email=client_email,
        variables=appointment_data,
        from_address=email_service.config["sender"]["support_email"],
        priority="high"
    )