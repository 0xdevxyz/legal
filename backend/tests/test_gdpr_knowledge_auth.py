"""
Auth-Tests für gdpr_api / knowledge_routes / i18n_api / risk_radar_routes
========================================================================

Hintergrund (2026-07-17), Schwesterdatei zu test_cookie_consent_auth.py:

* `gdpr_api.py` — POST /request-deletion und /export-data identifizierten den
  Betroffenen allein über eine E-Mail im Request-Body. Jeder Anonyme konnte
  damit die Daten beliebiger Dritter exportieren ODER löschen lassen.
  GET /retention-info war dasselbe Orakel per Query-Parameter.
* `knowledge_routes.py` — POST /trigger-refresh trug "(Admin)" im Docstring,
  hatte aber keine Dependency: jede Session konnte einen Ingestion-Lauf inkl.
  OpenAI-Kosten auslösen.
* `i18n_api.py` — POST /set-language ("Admin endpoint") ohne Auth.
* `risk_radar_routes.py` — kein einziger Endpunkt hatte Auth; /score gab die
  Issue-Liste (Schwachstellenkarte) beliebiger fremder Domains heraus.

Ausserdem: der `RETURNING COUNT(*)`-Defekt, der den GDPR-Cleanup seit jeher
lahmlegte (Postgres: "aggregate functions are not allowed in RETURNING").

Die statischen Wächter brauchen weder fastapi noch DB — sie sind der
eigentliche Regressionsschutz.
"""
import ast
import glob
import os

import pytest

_BACKEND = os.path.join(os.path.dirname(__file__), "..")

# Routen, die bewusst ohne Login erreichbar bleiben — jeweils mit Begründung.
# NICHTS hier eintragen, das Kundendaten liest/schreibt oder Kosten auslöst.
OEFFENTLICH_GEWOLLT = {
    # gdpr_api.py — statischer Rechtstext, keine personenbezogenen Daten.
    "/privacy-policy",
    # knowledge_routes.py — veröffentlichte Gesetzestexte/Updates aus dem Vault.
    # Ausdrücklich öffentlich (Produktentscheidung), lesend, keine Kundendaten.
    "/updates",
    "/updates/{update_id}",
    "/laws",
    "/search",
    "/stats",
    # i18n_api.py — Übersetzungen/Sprachdetektion für nicht eingeloggte Seiten
    # (Landing, Login). Rein lesend auf statischen Katalogen.
    "/languages",
    "/translations",
    "/text/{key}",
    "/form-validation",
    "/email-templates",
    "/detect-language",
}

_DATEIEN = ["gdpr_api.py", "knowledge_routes.py", "i18n_api.py", "risk_radar_routes.py"]

_ROUTER_NAMEN = {"gdpr_router", "i18n_router", "router"}
_METHODEN = {"get", "post", "patch", "delete", "put"}

# Marker, die eine serverseitig erzwungene Identität belegen.
# `admin_api_key` zählt: gdpr_api._verify_admin prüft ihn gegen ADMIN_API_KEY
# (gleiches Muster wie admin_routes.py).
_AUTH_MARKER = (
    "credentials",
    "current_user",
    "require_admin",
    "get_verified_email",
    "admin_api_key",
)


def _routen(dateiname):
    """Routen per AST einsammeln.

    Bewusst kein Regex: Eine frühere Variante verlangte ein `\\n):` am
    Signatur-Ende und übersprang damit stillschweigend jede einzeilige Signatur
    (`async def get_vault_stats():`) — schlimmer noch, der non-greedy Match lief
    dann in die NÄCHSTE Funktion und schrieb deren Auth-Marker der falschen
    Route gut. Ein Wächter, der Lücken übersieht, ist schlimmer als keiner.
    """
    with open(os.path.join(_BACKEND, dateiname), encoding="utf-8") as fh:
        baum = ast.parse(fh.read())

    for knoten in ast.walk(baum):
        if not isinstance(knoten, (ast.AsyncFunctionDef, ast.FunctionDef)):
            continue
        for deko in knoten.decorator_list:
            if not (isinstance(deko, ast.Call) and isinstance(deko.func, ast.Attribute)):
                continue
            if not isinstance(deko.func.value, ast.Name):
                continue
            if deko.func.value.id not in _ROUTER_NAMEN or deko.func.attr not in _METHODEN:
                continue
            if not (deko.args and isinstance(deko.args[0], ast.Constant)):
                continue
            signatur = ast.unparse(knoten.args)
            geschuetzt = any(marker in signatur for marker in _AUTH_MARKER)
            yield deko.func.attr.upper(), deko.args[0].value, knoten.name, geschuetzt


def _alle_routen():
    for datei in _DATEIEN:
        for eintrag in _routen(datei):
            yield (datei,) + eintrag


