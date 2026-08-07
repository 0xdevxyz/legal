"""
Beschriftungen fuer Links und Schaltflaechen ohne erkennbaren Namen.

Wo das herkommt
---------------
`link-name` ist im echten Bestand der zweithaeufigste Pflicht-Verstoss: 56
Fundstellen auf 13 von 24 deutschen KMU-Websites (Messung 06.08.2026), Schwere
"serious", WCAG 4.1.2 und 2.4.4. Fuer einen Screenreader-Nutzer ist so ein Link
schlicht "Link" — er erfaehrt nicht, wohin er fuehrt.

Warum aria-label hier richtig ist — und beim Linktext nicht
-----------------------------------------------------------
Fuer Links MIT sichtbarem, aber nichtssagendem Text ("hier klicken") waere ein
abweichendes `aria-label` ein Fehler: der sichtbare Text muss im zugaenglichen
Namen vorkommen (WCAG 2.5.3, Label in Name). Solche Faelle bleiben deshalb der
redaktionellen Arbeit vorbehalten.

Hier ist es umgekehrt. Diese Links haben **gar keinen** sichtbaren Text — ein
Icon, ein Bild, ein leerer Wrapper. Es gibt keinen sichtbaren Namen, mit dem
`aria-label` in Konflikt geraten koennte. Es ist die von WCAG vorgesehene
Loesung, nicht ein Umweg um sie herum.

Woher die Beschriftung kommt
----------------------------
Aus dem, was ohnehin dasteht — in dieser Reihenfolge, weil die frueheren
Quellen verlaesslicher sind als die spaeteren:

  1. `title` am Element                     (der Betreiber hat es hingeschrieben)
  2. Alt-Text eines enthaltenen Bildes      (auch der von complyo erzeugte)
  3. Titel der Zielseite aus dem Scan       (exakt, wenn die Seite bekannt ist)
  4. Bekannte Muster: Social, tel:, mailto:, Suche, Schliessen, Nach oben
  5. Der URL-Slug                           (Notnagel, niedrige Konfidenz)

Was sich nicht ableiten laesst, wird nicht erfunden — `href="#"` ohne jeden
Hinweis bekommt keinen Vorschlag, sondern bleibt liegen. Ein falscher
Linkname ist schlimmer als ein fehlender: der Nutzer folgt ihm.
"""
import logging
import posixpath
import re
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import unquote, urlparse

logger = logging.getLogger(__name__)

_TITLE_ATTR = re.compile(r"""(?<![\w-])title\s*=\s*(?:"([^"]*)"|'([^']*)')""", re.I)
_ALT_ATTR = re.compile(r"""(?<![\w-])alt\s*=\s*(?:"([^"]*)"|'([^']*)')""", re.I)
_HREF_ATTR = re.compile(r"""(?<![\w-])href\s*=\s*(?:"([^"]*)"|'([^']*)')""", re.I)
_KLASSEN = re.compile(r"""(?<![\w-])class\s*=\s*(?:"([^"]*)"|'([^']*)')""", re.I)
_ID_ATTR = re.compile(r"""(?<![\w-])id\s*=\s*(?:"([^"]*)"|'([^']*)')""", re.I)
_VALUE_ATTR = re.compile(r"""(?<![\w-])value\s*=\s*(?:"([^"]*)"|'([^']*)')""", re.I)

_BILD_ENDUNG = (".jpg", ".jpeg", ".png", ".gif", ".webp", ".avif", ".svg", ".bmp")
_DOKUMENT_ENDUNG = {".pdf": "PDF", ".doc": "Word-Dokument", ".docx": "Word-Dokument",
                    ".xls": "Excel-Datei", ".xlsx": "Excel-Datei", ".zip": "ZIP-Archiv"}

# Plattformen nach Domain. Der Name allein genuegt: "Facebook" sagt einem
# Screenreader-Nutzer alles, was der Icon-Link einem Sehenden sagt.
_PLATTFORMEN = {
    "facebook.com": "Facebook", "fb.com": "Facebook", "instagram.com": "Instagram",
    "twitter.com": "Twitter", "x.com": "X", "linkedin.com": "LinkedIn",
    "youtube.com": "YouTube", "youtu.be": "YouTube", "tiktok.com": "TikTok",
    "pinterest.com": "Pinterest", "pinterest.de": "Pinterest", "xing.com": "Xing",
    "whatsapp.com": "WhatsApp", "wa.me": "WhatsApp", "t.me": "Telegram",
    "threads.net": "Threads", "vimeo.com": "Vimeo", "flickr.com": "Flickr",
    "spotify.com": "Spotify", "github.com": "GitHub", "mastodon.social": "Mastodon",
    "tripadvisor.de": "Tripadvisor", "yelp.de": "Yelp", "google.com": "Google",
}

