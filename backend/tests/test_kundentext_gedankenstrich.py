# -*- coding: utf-8 -*-
"""Kein Gedankenstrich in Text, den ein Kunde liest.

Der Gedankenstrich ist in Befundtexten kein Stilfehler, sondern eine
Ungenauigkeit: er verschweigt, in welchem Verhaeltnis die beiden Teile
stehen. "Seite ohne Titel — abgeleitet aus der Hauptueberschrift" kann
heissen "deshalb", "obwohl" oder "und". Ein Komma, ein Doppelpunkt oder
ein Punkt sagen es.

Am 18.09.2026 standen 36 solche Stellen in Texten, die im Dashboard, im
Bericht oder auf dem oeffentlichen Pruefnachweis landen, darunter der
Seitentitel des Nachweises selbst und die sechs Punkte der
Cookie-Handlungsempfehlung. Aufgefallen war eine einzige davon, nebenbei.

Geprueft werden nur ausgegebene Zeichenketten. Kommentare und Docstrings
duerfen den Strich tragen: sie sind Werkstattsprache und erreichen keinen
Kunden.
"""

import ast
import os

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEDANKENSTRICH = "—"

# Schluessel und benannte Argumente, deren Wert ein Kunde zu sehen bekommt.
SICHTBAR = {"begruendung", "description", "title", "recommendation", "message",
            "summary", "reason", "text", "hinweis", "label", "legal_basis"}

UEBERSPRINGEN = {"tests", "__pycache__", "_archive_pre_baseline", "venv",
                 "node_modules", ".git"}


def _sichtbare_texte():
    """(Datei, Zeile, Schluessel, Text) fuer jede ausgegebene Zeichenkette."""
    for wurzel, unter, dateien in os.walk(BACKEND):
        unter[:] = [u for u in unter if u not in UEBERSPRINGEN]
        for name in dateien:
            if not name.endswith(".py") or ".bak" in name:
                continue
            pfad = os.path.join(wurzel, name)
            rel = os.path.relpath(pfad, BACKEND)
            try:
                baum = ast.parse(open(pfad, encoding="utf-8").read())
            except Exception:
                continue
            for k in ast.walk(baum):
                if isinstance(k, ast.Dict):
                    for s, w in zip(k.keys, k.values):
                        if isinstance(s, ast.Constant) and s.value in SICHTBAR:
                            yield rel, k.lineno, s.value, _text(w)
                elif isinstance(k, ast.Call):
                    for kw in k.keywords:
                        if kw.arg in SICHTBAR:
                            yield rel, k.lineno, kw.arg, _text(kw.value)


def _text(knoten) -> str:
    """Alle Zeichenketten-Teile eines Ausdrucks, auch aus f-Strings."""
    return "".join(n.value for n in ast.walk(knoten)
                   if isinstance(n, ast.Constant) and isinstance(n.value, str))


def test_kein_gedankenstrich_in_kundentext():
    treffer = [
        f"  {rel}:{zeile} [{schluessel}] {text.strip()[:80]}"
        for rel, zeile, schluessel, text in _sichtbare_texte()
        if GEDANKENSTRICH in text
    ]
    assert not treffer, (
        "Gedankenstrich in ausgegebenem Text:\n" + "\n".join(sorted(set(treffer)))
        + "\n\nStatt des Strichs sagen, wie die Teile zusammenhaengen: Komma, "
          "Doppelpunkt oder Punkt."
    )
