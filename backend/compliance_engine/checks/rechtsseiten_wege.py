"""
Weitere Wege zur Rechtsseite, wenn die Startseite keinen brauchbaren Link nennt.

Der Link-Finder liest, was die Startseite verlinkt. Fehlt dort ein Link (Menue aus
JavaScript, Impressum nur im Footer eines Unterbereichs, Verweis als Bild), blieb
bisher ein Satz Standardpfade. Der kannte `/impressum` und `/datenschutz`, aber
nicht `/impressum.html`, `/datenschutzerklaerung.html` oder `/rechtliches/...`,
also gerade die Formen, unter denen die Seiten der Bestandskunden liegen.

Dieses Modul probiert mehr, und zwar parallel, damit eine Seite ohne Rechtsseiten
nicht noch laenger braucht als vorher (sieben Abrufe nacheinander, je bis zu acht
Sekunden):

1. Standardpfade, jetzt auch mit Endung `.html`/`.php`, unter `/rechtliches/` und
   in den ueblichen Sprachvarianten.
2. Die `sitemap.xml` (und die der gaengigen WordPress-Plugins): Eintraege, deren
   Pfad nach der Rechtsseite heisst. Blogartikel und Werkzeuge ("impressum-
   generator", "datenschutz-check") scheiden aus, sonst traefe der Ratgeber ueber
   Impressumspflichten statt das Impressum.

Gilt als gefunden erst, was die Inhaltsschranke des jeweiligen Checks besteht: ein
Treffer mit HTTP 200 allein ist kein Nachweis (Catch-all-Domains liefern fuer jeden
Pfad dieselbe Seite).

Beides ist nur der Rueckfall fuer "kein Link gefunden"; findet der Link-Finder
etwas, wird hier nichts abgerufen.
"""
import asyncio
import html
import logging
import re
from typing import Awaitable, Callable, List, Optional, Tuple
from urllib.parse import urlparse

from .rechtsseiten_text import gleiche_website

logger = logging.getLogger(__name__)

Abruf = Callable[[str], Awaitable[Optional[Tuple[int, str]]]]

PFADE = {
    "impressum": [
        "/impressum", "/impressum/", "/impressum.html", "/impressum.php", "/imprint", "/imprint.html",
        "/legal-notice", "/legal", "/anbieterkennzeichnung", "/rechtliches", "/rechtliches/impressum",
        "/de/impressum", "/kontakt/impressum", "/ueber-uns/impressum", "/about/imprint",
        "/impressum-datenschutz", "/impressum-und-datenschutz",
    ],
    "datenschutz": [
        "/datenschutz", "/datenschutz/", "/datenschutz.html", "/datenschutz.php",
        "/datenschutzerklaerung", "/datenschutzerklaerung/", "/datenschutzerklaerung.html",
        "/datenschutzhinweise", "/datenschutz-erklaerung", "/privacy", "/privacy.html",
        "/privacy-policy", "/dsgvo", "/data-protection", "/de/datenschutz",
        "/rechtliches/datenschutz", "/impressum-datenschutz", "/impressum-und-datenschutz",
    ],
}

SITEMAPS = ("/sitemap.xml", "/sitemap_index.xml", "/wp-sitemap.xml")

WOERTER = {
    "impressum": ("impressum", "imprint", "legal-notice", "anbieterkennzeichnung", "rechtliches"),
    "datenschutz": ("datenschutz", "privacy", "dsgvo"),
}

# Pfadteile, die einen Artikel oder ein Werkzeug verraten statt der Rechtsseite.
AUSSCHLUSS = (
    "/blog", "/news", "/aktuelles", "/ratgeber", "/wissen", "/magazin", "/tag/", "/kategorie",
    "/category", "generator", "-check", "/check", "muster", "vorlage", "tool", "rechner",
    "/produkt", "/leistung", "/service", "/preis", "/portfolio", "/referenz",
)

_LOC = re.compile(r"<loc>\s*([^<]+?)\s*</loc>", re.I)