# Muster in Klassen und IDs. Reihenfolge zaehlt: das erste Muster gewinnt,
# deshalb stehen spezifische vor allgemeinen ("close-mobile-menu" vor "menu").
_MUSTER: List[Tuple[str, str]] = [
    (r"back[-_]?to[-_]?top|scroll[-_]?(to[-_]?)?top|totop", "Nach oben"),
    (r"close[-_]?mobile[-_]?menu|mobile[-_]?menu[-_]?close", "Menü schließen"),
    (r"(^|[-_ ])close([-_ ]|$)|fa-times|fa-close|icon-close|dialog[-_]?close", "Schließen"),
    (r"search|suche|glyphicon-search|fa-search", "Suchen"),
    (r"hamburger|menu[-_]?toggle|toggle[-_]?menu|nav[-_]?toggle|burger", "Menü öffnen"),
    (r"popup[:%]?open|action.*popup|lightbox[-_]?open", "Dialog öffnen"),
    (r"prev(ious)?|zurueck|zurück|arrow[-_]?left|slick-prev|swiper-button-prev", "Zurück"),
    (r"next|weiter|arrow[-_]?right|slick-next|swiper-button-next", "Weiter"),
    (r"play[-_]?(button|video)|fa-play", "Video abspielen"),
    (r"cart|warenkorb", "Warenkorb"),
    (r"print|drucken", "Drucken"),
]

# Woerter, die in einem aus dem Slug gebauten Titel klein bleiben.
_KLEIN = {
    "der", "die", "das", "des", "dem", "den", "ein", "eine", "einen", "einem",
    "und", "oder", "aber", "im", "in", "am", "an", "auf", "aus", "bei", "für",
    "fuer", "mit", "nach", "von", "vom", "zu", "zum", "zur", "über", "ueber",
    "unter", "vor", "als", "wie", "ist", "sind", "wir", "uns", "unser",
}


def _attribut(muster: re.Pattern, html: str) -> str:
    m = muster.search(html or "")
    if not m:
        return ""
    return (m.group(1) or m.group(2) or "").strip()


def slug_zu_text(slug: str) -> str:
    """
    `starke-aufholjagd-des-fv-wolkenburg` -> `Starke Aufholjagd des FV Wolkenburg`

    Bewusst zurueckhaltend: Bindestriche werden zu Leerzeichen, das erste Wort
    und alles, was kein bekanntes Fuellwort ist, bekommt einen Grossbuchstaben,
    und kurze reine Konsonantenfolgen (FV, SV, TC) gelten als Abkuerzung. Das
    trifft nicht jeden Fall perfekt — deshalb steht diese Quelle ganz hinten
    und ihre Vorschlaege gehen mit niedriger Konfidenz in die Freigabe.
    """
    text = unquote(slug or "").replace("_", "-").replace("-", " ")
    text = re.sub(r"\.\w{2,5}$", "", text)      # Dateiendung
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return ""

    woerter = []
    for i, wort in enumerate(text.split(" ")):
        klein = wort.lower()
        if len(wort) <= 3 and wort.isalpha() and not re.search(r"[aeiouäöü]", klein):
            woerter.append(wort.upper())         # FV, SV, TC, GmbH-artig
        elif i > 0 and klein in _KLEIN:
            woerter.append(klein)
        else:
            woerter.append(klein[:1].upper() + klein[1:])
    return " ".join(woerter)


def _muster_beschriftung(html: str, href: str = "") -> Optional[Dict[str, Any]]:
    """Bekannte Rollen aus Klasse, ID und Ziel — fuer Links wie Schaltflaechen."""
    kennung = (
        f"{_attribut(_KLASSEN, html)} {_attribut(_ID_ATTR, html)} {unquote(href)}"
    ).lower()
    for muster, label in _MUSTER:
        if re.search(muster, kennung):
            return {"label": label, "quelle": "Muster", "konfidenz": 0.85}
    return None


