"""
GDPR API Endpoints for Data Rights Management
Implements GDPR Articles 15/17/20 (Access, Erasure, Portability)

Seit 2026-08-11 erfassen Export und Löschung das KUNDENKONTO (users-Tabelle
samt zugehöriger Tabellen) — vorher liefen beide Rechte ins Leere, weil nur
die leere leads-Tabelle abgefragt wurde. Löschung ist zweistufig
(Antrag → Bestätigungslauf), siehe gdpr_retention_service.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel
from typing import Optional
import logging
from gdpr_retention_service import gdpr_service
from email_service import email_service
from dependencies import get_current_user, require_admin

logger = logging.getLogger(__name__)

gdpr_router = APIRouter(prefix="/api/gdpr", tags=["gdpr"])

# Einheitliche Aufbewahrungsfrist — 24 Monate (= 730 Tage, GDPR_RETENTION_DAYS).
# Frühere Texte nannten je nach Stelle 24 Monate, 3 Jahre oder 1 Jahr.
RETENTION_MONATE = 24


async def get_verified_user(current_user: dict = Depends(get_current_user)) -> dict:
    """Liefert den Betroffenen AUSSCHLIESSLICH aus dem JWT.

    Verhindert IDOR (Muster: legal_text_routes.get_current_user_id): Bis 2026-07-17
    identifizierten /request-deletion, /export-data und /retention-info den
    Betroffenen allein über eine frei wählbare E-Mail im Request-Body bzw. in der
    Query. Damit konnte jeder Anonyme die Daten beliebiger Dritter exportieren
    ODER löschen lassen — Art. 17/20 DSGVO als Waffe gegen den Betroffenen.

    Bewusste Entscheidung gegen einen "Besucher-Pfad": Ein Betroffenenrecht darf
    erst nach Identitätsnachweis (Art. 12 Abs. 6 DSGVO) erfüllt werden. Einen
    verifizierten Token-Flow für Nicht-Kunden gibt es hier nicht. Nicht-Kunden
    nutzen daher den manuellen Weg, den GET /privacy-policy ohnehin ausweist:
    datenschutz@complyo.de. Die Landing-Seite landing-react/src/app/gdpr/page.tsx
    verweist entsprechend auf Login bzw. den E-Mail-Weg.
    """
    if not current_user.get("email"):
        raise HTTPException(status_code=401, detail="Nicht authentifiziert")
    return current_user


async def get_verified_email(current_user: dict = Depends(get_current_user)) -> str:
    """E-Mail des Betroffenen aus dem JWT (siehe get_verified_user)."""
    email = current_user.get("email")
    if not email:
        raise HTTPException(status_code=401, detail="Nicht authentifiziert")
    return str(email)


class DataDeletionRequest(BaseModel):
    # Kein `email`-Feld mehr: Der Betroffene ergibt sich aus dem Token, nicht aus
    # dem Body. Ein mitgesendetes Feld würde nur zur Wiedereinführung der Lücke
    # einladen.
    reason: Optional[str] = "user_request"
    confirmation: bool = True

class DataExportRequest(BaseModel):
    # Absichtlich leer — die E-Mail kommt aus dem JWT (siehe get_verified_user).
    pass

class RetentionUpdateRequest(BaseModel):
    lead_id: str
    retention_days: int

class DeletionConfirmRequest(BaseModel):
    user_id: int

@gdpr_router.post("/request-deletion")
async def request_data_deletion(
    request: DataDeletionRequest,
    current_user: dict = Depends(get_verified_user),
):
    """
    Handle user request for data deletion (GDPR Article 17 - Right to Erasure)

    Betroffener = Token-Inhaber. ZWEISTUFIG: hier wird der Antrag registriert
    (gdpr_deletion_requests, status 'pending'), gelöscht wird erst nach
    Bestätigung. Keine sofortige Hard-Delete-Kaskade mehr.
    """
    try:
        if not request.confirmation:
            raise HTTPException(
                status_code=400,
                detail="Data deletion requires explicit confirmation"
            )

        email = str(current_user["email"])
        user_id = int(current_user["id"])
        logger.info(f"Registriere Kontolöschantrag für User {user_id}")

        result = await gdpr_service.request_user_deletion(
            user_id, email, request.reason
        )

        if result["success"]:
            return {
                "success": True,
                "message": result["message"],
                "details": {
                    "email": email,
                    "requested_at": result.get("requested_at"),
                    "reference_id": result.get("reference_id"),
                    "status": result.get("status", "pending"),
                    "gdpr_article": "Article 17 - Right to erasure ('right to be forgotten')"
                }
            }
        else:
            return {
                "success": False,
                "message": result["message"],
                "email": email
            }

    # HTTPException (401/403/400) muss durch — sonst wird daraus unten eine 500.
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing deletion request: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to process data deletion request"
        )

@gdpr_router.delete("/request-deletion")
async def cancel_data_deletion(
    current_user: dict = Depends(get_verified_user),
):
    """Offenen Löschantrag zurückziehen (solange noch nicht ausgeführt)."""
    try:
        zurueckgezogen = await gdpr_service.cancel_user_deletion(int(current_user["id"]))
        if zurueckgezogen:
            return {"success": True, "message": "Ihr Löschantrag wurde zurückgezogen."}
        return {"success": False, "message": "Kein offener Löschantrag gefunden."}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling deletion request: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel deletion request")

@gdpr_router.get("/deletion-status")
async def get_deletion_status(
    current_user: dict = Depends(get_verified_user),
):
    """Status des (letzten) Löschantrags des Token-Inhabers."""
    try:
        status = await gdpr_service.get_user_deletion_status(int(current_user["id"]))
        return {"success": True, "deletion_request": status}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reading deletion status: {e}")
        raise HTTPException(status_code=500, detail="Failed to read deletion status")

@gdpr_router.get("/export-data")
async def download_personal_data(
    current_user: dict = Depends(get_verified_user),
):
    """
    Direkter JSON-Download aller personenbezogenen Daten des Token-Inhabers
    (GDPR Art. 15/20). Wird vom Dashboard (Einstellungen → Datenschutz) genutzt.
    """
    try:
        export_data = await gdpr_service.export_user_data(
            int(current_user["id"]), str(current_user["email"])
        )
        if export_data is None:
            raise HTTPException(status_code=404, detail="No data found for this account")

        from fastapi.responses import JSONResponse
        return JSONResponse(
            content=export_data,
            headers={"Content-Disposition": 'attachment; filename="complyo-daten-export.json"'},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating data export download: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate data export")

@gdpr_router.post("/export-data")
async def export_personal_data(
    request: DataExportRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_verified_user),
):
    """
    Export all personal data for a user (GDPR Article 20 - Data Portability)

    Betroffener = Token-Inhaber. Aggregiert users + zugehörige Tabellen
    (plus Alt-Lead-Daten derselben E-Mail) und versendet per E-Mail.
    """
    try:
        email = str(current_user["email"])
        logger.info(f"Processing data export request for user {current_user['id']}")

        export_data = await gdpr_service.export_user_data(int(current_user["id"]), email)

        if export_data is None:
            raise HTTPException(
                status_code=404,
                detail="No data found for this account"
            )

        # Send export data via email in background
        background_tasks.add_task(
            email_service.send_data_export_email,
            email,
            export_data
        )

        return {
            "success": True,
            "message": "Your data export has been generated and will be sent to your email address",
            "details": {
                "email": email,
                "export_generated_at": export_data["export_info"]["generated_at"],
                "data_categories": list(export_data.keys()),
                "gdpr_article": "Article 20 - Right to data portability"
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing data export request: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to process data export request"
        )

@gdpr_router.get("/retention-info")
async def get_retention_information(
    current_user: dict = Depends(get_verified_user),
):
    """
    Get data retention information for the authenticated data subject.

    Der frühere Query-Parameter `email` war ein Auskunfts-Orakel über beliebige
    Dritte (Existenz, Anlagedatum, Rechtsgrundlage). Jetzt aus dem Token.
    """
    try:
        email = str(current_user["email"])
        return {
            "email": email,
            "data_retention_info": {
                "created_at": (current_user.get("created_at").isoformat()
                               if current_user.get("created_at") else None),
                # Kontodaten: solange das Konto besteht (Art. 6 Abs. 1 lit. b),
                # danach einheitlich 24 Monate Aufbewahrung.
                "retention_policy": (f"Kontodaten werden für die Vertragsdauer gespeichert; "
                                     f"nach Kontolöschung bzw. für Lead-Daten gilt eine "
                                     f"Aufbewahrungsfrist von {RETENTION_MONATE} Monaten."),
                "retention_period_months": RETENTION_MONATE,
                "legal_basis": "Art. 6 Abs. 1 lit. a/b DSGVO",
                "can_request_deletion": True,
                "can_request_export": True
            },
            "gdpr_rights": {
                "right_to_access": "Article 15 - Right of access by the data subject",
                "right_to_rectification": "Article 16 - Right to rectification",
                "right_to_erasure": "Article 17 - Right to erasure ('right to be forgotten')",
                "right_to_data_portability": "Article 20 - Right to data portability"
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting retention information: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve retention information"
        )

@gdpr_router.post("/admin/confirm-deletion")
async def admin_confirm_deletion(
    request: DeletionConfirmRequest,
    admin: dict = Depends(require_admin),
):
    """
    Admin: Bestätigungslauf für einen Kontolöschantrag (Stufe 2, Art. 17).
    Setzt den Antrag auf 'confirmed' und führt die Löschung aus.
    """
    try:
        result = await gdpr_service.confirm_user_deletion(
            request.user_id, int(admin["id"])
        )
        if not result["success"]:
            raise HTTPException(status_code=404, detail=result["message"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error confirming deletion: {e}")
        raise HTTPException(status_code=500, detail="Failed to confirm deletion request")

@gdpr_router.post("/admin/update-retention")
async def admin_update_retention_period(
    request: RetentionUpdateRequest,
    admin: dict = Depends(require_admin),
):
    """
    Admin endpoint to update data retention period for a specific lead

    Früher hing dieser Endpunkt an einem nie gesetzten ADMIN_API_KEY und
    antwortete dauerhaft 503 — jetzt reguläre require_admin-Dependency
    (JWT + users.role), wie im restlichen Adminbereich.
    """
    try:
        if request.retention_days < 1 or request.retention_days > 3650:  # Max 10 years
            raise HTTPException(
                status_code=400,
                detail="Retention period must be between 1 and 3650 days"
            )

        success = await gdpr_service.update_retention_period(
            request.lead_id,
            request.retention_days
        )

        if success:
            return {
                "success": True,
                "message": f"Retention period updated to {request.retention_days} days",
                "lead_id": request.lead_id,
                "new_retention_days": request.retention_days
            }
        else:
            raise HTTPException(
                status_code=404,
                detail="Lead not found"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating retention period: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to update retention period"
        )

@gdpr_router.get("/admin/cleanup-status")
async def admin_get_cleanup_status(
    admin: dict = Depends(require_admin),
):
    """
    Admin endpoint to get GDPR cleanup and deletion statistics
    """
    try:
        stats = gdpr_service.get_deletion_statistics()

        return {
            "cleanup_status": {
                "is_running": gdpr_service.is_running,
                "retention_period_days": stats["retention_period_days"],
                "cleanup_interval_hours": stats["cleanup_interval_hours"]
            },
            "deletion_statistics": {
                "total_deletions": stats["total_deletions"],
                "automatic_deletions": stats["automatic_deletions"],
                "user_requested_deletions": stats["user_requested_deletions"],
                "recent_deletions_count": len(stats["recent_deletions"])
            },
            "recent_deletions": stats["recent_deletions"][:10]  # Last 10 deletions
        }

    except Exception as e:
        logger.error(f"Error getting cleanup status: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve cleanup status"
        )

@gdpr_router.post("/admin/run-cleanup")
async def admin_run_manual_cleanup(
    background_tasks: BackgroundTasks,
    admin: dict = Depends(require_admin),
):
    """
    Admin endpoint to manually trigger GDPR cleanup process
    """
    try:
        logger.info("Manual GDPR cleanup triggered by admin")

        # Run cleanup in background
        background_tasks.add_task(gdpr_service.perform_retention_cleanup)

        return {
            "success": True,
            "message": "Manual GDPR cleanup process started",
            "triggered_at": "now",
            "note": "Cleanup is running in the background. Check cleanup status for results."
        }

    except Exception as e:
        logger.error(f"Error triggering manual cleanup: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to trigger manual cleanup"
        )

@gdpr_router.get("/privacy-policy")
async def get_privacy_policy_info():
    """
    Get privacy policy and GDPR compliance information
    """
    return {
        "privacy_policy": {
            "data_controller": "Complyo GmbH",
            "contact_email": "datenschutz@complyo.de",
            "data_protection_officer": "dpo@complyo.de",
            "legal_basis": "Article 6(1)(a) GDPR - Consent",
            "data_retention_period": f"{RETENTION_MONATE} months from collection",
            "purposes_of_processing": [
                "Website compliance analysis",
                "Lead management and communication",
                "Service improvement and analytics"
            ]
        },
        "your_rights": {
            "right_to_access": "Request access to your personal data",
            "right_to_rectification": "Request correction of inaccurate data",
            "right_to_erasure": "Request deletion of your personal data",
            "right_to_data_portability": "Request export of your personal data",
            "right_to_object": "Object to processing of your personal data",
            "right_to_withdraw_consent": "Withdraw consent at any time"
        },
        "contact_information": {
            "exercise_rights": "Send requests to datenschutz@complyo.de",
            "supervisory_authority": "Contact your local data protection authority",
            "response_time": "We will respond within 30 days"
        }
    }
