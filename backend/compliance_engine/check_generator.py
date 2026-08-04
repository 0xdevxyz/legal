"""
Declarative Check Generator
===========================
Schließt die fehlende Kette "erkanntes Gesetz -> automatische Prüfung".

Bisher endete die Legal-Update-Pipeline beim Versionieren BESTEHENDER Regeln —
eine völlig neue Pflicht (z.B. Widerrufsbutton) konnte nie zu einer neuen
Website-Prüfung werden. Dieser Generator nimmt eine erkannte Gesetzesänderung,
lässt das LLM sie in eine deklarative `compliance_checks`-Definition übersetzen
(sofern sie dem "required_element"-Muster folgt) und legt sie an.

Sicherheits-Gate: Neue Auto-Checks landen als `pending_review` und werden erst
durch das Admin-GO scharf geschaltet. Über das Env-Flag
AUTO_ACTIVATE_GENERATED_CHECKS=true entfällt das Review für unkritische Checks
(voll automatisch). Ausnahme (Safety-Governor): Checks mit severity=critical
bleiben IMMER `pending_review` — ein False-Positive trifft Kunden dort am
härtesten, daher nie ohne menschliche Freigabe.
"""

import os
import re
import json
import logging
from difflib import SequenceMatcher
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

    # Qualitaets-Gate (Regel-SSOT check_spec_rules, siehe Audit 2026-07):
    from compliance_engine.check_spec_rules import (
        detection_is_weak, detection_is_inverted, AUTO_CHECK_RISK_CAP,
    )
    inverted = detection_is_inverted(spec["detection"])
    if inverted:
        return (
            f"inverted logic: '{inverted}' ist ein Verstoss-Indikator und darf "
            f"nicht als required_element verlangt werden (der Check wuerde bei "
            f"konformen Seiten feuern und beim Verstoss schweigen)"
        )
    if detection_is_weak(spec["detection"]):
        return (
            "weak detection: generische Rechtsseiten-Link-Keywords ohne "
            "content_requirements bestehen auf jeder Seite mit DS-/Impressum-Link "
            "— content_requirements ergaenzen oder spezifische html_patterns nutzen"
        )
    if spec["risk_euro"] > AUTO_CHECK_RISK_CAP:
        return f"risk_euro {spec['risk_euro']} ueber KMU-Deckel {AUTO_CHECK_RISK_CAP}"
    return None


def _auto_activate() -> bool:
    return os.getenv("AUTO_ACTIVATE_GENERATED_CHECKS", "false").lower() in ("1", "true", "yes")


# --------------------------------------------------------------------------
# Themen-Dedup
# --------------------------------------------------------------------------
# Der Monitor recherchiert mit einem rollierenden 30-Tage-Fenster: dieselbe
# Pflicht (z.B. AI-Act-Kennzeichnung ab 02.08.2026) wird an vielen Tagen erneut
# gemeldet und bekommt jedes Mal eine neue legal_updates.id. Die bisherige
# Idempotenz griff nur über source_legal_update_id und den exakten Slug — das
# LLM formuliert den Slug aber jedes Mal etwas anders. Ergebnis waren 11 aktive
# Prüfungen für ein und dieselbe Pflicht, die ein Kunde alle einzeln als Befund
# sah. Diese Sperre vergleicht deshalb das THEMA, nicht den String.

_SLUG_STOPWORDS = {
    "fehlt", "fehlend", "vorhanden", "erforderlich", "required", "pflicht",
    "website", "websites", "webseite", "seite", "neu", "neue", "und", "der",
    "die", "das", "fuer", "für", "auf", "bei", "von",
    # Kontextwoerter ohne Unterscheidungskraft in Check-Slugs — verwaesserten
    # die Jaccard-Aehnlichkeit von Themen-Zwillingen (dsa-transparenzbericht-
    # online-plattform vs. -hosting). Der Norm-Referenz-Filter in
    # _is_same_topic schuetzt weiterhin vor Ueber-Dedup.
    "online", "plattform", "plattformen", "hosting", "dienst", "dienste",
}

# Beide Schwellen müssen greifen, damit zwei Prüfungen als dasselbe Thema gelten.
# Gegen die 131 aktiven Checks vom 29.07.2026 kalibriert: Slug allein ab 0.5 zieht
# fachlich verschiedene Pflichten zusammen (z.B. "netzdg-transparenzbericht-*" mit
# "netzdg-meldesystem-*"); Titel-Ähnlichkeit allein scheitert an der deutschen
# Flexion ("KI-generierter Inhalte" vs. "KI-generierten Inhalten").
_SLUG_SIMILARITY_THRESHOLD = 0.6
_TITLE_SIMILARITY_THRESHOLD = 0.6


# Praefix-Synonyme: verschiedene Wortbildungen derselben Pflicht (melde-
# mechanismus/-system/-wege, transparenzbericht-*) sollen als EIN Token
# zaehlen — sonst rutschen Themen-Zwillinge unter die Jaccard-Schwelle
# (so entstanden 4 parallele dsa-melde*-Checks im Altbestand).
_TOKEN_SYNONYM_PREFIXES = (
    "melde", "transparenzbericht", "kennzeichnung", "kuendigungs",
    "beschwerde", "transparenzhinweis",
)


def _canon_token(token: str) -> str:
    for prefix in _TOKEN_SYNONYM_PREFIXES:
        if token.startswith(prefix):
            return prefix
    return token


def _slug_tokens(slug: str) -> set:
    return {
        _canon_token(t) for t in re.split(r"[-_\s]+", (slug or "").lower())
        if len(t) >= 2 and t not in _SLUG_STOPWORDS
    }


