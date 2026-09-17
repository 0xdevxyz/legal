"""Werbeflaeche und Backoffice behaupten keine Zustaende, sie nennen Messungen.

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

Am 17.09. fiel beim Dreh der Backoffice-Aufnahmen auf, dass dieser Waechter nur
landing-react las. Im Dashboard standen dieselben Muster unangetastet weiter,
darunter "Ihre Website ist bereits DSGVO-konform bezueglich Cookies" - eine
Zustandsbehauptung nicht ueber das eigene Produkt, sondern ueber die Website des
Kunden. Seitdem deckt der Waechter beide Flaechen ab.

Dabei fiel auch auf, dass das Muster fuer die WCAG-Konformitaet den Fund gar
nicht haette machen koennen: es war als `WCAG[^.\\n]{0,20}...` geschrieben und
scheiterte am Punkt in "WCAG 2.1 AA". Der Satz, der am 13.09. von Hand entfernt
wurde, waere also nie aufgefallen, wenn ihn jemand zurueckgeschrieben haette.

GELTUNGSBEREICH. Auf der Landing nur die Werbeflaeche, NICHT der Ratgeber und
nicht die Rechtsseiten: dort ist "eine rechtssichere Einwilligung muss ..."
fachlich richtige Prosa und keine Zusage ueber das eigene Produkt. Im Dashboard
dagegen alles, denn hinter dem Login spricht complyo ausschliesslich ueber das
eigene Angebot und die eigenen Messungen; Ratgeber-Prosa gibt es dort nicht
(nachgesehen am 17.09.2026). Kommentarzeilen bleiben aussen vor, ein Kommentar
wird keinem Kunden angezeigt und kann deshalb auch nichts versprechen.
"""

import os
import re

import pytest

# ACHTUNG ZUM AUSFUEHREN: wird nur backend/ gemountet, sind landing-react und
# dashboard-react nicht da, und diese Tests werden UEBERSPRUNGEN. Ein
# uebersprungener Test bewacht nichts. Damit sie greifen, das ganze Repo
# mounten:
#     scripts/tests-lokal.sh
# oder COMPLYO_LANDING_SRC / COMPLYO_DASHBOARD_SRC auf die src-Verzeichnisse
# zeigen lassen.
LANDING_SRC = os.path.abspath(
    os.getenv("COMPLYO_LANDING_SRC")
    or os.path.join(os.path.dirname(__file__), "..", "..", "landing-react", "src")
)

