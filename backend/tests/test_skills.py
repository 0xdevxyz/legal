"""Die Belegpflicht muss durchgesetzt werden, nicht nur dokumentiert.

Von 159 automatisch erzeugten Prüfregeln sind 124 wieder abgeschaltet worden.
Sie waren **alle freigegeben** — einem gut formulierten Satz sieht niemand an,
dass er erfunden ist. Die Admin-Freigabe allein fängt das nicht ab.

Deshalb prüft dieses Modul drei Regeln, und diese Tests prüfen, dass es sie
wirklich durchsetzt statt sie nur zu erwähnen.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import skills


def skill(**felder):
    basis = {
        "befundtyp": "bild-ohne-alt-text",
        "verfahren": "vorschlag",
        "niemals_bei": ["alt bereits gesetzt"],
        "status": "vorschlag",
        "belege": {},
    }
    basis.update(felder)
    return basis


class TestForm:
    def test_vollstaendiger_skill_hat_keine_formfehler(self):
        assert skills.pruefe_form(skill()) == []

    @pytest.mark.parametrize("feld", ["befundtyp", "verfahren", "niemals_bei", "status"])
    def test_pflichtfelder(self, feld):
        s = skill()
        del s[feld]
        assert any(feld in f for f in skills.pruefe_form(s))

    def test_grenzen_sind_pflicht(self):
        """Ein Verfahren ohne benannte Grenzen wird angewandt, wo es nicht
        hingehört — die teuerste Sorte."""
        assert skills.pruefe_form(skill(niemals_bei=[])) != []
        assert skills.pruefe_form(skill(niemals_bei=None)) != []

    def test_unbekannter_zustand_faellt_auf(self):
        assert skills.pruefe_form(skill(status="halbwegs")) != []

    def test_unbekanntes_verfahren_faellt_auf(self):
        assert skills.pruefe_form(skill(verfahren="magie")) != []


class TestBelegpflicht:
    def test_ohne_belege_kein_aktiv(self):
        erlaubt, grund = skills.darf_aktiv_sein(skill())
        assert erlaubt is False
        assert "Meinung" in grund

    def test_zu_wenige_belege_reichen_nicht(self):
        s = skill(belege={"angenommen": 3, "abgelehnt": 0})
        erlaubt, grund = skills.darf_aktiv_sein(s)
        assert erlaubt is False
        assert "3 Entscheidungen" in grund

    def test_knapp_unter_der_schwelle(self):
        """Gegenprobe an der Kante."""
        s = skill(belege={"angenommen": skills.BELEGE_MINDESTENS - 1, "abgelehnt": 0})
        assert skills.darf_aktiv_sein(s)[0] is False

    def test_genug_belege_und_gute_quote(self):
        s = skill(belege={"angenommen": 40, "abgelehnt": 5})
        erlaubt, grund = skills.darf_aktiv_sein(s)
        assert erlaubt is True
        assert "45 Entscheidungen" in grund

    def test_schlechte_quote_trotz_vieler_belege(self):
        """Viele Entscheidungen helfen nicht, wenn das Verfahren danebenliegt."""
        s = skill(belege={"angenommen": 20, "abgelehnt": 30})
        erlaubt, grund = skills.darf_aktiv_sein(s)
        assert erlaubt is False
        assert "daneben" in grund

    def test_formfehler_schlaegt_belege(self):
        """Ein formal kaputter Skill darf auch mit tausend Belegen nicht aktiv
        sein."""
        s = skill(niemals_bei=[], belege={"angenommen": 1000, "abgelehnt": 0})
        assert skills.darf_aktiv_sein(s)[0] is False


class TestRueckzug:
    def test_aktiver_skill_mit_schlechter_quote_wird_zurueckgezogen(self):
        s = skill(status="aktiv", belege={"angenommen": 20, "abgelehnt": 30})
        assert skills.zustand_nach_belegen(s) == "zurueckgezogen"

    def test_aktiver_skill_mit_guter_quote_bleibt(self):
        s = skill(status="aktiv", belege={"angenommen": 40, "abgelehnt": 5})
        assert skills.zustand_nach_belegen(s) == "aktiv"

    def test_vorschlag_wird_nicht_automatisch_aktiv(self):
        """Automatik darf hochstufen WOLLEN, nicht hochstufen. Die Freigabe
        bleibt beim Menschen."""
        s = skill(status="vorschlag", belege={"angenommen": 40, "abgelehnt": 5})
        assert skills.zustand_nach_belegen(s) == "vorschlag"

    def test_aktiver_skill_ohne_belege_wird_zurueckgezogen(self):
        s = skill(status="aktiv")
        assert skills.zustand_nach_belegen(s) == "zurueckgezogen"


class TestBelegeAusLernstand:
    def test_zahlen_kommen_aus_der_auswertung(self):
        """Handgeschriebene Belege waeren wieder nur eine Behauptung."""
        lernstand = {"befundtypen": [{
            "befundtyp": "bild-ohne-alt-text",
            "vorgeschlagen": 412, "angenommen": 389, "abgelehnt": 23,
            "zuletzt": "2026-11-02T10:00:00",
            "ablehngruende": [{"grund": "Zu allgemein", "anzahl": 12}],
        }]}
        b = skills.belege_aus_lernstand("bild-ohne-alt-text", lernstand)
        assert b["angenommen"] == 389
        assert b["haeufigster_ablehngrund"] == "Zu allgemein"

    def test_unbekannter_typ_bleibt_leer(self):
        assert skills.belege_aus_lernstand("gibt-es-nicht", {"befundtypen": []}) == {}


class TestAblage:
    def test_leere_ablage_faellt_nicht_um(self, tmp_path):
        assert skills.lade_alle(str(tmp_path)) == []

    def test_fehlendes_verzeichnis_faellt_nicht_um(self):
        assert skills.lade_alle("/gibt/es/nicht") == []

    def test_alle_mitgelieferten_skills_sind_formal_in_ordnung(self):
        """Das Eichmass muss selbst dem Format genuegen — sonst taugt es
        nicht als Vorlage."""
        pfad = os.path.join(
            os.path.dirname(__file__), "..", "..", "knowledge", "skills")
        if not os.path.isdir(pfad):
            pytest.skip("Skill-Ablage nicht im Testbild")
        geladen = skills.lade_alle(pfad)
        assert geladen, "Ablage ist leer"
        for s in geladen:
            assert s["formfehler"] == [], f"{s['datei']}: {s['formfehler']}"

    def test_kein_mitgelieferter_skill_ist_aktiv(self):
        """Sie sind aus Musterdateien ueberfuehrt, nicht aus Entscheidungen
        gewachsen. Waere einer `aktiv`, waere die Belegpflicht eine Fassade."""
        pfad = os.path.join(
            os.path.dirname(__file__), "..", "..", "knowledge", "skills")
        if not os.path.isdir(pfad):
            pytest.skip("Skill-Ablage nicht im Testbild")
        for s in skills.lade_alle(pfad):
            assert s["status"] == "vorschlag", f"{s['datei']} steht auf {s['status']}"
            assert skills.darf_aktiv_sein(s)[0] is False
