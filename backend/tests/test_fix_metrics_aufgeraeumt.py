"""Die tote Messmechanik bleibt weg — und generated_fixes bleibt da.

`fix_acceptance_metrics` und `POST /api/v2/fixes/{fix_id}/outcome` wurden am
04.09.2026 entfernt: registriert, erreichbar, funktionsfaehig und ohne einen
einzigen Aufrufer, Tabelle seit Juli auf 0 Zeilen.

Der zweite Teil dieser Tests ist der wichtigere: `generated_fixes` sieht
genauso leer aus (0 Zeilen), ist aber der verdrahtete Weg, den das Dashboard
ueber /generate, /export, /history und /limits benutzt. Wer beim naechsten
Aufraeumen nur auf den Fuellstand schaut, loescht die Fix-Erzeugung mit.
"""

import os
import re
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def quelltext(*teile):
    return open(os.path.join(BACKEND, *teile), encoding="utf-8").read()


class TestToteMechanikIstWeg:
    def test_kein_zugriff_mehr_auf_die_tabelle(self):
        s = quelltext("fix_routes.py")
        assert "INSERT INTO fix_acceptance_metrics" not in s
        assert "FROM fix_acceptance_metrics" not in s

    def test_endpunkt_und_modell_sind_weg(self):
        s = quelltext("fix_routes.py")
        assert "record_fix_outcome" not in s
        assert "FixOutcomeRequest" not in s
        assert '"/{fix_id}/outcome"' not in s

    def test_kein_anderes_modul_greift_zu(self):
        treffer = []
        for wurzel, _, dateien in os.walk(BACKEND):
            if "alembic" in wurzel or "/tests" in wurzel or "__pycache__" in wurzel:
                continue
            for d in dateien:
                if not d.endswith(".py"):
                    continue
                pfad = os.path.join(wurzel, d)
                inhalt = open(pfad, encoding="utf-8", errors="replace").read()
                # Der Grabsteinkommentar nennt den Namen absichtlich.
                if re.search(r"(INSERT INTO|FROM|UPDATE)\s+fix_acceptance_metrics", inhalt):
                    treffer.append(pfad)
        assert not treffer, f"Zugriff geblieben in: {treffer}"


class TestWasBleibenMuss:
    """generated_fixes ist ebenfalls leer — aber lebendig."""

    @pytest.mark.parametrize("route", [
        '"/generate"', '"/export"', '"/history"', '"/limits"',
        '"/{fix_id}/download/{filename}"', '"/health"',
    ])
    def test_benutzte_routen_stehen_noch(self, route):
        assert route in quelltext("fix_routes.py"), f"Route {route} fehlt"

    def test_generated_fixes_wird_weiter_beschrieben(self):
        s = quelltext("fix_routes.py")
        assert "INSERT INTO generated_fixes" in s

    def test_generated_fixes_wird_weiter_gelesen(self):
        assert "FROM generated_fixes" in quelltext("export_service.py")


class TestMigration:
    def test_migration_loescht_nur_eine_leere_tabelle(self):
        """Sonst gingen Daten verloren, falls doch jemand angefangen hat zu
        schreiben."""
        s = quelltext("alembic", "versions", "20260904_0020_drop_fix_acceptance_metrics.py")
        assert "SELECT count(*) FROM fix_acceptance_metrics" in s
        assert "raise RuntimeError" in s

    def test_migration_ist_umkehrbar(self):
        s = quelltext("alembic", "versions", "20260904_0020_drop_fix_acceptance_metrics.py")
        assert "def downgrade" in s
        assert "create_table" in s

    def test_migration_haengt_am_richtigen_vorgaenger(self):
        s = quelltext("alembic", "versions", "20260904_0020_drop_fix_acceptance_metrics.py")
        assert 'down_revision: Union[str, None] = "0019_rule_review_queue"' in s

    def test_migration_faesst_generated_fixes_nicht_an(self):
        s = quelltext("alembic", "versions", "20260904_0020_drop_fix_acceptance_metrics.py")
        assert "drop_table(\"generated_fixes\")" not in s
        assert "DROP TABLE generated_fixes" not in s
