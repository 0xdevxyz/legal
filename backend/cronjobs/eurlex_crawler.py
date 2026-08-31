"""
AP4: EUR-Lex Korpus-Updater
Holt aktuelle Fassungen von EU-Rechtsakten und speichert sie als Markdown im knowledge/laws/-Verzeichnis.
Unterstützt: GDPR, DSA, AI Act, ePrivacy, NIS2, EAA in mind. 5 Sprachen.
Läuft monatlich (1. des Monats, 02:00 Uhr).

Bezugsquelle (Audit 2026-08): das Cellar der Publications Office
(publications.europa.eu/resource/celex/<CELEX>) liefert den Rechtsakt als
XHTML. Die alte HTML-Ansicht von eur-lex.europa.eu antwortet inzwischen
dauerhaft mit HTTP 202 (Dokument wird erst erzeugt) und wird nur noch als
Fallback versucht.

Ablage: ein Verzeichnis je Rechtsakt und Sprache mit EINER Datei je Artikel
(laws/de/AI_ACT/art-050.md) plus laws/de/AI_ACT/00-uebersicht.md. Grund: der
Retriever gibt den Dokumentkoerper als Treffer zurueck; eine
650.000-Zeichen-Datei pro Verordnung waere als RAG-Treffer unbrauchbar. Das
Verzeichnis haelt den Abruf ausserdem von laws/<sprache>/<AKT>.md fern, das von
Hand gepflegtes Stammwissen enthaelt und bisher ueberschrieben wurde.

Qualitaetsschranke: geschrieben wird nur, was wie Gesetzestext aussieht. Die
Vorgaengerversion schnitt die ersten 5.000 Zeichen des gestrippten HTML heraus
und legte damit monatelang den JavaScript-Kopf der EUR-Lex-Seite als
"Gesetzestext" ab, ohne dass es auffiel.
"""
import asyncio
import logging
import os
import re
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

LAWS_DIR = Path(
    os.getenv("KNOWLEDGE_VAULT_PATH", str(Path(__file__).parents[2] / "knowledge"))
) / "laws"
# Nach wie vielen Tagen ein zwischengespeicherter Rechtsakt neu geholt wird.
MAX_AGE_DAYS = int(os.getenv("EURLEX_MAX_AGE_DAYS", "30"))
# Mindestzahl erkannter Artikel, damit ein Abruf als brauchbar gilt.
MIN_ARTIKEL = 10
# Mindestlaenge des Artikeltexts in Zeichen.
MIN_ARTIKEL_LEN = 80

# Spuren von Seitengeruest statt Gesetzestext. Taucht eins davon auf, war der
# Abruf Schrott und die Bestandsdatei bleibt stehen.
GERUEST_SPUREN = (
    "localstorage", "getelementbyid", "datalayer", "function(",
    "cookie-consent", "javascript:",
)


def _needs_refresh(path: Path) -> bool:
    """True, wenn der Pfad fehlt oder aelter als MAX_AGE_DAYS ist."""
    try:
        age_days = (time.time() - path.stat().st_mtime) / 86400.0
        return age_days >= MAX_AGE_DAYS
    except OSError:
        return True


EUR_LEX_ACTS = {
    "GDPR":    {"celex": "32016R0679", "de_id": "DSGVO"},
    "NIS2":    {"celex": "32022L2555", "de_id": "NIS2"},
    "AI_ACT":  {"celex": "32024R1689", "de_id": "AI_ACT"},
    "DSA":     {"celex": "32022R2065", "de_id": "DSA"},
    "EAA":     {"celex": "32019L0882", "de_id": "BFSG"},
}

LANGUAGES = ["DE", "EN", "FR", "IT", "PL"]
LANG_DIR_MAP = {"DE": "de", "EN": "en", "FR": "fr", "IT": "it", "PL": "pl"}
# ISO-639-3, wie das Cellar es in Accept-Language erwartet.
CELLAR_LANG_MAP = {"DE": "deu", "EN": "eng", "FR": "fra", "IT": "ita", "PL": "pol"}

CELLAR_URL = "https://publications.europa.eu/resource/celex/{celex}"
EUR_LEX_URL = "https://eur-lex.europa.eu/legal-content/{lang}/TXT/HTML/?uri=CELEX:{celex}"
# Menschenlesbare Fundstelle fuer das Frontmatter.
EUR_LEX_PAGE = "https://eur-lex.europa.eu/legal-content/{lang}/TXT/?uri=CELEX:{celex}"


