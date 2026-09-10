# -*- coding: utf-8 -*-
"""
Ein Dienst, der beim Start angelegt wird, darf nicht per Wert importiert werden.

`from x import dienst` bindet den Wert im Augenblick des Imports. Legt
`main_production` den Dienst erst beim Start an, bleibt diese Bindung fuer
immer None — die spaetere Zuweisung im anderen Modul erreicht sie nicht.

Gemessen am 10.09.2026: vier Module machten das, drei davon in Rechtsfunktionen.

  * `compliance_engine/scanner.py` — `if legal_update_integration:` war IMMER
    falsch. Die aktiven Rechtsaenderungen wurden nie auf ein Scanergebnis
    angewendet. Das ist der Kern dessen, wofuer complyo ein Abo verlangt.
  * `legal_notification_routes.py` — alle vier Endpunkte antworteten dauerhaft
    mit 503 "Notification Service nicht verfuegbar".
  * `legal_change_routes.py` — die Wirkungsanalyse einer Rechtsaenderung lief
    ins Leere.

Kein Fehler im Log, kein roter Test: die Funktionen sahen aus wie vorhanden.
Deshalb prueft dieser Test die Regel, nicht die drei Fundstellen.
"""

import ast
import os
import re

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Re-Export, den niemand benutzt: `cookie_scanner_service` importiert die
# Klasse und legt sich eine eigene Instanz an. Bewusst stehen gelassen.
AUSNAHMEN = {("scanner/__init__.py", "headless_scanner.headless_scanner")}


def _singletons():
    """Namen, die irgendwo per `global` gesetzt werden — je Modul."""
    gefunden = {}
    for wurzel, ordner, dateien in os.walk(BACKEND):
        if any(t in wurzel.split(os.sep) for t in
               ("_archive_pre_baseline", "venv", "__pycache__", "tests", "node_modules")):
            continue
        for name in dateien:
            if not name.endswith(".py") or ".bak" in name:
                continue
            try:
                quelle = open(os.path.join(wurzel, name), encoding="utf-8", errors="replace").read()
            except Exception:
                continue
            for treffer in re.finditer(r"^\s*global\s+([a-zA-Z_]\w*)", quelle, re.M):
                gefunden.setdefault(name[:-3], set()).add(treffer.group(1))
    return gefunden


def test_kein_dienst_wird_per_wert_importiert():
    singletons = _singletons()
    verstoesse = []
    for wurzel, ordner, dateien in os.walk(BACKEND):
        if any(t in wurzel.split(os.sep) for t in
               ("_archive_pre_baseline", "venv", "__pycache__", "tests", "node_modules")):
            continue
        for name in dateien:
            if not name.endswith(".py") or ".bak" in name:
                continue
            pfad = os.path.join(wurzel, name)
            try:
                quelle = open(pfad, encoding="utf-8", errors="replace").read()
                baum = ast.parse(quelle)
            except Exception:
                continue
            rel = os.path.relpath(pfad, BACKEND)
            # Nur Importe auf oberster Ebene: die laufen VOR dem Start.
            for knoten in baum.body:
                if not isinstance(knoten, ast.ImportFrom) or not knoten.module:
                    continue
                modul = knoten.module.split(".")[-1]
                if modul == name[:-3] or modul not in singletons:
                    continue
                for alias in knoten.names:
                    if alias.name not in singletons[modul]:
                        continue
                    if (rel, f"{modul}.{alias.name}") in AUSNAHMEN:
                        continue
                    verstoesse.append(f"  {rel}:{knoten.lineno}  {modul}.{alias.name}")
    assert not verstoesse, (
        "Diese Module binden beim Import einen Dienst, den es zu diesem "
        "Zeitpunkt noch nicht gibt — die Bindung bleibt None:\n"
        + "\n".join(sorted(set(verstoesse)))
        + "\n\nStattdessen das Modul importieren und den Namen erst beim "
          "Aufruf lesen: `import x as _m` … `_m.dienst`."
    )


def test_die_drei_rechtsfunktionen_lesen_zur_laufzeit():
    """Punktprobe auf die konkreten Stellen, die es getroffen hatte."""
    paare = [
        ("compliance_engine/scanner.py", "_rechtsupdates.legal_update_integration"),
        ("legal_notification_routes.py", "_dienst.legal_notification_service"),
        ("legal_change_routes.py", "_monitor_modul.legal_monitor"),
    ]
    for datei, erwartet in paare:
        quelle = open(os.path.join(BACKEND, datei), encoding="utf-8").read()
        assert erwartet in quelle, f"{datei} liest den Dienst nicht mehr zur Laufzeit"
