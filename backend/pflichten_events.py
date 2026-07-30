"""
Pflichten-Events (Phase 7.3 „lebender Pflichten-Graph").

Mappt Einträge aus dem Legal-Change-Monitoring (`legal_updates`) auf die
Katalog-Regeln des Pflichten-Reports (pflichten_katalog.PFLICHTEN) und
persistiert sie als `pflichten_events`. Damit wird der Report lebendig:
„Zu dieser Pflicht gibt es eine neue Entwicklung."

Design:
- Keyword-Mapping auf Titel+Beschreibung (das `update_type`-Feld ist
  historisch unsauber — Severity-Werte und Rechtsgebiete gemischt — und
  dient nur als Zusatz-Hint).
- `sync_pflichten_events()` ist idempotent (UNIQUE + ON CONFLICT DO NOTHING)
  und wird lazy vom Feed-Endpoint aufgerufen — kein eigener Cron nötig;
  sobald das Monitoring neue legal_updates schreibt, tauchen sie beim
  nächsten Feed-Abruf auf.
"""
import logging
import re
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

# rule_id → Muster (case-insensitive) auf title + description + update_type
RULE_KEYWORDS: Dict[str, List[str]] = {
    "dsgvo_datenschutzerklaerung": [r"datenschutzerkl", r"privacy policy", r"art\.?\s*13\s*dsgvo"],
    "impressum": [r"impressum", r"anbieterkennzeichnung", r"§\s*5\s*(ddg|tmg)"],
    "ttdsg_cookie_consent": [r"cookie", r"consent", r"einwilligungsbanner", r"tdddg", r"ttdsg", r"tracking"],
    "bfsg": [r"bfsg", r"barrierefrei", r"accessibility", r"wcag"],
    "ai_act_transparenz": [r"ki[- ]?chatbot", r"kennzeichnungspflicht.*ki", r"ki[- ]generiert", r"ai[- ]act.*(transparenz|kennzeichnung)", r"art\.?\s*50"],
    "ai_act_hochrisiko": [r"hochrisiko", r"high[- ]risk", r"anhang\s*iii"],
    "e_rechnung": [r"e[- ]?rechnung", r"xrechnung", r"zugferd", r"§\s*14\s*ustg"],
    "nis2": [r"nis[- ]?2", r"cybersicherheit.*(pflicht|gesetz)", r"kritis"],
    "cra": [r"cyber resilience", r"\bcra\b", r"produkte mit digitalen elementen"],
    "uwg_newsletter": [r"newsletter", r"e[- ]?mail[- ]?(marketing|werbung)", r"double[- ]?opt[- ]?in", r"§\s*7\s*uwg"],
    "dsgvo_verzeichnis": [r"verzeichnis von verarbeitung", r"\bvvt\b", r"art\.?\s*30"],
    "dsgvo_dsb": [r"datenschutzbeauftragte", r"\bdsb\b", r"art\.?\s*37"],
    "widerruf_shop": [r"widerruf", r"button[- ]?lösung", r"fernabsatz", r"preisangab"],
}

# Grobe update_type-Hints als Ergänzung (nur wo eindeutig)
TYPE_HINTS: Dict[str, List[str]] = {
    "bfsg": ["bfsg"],
    "dsgvo": ["dsgvo_datenschutzerklaerung", "dsgvo_verzeichnis"],
    "tmg": ["impressum"],
    "cookie_compliance": ["ttdsg_cookie_consent"],
    "ai_act": ["ai_act_transparenz", "ai_act_hochrisiko"],
}


def map_update_to_rules(title: str, description: str, update_type: str) -> List[str]:
    """Deterministische Zuordnung eines Legal-Updates zu Katalog-Regeln."""
    haystack = f"{title or ''} {description or ''}".lower()
    hits = {
        rule_id
        for rule_id, patterns in RULE_KEYWORDS.items()
        if any(re.search(p, haystack) for p in patterns)
    }
    hits.update(TYPE_HINTS.get((update_type or "").lower(), []))
    return sorted(hits)


async def sync_pflichten_events(db, limit: int = 300) -> int:
    """Mappt die jüngsten legal_updates auf pflichten_events (idempotent)."""
    rows = await db.fetch(
        """
        SELECT id, title, description, update_type, severity, url,
               published_at, effective_date
        FROM legal_updates
        ORDER BY published_at DESC
        LIMIT $1
        """,
        limit,
    )
    inserted = 0
    for row in rows:
        rule_ids = map_update_to_rules(row["title"], row["description"], row["update_type"])
        for rule_id in rule_ids:
            result = await db.execute(
                """
                INSERT INTO pflichten_events
                    (legal_update_id, rule_id, title, summary, severity,
                     source_url, published_at, effective_date)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (legal_update_id, rule_id) DO NOTHING
                """,
                row["id"], rule_id, row["title"],
                (row["description"] or "")[:1000],
                row["severity"] or "info",
                row["url"], row["published_at"], row["effective_date"],
            )
            if result.endswith("1"):
                inserted += 1
    if inserted:
        logger.info(f"Pflichten-Events: {inserted} neue Zuordnungen erzeugt")
    return inserted


async def get_events_for_rules(db, rule_ids: List[str], limit: int = 50) -> List[Dict[str, Any]]:
    """Änderungs-Feed für die (profil-)relevanten Regeln, neueste zuerst."""
    if not rule_ids:
        return []
    rows = await db.fetch(
        """
        SELECT rule_id, title, summary, severity, source_url,
               published_at, effective_date
        FROM pflichten_events
        WHERE rule_id = ANY($1::text[])
        ORDER BY published_at DESC
        LIMIT $2
        """,
        rule_ids, limit,
    )
    return [dict(r) for r in rows]
