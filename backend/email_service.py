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
# `datetime.now()` steht in vier Mail-Vorlagen (Loeschbestaetigung,
# Datenexport, Warteliste), der Import fehlte. Diese Mails brachen beim
# Zusammenbauen ab und wurden NIE verschickt — ohne Spur beim Empfaenger,
# der nur nichts bekam. Gefunden vom Waechtertest fuer fehlende Importe,
# nachdem derselbe Fehler den Hauptscan abgeraeumt hatte.
from datetime import datetime
from typing import Optional, Dict, Any
import logging
import json
from pdf_report_generator import pdf_generator
from i18n_service import i18n_service
import mail_layout

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        # Email configuration from environment variables
        self.smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.sender_email = os.getenv('SENDER_EMAIL', 'noreply@complyo.de')
        self.sender_name = os.getenv('SENDER_NAME', 'Complyo Compliance')
        # Default war http://localhost:3000 — damit zeigten Kunden-Mails in
        # Produktion auf localhost-Links.
        self.frontend_url = os.getenv('FRONTEND_URL', 'https://complyo.de')
        self.admin_notify_email = os.getenv('ADMIN_NOTIFY_EMAIL', '')
        self.environment = os.getenv('ENVIRONMENT', 'development')

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
                except Exception:
                    # Unlesbar heisst unbekannt. Hier standen frueher erfundene
                    # Werte (Score 45 %, Risiko 5.000-15.000 EUR), die als
                    # Messergebnis beim Kunden ankamen.
                    analysis_data = {}
            
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
            # In Produktion ist der Demo-Modus ein Konfigurationsfehler, kein
            # Erfolg: Vorher wanderten DSGVO-Bestätigungen hier in die Konsole
            # und der Aufrufer loggte "verschickt". Jetzt ehrlich False.
            if self.environment.lower() in ('production', 'prod'):
                logger.error(
                    "MAIL NICHT VERSANDT (Demo-Modus in Produktion): an %s, "
                    "Betreff '%s' — SMTP_USERNAME/SMTP_PASSWORD fehlen",
                    to_email, subject,
                )
                return False
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
        Double-Opt-In fuer den Compliance-Report (Lead, kein Konto).

        Rahmen aus mail_layout.py. Der Einwilligungstext ist wortgleich zum
        frueheren geblieben: er ist die Grundlage fuer den Versand und wird
        hier nicht nebenbei umformuliert.
        """
        n = mail_layout.escape(name or "")
        link = mail_layout.escape(verification_url, quote=True)
        leise = '<span style="color:#4b5563;font-size:14px;">'
        return mail_layout.seite(
            "E-Mail-Verifizierung - Complyo",
            "Bitte bestätigen Sie Ihre E-Mail-Adresse, dann schicken wir Ihren Report.",
            mail_layout.kopf("Ihr Compliance-Report", "Bitte bestätigen Sie Ihre E-Mail-Adresse"),
            mail_layout.text(
                f"Hallo {n}," if n else "Hallo,",
                "vielen Dank für Ihr Interesse an unserem Compliance-Report. Sobald Sie "
                "Ihre Adresse bestätigt haben, schicken wir ihn Ihnen zu.",
            ),
            mail_layout.aktion("", "E-Mail-Adresse bestätigen", link),
            mail_layout.hinweis(
                "Datenschutz",
                "Mit der Bestätigung willigen Sie ein, dass wir Ihnen den angeforderten "
                "Compliance-Report sowie gelegentlich relevante Compliance-Informationen "
                "zusenden dürfen. <strong>Widerruf jederzeit möglich</strong> unter "
                '<a href="mailto:datenschutz@complyo.de" style="color:#00706c;">'
                "datenschutz@complyo.de</a>.",
            ),
            mail_layout.text(
                leise + "Dieser Link ist 24 Stunden gültig. Falls der Knopf nicht "
                "funktioniert, kopieren Sie diese Adresse in den Browser:<br>"
                f'<a href="{link}" style="color:#00706c;word-break:break-all;">{link}</a></span>',
                leise + "Falls Sie diese E-Mail nicht angefordert haben, können Sie sie "
                "einfach ignorieren.</span>",
            ),
            mail_layout.gruss(),
            mail_layout.kontakt(),
            mail_layout.fuss(mail_layout.rechtliches()),
        )

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
zusenden dürfen. Widerruf jederzeit möglich unter datenschutz@complyo.de

⏰ WICHTIG: Dieser Link ist 24 Stunden gültig.
Falls Sie diese E-Mail nicht angefordert haben, können Sie sie einfach ignorieren.

---
Yvonne Weishar · Complyo, Pappelallee 64, 10437 Berlin • Compliance Made Simple
datenschutz@complyo.de • https://complyo.de/datenschutz
        """

    def _get_report_email_template(self, name: str, analysis_data: Dict[str, Any]) -> str:
        """
        Begleitmail zum PDF-Report.

        Es stehen nur Werte in der Mail, die in analysis_data wirklich
        vorliegen. Frueher erfand send_compliance_report bei unlesbaren Daten
        einen Score von 45 % und ein Risiko von 5.000 bis 15.000 EUR und
        schickte beides als Messergebnis hinaus.
        """
        n = mail_layout.escape(name or "")
        zeilen = []
        if analysis_data.get('compliance_score') is not None:
            zeilen.append(("Compliance-Score",
                           f"{mail_layout.escape(str(analysis_data['compliance_score']))} %"))
        if analysis_data.get('findings'):
            zeilen.append(("Bereiche mit Befunden", str(len(analysis_data['findings']))))

        zusammenfassung = (
            mail_layout.angaben(zeilen, "Analyse-Zusammenfassung") if zeilen else
            mail_layout.text("Die Zusammenfassung ließ sich nicht aus den Analysedaten "
                             "lesen. Alle Ergebnisse stehen im beigefügten PDF.")
        )
        return mail_layout.seite(
            "Ihr Compliance-Report - Complyo",
            "Ihre Website-Analyse ist abgeschlossen, der Report hängt an dieser Mail.",
            mail_layout.kopf("Ihr Compliance-Report", "Ihre Analyse ist abgeschlossen"),
            mail_layout.text(
                f"Hallo {n}," if n else "Hallo,",
                "Ihre Website-Analyse ist abgeschlossen. Den vollständigen Report finden "
                "Sie als PDF im Anhang, hier die wichtigsten Werte:",
            ),
            zusammenfassung,
            mail_layout.hinweis(
                "Nächste Schritte",
                "Für eine detaillierte Lösungsstrategie und automatische Umsetzung "
                "empfehlen wir Ihnen unsere Tarife Single (29 €/Monat) oder Pro (89 €/Monat).",
            ),
            mail_layout.aktion("", "Tarife ansehen",
                               mail_layout.escape(f"{self.frontend_url}/#pricing", quote=True)),
            mail_layout.gruss(),
            mail_layout.kontakt(),
            mail_layout.fuss(
                "Rechtsgrundlage für diese Mail ist Ihre Einwilligung (Art. 6 Abs. 1 lit. a "
                "DSGVO). Widerruf jederzeit unter datenschutz@complyo.de.",
                mail_layout.rechtliches(),
            ),
        )

    def _get_report_email_text(self, name: str, analysis_data: Dict[str, Any]) -> str:
        """
        Plain text version of report email
        """
        zeilen = []
        if analysis_data.get('compliance_score') is not None:
            zeilen.append(f"• Compliance-Score: {analysis_data['compliance_score']}%")
        if analysis_data.get('findings'):
            zeilen.append(f"• Bereiche mit Befunden: {len(analysis_data['findings'])}")
        zusammenfassung = "\n".join(zeilen) or (
            "Die Zusammenfassung ließ sich nicht aus den Analysedaten lesen.\n"
            "Alle Ergebnisse stehen im beigefügten PDF.")

        return f"""
Hallo {name},

Ihre Website-Analyse ist abgeschlossen. Den vollständigen Report finden Sie als PDF im Anhang.

ANALYSE-ZUSAMMENFASSUNG:
{zusammenfassung}

NÄCHSTE SCHRITTE:
Für eine detaillierte Lösungsstrategie und automatische Umsetzung
empfehlen wir Ihnen unsere Tarife Single (29 €/Monat) oder Pro (89 €/Monat).

Tarife ansehen: {self.frontend_url}/#pricing

Rechtsgrundlage für diese Mail ist Ihre Einwilligung (Art. 6 Abs. 1 lit. a DSGVO).
Widerruf jederzeit unter datenschutz@complyo.de.

---
Yvonne Weishar · Complyo, Pappelallee 64, 10437 Berlin
support@complyo.de • {self.frontend_url}
        """

    # Was bei einer Kontoloeschung wirklich passiert, und nur das. Die
    # fruehere Mail sagte "permanent und unwiderruflich aus allen unseren
    # Systemen, einschliesslich Einwilligungsnachweis und technischer Logs"
    # und verwies auf "unseren Datenschutzbeauftragten". Nachgemessen am
    # 29.09.2026: die Loeschung schreibt die Adresse selbst ins Log, die
    # Datensicherung haelt Tagesstaende 14 und Monatsstaende 190 Tage
    # (scripts/datensicherung.sh), und einen Datenschutzbeauftragten nennt
    # die Datenschutzerklaerung nicht. Die Liste folgt
    # gdpr_retention_service._LOESCH_STATEMENTS.
    LOESCHUNG_UMFANG = [
        "Ihr Konto mit Anmeldedaten, Sitzungen und Einstellungen",
        "Ihre Websites, Scans und Scanverläufe",
        "erzeugte Dokumente und Korrekturen",
        "Firmen- und Abonnementdaten",
    ]
    LOESCHUNG_GRENZEN = (
        "Bearbeitungsvermerke, die andere Datensätze tragen, sind anonymisiert. "
        "In unseren Datensicherungen bleiben die Daten bis zu deren Ablauf erhalten, "
        "höchstens 190 Tage, danach werden sie überschrieben. Aus einer Sicherung "
        "stellen wir sie nicht wieder her. Rechnungen, die wir nach Handels- und "
        "Steuerrecht aufbewahren müssen, bleiben bis zum Ende dieser Frist gespeichert."
    )

    def send_deletion_confirmation_email(self, email: str, reference_id: str) -> bool:
        """
        Bestaetigung nach ausgefuehrter Kontoloeschung (Art. 17 DSGVO).
        """
        try:
            subject = "Bestätigung der Datenlöschung - Complyo"
            zeitpunkt = datetime.now().strftime('%d.%m.%Y um %H:%M Uhr')
            ref = mail_layout.escape(str(reference_id))

            html_content = mail_layout.seite(
                "Datenlöschung bestätigt",
                "Ihr Konto und die zugehörigen Daten sind gelöscht.",
                mail_layout.kopf("Art. 17 DSGVO", "Ihre Daten sind gelöscht"),
                mail_layout.text(
                    "Sehr geehrte Damen und Herren,",
                    "hiermit bestätigen wir die Löschung Ihres complyo-Kontos und der "
                    "zugehörigen personenbezogenen Daten gemäß Artikel 17 DSGVO.",
                ),
                mail_layout.angaben([
                    ("Durchgeführt am", zeitpunkt),
                    ("Referenz", ref),
                    ("Rechtsgrundlage", "Art. 17 DSGVO"),
                ]),
                mail_layout.liste("Gelöscht wurden", self.LOESCHUNG_UMFANG),
                mail_layout.hinweis("Was bleibt", self.LOESCHUNG_GRENZEN),
                mail_layout.text(
                    "Falls Sie unsere Dienste später erneut nutzen möchten, legen Sie "
                    "einfach ein neues Konto an. Bei Fragen erreichen Sie uns unter "
                    '<a href="mailto:datenschutz@complyo.de" style="color:#00706c;">'
                    "datenschutz@complyo.de</a>.",
                ),
                mail_layout.gruss(),
                mail_layout.kontakt(),
                mail_layout.fuss(mail_layout.rechtliches()),
            )

            umfang = "\n".join(f"- {p}" for p in self.LOESCHUNG_UMFANG)
            text_content = f"""Datenlöschung bestätigt - Complyo

Sehr geehrte Damen und Herren,

hiermit bestätigen wir die Löschung Ihres complyo-Kontos und der zugehörigen
personenbezogenen Daten gemäß Artikel 17 DSGVO.

Durchgeführt am: {zeitpunkt}
Referenz: {reference_id}
Rechtsgrundlage: Art. 17 DSGVO

Gelöscht wurden:
{umfang}

Was bleibt: {self.LOESCHUNG_GRENZEN}

Bei Fragen: datenschutz@complyo.de

Mit freundlichen Grüßen
Ihr complyo-Team
"""
            return self._send_email(email, subject, html_content, text_content)

        except Exception as e:
            logger.error(f"Error sending deletion confirmation email: {e}")
            return False
    
    def send_data_export_email(self, email: str, export_data: dict) -> bool:
        """
        Datenexport nach Art. 20 DSGVO.

        Der Export enthaelt Freitext aus dem Konto (Websites, Firmendaten). Er
        ging unmaskiert als <pre> ins HTML; jetzt maskiert.
        """
        try:
            subject = "Ihr Datenexport - Complyo"

            # Zusammenfassung generisch aufbauen — der Export ist seit 2026-08-11
            # das aggregierte Konto-JSON (users + zugehörige Tabellen), nicht
            # mehr das feste Lead-Schema.
            export_summary = {}
            for kategorie, inhalt in export_data.items():
                if kategorie == "export_info":
                    continue
                if isinstance(inhalt, list):
                    export_summary[kategorie] = f"{len(inhalt)} Einträge"
                elif isinstance(inhalt, dict):
                    export_summary[kategorie] = "Ja"
                else:
                    export_summary[kategorie] = "Ja" if inhalt else "Nein"

            zeitpunkt = datetime.now().strftime('%d.%m.%Y um %H:%M Uhr')
            daten_json = json.dumps(export_data, indent=2, ensure_ascii=False, default=str)
            leise = '<span style="color:#4b5563;font-size:14px;">'

            html_content = mail_layout.seite(
                "Ihr Datenexport",
                "Alle bei complyo gespeicherten Daten zu Ihrem Konto.",
                mail_layout.kopf("Art. 20 DSGVO", "Ihr Datenexport"),
                mail_layout.text(
                    "Sehr geehrte Damen und Herren,",
                    "gemäß Artikel 20 DSGVO (Recht auf Datenübertragbarkeit) erhalten Sie "
                    "hiermit alle Ihre bei uns gespeicherten personenbezogenen Daten. "
                    "Die vollständigen Daten stehen im JSON-Format am Ende dieser E-Mail.",
                ),
                mail_layout.angaben([
                    ("Erstellt am", zeitpunkt),
                    ("Datenkategorien", str(len(export_summary))),
                    ("Rechtsgrundlage", "Art. 20 DSGVO"),
                ]),
                mail_layout.angaben(
                    [(mail_layout.escape(str(k)), mail_layout.escape(str(v)))
                     for k, v in export_summary.items()],
                    "Ihre Daten im Überblick",
                ),
                mail_layout.hinweis(
                    "Vertraulich behandeln",
                    "Diese E-Mail enthält Ihre vollständigen personenbezogenen Daten. "
                    "Behandeln Sie sie vertraulich und löschen Sie sie nach der Verwendung.",
                    ton="warnung",
                ),
                mail_layout.karte(
                    '<div style="color:#111827;font-size:17px;font-weight:700;'
                    'margin:0 0 12px;">Ihre vollständigen Daten (JSON)</div>'
                    '<pre style="margin:0;white-space:pre-wrap;word-break:break-all;'
                    'font-family:Menlo,Consolas,monospace;font-size:11px;line-height:1.5;'
                    f'color:#111827;">{mail_layout.escape(daten_json)}</pre>',
                    innen="28px 32px",
                ),
                mail_layout.text(leise + "Bei Fragen: datenschutz@complyo.de</span>"),
                mail_layout.gruss(),
                mail_layout.kontakt(),
                mail_layout.fuss(mail_layout.rechtliches()),
            )

            text_content = f"""Ihr Datenexport - Complyo

Sehr geehrte Damen und Herren,

gemäß Artikel 20 DSGVO (Recht auf Datenübertragbarkeit) erhalten Sie hiermit
alle Ihre bei uns gespeicherten personenbezogenen Daten.

Erstellt am: {zeitpunkt}
Datenkategorien: {len(export_summary)}
Rechtsgrundlage: Art. 20 DSGVO

Ihre Daten (JSON-Format):
{daten_json}

Behandeln Sie diese Daten vertraulich.

Bei Fragen: datenschutz@complyo.de

Mit freundlichen Grüßen
Ihr complyo-Team
"""
            return self._send_email(email, subject, html_content, text_content)

        except Exception as e:
            logger.error(f"Error sending data export email: {e}")
            return False

    def send_waitlist_confirmation(self, email: str, name: str, confirm_url: str) -> bool:
        """
        Bestätigungs-E-Mail für die Early-Access Waitlist (Double-Opt-In, DSGVO-konform)

        Aufbau nach dem gemeinsamen Rahmen in mail_layout.py. Der Name kommt
        frei aus dem Formular und wird deshalb maskiert, bevor er ins HTML geht.
        """
        try:
            greeting = f"Hallo{(' ' + name) if name else ''},"
            subject = "Bestätige deine Anmeldung auf der Complyo Early-Access-Liste"
            anrede = f"Hallo{(' ' + mail_layout.escape(name)) if name else ''},"
            link = mail_layout.escape(confirm_url, quote=True)

            html_body = mail_layout.seite(
                "Bestätige deine Early-Access-Anmeldung",
                "Ein Klick auf den Link, dann ist deine Anmeldung bestätigt.",
                mail_layout.kopf("Early Access", "Bitte bestätige deine Anmeldung"),
                mail_layout.text(
                    anrede,
                    "vielen Dank für dein Interesse an <strong>complyo</strong>, "
                    "der KI-Compliance-Plattform für Websites.",
                    "Bitte bestätige jetzt deine E-Mail-Adresse, um deinen "
                    "Early-Access-Platz zu sichern. Der Link ist 7 Tage gültig.",
                ),
                mail_layout.aktion("E-Mail-Adresse bestätigen", "Jetzt bestätigen", link),
                mail_layout.text(
                    '<span style="color:#4b5563;font-size:14px;">Falls der Knopf nicht '
                    'funktioniert, kopiere diesen Link in deinen Browser:<br>'
                    f'<a href="{link}" style="color:#00706c;word-break:break-all;">{link}</a></span>',
                    '<span style="color:#4b5563;font-size:14px;">Falls du dich nicht '
                    'angemeldet hast, ignoriere diese E-Mail einfach. Ohne Bestätigung '
                    'passiert nichts weiter.</span>',
                ),
                mail_layout.gruss(),
                mail_layout.kontakt(),
                mail_layout.fuss(
                    "Du erhältst diese E-Mail, weil du dich auf complyo.de für Early "
                    "Access angemeldet hast. Rechtsgrundlage ist deine Einwilligung "
                    "(Art. 6 Abs. 1 lit. a DSGVO), die du jederzeit widerrufen kannst.",
                    mail_layout.rechtliches(),
                ),
            )

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

