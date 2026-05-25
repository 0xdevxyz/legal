"""
GDPR-compliant email service for Complyo lead generation
Supports verification emails and compliance report delivery
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
from typing import Optional, Dict, Any
import logging
from jinja2 import Template
import json
from pdf_report_generator import pdf_generator
from i18n_service import i18n_service

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        # Email configuration from environment variables
        self.smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.sender_email = os.getenv('SENDER_EMAIL', 'noreply@complyo.tech')
        self.sender_name = os.getenv('SENDER_NAME', 'Complyo Compliance')
        self.frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
        self.admin_notify_email = os.getenv('ADMIN_NOTIFY_EMAIL', '')

        # For demo/testing purposes, we'll use console output if no SMTP is configured
        self.demo_mode = not all([self.smtp_username, self.smtp_password])
        
        if self.demo_mode:
            logger.info("Email service running in DEMO MODE - emails will be logged to console")

    def send_verification_email(self, email: str, name: str, verification_token: str, language: str = "de") -> bool:
        """
        Send GDPR-compliant verification email with double opt-in in specified language
        """
        try:
            verification_url = f"{self.frontend_url}/verify-email?token={verification_token}"
            
            subject = i18n_service.get_translation("email_verification_subject", language)
            
            # GDPR-compliant email template
            html_body = self._get_verification_email_template(name, verification_url, language)
            text_body = self._get_verification_email_text(name, verification_url, language)
            
            return self._send_email(
                to_email=email,
                subject=subject,
                html_body=html_body,
                text_body=text_body
            )
            
        except Exception as e:
            logger.error(f"Failed to send verification email to {email}: {str(e)}")
            return False

    def send_compliance_report(self, email: str, name: str, analysis_data: Dict[str, Any], lead_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Send compliance report with PDF attachment after successful email verification
        """
        try:
            # Ensure analysis_data is a dict
            if isinstance(analysis_data, str):
                try:
                    import json
                    analysis_data = json.loads(analysis_data)
                except:
                    # If it's not valid JSON, create a minimal structure
                    analysis_data = {
                        'compliance_score': 45,
                        'estimated_risk_euro': '5000-15000',
                        'findings': {},
                        'url': 'N/A'
                    }
            
            # Generate PDF report
            if not lead_data:
                lead_data = {'name': name, 'email': email, 'company': ''}
            
            pdf_bytes = pdf_generator.generate_compliance_report(analysis_data, lead_data)
            
            # Save PDF temporarily for attachment
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(pdf_bytes)
                pdf_path = tmp_file.name
            
            try:
                subject = f"📊 Ihr Complyo Compliance-Report ist bereit"
                
                html_body = self._get_report_email_template(name, analysis_data)
                text_body = self._get_report_email_text(name, analysis_data)
                
                success = self._send_email(
                    to_email=email,
                    subject=subject,
                    html_body=html_body,
                    text_body=text_body,
                    attachment_path=pdf_path,
                    attachment_name=f"Complyo_Compliance_Report_{name.replace(' ', '_')}.pdf"
                )
                
                return success
                
            finally:
                # Clean up temporary file
                try:
                    os.unlink(pdf_path)
                except:
                    pass
            
        except Exception as e:
            logger.error(f"Failed to send compliance report to {email}: {str(e)}")
            return False

    def _send_email(self, to_email: str, subject: str, html_body: str, text_body: str, attachment_path: Optional[str] = None, attachment_name: Optional[str] = None) -> bool:
        """
        Core email sending function
        """
        if self.demo_mode:
            # Demo mode - log email to console
            print(f"\n" + "="*60)
            print(f"📧 DEMO EMAIL (would be sent to: {to_email})")
            print(f"="*60)
            print(f"From: {self.sender_name} <{self.sender_email}>")
            print(f"To: {to_email}")
            print(f"Subject: {subject}")
            print(f"\n--- EMAIL CONTENT ---")
            print(text_body)
            if attachment_path:
                filename = attachment_name or os.path.basename(attachment_path)
                file_size = os.path.getsize(attachment_path) if os.path.exists(attachment_path) else 0
                print(f"\n📎 Attachment: {filename} ({file_size} bytes)")
            print(f"="*60 + "\n")
            return True
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.sender_name} <{self.sender_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add text and HTML parts
            text_part = MIMEText(text_body, 'plain', 'utf-8')
            html_part = MIMEText(html_body, 'html', 'utf-8')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Add attachment if provided
            if attachment_path and os.path.exists(attachment_path):
                with open(attachment_path, "rb") as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                
                encoders.encode_base64(part)
                filename = attachment_name or os.path.basename(attachment_path)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {filename}',
                )
                msg.attach(part)
            
            # Send email
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

    def _get_verification_email_template(self, name: str, verification_url: str, language: str = "de") -> str:
        """
        GDPR-compliant verification email template in specified language
        """
        greeting = i18n_service.get_translation("greeting", language, name=name)
        title = i18n_service.get_translation("verify_email_title", language)
        button_text = i18n_service.get_translation("verify_button", language)
        gdpr_notice = i18n_service.get_translation("gdpr_notice", language)
        template = Template("""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>E-Mail-Verifizierung - Complyo</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
        <h1 style="margin: 0; font-size: 28px;">🛡️ Complyo</h1>
        <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">Compliance Made Simple</p>
    </div>
    
    <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px;">
        <h2 style="color: #333; margin-top: 0;">Hallo {{ name }},</h2>
        
        <p>vielen Dank für Ihr Interesse an unserem Compliance-Report! </p>
        
        <p><strong>🔐 Bitte bestätigen Sie Ihre E-Mail-Adresse:</strong></p>
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="{{ verification_url }}" 
               style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                      color: white; 
                      text-decoration: none; 
                      padding: 15px 30px; 
                      border-radius: 25px; 
                      font-weight: bold; 
                      display: inline-block;
                      box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);">
                ✅ E-Mail-Adresse bestätigen
            </a>
        </div>
        
        <div style="background: #e3f2fd; border-left: 4px solid #2196f3; padding: 15px; margin: 20px 0; border-radius: 4px;">
            <h4 style="margin-top: 0; color: #1976d2;">🇩🇪 DSGVO-Hinweis</h4>
            <p style="margin-bottom: 0; font-size: 14px;">
                Mit der Bestätigung willigen Sie ein, dass wir Ihnen den angeforderten Compliance-Report 
                sowie gelegentlich relevante Compliance-Informationen zusenden dürfen. 
                <strong>Widerruf jederzeit möglich</strong> unter datenschutz@complyo.tech
            </p>
        </div>
        
        <p style="font-size: 14px; color: #666;">
            <strong>⏰ Wichtig:</strong> Dieser Link ist 24 Stunden gültig.<br>
            Falls Sie diese E-Mail nicht angefordert haben, können Sie sie einfach ignorieren.
        </p>
        
        <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
        
        <p style="font-size: 12px; color: #888; text-align: center;">
            Complyo GmbH • Compliance Made Simple<br>
            <a href="mailto:datenschutz@complyo.tech" style="color: #667eea;">datenschutz@complyo.tech</a> • 
            <a href="https://complyo.tech/datenschutz" style="color: #667eea;">Datenschutzerklärung</a>
        </p>
    </div>
</body>
</html>
        """)
        
        return template.render(name=name, verification_url=verification_url)

    def _get_verification_email_text(self, name: str, verification_url: str, language: str = "de") -> str:
        """
        Plain text version of verification email
        """
        return f"""
Hallo {name},

vielen Dank für Ihr Interesse an unserem Compliance-Report!

🔐 BITTE BESTÄTIGEN SIE IHRE E-MAIL-ADRESSE:

{verification_url}

🇩🇪 DSGVO-HINWEIS:
Mit der Bestätigung willigen Sie ein, dass wir Ihnen den angeforderten 
Compliance-Report sowie gelegentlich relevante Compliance-Informationen 
zusenden dürfen. Widerruf jederzeit möglich unter datenschutz@complyo.tech

⏰ WICHTIG: Dieser Link ist 24 Stunden gültig.
Falls Sie diese E-Mail nicht angefordert haben, können Sie sie einfach ignorieren.

---
Complyo GmbH • Compliance Made Simple
datenschutz@complyo.tech • https://complyo.tech/datenschutz
        """

    def _get_report_email_template(self, name: str, analysis_data: Dict[str, Any]) -> str:
        """
        Compliance report delivery email template
        """
        compliance_score = analysis_data.get('compliance_score', 0)
        risk_level = analysis_data.get('estimated_risk_euro', 'Unbekannt')
        findings_count = len(analysis_data.get('findings', {}))
        
        template = Template("""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ihr Compliance-Report - Complyo</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
        <h1 style="margin: 0; font-size: 28px;">📊 Ihr Compliance-Report</h1>
        <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">Complyo Analyse-Ergebnisse</p>
    </div>
    
    <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px;">
        <h2 style="color: #333; margin-top: 0;">Hallo {{ name }},</h2>
        
        <p>Ihre Website-Analyse ist abgeschlossen! Hier sind die wichtigsten Ergebnisse:</p>
        
        <div style="background: white; border-radius: 8px; padding: 20px; margin: 20px 0; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <h3 style="margin-top: 0; color: #667eea;">🎯 Analyse-Zusammenfassung</h3>
            <ul style="list-style: none; padding: 0;">
                <li style="padding: 8px 0; border-bottom: 1px solid #eee;">
                    <strong>Compliance-Score:</strong> {{ compliance_score }}%
                </li>
                <li style="padding: 8px 0; border-bottom: 1px solid #eee;">
                    <strong>Geschätztes Risiko:</strong> {{ risk_level }} EUR
                </li>
                <li style="padding: 8px 0;">
                    <strong>Gefundene Probleme:</strong> {{ findings_count }} Bereiche
                </li>
            </ul>
        </div>
        
        <div style="background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; border-radius: 4px;">
            <h4 style="margin-top: 0; color: #856404;">⚡ Nächste Schritte</h4>
            <p style="margin-bottom: 0; font-size: 14px;">
                Für eine detaillierte Lösungsstrategie und automatische Umsetzung 
                empfehlen wir Ihnen unseren KI-Automatisierung Service (39€/Monat).
            </p>
        </div>
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="http://localhost:3000/#pricing" 
               style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                      color: white; 
                      text-decoration: none; 
                      padding: 15px 30px; 
                      border-radius: 25px; 
                      font-weight: bold; 
                      display: inline-block;
                      box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);">
                🚀 Jetzt Compliance optimieren
            </a>
        </div>
        
        <p style="font-size: 14px; color: #666;">
            <strong>🔒 Datenschutz:</strong> Ihre Daten werden DSGVO-konform verarbeitet. 
            Widerruf jederzeit unter datenschutz@complyo.tech möglich.
        </p>
        
        <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
        
        <p style="font-size: 12px; color: #888; text-align: center;">
            Complyo GmbH • Compliance Made Simple<br>
            <a href="mailto:support@complyo.tech" style="color: #667eea;">support@complyo.tech</a> • 
            <a href="http://localhost:3000" style="color: #667eea;">complyo.tech</a>
        </p>
    </div>
</body>
</html>
        """)
        
        return template.render(
            name=name,
            compliance_score=compliance_score,
            risk_level=risk_level,
            findings_count=findings_count
        )

    def _get_report_email_text(self, name: str, analysis_data: Dict[str, Any]) -> str:
        """
        Plain text version of report email
        """
        compliance_score = analysis_data.get('compliance_score', 0)
        risk_level = analysis_data.get('estimated_risk_euro', 'Unbekannt')
        findings_count = len(analysis_data.get('findings', {}))
        
        return f"""
Hallo {name},

Ihre Website-Analyse ist abgeschlossen! Hier sind die wichtigsten Ergebnisse:

📊 ANALYSE-ZUSAMMENFASSUNG:
• Compliance-Score: {compliance_score}%
• Geschätztes Risiko: {risk_level} EUR
• Gefundene Probleme: {findings_count} Bereiche

⚡ NÄCHSTE SCHRITTE:
Für eine detaillierte Lösungsstrategie und automatische Umsetzung 
empfehlen wir Ihnen unseren KI-Automatisierung Service (39€/Monat).

🚀 Jetzt optimieren: http://localhost:3000/#pricing

🔒 DATENSCHUTZ: 
Ihre Daten werden DSGVO-konform verarbeitet. 
Widerruf jederzeit unter datenschutz@complyo.tech möglich.

---
Complyo GmbH • Compliance Made Simple
support@complyo.tech • http://localhost:3000
        """

    def send_deletion_confirmation_email(self, email: str, reference_id: str) -> bool:
        """
        Send confirmation email after data deletion (GDPR compliance)
        """
        try:
            subject = "Bestätigung der Datenlöschung - Complyo"
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Datenlöschung bestätigt</title>
            </head>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="text-align: center; margin-bottom: 30px;">
                        <h1 style="color: #667eea;">🛡️ Complyo</h1>
                        <h2 style="color: #333;">Datenlöschung bestätigt</h2>
                    </div>
                    
                    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                        <p>Sehr geehrte Damen und Herren,</p>
                        
                        <p>hiermit bestätigen wir die <strong>vollständige Löschung</strong> Ihrer personenbezogenen Daten aus unserem System gemäß <strong>Artikel 17 DSGVO</strong> (Recht auf Vergessenwerden).</p>
                        
                        <div style="background-color: #e7f3ff; padding: 15px; border-radius: 5px; margin: 20px 0;">
                            <strong>Löschungsdetails:</strong><br>
                            📅 Durchgeführt am: {datetime.now().strftime('%d.%m.%Y um %H:%M Uhr')}<br>
                            🔗 Referenz-ID: {reference_id}<br>
                            ⚖️ Rechtsgrundlage: DSGVO Artikel 17
                        </div>
                        
                        <p>Ihre Daten wurden <strong>permanent und unwiderruflich</strong> aus allen unseren Systemen gelöscht, einschließlich:</p>
                        <ul>
                            <li>Persönliche Kontaktdaten</li>
                            <li>Website-Analyse-Ergebnisse</li>
                            <li>E-Mail-Kommunikation</li>
                            <li>Einwilligungsnachweis</li>
                            <li>Technische Logs</li>
                        </ul>
                        
                        <p>Falls Sie in Zukunft unsere Dienste erneut nutzen möchten, müssen Sie eine neue Einwilligung erteilen.</p>
                    </div>
                    
                    <div style="border-top: 1px solid #eee; padding-top: 20px; font-size: 12px; color: #666;">
                        <p><strong>Complyo GmbH</strong><br>
                        E-Mail: datenschutz@complyo.tech<br>
                        Website: https://complyo.tech</p>
                        
                        <p>Bei Fragen wenden Sie sich gerne an unseren Datenschutzbeauftragten.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            text_content = f"""
            Datenlöschung bestätigt - Complyo
            
            Sehr geehrte Damen und Herren,
            
            hiermit bestätigen wir die vollständige Löschung Ihrer personenbezogenen Daten 
            aus unserem System gemäß Artikel 17 DSGVO (Recht auf Vergessenwerden).
            
            Löschungsdetails:
            - Durchgeführt am: {datetime.now().strftime('%d.%m.%Y um %H:%M Uhr')}
            - Referenz-ID: {reference_id}
            - Rechtsgrundlage: DSGVO Artikel 17
            
            Ihre Daten wurden permanent und unwiderruflich gelöscht.
            
            Bei Fragen: datenschutz@complyo.tech
            
            Mit freundlichen Grüßen,
            Ihr Complyo Team
            """
            
            return self._send_email(email, subject, html_content, text_content)
            
        except Exception as e:
            logger.error(f"Error sending deletion confirmation email: {e}")
            return False
    
    def send_data_export_email(self, email: str, export_data: dict) -> bool:
        """
        Send data export email (GDPR data portability)
        """
        try:
            subject = "Ihre Datenexport - Complyo DSGVO"
            
            # Convert export data to readable format
            export_summary = {
                "Persönliche Daten": len(export_data.get("personal_data", {})),
                "Einwilligungsdaten": len(export_data.get("consent_data", {})),
                "Analysedaten": "Ja" if export_data.get("analysis_data") else "Nein",
                "Technische Daten": len(export_data.get("technical_data", {}))
            }
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Ihr Datenexport</title>
            </head>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="text-align: center; margin-bottom: 30px;">
                        <h1 style="color: #667eea;">🛡️ Complyo</h1>
                        <h2 style="color: #333;">Ihr Datenexport</h2>
                    </div>
                    
                    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                        <p>Sehr geehrte Damen und Herren,</p>
                        
                        <p>gemäß <strong>Artikel 20 DSGVO</strong> (Recht auf Datenübertragbarkeit) erhalten Sie hiermit alle Ihre bei uns gespeicherten personenbezogenen Daten.</p>
                        
                        <div style="background-color: #e7f3ff; padding: 15px; border-radius: 5px; margin: 20px 0;">
                            <strong>Export-Details:</strong><br>
                            📅 Erstellt am: {datetime.now().strftime('%d.%m.%Y um %H:%M Uhr')}<br>
                            📊 Datenkategorien: {len(export_data)}<br>
                            ⚖️ Rechtsgrundlage: DSGVO Artikel 20
                        </div>
                        
                        <h3>Ihre Daten im Überblick:</h3>
                        <ul>
                            {''.join([f"<li><strong>{k}:</strong> {v}</li>" for k, v in export_summary.items()])}
                        </ul>
                        
                        <div style="background-color: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0;">
                            <strong>⚠️ Wichtiger Hinweis:</strong><br>
                            Diese E-Mail enthält Ihre vollständigen personenbezogenen Daten. 
                            Behandeln Sie diese Informationen vertraulich und löschen Sie sie 
                            nach der Verwendung sicher.
                        </div>
                        
                        <p>Die vollständigen Daten finden Sie im JSON-Format am Ende dieser E-Mail.</p>
                    </div>
                    
                    <div style="border-top: 1px solid #eee; padding-top: 20px; font-size: 12px; color: #666;">
                        <p><strong>Complyo GmbH</strong><br>
                        E-Mail: datenschutz@complyo.tech<br>
                        Website: https://complyo.tech</p>
                    </div>
                    
                    <div style="margin-top: 30px; padding: 20px; background-color: #f8f9fa; border-radius: 8px;">
                        <h3>Ihre vollständigen Daten (JSON-Format):</h3>
                        <pre style="background-color: #fff; padding: 15px; border-radius: 5px; overflow-x: auto; font-size: 11px;">{json.dumps(export_data, indent=2, ensure_ascii=False)}</pre>
                    </div>
                </div>
            </body>
            </html>
            """
            
            text_content = f"""
            Ihr Datenexport - Complyo DSGVO
            
            Sehr geehrte Damen und Herren,
            
            gemäß Artikel 20 DSGVO (Recht auf Datenübertragbarkeit) erhalten Sie hiermit 
            alle Ihre bei uns gespeicherten personenbezogenen Daten.
            
            Export-Details:
            - Erstellt am: {datetime.now().strftime('%d.%m.%Y um %H:%M Uhr')}
            - Datenkategorien: {len(export_data)}
            - Rechtsgrundlage: DSGVO Artikel 20
            
            Ihre Daten (JSON-Format):
            {json.dumps(export_data, indent=2, ensure_ascii=False)}
            
            Behandeln Sie diese Daten vertraulich.
            
            Bei Fragen: datenschutz@complyo.tech
            
            Mit freundlichen Grüßen,
            Ihr Complyo Team
            """
            
            return self._send_email(email, subject, html_content, text_content)
            
        except Exception as e:
            logger.error(f"Error sending data export email: {e}")
            return False

    def send_waitlist_confirmation(self, email: str, name: str, confirm_url: str) -> bool:
        """
        Bestätigungs-E-Mail für die Early-Access Waitlist (Double-Opt-In, DSGVO-konform)
        """
        try:
            greeting = f"Hallo{(' ' + name) if name else ''},"
            subject = "Bestätige deine Anmeldung auf der Complyo Early-Access-Liste"

            html_body = f"""<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Bestätige deine Early-Access-Anmeldung</title>
