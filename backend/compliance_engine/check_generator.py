"""
Declarative Check Generator
===========================
Schließt die fehlende Kette "erkanntes Gesetz -> automatische Prüfung".

Bisher endete die Legal-Update-Pipeline beim Versionieren BESTEHENDER Regeln —
eine völlig neue Pflicht (z.B. Widerrufsbutton) konnte nie zu einer neuen
Website-Prüfung werden. Dieser Generator nimmt eine erkannte Gesetzesänderung,
lässt das LLM sie in eine deklarative `compliance_checks`-Definition übersetzen
(sofern sie dem "required_element"-Muster folgt) und legt sie an.

Sicherheits-Gate (Testphase): Neue Auto-Checks landen als `pending_review` und
werden erst durch das Admin-GO scharf geschaltet. Über das Env-Flag
AUTO_ACTIVATE_GENERATED_CHECKS=true entfällt das Review (voll automatisch).
"""

import os
import re
import json
import logging
from typing import Dict, Any, Optional, Callable, Awaitable

logger = logging.getLogger(__name__)


GENERATION_PROMPT = """\
Du bist Compliance-Engineer. Übersetze die folgende Gesetzesänderung in eine
MASCHINENPRÜFBARE Definition für einen Website-Scanner — ABER NUR, wenn sich die
Pflicht als "auf der Website muss ein bestimmtes Element / eine Seite / ein Button
vorhanden sein" ausdrücken lässt (Muster "required_element").

# GESETZESÄNDERUNG
Titel: {title}
Beschreibung: {description}
Anforderungen:
{requirements}

# REGELN
- Wenn die Pflicht NICHT als Vorhandensein eines konkreten, im HTML erkennbaren
  Elements prüfbar ist (z.B. reine Dokumentationspflichten, interne Prozesse),
  antworte exakt mit: {{"applicable": false}}
- Sonst liefere GENAU dieses JSON (keine Erklärung, kein Markdown):

{{
  "applicable": true,
  "slug": "kebab-case-eindeutig",
  "category": "shop" | "datenschutz" | "impressum" | "cookie" | "barrierefreiheit" | "shop",
  "title": "Kurzer Titel des Issues, wenn das Element fehlt",
  "description": "Was fehlt und warum es Pflicht ist (1-3 Sätze).",
  "recommendation": "Konkrete Handlungsanweisung zur Behebung.",
  "legal_basis": "Paragraf / Richtlinie + Datum",
  "severity": "warning",
  "risk_euro": 2000,
  "applies_when": {{"site_type": "shop"}} ODER {{"keywords_any": ["..."]}} ODER {{"always": true}},
  "detection": {{
    "type": "required_element",
    "link_text_keywords": ["sichtbarer linktext (kleingeschrieben)"],
    "link_href_keywords": ["url-fragmente"],
    "html_patterns": ["regex fuer inline-buttons/text"],
    "url_paths": ["/kandidaten-pfad"]
  }}
}}

# WICHTIG
- detection MUSS mindestens eines der Felder link_text_keywords / link_href_keywords
  / html_patterns / url_paths sinnvoll gefüllt haben.
- Wähle Keywords spezifisch genug, um Fehlalarme zu vermeiden.
- severity: im Zweifel "warning".
- Antworte AUSSCHLIESSLICH mit dem JSON-Objekt.
"""

CallAi = Callable[[str], Awaitable[str]]


def _strip_json(raw: str) -> str:
    """Entfernt Markdown-Fences und extrahiert das erste JSON-Objekt."""
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?", "", raw).strip()
    raw = re.sub(r"```$", "", raw).strip()
    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        return raw[start:end + 1]
    return raw


def _valid_detection(detection: Dict[str, Any]) -> bool:
    if not isinstance(detection, dict):
        return False
    if detection.get("type") != "required_element":
        return False
    signal_fields = ["link_text_keywords", "link_href_keywords", "html_patterns", "url_paths"]
    return any(
        isinstance(detection.get(f), list) and len(detection.get(f)) > 0
        for f in signal_fields
    )