def _jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _normalize_title(title: str) -> str:
    text = (title or "").lower()
    for umlaut, replacement in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        text = text.replace(umlaut, replacement)
    return re.sub(r"[^a-z0-9 ]", " ", text)


def _norm_refs(legal_basis: str) -> set:
    """Zieht Norm-Nummern aus der Rechtsgrundlage ('Art. 50', '§ 25')."""
    return set(re.findall(r"(?:art(?:ikel)?\.?|§)\s*(\d+[a-z]?)", (legal_basis or "").lower()))


def _is_same_topic(spec: Dict[str, Any], existing: Dict[str, Any]) -> bool:
    """Prüft, ob `spec` fachlich dieselbe Pflicht abdeckt wie ein bestehender Check."""
    if _jaccard(_slug_tokens(spec.get("slug", "")),
                _slug_tokens(existing.get("slug", ""))) < _SLUG_SIMILARITY_THRESHOLD:
        return False

    title_similarity = SequenceMatcher(
        None,
        _normalize_title(spec.get("title", "")),
        _normalize_title(existing.get("title", "")),
    ).ratio()
    if title_similarity < _TITLE_SIMILARITY_THRESHOLD:
        return False

    # Letzter Filter: verschiedene Normen = verschiedene Pflichten, auch wenn
    # Slug und Titel fast gleich klingen. AI Act Art. 50 (Kennzeichnung
    # KI-generierter Inhalte) ist NICHT Art. 13 (Hochrisiko-Transparenz) —
    # ohne diesen Vergleich hätte der Guard die zweite Pflicht unterdrückt.
    # Fehlt auf einer Seite die Normangabe, entscheiden Slug und Titel allein.
    new_refs = _norm_refs(spec.get("legal_basis", ""))
    old_refs = _norm_refs(existing.get("legal_basis", ""))
    if new_refs and old_refs and new_refs != old_refs:
        return False

    return True


async def _find_topic_duplicate(conn, spec: Dict[str, Any]) -> Optional[str]:
    """Gibt den Slug eines bestehenden Checks zurück, der dasselbe Thema abdeckt."""
    rows = await conn.fetch(
        """
        SELECT slug, title, legal_basis
        FROM compliance_checks
        WHERE status IN ('active', 'pending_review')
        """
    )
    for row in rows:
        if _is_same_topic(spec, dict(row)):
            return row["slug"]
    return None


async def _find_topic_twin(conn, spec: "Dict[str, Any]") -> "Optional[str]":
    """
    Sucht einen bestehenden Check mit demselben THEMA (nicht demselben Namen).

    Ergaenzt `_find_topic_duplicate`: der vergleicht Zeichenketten und uebersieht
    Zwillinge mit abweichend gebautem Slug. Hier entscheidet die Themen-Tabelle
    in `check_topics` — eine gepflegte Liste praktischer Pflichten.
    """
    from compliance_engine.check_topics import erkenne_thema

    thema = erkenne_thema(spec.get("slug", ""), spec.get("title", ""))
    if not thema:
        return None

    rows = await conn.fetch(
        """
        SELECT slug, title
        FROM compliance_checks
        WHERE status IN ('active', 'pending_review')
        """
    )
    for row in rows:
        if erkenne_thema(row["slug"], row["title"]) == thema:
            return row["slug"]
    return None


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
    # Safety-Governor: kritische Auto-Checks nie ungereviewt scharf schalten.
    # Ein False-Positive bei einem critical-Check trifft Kunden am haertesten
    # (roter Score-Einbruch, Fehlalarm). Selbst bei AUTO_ACTIVATE_GENERATED_CHECKS
    # landen sie in der Admin-Review-Queue; /checks/{id}/activate gibt das finale GO.
    if status == "active" and spec.get("severity") == "critical":
        status = "pending_review"
        logger.info(
            f"check_generator: {spec.get('slug')} ist critical -> trotz "
            f"Auto-Activate auf pending_review (Safety-Governor)"
        )
    # Always-gated Checks laufen auf JEDER Kundenseite — ob die vom LLM
    # erfundenen Detection-Begriffe verbreitet genug sind, kann statisch
    # nicht validiert werden (Haupttreiber der Cookie-FP-Duplikate im
    # Altbestand). Ein Mensch gibt frei.
    if status == "active" and (spec.get("applies_when") or {}).get("always") is True:
        status = "pending_review"
        logger.info(
            f"check_generator: {spec.get('slug')} ist always-gated -> trotz "
            f"Auto-Activate auf pending_review (Safety-Governor)"
        )

    try:
        async with db_pool.acquire() as conn:
            duplicate_of = await _find_topic_duplicate(conn, spec)
            if duplicate_of:
                logger.info(
                    f"check_generator: #{update_id} übersprungen — Thema bereits "
                    f"abgedeckt durch '{duplicate_of}'"
                )
                result["reason"] = f"topic already covered by '{duplicate_of}'"
                return result

            # Dritte Stufe: gleiches Thema trotz anderem Namen. Nicht verwerfen —
            # eine Detailpflicht kann dasselbe Thema treffen und trotzdem neu
            # sein. Ein Mensch entscheidet in der Review-Queue.
            twin_of = await _find_topic_twin(conn, spec)
            if twin_of and status == "active":
                status = "pending_review"
                logger.info(
                    f"check_generator: {spec.get('slug')} trifft dasselbe Thema wie "
                    f"'{twin_of}' -> pending_review statt active (Safety-Governor)"
                )

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
