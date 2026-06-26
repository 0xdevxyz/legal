"""
Legal Text Routes — /api/legal-texts/*
Ersetzt alle /api/erecht24/* und /api/v2/erecht24/* Endpunkte.

Routen:
  GET  /api/legal-texts/{type}              — aktives Dokument holen
  POST /api/legal-texts/{type}/generate     — neue Generierung erzwingen
  GET  /api/legal-texts/{type}/history      — Versionshistorie
  GET  /api/legal-texts/{type}/preview      — Preview ohne Speichern

type ∈ imprint | privacy | tos | cookie-policy
"""

import logging
from typing import Optional, List, Dict
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from legal_text_generator import LegalTextGenerator, DocumentType, get_legal_text_generator
from legal_disclaimer import DISCLAIMER_LONG, DISCLAIMER_SHORT
from auth_routes import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/legal-texts", tags=["legal-texts"])

VALID_TYPES = {t.value for t in DocumentType}


async def get_current_user_id(current_user: dict = Depends(get_current_user)) -> int:
    """Liefert die authentifizierte User-ID aus dem JWT.

    Verhindert IDOR: Rechtstexte enthalten personenbezogene Daten (Adresse,
    E-Mail, USt-IdNr., Datenschutzbeauftragter) — der Zugriff darf nicht über
    einen frei wählbaren Query-Parameter steuerbar sein.
    """
    uid = current_user.get("user_id") or current_user.get("id")
    if uid is None:
        raise HTTPException(status_code=401, detail="Nicht authentifiziert")
    return int(uid)


class LegalTextUserData(BaseModel):
    # Pflicht-/Stammdaten (Impressum, alle Dokumente)
    company_name: str = Field(..., min_length=1, max_length=200)
    legal_form: Optional[str] = None
    address: Optional[str] = None
    zip_city: Optional[str] = None
    country: Optional[str] = "Deutschland"
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    represented_by: Optional[str] = None
    representative_role: Optional[str] = None
    court: Optional[str] = None
    registration_number: Optional[str] = None
    vat_id: Optional[str] = None
    dpo_name: Optional[str] = None
    dpo_email: Optional[str] = None

    # Impressum — berufsrechtliche & inhaltliche Verantwortung
    profession: Optional[str] = None
    regulatory_authority: Optional[str] = None
    content_responsible: Optional[str] = None
    content_responsible_address: Optional[str] = None

    # Datenschutz — Infrastruktur & Website-Funktionen
    hosting_provider: Optional[str] = None
    server_location: Optional[str] = None
    uses_analytics: Optional[str] = None
    uses_marketing: Optional[str] = None
    third_party_cookies: Optional[str] = None
    has_registration: Optional[str] = None
    has_contact_form: Optional[str] = None
    has_newsletter: Optional[str] = None
    has_shop: Optional[str] = None
    payment_providers: Optional[str] = None

    # Cookie-Richtlinie
    consent_tool: Optional[str] = None
    third_party_services: Optional[str] = None
    functional_cookie_duration: Optional[str] = None
    analytics_cookie_duration: Optional[str] = None
    marketing_cookie_duration: Optional[str] = None
    privacy_url: Optional[str] = None

    # AGB — Leistung, Preise, Laufzeit
    target_audience: Optional[str] = None
    service_description: Optional[str] = None
    pricing_model: Optional[str] = None
    payment_methods: Optional[str] = None
    payment_due: Optional[str] = None
    invoicing: Optional[str] = None
    min_contract_duration: Optional[str] = None
    cancellation_period: Optional[str] = None
    auto_renewal: Optional[str] = None
    jurisdiction: Optional[str] = None

    # Widerruf
    has_withdrawal_right: Optional[str] = None
    withdrawal_exceptions: Optional[str] = None


class GenerateRequest(BaseModel):
    user_data: LegalTextUserData
    language: str = "de"
    services_used: Optional[List[str]] = None
    business_type: Optional[str] = "saas"
    cookie_inventory: Optional[List[Dict[str, str]]] = None
    force_regenerate: bool = False


class LegalTextResponse(BaseModel):
    document_id: Optional[int]
    document_type: str
    language: str
    html_content: str
    plain_text: str
    template_version: str
    generated_at: str
    regeneration_trigger: str
    disclaimer: str
    source: str = "complyo-internal"


