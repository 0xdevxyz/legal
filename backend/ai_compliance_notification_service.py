"""
AI Compliance Notification Service
Handles alerts and notifications for AI Act compliance monitoring
"""

import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List
from datetime import datetime
import logging

from adressen import dashboard_url
import mail_layout

logger = logging.getLogger(__name__)


# Risikoklassen des AI Act, wie sie in der Mail stehen. Vorher stand der
# Datenbankwert in Grossbuchstaben da ("als HIGH eingestuft").
RISIKOKLASSE = {
    "prohibited": "verboten",
    "high": "Hochrisiko",
    "limited": "begrenztes Risiko",
    "minimal": "minimales Risiko",
}


def _risikoklasse(wert) -> str:
    return RISIKOKLASSE.get(str(wert).lower(), str(wert))


class AIComplianceNotificationService:
    def __init__(self):
        self.smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.sender_email = os.getenv('SENDER_EMAIL', 'noreply@complyo.de')
        self.sender_name = os.getenv('SENDER_NAME', 'Complyo AI Compliance')
        # Alle Links dieser Mails gehen ins Dashboard (adressen.py).
        self.frontend_url = dashboard_url()
        self.environment = os.getenv('ENVIRONMENT', 'development')
        self.demo_mode = not all([self.smtp_username, self.smtp_password])

        if self.demo_mode:
            logger.info("AI Notification Service running in DEMO MODE")

    def _send_email(self, to_email: str, subject: str, html_body: str, text_body: str) -> bool:
        if self.demo_mode:
            # Demo-Modus in Produktion ist ein Konfigurationsfehler — ehrlich
            # False zurückgeben statt "verschickt" vorzutäuschen.
            if self.environment.lower() in ('production', 'prod'):
                logger.error(
                    "MAIL NICHT VERSANDT (Demo-Modus in Produktion): an %s, "
                    "Betreff '%s' — SMTP_USERNAME/SMTP_PASSWORD fehlen",
                    to_email, subject,
                )
                return False
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
        
        name = mail_layout.escape(system_name or "")
        treffer = [mail_layout.escape(str(f.get('requirement', f.get('title', 'N/A'))))
                   for f in (findings or [])[:5]]
        html_body = mail_layout.seite(
            f"KI-Compliance: {system_name}",
            f"Der Compliance-Score von {system_name} ist von {old_score} auf {new_score} % gesunken.",
            mail_layout.kopf("KI-Compliance", f"Score von {name} gesunken"),
            mail_layout.text(
                f"Hallo {mail_layout.escape(user_name or '')},",
                f"der Compliance-Score Ihres KI-Systems <strong>{name}</strong> hat sich verändert.",
            ),
            mail_layout.angaben([
                ("Vorher", f"{old_score} %"),
                ("Aktuell", f"<strong>{new_score} %</strong>"),
                ("Risikokategorie", mail_layout.escape(_risikoklasse(risk_category))),
            ]),
            mail_layout.liste("Gefundene Probleme", treffer) if treffer else "",
            mail_layout.aktion("", "System überprüfen",
                               mail_layout.escape(system_url, quote=True)),
            mail_layout.gruss(),
            mail_layout.fuss(
                "Diese E-Mail wurde automatisch von complyo gesendet. "
                f'<a href="{mail_layout.escape(self.frontend_url + "/profile", quote=True)}" '
                'style="color:#5b6b78;">Benachrichtigungseinstellungen ändern</a>',
                mail_layout.rechtliches(),
            ),
        )
        
        text_body = f"""
AI Compliance Alert - {system_name}

Hallo {user_name},

Der Compliance-Score Ihres KI-Systems "{system_name}" hat sich verändert:
- Vorher: {old_score}%
- Aktuell: {new_score}%
- Risikokategorie: {_risikoklasse(risk_category)}

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
        
        
        eintraege = []
        for s_ in systems:
            last_scan = s_.get('last_assessment_date', 'Nie')
            if last_scan and last_scan != 'Nie':
                try:
                    last_scan = datetime.fromisoformat(str(last_scan).replace('Z', '+00:00')).strftime('%d.%m.%Y')
                except Exception:
                    pass
            eintraege.append(
                f"<strong>{mail_layout.escape(str(s_.get('name', 'Unbekannt')))}</strong><br>"
                f'<span style="color:#4b5563;font-size:13px;">Letzter Scan: '
                f"{mail_layout.escape(str(last_scan or 'Nie'))}</span>"
            )
        html_body = mail_layout.seite(
            "Scan-Erinnerung",
            "Einige Ihrer KI-Systeme wurden länger nicht geprüft.",
            mail_layout.kopf("KI-Compliance", "Scan-Erinnerung"),
            mail_layout.text(
                f"Hallo {mail_layout.escape(user_name or '')},",
                "folgende KI-Systeme wurden länger nicht auf Compliance geprüft:",
            ),
            mail_layout.liste("", eintraege),
            mail_layout.text("Regelmäßige Scans zeigen, ob Ihre KI-Systeme die Anforderungen "
                             "des EU AI Act weiterhin erfüllen."),
            mail_layout.aktion("", "Jetzt Scans durchführen",
                               mail_layout.escape(f"{self.frontend_url}/ai-compliance", quote=True)),
            mail_layout.gruss(),
            mail_layout.fuss(
                "Diese E-Mail wurde automatisch von complyo gesendet. "
                f'<a href="{mail_layout.escape(self.frontend_url + "/profile", quote=True)}" '
                'style="color:#5b6b78;">Benachrichtigungseinstellungen ändern</a>',
                mail_layout.rechtliches(),
            ),
        )
        
        text_body = f"""