</head>
<body style="font-family:Arial,sans-serif;line-height:1.6;color:#333;max-width:600px;margin:0 auto;padding:20px;">
  <div style="background:linear-gradient(135deg,#2563eb 0%,#1d4ed8 100%);color:white;padding:32px;text-align:center;border-radius:12px 12px 0 0;">
    <div style="display:inline-flex;align-items:center;gap:10px;margin-bottom:8px;">
      <div style="width:36px;height:36px;background:rgba(255,255,255,0.2);border-radius:8px;display:inline-flex;align-items:center;justify-content:center;font-weight:bold;font-size:18px;">C</div>
      <span style="font-size:22px;font-weight:bold;">complyo</span>
    </div>
    <p style="margin:0;font-size:15px;opacity:0.85;">Early Access – Jetzt bestätigen</p>
  </div>

  <div style="background:#f8fafc;padding:32px;border-radius:0 0 12px 12px;border:1px solid #e2e8f0;border-top:none;">
    <h2 style="color:#1e293b;margin-top:0;">{greeting}</h2>

    <p>vielen Dank für dein Interesse an <strong>complyo</strong> – der KI-Compliance-Plattform für Websites.</p>

    <p>Bitte bestätige jetzt deine E-Mail-Adresse, um deinen Early-Access-Platz zu sichern:</p>

    <div style="text-align:center;margin:32px 0;">
      <a href="{confirm_url}"
         style="background:#2563eb;color:white;text-decoration:none;padding:14px 32px;border-radius:10px;font-weight:bold;font-size:16px;display:inline-block;box-shadow:0 4px 14px rgba(37,99,235,0.35);">
        E-Mail bestätigen
      </a>
    </div>

    <p style="font-size:13px;color:#64748b;">
      Falls der Button nicht funktioniert, kopiere diesen Link in deinen Browser:<br>
      <a href="{confirm_url}" style="color:#2563eb;word-break:break-all;">{confirm_url}</a>
    </p>

    <p style="font-size:13px;color:#64748b;">
      Dieser Link ist 7 Tage gültig. Falls du dich nicht angemeldet hast, ignoriere diese E-Mail einfach.
    </p>

    <hr style="border:none;border-top:1px solid #e2e8f0;margin:28px 0;">

    <p style="font-size:12px;color:#94a3b8;text-align:center;">
      <strong>Complyo</strong> &bull; KI-Compliance-Plattform &bull; Made in Germany<br>
      <a href="https://complyo.de/impressum" style="color:#94a3b8;">Impressum</a> &bull;
      <a href="https://complyo.de/datenschutz" style="color:#94a3b8;">Datenschutz</a> &bull;
      <a href="mailto:support@complyo.de" style="color:#94a3b8;">support@complyo.de</a>
    </p>
    <p style="font-size:11px;color:#cbd5e1;text-align:center;">
      Du erhältst diese E-Mail, weil du dich auf complyo.de / complyo.tech für Early Access angemeldet hast.
      Deine Daten werden DSGVO-konform verarbeitet (Art. 6 Abs. 1 lit. a DSGVO).
    </p>
  </div>