def _validate_spec(spec: Dict[str, Any]) -> Optional[str]:
    """Gibt None zurück wenn gültig, sonst eine Fehlermeldung."""
    required = ["slug", "category", "title", "description", "recommendation",
                "legal_basis", "severity", "risk_euro", "applies_when", "detection"]
    for field in required:
        if field not in spec or spec[field] in (None, ""):
            return f"missing field: {field}"
    if spec["severity"] not in ("critical", "warning", "info"):
        return f"invalid severity: {spec['severity']}"
    if not isinstance(spec["risk_euro"], int) or spec["risk_euro"] <= 0:
        return "risk_euro must be positive int"
    if not isinstance(spec["applies_when"], dict):
        return "applies_when must be object"
    if not _valid_detection(spec["detection"]):
        return "detection invalid (need type=required_element + >=1 signal field)"
    # Validate regex patterns compile
    for pat in spec["detection"].get("html_patterns", []):
        try:
            re.compile(pat)
        except re.error as e:
            return f"invalid html_pattern '{pat}': {e}"
    return None


def _auto_activate() -> bool:
    return os.getenv("AUTO_ACTIVATE_GENERATED_CHECKS", "false").lower() in ("1", "true", "yes")


async def generate_check_for_legal_update(
    db_pool,
    legal_update: Dict[str, Any],
    call_ai: CallAi,
) -> Dict[str, Any]:
    """
    Erzeugt aus einem legal_update-Eintrag (per LLM) einen deklarativen Check.

    Returns:
        {"created": bool, "slug": str|None, "status": str|None, "reason": str|None}
    """
    update_id = legal_update.get("id")
    result = {"created": False, "slug": None, "status": None, "reason": None}

    if not db_pool:
        result["reason"] = "no db_pool"
        return result

    # Idempotenz: existiert schon ein Check aus diesem Legal-Update?
    try:
        async with db_pool.acquire() as conn:
            exists = await conn.fetchval(
                "SELECT 1 FROM compliance_checks WHERE source_legal_update_id = $1 LIMIT 1",
                update_id,
            )
            if exists:
                result["reason"] = "check already exists for this legal_update"
                return result
    except Exception as e:
        logger.error(f"check_generator dedup query failed: {e}")
        result["reason"] = f"db error: {e}"
        return result

    requirements = legal_update.get("requirements") or []
    if isinstance(requirements, list):
        req_text = "\n".join(f"- {r}" for r in requirements) or "- (keine strukturierten Anforderungen)"
    else:
        req_text = str(requirements)

    prompt = GENERATION_PROMPT.format(
        title=legal_update.get("title", ""),
        description=legal_update.get("description", ""),
        requirements=req_text,
    )

    try:
        raw = await call_ai(prompt)
        spec = json.loads(_strip_json(raw))
    except Exception as e:
        logger.warning(f"check_generator: LLM/JSON parse failed for #{update_id}: {e}")
        result["reason"] = f"llm/parse error: {e}"
        return result

    if not spec.get("applicable", False):
        result["reason"] = "not expressible as required_element check"
        return result

    err = _validate_spec(spec)
    if err:
        logger.warning(f"check_generator: invalid spec for #{update_id}: {err}")
        result["reason"] = f"invalid spec: {err}"
        return result

    status = "active" if _auto_activate() else "pending_review"

    try:
        async with db_pool.acquire() as conn:
            inserted = await conn.fetchval(
                """
                INSERT INTO compliance_checks
                    (slug, category, title, description, recommendation, legal_basis,
                     severity, risk_euro, applies_when, detection, effective_date,
                     status, auto_generated, source_legal_update_id, generation_notes)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9::jsonb,$10::jsonb,
                        COALESCE($11::date, CURRENT_DATE), $12, TRUE, $13, $14)
                ON CONFLICT (slug) DO NOTHING
                RETURNING slug
                """,
                spec["slug"], spec["category"], spec["title"], spec["description"],
                spec["recommendation"], spec["legal_basis"], spec["severity"],
                int(spec["risk_euro"]),
                json.dumps(spec["applies_when"]), json.dumps(spec["detection"]),
                legal_update.get("effective_date"),
                status, update_id,
                f"Auto-generiert aus Legal-Update #{update_id}: {legal_update.get('title', '')}",
            )
        if inserted:
            result.update({"created": True, "slug": inserted, "status": status})
            logger.info(f"✅ check_generator: created '{inserted}' (status={status}) from update #{update_id}")
        else:
            result["reason"] = f"slug '{spec['slug']}' already exists"
    except Exception as e:
        logger.error(f"check_generator insert failed for #{update_id}: {e}", exc_info=True)
        result["reason"] = f"insert error: {e}"

    return result
