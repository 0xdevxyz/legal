# -*- coding: utf-8 -*-
"""
Die API beschreibt sich nicht selbst, solange sie in Produktion laeuft.

Am 13.10.2026 lieferte `https://api.complyo.de/openapi.json` ohne Anmeldung
das vollstaendige Schema aus: 333 Pfade, 354 Operationen, 144 Datenmodelle,
darunter alle Admin-Routen (`/api/admin/*`, `/api/gdpr/admin/*`,
`/api/auth/admin/reset-master-password`) und die internen Funktionen
(`risk-radar`, `wirkungsscan`, `fix-jobs`, `knowledge`). `/docs` und `/redoc`
waren schon zu, das Schema dahinter nicht: halb abgeschaltet ist offen.

Zusammen mit `GET /health`, das Latenzen von Datenbank und Redis sowie die
Angabe nannte, welche Dienste konfiguriert sind, war das die Landkarte fuer
jeden, der das Produkt nachbauen oder angreifen will.

Der Test liest `main_production.py` statt es zu importieren: die Import-Kette
braucht Datenbank und Schluessel und scheitert in der Testumgebung. Er liest
genau diese eine Datei, denn dort wird die App erzeugt und `/health` definiert.
Eine zweite App-Erzeugung an anderer Stelle sahe er nicht.
"""

import ast
import os

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUELLE = os.path.join(BACKEND, "main_production.py")

# Was /health ohne Anmeldung zeigen darf. Alles Weitere (Latenzen,
# konfigurierte Dienste) gehoert hinter die Anmeldung oder nach /metrics.
HEALTH_ERLAUBT = {"status", "timestamp"}


def _baum():
    with open(QUELLE, encoding="utf-8") as f:
        return ast.parse(f.read())


def _app_aufruf(baum):
    treffer = [
        n for n in ast.walk(baum)
        if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "FastAPI"
    ]
    assert len(treffer) == 1, f"erwartet genau eine App-Erzeugung, gefunden {len(treffer)}"
    return treffer[0]


def _zuweisung(baum, name):
    treffer = [
        n for n in ast.walk(baum)
        if isinstance(n, ast.Assign)
        and any(getattr(t, "id", None) == name for t in n.targets)
    ]
    assert len(treffer) == 1, f"{name} muss genau einmal zugewiesen werden, gefunden {len(treffer)}"
    return treffer[0].value


class TestSchemaNichtOeffentlich:
    def test_docs_redoc_und_schema_haengen_an_der_umgebung(self):
        baum = _baum()
        kw = {k.arg: k.value for k in _app_aufruf(baum).keywords}
        for schluessel in ("docs_url", "redoc_url", "openapi_url"):
            assert schluessel in kw, (
                f"FastAPI(...) setzt {schluessel} nicht: Standard ist ein offener Pfad"
            )
            wert = kw[schluessel]
            # Eine feste Zeichenkette waere in Produktion offen.
            assert isinstance(wert, ast.Name), (
                f"{schluessel} muss aus der Umgebung abgeleitet werden, nicht fest stehen"
            )
            ausdruck = _zuweisung(baum, wert.id)
            assert isinstance(ausdruck, ast.IfExp), f"{wert.id}: erwartet 'X if ... else None'"
            bedingung = ast.dump(ausdruck.test)
            assert "ENVIRONMENT" in bedingung and "NotEq" in bedingung and "production" in bedingung, (
                f"{wert.id}: muss mit ENVIRONMENT != 'production' geschaltet sein"
            )
            assert isinstance(ausdruck.orelse, ast.Constant) and ausdruck.orelse.value is None, (
                f"{wert.id}: in Produktion muss der Wert None sein"
            )


class TestHealthOhneEinzelwerte:
    def test_health_gibt_nur_den_status_heraus(self):
        funktion = [
            n for n in ast.walk(_baum())
            if isinstance(n, ast.AsyncFunctionDef) and n.name == "health_check"
        ]
        assert len(funktion) == 1, "health_check nicht eindeutig gefunden"
        rueckgaben = [
            r.value for r in ast.walk(funktion[0])
            if isinstance(r, ast.Return) and isinstance(r.value, ast.Dict)
        ]
        assert rueckgaben, "health_check gibt kein Dict zurueck, der Test prueft dann nichts"
        for d in rueckgaben:
            schluessel = {k.value for k in d.keys if isinstance(k, ast.Constant)}
            zu_viel = schluessel - HEALTH_ERLAUBT
            assert not zu_viel, f"/health nennt ohne Anmeldung: {sorted(zu_viel)}"
