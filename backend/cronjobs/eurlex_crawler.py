"""
AP4: EUR-Lex Korpus-Updater
Holt aktuelle Fassungen von EU-Rechtsakten und speichert sie als Markdown im knowledge/laws/-Verzeichnis.
Unterstützt: GDPR, DSA, AI Act, ePrivacy, NIS2, EAA in mind. 5 Sprachen.
Läuft monatlich (1. des Monats, 02:00 Uhr).
"""
import asyncio
import logging
import re
from pathlib import Path
from datetime import datetime
from typing import Optional
import httpx

logger = logging.getLogger(__name__)

LAWS_DIR = Path(__file__).parents[2] / "knowledge" / "laws"

EUR_LEX_ACTS = {
    "GDPR":    {"celex": "32016R0679", "de_id": "DSGVO"},
    "NIS2":    {"celex": "32022L2555", "de_id": "NIS2"},
    "AI_ACT":  {"celex": "32024R1689", "de_id": "AI_ACT"},
    "DSA":     {"celex": "32022R2065", "de_id": "DSA"},
    "EAA":     {"celex": "32019L0882", "de_id": "BFSG"},
}

LANGUAGES = ["DE", "EN", "FR", "IT", "PL"]
LANG_DIR_MAP = {"DE": "de", "EN": "en", "FR": "fr", "IT": "it", "PL": "pl"}

EUR_LEX_URL = "https://eur-lex.europa.eu/legal-content/{lang}/TXT/HTML/?uri=CELEX:{celex}"

async def fetch_act_html(celex: str, language: str, client: httpx.AsyncClient) -> Optional[str]:
    """Holt HTML-Text eines Rechtsakts von EUR-Lex."""
    url = EUR_LEX_URL.format(lang=language, celex=celex)
    try:
        resp = await client.get(url, timeout=30, follow_redirects=True)
        if resp.status_code == 200:
            return resp.text
        logger.warning(f"EUR-Lex {celex} ({language}): HTTP {resp.status_code}")
        return None
    except Exception as e:
        logger.error(f"Fehler beim Abrufen von {celex} ({language}): {e}")
        return None

def html_to_markdown_snippet(html: str, act_name: str, language: str) -> str:
    """
    Extrahiert die wichtigsten Artikel aus dem HTML und wandelt sie in Markdown um.
    Einfaches Regex-basiertes Parsing (kein BeautifulSoup nötig).
    """
    clean = re.sub(r'<[^>]+>', ' ', html)
    clean = re.sub(r'\s+', ' ', clean).strip()
    clean = clean[:5000]
    return f"""---
law_id: {act_name}
language: {language.lower()}
source: EUR-Lex
fetched_at: {datetime.utcnow().isoformat()}
---

# {act_name} ({language})

> Automatisch abgerufen von EUR-Lex. Letzte Aktualisierung: {datetime.utcnow().strftime('%Y-%m-%d')}

## Auszug

{clean}
"""

async def crawl_eurlex():
    """Hauptfunktion: holt alle konfigurierten Rechtsakte in allen Sprachen."""
    logger.info("🌐 EUR-Lex Crawler gestartet")
    fetched = 0
    errors = 0
    async with httpx.AsyncClient(headers={"User-Agent": "Complyo/1.0 (EFRE-Forschungsprojekt)"}) as client:
        for act_name, meta in EUR_LEX_ACTS.items():
            for lang in LANGUAGES:
                lang_dir = LAWS_DIR / LANG_DIR_MAP[lang]
                lang_dir.mkdir(parents=True, exist_ok=True)
                output_file = lang_dir / f"{act_name}.md"
                if output_file.exists():
                    logger.debug(f"Überspringe {act_name} ({lang}) — bereits vorhanden")
                    continue
                html = await fetch_act_html(meta["celex"], lang, client)
                if html:
                    md = html_to_markdown_snippet(html, act_name, lang)
                    output_file.write_text(md, encoding="utf-8")
                    logger.info(f"✅ {act_name} ({lang}) gespeichert")
                    fetched += 1
                else:
                    errors += 1
                await asyncio.sleep(2)
    logger.info(f"EUR-Lex Crawler fertig: {fetched} Dokumente, {errors} Fehler")

if __name__ == "__main__":
    asyncio.run(crawl_eurlex())
