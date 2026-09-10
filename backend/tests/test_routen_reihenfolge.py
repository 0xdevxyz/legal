# -*- coding: utf-8 -*-
"""
Ein fester Pfad darf nicht hinter einem Platzhalter-Pfad stehen.

FastAPI nimmt die erste passende Route. Steht `/scan/{site_id}` vor
`/scan/capabilities`, wird "capabilities" als site_id gelesen — der Endpunkt
antwortet dann nicht mit seiner Auskunft, sondern mit "Kein Scan-Ergebnis
gefunden". Genau das war am 10.09.2026 der Fall: der dynamische Pfad stand in
`widget_routes`, der feste in `cookie_compliance_routes`, und der
widget_router wurde zuerst eingebunden.

Der Fehler ist von aussen kaum zu erkennen — der Endpunkt antwortet ja, nur
falsch. Deshalb dieser Test.
"""

import ast
import os
import re

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _include_reihenfolge():
    """Router in der Reihenfolge, in der main_production sie einbindet."""
    quelle = open(os.path.join(BACKEND, "main_production.py"), encoding="utf-8").read()
    return [m.group(1) for m in re.finditer(r"app\.include_router\(\s*([\w.]+)", quelle)]


def _praefix(quelle: str) -> str:
    """Der prefix= des APIRouter in dieser Datei. Ohne ihn vergleicht man Aepfel mit Birnen."""
    m = re.search(r"APIRouter\(\s*[^)]*?prefix\s*=\s*[\"\']([^\"\']*)[\"\']", quelle, re.S)
    return m.group(1) if m else ""


def _routen():
    """(datei, zeile, methode, vollstaendiger pfad) fuer jede Route."""
    treffer = []
    for wurzel, ordner, dateien in os.walk(BACKEND):
        if any(t in wurzel.split(os.sep) for t in
               ("_archive_pre_baseline", "venv", "__pycache__", "tests", "alembic", "tools")):
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
            praefix = _praefix(quelle)
            for knoten in ast.walk(baum):
                if not isinstance(knoten, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                for dek in knoten.decorator_list:
                    if not (isinstance(dek, ast.Call) and isinstance(dek.func, ast.Attribute)):
                        continue
                    if dek.func.attr not in ("get", "post", "put", "delete", "patch"):
                        continue
                    if not (isinstance(dek.func.value, ast.Name)
                            and dek.func.value.id in ("router", "app")):
                        continue
                    if not (dek.args and isinstance(dek.args[0], ast.Constant)):
                        continue
                    roh = str(dek.args[0].value)
                    voll = roh if roh.startswith(praefix) and praefix else (praefix + roh)
                    treffer.append((os.path.relpath(pfad, BACKEND), dek.lineno,
                                    dek.func.attr.upper(), voll))
    return treffer


def _passt(dynamisch, fest):
    m = re.escape(dynamisch)
    m = re.sub(r"\\\{[^}]*\\\}", "[^/]+", m)
    return re.fullmatch(m, fest) is not None


def test_kein_fester_pfad_steht_hinter_einem_platzhalter():
    routen = _routen()
    reihenfolge = _include_reihenfolge()

    def rang(datei):
        # Grobe Naeherung: Reihenfolge der include_router-Aufrufe ueber den
        # Dateinamen. Wo sie nicht zuzuordnen ist, zaehlt nur die Zeilennummer.
        stamm = os.path.basename(datei)[:-3].replace("_routes", "")
        for i, name in enumerate(reihenfolge):
            if stamm and stamm in name:
                return i
        return len(reihenfolge)

    verdeckt = []
    fest = [r for r in routen if "{" not in r[3]]
    dyn = [r for r in routen if "{" in r[3]]
    for df, dz, dm, dp in dyn:
        for ff, fz, fm, fp in fest:
            if dm != fm or not _passt(dp, fp):
                continue
            frueher = (rang(df), dz) < (rang(ff), fz)
            if frueher:
                verdeckt.append(f"  {fm:6s} {fp:52s} ({ff}:{fz})\n"
                                f"         verdeckt von {dp}  ({df}:{dz})")
    assert not verdeckt, (
        "Diese festen Pfade werden von einem Platzhalter-Pfad verdeckt:\n"
        + "\n".join(sorted(set(verdeckt)))
        + "\n\nDie feste Route muss zuerst eingebunden bzw. zuerst definiert werden."
    )
