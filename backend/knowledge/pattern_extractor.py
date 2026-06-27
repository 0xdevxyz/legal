import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import yaml

logger = logging.getLogger(__name__)

VAULT_ROOT = Path(os.getenv("KNOWLEDGE_VAULT_PATH", "/home/clawd/saas/legal/knowledge"))
PATTERNS_DIR = VAULT_ROOT / "patterns"

KNOWN_PATTERNS = [
    {
        "check_name": "cookie_check",
        "slug": "cookie-check",
        "title": "Cookie-Consent Fehler",
        "law_areas": ["TTDSG", "DSGVO"],
        "description": "Häufige Fehler bei der Cookie-Einwilligung nach § 25 TTDSG",
        "patterns": [
            {
                "name": "Kein Ablehn-Button",
                "frequency": "sehr häufig",
                "bad_code": '<button onclick="acceptAll()">Alle akzeptieren</button>',
                "good_code": '<button onclick="acceptAll()">Alle akzeptieren</button>\n<button onclick="rejectAll()">Ablehnen</button>',
                "law_ref": "§ 25 TTDSG – Einwilligung muss freiwillig sein",
            },
            {
                "name": "Tracking vor Einwilligung",
                "frequency": "häufig",
                "bad_code": "<!-- Google Analytics vor Consent-Check -->\n<script async src='https://www.googletagmanager.com/gtag/js?id=GA_ID'></script>",
                "good_code": "<!-- Erst laden wenn Consent gegeben -->\n<script>\nif (window.cookieConsent && window.cookieConsent.analytics) {\n  // Google Analytics laden\n}\n</script>",
                "law_ref": "DSGVO Art. 6 + § 25 TTDSG",
            },
            {
                "name": "Vorausgewählte Checkboxen",
                "frequency": "häufig",
                "bad_code": '<input type="checkbox" name="analytics" checked> Analytics aktivieren',
                "good_code": '<input type="checkbox" name="analytics"> Analytics aktivieren',
                "law_ref": "DSGVO Art. 7 Abs. 2 – Opt-In Pflicht",
            },
        ],
    },
    {
        "check_name": "impressum_check",
        "slug": "impressum-check",
        "title": "Impressum Fehler",
        "law_areas": ["TMG", "UWG"],
        "description": "Typische Fehler bei der Impressumspflicht nach § 5 TMG",
        "patterns": [
            {
                "name": "Nur Kontaktformular ohne E-Mail",
                "frequency": "sehr häufig",
                "bad_code": "<!-- Impressum -->\nKontaktformular: <a href='/kontakt'>Kontakt</a>",
                "good_code": "<!-- Impressum -->\nE-Mail: <a href='mailto:info@beispiel.de'>info@beispiel.de</a>",
                "law_ref": "§ 5 Abs. 1 Nr. 2 TMG – E-Mail-Adresse Pflicht",
            },
            {
                "name": "Impressum nur 3+ Klicks erreichbar",
                "frequency": "mittel",
                "bad_code": "<!-- Impressum im verschachtelten Menü -->\nÜber uns > Rechtliches > Impressum",
                "good_code": "<!-- Impressum direkt im Footer -->\n<footer>\n  <a href='/impressum'>Impressum</a>\n</footer>",
                "law_ref": "§ 5 TMG – muss leicht erkennbar und unmittelbar erreichbar sein",
            },
        ],
    },
    {
        "check_name": "barrierefreiheit_check",
        "slug": "barrierefreiheit-check",
        "title": "Barrierefreiheit Fehler",
        "law_areas": ["BFSG"],
        "description": "Häufige WCAG-Verstöße nach BFSG-Prüfung",
        "patterns": [
            {
                "name": "Bilder ohne Alt-Text",
                "frequency": "sehr häufig",
                "bad_code": '<img src="produkt.jpg">',
                "good_code": '<img src="produkt.jpg" alt="Rotes T-Shirt aus Bio-Baumwolle">',
                "law_ref": "WCAG 2.1 Kriterium 1.1.1 – Nicht-Text-Inhalte",
            },
            {
                "name": "Zu geringer Kontrast",
                "frequency": "häufig",
                "bad_code": "/* Text: #999999 auf #FFFFFF = Kontrast 2.85:1 (Minimum: 4.5:1) */\ncolor: #999999;",
                "good_code": "/* Text: #595959 auf #FFFFFF = Kontrast 7.0:1 */\ncolor: #595959;",
                "law_ref": "WCAG 2.1 Kriterium 1.4.3 – Kontrast Minimum 4.5:1",
            },
            {
                "name": "Formularfelder ohne Label",
                "frequency": "häufig",
                "bad_code": '<input type="email" placeholder="E-Mail">',
                "good_code": '<label for="email">E-Mail-Adresse</label>\n<input type="email" id="email" placeholder="name@beispiel.de">',
                "law_ref": "WCAG 2.1 Kriterium 1.3.1 – Info und Beziehungen",
            },
        ],
    },
    {
        "check_name": "datenschutz_check",
        "slug": "datenschutz-check",
        "title": "Datenschutzerklärung Fehler",
        "law_areas": ["DSGVO"],
        "description": "Typische Mängel in Datenschutzerklärungen nach DSGVO Art. 13/14",
        "patterns": [
            {
                "name": "Fehlende Rechtsgrundlage",
                "frequency": "sehr häufig",
                "bad_code": "Wir verarbeiten Ihre Daten für Newsletter-Zwecke.",
                "good_code": "Wir verarbeiten Ihre Daten für Newsletter-Zwecke auf Grundlage Ihrer Einwilligung (Art. 6 Abs. 1 lit. a DSGVO). Sie können Ihre Einwilligung jederzeit widerrufen.",
                "law_ref": "DSGVO Art. 13 Abs. 1 lit. c – Zwecke und Rechtsgrundlage",
            },
            {
                "name": "Fehlende Drittland-Übermittlung",
                "frequency": "häufig",
                "bad_code": "Wir nutzen Google Analytics zur Analyse.",
                "good_code": "Wir nutzen Google Analytics (Google LLC, USA). Ihre Daten werden in die USA übertragen. Rechtsgrundlage: Ihre Einwilligung (Art. 6 Abs. 1 lit. a DSGVO) i.V.m. den EU-Standardvertragsklauseln.",
                "law_ref": "DSGVO Art. 13 Abs. 1 lit. f + Art. 46",
            },
        ],
    },
]


