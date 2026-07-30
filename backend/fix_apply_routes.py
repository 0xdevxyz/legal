"""
Direct-Deploy von Fixes (FTP/SFTP) — Kunden-Klick, Backup-Pflicht, Rollback.

Neufassung 30.07.2026. Der alte Stand war end-to-end nie funktionsfähig:
_get_fix_code las generated_fixes.fix_data (Spalte existiert nicht), das Backup
war ein Stub (meldete backup_created=True ohne zu sichern), der Rollback las
backup_type/backed_up_files (Spalten existieren nicht), und der Upload las eine
lokale Datei, die es im API-Container nie gab.

Grundsätze (Betreiber-Entscheidung 29.07.2026):
- Direktschreiben nur mit Backup — serverseitig erzwungen, nicht abschaltbar
  (secure_deployment.py, fail-closed).
- Nur auf expliziten Kunden-Klick (user_confirmed) — nie autonom durch KI/MCP.
- Nur Fixes, deren Quality Gate grün ist oder die ein Admin freigegeben hat.
- Kunden-Credentials (FTP/SFTP) werden nie persistiert — nur im Request.
- Backups liegen in der DB (fix_backups.file_contents), Restore läuft daraus.
"""

from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import json
import logging
import asyncpg
from dependencies import get_current_user, rate_limit

from compliance_engine.secure_deployment import (
    DeployFile,
    DeploymentError,
    SecureDeploymentEngine,
    ERLAUBTE_METHODEN,
)
from audit_service import FixAuditService

logger = logging.getLogger(__name__)

apply_router = APIRouter(prefix="/api/v2/fixes", tags=["fix-apply"])

# Global references (set in main_production.py)
db_pool: Optional[asyncpg.Pool] = None
auth_service = None
audit_service: Optional[FixAuditService] = None

_engine = SecureDeploymentEngine()

# Auslieferbar sind nur geprüfte Fixes. 'approved' entsteht, wenn ein Admin
# einen pending_review-Fix freigibt und die Spiegelung (admin_routes) den
# Status setzt; historisch wird dabei 'validated' geschrieben — beide gelten.
_DEPLOYBARE_STATUS = ("validated", "approved")


# ============================================================================
# Request/Response Models
# ============================================================================

class ApplyFixRequest(BaseModel):
    fix_id: str = Field(..., description="Job-ID des generierten Fixes (fix_jobs.job_id)")
    deployment_method: str = Field(..., description="ftp | sftp")
    credentials: Dict[str, str] = Field(..., description="Deployment-Credentials (werden nie gespeichert)")
    target_path: str = Field(..., description="Remote-Pfad der Zieldatei, z. B. snippets/complyo-fix.html")
    user_confirmed: bool = Field(False, description="Explizite Kundenbestätigung — Pflicht")


class ApplyFixResponse(BaseModel):
    success: bool
    deployment_id: str
    audit_id: str
    files_deployed: list
    backup_id: str
    message: str


class RollbackRequest(BaseModel):
    backup_id: str = Field(..., description="ID des Backups")
    credentials: Dict[str, str] = Field(..., description="Deployment-Credentials (werden nie gespeichert)")
    user_confirmed: bool = Field(False, description="Explizite Kundenbestätigung — Pflicht")


class ApplyStatusResponse(BaseModel):
    apply_id: str
    status: str
    progress: int
    current_step: str
    error: Optional[str] = None


# ============================================================================
# Endpoints
# ============================================================================

@apply_router.post("/apply", response_model=ApplyFixResponse,
                   dependencies=[Depends(rate_limit("fix_apply", 5, 60))])