def _parse_type(doc_type: str) -> DocumentType:
    try:
        return DocumentType(doc_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Ungültiger Dokumenttyp '{doc_type}'. Erlaubt: {', '.join(VALID_TYPES)}"
        )


async def _get_generator(request) -> LegalTextGenerator:
    from dependencies import get_db_pool
    db_pool = await get_db_pool()
    return get_legal_text_generator(db_pool)


async def _build_complyo_context(db_pool, user_id: int) -> Optional[dict]:
    """Leitet aus den aktiven Complyo-Konfigurationen ab, welche Dienste beim
    Kunden laufen, damit der Datenschutz-Passus nur die tatsächlich aktiven
    Dienste beschreibt (modular). Gibt None zurück, wenn KEIN Complyo-Dienst
    aktiv ist — dann erscheint kein Passus.
    """
    import json as _json

    # 1) Cookie-Consent-Banner (autoritative Quelle: cookie_banner_configs)
    row = None
    try:
        row = await db_pool.fetchrow(
            """
            SELECT cookie_lifetime_days, services
            FROM cookie_banner_configs
            WHERE user_id = $1 AND is_active = true
            ORDER BY created_at DESC
            LIMIT 1
            """,
            user_id,
        )
    except Exception as e:
        logger.warning(f"Cookie-Banner-Status nicht ermittelbar (user={user_id}): {e}")

    # 2) A11y-Runtime-Fixer: ein vorhandenes accessibility_fix_package bedeutet,
    #    dass der Kunde den Complyo-Barrierefreiheits-Assistenten einsetzt, der das
    #    Skript zur Laufzeit von api.complyo.de nachlädt (Channel #3). user_id ist
    #    dort VARCHAR — daher als Text vergleichen.
    a11y_active = False
    try:
        a11y_active = bool(
            await db_pool.fetchval(
                "SELECT 1 FROM accessibility_fix_packages WHERE user_id = $1 LIMIT 1",
                str(user_id),
            )
        )
    except Exception as e:
        logger.warning(f"A11y-Status nicht ermittelbar (user={user_id}): {e}")

    cookie_active = row is not None
    if not cookie_active and not a11y_active:
        return None

    services = row.get("services") if row else None
    if isinstance(services, str):
        try:
            services = _json.loads(services)
        except (ValueError, TypeError):
            services = []
    services = services or []

    # Drittland-Gating (Art. 49): True, sobald ein konfigurierter Dienst
    # personenbezogene Daten in ein unsicheres Drittland überträgt.
    third_country = any(
        isinstance(s, dict) and s.get("requires_third_country_consent")
        for s in services
    )

    return {
        "cookie_banner_active": cookie_active,
        "cookie_lifetime_days": int((row.get("cookie_lifetime_days") if row else None) or 365),
        "a11y_widget_active": a11y_active,
        "third_country_services_enabled": third_country,
    }


@router.get("/{doc_type}", response_model=LegalTextResponse)
async def get_legal_text(
    doc_type: str,
    user_id: int = Depends(get_current_user_id),
):
    """Gibt das aktive Dokument des Users zurück."""
    dt = _parse_type(doc_type)
    from dependencies import get_db_pool
    db_pool = await get_db_pool()
    generator = get_legal_text_generator(db_pool)

    doc = await generator.get_active_document(user_id, dt)
    if not doc:
        raise HTTPException(
            status_code=404,
            detail=f"Kein aktives {doc_type}-Dokument gefunden. Bitte zuerst generieren."
        )

    import json
    meta = doc.get("metadata") or {}
    if isinstance(meta, str):
        meta = json.loads(meta)

    return LegalTextResponse(
        document_id=doc["id"],
        document_type=doc["document_type"],
        language=doc.get("language", "de"),
        html_content=doc.get("html_content") or doc.get("content", ""),
        plain_text=LegalTextGenerator._strip_html(doc.get("html_content") or doc.get("content", "")),
        template_version=meta.get("template_version", "1.0"),
        generated_at=doc["created_at"].isoformat() if hasattr(doc["created_at"], "isoformat") else str(doc["created_at"]),
        regeneration_trigger=meta.get("regeneration_trigger", "manual"),
        disclaimer=DISCLAIMER_LONG,
        source="complyo-internal",
    )


