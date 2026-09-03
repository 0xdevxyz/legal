"""
Jurisdiction-Profil-Registry (Stufe 1: "de" + "eu").

Ein Codebase, Jurisdiction als Config: Jedes Profil definiert Sprache,
aktive Checks und gewertete Score-Säulen. Die Engine aktiviert Checks
und Säulen ausschließlich über diese Registry — neue Rechtsräume werden
als weiterer Eintrag ergänzt, ohne Engine-Änderung.

Check-Namen entsprechen den Modulen in compliance_engine/checks/:
    datenschutz, cookie, impressum, barrierefreiheit, agb, uwg,
    pangv, widerruf (Teil von shop_check), tcf
Säulen entsprechen ScoreCalculator.PILLAR_IDS:
    accessibility, gdpr, legal, cookies
"""

from typing import Dict, List

DEFAULT_JURISDICTION = "de"

JURISDICTION_PROFILES: Dict[str, Dict] = {
    "de": {
        "language": "de",
        "checks": [
            "datenschutz", "cookie", "impressum", "barrierefreiheit",
            "agb", "uwg", "pangv", "widerruf", "tcf",
        ],
        "pillars": ["accessibility", "gdpr", "legal", "cookies"],
    },
    "eu": {
        "language": "en",
        # DE-only Checks (Impressum/AGB/UWG/PAngV/Widerruf) deaktiviert
        "checks": ["datenschutz", "cookie", "barrierefreiheit", "tcf"],
        "pillars": ["accessibility", "gdpr", "cookies"],
    },
}

SUPPORTED_JURISDICTIONS = tuple(JURISDICTION_PROFILES.keys())


def normalize_jurisdiction(value: str) -> str:
    """Normalisiert Eingaben ("DE", " eu ", None) auf einen Registry-Key.

    Unbekannte/leere Werte fallen sicher auf DEFAULT_JURISDICTION zurück,
    damit Alt-Daten und fehlerhafte Eingaben nie einen Scan brechen.
    """
    if not value or not isinstance(value, str):
        return DEFAULT_JURISDICTION
    key = value.strip().lower()
    return key if key in JURISDICTION_PROFILES else DEFAULT_JURISDICTION


def is_supported_jurisdiction(value: str) -> bool:
    """True, wenn value (case-insensitiv) ein bekanntes Profil ist."""
    return isinstance(value, str) and value.strip().lower() in JURISDICTION_PROFILES


def active_checks(jurisdiction: str) -> List[str]:
    """Liste der aktiven Check-Namen für das Profil."""
    return list(JURISDICTION_PROFILES[normalize_jurisdiction(jurisdiction)]["checks"])


def active_pillars(jurisdiction: str) -> List[str]:
    """Liste der gewerteten Score-Säulen für das Profil."""
    return list(JURISDICTION_PROFILES[normalize_jurisdiction(jurisdiction)]["pillars"])


def profile_language(jurisdiction: str) -> str:
    """Ausgabesprache des Profils ("de" | "en")."""
    return JURISDICTION_PROFILES[normalize_jurisdiction(jurisdiction)]["language"]


async def get_effective_jurisdiction(conn, website_id, user_id) -> str:
    """Effektive Jurisdiction einer Website: Site-Override oder Account-Default.

    tracked_websites.jurisdiction (Pro-Site-Override, NULL = erben)
    → user_limits.jurisdiction (Account-Default) → DEFAULT_JURISDICTION.
    """
    row = await conn.fetchrow(
        """
        SELECT
            tw.jurisdiction AS site_jurisdiction,
            ul.jurisdiction AS account_jurisdiction
        FROM tracked_websites tw
        LEFT JOIN user_limits ul ON ul.user_id = tw.user_id
        WHERE tw.id = $1 AND tw.user_id = $2
        """,
        website_id, user_id,
    )
    if not row:
        return DEFAULT_JURISDICTION
    return normalize_jurisdiction(
        row["site_jurisdiction"] or row["account_jurisdiction"]
    )
