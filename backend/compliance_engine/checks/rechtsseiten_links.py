"""
Rechtsseiten-Links: welcher Link fuehrt wirklich zu einer Seite, und steht
auf dieser Seite auch der Rechtstext?

Zwei Fehler, die bis zum 02.10.2026 beide still durchliefen:

1. Ein Footer-Link "Impressum" mit href="mailto:info@firma.de" (oder
   javascript:void(0) fuer ein Modal, tel:, #) wurde als Impressumsseite
   gewaehlt. Der Abruf von "mailto:" wirft, die Deep-Analyse fing die
   Ausnahme und schwieg. Ergebnis: null Impressum-Befunde, die Seite galt
   als sauber, obwohl kein Besucher ein Impressum erreicht.

2. Fuehrte der Link zu einer echten Seite, wurde deren Inhalt nie
   angesehen, bevor er als Rechtstext geprueft wurde. Eine Kontaktseite,
   ein Impressum-Generator eines Drittanbieters oder die Startseite selbst
   (bei "#impressum" ohne passenden Abschnitt) landeten als "das Impressum"
   im Hybrid-Validator. Ohne KI hiess das "7 Angaben nicht abschliessend
   geprueft" (info, 0 EUR), mit KI fuenf kritische Befunde. Welches von
   beiden ein Kunde sah, hing am KI-Budget und nicht an seiner Website.

Die Inhaltsschranke (_looks_like_impressum / _looks_like_datenschutz) gab
es schon, sie galt aber nur fuer den Direkt-URL-Fallback ohne Link. Hier
gilt sie fuer jeden Kandidaten, bevor ein Pruefer ihn liest.
"""

import logging
from dataclasses import dataclass
from typing import Callable, Iterable, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

import aiohttp
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Schemata, hinter denen keine Seite steht. "data:" und "blob:" wuerden
# zwar etwas liefern, aber nichts, was ein Besucher als Rechtsseite findet.
_KEINE_SEITE = ("mailto:", "tel:", "sms:", "fax:", "callto:", "javascript:",
                "data:", "blob:")

ART_SEITE = "seite"
ART_ANKER = "anker"
ART_ATTRAPPE = "attrappe"


def seitenlink_art(href: Optional[str]) -> str:
    """
    seite:    fuehrt (relativ oder absolut) zu einer abrufbaren Adresse
    anker:    nur ein Fragment (#impressum), zeigt auf die aktuelle Seite
    attrappe: kein Ziel, das ein Browser als Seite laedt
    """
    wert = (href or "").strip()
    if not wert or wert == "#":
        return ART_ATTRAPPE
    unten = wert.lower()
    if unten.startswith(_KEINE_SEITE):
        return ART_ATTRAPPE
    if wert.startswith("#"):
        return ART_ANKER
    return ART_SEITE


def ist_seitenlink(href: Optional[str]) -> bool:
    """Wahr fuer Seite und Anker, falsch fuer Attrappen."""
    return seitenlink_art(href) != ART_ATTRAPPE


def attrappen(soup: BeautifulSoup, text_keywords: Iterable[str]) -> List[Tuple[str, str]]:
    """
    Links, die wie ein Rechtsseiten-Link beschriftet sind, aber zu keiner
    Seite fuehren: (href, Linktext). Fuer den Befundtext, damit der Kunde
    liest, WAS an seinem Footer falsch ist, nicht nur dass etwas fehlt.
    """
    woerter = [w.lower() for w in text_keywords]
    treffer = []
    for a_tag in soup.find_all("a", href=True):
        href = a_tag.get("href") or ""
        if seitenlink_art(href) != ART_ATTRAPPE:
            continue
        text = a_tag.get_text(strip=True).lower()
        beschriftung = " ".join(
            t for t in (text, (a_tag.get("aria-label") or "").lower(),
                        (a_tag.get("title") or "").lower()) if t
        )
        if any(w in beschriftung for w in woerter):
            treffer.append((href.strip(), a_tag.get_text(strip=True)))
    return treffer


def attrappen_satz(liste: List[Tuple[str, str]]) -> str:
    """Ein Satz fuer die Befundbeschreibung, leer wenn es keine Attrappen gibt."""
    if not liste:
        return ""
    href, text = liste[0]
    schema = href.split(":", 1)[0] + ":" if ":" in href else href
    return (f' Der Link "{text or href}" auf der Seite ist ein {schema}-Link '
            f'und führt zu keiner Seite.')


# Pfadbestandteile, die ein Werkzeug statt eines Rechtstexts verraten. Enger
# als _WERBEPFADE der Checks: "service" oder "wissen" kommen auch in echten
# Konzern-Impressen vor, "generator" nicht.
_WERKZEUGPFADE = ("generator", "rechner", "muster", "vorlage", "tool", "-check", "/check")


def ist_fremdes_werkzeug(basis_url: str, ziel_url: str) -> bool:
    """Fremder Host und ein Werkzeugpfad: das ist der Generator, nicht das Impressum."""
    basis_host = (urlparse(basis_url).hostname or "").lower().removeprefix("www.")
    ziel = urlparse(ziel_url)
    ziel_host = (ziel.hostname or "").lower().removeprefix("www.")
    if not ziel_host or ziel_host == basis_host or ziel_host.endswith("." + basis_host):
        return False
    pfad = (ziel.path or "").lower()
    return any(w in pfad for w in _WERKZEUGPFADE)


