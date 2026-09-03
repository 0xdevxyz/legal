"""
GDPR Data Retention and Deletion Service
Handles automated data retention compliance and right to be forgotten requests

Seit 2026-08-11 decken Export (Art. 15/20) und Löschantrag (Art. 17) auch die
users-Tabelle samt zugehöriger Tabellen ab — vorher erfassten beide Wege nur
die leere leads-Tabelle, die echten Kundenkonten waren unerreichbar.
Löschung von Kundenkonten läuft ZWEISTUFIG über gdpr_deletion_requests:
Antrag (pending) → Bestätigung (confirmed) → Löschlauf (completed).
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from database_service import db_service
import os

logger = logging.getLogger(__name__)


def _json_tauglich(wert: Any) -> Any:
    """Rekursiv in JSON-serialisierbare Werte wandeln (datetime, Decimal,
    UUID, date …) — der Export geht als JSONResponse UND als Mailanhang raus,
    beide Wege scheitern sonst still an asyncpg-Typen."""
    import uuid as _uuid
    from datetime import date as _date
    from decimal import Decimal as _Decimal

    if isinstance(wert, dict):
        return {k: _json_tauglich(v) for k, v in wert.items()}
    if isinstance(wert, (list, tuple)):
        return [_json_tauglich(v) for v in wert]
    if isinstance(wert, (datetime, _date)):
        return wert.isoformat()
    if isinstance(wert, _Decimal):
        return float(wert)
    if isinstance(wert, _uuid.UUID):
        return str(wert)
    if isinstance(wert, (str, int, float, bool)) or wert is None:
        return wert
    return str(wert)


def _zeile_als_dict(row) -> Dict[str, Any]:
    """asyncpg.Record → JSON-taugliches Dict."""
    return _json_tauglich(dict(row))


class GDPRRetentionService:
    def __init__(self):
        # 730 Tage = 24 Monate — die eine, einheitliche Aufbewahrungsfrist.
        self.retention_period_days = int(os.getenv("GDPR_RETENTION_DAYS", "730"))
        self.cleanup_interval_hours = int(os.getenv("GDPR_CLEANUP_INTERVAL_HOURS", "24"))  # Daily cleanup
        self.is_running = False
        self.deletion_log = []

    async def start_automated_cleanup(self):
        """Start the automated GDPR cleanup process"""
        if self.is_running:
            logger.warning("GDPR cleanup already running")
            return

        self.is_running = True
        logger.info(f"Starting GDPR automated cleanup - retention period: {self.retention_period_days} days")

        while self.is_running:
            try:
                await self.perform_retention_cleanup()
                await asyncio.sleep(self.cleanup_interval_hours * 3600)  # Convert hours to seconds
            except Exception as e:
                logger.error(f"Error in automated cleanup: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes before retry

    def stop_automated_cleanup(self):
        """Stop the automated cleanup process"""
        self.is_running = False
        logger.info("GDPR automated cleanup stopped")

    async def perform_retention_cleanup(self) -> Dict[str, Any]:
        """
        Perform GDPR data retention cleanup
        Deletes leads that have exceeded their retention period
        """
        cleanup_results = {
            "timestamp": datetime.now().isoformat(),
            "leads_checked": 0,
            "leads_deleted": 0,
            "deletion_requests_processed": 0,
            "user_deletions_completed": 0,
            "errors": []
        }

        try:

            # Get leads that need to be deleted due to retention policy
            expired_leads = await db_service.get_leads_for_retention_cleanup()
            cleanup_results["leads_checked"] = len(expired_leads)

            for lead in expired_leads:
                try:
                    # Send deletion notification before deleting (if email still valid)
                    await self._send_deletion_notification(lead)

                    # Permanently delete the lead
                    success = await db_service.delete_lead_permanently(lead["id"])

                    if success:
                        cleanup_results["leads_deleted"] += 1

                        # Log the deletion
                        deletion_log_entry = {
                            "lead_id": lead["id"],
                            "email": lead["email"],
                            "deletion_reason": "automatic_retention_cleanup",
                            "retention_expired_date": lead["data_retention_until"],
                            "deleted_at": datetime.now().isoformat()
                        }
                        self.deletion_log.append(deletion_log_entry)

                        logger.info(f"Deleted expired lead: {lead['email']} (ID: {lead['id']})")
                    else:
                        cleanup_results["errors"].append(f"Failed to delete lead {lead['id']}")

                except Exception as e:
                    error_msg = f"Error deleting lead {lead['id']}: {str(e)}"
                    cleanup_results["errors"].append(error_msg)
                    logger.error(error_msg)

            # Zweite Stufe für Lead-Löschanträge (deletion_requested = TRUE):
            # der Antrag wurde beim Eingang nur markiert, gelöscht wird hier.
            deletion_requests = await self._get_pending_deletion_requests()

            for request in deletion_requests:
                try:
                    success = await self.process_deletion_request(request["lead_id"], "right_to_be_forgotten")
                    if success:
                        cleanup_results["deletion_requests_processed"] += 1
                except Exception as e:
                    error_msg = f"Error processing deletion request {request['lead_id']}: {str(e)}"
                    cleanup_results["errors"].append(error_msg)
                    logger.error(error_msg)

            # Zweite Stufe für Kundenkonten: bestätigte, aber noch nicht
            # ausgeführte Löschanträge aus gdpr_deletion_requests abarbeiten.
            try:
                erledigt = await self.process_confirmed_user_deletions()
                cleanup_results["user_deletions_completed"] = erledigt
            except Exception as e:
                error_msg = f"Fehler beim Abarbeiten bestätigter Konto-Löschanträge: {e}"
                cleanup_results["errors"].append(error_msg)
                logger.error(error_msg)

            logger.info(f"GDPR cleanup completed: {cleanup_results['leads_deleted']} leads deleted, "
                       f"{cleanup_results['deletion_requests_processed']} deletion requests processed, "
                       f"{cleanup_results['user_deletions_completed']} Kontolöschungen ausgeführt")

            return cleanup_results

        except Exception as e:
            logger.error(f"Error in retention cleanup: {e}")
            cleanup_results["errors"].append(str(e))
            return cleanup_results

    async def process_deletion_request(self, lead_id: str, reason: str = "user_request") -> bool:
        """
        Process a right to be forgotten request
        """
        try:
            # Lead wirklich laden — vorher stand hier ein Platzhalter
            # {"email": "unknown"}, der die Löschbestätigung ins Leere schickte.
            lead = await db_service.get_lead_by_id(lead_id)

            if not lead:
                logger.warning(f"Lead {lead_id} not found for deletion request")
                return False

            # Send deletion confirmation email
            await self._send_deletion_confirmation(lead)

            # Mark for deletion first
            await db_service.mark_lead_for_deletion(lead_id)

            # Permanently delete the lead and all associated data
            success = await db_service.delete_lead_permanently(lead_id)

            if success:
                # Log the deletion
                deletion_log_entry = {
                    "lead_id": lead_id,
                    "email": lead.get("email", "unknown"),
                    "deletion_reason": reason,
                    "requested_at": datetime.now().isoformat(),
                    "deleted_at": datetime.now().isoformat(),
                    "gdpr_article": "Article 17 - Right to erasure"
                }
                self.deletion_log.append(deletion_log_entry)

                logger.info(f"Processed GDPR deletion request for lead {lead_id} - Reason: {reason}")
                return True
            else:
                logger.error(f"Failed to delete lead {lead_id}")
                return False

        except Exception as e:
            logger.error(f"Error processing deletion request for lead {lead_id}: {e}")
            return False

    async def request_data_deletion(self, email: str, reason: str = "user_request") -> Dict[str, Any]:
        """
        Handle user request for data deletion (right to be forgotten)

        Zweistufig: hier wird nur MARKIERT (deletion_requested = TRUE),
        gelöscht wird im nächsten Cleanup-Lauf. Vorher löschte dieser Weg
        sofort und unwiderruflich — ohne jede Bestätigungsstufe.
        """
        try:
            # Find lead by email
            lead = await db_service.get_lead_by_email(email)

            if not lead:
                return {
                    "success": False,
                    "message": "No data found for the provided email address",
                    "email": email
                }

            markiert = await db_service.mark_lead_for_deletion(lead["id"])

            if markiert:
                return {
                    "success": True,
                    "message": ("Ihr Löschantrag wurde registriert. Die Löschung wird "
                                "im nächsten Bereinigungslauf ausgeführt; Sie erhalten "
                                "eine Bestätigung per E-Mail."),
                    "email": email,
                    "requested_at": datetime.now().isoformat(),
                    "reference_id": lead["id"]
                }
            else:
                return {
                    "success": False,
                    "message": "Failed to process deletion request. Please contact support.",
                    "email": email
                }

        except Exception as e:
            logger.error(f"Error processing data deletion request for {email}: {e}")
            return {
                "success": False,
                "message": "An error occurred while processing your request",
                "email": email,
                "error": str(e)
            }

    # ==================== BETROFFENENRECHTE FÜR KUNDENKONTEN (users) ====================

    # Export: Tabellenname → (Anzeigename, Query). Bewusst kuratierte Spalten:
    # keine Passwort-Hashes, keine Session-/OAuth-Tokens, keine Mega-JSONBs
    # (Scan-Rohdaten sind Daten ÜBER die Website, nicht über die Person).
    _EXPORT_ABFRAGEN = [
        ("rechnungsdaten",
         "SELECT company_name, tax_id, company_address, created_at, updated_at "
         "FROM user_company_data WHERE user_id = $1"),
        ("firmenprofil",
         "SELECT answers, created_at, updated_at FROM company_profiles WHERE user_id = $1"),
        ("tarif_und_limits",
         "SELECT plan_type, websites_count, websites_max, exports_this_month, exports_max, "
         "fixes_used, fixes_limit, locked_domain, jurisdiction, subscription_start, created_at "
         "FROM user_limits WHERE user_id = $1"),
        ("abonnements",
         "SELECT plan_type, status, started_at, refund_eligible, refund_deadline, created_at "
         "FROM subscriptions WHERE user_id = $1 ORDER BY created_at"),
        ("zahlungsreferenz",
         "SELECT stripe_customer_id, email, created_at FROM stripe_customers WHERE user_id = $1"),
        ("addons",
         "SELECT addon_key, addon_name, status, price_monthly, started_at, expires_at, cancelled_at "
         "FROM user_addons WHERE user_id = $1 ORDER BY started_at"),
        ("module",
         "SELECT module_id, status, enabled_at, cancelled_at, expires_at "
         "FROM user_modules WHERE user_id = $1 ORDER BY enabled_at"),
        ("websites",
         "SELECT url, name, status, last_scan_date, last_score, scan_count, jurisdiction, created_at "
         "FROM tracked_websites WHERE user_id = $1 ORDER BY created_at"),
        ("scans",
         "SELECT scan_id, url, scan_date, overall_score, compliance_score, accessibility_score, "
         "issues_count, critical_issues, created_at "
         "FROM scan_history WHERE user_id = $1 ORDER BY scan_date"),
        ("generierte_dokumente",
         "SELECT document_type, title, status, language, created_at, updated_at "
         "FROM generated_documents WHERE user_id = $1 ORDER BY created_at"),
        ("domain_freischaltungen",
         "SELECT domain_name, fixes_used, fixes_limit, is_unlocked, created_at, unlocked_at "
         "FROM domain_locks WHERE user_id = $1 ORDER BY created_at"),
        ("ki_systeme",
         "SELECT name, description, vendor, purpose, risk_category, compliance_score, status, "
         "domain, created_at FROM ai_systems WHERE user_id = $1 ORDER BY created_at"),
        ("cookie_tiefenscans",
         "SELECT url, status, total_cookies, unique_services, total_requests, created_at "
         "FROM deep_cookie_scans WHERE user_id = $1 ORDER BY created_at"),
        ("anmeldesitzungen",
         "SELECT created_at, expires_at, last_used_at, user_agent, ip_address "
         "FROM user_sessions WHERE user_id = $1 ORDER BY created_at"),
        ("oauth_verknuepfungen",
         "SELECT provider, provider_email, created_at FROM oauth_providers WHERE user_id = $1"),
        ("rechts_benachrichtigungen",
         "SELECT notification_type, is_read, created_at, read_at "
         "FROM user_legal_notifications WHERE user_id = $1 ORDER BY created_at"),
        ("loeschantraege",
         "SELECT status, reason, requested_at, confirmed_at, completed_at "
         "FROM gdpr_deletion_requests WHERE user_id = $1 ORDER BY requested_at"),
    ]

    async def export_user_data(self, user_id: int, email: str) -> Optional[Dict[str, Any]]:
        """
        Aggregierter DSGVO-Export (Art. 15/20) über alle personenbezogenen
        Tabellen eines Kundenkontos. Liefert None, wenn das Konto nicht existiert.
        """
        export: Dict[str, Any] = {
            "export_info": {
                "user_id": user_id,
                "email": email,
                "generated_at": datetime.now().isoformat(),
                "gdpr_articles": [
                    "Art. 15 DSGVO - Auskunftsrecht",
                    "Art. 20 DSGVO - Recht auf Datenübertragbarkeit",
                ],
                "hinweis": ("Scan-Rohdaten und generierte Dokumentinhalte sind Daten über "
                            "Ihre Website bzw. Werkergebnisse und als Metadaten aufgeführt."),
            }
        }
        try:
            async with db_service.get_connection() as conn:
                konto = await conn.fetchrow(
                    "SELECT id, email, full_name, company, is_active, is_verified, "
                    "onboarding_completed, plan_type, role, created_at, updated_at "
                    "FROM users WHERE id = $1",
                    user_id,
                )
                if not konto:
                    return None
                export["konto"] = _zeile_als_dict(konto)

                # Tabellenweise sammeln — eine fehlende Tabelle (z. B.
                # gdpr_deletion_requests vor der Migration) darf den
                # Gesamtexport nicht kippen.
                for name, query in self._EXPORT_ABFRAGEN:
                    try:
                        zeilen = await conn.fetch(query, user_id)
                        export[name] = [_zeile_als_dict(z) for z in zeilen]
                    except Exception as e:
                        logger.warning(f"DSGVO-Export: Kategorie {name} übersprungen: {e}")
                        export[name] = {"fehler": "Kategorie derzeit nicht abrufbar"}

            # Alt-Daten aus der Lead-Erfassung (gleiche E-Mail) mitliefern.
            try:
                lead_export = await self.get_data_for_export(email)
                if lead_export:
                    export["legacy_lead_daten"] = lead_export
            except Exception as e:
                logger.warning(f"DSGVO-Export: Lead-Altdaten übersprungen: {e}")

            logger.info(f"DSGVO-Export für Konto {user_id} ({email}) erstellt")
            return _json_tauglich(export)

        except Exception as e:
            logger.error(f"Fehler beim DSGVO-Export für Konto {user_id}: {e}")
            return None

    async def request_user_deletion(self, user_id: int, email: str,
                                    reason: str = "user_request") -> Dict[str, Any]:
        """
        Stufe 1 der Kontolöschung (Art. 17 DSGVO): Antrag registrieren.
        KEINE sofortige Löschung — erst der Bestätigungslauf
        (confirm_user_deletion / process_confirmed_user_deletions) löscht.
        """
        try:
            async with db_service.get_connection() as conn:
                offen = await conn.fetchrow(
                    "SELECT id, status, requested_at FROM gdpr_deletion_requests "
                    "WHERE user_id = $1 AND status IN ('pending', 'confirmed')",
                    user_id,
                )
                if offen:
                    return {
                        "success": True,
                        "already_requested": True,
                        "message": "Für dieses Konto liegt bereits ein offener Löschantrag vor.",
                        "status": offen["status"],
                        "requested_at": offen["requested_at"].isoformat(),
                    }

                antrag = await conn.fetchrow(
                    "INSERT INTO gdpr_deletion_requests (user_id, email, reason, status) "
                    "VALUES ($1, $2, $3, 'pending') RETURNING id, requested_at",
                    user_id, email, reason,
                )

            # Alt-Lead mit derselben E-Mail gleich mit zur Löschung vormerken.
            try:
                lead = await db_service.get_lead_by_email(email)
                if lead:
                    await db_service.mark_lead_for_deletion(lead["id"])
            except Exception as e:
                logger.warning(f"Lead-Vormerkung bei Kontolöschantrag {user_id} fehlgeschlagen: {e}")

            # Eingangsbestätigung — Rückgabewert respektieren, nicht so tun
            # als wäre verschickt worden.
            email_versandt = self._send_user_deletion_received(email, antrag["id"])

            logger.info(f"Kontolöschantrag {antrag['id']} für User {user_id} registriert")
            return {
                "success": True,
                "message": ("Ihr Löschantrag wurde registriert. Nach Prüfung wird Ihr Konto "
                            "mit allen personenbezogenen Daten gelöscht; Sie erhalten eine "
                            "Bestätigung per E-Mail."),
                "reference_id": antrag["id"],
                "requested_at": antrag["requested_at"].isoformat(),
                "email_sent": email_versandt,
                "gdpr_article": "Art. 17 DSGVO - Recht auf Löschung",
            }

        except Exception as e:
            logger.error(f"Fehler beim Kontolöschantrag für User {user_id}: {e}")
            return {
                "success": False,
                "message": "Der Löschantrag konnte nicht registriert werden. "
                           "Bitte wenden Sie sich an datenschutz@complyo.de.",
            }

    async def cancel_user_deletion(self, user_id: int) -> bool:
        """Offenen Löschantrag zurückziehen (nur solange nicht ausgeführt)."""
        try:
            async with db_service.get_connection() as conn:
                ergebnis = await conn.execute(
                    "UPDATE gdpr_deletion_requests SET status = 'cancelled' "
                    "WHERE user_id = $1 AND status IN ('pending', 'confirmed')",
                    user_id,
                )
            return ergebnis.split()[-1] != "0"
        except Exception as e:
            logger.error(f"Fehler beim Zurückziehen des Löschantrags für User {user_id}: {e}")
            return False

    async def get_user_deletion_status(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Aktuellster Löschantrag eines Kontos (oder None)."""
        try:
            async with db_service.get_connection() as conn:
                zeile = await conn.fetchrow(
                    "SELECT id, status, reason, requested_at, confirmed_at, completed_at "
                    "FROM gdpr_deletion_requests WHERE user_id = $1 "
                    "ORDER BY requested_at DESC LIMIT 1",
                    user_id,
                )
            return _zeile_als_dict(zeile) if zeile else None
        except Exception as e:
            logger.error(f"Fehler beim Lesen des Löschantrag-Status für User {user_id}: {e}")
            return None

    async def confirm_user_deletion(self, user_id: int, confirmed_by: int) -> Dict[str, Any]:
        """
        Stufe 2 der Kontolöschung: Admin bestätigt den Antrag, danach wird
        sofort gelöscht. confirmed_by = Admin-User-ID (Rechenschaftspflicht).
        """
        try:
            async with db_service.get_connection() as conn:
                antrag = await conn.fetchrow(
                    "UPDATE gdpr_deletion_requests "
                    "SET status = 'confirmed', confirmed_at = NOW(), confirmed_by = $2 "
                    "WHERE user_id = $1 AND status = 'pending' "
                    "RETURNING id, email",
                    user_id, confirmed_by,
                )
            if not antrag:
                return {"success": False,
                        "message": "Kein offener Löschantrag für dieses Konto gefunden."}

            geloescht = await self._execute_user_deletion(user_id, antrag["email"], antrag["id"])
            if geloescht:
                return {"success": True,
                        "message": f"Konto {user_id} wurde gelöscht.",
                        "reference_id": antrag["id"]}
            return {"success": False,
                    "message": "Löschantrag bestätigt, Ausführung fehlgeschlagen — "
                               "wird im nächsten Bereinigungslauf erneut versucht.",
                    "reference_id": antrag["id"]}

        except Exception as e:
            logger.error(f"Fehler beim Bestätigen des Löschantrags für User {user_id}: {e}")
            return {"success": False, "message": "Bestätigung fehlgeschlagen."}

    async def process_confirmed_user_deletions(self) -> int:
        """Bestätigte, noch nicht ausgeführte Kontolöschungen abarbeiten."""
        erledigt = 0
        try:
            async with db_service.get_connection() as conn:
                antraege = await conn.fetch(
                    "SELECT id, user_id, email FROM gdpr_deletion_requests "
                    "WHERE status = 'confirmed'"
                )
        except Exception as e:
            # Tabelle existiert erst nach der Migration — kein Fehler des Laufs.
            logger.info(f"gdpr_deletion_requests nicht abfragbar (Migration ausstehend?): {e}")
            return 0

        for antrag in antraege:
            if await self._execute_user_deletion(antrag["user_id"], antrag["email"], antrag["id"]):
                erledigt += 1
        return erledigt

    # Löschreihenfolge für Tabellen OHNE ON-DELETE-CASCADE auf users(id).
    # Die kaskadierenden Tabellen (user_modules, user_addons, domain_locks,
    # ai_systems, company_profiles, user_sessions, oauth_providers, …) räumt
    # das DELETE auf users selbst ab.
    _LOESCH_STATEMENTS = [
        # Referenzen auf den User als Bearbeiter → anonymisieren, nicht löschen
        ("UPDATE ai_documentation SET approved_by = NULL WHERE approved_by = $1"),
        ("UPDATE compliance_fixes SET applied_by = NULL WHERE applied_by = $1"),
        ("UPDATE cookie_banner_revisions SET changed_by = NULL WHERE changed_by = $1"),
        # FK ohne Cascade → muss vor users weg
        ("DELETE FROM stripe_customers WHERE user_id = $1"),
        # Abhängige von user_limits zuerst
        ("DELETE FROM export_history WHERE user_id = $1"),
        ("DELETE FROM generated_fixes WHERE user_id = $1"),
        ("DELETE FROM user_limits WHERE user_id = $1"),
        # Tabellen ganz ohne FK auf users
        ("DELETE FROM scan_history WHERE user_id = $1"),
        ("DELETE FROM generated_documents WHERE user_id = $1"),
        ("DELETE FROM user_company_data WHERE user_id = $1"),
        ("DELETE FROM tracked_websites WHERE user_id = $1"),
        ("DELETE FROM subscriptions WHERE user_id = $1"),
        # Zuletzt das Konto selbst — kaskadiert in die FK-Tabellen
        ("DELETE FROM users WHERE id = $1"),
    ]

    async def _execute_user_deletion(self, user_id: int, email: str, antrag_id: int) -> bool:
        """Bestätigten Löschantrag ausführen (transaktional) und protokollieren."""
        try:
            async with db_service.get_connection() as conn:
                async with conn.transaction():
                    for statement in self._LOESCH_STATEMENTS:
                        await conn.execute(statement, user_id)
                await conn.execute(
                    "UPDATE gdpr_deletion_requests "
                    "SET status = 'completed', completed_at = NOW() WHERE id = $1",
                    antrag_id,
                )

            self.deletion_log.append({
                "lead_id": f"user:{user_id}",
                "email": email,
                "deletion_reason": "right_to_be_forgotten",
                "deleted_at": datetime.now().isoformat(),
                "gdpr_article": "Article 17 - Right to erasure",
            })

            # Löschbestätigung an die (extern weiterhin erreichbare) Adresse.
            versandt = self._send_user_deletion_completed(email, antrag_id)
            if not versandt:
                logger.error("Löschbestätigung für Konto %s an %s NICHT verschickt",
                             user_id, email)

            logger.info(f"Konto {user_id} ({email}) DSGVO-konform gelöscht (Antrag {antrag_id})")
            return True

        except Exception as e:
            logger.error(f"Fehler beim Löschen von Konto {user_id} (Antrag {antrag_id}): {e}")
            return False

    def _send_user_deletion_received(self, email: str, antrag_id: int) -> bool:
        """Eingangsbestätigung für einen Kontolöschantrag. Gibt Versandstatus zurück."""
        try:
            from email_service import email_service
            inhalt = f"""
            Sehr geehrte Damen und Herren,

            wir haben Ihren Antrag auf Löschung Ihres Complyo-Kontos erhalten
            (Art. 17 DSGVO, Referenz {antrag_id}).

            Die Löschung wird nach Prüfung ausgeführt; Sie erhalten dann eine
            abschließende Bestätigung. Bis dahin können Sie den Antrag im
            Dashboard oder per E-Mail an datenschutz@complyo.de zurückziehen.

            Mit freundlichen Grüßen,
            Ihr Complyo Team
            """
            return email_service._send_email(
                to_email=email,
                subject="Ihr Löschantrag ist eingegangen - Complyo",
                html_body=inhalt.replace("\n", "<br>"),
                text_body=inhalt,
            )
        except Exception as e:
            logger.error(f"Fehler beim Senden der Antragseingangs-Mail an {email}: {e}")
            return False

    def _send_user_deletion_completed(self, email: str, antrag_id: int) -> bool:
        """Abschlussbestätigung nach ausgeführter Kontolöschung."""
        try:
            from email_service import email_service
            return email_service.send_deletion_confirmation_email(email, f"user-{antrag_id}")
        except Exception as e:
            logger.error(f"Fehler beim Senden der Löschbestätigung an {email}: {e}")
            return False

    async def get_data_for_export(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Export all data for a lead (GDPR data portability)
        """
        try:
            lead = await db_service.get_lead_by_email(email)

            if not lead:
                return None

            # Prepare comprehensive data export
            export_data = {
                "personal_data": {
                    "email": lead.get("email"),
                    "name": lead.get("name"),
                    "company": lead.get("company"),
                    "created_at": lead.get("created_at"),
                    "verified_at": lead.get("verified_at")
                },
                "consent_data": {
                    "consent_given": lead.get("consent_given"),
                    "consent_timestamp": lead.get("consent_timestamp"),
                    "consent_ip_address": lead.get("consent_ip_address"),
                    "legal_basis": lead.get("legal_basis")
                },
                "analysis_data": lead.get("analysis_data"),
                "technical_data": {
                    "source": lead.get("source"),
                    "session_id": lead.get("session_id"),
                    "url_analyzed": lead.get("url_analyzed"),
                    "email_verified": lead.get("email_verified"),
                    "status": lead.get("status")
                },
                "gdpr_data": {
                    "data_retention_until": lead.get("data_retention_until"),
                    "deletion_requested": lead.get("deletion_requested", False),
                    "export_generated_at": datetime.now().isoformat()
                }
            }

            logger.info(f"Generated data export for {email}")
            return export_data

        except Exception as e:
            logger.error(f"Error generating data export for {email}: {e}")
            return None

    async def update_retention_period(self, lead_id: str, new_retention_days: int) -> bool:
        """
        Update the data retention period for a specific lead
        """
        try:
            new_retention_date = datetime.now() + timedelta(days=new_retention_days)

            async with db_service.get_connection() as conn:
                query = """
                UPDATE leads SET
                    data_retention_until = $1,
                    updated_at = $2
                WHERE id = $3
                """
                await conn.execute(query, new_retention_date, datetime.now(), lead_id)
                logger.info(f"Updated retention period for lead {lead_id} to {new_retention_days} days")
                return True

        except Exception as e:
            logger.error(f"Error updating retention period for lead {lead_id}: {e}")
            return False

    async def _send_deletion_notification(self, lead: Dict[str, Any]):
        """Send notification before automatic deletion"""
        try:
            subject = "Automatische Löschung Ihrer Daten - Complyo"

            # Create notification email content
            email_content = f"""
            Sehr geehrte/r {lead.get('name', 'Kunde/Kundin')},

            gemäß der Datenschutz-Grundverordnung (DSGVO) werden Ihre Daten automatisch nach Ablauf
            der Aufbewahrungsfrist gelöscht.

            Ihre Daten wurden am {lead.get('data_retention_until', 'unbekannt')} zur Löschung vorgesehen.

            Falls Sie Fragen haben, kontaktieren Sie uns unter datenschutz@complyo.de.

            Mit freundlichen Grüßen,
            Ihr Complyo Team
            """

            # Frueher stand hier nur "Would send actual email in production"
            # samt einer Logzeile, die so tat, als waere etwas passiert.
            # Fuer einen Anbieter, der DSGVO-Konformitaet verkauft, ist eine
            # nicht verschickte Loeschankuendigung kein Schoenheitsfehler.
            from email_service import email_service
            versandt = email_service._send_email(
                to_email=lead["email"], subject=subject,
                html_body=email_content.replace("\n", "<br>"),
                text_body=email_content)
            if versandt:
                logger.info("Loeschankuendigung an %s verschickt", lead["email"])
            else:
                logger.error("Loeschankuendigung an %s NICHT verschickt",
                             lead["email"])

        except Exception as e:
            logger.error(f"Error sending deletion notification: {e}")

    async def _send_deletion_confirmation(self, lead: Dict[str, Any]):
        """Send confirmation after deletion"""
        try:
            subject = "Bestätigung der Datenlöschung - Complyo"

            email_content = f"""
            Sehr geehrte/r {lead.get('name', 'Kunde/Kundin')},

            hiermit bestätigen wir die vollständige Löschung Ihrer personenbezogenen Daten
            aus unserem System gemäß Artikel 17 DSGVO (Recht auf Vergessenwerden).

            Löschung durchgeführt am: {datetime.now().strftime('%d.%m.%Y %H:%M')}
            Referenz-ID: {lead['id']}

            Ihre Daten wurden permanent und unwiderruflich gelöscht.

            Mit freundlichen Grüßen,
            Ihr Complyo Team
            """

            # Wie die Ankuendigung: sie wurde nie verschickt, die Logzeile
            # tat nur so. Eine Loeschbestaetigung nach Art. 17 DSGVO ist die
            # Zusage, die ein Betroffener am ehesten einfordert.
            from email_service import email_service
            versandt = email_service._send_email(
                to_email=lead["email"], subject=subject,
                html_body=email_content.replace("\n", "<br>"),
                text_body=email_content)
            if versandt:
                logger.info("Loeschbestaetigung an %s verschickt", lead["email"])
            else:
                logger.error("Loeschbestaetigung an %s NICHT verschickt",
                             lead["email"])

        except Exception as e:
            logger.error(f"Error sending deletion confirmation: {e}")

    async def _get_pending_deletion_requests(self) -> List[Dict[str, Any]]:
        """Get leads marked for deletion"""
        try:
            async with db_service.get_connection() as conn:
                query = """
                SELECT id as lead_id, email
                FROM leads
                WHERE deletion_requested = TRUE
                """
                rows = await conn.fetch(query)
                return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Error getting pending deletion requests: {e}")
            return []

    def get_deletion_statistics(self) -> Dict[str, Any]:
        """Get statistics about deletions performed"""
        return {
            "total_deletions": len(self.deletion_log),
            "automatic_deletions": len([d for d in self.deletion_log if d["deletion_reason"] == "automatic_retention_cleanup"]),
            "user_requested_deletions": len([d for d in self.deletion_log if d["deletion_reason"] in ["user_request", "right_to_be_forgotten"]]),
            "recent_deletions": [d for d in self.deletion_log if
                               datetime.fromisoformat(d["deleted_at"]) > datetime.now() - timedelta(days=30)],
            "retention_period_days": self.retention_period_days,
            "cleanup_interval_hours": self.cleanup_interval_hours
        }

# Global GDPR retention service instance
gdpr_service = GDPRRetentionService()