@router.post("/{doc_type}/generate", response_model=LegalTextResponse)
async def generate_legal_text(
    doc_type: str,
    body: GenerateRequest,
    user_id: int = Depends(get_current_user_id),
):
    """Erzwingt neue KI-Generierung und speichert das Ergebnis."""
    dt = _parse_type(doc_type)
    from dependencies import get_db_pool
    db_pool = await get_db_pool()
    generator = get_legal_text_generator(db_pool)

    user_data = body.user_data.model_dump(exclude_none=True)

    try:
        if dt == DocumentType.IMPRINT:
            result = await generator.generate_imprint(user_id, user_data, body.language)
        elif dt == DocumentType.PRIVACY:
            complyo_context = await _build_complyo_context(db_pool, user_id)
            result = await generator.generate_privacy_policy(
                user_id, user_data, body.services_used, body.language,
                complyo_context=complyo_context,
            )
        elif dt == DocumentType.TOS:
            result = await generator.generate_tos(
                user_id, user_data, body.business_type or "saas", body.language
            )
        elif dt == DocumentType.COOKIE_POLICY:
            result = await generator.generate_cookie_policy(
                user_id, user_data, body.cookie_inventory, body.language
            )
        elif dt == DocumentType.WITHDRAWAL:
            result = await generator.generate_withdrawal(user_id, user_data, body.language)
        else:
            raise HTTPException(status_code=400, detail="Unbekannter Dokumenttyp")
    except Exception as e:
        logger.error(f"Generierung fehlgeschlagen ({doc_type}, user={user_id}): {e}")
        raise HTTPException(status_code=500, detail=f"Generierung fehlgeschlagen: {str(e)}")

    return LegalTextResponse(
        document_id=result.document_id,
        document_type=result.document_type,
        language=result.language,
        html_content=result.html_content,
        plain_text=result.plain_text,
        template_version=result.template_version,
        generated_at=result.generated_at,
        regeneration_trigger=result.regeneration_trigger,
        disclaimer=result.disclaimer,
        source="complyo-internal",
    )


@router.get("/{doc_type}/history")
async def get_legal_text_history(
    doc_type: str,
    user_id: int = Depends(get_current_user_id),
    limit: int = Query(10, ge=1, le=50),
):
    """Gibt die Versionshistorie eines Dokumenttyps zurück."""
    dt = _parse_type(doc_type)
    from dependencies import get_db_pool
    db_pool = await get_db_pool()
    generator = get_legal_text_generator(db_pool)

    history = await generator.get_document_history(user_id, dt, limit)
    return {
        "document_type": doc_type,
        "user_id": user_id,
        "versions": history,
        "count": len(history),
    }


@router.get("/{doc_type}/preview")
async def preview_legal_text(
    doc_type: str,
    company_name: str = Query(...),
    language: str = Query("de"),
    email: Optional[str] = Query(None),
    address: Optional[str] = Query(None),
):
    """
    Generiert eine Preview ohne Speichern in der DB.
    Ideal für den Onboarding-Wizard.
    """
    dt = _parse_type(doc_type)
    from dependencies import get_db_pool
    db_pool = await get_db_pool()
    generator = get_legal_text_generator(db_pool)

    user_data = {
        "company_name": company_name,
        "email": email or "[E-MAIL AUSFÜLLEN]",
        "address": address or "[ADRESSE AUSFÜLLEN]",
    }

    class _NullSaveGenerator(LegalTextGenerator):
        async def _save(self, *args, **kwargs):
            return None

    preview_gen = _NullSaveGenerator(db_pool)

    try:
        if dt == DocumentType.IMPRINT:
            result = await preview_gen.generate_imprint(0, user_data, language)
        elif dt == DocumentType.PRIVACY:
            result = await preview_gen.generate_privacy_policy(0, user_data, language=language)
        elif dt == DocumentType.TOS:
            result = await preview_gen.generate_tos(0, user_data, language=language)
        elif dt == DocumentType.COOKIE_POLICY:
            result = await preview_gen.generate_cookie_policy(0, user_data, language=language)
        elif dt == DocumentType.WITHDRAWAL:
            result = await preview_gen.generate_withdrawal(0, user_data, language=language)
        else:
            raise HTTPException(status_code=400, detail="Unbekannter Dokumenttyp")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Preview fehlgeschlagen: {str(e)}")

    return {
        "document_type": doc_type,
        "language": language,
        "html_content": result.html_content,
        "disclaimer": DISCLAIMER_SHORT,
        "is_preview": True,
        "note": "Diese Preview wird nicht gespeichert.",
    }
