"""Verworfene Prüfregeln bekommen einen auswertbaren Grund.

Von 159 automatisch erzeugten Checks sind **124 verworfen** — Annahmequote
0,22. Der Grund wurde bisher als Freitext an `generation_notes` angehängt,
hinter die Erzeugungsnotiz. Zwei Folgen:

1. Nicht auswertbar. Aus fünfzig Formulierungen für dasselbe Problem wird kein
   Muster — genau deshalb bekamen die Fix-Vorschläge feste Gründe.
2. Meist gar nicht vorhanden: ein Großteil wurde per Sammelaktion
   `audit-cleanup-2026-07` stillgelegt, ohne jede Begründung.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from legal_change_routes import ABLEHNGRUENDE_REGEL, DismissCheckRequest

BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def quelle(*teile):
    return open(os.path.join(BACKEND, *teile), encoding="utf-8").read()


class TestModell:
    def test_fester_grund_und_freitext_nebeneinander(self):
        r = DismissCheckRequest(grund="Trifft zu oft daneben",
                                reason="'ki' trifft auch Kindermobiliar")
        assert r.grund == "Trifft zu oft daneben"
        assert r.reason.startswith("'ki'")

    def test_beide_freiwillig(self):
        r = DismissCheckRequest()
        assert r.grund is None and r.reason is None


class TestGruendeliste:
    def test_liste_ist_nicht_leer(self):
        assert len(ABLEHNGRUENDE_REGEL) >= 4

    def test_es_gibt_einen_auffangposten(self):
        """Ohne 'Anderer Grund' waehlt man den naechstbesten falschen."""
        assert "Anderer Grund" in ABLEHNGRUENDE_REGEL

    def test_falschtreffer_ist_dabei(self):
        """Das haeufigste Fehlerbild: das Kurz-Stichwort 'ki' traf im August
        'Kindermobiliar' und erzeugte ein Phantomrisiko von 15.000 EUR."""
        assert "Trifft zu oft daneben" in ABLEHNGRUENDE_REGEL


class TestSpeicherung:
    def test_grund_geht_in_eine_eigene_spalte(self):
        s = quelle("legal_change_routes.py")
        assert "dismissal_reason = $4" in s

    def test_freitext_bleibt_im_pruefpfad(self):
        """Die Auswahlliste bildet Nuancen nicht ab — der Freitext ergaenzt
        sie, statt sie zu ersetzen."""
        s = quelle("legal_change_routes.py")
        assert "generation_notes = CASE" in s

    def test_migration_legt_die_spalte_an(self):
        s = quelle("alembic", "versions", "20260905_0023_ablehngrund_pruefregeln.py")
        assert "dismissal_reason" in s
        assert 'down_revision: Union[str, None] = "0022_ablehngrund_dokumentfixes"' in s
        assert "def downgrade" in s


class TestAuswertung:
    def test_lernstand_zaehlt_die_gruende(self):
        s = quelle("lernstand.py")
        assert "dismissal_reason AS grund" in s
        assert "ablehngruende" in s

    def test_lernstand_ignoriert_leere_gruende(self):
        """Ein leerer String waere ein Grund ohne Aussage."""
        s = quelle("lernstand.py")
        assert "dismissal_reason IS NOT NULL AND dismissal_reason <> ''" in s


class TestOberflaeche:
    def _seite(self):
        pfad = os.path.join(BACKEND, "..", "dashboard-react", "src", "app",
                            "admin", "check-review", "page.tsx")
        return open(pfad, encoding="utf-8").read()

    def test_feste_gruende_werden_angeboten(self):
        s = self._seite()
        assert "REGEL_ABLEHNGRUENDE" in s
        assert "Trifft zu oft daneben" in s

    def test_grund_wird_mitgeschickt(self):
        s = self._seite()
        assert "grund: dismissGrund || undefined" in s

    def test_grund_wird_beim_wechsel_zurueckgesetzt(self):
        """Sonst truege der naechste Check den Grund des vorigen — und die
        Auswertung waere still falsch."""
        s = self._seite()
        assert s.count("setDismissGrund(null);") >= 2
