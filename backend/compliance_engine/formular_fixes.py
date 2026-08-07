"""
Formularfelder, Seitentitel und ARIA-Elternrollen — die letzten mechanisch
lösbaren Pflicht-Verstöße aus der Bestandsmessung.

Was übrig war
-------------
Nach Kontrast, Link-Namen und Struktur blieben aus den 24 gemessenen Seiten:

    label                  5   Pflicht (1.3.1 / 4.1.2)
    select-name            3   Pflicht (4.1.2)
    aria-required-parent   3   Pflicht (1.3.1)
    document-title         2   Pflicht (2.4.2)

Bei allen vieren galt zunächst "braucht ein Urteil". Der Blick auf die echten
Fundstellen hat das für drei davon widerlegt — und beim vierten einen Fall
zutage gefördert, der überhaupt kein Label braucht.

Der Honeypot
------------
Eine der fünf `label`-Fundstellen ist `<input name="spamify_hp_5147404f"
tabindex="-1" autocomplete="off">` — ein Spam-Köder. Er ist absichtlich
unsichtbar und soll von Menschen nie ausgefüllt werden. Ihm ein Label zu geben
wäre die formal richtige und praktisch falsche Antwort: der Screenreader würde
ein Feld ansagen, das niemand ausfüllen darf. Richtig ist `aria-hidden="true"`
plus `tabindex="-1"` — dann ist er für alle gleich unsichtbar.

Genau solche Fälle sind der Grund, warum "axe meldet 5 Verstöße, wir beheben 5"
die falsche Zielgröße ist. Einer davon war nie ein Verstoß gegen einen Nutzer,
sondern gegen eine Regel.

Warum `aria-required-parent` hier NICHT behoben wird
---------------------------------------------------
Die Annahme war: `role="tab"` fehlt ein Vorfahre mit `role="tablist"`, also
trägt man den nach — ein reines Attribut. Die Messung an spedition-mahn.de hat
sie widerlegt. Die tatsächliche Struktur ist

    <ul role="tablist"> <li role="tab"> <h3 role="tab"> …

Der `tablist` ist da. Der Fehler ist die **doppelt vergebene** Rolle am `<h3>`
innerhalb eines `<li>`, das bereits Reiter ist. Die Reparatur wäre ein
Entfernen, kein Setzen — und ein entferntes `role="tab"` kann die Skripte des
Themes brechen, die genau danach suchen. Also bleibt es liegen; drei
Fundstellen über 24 Seiten sind den Schaden nicht wert.

Der Weg dahin ist der Grund, warum in diesem Modul gemessen und nicht
angenommen wird: die naheliegende Erklärung war plausibel, verbreitet — und
falsch.
"""
import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Feldnamen, die aus sich heraus sprechen. Die Liste kommt aus den echten
# Fundstellen plus den üblichen Verdächtigen deutscher Kontaktformulare.
_FELDNAMEN = {
    "s": "Suche", "q": "Suche", "search": "Suche", "suche": "Suche",
    "name": "Name", "vorname": "Vorname", "nachname": "Nachname",
    "email": "E-Mail-Adresse", "mail": "E-Mail-Adresse", "e-mail": "E-Mail-Adresse",
    "telefon": "Telefonnummer", "phone": "Telefonnummer", "tel": "Telefonnummer",
    "nachricht": "Nachricht", "message": "Nachricht", "betreff": "Betreff",
    "subject": "Betreff", "firma": "Firma", "company": "Firma",
    "strasse": "Straße", "plz": "Postleitzahl", "ort": "Ort", "stadt": "Stadt",
    "anlass": "Anlass", "datum": "Datum", "uhrzeit": "Uhrzeit",
    "personen": "Anzahl Personen", "anzahl": "Anzahl",
}

# Eingabetypen sagen oft mehr als der Name.
_TYPEN = {
    "email": "E-Mail-Adresse", "tel": "Telefonnummer", "url": "Web-Adresse",
    "date": "Datum", "time": "Uhrzeit", "number": "Zahl", "search": "Suche",
    "password": "Passwort",
}

# Ein Honeypot ist ein Koeder gegen Spam-Roboter, kein Bedienelement.
_HONEYPOT = re.compile(
    r"(^|[-_])(hp|honeypot|honey_pot|spam[-_]?trap|nospam|leave[-_]?blank|"
    r"comment[-_]?url|url_check)([-_]|\d|$)", re.I
)


def ist_honeypot(name: str, klassen: str = "", tabindex: str = "") -> bool:
    """Ein Feld, das absichtlich niemand ausfuellen soll."""
    if _HONEYPOT.search(name or "") or _HONEYPOT.search(klassen or ""):
        return True
    # Ein Feld, das aus der Tabreihenfolge genommen wurde UND keinen
    # sprechenden Namen hat, ist mit hoher Wahrscheinlichkeit ein Koeder.
    return str(tabindex).strip() == "-1" and not _bezeichnung_aus_name(name)


def _bezeichnung_aus_name(name: str) -> Optional[str]:
    """`anlass` -> `Anlass`, `field1` -> None."""
    if not name:
        return None
    sauber = re.sub(r"\[\]$", "", name.strip()).lower()
    if sauber in _FELDNAMEN:
        return _FELDNAMEN[sauber]
    # Zusammengesetzte Namen: `kontakt-email`, `form_telefon`
    for teil in re.split(r"[-_\s.]+", sauber):
        if teil in _FELDNAMEN:
            return _FELDNAMEN[teil]
    return None