class TestOeffentlicheRouten:
    def test_keine_unerwartet_offene_route(self):
        offen = {
            f"{datei}:{pfad}"
            for datei, _, pfad, _, geschuetzt in _alle_routen()
            if not geschuetzt and pfad not in OEFFENTLICH_GEWOLLT
        }
        assert not offen, (
            "Route(n) ohne Auth-Prüfung: "
            + ", ".join(sorted(offen))
            + ". Entweder Depends(get_current_user)/require_admin ergänzen oder — "
            "falls die Route wirklich ohne Login gebraucht wird — mit Begründung "
            "in OEFFENTLICH_GEWOLLT aufnehmen."
        )

    def test_allowlist_ist_nicht_verwaist(self):
        """Schützt die Allowlist davor, zur Legende zu werden."""
        vorhandene = {pfad for _, _, pfad, _, _ in _alle_routen()}
        verwaist = OEFFENTLICH_GEWOLLT - vorhandene
        assert not verwaist, f"Allowlist nennt nicht (mehr) existierende Routen: {sorted(verwaist)}"

    def test_router_ueberhaupt_geparst(self):
        """Ein kaputtes Regex darf nicht als 'alles sauber' durchgehen."""
        for datei in _DATEIEN:
            assert list(_routen(datei)), f"Keine Route in {datei} erkannt — Pattern prüfen"

    @pytest.mark.parametrize(
        "datei,pfad",
        [
            ("gdpr_api.py", "/request-deletion"),
            ("gdpr_api.py", "/export-data"),
            ("gdpr_api.py", "/retention-info"),
            ("gdpr_api.py", "/admin/update-retention"),
            ("gdpr_api.py", "/admin/cleanup-status"),
            ("gdpr_api.py", "/admin/run-cleanup"),
            ("knowledge_routes.py", "/trigger-refresh"),
            ("i18n_api.py", "/set-language"),
            ("risk_radar_routes.py", "/score"),
            ("risk_radar_routes.py", "/early-warnings"),
            ("risk_radar_routes.py", "/summary"),
        ],
    )
    def test_sensible_route_ist_geschuetzt(self, datei, pfad):
        """Namentlich die Routen, die 2026-07-17 offen standen."""
        treffer = [g for _, p, _, g in _routen(datei) if p == pfad]
        assert treffer, f"Route {datei}:{pfad} nicht gefunden — Test anpassen oder Route wiederherstellen"
        assert all(treffer), f"Route {datei}:{pfad} ist wieder ohne Auth-Prüfung"


class TestBetroffenerKommtAusDemToken:
    """Der Kernbefund: die E-Mail darf nicht aus dem Request stammen."""

    def _quelle(self):
        with open(os.path.join(_BACKEND, "gdpr_api.py"), encoding="utf-8") as fh:
            return fh.read()

    def test_request_models_haben_kein_email_feld(self):
        """Per AST auf FELDER prüfen — eine reine Textsuche nach "email" schlug
        schon am Kommentar "siehe get_verified_email" an."""
        baum = ast.parse(self._quelle())
        gefunden = set()
        for knoten in ast.walk(baum):
            if not isinstance(knoten, ast.ClassDef):
                continue
            if knoten.name not in ("DataDeletionRequest", "DataExportRequest"):
                continue
            gefunden.add(knoten.name)
            felder = {
                s.target.id
                for s in knoten.body
                if isinstance(s, ast.AnnAssign) and isinstance(s.target, ast.Name)
            }
            assert "email" not in felder, (
                f"{knoten.name} nimmt wieder eine E-Mail entgegen — der Betroffene "
                "muss aus dem JWT kommen (get_verified_email), sonst ist die "
                "IDOR-Lücke zurück."
            )
        assert gefunden == {"DataDeletionRequest", "DataExportRequest"}, (
            f"Request-Models nicht gefunden: {gefunden} — Test anpassen"
        )

    def test_kein_request_email_zugriff(self):
        assert "request.email" not in self._quelle(), (
            "gdpr_api.py liest wieder request.email — Betroffener muss aus dem Token kommen"
        )

    def test_retention_info_hat_keinen_email_query(self):
        src = self._quelle()
        block = src.split("async def get_retention_information(")[1].split("\n):")[0]
        assert "Query(" not in block, (
            "retention-info nimmt wieder eine E-Mail per Query entgegen "
            "(Auskunfts-Orakel über Dritte)"
        )


class TestKeinReturningCount:
    """Postgres: 'aggregate functions are not allowed in RETURNING'.

    `DELETE ... RETURNING COUNT(*)` wirft immer — der tägliche GDPR-Cleanup ist
    daran bei der ersten Anweisung gescheitert und hat nie etwas gelöscht.
    Korrekt: conn.execute() + Command-Tag parsen (_parse_delete_count).
    """

    # backup_retention.py trägt denselben Defekt (Z. 17/20/23), ist aber toter
    # Code: ein 37-Zeilen-Standalone-Skript mit __main__-Block, das niemand
    # importiert und kein Cron/systemd-Unit aufruft (verifiziert 2026-07-17).
    # Bewusst nicht angefasst — hier nur dokumentiert, damit die Ausnahme nicht
    # als Versehen durchgeht. Wird das Skript je reaktiviert, muss es vorher den
    # _parse_delete_count-Weg gehen und aus dieser Liste verschwinden.
    _TOTER_CODE = {"backup_retention.py"}

    def test_kein_returning_count_im_backend(self):
        treffer = []
        for pfad in glob.glob(os.path.join(_BACKEND, "*.py")):
            name = os.path.basename(pfad)
            if name.startswith("_archive") or name in self._TOTER_CODE:
                continue
            with open(pfad, encoding="utf-8") as fh:
                for nr, zeile in enumerate(fh, 1):
                    if "RETURNING COUNT(" in zeile.upper():
                        treffer.append(f"{os.path.basename(pfad)}:{nr}")
        assert not treffer, (
            "RETURNING COUNT( ist in Postgres unzulässig und lässt das Statement "
            "immer scheitern. Gefunden in: " + ", ".join(treffer)
        )


class TestParseDeleteCount:
    """Verhalten des Helfers. Braucht das echte Modul -> läuft im Backend-Container."""

    def test_command_tag_wird_geparst(self):
        mp = pytest.importorskip("main_production")
        assert mp._parse_delete_count("DELETE 42") == 42
        assert mp._parse_delete_count("DELETE 0") == 0

    def test_unerwartetes_tag_wirft_nicht(self):
        """Der Cleanup darf nicht am Logging der Zeilenzahl sterben."""
        mp = pytest.importorskip("main_production")
        assert mp._parse_delete_count("") == 0
        assert mp._parse_delete_count("DELETE") == 0
        assert mp._parse_delete_count(None) == 0
