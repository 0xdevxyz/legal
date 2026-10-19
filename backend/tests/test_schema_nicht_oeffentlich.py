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

Zweiter Teil (13.10.2026, nach dem Schliessen des Schemas): dieselbe Landkarte
steckte auch in den kleinen Betriebsrouten. `/api/auth/health`,
`/api/user/health`, `/api/v2/fixes/health`, `/api/cookie-compliance/health`
und `/` nannten ohne Anmeldung, welche Dienste initialisiert sind, wie viele
Cookie-Dienste aktiv sind, ob KI konfiguriert ist und in welcher Umgebung das
Backend laeuft; die Cookie-Route gab bei einem Fehler `str(e)` heraus.
`POST /api/auth/admin/reset-master-password` hing nur an einem Schluessel in
der URL und war ohne `ADMIN_KEY` tot. Diese Teile lesen jede Python-Datei des
Backends ausser Tests und zaehlen, wie viele sie wirklich gesehen haben.
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


# ---------------------------------------------------------------------------
# Teil 2: alle Routen des Backends
# ---------------------------------------------------------------------------

METHODEN = {"get", "post", "put", "delete", "patch"}

# Was eine Betriebsroute ohne Anmeldung nennen darf: den Gesamtzustand.
# Keine Teildienste (`*_initialized`), keine Zahlen (`active_services`), keine
# Konfiguration (`ai_enabled`, `environment`), keine Fehlertexte (`error`).
BETRIEB_ERLAUBT = {"status", "success", "timestamp", "service"}

# Diese Dateien verlangen Anmeldung fuer jede Route; dort darf es mehr sein.
BETRIEB_AUSNAHME_DATEIEN = {"admin_routes.py"}


def _backend_dateien():
    """Alle Python-Dateien des Backends ausser Tests und Sicherungen."""
    treffer = []
    for ordner, unterordner, namen in os.walk(BACKEND):
        unterordner[:] = [
            u for u in unterordner
            if u not in ("tests", "__pycache__", "node_modules") and not u.startswith(".")
        ]
        treffer.extend(os.path.join(ordner, n) for n in namen if n.endswith(".py"))
    return treffer


def _routen(pfad):
    """(Methode, Pfad, Funktion) je Funktion mit @x.get("/pfad") und Verwandten."""
    with open(pfad, encoding="utf-8") as f:
        baum = ast.parse(f.read())
    for n in ast.walk(baum):
        if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for d in n.decorator_list:
            if (
                isinstance(d, ast.Call)
                and isinstance(d.func, ast.Attribute)
                and d.func.attr in METHODEN
                and d.args
                and isinstance(d.args[0], ast.Constant)
                and isinstance(d.args[0].value, str)
            ):
                yield d.func.attr.upper(), d.args[0].value, n


def _alle_routen():
    dateien = _backend_dateien()
    routen = []
    for datei in dateien:
        for methode, pfad, funktion in _routen(datei):
            routen.append((os.path.basename(datei), methode, pfad, funktion))
    return dateien, routen


class TestKeineSchluesselRouteInDerUrl:
    def test_keine_route_nimmt_admin_key_oder_setzt_das_master_passwort_zurueck(self):
        dateien, routen = _alle_routen()
        # Zaehlprobe: ein Waechter, der kaum etwas liest, beweist nichts.
        assert len(dateien) >= 200, f"nur {len(dateien)} Backend-Dateien gelesen"
        assert len(routen) >= 250, f"nur {len(routen)} Routen gefunden"
        verstoesse = []
        for datei, methode, pfad, funktion in routen:
            namen = [a.arg for a in funktion.args.args + funktion.args.kwonlyargs]
            if "admin_key" in namen:
                verstoesse.append(f"{datei}: {methode} {pfad} nimmt admin_key")
            if "reset-master-password" in pfad:
                verstoesse.append(f"{datei}: {methode} {pfad}")
        assert not verstoesse, "Schluessel in der URL ist kein Zugangsschutz:\n" + "\n".join(verstoesse)


class TestOeffentlicheBetriebsrouten:
    def test_health_und_wurzel_nennen_nur_den_gesamtzustand(self):
        _dateien, routen = _alle_routen()
        betrieb = [
            (datei, pfad, funktion)
            for datei, methode, pfad, funktion in routen
            if methode == "GET"
            and datei not in BETRIEB_AUSNAHME_DATEIEN
            and (pfad.endswith("/health") or (datei == "main_production.py" and pfad == "/"))
        ]
        # auth, user, fixes, cookie, public, main /health, main /
        assert len(betrieb) >= 7, f"nur {len(betrieb)} Betriebsrouten gefunden: {[(d, p) for d, p, _ in betrieb]}"
        verstoesse = []
        for datei, pfad, funktion in betrieb:
            rueckgaben = [
                r.value for r in ast.walk(funktion)
                if isinstance(r, ast.Return) and isinstance(r.value, ast.Dict)
            ]
            assert rueckgaben, f"{datei}: {pfad} gibt kein Dict zurueck, der Test prueft dann nichts"
            for d in rueckgaben:
                schluessel = {
                    k.value if isinstance(k, ast.Constant) else "<dynamisch>" for k in d.keys
                }
                zu_viel = schluessel - BETRIEB_ERLAUBT
                if zu_viel:
                    verstoesse.append(f"{datei}: GET {pfad} nennt {sorted(zu_viel)}")
        assert not verstoesse, "Ohne Anmeldung nur den Gesamtzustand:\n" + "\n".join(verstoesse)
