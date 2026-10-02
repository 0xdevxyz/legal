"""
Rechtstext im Dokument und die Frage, ob ein Link zur Website gehoert.

Ergaenzt `rechtsseiten_links` (Attrappen, Inhaltsschranke) um zwei Faelle, die der
Pruefstand vom 02.10.2026 an konditorei-limbach.de und zahnarztpraxis-mittweida.de
gezeigt hat. Beide Seiten legen Impressum und Datenschutz als Overlay oder
Abschnitt in dieselbe Seite (`#impressumModal`, `#rechtliches`), geoeffnet ueber
Schaltflaechen. Es gibt keinen Link auf eine eigene Seite, aber der Text steht im
Dokument.

Ohne diese Ergaenzung machen die Attrappen-Regeln aus "kein Link" ein
"Kein Impressum-Link gefunden" samt sechs Folgebefunden, obwohl das Impressum auf
der Seite steht. Und der einzige Treffer fuer die Datenschutzerklaerung der
Konditorei war `https://www.datenschutz.sachsen.de`, die Landesbehoerde: deren
Startseite wurde als Erklaerung der Praxis analysiert, vier kritische Maengel,
darunter "Betroffenenrechte fehlen".

1. `fremder_host_ohne_klartext`: ein Link auf einen fremden Host kommt nur in
   Frage, wenn sein Text die Rechtsseite beim Namen nennt ("Datenschutzerklaerung").
   Gehostete Erklaerungen eines Generators bleiben moeglich; die Adresse
   "www.datenschutz.sachsen.de" als Linktext nennt keine Erklaerung.
2. `finde_eingebetteten_text`: steht der Text im Dokument, wird er gelesen,
   statt "keine Seite gefunden" zu melden.
"""
import re
from typing import Callable, Optional
from urllib.parse import urlparse

from .rechtsseiten_links import GeladeneRechtsseite

# Linktexte, die genau die gesuchte Rechtsseite benennen.
GENAUE_TEXTE = {
    "datenschutz", "datenschutzerklärung", "datenschutzerklaerung",
    "datenschutzhinweise", "datenschutzrichtlinie", "privacy", "privacy policy",
    "privacy notice", "impressum", "imprint", "legal notice",
    "anbieterkennzeichnung", "pflichtangaben",
}


def _host(adresse: str) -> str:
    netz = urlparse(adresse if "//" in adresse else "//" + adresse).netloc.lower()
    netz = netz.rsplit("@", 1)[-1].split(":")[0]
    return netz[4:] if netz.startswith("www.") else netz


def gleiche_website(href: str, basis_url: str) -> bool:
    """Gehoert der Verweis zur Website, die gerade geprueft wird?

    Relative Adressen sind es immer. Bei absoluten gilt Gleichheit oder
    Unterdomain in einer der beiden Richtungen: `datenschutz.beispiel.de` und
    `www.beispiel.de` gehoeren zusammen, `datenschutz.sachsen.de` und
    `konditorei-limbach.de` nicht. Ohne Public-Suffix-Liste bewusst einfach.
    """
    h = (href or "").strip()
    if not h.lower().startswith(("http://", "https://", "//")):
        return True
    ziel, basis = _host(h), _host(basis_url or "")
    if not ziel or not basis:
        return True
    return ziel == basis or ziel.endswith("." + basis) or basis.endswith("." + ziel)


def fremder_host_ohne_klartext(a_tag, basis_url: Optional[str]) -> bool:
    """Wahr, wenn der Link auf einen fremden Host zeigt und sein Text die
    Rechtsseite nicht beim Namen nennt. Ohne `basis_url` nie wahr."""
    if not basis_url or gleiche_website(a_tag.get("href") or "", basis_url):
        return False
    return a_tag.get_text(strip=True).lower() not in GENAUE_TEXTE


# --- Text im Dokument ------------------------------------------------------

_ARTEN = {
    "impressum": {
        "kennung": re.compile(r"impressum|imprint|legal[-_ ]?notice|rechtliches", re.I),
        "ueberschrift": re.compile(
            r"^\W*(impressum|imprint|legal notice|anbieterkennzeichnung|angaben gem)",
            re.I),
        "mindestens": 200,
    },
    "datenschutz": {
        "kennung": re.compile(r"datenschutz|privacy|dsgvo|rechtliches", re.I),
        # "Datenschutz-Einstellungen" (Cookie-Dialog) ist keine Erklaerung:
        # nacktes "Datenschutz" nur, wenn die Ueberschrift danach endet.
        "ueberschrift": re.compile(
            r"^\W*(datenschutzerkl|datenschutzhinweis|datenschutzinformation"
            r"|datenschutzrichtlinie|privacy policy|privacy notice"
            r"|datenschutz\W*$|datenschutz\s+(auf|bei|gem|nach)\b)",
            re.I),
        "mindestens": 600,
    },
}

_UEBERSPRINGEN = {"html", "head", "body", "script", "style", "a", "button",
                  "link", "meta", "noscript", "svg"}


def finde_eingebetteten_text(soup, art: str,
                             sieht_richtig_aus: Callable[[str], bool]) -> Optional[str]:
    """Liest Impressum oder Datenschutzerklaerung, die im Dokument selbst stehen.

    Gesucht wird ein Bereich, der sich nach der Rechtsseite nennt (id oder
    Klasse), eine Ueberschrift der Rechtsseite traegt, lang genug ist und dem
    Inhalt nach die Seite sein kann (`sieht_richtig_aus`, die Heuristik der
    Checks). Alle vier Bedingungen: eine Kennung allein trifft auch den
    Cookie-Dialog ("privacy-settings"), eine Ueberschrift allein jede Fusszeile
    mit dem Wort "Impressum".

    Die Ueberschrift darf irgendwo im Bereich stehen, nicht nur am Anfang. Bei
    einem Sammelbereich `#rechtliches` mit beiden Texten genuegt, dass eine der
    Ueberschriften passt; der Text des Bereichs ist dann der von beiden. Das ist
    unscharf, aber nie falsch-negativ.

    Bei mehreren Treffern gewinnt der kleinste Bereich. Ein Elternbereich, der
    beide Overlays umschliesst, wuerde sonst die Erklaerung als Impressum auslegen.
    """
    cfg = _ARTEN[art]
    beste: Optional[str] = None
    for el in soup.find_all(True):
        if el.name in _UEBERSPRINGEN:
            continue
        kennung = " ".join(filter(None, [
            el.get("id") or "",
            " ".join(el.get("class") or []),
        ]))
        if not cfg["kennung"].search(kennung):
            continue
        if not any(cfg["ueberschrift"].search(h.get_text(" ", strip=True))
                   for h in el.find_all(["h1", "h2", "h3", "h4"])):
            continue
        text = el.get_text(" ", strip=True)
        if len(text) < cfg["mindestens"] or not sieht_richtig_aus(text):
            continue
        if beste is None or len(text) < len(beste):
            beste = text
    return beste


def eingebettete_seite(url: str, text: str) -> GeladeneRechtsseite:
    """Der Text aus dem Dokument im selben Rahmen wie eine geladene Seite."""
    return GeladeneRechtsseite(url=url, html=text, status=200)