async def fetch_act_html(celex: str, language: str, client: httpx.AsyncClient) -> Optional[str]:
    """Holt den Rechtsakt als XHTML, zuerst aus dem Cellar, dann via EUR-Lex."""
    cellar = CELLAR_URL.format(celex=celex)
    headers = {
        "Accept": "application/xhtml+xml",
        "Accept-Language": CELLAR_LANG_MAP.get(language, "eng"),
    }
    try:
        resp = await client.get(cellar, headers=headers, timeout=60, follow_redirects=True)
        if resp.status_code == 200 and len(resp.text) > 10000:
            return resp.text
        logger.warning(f"Cellar {celex} ({language}): HTTP {resp.status_code}, {len(resp.text)} Zeichen")
    except Exception as e:
        logger.warning(f"Cellar-Abruf {celex} ({language}) fehlgeschlagen: {e}")

    url = EUR_LEX_URL.format(lang=language, celex=celex)
    try:
        resp = await client.get(url, timeout=60, follow_redirects=True)
        if resp.status_code == 200:
            return resp.text
        logger.warning(f"EUR-Lex {celex} ({language}): HTTP {resp.status_code}")
    except Exception as e:
        logger.error(f"Fehler beim Abrufen von {celex} ({language}): {e}")
    return None


# Der erste Artikel wird in einigen Sprachen ausgeschrieben statt beziffert
# ("Article premier" im franzoesischen Amtsblatt). Ohne diese Zuordnung fehlte
# Artikel 1 in jedem franzoesischen Rechtsakt.
ORDINAL_EINS = ("premier", "première", "primo", "prima", "pierwszy", "first")


def _artikel_nummer(text: str) -> Optional[str]:
    """'Artikel 50' / 'Article 50' / 'Articolo 50' -> '50' (auch '50a')."""
    roh = (text or "").strip()
    m = re.search(r"(\d+\s*[a-z]?)\s*$", roh, re.IGNORECASE)
    if m:
        return m.group(1).replace(" ", "")
    letztes = roh.lower().split()[-1] if roh.split() else ""
    return "1" if letztes in ORDINAL_EINS else None


def parse_artikel(html: str) -> List[Dict[str, str]]:
    """
    Zerlegt den Rechtsakt in seine Artikel.

    Das Cellar-XHTML klammert jeden Artikel in
    <div class="eli-subdivision" id="art_50"> mit der Nummer in p.oj-ti-art und
    der Ueberschrift in p.oj-sti-art. Erwaegungsgruende tragen diese Struktur
    nicht und fallen damit von selbst heraus.
    """
    soup = BeautifulSoup(html, "lxml")
    artikel: List[Dict[str, str]] = []

    for div in soup.find_all("div", class_="eli-subdivision"):
        div_id = div.get("id") or ""
        if not div_id.startswith("art_") or "." in div_id:
            continue
        ti = div.find("p", class_="oj-ti-art")
        if not ti:
            continue
        nummer = _artikel_nummer(ti.get_text(" ", strip=True))
        if not nummer:
            continue
        sti = div.find("p", class_="oj-sti-art")
        ueberschrift = sti.get_text(" ", strip=True) if sti else ""
        body = div.get_text("\n", strip=True)
        if len(body) < MIN_ARTIKEL_LEN:
            continue
        artikel.append({
            "nummer": nummer,
            "label": ti.get_text(" ", strip=True),
            "ueberschrift": ueberschrift,
            "text": body,
        })

    return artikel


def qualitaet_ok(artikel: List[Dict[str, str]]) -> Tuple[bool, str]:
    """Sieht das Ergebnis nach Gesetzestext aus? (ok, Begruendung)"""
    if len(artikel) < MIN_ARTIKEL:
        return False, f"nur {len(artikel)} Artikel erkannt (mindestens {MIN_ARTIKEL} erwartet)"
    probe = " ".join(a["text"] for a in artikel[:3]).lower()
    for spur in GERUEST_SPUREN:
        if spur in probe:
            return False, f"Seitengeruest statt Gesetzestext erkannt ('{spur}')"
    return True, "ok"


def _sortier_key(nummer: str) -> str:
    m = re.match(r"(\d+)([a-z]?)", nummer)
    return f"{int(m.group(1)):03d}{m.group(2)}" if m else nummer


def _yaml_escape(text: str) -> str:
    return (text or "").replace('"', "'").replace("\n", " ").strip()