def _bild_alt_im_link(html: str, alt_texte: Optional[Dict[str, str]]) -> str:
    """Alt-Text eines enthaltenen Bildes — auch der von complyo erzeugte."""
    for bild in re.findall(r"<img\b[^>]*>", html or "", re.I):
        vorhanden = _attribut(_ALT_ATTR, bild)
        if vorhanden:
            return vorhanden
        if alt_texte:
            quelle = _attribut(_HREF_ATTR, bild) or ""
            m = re.search(r"""(?<![\w-])src\s*=\s*(?:"([^"]*)"|'([^']*)')""", bild, re.I)
            if m:
                quelle = m.group(1) or m.group(2) or ""
            name = posixpath.basename(urlparse(quelle).path).lower()
            if name and name in alt_texte:
                return alt_texte[name]
    return ""


def beschriftung_fuer(
    html: str,
    seiten_titel: Optional[Dict[str, str]] = None,
    alt_texte: Optional[Dict[str, str]] = None,
) -> Optional[Dict[str, Any]]:
    """
    Leitet eine Beschriftung fuer ein Element ohne zugaenglichen Namen ab.

    Args:
        html: aeusseres HTML des Elements (aus dem axe-Befund).
        seiten_titel: {url_oder_pfad: <title>} aus dem Scan — die genaueste Quelle.
        alt_texte: {bilddateiname: alt} aus dem Fix-Manifest.

    Returns:
        {"label", "quelle", "konfidenz"} oder None, wenn nichts Belastbares
        abzuleiten ist. None ist ein gueltiges Ergebnis: ein erfundener
        Linkname ist schlimmer als ein fehlender.
    """
    if not html:
        return None

    # 1. Was der Betreiber selbst hingeschrieben hat.
    titel = _attribut(_TITLE_ATTR, html)
    if titel:
        return {"label": titel, "quelle": "title-Attribut", "konfidenz": 0.95}

    # 2. Bild im Link — oder ein Bild ALS Ziel.
    href = _attribut(_HREF_ATTR, html)
    alt = _bild_alt_im_link(html, alt_texte)
    pfad = urlparse(href).path.lower() if href else ""
    ist_bilddatei = pfad.endswith(_BILD_ENDUNG)

    # Lightbox-Links zeigen direkt auf die Bilddatei und enthalten oft gar kein
    # <img> (das Vorschaubild steckt im Hintergrund-CSS). Der Dateiname ist
    # trotzdem der Schluessel ins Alt-Text-Manifest — genau diese Bilder hat
    # complyo beschrieben. Auf spedition-mahn.de sind das 12 von 56 Fundstellen.
    if not alt and ist_bilddatei and alt_texte:
        alt = alt_texte.get(posixpath.basename(pfad), "")

    if alt:
        if ist_bilddatei:
            return {"label": f"Bild vergrößern: {alt}", "quelle": "Alt-Text",
                    "konfidenz": 0.9}
        return {"label": alt, "quelle": "Alt-Text", "konfidenz": 0.9}

    if not href:
        # Schaltflaechen haben kein href, aber dieselben sprechenden Klassen.
        # `<button class="gensearch__submit glyphicon-search">` ist eindeutig
        # eine Suche — vor dieser Zeile fiel genau der Fall durchs Raster.
        muster_treffer = _muster_beschriftung(html)
        if muster_treffer:
            return muster_treffer
        wert = _attribut(_VALUE_ATTR, html)
        if wert and wert.lower() not in ("go", "ok", "submit", "senden", ""):
            return {"label": wert, "quelle": "value-Attribut", "konfidenz": 0.7}
        return None

    # 3. Dokument- und Bildziele ohne Alt-Text.
    endung = posixpath.splitext(pfad)[1]
    if endung in _DOKUMENT_ENDUNG:
        name = slug_zu_text(posixpath.basename(pfad))
        art = _DOKUMENT_ENDUNG[endung]
        return {"label": f"{name} ({art})" if name else f"{art} öffnen",
                "quelle": "Dateiname", "konfidenz": 0.8}
    if ist_bilddatei:
        name = slug_zu_text(posixpath.basename(pfad))
        return {"label": f"Bild vergrößern: {name}" if name else "Bild vergrößern",
                "quelle": "Dateiname", "konfidenz": 0.6}

    # 4. Bekannte Ziele.
    if href.lower().startswith("tel:"):
        return {"label": f"Anrufen: {unquote(href[4:]).strip()}",
                "quelle": "tel-Link", "konfidenz": 0.95}
    if href.lower().startswith("mailto:"):
        adresse = unquote(href[7:]).split("?")[0].strip()
        return {"label": f"E-Mail schreiben an {adresse}",
                "quelle": "mailto-Link", "konfidenz": 0.95}

    host = (urlparse(href).netloc or "").lower().removeprefix("www.")
    for domain, name in _PLATTFORMEN.items():
        if host == domain or host.endswith("." + domain):
            return {"label": f"{name} (öffnet in neuem Fenster)"
                             if 'target="_blank"' in html.lower() else name,
                    "quelle": "Plattform", "konfidenz": 0.9}

    # 5. Muster in Klasse, ID und Ziel.
    treffer = _muster_beschriftung(html, href)
    if treffer:
        return treffer

    # 6. Titel der Zielseite aus dem Scan.
    if seiten_titel:
        for schluessel in (href, urlparse(href).path, urlparse(href).path.rstrip("/")):
            if schluessel and schluessel in seiten_titel:
                return {"label": seiten_titel[schluessel], "quelle": "Seitentitel",
                        "konfidenz": 0.9}

    # 7. Startseite. `href="#"` faellt hier bewusst NICHT hinein: der Pfad ist
    #    leer und der Fragmentbezeichner ebenfalls, das Ziel ist aber die
    #    aktuelle Seite und nicht die Startseite. Ein solcher Link ist ohne
    #    weiteren Hinweis nicht zu beschriften.
    if href.strip().startswith("#") or href.strip().lower().startswith("javascript:"):
        return None
    if pfad in ("", "/"):
        return {"label": "Startseite", "quelle": "Ziel ist die Startseite",
                "konfidenz": 0.8}

    # 8. Notnagel: der Slug.
    letzter = posixpath.basename(pfad.rstrip("/"))
    text = slug_zu_text(letzter)
    if text and len(text) >= 3:
        return {"label": text, "quelle": "URL", "konfidenz": 0.5}

    return None