</body>
</html>"""

            text_body = f"""{greeting}

vielen Dank für dein Interesse an complyo – der KI-Compliance-Plattform für Websites.

Bitte bestätige deine E-Mail-Adresse, um deinen Early-Access-Platz zu sichern:

{confirm_url}

Dieser Link ist 7 Tage gültig.
Falls du dich nicht angemeldet hast, ignoriere diese E-Mail einfach.

---
Complyo – KI-Compliance-Plattform – Made in Germany
Impressum: https://complyo.de/impressum
Datenschutz: https://complyo.de/datenschutz
Kontakt: support@complyo.de

Du erhältst diese E-Mail, weil du dich auf complyo.de / complyo.tech für Early Access angemeldet hast.
Deine Daten werden DSGVO-konform verarbeitet (Art. 6 Abs. 1 lit. a DSGVO).
"""
            return self._send_email(
                to_email=email,
                subject=subject,
                html_body=html_body,
                text_body=text_body,
            )

        except Exception as e:
            logger.error(f"Failed to send waitlist confirmation to {email}: {e}")
            return False

    def send_waitlist_admin_notification(self, email: str, name: str, phone: str, source: str) -> bool:
        """
        Interne Benachrichtigung an den Admin bei jeder neuen Waitlist-Anmeldung
        """
        if not self.admin_notify_email:
            return False
        try:
            display_name = name or "(kein Name)"
            display_phone = phone or "(keine Telefonnummer)"
            subject = f"[complyo] Neue Waitlist-Anmeldung: {display_name} <{email}>"
            html_body = f"""<!DOCTYPE html>