_ATTRIBUT_HINWEISE = [
    (r"hour|stunde", "Stunden"), (r"minute", "Minuten"), (r"second|sekunde", "Sekunden"),
    (r"day|tag(?!e?sz)", "Tag"), (r"month|monat", "Monat"), (r"year|jahr", "Jahr"),
    (r"guest|gast|person", "Anzahl Personen"), (r"room|zimmer", "Zimmer"),
    (r"quantity|menge", "Menge"), (r"price|preis", "Preis"),
]


def _bezeichnung_aus_attributnamen(namen) -> Optional[str]:
    """`update-hours` -> `Stunden`. Der Zweck steht im Attributnamen."""
    zusammen = " ".join(str(n) for n in namen).lower()
    for muster, label in _ATTRIBUT_HINWEISE:
        if re.search(muster, zusammen):
            return label
    return None


def beschriftung_fuer_feld(attribute: Dict[str, str],
                           umgebungstext: str = "") -> Optional[Dict[str, Any]]:
    """
    Leitet eine Feldbeschriftung ab — oder gibt None zurück.

    Reihenfolge nach Verlaesslichkeit: was der Betreiber selbst hingeschrieben
    hat (placeholder, title, aria-label eines Nachbarn), dann der Eingabetyp,
    dann der Feldname, zuletzt der Text davor im Formular.

    Args:
        attribute: name, type, placeholder, title, value, data-val-type, class,
                   tabindex — so wie im Markup.
        umgebungstext: sichtbarer Text unmittelbar vor dem Feld (aus dem Browser).

    Returns:
        {"label", "quelle", "konfidenz"} oder None. `None` ist ein Ergebnis:
        ein falsch benanntes Feld schickt Nutzer in die Irre.
    """
    hole = lambda k: (attribute.get(k) or "").strip()  # noqa: E731

    if ist_honeypot(hole("name"), hole("class"), hole("tabindex")):
        return {"label": None, "quelle": "Honeypot", "konfidenz": 0.95,
                "honeypot": True}

    platzhalter = hole("placeholder")
    if platzhalter:
        return {"label": platzhalter, "quelle": "placeholder", "konfidenz": 0.9}

    titel = hole("title")
    if titel:
        return {"label": titel, "quelle": "title-Attribut", "konfidenz": 0.9}

    # `value="Enter Keyword"` als Platzhalter-Ersatz — alte Themes machen das.
    wert = hole("value")
    if wert and len(wert) > 3 and not wert.isdigit():
        return {"label": wert, "quelle": "Vorbelegung", "konfidenz": 0.7}

    typ = (hole("data-val-type") or hole("type")).lower()
    if typ in _TYPEN:
        return {"label": _TYPEN[typ], "quelle": "Eingabetyp", "konfidenz": 0.85}

    aus_name = _bezeichnung_aus_name(hole("name"))
    if aus_name:
        return {"label": aus_name, "quelle": "Feldname", "konfidenz": 0.8}

    # Eigene Attribute verraten die Bedeutung oft deutlicher als der Name.
    # Auf rhino.cafe steht `<select update-hours hrs-min="0" hrs-max="24">` —
    # ohne name, ohne Label, aber der Zweck steht im Attributnamen.
    aus_attribut = _bezeichnung_aus_attributnamen(attribute.keys())
    if aus_attribut:
        return {"label": aus_attribut, "quelle": "Eigenes Attribut",
                "konfidenz": 0.75}

    text = re.sub(r"\s+", " ", umgebungstext or "").strip(" \t\n:*")
    if 2 < len(text) <= 60:
        return {"label": text, "quelle": "Text davor", "konfidenz": 0.6}

    return None




# =============================================================================
# Browser-Logik
# =============================================================================

FORMULARFELDER_JS = r"""
() => {
  // Attribute und Umgebungstext der bemängelten Felder einsammeln. Der Text
  // davor lässt sich nur am gerenderten Baum bestimmen.
  const sel = window.__complyoFeldSelektoren || [];
  const out = [];
  for (const s of sel) {
    let el;
    try { el = document.querySelector(s); } catch (e) { continue; }
    if (!el) continue;

    // ALLE Attribute einsammeln: bei manchen Feldern steht der Zweck nur im
    // Namen eines eigenen Attributs (`update-hours`, `minute-step`).
    const attr = {};
    for (const a of el.attributes) attr[a.name] = a.value || '';
    for (const a of ['name', 'type', 'placeholder', 'title', 'value',
                     'data-val-type', 'class', 'tabindex', 'id']) {
      if (!(a in attr)) attr[a] = '';
    }

    // Sichtbarer Text unmittelbar davor — oft steht die Beschriftung dort,
    // nur ohne <label for>.
    let davor = '';
    let n = el.previousElementSibling;
    while (n && !davor) {
      const t = (n.innerText || n.textContent || '').trim();
      if (t && t.length < 80) davor = t;
      n = n.previousElementSibling;
    }
    if (!davor && el.parentElement) {
      const eltern = (el.parentElement.innerText || '').trim();
      if (eltern && eltern.length < 80) davor = eltern;
    }

    out.push({ selector: s, attribute: attr, umgebungstext: davor });
  }
  return out;
}
"""



def titel_aus_seite(h1: str, og_titel: str, host: str) -> Optional[str]:
    """
    Ein fehlender `<title>` ist WCAG 2.4.2 — und der einzige Text, den ein
    Screenreader beim Laden ansagt.

    Abgeleitet wird in dieser Reihenfolge: die Hauptueberschrift der Seite, ein
    vorhandener og:title, sonst die Domain. Erfunden wird nichts.
    """
    for kandidat in (h1, og_titel):
        text = re.sub(r"\s+", " ", kandidat or "").strip()
        if 2 < len(text) <= 120:
            return text
    if host:
        return host.removeprefix("www.")
    return None
