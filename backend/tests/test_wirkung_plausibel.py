"""Der Pruefnachweis darf keine Zahl zeigen, die nichts bedeutet.

Anlass (25.09.2026). Zwei Befunde am oeffentlichen Nachweis, beide auf der
Seite, mit der complyo seine Messgenauigkeit vorzeigt:

**Erstens, arithmetisch unmoeglich.** Fuer eine loqal.io-Unterseite stand
`verfehlt=35` bei `erwartet=4`. Man kann nicht mehr Ziele verfehlen, als es zu
treffen gab. Elf Zeilen verletzten die Invariante, und ihre Summe floss in die
oeffentliche Kennzahl "Ziele nicht gefunden". Derselbe Fehler war am 10.09.2026
schon einmal behoben (17d0a8f); er kam zurueck, weil ihn niemand faengt.

**Zweitens, ein Fehlalarm.** Auch die stimmigen Zahlen wurden falsch gedeutet:
"Das deutet auf eine Aenderung an der Website hin (etwa ein Theme-Update)."
Eine freigegebene Reparatur gilt aber fuer die Stelle, an der sie gemessen
wurde. Dass der Alternativtext des Startseitenbildes auf /impressum/ nicht
greift, ist der Normalfall. Gemessen am 25.09. auf complyo.de: 25 angewendet,
33 "nicht gefunden", kein einziger davon ein Mangel.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import wirkung_routes as wr  # noqa: E402

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _lese(*teile):
    with open(os.path.join(_BACKEND, *teile), encoding="utf-8") as fh:
        return fh.read()


# ---------------------------------------------------------------------------
# Die Invariante
# ---------------------------------------------------------------------------
def test_die_pruefung_steht_im_schreibweg():
    """Nicht in der Auswertung, sondern dort, wo die Zahl entsteht.

    Eine Pruefung erst beim Anzeigen haette den Bestand nie markiert und
    saemtliche Altzeilen weiter veroeffentlicht.
    """
    quelle = _lese("wirkung_routes.py")
    assert "unplausibel = verfehlt > erwartet" in quelle, (
        "Die Invariante wird beim Speichern nicht geprueft.")
    stelle = quelle[quelle.index("unplausibel = verfehlt > erwartet"):][:700]
    assert "logger.warning" in stelle, (
        "Eine unstimmige Meldung muss laut protokolliert werden, sonst faellt "
        "sie genauso wenig auf wie beim ersten Mal.")


def test_unstimmige_meldung_wird_nicht_verworfen_sondern_gekennzeichnet():
    """Die Zeile ist der Beleg. Loeschen waere bequemer und falsch."""
    quelle = _lese("wirkung_routes.py")
    stelle = quelle[quelle.index("unplausibel = verfehlt > erwartet"):][:900]
    assert "raise" not in stelle and "HTTPException" not in stelle, (
        "Die Meldung wird abgewiesen statt gekennzeichnet. Dann fehlt der "
        "Beleg, mit dem sich der Fehler beim naechsten Mal finden laesst.")
    assert "unplausibel" in quelle[quelle.index("INSERT INTO accessibility_wirkung"):][:900], (
        "Die Kennzeichnung wird nicht gespeichert.")


def test_migration_zieht_den_bestand_nach():
    mig = _lese("alembic", "versions", "20260925_0034_wirkung_plausibel.py")
    assert "verfehlt > erwartet" in mig, "Der Bestand wird nicht nachgezogen."
    assert "DELETE" not in mig.upper(), (
        "Die Migration loescht. Die Zeilen sind der Beleg und bleiben.")


# ---------------------------------------------------------------------------
# Was veroeffentlicht wird
# ---------------------------------------------------------------------------
def test_auswertung_laesst_unplausible_zeilen_weg():
    quelle = _lese("wirkung_routes.py")
    stelle = quelle[quelle.index("async def wirkung_fuer_site"):]
    assert 'z["unplausibel"]' in stelle, (
        "Die Auswertung filtert nicht; unstimmige Zeilen wuerden weiter "
        "veroeffentlicht.")
    assert "meldungen_verworfen" in stelle, (
        "Was weggelassen wurde, muss ausgewiesen werden. Eine Auswertung, die "
        "stillschweigend etwas unterschlaegt, ist dieselbe Sorte Aussage wie "
        "eine falsche.")


def test_auswertung_nennt_die_reichweite():
    """Die Zahl, die etwas aussagt."""
    stelle = _lese("wirkung_routes.py")
    assert "seiten_mit_wirkung" in stelle


# ---------------------------------------------------------------------------
# Der Fehlalarm, namentlich
# ---------------------------------------------------------------------------
def test_kein_theme_update_alarm_mehr_auf_der_nachweisseite():
    """Die Gegenprobe gegen einen Rueckfall.

    Der Satz stand woertlich auf der oeffentlichen Seite und deutete den
    Normalfall als Mangel.
    """
    seite = _lese("compliance_engine", "nachweis_seite.py")
    generator = _lese("compliance_engine", "nachweis_generator.py")
    for name, quelle in (("nachweis_seite.py", seite), ("nachweis_generator.py", generator)):
        # Im Kommentar darf der Satz stehen, er erklaert ja den Anlass. In einer
        # ausgegebenen Zeichenkette nicht.
        code = "\n".join(z for z in quelle.split("\n")
                         if not z.strip().startswith("#"))
        assert "deutet auf eine Änderung an der Website hin" not in code, (
            f"{name} deutet verfehlte Ziele wieder als Mangel.")


def test_nachweisseite_erklaert_warum_verfehlt_kein_mangel_ist():
    seite = _lese("compliance_engine", "nachweis_seite.py")
    assert "Normalfall" in seite and "kein Mangel" in seite, (
        "Die Seite zeigt Zahlen, ohne zu sagen, wie sie zu lesen sind.")


def test_ziele_verfehlt_ist_keine_kennzahl_mehr():
    """Es bleibt im Datensatz, aber nicht als Kachel neben den anderen.

    Nebeneinandergestellt liest sich "25 angewendet / 33 nicht gefunden" wie
    eine Quote, und zwar wie eine schlechte.
    """
    seite = _lese("compliance_engine", "nachweis_seite.py")
    kacheln = seite[seite.index('<div class="kennzahl">'):][:900]
    assert "Ziele nicht gefunden" not in kacheln, (
        "Die Kachel ist zurueck und stellt den Normalfall neben die Leistung.")


# ---------------------------------------------------------------------------
# Herkunft
# ---------------------------------------------------------------------------
def test_widget_meldet_seine_fassung():
    widget = _lese("widgets", "a11y_remediation.js")
    assert "MELDER_FASSUNG" in widget
    assert "melder: MELDER_FASSUNG" in widget, (
        "Die Fassung wird nicht mitgeschickt. Dann laesst sich nach dem "
        "naechsten Umbau nicht sagen, ob eine Zahl alt oder falsch ist.")


def test_server_nimmt_die_fassung_entgegen_und_speichert_sie():
    quelle = _lese("wirkung_routes.py")
    assert "melder: str = Field" in quelle, "Das Modell kennt die Fassung nicht."
    einfuegen = quelle[quelle.index("INSERT INTO accessibility_wirkung"):][:900]
    assert "melder" in einfuegen, "Die Fassung wird nicht gespeichert."


def test_meldung_ohne_fassung_bleibt_zulaessig():
    """Alte Widgets im Umlauf duerfen nicht abbrechen.

    Auf Kundenseiten steht eine zwischengespeicherte Fassung, teils fuer
    Stunden. Wer hier eine Pflichtangabe daraus macht, verliert genau die
    Meldungen, die den Uebergang belegen.
    """
    m = wr.WirkungsMeldung(pfad="/")
    assert m.melder == ""


def test_widget_fassung_steht_auch_beim_server():
    """Die Falle, die sich sonst beim naechsten Hochzaehlen stellt.

    Traegt jemand im Widget eine neue Fassung ein und vergisst die Menge im
    Server, werden alle Meldungen still zu "unbekannt". Der Fehler faellt erst
    auf, wenn man ihn braucht, naemlich beim naechsten Zaehlfehler.
    """
    import re
    widget = _lese("widgets", "a11y_remediation.js")
    m = re.search(r"var MELDER_FASSUNG = '([^']+)'", widget)
    assert m, "Das Widget nennt keine Fassung."
    assert m.group(1) in wr.MELDER_FASSUNGEN, (
        f"Die Widget-Fassung {m.group(1)!r} steht nicht in "
        f"wirkung_routes.MELDER_FASSUNGEN. Alle Meldungen wuerden als "
        f"unbekannt gespeichert.")