def baue_linkname_vorschlaege(
    nodes: List[Dict[str, Any]],
    seiten_titel: Optional[Dict[str, str]] = None,
    alt_texte: Optional[Dict[str, str]] = None,
) -> List[Dict[str, Any]]:
    """
    Aus axe-Fundstellen (`link-name`, `button-name`) werden Vorschlaege.

    Gleiche Beschriftung am gleichen Ziel wird zusammengefasst — die zwoelf
    Lightbox-Links auf spedition-mahn.de sind vier Bilder, nicht zwoelf
    Entscheidungen.
    """
    gruppen: Dict[Tuple[str, str], Dict[str, Any]] = {}
    ohne_vorschlag = 0

    for node in nodes:
        html = node.get("html") or ""
        vorschlag = beschriftung_fuer(html, seiten_titel, alt_texte)
        if not vorschlag:
            ohne_vorschlag += 1
            continue
        href = _attribut(_HREF_ATTR, html)
        schluessel = (vorschlag["label"], href)
        eintrag = gruppen.setdefault(schluessel, {
            "label": vorschlag["label"],
            "quelle": vorschlag["quelle"],
            "konfidenz": vorschlag["konfidenz"],
            "href": href,
            "stellen": 0,
            "selektoren": [],
            "beispiel_html": html[:200],
        })
        eintrag["stellen"] += 1
        ziele = node.get("target") or []
        if ziele and len(eintrag["selektoren"]) < 50:
            eintrag["selektoren"].append(ziele[0])

    ergebnis = sorted(gruppen.values(), key=lambda e: (-e["konfidenz"], -e["stellen"]))
    if ohne_vorschlag:
        logger.info(
            f"Linkname: {len(ergebnis)} Vorschlaege, {ohne_vorschlag} Fundstelle(n) "
            f"ohne ableitbare Beschriftung — bleiben liegen statt geraten zu werden"
        )
    return ergebnis