Scan-Erinnerung - EU AI Act Compliance

Hallo {user_name},

Folgende KI-Systeme wurden länger nicht auf Compliance geprüft:

{chr(10).join([f"- {s.get('name', 'Unbekannt')}" for s in systems])}

Regelmäßige Scans zeigen, ob Ihre KI-Systeme die Anforderungen des EU AI Act weiterhin erfüllen.

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
        
        name = mail_layout.escape(system_name or "")
        html_body = mail_layout.seite(
            f"KI-System eingestuft: {system_name}",
            f"{system_name} wurde als {'verboten' if is_prohibited else 'Hochrisiko'} eingestuft.",
            mail_layout.kopf("KI-Compliance", "Verbotenes KI-System erkannt"
                             if is_prohibited else "Hochrisiko-System erkannt"),
            mail_layout.text(
                f"Hallo {mail_layout.escape(user_name or '')},",
                f"Ihr KI-System <strong>{name}</strong> wurde als "
                f"<strong>{mail_layout.escape(_risikoklasse(risk_category))}</strong> eingestuft.",
            ),
            mail_layout.hinweis("Begründung", mail_layout.escape(str(risk_reasoning or "")),
                                ton="gefahr" if is_prohibited else "warnung"),
            mail_layout.hinweis(
                "Achtung",
                "Verbotene KI-Systeme dürfen in der EU nicht betrieben werden. "
                "Sofortige Maßnahmen erforderlich.",
                ton="gefahr",
            ) if is_prohibited else "",
            mail_layout.aktion("", "Details ansehen", mail_layout.escape(system_url, quote=True)),
            mail_layout.gruss(),
            mail_layout.fuss(
                "Diese E-Mail wurde automatisch von complyo gesendet. "
                f'<a href="{mail_layout.escape(self.frontend_url + "/profile", quote=True)}" '
                'style="color:#5b6b78;">Benachrichtigungseinstellungen ändern</a>',
                mail_layout.rechtliches(),
            ),
        )
        
        text_body = f"""
{'VERBOTENES' if is_prohibited else 'Hochrisiko'} KI-System erkannt

Hallo {user_name},

Ihr KI-System "{system_name}" wurde als {_risikoklasse(risk_category)} klassifiziert.

Begründung: {risk_reasoning}

{'ACHTUNG: Verbotene KI-Systeme dürfen in der EU nicht betrieben werden!' if is_prohibited else ''}

Details: {system_url}

---
Complyo AI Compliance
        """
        
        return self._send_email(user_email, subject, html_body, text_body)


ai_compliance_notification_service = AIComplianceNotificationService()
