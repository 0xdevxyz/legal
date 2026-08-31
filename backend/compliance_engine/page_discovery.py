"""
Findet die Unterseiten, auf denen die teuren Verstoesse sitzen.

Bis hierher prueft complyo nur die Startseite (plus Impressum/Datenschutz ueber
verfolgte Links). Die Widerrufsbelehrung steht aber auf /agb, das Formular ohne
Datenschutzhinweis auf /kontakt, der Bestellbutton im Checkout. Wettbewerber
scannen 50-100 Unterseiten je Durchlauf.

Dieses Modul beantwortet EINE Frage: welche Seiten lohnen die Pruefung? Nicht
alle — ein Blog mit 800 Artikeln bringt keinen zusaetzlichen Rechtsbefund, aber
800-mal Kosten. Priorisiert wird nach rechtlicher Relevanz:

  1. Pflichtseiten (Impressum, Datenschutz, AGB, Widerruf)   — immer
  2. Interaktionsseiten (Kontakt, Checkout, Warenkorb, Login) — fast immer
  3. Angebotsseiten (Produkt, Preise, Leistungen)             — wenn Platz
  4. Inhaltsseiten (Blog, News, Referenzen)                   — Stichprobe

Quellen in dieser Reihenfolge: sitemap.xml (autoritativ), interne Links der
Startseite, geratene Standardpfade (nur wenn sonst nichts gefunden wurde).
"""
import asyncio
import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from urllib.parse import urljoin, urlparse, urldefrag

from compliance_engine.sicherer_abruf import hole
from xml.etree import ElementTree as ET

import aiohttp
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------
# Relevanz-Klassen. Die Reihenfolge in PRIORITAETEN ist die Reihenfolge, in der
# gescannt wird — was nicht mehr ins Budget passt, faellt hinten weg.
# --------------------------------------------------------------------------
KLASSE_PFLICHT = "pflichtseite"
KLASSE_INTERAKTION = "interaktion"
KLASSE_ANGEBOT = "angebot"
KLASSE_INHALT = "inhalt"

# Muster auf dem PFAD (nicht dem ganzen Text) — mit Wortgrenzen, damit
# "/kontaktlinsen" nicht als Kontaktformular durchgeht.
PFAD_MUSTER: "List[tuple[str, str]]" = [
    # Pflichtseiten
    (KLASSE_PFLICHT, r"impressum|imprint|anbieterkennzeichnung|legal-notice"),
    (KLASSE_PFLICHT, r"datenschutz|privacy|dsgvo|gdpr"),
    (KLASSE_PFLICHT, r"agb|terms|geschaeftsbedingungen|nutzungsbedingungen|tos"),
    (KLASSE_PFLICHT, r"widerruf|widerrufsbelehrung|rueckgabe|retoure|cancellation"),
    (KLASSE_PFLICHT, r"barrierefreiheit|accessibility|erklaerung-zur-barrierefreiheit"),
    (KLASSE_PFLICHT, r"cookie|cookies|cookie-richtlinie|cookie-policy"),
    # Interaktion — hier sitzen Formulare und Bestellstrecken
    (KLASSE_INTERAKTION, r"kontakt|contact|anfrage|beratung"),
    (KLASSE_INTERAKTION, r"checkout|kasse|bestellung|order|warenkorb|cart|basket"),
    (KLASSE_INTERAKTION, r"registrier|anmeld|login|signup|konto|account|mein-"),
    (KLASSE_INTERAKTION, r"newsletter|abonnieren|subscribe"),
    (KLASSE_INTERAKTION, r"termin|booking|buchen|reservierung"),
    # Angebot — Preisangaben, Buttons, Produktinformationen
    (KLASSE_ANGEBOT, r"preis|pricing|tarif|kosten|paket"),
    (KLASSE_ANGEBOT, r"produkt|product|shop|artikel|leistung|service|angebot"),
    # Inhalt — nur als Stichprobe, selten rechtlich neu
    (KLASSE_INHALT, r"blog|news|magazin|artikel|ratgeber|referenz|projekt|ueber-uns|about|team"),
]