def schreibe_artikel(
    act_name: str, language: str, celex: str, artikel: List[Dict[str, str]]
) -> int:
    """Legt je Artikel eine Markdown-Datei an und gibt deren Zahl zurueck."""
    lang_dir = LAWS_DIR / LANG_DIR_MAP[language]
    act_dir = lang_dir / act_name
    act_dir.mkdir(parents=True, exist_ok=True)
    quelle = EUR_LEX_PAGE.format(lang=language, celex=celex)
    stand = datetime.utcnow().isoformat()

    # Bestand aufraeumen, damit entfallene Artikel nicht als Karteileiche bleiben.
    for alt in act_dir.glob("art-*.md"):
        alt.unlink()

    for a in artikel:
        key = _sortier_key(a["nummer"])
        titel = f"{a['label']}: {a['ueberschrift']}" if a["ueberschrift"] else a["label"]
        md = (
            "---\n"
            f"law_id: {act_name}\n"
            f"language: {LANG_DIR_MAP[language]}\n"
            f"article: \"{a['nummer']}\"\n"
            f"title: \"{_yaml_escape(titel)}\"\n"
            f"celex: {celex}\n"
            f"law_areas: [{act_name}]\n"
            "source: EUR-Lex (Cellar)\n"
            f"source_url: {quelle}\n"
            f"fetched_at: {stand}\n"
            "---\n\n"
            f"# {titel}\n\n"
            f"{a['text']}\n"
        )
        (act_dir / f"art-{key}.md").write_text(md, encoding="utf-8")

    uebersicht = (
        "---\n"
        f"law_id: {act_name}\n"
        f"language: {LANG_DIR_MAP[language]}\n"
        f"title: \"{act_name} ({language})\"\n"
        f"celex: {celex}\n"
        f"law_areas: [{act_name}]\n"
        "source: EUR-Lex (Cellar)\n"
        f"source_url: {quelle}\n"
        f"fetched_at: {stand}\n"
        f"articles: {len(artikel)}\n"
        "---\n\n"
        f"# {act_name} ({language})\n\n"
        f"Volltext je Artikel unter `{LANG_DIR_MAP[language]}/{act_name}/`. "
        f"Stand: {datetime.utcnow().strftime('%Y-%m-%d')}, {len(artikel)} Artikel.\n\n"
        "## Artikeluebersicht\n\n"
        + "\n".join(
            f"- [[art-{_sortier_key(a['nummer'])}|{a['label']}"
            + (f": {a['ueberschrift']}" if a["ueberschrift"] else "")
            + "]]"
            for a in artikel
        )
        + "\n"
    )
    # Bewusst IN das Aktenverzeichnis: laws/<sprache>/<AKT>.md ist von Hand
    # gepflegtes Stammwissen. Die Vorgaengerversion schrieb ihren Abruf genau
    # dorthin und hat die kuratierten Zusammenfassungen ueberschrieben.
    (act_dir / "00-uebersicht.md").write_text(uebersicht, encoding="utf-8")
    return len(artikel)


async def crawl_eurlex():
    """Hauptfunktion: holt alle konfigurierten Rechtsakte in allen Sprachen."""
    logger.info("🌐 EUR-Lex Crawler gestartet")
    fetched = 0
    errors = 0
    verworfen = 0
    async with httpx.AsyncClient(headers={"User-Agent": "Complyo/1.0 (EFRE-Forschungsprojekt)"}) as client:
        for act_name, meta in EUR_LEX_ACTS.items():
            for lang in LANGUAGES:
                act_dir = LAWS_DIR / LANG_DIR_MAP[lang] / act_name
                if act_dir.exists() and not _needs_refresh(act_dir):
                    logger.debug(
                        f"Überspringe {act_name} ({lang}) — aktuell (< {MAX_AGE_DAYS}d)"
                    )
                    continue
                html = await fetch_act_html(meta["celex"], lang, client)
                if not html:
                    errors += 1
                    await asyncio.sleep(2)
                    continue

                artikel = parse_artikel(html)
                ok, grund = qualitaet_ok(artikel)
                if not ok:
                    # Bewusst NICHT schreiben: lieber der alte Stand als Muell,
                    # der unbemerkt als Gesetzestext durchgereicht wird.
                    logger.error(
                        f"❌ {act_name} ({lang}) verworfen: {grund} — Bestand bleibt unveraendert"
                    )
                    verworfen += 1
                    await asyncio.sleep(2)
                    continue

                n = schreibe_artikel(act_name, lang, meta["celex"], artikel)
                logger.info(f"✅ {act_name} ({lang}) gespeichert: {n} Artikel")
                fetched += 1
                await asyncio.sleep(2)
    logger.info(
        f"EUR-Lex Crawler fertig: {fetched} Rechtsakte, {verworfen} verworfen, {errors} Fehler"
    )
    return {"fetched": fetched, "verworfen": verworfen, "errors": errors}


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    asyncio.run(crawl_eurlex())
