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
3. `ist_duenne_erklaerung`: eine Seite, die die Inhaltsschranke nicht besteht,
   sich aber in Titel oder H1 als Datenschutzerklaerung ausweist und lang genug
   ist, ist eine knappe Erklaerung und keine Nicht-Erklaerung. Gemessen am
   07.10.2026 an einer Kundenseite (Ingenieurbuero): eine Standardvorlage mit
   acht Abschnitten,
   Ueberschrift "Datenschutzerklaerung", rund 5.000 Zeichen, aber weniger als
   zwei der neun Merkmale der Schranke. Vorher las der Kunde dort kritisch
   (5.000 EUR) "Datenschutz-Link fuehrt zu keiner Datenschutzerklaerung", eine
   falsche Aussage.
"""
import re
from typing import Callable, List, Optional
from urllib.parse import urlparse

from bs4 import BeautifulSoup

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


# --- Knappe Erklaerung -----------------------------------------------------

# Ab dieser Laenge des Inhaltstextes (ohne Menue und Fusszeile, in Zeichen)
# gilt eine Seite mit passender Ueberschrift als knappe Erklaerung.
#
# Herleitung, keine Schaetzung: im Pruefstand vom 07.10.2026 (24 Kundenseiten,
# 19 mit lesbarer Datenschutzerklaerung) ist der kuerzeste Text, der die
# Schranke besteht, 2.182 Zeichen lang, der naechste 2.851. Die Schwelle liegt
# bei rund der Haelfte davon. Darunter ist eine Seite mit der Ueberschrift
# "Datenschutzerklaerung" ein Platzhalter oder ein Verweis, keine Erklaerung.
# Nur Datenschutz: beim Impressum zeigt der Bestand keinen Fall, die Schranke
# dort (Stichwort plus E-Mail oder PLZ) verlangt ohnehin nur wenig.
DUENN_MINDESTENS = {"datenschutz": 1000}

_TITEL_TRENNER = re.compile(r"\s+[|\u2013\u2014\u00b7\u2022:]\s+|\s+-\s+")
_KOPF_UND_FUSS = ["script", "style", "noscript", "template", "svg", "nav", "header", "footer"]


def seiten_ueberschriften(soup: BeautifulSoup) -> List[str]:
    """Alle H1 und der Anfang des Titels (vor dem Seitennamen)."""
    liste = [h.get_text(" ", strip=True) for h in soup.find_all("h1")]
    titel = soup.title.get_text(" ", strip=True) if soup.title else ""
    if titel:
        liste.append(_TITEL_TRENNER.split(titel)[0])
    return [t for t in liste if t]


def inhaltstext(html: str) -> str:
    """Der Fliesstext ohne Menue, Kopf- und Fusszeile."""
    suppe = BeautifulSoup(html or "", "html.parser")
    for tag in suppe(_KOPF_UND_FUSS):
        tag.decompose()
    return suppe.get_text(" ", strip=True)


def ist_duenne_erklaerung(html: str, art: str) -> bool:
    """Weist sich die Seite als Rechtsseite aus und ist sie lang genug?

    Beides ist Pflicht. Die Ueberschrift allein trifft auch einen Platzhalter
    ("Datenschutzerklaerung folgt"), die Laenge allein jede Kontakt- oder
    Behoerdenseite, die das Wort Datenschutz nennt. Die Ueberschrift prueft
    dieselbe Regel wie `finde_eingebetteten_text`: "Datenschutz-Einstellungen"
    (Cookie-Dialog) ist keine Erklaerung, "Datenschutz- und Transparenz-
    beauftragter" (Behoerde) ebenfalls nicht.
    """
    mindestens = DUENN_MINDESTENS.get(art)
    if not mindestens or not html:
        return False
    suppe = BeautifulSoup(html, "html.parser")
    muster = _ARTEN[art]["ueberschrift"]
    if not any(muster.search(t) for t in seiten_ueberschriften(suppe)):
        return False
    return len(inhaltstext(html)) >= mindestens