PRIORITAETEN = [KLASSE_PFLICHT, KLASSE_INTERAKTION, KLASSE_ANGEBOT, KLASSE_INHALT]

# Wieviele Seiten je Klasse hoechstens — verhindert, dass ein Shop mit 400
# Produktseiten das ganze Budget frisst und die Pflichtseiten verdraengt.
MAX_JE_KLASSE = {
    KLASSE_PFLICHT: 12,
    KLASSE_INTERAKTION: 8,
    KLASSE_ANGEBOT: 6,
    KLASSE_INHALT: 3,
}

# Standardpfade, die geraten werden, wenn Sitemap und Links nichts hergeben.
GERATENE_PFADE = [
    "/impressum", "/datenschutz", "/agb", "/widerruf", "/kontakt",
    "/impressum/", "/datenschutz/", "/agb/", "/kontakt/",
    "/barrierefreiheit", "/cookie-richtlinie",
]

# Dateiendungen, die keine HTML-Seiten sind
KEINE_SEITE = re.compile(
    r"\.(pdf|jpe?g|png|gif|webp|svg|ico|css|js|zip|rar|docx?|xlsx?|pptx?|mp[34]|avi|mov|woff2?|ttf|eot)(\?|$)",
    re.I,
)


@dataclass
class GefundeneSeite:
    """Eine Seite, die gescannt werden soll."""
    url: str
    klasse: str
    quelle: str          # "sitemap" | "link" | "geraten"
    titel: str = ""

    def __hash__(self):
        return hash(self.url)


@dataclass
class Entdeckung:
    """Ergebnis der Seitensuche."""
    startseite: str
    seiten: List[GefundeneSeite] = field(default_factory=list)
    sitemap_gefunden: bool = False
    gesamt_gesehen: int = 0
    hinweis: str = ""

    def nach_klasse(self) -> Dict[str, List[GefundeneSeite]]:
        gruppen: Dict[str, List[GefundeneSeite]] = {k: [] for k in PRIORITAETEN}
        for s in self.seiten:
            gruppen.setdefault(s.klasse, []).append(s)
        return gruppen


def _normalisiere(url: str, host_wie: Optional[str] = None) -> str:
    """
    Fragment weg, Trailing-Slash vereinheitlichen, Query behalten.

    `host_wie` vereinheitlicht zusaetzlich den Host auf die Schreibweise der
    Startseite. Sitemaps liefern gern `www.example.de`, die Links im HTML aber
    `example.de` — ohne diesen Abgleich wuerde dieselbe Seite zweimal gescannt.
    """
    url, _ = urldefrag(url)
    if url.endswith("/") and len(urlparse(url).path) > 1:
        url = url[:-1]
    if host_wie:
        teile = urlparse(url)
        ziel = urlparse(host_wie)
        if teile.netloc and ziel.netloc:
            kahl = teile.netloc[4:] if teile.netloc.lower().startswith("www.") else teile.netloc
            ziel_kahl = ziel.netloc[4:] if ziel.netloc.lower().startswith("www.") else ziel.netloc
            if kahl.lower() == ziel_kahl.lower():
                url = teile._replace(netloc=ziel.netloc, scheme=ziel.scheme).geturl()
    return url


def _gleiche_domain(a: str, b: str) -> bool:
    ha, hb = urlparse(a).netloc.lower(), urlparse(b).netloc.lower()
    ha = ha[4:] if ha.startswith("www.") else ha
    hb = hb[4:] if hb.startswith("www.") else hb
    return ha == hb