def _build_pattern_frontmatter(pattern_def: Dict[str, Any]) -> str:
    fm = {
        "title": f"Muster: {pattern_def['title']}",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "category": "pattern",
        "law_areas": pattern_def["law_areas"],
        "relevance_score": 0.9,
        "impact": "high",
        "source_url": "",
        "source_type": "internal",
        "affected_checks": [pattern_def["check_name"]],
        "tags": ["pattern"] + pattern_def["law_areas"],
        "obsidian_links": [f"[[{la}]]" for la in pattern_def["law_areas"]],
        "status": "active",
        "embedding_hash": "",
        "last_embedded": "",
    }
    return "---\n" + yaml.dump(fm, allow_unicode=True, default_flow_style=False) + "---\n"


def _build_pattern_body(pattern_def: Dict[str, Any]) -> str:
    parts = [
        f"# Muster: {pattern_def['title']}\n\n",
        f"{pattern_def['description']}\n\n",
    ]

    for i, p in enumerate(pattern_def["patterns"], 1):
        parts.append(f"## Muster {i}: {p['name']}\n\n")
        parts.append(f"**Häufigkeit:** {p['frequency']}\n\n")
        parts.append(f"**Rechtsgrundlage:** {p['law_ref']}\n\n")
        parts.append("### Fehlerhafte Implementierung\n\n")
        parts.append(f"```html\n{p['bad_code']}\n```\n\n")
        parts.append("### Korrekte Implementierung\n\n")
        parts.append(f"```html\n{p['good_code']}\n```\n\n")

    parts.append("## Betroffene complyo-Checks\n\n")
    parts.append(f"- [[{pattern_def['check_name']}]]\n\n")
    parts.append("## Verwandte Gesetze\n\n")
    parts.append(" | ".join([f"[[{la}]]" for la in pattern_def["law_areas"]]) + "\n\n")
    parts.append(f"---\n*Automatisch generiert am {datetime.now().strftime('%Y-%m-%d')} durch complyo Pattern Extractor*\n")

    return "".join(parts)


class PatternExtractor:
    def __init__(self, db_pool=None):
        self.db_pool = db_pool
        PATTERNS_DIR.mkdir(parents=True, exist_ok=True)

    def generate_static_patterns(self) -> List[str]:
        paths = []
        for pattern_def in KNOWN_PATTERNS:
            filepath = PATTERNS_DIR / f"{pattern_def['slug']}-patterns.md"
            if filepath.exists():
                logger.debug(f"Pattern file exists: {filepath.name}")
                paths.append(str(filepath))
                continue

            content = _build_pattern_frontmatter(pattern_def) + "\n" + _build_pattern_body(pattern_def)
            filepath.write_text(content, encoding="utf-8")
            logger.info(f"Written pattern: {filepath.name}")
            paths.append(str(filepath))

        return paths

    async def extract_from_scan_data(self) -> List[str]:
        if not self.db_pool:
            logger.info("No DB pool, using static patterns only")
            return self.generate_static_patterns()

        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT
                        check_type,
                        issue_title,
                        COUNT(*) as frequency,
                        MAX(created_at) as last_seen
                    FROM scan_issues
                    WHERE created_at >= NOW() - INTERVAL '30 days'
                    GROUP BY check_type, issue_title
                    HAVING COUNT(*) >= 5
                    ORDER BY frequency DESC
                    LIMIT 50
                    """
                )
                logger.info(f"Found {len(rows)} frequent patterns in DB scan data")
        except Exception as e:
            logger.warning(f"Could not fetch scan data from DB: {e}")

        return self.generate_static_patterns()

    async def run(self) -> List[str]:
        return await self.extract_from_scan_data()
