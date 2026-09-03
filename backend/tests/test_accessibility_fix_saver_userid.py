"""
Tests fuer die user_id-Normalisierung in der Fix-Speicherung.

Hintergrund: Die accessibility_*-Tabellen trugen eine uuid-Spalte, obwohl
users.id integer ist. Jeder Insert scheiterte, der Fehler wurde geloggt und
mit `continue` verschluckt — vom 2026-06-25 bis 2026-08-04 wurde kein einziger
KI-Alt-Text gespeichert. Nach der Schema-Migration reichten die Aufrufer den
Wert weiterhin als String durch (`str(user_id)` in public_routes), was asyncpg
mit "'str' object cannot be interpreted as an integer" ablehnte.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from accessibility_fix_saver import _als_user_id


class TestUserIdNormalisierung:
    def test_string_wird_zahl(self):
        """Der konkrete Produktionsfall: public_routes uebergibt str(user_id)."""
        assert _als_user_id("5") == 5

    def test_zahl_bleibt_zahl(self):
        assert _als_user_id(5) == 5

    def test_leerzeichen_werden_entfernt(self):
        assert _als_user_id("  42  ") == 42

    def test_none_bleibt_none(self):
        assert _als_user_id(None) is None

    def test_leerer_string_wird_none(self):
        assert _als_user_id("") is None
        assert _als_user_id("   ") is None

    def test_unkonvertierbares_wird_none_statt_absturz(self):
        """
        Ein fehlender Nutzerbezug ist besser als ein abgebrochener Insert —
        die Fixes haengen fachlich an site_id, nicht an user_id.
        """
        assert _als_user_id("550e8400-e29b-41d4-a716-446655440000") is None
        assert _als_user_id("keine-zahl") is None

    def test_negative_und_grosse_zahlen(self):
        assert _als_user_id("-1") == -1
        assert _als_user_id("2147483647") == 2147483647