<html lang="de">
<head><meta charset="utf-8"><title>Neue Waitlist-Anmeldung</title></head>
<body style="font-family:Arial,sans-serif;color:#333;max-width:500px;margin:0 auto;padding:20px;">
  <div style="background:#2563eb;color:white;padding:16px 20px;border-radius:10px 10px 0 0;">
    <strong>complyo – Neue Waitlist-Anmeldung</strong>
  </div>
  <div style="background:#f8fafc;border:1px solid #e2e8f0;border-top:none;padding:20px;border-radius:0 0 10px 10px;">
    <table style="width:100%;border-collapse:collapse;font-size:14px;">
      <tr><td style="padding:6px 0;color:#64748b;width:110px;">E-Mail</td><td style="padding:6px 0;font-weight:bold;">{email}</td></tr>
      <tr><td style="padding:6px 0;color:#64748b;">Name</td><td style="padding:6px 0;">{display_name}</td></tr>
      <tr><td style="padding:6px 0;color:#64748b;">Telefon</td><td style="padding:6px 0;">{display_phone}</td></tr>
      <tr><td style="padding:6px 0;color:#64748b;">Quelle</td><td style="padding:6px 0;">{source}</td></tr>
    </table>
    <p style="font-size:12px;color:#94a3b8;margin-top:16px;">
      Double-Opt-In ausstehend – Bestätigungsmail wurde an den Nutzer gesendet.
    </p>
  </div>
</body>
</html>"""
            text_body = f"""Neue Waitlist-Anmeldung

E-Mail:   {email}
Name:     {display_name}
Telefon:  {display_phone}
Quelle:   {source}

Double-Opt-In ausstehend.
"""
            return self._send_email(
                to_email=self.admin_notify_email,
                subject=subject,
                html_body=html_body,
                text_body=text_body,
            )
        except Exception as e:
            logger.error(f"Failed to send admin notification for {email}: {e}")
            return False


# Global email service instance
email_service = EmailService()