DASHBOARD_SRC = os.path.abspath(
    os.getenv("COMPLYO_DASHBOARD_SRC")
    or os.path.join(os.path.dirname(__file__), "..", "..", "dashboard-react", "src")
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
#
# Die Norm-Alternative deckt bewusst mehr als WCAG ab: gefunden wurden am
# 17.09. neben "WCAG 2.1 AA Konformitaet" auch "WCAG 2.2 AA konform" (als Badge
# ab 70 von 100 Punkten), "TCF 2.2 Konform" und "BFSG-konforme
# Barrierefreiheitserklaerung". Der Punkt in "2.1" darf das Muster nicht mehr
# stoppen, siehe Modulkopf.
VERBOTEN = {
    "DSGVO-konform": r"DSGVO[- ]konform",
    "rechtssicher": r"rechtssicher",
    "rechtskonform": r"rechtskonform",
    "Norm-Konformitaet behauptet": (
        r"(WCAG|BFSG|BITV|TCF|TTDSG|TDDDG|EAA|DDG)[^\n]{0,25}"
        r"(konform|Konformität|erreicht)"
    ),
    "abmahnsicher": r"abmahnsicher",
    "anwaltlich geprueft": r"anwaltlich\s+geprüft",
    "100 Prozent": r"(100\s?%|zu\s+100\s+Prozent)\s*(konform|sicher|rechts|DSGVO)",
}

# Zeilen, die ein Muster tragen, aber nichts behaupten. Jeder Eintrag nennt
# Datei, Textstueck und Grund. Ein Eintrag, der nichts mehr trifft, faellt in
# test_jede_ausnahme_wird_noch_gebraucht auf und gehoert dann geloescht.
AUSNAHMEN = (
    (
        os.path.join("components", "dashboard", "ComplianceIssueCard.tsx"),
        "includes('rechtssicher')",
        "Code-Logik: vergleicht die Kategorie eines Befunds, wird nicht angezeigt.",
    ),
    (
        os.path.join("components", "dashboard", "ComplianceIssueCard.tsx"),
        "'Rechtssichere Texte': 'legal_texts'",
        "Nachschlage-Schluessel fuer den Saeulennamen, den das Backend bis zum "
        "17.09.2026 geliefert hat und der in gespeicherten Scans noch steht.",
    ),
)

# Ein Kommentar wird nicht angezeigt und kann nichts versprechen. Die
# Begruendungen zu entfernten Behauptungen ("Hier stand ...") zitieren den alten
# Wortlaut und sind gerade deshalb wertvoll.
KOMMENTARZEILE = re.compile(r"^\s*(//|\*|/\*|\{/\*|\{\s*/\*)")


def _quellen(wurzel, ziele=None):
    """Alle .ts/.tsx unter `wurzel`, optional auf `ziele` eingegrenzt."""
    treffer = []
    for ziel in ziele or ("",):
        pfad = os.path.join(wurzel, ziel) if ziel else wurzel
        if os.path.isfile(pfad):
            treffer.append(pfad)
            continue
        for ordner, unterordner, namen in os.walk(pfad):
            unterordner[:] = [u for u in unterordner if u not in ("node_modules", ".next")]
            for name in namen:
                if name.endswith((".tsx", ".ts")):
                    treffer.append(os.path.join(ordner, name))
    return treffer


def _ist_ausnahme(wurzel, pfad, zeile):
    rel = os.path.relpath(pfad, wurzel)
    for datei, textstueck, _grund in AUSNAHMEN:
        if rel.endswith(datei) and textstueck in zeile:
            return True
    return False


def _funde(wurzel, dateien, muster):
    regex = re.compile(muster, re.IGNORECASE)
    funde = []
    for pfad in dateien:
        with open(pfad, encoding="utf-8") as f:
            for nr, zeile in enumerate(f, 1):
                if KOMMENTARZEILE.match(zeile):
                    continue
                if not regex.search(zeile):
                    continue
                if _ist_ausnahme(wurzel, pfad, zeile):
                    continue
                kurz = os.path.relpath(pfad, wurzel)
                funde.append(f"{kurz}:{nr}: {zeile.strip()[:110]}")
    return funde


HINWEIS = (
    "\n\nStatt eines Zustands eine Messung nennen: \"gemessen gegen WCAG 2.1 AA\", "
    "\"geprueft am TT.MM.\", \"im Scan ohne Befund geblieben\". Grund: § 305c BGB "
    "legt den Widerspruch zwischen Werbung und Haftungsausschluss gegen uns aus."
)


def _dateien():
    if not os.path.isdir(LANDING_SRC):
        pytest.skip(
            f"landing-react/src nicht gefunden unter {LANDING_SRC}. Diese Pruefung "
            "braucht das Repo-Wurzelverzeichnis im Container "
            "(-v $(pwd):/repo -w /repo/backend), siehe scripts/tests-lokal.sh."
        )
    treffer = _quellen(LANDING_SRC, WERBEFLAECHE)
    if not treffer:
        pytest.skip(f"keine Werbeflaechen-Dateien unter {LANDING_SRC}")
    return treffer


def _dashboard_dateien():
    if not os.path.isdir(DASHBOARD_SRC):
        pytest.skip(
            f"dashboard-react/src nicht gefunden unter {DASHBOARD_SRC}. Diese "
            "Pruefung braucht das Repo-Wurzelverzeichnis im Container "
            "(-v $(pwd):/repo -w /repo/backend), siehe scripts/tests-lokal.sh."
        )
    treffer = _quellen(DASHBOARD_SRC)
    if not treffer:
        pytest.skip(f"keine Quelldateien unter {DASHBOARD_SRC}")
    return treffer


@pytest.mark.parametrize("bezeichnung,muster", sorted(VERBOTEN.items()))
def test_werbeflaeche_behauptet_keinen_zustand(bezeichnung, muster):
    """Kein Zustandsversprechen in Komponenten, die das Angebot bewerben."""
    funde = _funde(LANDING_SRC, _dateien(), muster)
    assert not funde, (
        f"Zustandsbehauptung \"{bezeichnung}\" auf der Werbeflaeche:\n  "
        + "\n  ".join(funde)
        + HINWEIS
    )


@pytest.mark.parametrize("bezeichnung,muster", sorted(VERBOTEN.items()))
def test_dashboard_behauptet_keinen_zustand(bezeichnung, muster):
    """Kein Zustandsversprechen im Backoffice, das der Kunde nach dem Login sieht.

    Die schwerste Fundstelle vom 17.09.2026 war "Ihre Website ist bereits
    DSGVO-konform bezueglich Cookies": eine Aussage nicht ueber das eigene
    Produkt, sondern ueber die Rechtslage der Kundenwebsite, abgeleitet aus
    einem Scan, der nur Cookies gesehen hat. Ersetzt durch den Befund, der
    tatsaechlich vorlag ("im Scan ohne Befund geblieben").
    """
    funde = _funde(DASHBOARD_SRC, _dashboard_dateien(), muster)
    assert not funde, (
        f"Zustandsbehauptung \"{bezeichnung}\" im Dashboard:\n  "
        + "\n  ".join(funde)
        + HINWEIS
    )


def test_jede_ausnahme_wird_noch_gebraucht():
    """Eine Ausnahme, die nichts mehr trifft, verdeckt spaeter einen echten Fund."""
    dateien = _dashboard_dateien() + (
        _quellen(LANDING_SRC, WERBEFLAECHE) if os.path.isdir(LANDING_SRC) else []
    )
    tot = []
    for datei, textstueck, grund in AUSNAHMEN:
        if not any(
            pfad.endswith(datei) and textstueck in open(pfad, encoding="utf-8").read()
            for pfad in dateien
        ):
            tot.append(f"  {datei}: {textstueck!r} ({grund})")
    assert not tot, (
        "Diese Ausnahmen treffen nichts mehr und gehoeren geloescht:\n"
        + "\n".join(tot)
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