Du erhältst diese E-Mail, weil du dich auf complyo.de für Early Access angemeldet hast.
Rechtsgrundlage ist deine Einwilligung (Art. 6 Abs. 1 lit. a DSGVO), die du jederzeit widerrufen kannst.
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

    def send_waitlist_admin_notification(
        self, email: str, name: str, phone: str, source: str,
        herkunft: str = "", angebot: str = "",
        bestaetigt: bool = False, platz_nr=None,
    ) -> bool:
        """
        Interne Benachrichtigung an den Admin bei jeder neuen Waitlist-Anmeldung

        `herkunft` traegt Kampagne und UTM-Parameter. Ohne sie steht in der
        Meldung nur "landing", und bei laufenden Anzeigen ist genau die Frage
        offen, welche davon den Eintrag gebracht hat.
        """
        if not self.admin_notify_email:
            # Fehlt die Adresse, gibt es niemanden zu benachrichtigen. Das ist
            # eine Konfigurationsluecke und kein Normalfall — deshalb sichtbar
            # im Log statt stillem return False.
            logger.warning(
                "ADMIN_NOTIFY_EMAIL ist nicht gesetzt — Waitlist-Anmeldung "
                f"von {email} wird nicht gemeldet"
            )
            return False
        try:
            display_name = name or "(kein Name)"
            display_phone = phone or "(keine Telefonnummer)"

            # Zwei Meldungen je Interessent, und der Unterschied gehoert in die
            # Betreffzeile: die erste sagt nur, dass jemand das Formular
            # abgeschickt hat, die zweite, dass er den Link in der Mail geklickt
            # hat. Erst die zweite ist ein Lead, den man anschreiben darf, und
            # erst sie belegt einen der 100 Plaetze.
            # Betreff: das Wichtigste zuerst. Vorher stand die Platznummer am
            # Ende und wurde auf dem Handy abgeschnitten — sichtbar war nur
            # "[complyo] Bestätigt: (kein Name) <probe…". Das Präfix "[complyo]"
            # ist ebenfalls weg: der Absender heißt bereits complyo, und die
            # zehn Zeichen fehlten genau dort, wo die Zahl stehen soll.
            # Der Name kommt nur noch vor, wenn es einen gibt; das Formular
            # fragt keinen mehr ab, also stand dort immer "(kein Name)".
            wer = f"{name.strip()} <{email}>" if name and name.strip() else email

            if bestaetigt:
                platz_text = f"Platz {platz_nr}" if platz_nr else "kein Platz mehr frei"
                subject = (
                    f"Platz {platz_nr} bestätigt: {wer}" if platz_nr
                    else f"Bestätigt, kein Platz mehr frei: {wer}"
                )
                kopfzeile = "complyo – Wartelisten-Eintrag bestätigt"
                fusszeile = (
                    f"Double-Opt-In abgeschlossen – {platz_text}."
                    if platz_nr else
                    "Double-Opt-In abgeschlossen – das Kontingent war bereits vergeben, "
                    "der Eintrag steht ohne Preiszusage auf der Liste."
                )
            else:
                subject = f"Neue Anmeldung: {wer}"
                kopfzeile = "complyo – Neue Waitlist-Anmeldung"
                fusszeile = (
                    "Double-Opt-In ausstehend – Bestätigungsmail wurde an den Nutzer gesendet."
                )
            # Die Mail traegt genau eine Nachricht, und die gehoert gross
            # nach oben: bei einer neuen Anmeldung die Adresse, bei einer
            # Bestaetigung die Platznummer. Alles andere sind Nebenangaben.
            #
            # Vorher stand ueber allem ein blauer Balken mit dem Wort
            # "complyo – Neue Waitlist-Anmeldung", darunter eine graue Tabelle
            # mit sechs gleich gewichteten Zeilen. Es war nichts falsch daran,
            # aber man musste lesen, um zu erfahren, was passiert ist.
            #
            # Aufbau bewusst mit Tabellen und Inline-Stilen: Outlook rendert
            # weder flex noch grid, und externe Schriften laedt kein
            # Mailprogramm zuverlaessig.
            if bestaetigt and platz_nr:
                augenmerk = "Warteliste"
                schlagzeile = f"Platz {platz_nr}"
                unterzeile = email
            elif bestaetigt:
                augenmerk = "Warteliste"
                schlagzeile = "Bestätigt"
                unterzeile = email
            else:
                augenmerk = "Neue Anmeldung"
                schlagzeile = email
                unterzeile = ""

            def _zeile(bezeichnung: str, wert: str) -> str:
                return (
                    '<tr>'
                    '<td style="padding:0 0 14px;color:#4b5563;font-size:14px;'
                    'width:132px;vertical-align:top;">' + bezeichnung + '</td>'
                    '<td style="padding:0 0 14px;color:#111827;font-size:14px;'
                    'word-break:break-word;">' + mail_layout.escape(wert) + '</td>'
                    '</tr>'
                )

            angaben = (
                _zeile("E-Mail", email)
                + _zeile("Name", display_name)
                + _zeile("Telefon", display_phone)
                + _zeile("Quelle", source)
                + _zeile("Herkunft", herkunft or "(direkt)")
                + _zeile("Angebot", angebot or "(keines)")
            )

            # Derselbe Rahmen wie die Mails an Interessenten (mail_layout.py),
            # ohne Gruss und Kontakt: die Meldung geht nur an uns.
            html_body = mail_layout.seite(
                kopfzeile,
                f"{augenmerk}: {schlagzeile}",
                mail_layout.kopf(augenmerk, mail_layout.escape(schlagzeile),
                                 mail_layout.escape(unterzeile)),
                mail_layout.karte(
                    '<table role="presentation" width="100%" cellpadding="0" '
                    f'cellspacing="0" border="0" style="font-family:{mail_layout.SCHRIFT};">'
                    f'{angaben}</table>',
                    innen="32px 40px 22px",
                ),
                mail_layout.fuss(fusszeile),
            )
            text_body = f"""{augenmerk}

{schlagzeile}{chr(10) + unterzeile if unterzeile else ""}

E-Mail:   {email}
Name:     {display_name}
Telefon:  {display_phone}
Quelle:   {source}
Herkunft: {herkunft or "(direkt)"}
Angebot:  {angebot or "(keines)"}

{fusszeile}

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

    # =======================================================================
    # Kontosicherheit: Bestaetigung, Zuruecksetzen, Loeschankuendigung
    # =======================================================================
    #
    # Drei Mails, die es bis zum 10.09.2026 nicht gab. Seit 29.09.2026 im
    # Rahmen aus mail_layout.py, damit sie aussehen wie der Rest von complyo.
    # Geblieben ist die Regel von damals: keine Nachverfolgung, und der
    # einzige anklickbare Weg ist der eine Link, um den es geht. Deshalb
    # hier keine Kontaktkarte und keine Links im Fuss. Wer eine Mail zum
    # Zuruecksetzen bekommt, die er nicht angefordert hat, soll auf einen
    # Blick sehen, was zu tun ist, naemlich nichts. Das Logo ist eine
    # statische Datei ohne Kennung, es verraet nicht, wer die Mail oeffnet.

    def _rahmen(self, ueberschrift: str, absatz: str, knopf_text: str,
                knopf_url: str, fusszeile: str) -> str:
        link = mail_layout.escape(knopf_url, quote=True)
        leise = '<span style="color:#4b5563;font-size:14px;">'
        return mail_layout.seite(
            ueberschrift,
            ueberschrift,
            mail_layout.kopf("Ihr complyo-Konto", ueberschrift),
            mail_layout.text(absatz),
            mail_layout.aktion("", knopf_text, link),
            mail_layout.text(
                leise + "Falls der Knopf nicht funktioniert, diese Adresse in den "
                "Browser kopieren:<br>"
                f'<span style="color:#111827;word-break:break-all;">{link}</span></span>',
                leise + fusszeile + "</span>",
            ),
            mail_layout.gruss(),
            mail_layout.fuss(
                f"{mail_layout.ANBIETER['geschaeftsbezeichnung']} · "
                f"{mail_layout.ANBIETER['strasse']} · {mail_layout.ANBIETER['plz_ort']}"
            ),
        )

    def sende_konto_bestaetigung(self, email: str, name: str, url: str) -> bool:
        """Bestaetigung der E-Mail-Adresse eines Kontos (nicht eines Leads)."""
        html = self._rahmen(
            "Bitte E-Mail-Adresse bestätigen",
            f"Hallo {mail_layout.escape(name)}, für diese Adresse wurde ein complyo-Konto angelegt. "
            "Mit der Bestätigung ist sichergestellt, dass Hinweise zu Fristen und "
            "Rechtsänderungen Sie auch erreichen.",
            "Adresse bestätigen", url,
            "Wenn Sie kein Konto angelegt haben, können Sie diese Nachricht ignorieren. "
            "Ohne Bestätigung passiert nichts weiter.",
        )
        text = (
            f"Hallo {name},\n\n"
            "für diese Adresse wurde ein complyo-Konto angelegt. "
            "Bitte bestätigen Sie die Adresse:\n\n"
            f"{url}\n\n"
            "Wenn Sie kein Konto angelegt haben, ignorieren Sie diese Nachricht.\n"
        )
        return self._send_email(email, "complyo: E-Mail-Adresse bestätigen", html, text)

    def sende_passwort_zuruecksetzen(self, email: str, name: str, url: str,
                                     gueltig_minuten: int) -> bool:
        html = self._rahmen(
            "Passwort zurücksetzen",
            f"Hallo {mail_layout.escape(name)}, für Ihr complyo-Konto wurde ein neues Passwort angefordert. "
            f"Der Link gilt {gueltig_minuten} Minuten und lässt sich einmal verwenden.",
            "Neues Passwort setzen", url,
            "Wenn Sie das nicht waren, ist nichts passiert: Ihr Passwort bleibt "
            "unverändert, solange dieser Link nicht benutzt wird. Sie müssen nichts tun. "
            "Häufen sich solche Nachrichten, melden Sie sich bitte bei uns.",
        )
        text = (
            f"Hallo {name},\n\n"
            "für Ihr complyo-Konto wurde ein neues Passwort angefordert.\n"
            f"Der folgende Link gilt {gueltig_minuten} Minuten und nur einmal:\n\n"
            f"{url}\n\n"
            "Wenn Sie das nicht waren, müssen Sie nichts tun — Ihr Passwort bleibt "
            "unverändert, solange der Link nicht benutzt wird.\n"
        )
        return self._send_email(email, "complyo: Passwort zurücksetzen", html, text)

    def sende_loeschankuendigung(self, email: str, name: str, tage: int,
                                 anmelde_url: str) -> bool:
        """
        Ankuendigung der Loeschung eines ruhenden Kontos.

        Die Loeschung selbst ist die Pflicht (Art. 5 Abs. 1 lit. e) — die
        Ankuendigung ist die Fairness. Eine einzige Anmeldung genuegt, um sie
        abzuwenden.
        """
        html = self._rahmen(
            "Ihr complyo-Konto wird gelöscht",
            f"Hallo {mail_layout.escape(name)}, Ihr Konto wurde lange nicht genutzt. Nach den eigenen "
            "Löschfristen von complyo werden Daten nicht länger aufbewahrt, als der "
            f"Zweck es trägt. Ihr Konto und alle zugehörigen Daten werden deshalb in "
            f"{tage} Tagen gelöscht. Eine einzige Anmeldung genügt, um das abzuwenden.",
            "Jetzt anmelden und Konto behalten", anmelde_url,
            "Wenn Sie das Konto nicht mehr brauchen, müssen Sie nichts tun. "
            "Die Löschung erfolgt dann automatisch und vollständig.",
        )
        text = (
            f"Hallo {name},\n\n"
            f"Ihr complyo-Konto wurde lange nicht genutzt und wird in {tage} Tagen "
            "mit allen zugehörigen Daten gelöscht.\n\n"
            f"Eine einzige Anmeldung genügt, um das abzuwenden:\n{anmelde_url}\n\n"
            "Wenn Sie das Konto nicht mehr brauchen, müssen Sie nichts tun.\n"
        )
        return self._send_email(email, "complyo: Ihr Konto wird in "
                                       f"{tage} Tagen gelöscht", html, text)


# Global email service instance
email_service = EmailService()