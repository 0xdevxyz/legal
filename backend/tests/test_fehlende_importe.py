"""
Ein benutztes Standardmodul muss auch importiert sein.

Der Anlass ist der teuerste Fehler des Audits: `public_routes.py` rief
`re.split()` auf und importierte `re` nie. Folge war kein stiller Ausfall,
sondern ein Abbruch des GANZEN Scans — im oeffentlichen Hauptendpunkt, den
jeder Neukunde als allererstes trifft. Nach aussen kam:

    "Die Website '…' konnte nicht gescannt werden.
     name 're' is not defined.
     Stellen Sie sicher, dass die Website online ist"

Ein Fehler in unserem Code, dem Kunden als Problem SEINER Website vorgelegt.
Er haette ewig gesucht.

Warum kein Linter das gefangen hat: es gibt keinen im Build. Dieser Test ist
der Ersatz — er liest den Quelltext, sammelt alle `modul.attribut`-Zugriffe
auf bekannte Standardmodule und vergleicht sie mit den Importen der Datei.
Statisch, ohne die Module zu laden, deshalb schnell und ohne Nebenwirkungen.
"""
import ast
import os
import pathlib

import pytest

# Standardmodule, die typischerweise "vergessen" werden, weil sie in
# NACHBARdateien importiert sind und der Aufruf beim Kopieren mitwandert.
VERDAECHTIG = {
    "re", "os", "json", "time", "math", "uuid", "hashlib", "hmac", "base64",
    "secrets", "random", "socket", "asyncio", "logging", "datetime",
    "itertools", "collections", "urllib", "pathlib", "subprocess", "shutil",
    "traceback", "copy", "csv", "io", "gzip", "zlib", "string", "textwrap",
}

WURZEL = pathlib.Path(__file__).resolve().parent.parent


def _dateien():
    for pfad in sorted(WURZEL.glob("*.py")):
        if pfad.name.startswith("test_") or pfad.name.endswith(".bak"):
            continue
        yield pfad
    for unter in ("compliance_engine", "compliance_engine/checks"):
        verz = WURZEL / unter
        if verz.is_dir():
            for pfad in sorted(verz.glob("*.py")):
                yield pfad


def _fehlende_importe(quelle: str):
    """Benutzte Standardmodule, die nirgends in der Datei importiert werden."""
    baum = ast.parse(quelle)

    verfuegbar = set()
    for knoten in ast.walk(baum):
        if isinstance(knoten, ast.Import):
            for name in knoten.names:
                verfuegbar.add((name.asname or name.name).split(".")[0])
        elif isinstance(knoten, ast.ImportFrom):
            for name in knoten.names:
                verfuegbar.add(name.asname or name.name)
            if knoten.module:
                verfuegbar.add(knoten.module.split(".")[0])

    # Namen, die lokal gebunden werden (Zuweisung, Parameter, Schleife),
    # zaehlen ebenfalls als vorhanden — `os = ...` waere zwar seltsam, aber
    # kein fehlender Import.
    for knoten in ast.walk(baum):
        if isinstance(knoten, ast.Name) and isinstance(knoten.ctx, ast.Store):
            verfuegbar.add(knoten.id)
        elif isinstance(knoten, ast.arg):
            verfuegbar.add(knoten.arg)
        elif isinstance(knoten, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            verfuegbar.add(knoten.name)

    benutzt = set()
    for knoten in ast.walk(baum):
        if (isinstance(knoten, ast.Attribute)
                and isinstance(knoten.value, ast.Name)
                and knoten.value.id in VERDAECHTIG):
            benutzt.add(knoten.value.id)

    return sorted(benutzt - verfuegbar)


@pytest.mark.parametrize("pfad", list(_dateien()), ids=lambda p: p.name)
def test_kein_benutztes_modul_ohne_import(pfad):
    try:
        quelle = pfad.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        pytest.skip(f"nicht lesbar: {pfad.name}")
    try:
        fehlt = _fehlende_importe(quelle)
    except SyntaxError as e:
        pytest.fail(f"{pfad.name} laesst sich nicht parsen: {e}")
    assert not fehlt, (
        f"{pfad.name} benutzt {', '.join(fehlt)}, importiert es aber nicht — "
        f"das bricht zur Laufzeit ab, nicht beim Start"
    )


class TestDerWaechterFunktioniert:
    """Ein Waechter, der nie anschlaegt, ist kein Waechter."""

    def test_erkennt_den_echten_fall(self):
        quelle = "def f(t):\n    return re.split(r'x', t)\n"
        assert _fehlende_importe(quelle) == ["re"]

    def test_meldet_nicht_bei_vorhandenem_import(self):
        assert _fehlende_importe("import re\ndef f(t):\n    return re.split('x', t)\n") == []

    def test_import_in_der_funktion_zaehlt_auch(self):
        quelle = "def f(t):\n    import re\n    return re.split('x', t)\n"
        assert _fehlende_importe(quelle) == []

    def test_lokale_variable_ist_kein_fehlender_import(self):
        assert _fehlende_importe("def f():\n    io = Ding()\n    return io.lesen()\n") == []