async def apply_fix(
    request: Request,
    apply_request: ApplyFixRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
):
    """Deployt einen geprüften Fix per FTP/SFTP — mit erzwungenem Backup."""
    user_id = int(current_user["id"])

    # 1. Expliziter Kunden-Klick — die KI löst nie selbst aus.
    if not apply_request.user_confirmed:
        raise HTTPException(
            status_code=400,
            detail="Bestätigung erforderlich: Setzen Sie user_confirmed, um den Fix anzuwenden.",
        )

    # 2. Nur bezahlte Pläne. (Die frühere Allowlist 'managed'/'premium' entsprach
    #    keinem real vergebenen plan_type und sperrte alle.)
    plan = (current_user.get("plan_type") or "free").lower()
    if plan in ("", "free"):
        raise HTTPException(
            status_code=403,
            detail="Direct-Deploy ist in bezahlten Plänen enthalten. "
                   "Im Free-Plan nutzen Sie Copy-Paste oder den GitHub-Pull-Request.",
        )

    # 3. Nur unterstützte Methoden — andere haben sichere Alternativen.
    methode = apply_request.deployment_method.lower()
    if methode not in ERLAUBTE_METHODEN:
        raise HTTPException(
            status_code=400,
            detail=f"Methode '{methode}' wird nicht direkt unterstützt. "
                   "Nutzen Sie den GitHub-Pull-Request oder die Fix-Manifest-Kanäle.",
        )

    # 4. Fix laden + Review-Gate durchsetzen.
    fix = await _get_deploybaren_fix(apply_request.fix_id, user_id)
    if fix is None:
        raise HTTPException(
            status_code=404,
            detail="Fix nicht gefunden, nicht freigegeben oder ohne deploybaren Inhalt. "
                   "Nur geprüfte Fixes (Quality Gate grün oder Admin-Freigabe) können deployt werden.",
        )

    # 5. Deploy mit erzwungenem Backup (fail-closed im Engine).
    try:
        ergebnis = await _engine.deploy(
            method=methode,
            credentials=apply_request.credentials,
            files=[DeployFile(remote_path=apply_request.target_path, content=fix["code"])],
        )
    except DeploymentError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Deploy fehlgeschlagen (fix={apply_request.fix_id}): {e}")
        raise HTTPException(status_code=502, detail="Deployment fehlgeschlagen — es wurde nichts verändert oder der Bestand ist gesichert.")

    # 6. Audit + Backup-Persistenz (Backup-Inhalte in die DB).
    audit_id = await audit_service.log_fix_application(
        user_id=user_id,
        fix_id=apply_request.fix_id,
        fix_category=fix["category"],
        fix_type=fix["type"],
        deployment_method=methode,
        deployment_result={
            "deployment_id": ergebnis.deployment_id,
            "files_deployed": ergebnis.files_deployed,
            "deployed_at": ergebnis.deployed_at,
        },
        success=True,
        backup_id=ergebnis.backup_id,
        backup_location="db://fix_backups.file_contents",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        user_confirmed=True,
        metadata={"target_path": apply_request.target_path},
        backup_file_contents=ergebnis.backup_contents,
    )

    # 7. Best-Effort Post-Deploy-Verifikation (beeinflusst die Antwort nie).
    if fix.get("page_url"):
        background_tasks.add_task(
            _verify_post_deploy,
            apply_request.fix_id, user_id, fix["page_url"],
            fix["category"], fix["code"],
        )

    return ApplyFixResponse(
        success=True,
        deployment_id=ergebnis.deployment_id,
        audit_id=audit_id,
        files_deployed=ergebnis.files_deployed,
        backup_id=ergebnis.backup_id,
        message=f"Fix deployt. Backup {ergebnis.backup_id[:8]}… kann jederzeit "
                f"über /api/v2/fixes/rollback wiederhergestellt werden.",
    )