def klassifiziere(url: str) -> Optional[str]:
    """
    Ordnet eine URL einer Relevanzklasse zu — oder None, wenn sie nicht lohnt.

    Bewertet wird nur der PFAD. Ein Blogartikel ueber Datenschutz
    (/blog/datenschutz-tipps) ist keine Datenschutzerklaerung; deshalb gewinnt
    ein frueher Treffer in der Musterliste nur, wenn kein Inhalts-Praefix davor
    steht.
    """
    pfad = (urlparse(url).path or "/").lower()
    if pfad in ("", "/"):
        return None  # Startseite wird separat gescannt
    if KEINE_SEITE.search(pfad):
        return None

    # Inhalts-Praefix — auch in Bindestrich-Schreibweise. "/blog/dsgvo-tipps"
    # UND "/blog-dsgvo-2024" sind Artikel, keine Datenschutzerklaerung.
    inhalts_praefix = re.match(
        r"^/(blog|news|magazin|artikel|ratgeber|presse|wissen|lexikon|glossar)([-/]|$)", pfad
    )

    # Marketing-Landingpages tragen Rechtswoerter im Namen, sind aber keine
    # Pflichtseiten: "/dsgvo-website-check", "/barrierefreiheit-website-testen".
    # Auf ihnen die Vollstaendigkeit von Pflichtangaben zu pruefen, erzeugt
    # garantierte Fehlbefunde.
    marketing = re.search(
        r"(check|test(en)?|pruef|rechner|tool|tipps|guide|vergleich|beispiel|vorlage|"
        r"generator|kosten|preis[e]?-|\b20\d\d)", pfad
    )

    for klasse, muster in PFAD_MUSTER:
        if re.search(muster, pfad):
            if klasse == KLASSE_PFLICHT and (inhalts_praefix or marketing):
                return KLASSE_INHALT
            if inhalts_praefix and klasse != KLASSE_INHALT:
                return KLASSE_INHALT
            return klasse
    return None


async def _hole(session: aiohttp.ClientSession, url: str, timeout: int = 10) -> Optional[str]:
    """
    Holt eine Seite als Text, oder None.

    Über sicherer_abruf, weil hier fremdbestimmte Adressen landen: die
    `Sitemap:`-Zeile der robots.txt schreibt der Betreiber der geprüften Seite,
    und sie zeigte bis zum Sicherheitsreview 2026-08-31 ungeprüft überallhin.
    """
    abruf = await hole(session, url, timeout=timeout)
    if abruf is None or abruf.status != 200:
        return None
    if "html" not in abruf.content_type and "xml" not in abruf.content_type:
        return None
    return abruf.text()


async def _aus_sitemap(session: aiohttp.ClientSession, basis: str) -> "List[str]":
    """
    Liest sitemap.xml (auch Sitemap-Index). Autoritativste Quelle: hier steht,
    was der Betreiber selbst fuer seine Seiten haelt.
    """
    kandidaten = [urljoin(basis, p) for p in ("/sitemap.xml", "/sitemap_index.xml", "/sitemap-index.xml")]

    # robots.txt kann auf eine abweichende Sitemap zeigen
    robots = await _hole(session, urljoin(basis, "/robots.txt"), timeout=6)
    if robots:
        for zeile in robots.splitlines():
            if zeile.lower().startswith("sitemap:"):
                kandidaten.append(zeile.split(":", 1)[1].strip())

    urls: List[str] = []
    gesehen_sitemaps: Set[str] = set()

    async def lies(sm_url: str, tiefe: int = 0):
        if tiefe > 1 or sm_url in gesehen_sitemaps or len(urls) > 2000:
            return
        gesehen_sitemaps.add(sm_url)
        text = await _hole(session, sm_url, timeout=12)
        if not text:
            return
        try:
            wurzel = ET.fromstring(text.encode("utf-8", "replace"))
        except ET.ParseError:
            return
        tag = wurzel.tag.lower()
        if "sitemapindex" in tag:
            unter = [el.text.strip() for el in wurzel.iter() if el.tag.lower().endswith("loc") and el.text]
            for u in unter[:10]:
                await lies(u, tiefe + 1)
        else:
            for el in wurzel.iter():
                if el.tag.lower().endswith("loc") and el.text:
                    urls.append(el.text.strip())

    for k in kandidaten[:5]:
        await lies(k)
        if urls:
            break
    return urls


def _aus_links(html: str, basis: str) -> "List[tuple[str, str]]":
    """Interne Links der Startseite als (url, linktext)."""
    soup = BeautifulSoup(html, "html.parser")
    treffer = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith(("#", "mailto:", "tel:", "javascript:")):
            continue
        voll = _normalisiere(urljoin(basis, href), host_wie=basis)
        if not voll.startswith(("http://", "https://")) or not _gleiche_domain(voll, basis):
            continue
        treffer.append((voll, a.get_text(strip=True)[:80]))
    return treffer


