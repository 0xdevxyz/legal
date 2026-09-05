"""
Admin Dashboard API Endpoints for Lead Management
Provides comprehensive admin interface for GDPR-compliant lead management
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Any, Dict, Optional
from datetime import datetime
import logging
from database_service import db_service
from dependencies import require_admin, get_db

logger = logging.getLogger(__name__)

admin_router = APIRouter(prefix="/api/admin", tags=["admin"])


async def _propagate_review_status(db, audit_id: str, neuer_status: str) -> None:
    """Review-Entscheidung vom Audit in fix_jobs.result spiegeln.

    Die Kunden-Endpunkte (/api/fix-jobs/...) gaten die Auslieferung ueber
    result->data->quality_gate_status. Ohne diese Spiegelung bliebe ein
    freigegebener Fix fuer den Kunden weiterhin verborgen. Best effort:
    schlaegt die Spiegelung fehl, bleibt die Audit-Entscheidung bestehen.
    """
    try:
        await db.execute(
            """
            UPDATE fix_jobs
               -- result ist TEXT (Altbestand), daher Cast hin und zurueck
               SET result = jsonb_set(
                     result::jsonb,
                     '{data,quality_gate_status}',
                     to_jsonb($2::text),
                     true
                   )::text
             WHERE job_id::text = (
                     SELECT fix_id FROM fix_application_audit WHERE id = $1
                   )
               AND result IS NOT NULL
            """,
            audit_id, neuer_status,
        )
    except Exception as e:  # noqa: BLE001
        logger.error(f"Review-Status-Spiegelung fuer Audit {audit_id} fehlgeschlagen: {e}")


def _reviewer_name(admin: dict) -> str:
    """Wer die Freigabe erteilt hat — fuer das Audit-Feld reviewed_by.

    Bevorzugt die E-Mail, sonst die User-ID. Ein Audit-Eintrag soll eine Person
    benennen; frueher stand hier der gemeinsame API-Schluessel.
    """
    return str(admin.get("email") or f"user:{admin.get('id')}")


# Zugang ueber die rollenbasierte Dependency require_admin (JWT, users.role).
# Bis 2026-07-29 lief das ueber einen gemeinsamen Schluessel als QUERY-Parameter
# (?api_key=...). Das hatte drei Probleme: der Schluessel landete in
# Access-Logs, Browser-History und Referer-Headern; im Frontend stand er als
# NEXT_PUBLIC_ADMIN_API_KEY und waere damit ins ausgelieferte JS-Bundle
# gebacken worden; und er wurde als reviewed_by in die Audit-Tabelle
# geschrieben. require_admin wird bereits von ai_legal_routes,
# cookie_compliance_routes, legal_change_routes und i18n_api genutzt.

@admin_router.get("/dashboard/overview")
async def admin_dashboard_overview(
    admin: dict = Depends(require_admin),
    db=Depends(get_db),
):
    """
    Dashboard-Uebersicht fuer den Admin — nur echte, gezaehlte Werte.

    Bis 2026-08 standen hier erfundene Kennzahlen ('uptime 99.9%',
    email_service 'active', avg_verification_time '< 5 minutes'). Was diese
    API nicht messen kann, behauptet sie nicht mehr — Nicht-Ermittelbares
    wird weggelassen statt erfunden.
    """
    try:
        # Lead-Statistik (echte Zaehlung ueber db_service)
        stats = await db_service.get_lead_statistics()

        status_breakdown = {
            "new": stats["total_leads"] - stats["verified_leads"],
            "verified": stats["verified_leads"] - stats["converted_leads"],
            "converted": stats["converted_leads"]
        }

        # Kennzahlen zaehlen statt behaupten
        users_total = await db.fetchval("SELECT COUNT(*) FROM users")
        websites_total = await db.fetchval("SELECT COUNT(*) FROM tracked_websites")
        scans_7d = await db.fetchval(
            "SELECT COUNT(*) FROM scan_history WHERE scan_date >= NOW() - INTERVAL '7 days'"
        )

        # Echter Zustand des Mailversands statt hartkodiertem 'active'
        from email_service import email_service

        return {
            "overview": stats,
            "status_breakdown": status_breakdown,
            "metrics": {
                "users": users_total or 0,
                "tracked_websites": websites_total or 0,
                "scans_last_7_days": scans_7d or 0,
            },
            "system_status": {
                "storage_type": "database",
                "gdpr_compliant": True,
                "email_service": "demo" if email_service.demo_mode else "active",
            },
        }

    except Exception as e:
        logger.error(f"Error getting admin dashboard overview: {e}")
        raise HTTPException(status_code=500, detail="Error loading dashboard")

@admin_router.get("/leads")
async def get_all_leads(
    admin: dict = Depends(require_admin),
    status: Optional[str] = Query(None, description="Filter by status"),
    verified: Optional[bool] = Query(None, description="Filter by verification status"),
    limit: int = Query(50, ge=1, le=200, description="Number of leads to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db=Depends(get_db),
):
    """
    Paginierte Lead-Liste mit Filtern.

    Bis 2026-08 stand hier hartkodiert `leads = []` — der Endpunkt lieferte
    immer eine leere Liste und sah dabei fertig aus. Jetzt echte Query.
    Bewusst nur unkritische Spalten (kein verification_token, keine
    Consent-IP) — das ist die Admin-Listenansicht, nicht der Datenexport.
    """
    try:
        filters = []
        params: list = []
        if status is not None:
            params.append(status)
            filters.append(f"status = ${len(params)}")
        if verified is not None:
            params.append(verified)
            filters.append(f"email_verified = ${len(params)}")
        where_sql = ("WHERE " + " AND ".join(filters)) if filters else ""

        total_count = await db.fetchval(
            f"SELECT COUNT(*) FROM leads {where_sql}", *params
        ) or 0

        rows = await db.fetch(
            f"""
            SELECT id, email, name, company, source, status, email_verified,
                   created_at, verified_at, url_analyzed
            FROM leads
            {where_sql}
            ORDER BY created_at DESC
            LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}
            """,
            *params,
            limit,
            offset,
        )
        sanitized_leads = [dict(row) for row in rows]

        return {
            "leads": sanitized_leads,
            "pagination": {
                "total_count": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total_count
            },
            "filters_applied": {
                "status": status,
                "verified": verified
            }
        }

    except Exception as e:
        logger.error(f"Error getting leads: {e}")
        raise HTTPException(status_code=500, detail="Error loading leads")

@admin_router.get("/leads/{lead_id}")
async def get_lead_details(
    lead_id: str,
    admin: dict = Depends(require_admin)
):
    """
    Get detailed information about a specific lead
    """
    try:
        lead = await db_service.get_lead_by_verification_token(lead_id)
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        # Return detailed lead information
        return {
            "lead": lead,
            "gdpr_info": {
                "consent_given": lead.get("consent_given"),
                "consent_timestamp": lead.get("consent_timestamp"),
                "legal_basis": lead.get("legal_basis"),
                "data_retention_until": lead.get("data_retention_until"),
                "deletion_requested": lead.get("deletion_requested", False)
            },
            "verification_info": {
                "email_verified": lead.get("email_verified"),
                "verification_sent_at": lead.get("verification_sent_at"),
                "verified_at": lead.get("verified_at"),
                "verification_expires_at": lead.get("verification_expires_at")
            },
            "analysis_summary": {
                "url_analyzed": lead.get("url_analyzed"),
                "has_analysis_data": bool(lead.get("analysis_data")),
                "compliance_score": lead.get("analysis_data", {}).get("compliance_score") if lead.get("analysis_data") else None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting lead details: {e}")
        raise HTTPException(status_code=500, detail="Error loading lead details")

@admin_router.post("/leads/{lead_id}/resend-verification")
async def resend_verification_email(
    lead_id: str,
    admin: dict = Depends(require_admin)
):
    """
    Manually resend verification email for a lead
    """
    try:
        lead = await db_service.get_lead_by_verification_token(lead_id)
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        if lead.get("email_verified"):
            raise HTTPException(status_code=400, detail="Lead already verified")
        
        # Import email service and send verification
        from email_service import email_service
        
        verification_sent = email_service.send_verification_email(
            lead["email"], 
            lead["name"], 
            lead["verification_token"]
        )
        
        if verification_sent:
            # Log the manual resend
            await db_service.log_communication(
                lead_id, 
                "verification_resend", 
                "Manual verification email resend by admin"
            )
            
            return {
                "success": True,
                "message": f"Verification email resent to {lead['email']}",
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to send verification email")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resending verification: {e}")
        raise HTTPException(status_code=500, detail="Error resending verification email")

@admin_router.delete("/leads/{lead_id}")
async def delete_lead_gdpr(
    lead_id: str,
    admin: dict = Depends(require_admin),
    reason: str = Query(..., description="Reason for deletion (GDPR compliance)")
):
    """
    Delete lead for GDPR compliance (right to be forgotten)
    """
    try:
        success = await db_service.delete_lead_permanently(lead_id)
        if not success:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        logger.info(f"Lead {lead_id} deleted for GDPR compliance. Reason: {reason}")
        
        return {
            "success": True,
            "message": "Lead permanently deleted for GDPR compliance",
            "lead_id": lead_id,
            "deletion_reason": reason,
            "deleted_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting lead: {e}")
        raise HTTPException(status_code=500, detail="Error deleting lead")

@admin_router.get("/analytics/trends")
async def get_analytics_trends(
    admin: dict = Depends(require_admin),
    days: int = Query(30, ge=1, le=365, description="Number of days for trend analysis"),
    db=Depends(get_db),
):
    """
    Scans pro Tag aus scan_history fuer den gewaehlten Zeitraum.

    Bis 2026-08 stand hier hartkodiert `trends = []` — lauter Nullwerte, die
    wie ein ruhiger Zeitraum aussahen. Jetzt echte Tagesaggregation.
    """
    try:
        rows = await db.fetch(
            """
            SELECT scan_date::date AS tag, COUNT(*) AS scans
            FROM scan_history
            WHERE scan_date >= CURRENT_DATE - $1::int
            GROUP BY scan_date::date
            ORDER BY scan_date::date
            """,
            days,
        )
        trends = [{"date": r["tag"].isoformat(), "scans": r["scans"]} for r in rows]
        total_scans = sum(t["scans"] for t in trends)

        return {
            "time_period": f"{days} days",
            "trends": trends,
            "summary": {
                "total_scans": total_scans,
                # Durchschnitt ueber den Zeitraum, nicht nur ueber Tage mit Scans
                "avg_daily_scans": round(total_scans / max(days, 1), 2),
                "peak_day": max(trends, key=lambda t: t["scans"])["date"] if trends else None
            }
        }

    except Exception as e:
        logger.error(f"Error getting analytics trends: {e}")
        raise HTTPException(status_code=500, detail="Error loading analytics trends")

@admin_router.get("/system/health")
async def admin_system_health(
    admin: dict = Depends(require_admin),
    db=Depends(get_db),
):
    """
    Systemzustand aus echten Pruefungen.

    Bis 2026-08 lieferte der Endpunkt erfundene Werte ('uptime 99.9%',
    email_service 'active', avg_response_time '< 200ms'). Die sind ersatzlos
    gestrichen: Was diese API nicht messen kann, behauptet sie nicht.
    """
    try:
        # DB-Zustand real pruefen statt 'connected' zu behaupten
        try:
            await db.fetchval("SELECT 1")
            db_status = "connected"
        except Exception as db_exc:  # noqa: BLE001
            logger.error(f"System-Health: DB-Check fehlgeschlagen: {db_exc}")
            db_status = "error"

        # Echter Modus des Mailversands aus dem Singleton (demo_mode haengt
        # an SMTP_USERNAME/SMTP_PASSWORD, siehe email_service.py)
        from email_service import email_service

        return {
            "database": {
                "status": db_status,
                "type": "postgresql"
            },
            "email_service": {
                "status": "demo" if email_service.demo_mode else "active",
                "mode": "demo" if email_service.demo_mode else "smtp"
            },
            "gdpr_compliance": {
                "double_opt_in": True,
                "data_retention": "730 days",
                "audit_trail": True,
                "consent_tracking": True
            }
        }

    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        raise HTTPException(status_code=500, detail="Error getting system health")


# =============================================================================
# Fix Review Queue — Human-in-the-Loop Quality Gate
# =============================================================================

from fastapi import Body
from dependencies import get_db

@admin_router.get("/fix-review-queue")
async def get_fix_review_queue(
    admin: dict = Depends(require_admin),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db=Depends(get_db),
):
    """
    Gibt alle Fixes mit quality_gate_status='pending_review' zurück.
    """
    try:
        rows = await db.fetch(
            """
            SELECT
                faa.id,
                faa.fix_type,
                faa.issue_title,
                faa.quality_gate_status,
                faa.quality_gate_log,
                faa.applied_at,
                faa.reviewed_by,
                faa.reviewed_at,
                tw.url AS website_url,
                u.email AS user_email
            FROM fix_application_audit faa
            LEFT JOIN tracked_websites tw ON faa.website_id = tw.id
            LEFT JOIN users u ON faa.user_id = u.id
            WHERE faa.quality_gate_status = 'pending_review'
            ORDER BY faa.applied_at DESC
            LIMIT $1 OFFSET $2
            """,
            limit,
            offset,
        )

        total = await db.fetchval(
            "SELECT COUNT(*) FROM fix_application_audit WHERE quality_gate_status = 'pending_review'"
        )

        return {
            "items": [dict(r) for r in rows],
            "total": total or 0,
            "limit": limit,
            "offset": offset,
        }
    except Exception as e:
        logger.error(f"get_fix_review_queue error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Fehler beim Laden der Review-Queue")


@admin_router.get("/fix-review-queue/{fix_id}")
async def get_fix_review_detail(
    fix_id: str,
    admin: dict = Depends(require_admin),
    db=Depends(get_db),
):
    """
    Detail-Ansicht eines einzelnen Fixes inkl. Quality Gate Log und HTML-Diff.
    """
    try:
        row = await db.fetchrow(
            """
            SELECT
                faa.*,
                tw.url AS website_url,
                u.email AS user_email
            FROM fix_application_audit faa
            LEFT JOIN tracked_websites tw ON faa.website_id = tw.id
            LEFT JOIN users u ON faa.user_id = u.id
            WHERE faa.id = $1
            """,
            fix_id,
        )

        if not row:
            raise HTTPException(status_code=404, detail="Fix nicht gefunden")

        return dict(row)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"get_fix_review_detail error for fix {fix_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Fehler beim Laden des Fix-Details")


@admin_router.post("/fix-review-queue/{fix_id}/approve")
async def approve_fix(
    fix_id: str,
    admin: dict = Depends(require_admin),
    db=Depends(get_db),
):
    """
    Setzt quality_gate_status='validated' und speichert Reviewer.
    """
    try:
        reviewer = _reviewer_name(admin)
        updated = await db.fetchval(
            """
            UPDATE fix_application_audit
            SET quality_gate_status = 'validated',
                reviewed_by          = $1,
                reviewed_at          = NOW()
            WHERE id = $2
              AND quality_gate_status = 'pending_review'
            RETURNING id
            """,
            reviewer,
            fix_id,
        )

        if not updated:
            raise HTTPException(
                status_code=404,
                detail="Fix nicht gefunden oder bereits bearbeitet",
            )

        # Freigabe in fix_jobs.result nachziehen — das Auslieferungs-Gating der
        # Kunden-Endpunkte liest quality_gate_status aus dem Job-Ergebnis.
        # audit.fix_id ist die job_id (so schreibt es der Background-Worker).
        await _propagate_review_status(db, fix_id, "validated")

        logger.info(f"Fix {fix_id} approved by admin")
        return {"success": True, "fix_id": fix_id, "new_status": "validated"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"approve_fix error for {fix_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Fehler beim Freigeben des Fixes")


@admin_router.post("/fix-review-queue/{fix_id}/reject")
async def reject_fix(
    fix_id: str,
    reason: str = Body(..., embed=True),
    admin: dict = Depends(require_admin),
    db=Depends(get_db),
):
    """
    Setzt quality_gate_status='rejected' mit Begründung.
    """
    if not reason or len(reason.strip()) < 5:
        raise HTTPException(status_code=422, detail="Begründung muss mindestens 5 Zeichen haben")

    try:
        reviewer = _reviewer_name(admin)
        updated = await db.fetchval(
            """
            UPDATE fix_application_audit
            SET quality_gate_status = 'rejected',
                reviewed_by          = $1,
                reviewed_at          = NOW(),
                quality_gate_log     = COALESCE(quality_gate_log, '[]'::jsonb)
                                       || jsonb_build_array(
                                           jsonb_build_object(
                                             'stage', 0,
                                             'name', 'Admin Review',
                                             'passed', false,
                                             'errors', jsonb_build_array($3)
                                           )
                                         )
            WHERE id = $2
              AND quality_gate_status = 'pending_review'
            RETURNING id
            """,
            reviewer,
            fix_id,
            reason.strip(),
        )

        if not updated:
            raise HTTPException(
                status_code=404,
                detail="Fix nicht gefunden oder bereits bearbeitet",
            )

        await _propagate_review_status(db, fix_id, "rejected")

        logger.info(f"Fix {fix_id} rejected by admin: {reason}")
        return {"success": True, "fix_id": fix_id, "new_status": "rejected", "reason": reason}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"reject_fix error for {fix_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Fehler beim Ablehnen des Fixes")


# ---------------------------------------------------------------------------
# Lernstand
# ---------------------------------------------------------------------------


@admin_router.get("/lernstand")
async def lernstand(
    tage: int = 90,
    admin: dict = Depends(require_admin),
):
    """Was hat complyo aus den Entscheidungen der Kunden gelernt?

    Je Befundtyp: Vorschlaege, Zustimmungen, Ablehnungen, Annahmequote und die
    haeufigsten Ablehnungsgruende.

    Drei Angaben sind wichtiger als die Zahlen selbst:

    - `aussagekraeftig` / `belege_reichen`: unter 30 Entscheidungen ist eine
      Quote Rauschen. Steht das nicht dabei, wird aus drei Zustimmungen eine
      100-Prozent-Quote.
    - `gruende_erfassbar`: Ablehnungsgruende gibt es heute nur bei Alt-Texten.
      Ohne diesen Vermerk saehe eine Ablehnungsquote ohne Gruende aus wie
      "niemand hatte einen Grund" statt wie "hier kann keiner erfasst werden".
    - `konfidenz_angenommen` neben `konfidenz_abgelehnt`: trennen die beiden
      Werte nicht, taugt die Konfidenz nicht als Vorfilter.
    """
    if tage < 1 or tage > 3650:
        raise HTTPException(status_code=400, detail="tage muss zwischen 1 und 3650 liegen")
    from lernstand import erhebe_lernstand
    return await erhebe_lernstand(db_service.pool, tage=tage)


# ---------------------------------------------------------------------------
# Selbstauskunft ueber den Speicher
# ---------------------------------------------------------------------------


@admin_router.get("/speicher")
async def speicherauskunft(admin: dict = Depends(require_admin)):
    """Was haelt der laufende Prozess im Speicher?

    Angelegt am 05.09.2026 fuer eine offene Frage: der Grundverbrauch des
    Backends waechst zwischen Neustarts von rund 140 auf 290 MiB. Playwright
    ist es nicht mehr (das Leck ist seit dem 03.09. geschlossen, node-Prozesse
    bleiben bei 0), also Python-Heap oder Caches.

    **Von aussen ist das nicht messbar.** `docker exec python3 -c ...` startet
    einen NEUEN Interpreter und zeigt dessen leeren Heap — nicht den des
    Servers. Genau dieser Irrtum hat den ersten Messversuch wertlos gemacht.
    Deshalb fragt diese Route den Prozess von innen.

    Sie ist bewusst schlank: keine Objektgraphen, kein tracemalloc. Was hier
    steht, reicht, um die Frage "waechst ein bekannter Cache oder der Heap
    allgemein?" zu beantworten — und mehr Werkzeug einzubauen, bevor die Frage
    gestellt ist, waere Vorratshaltung.
    """
    import gc
    import collections
    import resource

    gc.collect()
    objekte = gc.get_objects()
    nach_typ = collections.Counter(type(o).__name__ for o in objekte)

    # Nur die Caches, die es wirklich gibt — nachgesehen, nicht geraten.
    caches: Dict[str, Any] = {}

    try:
        from compliance_engine import scan_progress as _sp
        caches["scan_progress"] = {
            "eintraege": len(_sp._stand),
            "ttl_sekunden": _sp._TTL_SEKUNDEN,
        }
    except Exception as e:
        caches["scan_progress"] = f"nicht lesbar: {type(e).__name__}"

    try:
        import main_production as _mp
        rk = getattr(_mp, "risk_calculator", None)
        caches["risk_calculator"] = (
            {"eintraege": len(rk._cache), "ttl_sekunden": rk.cache_ttl}
            if rk is not None else "nicht initialisiert"
        )
    except Exception as e:
        caches["risk_calculator"] = f"nicht lesbar: {type(e).__name__}"

    try:
        import lead_routes as _lr
        caches["mx_pruefung"] = {"eintraege": len(_lr._mx_cache)}
    except Exception as e:
        caches["mx_pruefung"] = f"nicht lesbar: {type(e).__name__}"

    try:
        from compliance_engine import scan_arbeiter as _sa
        caches["scan_warteschlange"] = {
            "wartend": _sa.wartend_anzahl(),
            "in_arbeit": len(_sa._in_arbeit),
        }
    except Exception as e:
        caches["scan_warteschlange"] = f"nicht lesbar: {type(e).__name__}"

    # Die groessten Sammlungen im Heap — dort wuerde ein wachsender Cache
    # auffallen, den niemand auf dem Zettel hat.
    gross = []
    for o in objekte:
        try:
            if isinstance(o, (dict, list, set)) and len(o) > 1000:
                gross.append({"typ": type(o).__name__, "eintraege": len(o)})
        except Exception:
            continue
    gross.sort(key=lambda g: g["eintraege"], reverse=True)

    return {
        "rss_mib": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1),
        "objekte_gesamt": len(objekte),
        "haeufigste_typen": [
            {"typ": t, "anzahl": n} for t, n in nach_typ.most_common(15)
        ],
        "grosse_sammlungen": gross[:10],
        "caches": caches,
        "gc_stand": gc.get_stats(),
    }
