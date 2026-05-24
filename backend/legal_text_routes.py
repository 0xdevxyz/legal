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
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from legal_text_generator import LegalTextGenerator, DocumentType, get_legal_text_generator
from legal_disclaimer import DISCLAIMER_LONG, DISCLAIMER_SHORT

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/legal-texts", tags=["legal-texts"])

VALID_TYPES = {t.value for t in DocumentType}


class LegalTextUserData(BaseModel):
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


@router.get("/{doc_type}", response_model=LegalTextResponse)
async def get_legal_text(
    doc_type: str,
    user_id: int = Query(..., description="User-ID (aus JWT)"),
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
    user_id: int = Query(..., description="User-ID (aus JWT)"),
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
            result = await generator.generate_privacy_policy(
                user_id, user_data, body.services_used, body.language
            )
        elif dt == DocumentType.TOS:
            result = await generator.generate_tos(
                user_id, user_data, body.business_type or "saas", body.language
            )
        elif dt == DocumentType.COOKIE_POLICY:
            result = await generator.generate_cookie_policy(
                user_id, user_data, body.cookie_inventory, body.language
            )
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
    user_id: int = Query(..., description="User-ID (aus JWT)"),
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