PROBLEM_KEIN_RECHTSTEXT = "kein_rechtstext"
PROBLEM_NICHT_ERREICHBAR = "nicht_erreichbar"
PROBLEM_NICHT_LADBAR = "nicht_ladbar"


@dataclass
class GeladeneRechtsseite:
    url: str
    html: Optional[str] = None
    problem: Optional[str] = None
    status: Optional[int] = None
    fehler: Optional[str] = None
    # Wahr, wenn die Seite die Inhaltsschranke NICHT bestanden hat, sich aber
    # selbst als Rechtsseite ausweist und lang genug ist (siehe
    # rechtsseiten_text.ist_duenne_erklaerung). Sie wird dann gelesen und
    # bewertet, der Befund sagt "knapp" statt "keine Erklaerung".
    duenn: bool = False

    @property
    def ok(self) -> bool:
        return self.problem is None and self.html is not None


def _fliesstext(html: str) -> str:
    from ..hybrid_validator import zu_fliesstext
    return zu_fliesstext(html)


async def _im_browser_nachladen(url: str, html: str) -> Optional[str]:
    """
    Zweiter Versuch fuer Seiten, deren Server-HTML leer ist (React, Vue,
    Next.js). Nur dann, nicht fuer jede Rechtsseite: ein Browserstart je
    Rechtstext waere der teuerste Teil des Scans.
    """
    try:
        from ..browser_renderer import detect_client_rendering, smart_fetch_html
    except Exception as e:  # Playwright fehlt (Tests, Werkzeuge)
        logger.info(f"Browser-Nachladen nicht verfuegbar: {e}")
        return None
    try:
        braucht_browser, grund = detect_client_rendering(html)
        if not braucht_browser:
            return None
        logger.info(f"Rechtsseite im Browser nachladen ({grund}): {url}")
        gerendert, _meta = await smart_fetch_html(url, html)
        return gerendert
    except Exception as e:
        logger.warning(f"Browser-Nachladen fehlgeschlagen fuer {url}: {e}")
        return None


async def lade_rechtsseite(
    basis_url: str,
    href: str,
    soup: BeautifulSoup,
    session: aiohttp.ClientSession,
    sieht_aus_wie: Callable[[str], bool],
    timeout_s: int = 10,
    duenn_aus_wie: Optional[Callable[[str], bool]] = None,
) -> GeladeneRechtsseite:
    """
    Holt die Rechtsseite hinter einem Link und prueft, ob dort der Rechtstext
    steht. Erst wenn das stimmt, darf ein Pruefer den Inhalt bewerten.

    Anker (#impressum) zeigen auf die Seite, die der Aufrufer schon in der
    Hand hat: kein Abruf, nur die Inhaltsschranke. Auf einem Einseiter mit
    Impressumsabschnitt ist das richtig; auf einer Seite ohne den Abschnitt
    ist der Anker eine Attrappe mit Umweg.

    `duenn_aus_wie` bekommt das rohe HTML und entscheidet, ob eine Seite, die
    die Inhaltsschranke nicht besteht, trotzdem eine knappe Erklaerung ist.
    Ohne die Funktion bleibt es bei "ganz oder gar nicht".
    """
    art = seitenlink_art(href)
    ziel = urljoin(basis_url, href)

    if art == ART_ATTRAPPE:
        return GeladeneRechtsseite(url=ziel, problem=PROBLEM_KEIN_RECHTSTEXT)

    if ist_fremdes_werkzeug(basis_url, ziel):
        # Ein Impressum-Generator eines Drittanbieters sieht wie ein Impressum
        # aus (Stichwort, E-Mail, PLZ), ist aber das Werkzeug, nicht das
        # Ergebnis. Nur fremde Hosts, nur eindeutige Werkzeugpfade.
        return GeladeneRechtsseite(url=ziel, problem=PROBLEM_KEIN_RECHTSTEXT)

    if art == ART_ANKER:
        html = str(soup)
        if sieht_aus_wie(_fliesstext(html)):
            return GeladeneRechtsseite(url=ziel, html=html)
        return GeladeneRechtsseite(url=ziel, problem=PROBLEM_KEIN_RECHTSTEXT)

    try:
        async with session.get(ziel, timeout=aiohttp.ClientTimeout(total=timeout_s),
                               allow_redirects=True) as antwort:
            status = antwort.status
            if status != 200:
                return GeladeneRechtsseite(url=ziel, status=status,
                                           problem=PROBLEM_NICHT_ERREICHBAR)
            html = await antwort.text()
    except Exception as e:
        return GeladeneRechtsseite(url=ziel, problem=PROBLEM_NICHT_LADBAR,
                                   fehler=f"{type(e).__name__}: {e}")

    if sieht_aus_wie(_fliesstext(html)):
        return GeladeneRechtsseite(url=ziel, html=html, status=200)

    gerendert = await _im_browser_nachladen(ziel, html)
    if gerendert and sieht_aus_wie(_fliesstext(gerendert)):
        return GeladeneRechtsseite(url=ziel, html=gerendert, status=200)

    if duenn_aus_wie:
        for kandidat in (html, gerendert):
            if kandidat and duenn_aus_wie(kandidat):
                logger.info(f"Rechtsseite ist knapp, wird trotzdem gelesen: {ziel}")
                return GeladeneRechtsseite(url=ziel, html=kandidat, status=200, duenn=True)

    logger.info(f"Rechtsseiten-Link fuehrt zu keinem Rechtstext: {ziel}")
    return GeladeneRechtsseite(url=ziel, status=200, problem=PROBLEM_KEIN_RECHTSTEXT)