async def entdecke_seiten(
    startseite: str,
    html: Optional[str] = None,
    session: Optional[aiohttp.ClientSession] = None,
    max_seiten: int = 20,
) -> Entdeckung:
    """
    Findet bis zu `max_seiten` pruefenswerte Unterseiten.

    Args:
        startseite: die bereits gescannte Startseite (wird NICHT mit zurueckgegeben)
        html:       deren HTML, falls schon geholt — spart einen Abruf
        session:    bestehende aiohttp-Session
        max_seiten: Budget; Pflichtseiten werden zuerst bedient

    Returns:
        Entdeckung mit priorisierter Seitenliste
    """
    startseite = _normalisiere(startseite)
    eigene_session = session is None
    if eigene_session:
        import ssl as _ssl
        import certifi
        ctx = _ssl.create_default_context(cafile=certifi.where())
        session = aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=ctx))

    ergebnis = Entdeckung(startseite=startseite)
    try:
        kandidaten: Dict[str, GefundeneSeite] = {}

        # --- 1. Sitemap (autoritativ)
        sitemap_urls = await _aus_sitemap(session, startseite)
        if sitemap_urls:
            ergebnis.sitemap_gefunden = True
        for u in sitemap_urls:
            u = _normalisiere(u, host_wie=startseite)
            if not _gleiche_domain(u, startseite) or u == startseite:
                continue
            klasse = klassifiziere(u)
            if klasse and u not in kandidaten:
                kandidaten[u] = GefundeneSeite(url=u, klasse=klasse, quelle="sitemap")

        # --- 2. Interne Links der Startseite
        if html is None:
            html = await _hole(session, startseite, timeout=12)
        if html:
            for u, text in _aus_links(html, startseite):
                if u == startseite:
                    continue
                klasse = klassifiziere(u)
                if klasse and u not in kandidaten:
                    kandidaten[u] = GefundeneSeite(url=u, klasse=klasse, quelle="link", titel=text)

        ergebnis.gesamt_gesehen = len(kandidaten)

        # --- 3. Standardpfade raten, wenn Pflichtseiten fehlen
        hat_pflicht = any(s.klasse == KLASSE_PFLICHT for s in kandidaten.values())
        if not hat_pflicht:
            pruefungen = [(_normalisiere(urljoin(startseite, p), host_wie=startseite), p)
                          for p in GERATENE_PFADE]
            treffer = await asyncio.gather(
                *[_hole(session, u, timeout=6) for u, _ in pruefungen],
                return_exceptions=True,
            )
            for (u, _), inhalt in zip(pruefungen, treffer):
                if isinstance(inhalt, str) and inhalt and u not in kandidaten:
                    klasse = klassifiziere(u)
                    if klasse:
                        kandidaten[u] = GefundeneSeite(url=u, klasse=klasse, quelle="geraten")

        # --- 4. Nach Relevanz auswaehlen
        gewaehlt: List[GefundeneSeite] = []
        for klasse in PRIORITAETEN:
            der_klasse = [s for s in kandidaten.values() if s.klasse == klasse]
            der_klasse.sort(key=lambda s: (s.quelle != "sitemap", len(s.url)))
            platz = min(MAX_JE_KLASSE.get(klasse, 5), max_seiten - len(gewaehlt))
            if platz <= 0:
                break
            gewaehlt.extend(der_klasse[:platz])

        ergebnis.seiten = gewaehlt[:max_seiten]

        uebrig = len(kandidaten) - len(ergebnis.seiten)
        if uebrig > 0:
            ergebnis.hinweis = (
                f"{uebrig} weitere relevante Seite(n) gefunden, aber nicht geprüft "
                f"(Budget: {max_seiten} Unterseiten)."
            )
        logger.info(
            f"Seitensuche {startseite}: {len(ergebnis.seiten)} von {len(kandidaten)} "
            f"Kandidaten gewählt (Sitemap: {ergebnis.sitemap_gefunden})"
        )
        return ergebnis
    finally:
        if eigene_session:
            await session.close()
