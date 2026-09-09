# -*- coding: utf-8 -*-
"""
complyo darf nicht behaupten, etwas anderes zu sein, als es ist.

Gemessen am 10.09.2026: an dreizehn Stellen in fuenf Backend-Dateien trat
complyo als "Complyo GmbH" auf, teils an einer Anschrift in Markkleeberg, die
nie gestimmt hat. Betroffen war nicht nur die eigene Aussendarstellung:

  * `complyo_privacy_clause.py` schrieb diesen Namen in die
    Datenschutzerklaerung JEDES Kunden. Der Kunde benennt darin seinen
    Auftragsverarbeiter (Art. 13 DSGVO) — und benannte einen, den es nicht gibt.
  * Der Haftungsausschluss im PDF-Bericht lautete "Complyo GmbH uebernimmt
    keine Haftung". Ein Ausschluss im Namen einer Gesellschaft, die es nicht
    gibt, schuetzt niemanden.
  * `gdpr_api.py` nannte einer betroffenen Person diese GmbH als
    Verantwortlichen und einen Datenschutzbeauftragten unter dpo@complyo.de.

complyo wird als Einzelunternehmen von Yvonne Weishar gefuehrt. Wer ohne
existierende GmbH als GmbH auftritt, loest Rechtsscheinhaftung aus: der
Handelnde haftet persoenlich — das Gegenteil dessen, was ein Rechtsformzusatz
bewirken soll. Genau deshalb ist das hier ein Test und keine Notiz.
"""

import ast
import os

import pytest

import anbieter

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WURZEL = os.path.dirname(BACKEND)

# Nur Angaben, die complyo SELBST betreffen. "Max Mustermann" und
# "Musterstrasse 123" sind Beispieldaten eines Pruefwerkzeugs und in Vorlagen,
# Tests und Formularfeldern voellig richtig — sie stehen hier bewusst nicht.
VERBOTEN = (
    "Complyo GmbH",
    "complyo GmbH",
    "Koburger",
    "Markkleeberg",
    "dpo@complyo.de",
)

# Dateien, die solche Angaben als PRUEFGEGENSTAND enthalten duerfen: sie
# beschreiben eine fremde Website, die geprueft wird, nicht uns. Und
# anbieter.py selbst, dessen Dokumentation die Geschichte erzaehlt.
AUSNAHMEN = {
    "anbieter.py",
    "tests/test_anbieterdaten.py",   # dieser Test nennt die verbotenen Woerter selbst
    "tests/test_pflichtangaben_erkennung.py",
    "compliance_engine/checks/deep_content_analyzer.py",
}


def _python_dateien():
    for wurzel, ordner, dateien in os.walk(BACKEND):
        teile = wurzel.split(os.sep)
        if any(t in ("_archive_pre_baseline", "venv", "node_modules", "__pycache__",
                     "alembic") for t in teile):
            continue
        for name in dateien:
            if name.endswith(".py") and ".bak" not in name:
                yield os.path.join(wurzel, name)


def test_keine_erfundene_rechtsform_in_ausgegebenen_texten():
    """Prueft Zeichenketten, nicht Kommentare — die duerfen die Geschichte erzaehlen."""
    treffer = []
    for pfad in _python_dateien():
        rel = os.path.relpath(pfad, BACKEND)
        if rel in AUSNAHMEN:
            continue
        try:
            quelle = open(pfad, encoding="utf-8", errors="replace").read()
            baum = ast.parse(quelle)
        except Exception:
            continue
        for knoten in ast.walk(baum):
            if isinstance(knoten, ast.Constant) and isinstance(knoten.value, str):
                for wort in VERBOTEN:
                    if wort in knoten.value:
                        treffer.append(f"  {rel}:{knoten.lineno}  enthaelt '{wort}'")
    assert not treffer, (
        "Erfundene Anbieterangaben in ausgegebenem Text:\n" + "\n".join(sorted(set(treffer)))
        + "\n\ncomplyo ist ein Einzelunternehmen. Die Angaben stehen in anbieter.py."
    )


@pytest.mark.parametrize("datei,erwartet", [
    ("email_service.py", "Yvonne Weishar · Complyo, Pappelallee 64, 10437 Berlin"),
    ("legal_notification_service.py", "Yvonne Weishar · Complyo, Pappelallee 64, 10437 Berlin"),
    ("pdf_report_generator.py", "Yvonne Weishar · Complyo"),
])
def test_vorlagen_nennen_den_richtigen_anbieter(datei, erwartet):
    quelle = open(os.path.join(BACKEND, datei), encoding="utf-8").read()
    assert erwartet in quelle, f"{datei} nennt den Anbieter nicht (mehr) vollstaendig"


def test_vorlagentext_deckt_sich_mit_der_quelle():
    """Der woertliche Text in den Vorlagen und anbieter.py duerfen nicht auseinanderlaufen."""
    assert anbieter.ABSENDER == "Yvonne Weishar · Complyo"
    assert anbieter.ANSCHRIFT_EINZEILIG == "Pappelallee 64, 10437 Berlin"
    assert anbieter.ABSENDER_MIT_ANSCHRIFT == (
        "Yvonne Weishar · Complyo, Pappelallee 64, 10437 Berlin")


def test_backend_und_frontend_nennen_denselben_anbieter():
    """Zwei Quellen sind erlaubt — zwei verschiedene Wahrheiten nicht."""
    pfad = os.path.join(WURZEL, "landing-react", "src", "lib", "anbieter.ts")
    if not os.path.exists(pfad):
        pytest.skip("landing-react nicht eingehaengt")
    ts = open(pfad, encoding="utf-8").read()
    for wert in (anbieter.NAME, anbieter.STRASSE, anbieter.PLZ, anbieter.ORT,
                 anbieter.EMAIL, anbieter.UST_ID):
        assert f"'{wert}'" in ts, (
            f"'{wert}' steht in backend/anbieter.py, aber nicht in anbieter.ts")


def test_kein_datenschutzbeauftragter_wird_behauptet():
    """
    Ein Einzelunternehmen unterhalb von 20 staendig verarbeitenden Personen
    muss keinen bestellen (§ 38 BDSG). Eine Adresse zu nennen, an die niemand
    antwortet, verletzt dagegen Art. 12 Abs. 2 DSGVO.
    """
    assert anbieter.DATENSCHUTZBEAUFTRAGTER is None