@apply_router.post("/rollback", dependencies=[Depends(rate_limit("fix_rollback", 5, 60))])
async def rollback_fix(
    request: Request,
    rollback_request: RollbackRequest,
    current_user: dict = Depends(get_current_user),
):
    """Stellt den gesicherten Stand eines Deployments wieder her."""
    user_id = int(current_user["id"])

    if not rollback_request.user_confirmed:
        raise HTTPException(
            status_code=400,
            detail="Bestätigung erforderlich: Setzen Sie user_confirmed, um den Rollback auszuführen.",
        )

    backup = await _get_backup(rollback_request.backup_id, user_id)
    if backup is None:
        raise HTTPException(
            status_code=404,
            detail="Backup nicht gefunden, bereits wiederhergestellt oder abgelaufen.",
        )
    if not backup["file_contents"]:
        raise HTTPException(
            status_code=409,
            detail="Dieses Backup enthält keine Dateiinhalte (Altbestand vor Revision 0011) "
                   "und kann nicht automatisch wiederhergestellt werden.",
        )

    try:
        pfade = await _engine.restore(
            method=backup["deployment_method"],
            credentials=rollback_request.credentials,
            backup_contents=backup["file_contents"],
        )
    except DeploymentError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Rollback fehlgeschlagen (backup={rollback_request.backup_id}): {e}")
        raise HTTPException(status_code=502, detail="Rollback fehlgeschlagen — Backup bleibt erhalten, bitte erneut versuchen.")

    async with db_pool.acquire() as conn:
        await conn.execute(
            "UPDATE fix_backups SET is_restored = TRUE, restored_at = NOW() WHERE backup_id = $1",
            rollback_request.backup_id,
        )

    await audit_service.log_rollback(
        user_id=user_id,
        fix_id=backup["fix_id"] or "",
        backup_id=rollback_request.backup_id,
        deployment_method=backup["deployment_method"],
        success=True,
        rollback_result={"files_restored": pfade},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    return {
        "success": True,
        "backup_id": rollback_request.backup_id,
        "files_restored": pfade,
        "message": "Der gesicherte Stand wurde wiederhergestellt.",
    }


@apply_router.get("/apply/status/{apply_id}")
async def get_apply_status(
    apply_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Status eines Apply-Vorgangs (aus dem Audit-Log)."""
    audit_entry = await _get_audit_entry(apply_id, int(current_user["id"]))
    if not audit_entry:
        raise HTTPException(status_code=404, detail="Apply-Vorgang nicht gefunden")

    return ApplyStatusResponse(
        apply_id=apply_id,
        status="deployed" if audit_entry["success"] else "failed",
        progress=100,
        current_step="completed",
        error=audit_entry.get("error_message"),
    )


# ============================================================================
# Helper Functions
# ============================================================================

async def _verify_post_deploy(
    fix_id: str, user_id: int, page_url: str, category: str, code: str
) -> None:
    """Best-Effort: Live-Seite re-fetchen, verifizieren, Ergebnis in fix_jobs.result ablegen.

    Laeuft im Hintergrund; Fehler werden nur geloggt und beeinflussen den Deploy nie.
    """
    try:
        from post_deploy_verifier import verify_live_url

        verification = await verify_live_url(page_url, category, code)
        async with db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT result FROM fix_jobs WHERE job_id::text = $1 AND user_id = $2",
                fix_id, user_id,
            )
            if row and row["result"]:
                res = row["result"]
                if isinstance(res, str):
                    res = json.loads(res)
                res["post_deploy_verification"] = verification
                await conn.execute(
                    "UPDATE fix_jobs SET result = $3 WHERE job_id::text = $1 AND user_id = $2",
                    fix_id, user_id, json.dumps(res),
                )
        logger.info(
            f"Post-Deploy-Verifikation fix={fix_id}: "
            f"verified={verification.get('verified')} "
            f"({str(verification.get('reason', ''))[:140]})"
        )
    except Exception as e:
        logger.warning(f"Post-Deploy-Verifikation fehlgeschlagen (fix={fix_id}): {e}")


async def _get_deploybaren_fix(fix_id: str, user_id: int) -> Optional[Dict]:
    """Fix aus fix_jobs laden — nur wenn geprüft und mit Inhalt.

    Der Fix-Inhalt lebt in fix_jobs.result (der frühere Pfad las die nie
    existierende Spalte generated_fixes.fix_data). Fixes ohne Gate-Status
    (Altbestand) dürfen NICHT direct-deployt werden — für die Anzeige gelten
    sie als ausgeliefert, aber Serverschreiben verlangt eine echte Prüfung.
    """
    try:
        async with db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT result, issue_data
                FROM fix_jobs
                WHERE job_id::text = $1 AND user_id = $2 AND status = 'completed'
                """,
                fix_id, user_id,
            )
        if not row or not row["result"]:
            return None

        result = row["result"]
        if isinstance(result, str):
            result = json.loads(result)
        data = result.get("data", result) or {}

        if data.get("quality_gate_status") not in _DEPLOYBARE_STATUS:
            return None

        code = data.get("code") or data.get("content") or data.get("html")
        if not code or not isinstance(code, str):
            return None

        issue = row["issue_data"]
        if isinstance(issue, str):
            issue = json.loads(issue or "{}")

        return {
            "code": code,
            "category": str((issue or {}).get("category") or "unknown"),
            "type": str(data.get("fix_type") or "code"),
            "page_url": str(
                (issue or {}).get("page_url")
                or (issue or {}).get("url")
                or (issue or {}).get("site_url")
                or ""
            ),
        }
    except Exception as e:
        logger.error(f"Fix-Laden fehlgeschlagen ({fix_id}): {e}")
        return None


async def _get_backup(backup_id: str, user_id: int) -> Optional[Dict]:
    """Backup inkl. Dateiinhalten — nur eigene, nicht wiederhergestellte, gültige."""
    try:
        async with db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT fb.backup_id, fb.deployment_method, fb.file_contents,
                       faa.fix_id
                FROM fix_backups fb
                LEFT JOIN fix_application_audit faa ON fb.audit_id = faa.id
                WHERE fb.backup_id = $1 AND fb.user_id = $2
                  AND fb.is_restored = FALSE
                  AND (fb.expires_at IS NULL OR fb.expires_at > NOW())
                """,
                backup_id, user_id,
            )
        if not row:
            return None
        inhalte = row["file_contents"]
        if isinstance(inhalte, str):
            inhalte = json.loads(inhalte)
        return {
            "backup_id": row["backup_id"],
            "deployment_method": row["deployment_method"],
            "file_contents": inhalte,
            "fix_id": row["fix_id"],
        }
    except Exception as e:
        logger.error(f"Backup-Laden fehlgeschlagen ({backup_id}): {e}")
        return None


async def _get_audit_entry(audit_id: str, user_id: int) -> Optional[Dict]:
    try:
        async with db_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, fix_id, action_type, deployment_method,
                       success, error_message, applied_at
                FROM fix_application_audit
                WHERE id = $1 AND user_id = $2
                """,
                audit_id, user_id,
            )
        return dict(row) if row else None
    except Exception as e:
        logger.error(f"Failed to get audit entry: {e}")
        return None


# ============================================================================
# Initialization
# ============================================================================

def init_apply_routes(
    _db_pool: asyncpg.Pool,
    _auth_service,
    _audit_service: FixAuditService,
):
    """Initialisiert die Apply-Routes mit Services"""
    global db_pool, auth_service, audit_service
    db_pool = _db_pool
    auth_service = _auth_service
    audit_service = _audit_service
    logger.info("✅ Fix Apply Routes initialized (secure deployment)")
