# -*- coding: utf-8 -*-
"""
Ein Rechtstext von complyo darf keine abgeloesten Gesetze zitieren.

Am 14.05.2024 wurden drei Bezeichnungen abgeloest, die in jedem aelteren
Mustertext stehen — und die ein Sprachmodell entsprechend haeufig reproduziert:
TMG -> DDG, TTDSG -> TDDDG, § 55 RStV -> § 18 MStV.

Der Prompt nennt die richtigen Namen seit dem 31.08.2026. Das genuegte nicht:
von den drei in der Produktion gespeicherten Dokumenten zitierte das Impressum
das TMG und beide Datenschutzerklaerungen das TTDSG — die juengste davon am
08.09.2026 erzeugt, also nach der Prompt-Korrektur. Ein Sprachmodell laesst
sich bitten, nicht zwingen.

Deshalb eine feste Nachkorrektur, die ausschliesslich Bezeichnungen ersetzt,
nie Inhalte — und dieser Test, der sie festhaelt.
"""

import os
import re

import pytest

from legal_text_generator import aktuelle_gesetzesnamen

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.mark.parametrize("vorher,nachher", [
    ("Angaben gemäß § 5 TMG", "Angaben gemäß § 5 DDG"),
    ("Angaben gemäß §5 TMG", "Angaben gemäß §5 DDG"),
    ("nach dem Telemediengesetz (TMG)", "nach dem Digitale-Dienste-Gesetz (DDG)"),
    ("Verantwortlich nach § 55 Abs. 2 RStV", "Verantwortlich nach § 18 Abs. 2 MStV"),
    ("gemäß TTDSG", "gemäß TDDDG"),
    ("§ 25 TTDSG", "§ 25 TDDDG"),
])
def test_abgeloeste_bezeichnungen_werden_ersetzt(vorher, nachher):
    assert aktuelle_gesetzesnamen(vorher) == nachher


def test_inhalte_bleiben_unberuehrt():
    """Ersetzt werden Namen, nicht Aussagen."""
    text = "<h1>Impressum</h1><p>Musterfirma GmbH, Hauptstr. 1</p>"
    assert aktuelle_gesetzesnamen(text) == text


def test_jeder_erzeugungsweg_geht_durch_die_korrektur():
    """Fuenf Dokumenttypen, fuenf Wege — keiner darf daran vorbei."""
    quelle = open(os.path.join(BACKEND, "legal_text_generator.py"), encoding="utf-8").read()
    zusammenbau = re.findall(r"html_with_disclaimer = .*", quelle)
    assert len(zusammenbau) >= 5, f"Nur {len(zusammenbau)} Zusammenbau-Stellen gefunden"
    for zeile in zusammenbau:
        assert "aktuelle_gesetzesnamen" in zeile or "third_country_clause" in zeile, (
            f"Erzeugungsweg ohne Nachkorrektur: {zeile.strip()}")


def test_ergebnis_enthaelt_keine_abgeloeste_bezeichnung_mehr():
    beispiel = ("<h1>Impressum</h1><p>Angaben gemäß § 5 TMG</p>"
                "<p>Verantwortlich nach § 55 Abs. 2 RStV</p>"
                "<p>Einwilligung nach § 25 TTDSG</p>")
    ergebnis = aktuelle_gesetzesnamen(beispiel)
    for veraltet in ("TMG", "RStV", "TTDSG"):
        assert veraltet not in ergebnis, f"{veraltet} steht noch im Ergebnis"


# Stellen, an denen der alte Name mit Absicht steht.
ERLAUBT = {
    # Der Prompt erklaert den Wechsel ausdruecklich.
    ("ai_fix_engine/prompts_v2.py", "seit 14.05.2024 gilt das DDG"),
    # Die Wissensablage ordnet Fundstellen zu und muss beide Namen kennen,
    # weil aeltere Quellen den alten fuehren.
    ("knowledge/knowledge_classifier.py", None),
    ("knowledge/pattern_extractor.py", None),
    ("knowledge/md_writer.py", None),
    ("ai_legal_classifier.py", None),
    # Ordnet eingehende Meldungen Rechtsgebieten zu.
    ("legal_area_mapping.py", None),
    ("pdf_report_generator.py", None),
    ("complyo_privacy_clause.py", None),
    ("legal_text_generator.py", None),   # die Ersetzungstabelle selbst
}


def _ist_erlaubt(rel, inhalt):
    # "DDG (ex TMG)" nennt den alten Namen, um den Wechsel zu erklaeren —
    # das ist kein veraltetes Zitat, sondern das Gegenteil davon.
    # Der alte Name darf genannt werden, um den Wechsel zu ERKLAEREN —
    # "DDG (ex TMG)" oder "bis 14.05.2024 TMG". Das ist kein veraltetes Zitat,
    # sondern das Gegenteil davon.
    if re.search(r"\(ex (TMG|TTDSG|RStV)\)|bis 14\.05\.2024", inhalt):
        return True
    # Suchmuster, mit denen complyo FREMDE Seiten prueft, muessen den alten
    # Namen kennen — dort steht er ja noch. Erkennbar an der Regex-Syntax.
    if re.search(r"\(\?:|\\s\*|\\b|\[\^", inhalt):
        return True
    for datei, marke in ERLAUBT:
        if rel.endswith(datei) and (marke is None or marke in inhalt):
            return True
    return False


def test_kein_ausgegebener_text_zitiert_ein_abgeloestes_gesetz():
    """
    Die Breitenprobe: nicht nur der Generator, jede Zeichenkette im Backend.

    Gefunden wurden dabei der Beispiel-Impressum des kostenlosen Checks
    ("Angaben gemäß § 5 TMG"), die Handlungsschritte dazu, die
    Rechtsgrundlage im Schnellscan ("TMG § 5") und die Ablaufbeschreibung
    ("DSGVO, TMG, TTDSG und Barrierefreiheit") — alles Text, den ein Kunde
    liest, und alles seit dem 14.05.2024 falsch.
    """
    import ast as _ast
    treffer = []
    for wurzel, ordner, dateien in os.walk(BACKEND):
        if any(t in wurzel.split(os.sep) for t in
               ("_archive_pre_baseline", "venv", "__pycache__", "tests", "node_modules")):
            continue
        for name in dateien:
            if not name.endswith(".py") or ".bak" in name:
                continue
            pfad = os.path.join(wurzel, name)
            rel = os.path.relpath(pfad, BACKEND)
            try:
                quelle = open(pfad, encoding="utf-8", errors="replace").read()
                baum = _ast.parse(quelle)
            except Exception:
                continue
            for knoten in _ast.walk(baum):
                if not (isinstance(knoten, _ast.Constant) and isinstance(knoten.value, str)):
                    continue
                if not re.search(r"\bTMG\b|\bTTDSG\b|\bRStV\b", knoten.value):
                    continue
                if _ist_erlaubt(rel, knoten.value):
                    continue
                treffer.append(f"  {rel}:{knoten.lineno}  {knoten.value.strip()[:70]}")
    assert not treffer, (
        "Abgeloestes Gesetz in einem ausgegebenen Text:\n" + "\n".join(sorted(set(treffer)))
        + "\n\nSeit 14.05.2024: TMG -> DDG, TTDSG -> TDDDG, § 55 RStV -> § 18 MStV."
    )
