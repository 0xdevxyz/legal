"""
Der Wirkungsscan — misst, was der Besucher wirklich vorfindet.

Warum es diesen Modus gibt
--------------------------
Der normale Scan blockiert complyos eigenes Widget. Das muss er: sonst misst
er eine Seite, die complyo bereits repariert hat, findet nichts mehr und
ueberschreibt den gespeicherten Messwert mit einer Null. Je besser die
Reparatur wirkt, desto leerer waere der Pruefnachweis, der sie belegen soll.

Der Preis dieser Entscheidung: **niemand hat je den reparierten Zustand
gemessen.** Der Pruefnachweis sagt "vorher 22, nachher 2" — aber das
"nachher" stammt aus dem Scan-Browser, in den der Vorschlag versuchsweise
eingespielt wurde. Ob dieselbe Reparatur beim echten Besucher ankommt, war
bisher nur ueber die Wirkungsmeldungen des Widgets zu erahnen.

Der Wirkungsscan schliesst diese Luecke: **dieselbe Seite, zweimal, im selben
Lauf.**

    ohne Widget   was ein Besucher OHNE complyo vorfaende (Ausgangslage)
    mit Widget    was ein Besucher TATSAECHLICH vorfindet (Auslieferung)

Die Differenz ist kein gerechneter Wert und keine Behauptung, sondern zwei
Messungen im echten Browser auf der echten Seite. Genau das, was ein
Compliance-Kaeufer im Ernstfall braucht: nicht "wir haben repariert", sondern
"so sieht es bei Ihnen aus, nachgemessen am 10.08. um 14:12".

Was der Modus NICHT tut
-----------------------
Er repariert nichts und schlaegt nichts vor. Er stellt nur fest. Deshalb
laeuft er auch ohne Freigaben und ohne KI — er ist billig genug, um oft zu
laufen, und ehrlich genug, um in ein oeffentliches Protokoll zu gehen.

Ist auf einer Website gar kein Widget eingebaut, sind beide Messungen gleich.
Das ist kein Fehler des Scans, sondern der wichtigste Einzelbefund, den er
liefern kann — und genau der Fall, der im Bestand am haeufigsten vorkam.
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _regelzaehlung(ergebnis) -> Dict[str, int]:
    """Fundstellen je axe-Regel."""
    zaehlung: Dict[str, int] = {}
    for v in (getattr(ergebnis, "violations", None) or []):
        regel = v.get("id") if isinstance(v, dict) else getattr(v, "id", None)
        knoten = v.get("nodes") if isinstance(v, dict) else getattr(v, "nodes", None)
        if regel:
            zaehlung[regel] = zaehlung.get(regel, 0) + len(knoten or [])
    return zaehlung


def _fehler(ergebnis) -> Optional[str]:
    bi = getattr(ergebnis, "by_impact", None)
    return bi.get("error") if isinstance(bi, dict) else None


def vergleiche(ohne: Dict[str, int], mit: Dict[str, int]) -> Dict[str, Any]:
    """
    Stellt die beiden Messungen gegenueber — Regel fuer Regel.

    `behoben` zaehlt nur, was die zweite Messung wirklich nicht mehr findet.
    `neu` ist der unangenehme Fall: eine Regel, die ERST mit Widget auffaellt.
    Den gibt es, und er gehoert benannt — ein Overlay, das neue Barrieren
    schafft, ist genau das, was complyo den anderen vorwirft.
    """
    regeln = sorted(set(ohne) | set(mit))
    zeilen: List[Dict[str, Any]] = []
    for r in regeln:
        v, n = ohne.get(r, 0), mit.get(r, 0)
        zeilen.append({"regel": r, "ohne_widget": v, "mit_widget": n,
                       "differenz": v - n})
    v_gesamt, n_gesamt = sum(ohne.values()), sum(mit.values())
    return {
        "je_regel": zeilen,
        "behoben": [z for z in zeilen if z["differenz"] > 0],
        "neu": [z for z in zeilen if z["differenz"] < 0],
        "unveraendert": [z for z in zeilen if z["differenz"] == 0 and z["ohne_widget"]],
        "summe": {
            "ohne_widget": v_gesamt,
            "mit_widget": n_gesamt,
            "behoben": max(0, v_gesamt - n_gesamt),
            "quote": round(100 * (v_gesamt - n_gesamt) / v_gesamt) if v_gesamt else 0,
        },
    }


def _urteil(vergleich: Dict[str, Any], widget_lief: bool) -> Dict[str, str]:
    """
    Ein Satz, den ein Mensch ohne Vorwissen versteht.

    Bewusst nicht "Score 87" — eine Zahl ohne Aussage ist der Grund, warum
    niemand Scannern glaubt.
    """
    s = vergleich["summe"]
    if not widget_lief:
        return {"lage": "kein_widget",
                "satz": ("Auf dieser Website ist complyo nicht eingebaut. Beide "
                         "Messungen zeigen denselben Zustand — die freigegebenen "
                         "Reparaturen erreichen niemanden. Kleine Unterschiede "
                         "zwischen den beiden Laeufen sind Messrauschen (Lazy "
                         "Loading, Schieberegler) und nicht complyo zuzuschreiben.")}
    if vergleich["neu"]:
        regeln = ", ".join(z["regel"] for z in vergleich["neu"][:3])
        return {"lage": "verschlechterung",
                "satz": (f"Mit complyo treten Befunde auf, die ohne complyo nicht "
                         f"da sind ({regeln}). Das muss geprüft werden, bevor "
                         f"irgendetwas anderes zählt.")}
    if s["behoben"] == 0 and s["ohne_widget"] > 0:
        return {"lage": "wirkungslos",
                "satz": (f"complyo läuft, ändert am Messergebnis aber nichts: "
                         f"{s['ohne_widget']} Befunde vorher wie nachher. "
                         f"Vermutlich ist nichts freigegeben oder die "
                         f"Reparaturen finden ihr Ziel nicht mehr.")}
    if s["mit_widget"] == 0:
        return {"lage": "vollstaendig",
                "satz": (f"Alle {s['ohne_widget']} messbaren Befunde sind für "
                         f"Besucher behoben.")}
    return {"lage": "wirksam",
            "satz": (f"Von {s['ohne_widget']} messbaren Befunden sind für "
                     f"Besucher {s['behoben']} behoben ({s['quote']} %); "
                     f"{s['mit_widget']} bestehen fort.")}


async def wirkungsscan(scanner, url: str, wcag_level: str = "wcag21aa",
                       timeout: int = 30000) -> Dict[str, Any]:
    """
    Misst `url` zweimal: ohne und mit complyo-Widget.

    Args:
        scanner: eine AxeScanner-Instanz.

    Returns:
        Beide Messungen, der Vergleich je Regel und ein Urteil in einem Satz.
        Bei einem Fehler in einer der beiden Messungen steht das drin, statt
        eine Differenz aus einer halben Messung zu erfinden.
    """
    gemessen_am = datetime.now().isoformat()

    ohne = await scanner.scan_page(url, wcag_level=wcag_level, timeout=timeout,
                                   widget_blockieren=True)
    if _fehler(ohne):
        return {"success": False, "url": url, "gemessen_am": gemessen_am,
                "fehler": f"Ausgangsmessung fehlgeschlagen: {_fehler(ohne)}"}

    mit = await scanner.scan_page(url, wcag_level=wcag_level, timeout=timeout,
                                  widget_blockieren=False)
    if _fehler(mit):
        return {"success": False, "url": url, "gemessen_am": gemessen_am,
                "fehler": f"Auslieferungsmessung fehlgeschlagen: {_fehler(mit)}"}

    z_ohne, z_mit = _regelzaehlung(ohne), _regelzaehlung(mit)
    vergleich = vergleiche(z_ohne, z_mit)

    # Lief das Widget ueberhaupt?
    #
    # Diese Frage entscheidet die ZUSCHREIBUNG, und nur die Beobachtung darf
    # sie beantworten: hat die Seite im zweiten Lauf das Skript angefordert?
    #
    # Der erste Anlauf hatte hier eine Zeile, die "kein Widget" in "Widget
    # lief" umdrehte, sobald sich die beiden Messungen unterscheiden. Das ist
    # genau falsch herum: zwei Laeufe derselben Seite unterscheiden sich immer
    # ein wenig — Lazy Loading, Schieberegler, Werbung, Zufall. panoart360.de
    # hat gar kein complyo eingebaut und wurde damit prompt als
    # "Verschlechterung durch complyo" gemeldet.
    #
    # Ein Unterschied ohne Widget ist Messrauschen. Ihn complyo anzulasten
    # waere dieselbe Sorte Behauptung, die dieses Produkt anderen vorwirft.
    widget_lief = bool(getattr(mit, "widget_geladen", None))
    if not widget_lief:
        vergleich["messrauschen"] = vergleich.pop("neu", [])
        vergleich["neu"] = []

    return {
        "success": True,
        "modus": "wirkung",
        "url": url,
        "gemessen_am": gemessen_am,
        "regelsatz": wcag_level,
        "ohne_widget": {"gesamt": sum(z_ohne.values()), "je_regel": z_ohne},
        "mit_widget": {"gesamt": sum(z_mit.values()), "je_regel": z_mit},
        "vergleich": vergleich,
        "urteil": _urteil(vergleich, widget_lief),
        "hinweis": ("Zwei Messungen derselben Seite im selben Lauf: einmal mit "
                    "blockiertem complyo-Widget, einmal so, wie ein Besucher "
                    "die Seite lädt. Die Differenz ist gemessen, nicht "
                    "gerechnet."),
    }