def sitemap_kandidaten(xml: str, basis_url: str, art: str, limit: int = 4) -> List[str]:
    """Adressen aus einer Sitemap, die nach der gesuchten Rechtsseite heissen."""
    treffer: List[str] = []
    for roh in _LOC.findall(xml or ""):
        adresse = html.unescape(roh).strip()
        if not gleiche_website(adresse, basis_url):
            continue
        pfad = urlparse(adresse).path.lower()
        if not pfad or pfad == "/":
            continue
        if not any(w in pfad for w in WOERTER[art]):
            continue
        if any(a in pfad for a in AUSSCHLUSS):
            continue
        if adresse not in treffer:
            treffer.append(adresse)
    # Kuerzere Pfade zuerst: "/impressum" vor "/rechtliches/impressum-angaben-2024".
    treffer.sort(key=lambda u: len(urlparse(u).path))
    return treffer[:limit]


def unter_sitemaps(xml: str, basis_url: str, limit: int = 2) -> List[str]:
    """Bei einem Sitemap-Index: die Teil-Sitemaps, in denen Seiten (nicht Beitraege) stehen."""
    if "<sitemapindex" not in (xml or "").lower():
        return []
    treffer = []
    for roh in _LOC.findall(xml):
        adresse = html.unescape(roh).strip()
        name = urlparse(adresse).path.lower()
        if gleiche_website(adresse, basis_url) and ("page" in name or "seite" in name):
            treffer.append(adresse)
    return treffer[:limit]


async def finde_rechtsseite(basis_url: str, art: str, hole: Abruf,
                            bewerte: Callable[[str], bool], parallel: int = 8) -> Optional[str]:
    """Sucht die Rechtsseite ohne Link: Standardpfade, dann Sitemap.

    `hole(url)` liefert `(Status, Text)` oder `None`; `bewerte(text)` ist die
    Inhaltsschranke des Checks. Gibt die gefundene Adresse zurueck, sonst `None`.
    """
    parsed = urlparse(basis_url)
    basis = f"{parsed.scheme}://{parsed.netloc}"
    sem = asyncio.Semaphore(parallel)

    async def abrufen(adresse: str):
        async with sem:
            return adresse, await hole(adresse)

    # Catch-all-Probe: ein Pfad, den es nie gibt. Liefert er 200, ist die Domain
    # ein Catch-all und dieselbe Seite fuer jeden Pfad kein Rechtstext.
    _, probe = await abrufen(basis + "/__complyo_probe_404__")
    catch_all = bool(probe and probe[0] == 200 and len(probe[1].strip()) > 200)
    if catch_all:
        logger.info("⚠️ Catch-all-Domain erkannt, Inhalt wird strikt geprueft")

    def gueltig(antwort) -> bool:
        if not antwort or antwort[0] != 200:
            return False
        if probe and probe[0] == 200 and antwort[1].strip() == probe[1].strip():
            return False
        return bewerte(antwort[1])

    pfade = [basis + p for p in PFADE[art]]
    ergebnisse = await asyncio.gather(*(abrufen(u) for u in pfade),
                                      *(abrufen(basis + s) for s in SITEMAPS))
    for adresse, antwort in ergebnisse[:len(pfade)]:
        if gueltig(antwort):
            logger.info(f"✅ {art}: Rechtsseite unter Standardpfad gefunden: {adresse}")
            return adresse

    kandidaten: List[str] = []
    for adresse, antwort in ergebnisse[len(pfade):]:
        if not antwort or antwort[0] != 200:
            continue
        kandidaten += sitemap_kandidaten(antwort[1], basis_url, art)
        for unter in unter_sitemaps(antwort[1], basis_url):
            _, a2 = await abrufen(unter)
            if a2 and a2[0] == 200:
                kandidaten += sitemap_kandidaten(a2[1], basis_url, art)
    bekannt = set(pfade)
    neu = []
    for k in kandidaten:
        if k not in bekannt and k not in neu:
            neu.append(k)
    if not neu:
        return None
    for adresse, antwort in await asyncio.gather(*(abrufen(u) for u in neu[:4])):
        if gueltig(antwort):
            logger.info(f"✅ {art}: Rechtsseite ueber die Sitemap gefunden: {adresse}")
            return adresse
    return None
