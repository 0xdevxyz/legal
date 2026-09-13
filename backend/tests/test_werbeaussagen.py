"""Die Werbeflaeche behauptet keine Zustaende, sie nennt Messungen.

Am 01.09.2026 stand im Backend woertlich "Wir geben KEINE Garantie auf
Abmahnsicherheit", waehrend die Landing an denselben Stellen "rechtssicher und
DSGVO-konform" versprach. Solche Widersprueche gehen nach § 305c BGB zu Lasten
des Verwenders: vor Gericht gilt die Werbeaussage, nicht der Haftungsausschluss.
Der Referenzfall fuer den Rechtstexte-Generator ist BGH I ZR 113/20 (smartlaw)
- der Generator selbst war zulaessig, verloren wurde ueber die Werbeaussage.

Am 11.09. wurde nachgemessen, dass drei Behauptungen weiter live standen, und
am 13.09. entfernt: "DSGVO-konform" in der Fussleiste JEDER Seite,
"WCAG 2.1 AA Konformitaet" als Saeulenbeschriftung im Scanner, "rechtssichere
Texte" im Begleittext des Erklaervideos.

Dieser Test bewacht die Werbeflaeche, NICHT den Ratgeber und nicht die
Rechtsseiten. Dort ist "eine rechtssichere Einwilligung muss ..." fachlich
richtige Prosa und keine Zusage ueber das eigene Produkt. Eine pauschale Sperre
ueber alle Dateien waere eine Fehlalarm-Maschine und wuerde ehrliche Inhalte
blockieren.
"""

import os
import re

import pytest

# ACHTUNG ZUM AUSFUEHREN: wird nur backend/ gemountet, ist landing-react nicht
# da, und diese Tests werden UEBERSPRUNGEN. Ein uebersprungener Test bewacht
# nichts. Damit sie greifen, das ganze Repo mounten:
#     scripts/tests-lokal.sh
# oder COMPLYO_LANDING_SRC auf das src-Verzeichnis der Landing zeigen lassen.
LANDING_SRC = os.path.abspath(
    os.getenv("COMPLYO_LANDING_SRC")
    or os.path.join(os.path.dirname(__file__), "..", "..", "landing-react", "src")
)

# Die Werbeflaeche: hier spricht complyo ueber das eigene Angebot.
WERBEFLAECHE = (
    os.path.join("components", "saas-landing"),
    os.path.join("components", "kampagne"),
    os.path.join("components", "landing"),
    os.path.join("components", "Erklaervideo.tsx"),
    os.path.join("app", "page.tsx"),
    os.path.join("app", "produkt"),
    os.path.join("app", "preise"),
)

# Zustandsbehauptungen. Erlaubt ist die Messung ("gemessen gegen WCAG 2.1 AA",
# "geprueft am TT.MM."), verboten der Zustand ("ist konform").
VERBOTEN = {
    "DSGVO-konform": r"DSGVO[- ]konform",
    "rechtssicher": r"rechtssicher",
    "WCAG-Konformitaet behauptet": r"WCAG[^.\n]{0,20}(konform|Konformität|erreicht)",
    "abmahnsicher": r"abmahnsicher",
    "anwaltlich geprueft": r"anwaltlich\s+geprüft",
    "100 Prozent": r"(100\s?%|zu\s+100\s+Prozent)\s*(konform|sicher|rechts)",
}


def _dateien():
    if not os.path.isdir(LANDING_SRC):
        pytest.skip(
            f"landing-react/src nicht gefunden unter {LANDING_SRC}. Diese Pruefung "
            "braucht das Repo-Wurzelverzeichnis im Container "
            "(-v $(pwd):/repo -w /repo/backend), siehe scripts/tests-lokal.sh."
        )
    treffer = []
    for ziel in WERBEFLAECHE:
        pfad = os.path.join(LANDING_SRC, ziel)
        if os.path.isfile(pfad):
            treffer.append(pfad)
            continue
        for wurzel, _, namen in os.walk(pfad):
            for name in namen:
                if name.endswith((".tsx", ".ts")):
                    treffer.append(os.path.join(wurzel, name))
    if not treffer:
        pytest.skip(f"keine Werbeflaechen-Dateien unter {LANDING_SRC}")
    return treffer


@pytest.mark.parametrize("bezeichnung,muster", sorted(VERBOTEN.items()))
def test_werbeflaeche_behauptet_keinen_zustand(bezeichnung, muster):
    """Kein Zustandsversprechen in Komponenten, die das Angebot bewerben."""
    regex = re.compile(muster, re.IGNORECASE)
    funde = []
    for pfad in _dateien():
        with open(pfad, encoding="utf-8") as f:
            for nr, zeile in enumerate(f, 1):
                if regex.search(zeile):
                    kurz = os.path.relpath(pfad, LANDING_SRC)
                    funde.append(f"{kurz}:{nr}: {zeile.strip()[:110]}")
    assert not funde, (
        f"Zustandsbehauptung \"{bezeichnung}\" auf der Werbeflaeche:\n  "
        + "\n  ".join(funde)
        + "\n\nStatt eines Zustands eine Messung nennen: \"gemessen gegen "
        "WCAG 2.1 AA\", \"geprueft am TT.MM.\". Grund: § 305c BGB legt den "
        "Widerspruch zwischen Werbung und Haftungsausschluss gegen uns aus."
    )


def test_agb_schliessen_abmahnsicherheit_weiter_aus():
    """Der Haftungsausschluss in den AGB ist das Gegenstueck und bleibt stehen."""
    pfad = os.path.join(LANDING_SRC, "app", "agb", "page.tsx")
    if not os.path.exists(pfad):
        pytest.skip(f"AGB-Seite nicht gefunden unter {pfad}")
    text = open(pfad, encoding="utf-8").read()
    assert "Abmahnsicherheit" in text, (
        "Die AGB nennen Abmahnsicherheit nicht mehr. Der Ausschluss in Ziffer 8 "
        "ist das Gegenstueck zur Messsprache auf der Werbeflaeche."
    )


@pytest.mark.parametrize("seite", ["datenschutz", "agb", "cookie-richtlinie"])
def test_stand_datum_ist_fest_und_nicht_heute(seite):
    """Ein Stand-Datum aus `new Date()` zeigt immer heute und beweist nichts.

    Genau das war bis zum 01.09.2026 der Fall: das Datum der Rechtstexte wurde
    bei jedem Aufruf neu erzeugt, ein Nachweis ueber den Stand war damit nicht
    fuehrbar.
    """
    pfad = os.path.join(LANDING_SRC, "app", seite, "page.tsx")
    if not os.path.exists(pfad):
        pytest.skip(f"{seite} nicht gefunden unter {pfad}")
    text = open(pfad, encoding="utf-8").read()
    abschnitt = text[: text.find("<section") if "<section" in text else len(text)]
    assert re.search(r"Stand:", abschnitt), f"{seite}: kein Stand-Datum gefunden"
    assert "new Date()" not in abschnitt, (
        f"{seite}: Stand-Datum wird aus new Date() erzeugt und zeigt immer heute. "
        "Ein festes Datum eintragen, das zur letzten inhaltlichen Aenderung passt."
    )
    assert re.search(r"\d{1,2}\.\s+\w+\s+20\d\d", abschnitt), (
        f"{seite}: Stand-Datum nicht als festes Datum lesbar."
    )
