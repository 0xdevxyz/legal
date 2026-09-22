"""Der Einbettungscode muss auf einen Host zeigen, den es gibt.

Anlass (23.09.2026): In den Vorlagen der Fix-Engine stand an vier Stellen

    <script src="https://widgets.complyo.de/cookie-banner-v2.0.0.min.js" ...>

Diesen Host gibt es nicht. widgets.complyo.de hat keinen A-Eintrag im DNS,
ausgeliefert wird ausschliesslich ueber api.complyo.de. Die Zeichenketten
stehen in den Anweisungen an das Sprachmodell und koennen damit in dessen
Antwort landen. Ein Kunde, der den Vorschlag uebernimmt, baut eine Zeile ein,
die nichts laedt, und haelt sich danach fuer geschuetzt.

Das ist die schlimmere Sorte Fehler: sie ist unsichtbar. Kein Banner
erscheint, keine Meldung erklaert warum, und der naechste Scan sieht auf der
Kundenseite dieselbe Luecke wie vorher.

Was dieser Waechter liest, nachgezaehlt
---------------------------------------
Ein gruener Waechter sagt nichts, solange nicht feststeht, wie viel er
ueberhaupt anfasst. Deshalb hier ausdruecklich:

* `prompts_v2.py` enthaelt zwei ausgeschriebene Schnipsel. Die findet
  `test_zeigt_nur_auf_die_api` und `test_trifft_eine_bediente_route`.
* `widget_routes.py` baut seinen Schnipsel aus einer Variablen zusammen
  (`base_url`). Dort greift die Suche nach `<script src="https://...` NICHT.
  Deshalb gibt es `test_snippet_endpunkt_nutzt_die_api`, der die Variable
  selbst prueft. Ohne diesen dritten Test waere die kanonische Quelle des
  Einbettungscodes ungeprueft geblieben, und der Waechter haette nur die
  Kopien bewacht.
"""
import re
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent

# Wo Einbettungscode als fertige Zeichenkette steht. Bewusst eine Liste und
# kein Baumlauf ueber alles: Testdateien und Archivstaende sollen den Waechter
# nicht ausloesen.
QUELLEN = [
    BACKEND / "ai_fix_engine" / "prompts_v2.py",
    BACKEND / "widget_routes.py",
]

ERLAUBTER_HOST = "api.complyo.de"

# <script ... src="https://host/pfad"
#
# Die Anfuehrungszeichen stehen im Quelltext je nach Umgebung nackt, einfach
# oder doppelt maskiert: in prompts_v2.py liegt der Schnipsel in einem
# JSON-Beispiel innerhalb eines Python-Strings, dort sind es zwei Backslashes.
# Deshalb `\\*` und nicht `\\?`. Mit `\\?` fand die Suche genau null Treffer,
# und der Waechter waere gruen gewesen, ohne irgendetwas zu bewachen.
SCRIPT_SRC = re.compile(r'<script[^>]*src=\\*"(https?://[^"\\]+)')


def _schnipsel(pfad: Path):
    if not pfad.exists():
        return []
    return SCRIPT_SRC.findall(pfad.read_text(encoding="utf-8"))


def _bediente_routen():
    return set(
        re.findall(
            r'@router\.get\("(/api/widgets/[^"]+\.js)"',
            (BACKEND / "widget_routes.py").read_text(encoding="utf-8"),
        )
    )


def test_zeigt_nur_auf_die_api():
    gefunden = [(q.name, a) for q in QUELLEN for a in _schnipsel(q)]
    assert gefunden, (
        "Kein einziger Schnipsel gefunden. Entweder hat sich die Schreibweise "
        "geaendert, oder dieser Waechter misst nichts mehr."
    )

    fehler = [
        f"{name}: {adresse}"
        for name, adresse in gefunden
        if adresse.split("//", 1)[1].split("/", 1)[0] != ERLAUBTER_HOST
    ]
    assert not fehler, (
        "Einbettungscode zeigt auf einen Host, der nicht ausliefert:\n  "
        + "\n  ".join(fehler)
        + f"\nAusgeliefert wird nur ueber {ERLAUBTER_HOST}."
    )


def test_trifft_eine_bediente_route():
    routen = _bediente_routen()
    assert routen, "Keine Widget-Routen gefunden, der Waechter misst nichts."

    fehler = []
    for quelle in QUELLEN:
        for adresse in _schnipsel(quelle):
            rest = adresse.split("//", 1)[1]
            pfad = "/" + rest.split("/", 1)[1] if "/" in rest else "/"
            if pfad not in routen:
                fehler.append(f"{quelle.name}: {pfad}")
    assert not fehler, (
        "Einbettungscode nennt einen Pfad, den widget_routes.py nicht bedient:\n  "
        + "\n  ".join(fehler)
        + "\nBediente Pfade: "
        + ", ".join(sorted(routen))
    )


def test_snippet_endpunkt_nutzt_die_api():
    """Die kanonische Quelle: /api/widgets/snippet/{widget_type}.

    Der Endpunkt setzt den Schnipsel aus einer Variablen zusammen, die keine
    Suche nach `<script src="https://` findet. Er ist aber genau der Weg, ueber
    den ein zahlender Kunde seinen Einbettungscode bekommt.
    """
    quelltext = (BACKEND / "widget_routes.py").read_text(encoding="utf-8")
    basis = re.findall(r'base_url\s*=\s*"(https?://[^"]+)"', quelltext)
    assert basis, (
        "base_url in widget_routes.py nicht gefunden. Wenn der Endpunkt "
        "umgebaut wurde, muss dieser Waechter mitwandern, sonst bewacht er "
        "nur noch die Kopien in den KI-Vorlagen."
    )
    fehler = [b for b in basis if b.rstrip("/") != f"https://{ERLAUBTER_HOST}"]
    assert not fehler, (
        "Der Snippet-Endpunkt liefert einen anderen Host aus: "
        + ", ".join(fehler)
        + f"\nAusgeliefert wird nur ueber {ERLAUBTER_HOST}."
    )
