"""
Tests für den Prüfnachweis.

Das Protokoll ist das Verkaufsargument — und zugleich das größte Risiko: Wer
Zahlen veröffentlicht, die sich nicht halten lassen, ist als
Compliance-Anbieter erledigt. Die Tests hier sichern deshalb vor allem, was
NICHT darin stehen darf.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from compliance_engine.nachweis_generator import (  # noqa: E402
    NICHT_MECHANISCH, baue_nachweis, erklaerung_aus_nachweis, nachweis_token,
)

VORHER = {"color-contrast": 11, "region": 20, "link-name": 4, "nested-interactive": 2}
NACHHER = {"region": 3, "nested-interactive": 2}


def _nachweis(**kw):
    grund = dict(
        site_id="beispiel-de", site_url="https://beispiel.de",
        messung_vorher=VORHER, messung_nachher=NACHHER,
        fixes=[{"regel": "color-contrast", "attribut": "color", "selector": ".x",
                "begruendung": "Kontrast 3,1:1 auf 4,6:1 angehoben."}],
        alt_texte_live=9, gemessen_am="2026-08-07 09:00",
    )
    grund.update(kw)
    return baue_nachweis(**grund)


class TestZahlen:
    def test_summe_stimmt(self):
        n = _nachweis()
        assert n["summe"] == {"vorher": 37, "nachher": 5, "behoben": 32, "quote": 86}

    def test_je_regel_nach_wirkung_sortiert(self):
        n = _nachweis()
        assert n["je_regel"][0]["regel"] == "region"
        assert n["je_regel"][0]["behoben"] == 17

    def test_ohne_befunde_keine_division_durch_null(self):
        n = _nachweis(messung_vorher={}, messung_nachher={})
        assert n["summe"]["quote"] == 0


class TestLueckenWerdenBenannt:
    def test_offene_regeln_tragen_einen_grund(self):
        """Ein Protokoll, das seine Lücken verschweigt, ist ein Siegel."""
        n = _nachweis()
        offen = {o["regel"]: o["grund"] for o in n["offen"]}
        assert "nested-interactive" in offen
        assert "Strukturfehler" in offen["nested-interactive"]

    def test_unbekannte_regel_bekommt_trotzdem_einen_grund(self):
        n = _nachweis(messung_vorher={"irgendwas-neues": 3},
                      messung_nachher={"irgendwas-neues": 3})
        assert n["offen"][0]["grund"]

    def test_behobene_regeln_stehen_nicht_unter_offen(self):
        n = _nachweis()
        assert "color-contrast" not in {o["regel"] for o in n["offen"]}

    def test_jede_nicht_mechanische_regel_hat_eine_begruendung(self):
        assert all(len(g) > 40 for g in NICHT_MECHANISCH.values())


class TestMethodeIstNachvollziehbar:
    def test_werkzeug_regelsatz_und_zeitpunkt_stehen_drin(self):
        n = _nachweis()
        assert "axe-core" in n["pruefwerkzeug"]
        assert "WCAG 2.1 AA" in n["regelsatz"]
        assert n["gemessen_am"] == "2026-08-07 09:00"

    def test_die_nachmessung_wird_erklaert(self):
        """Der eigentliche Unterschied zum Markt gehört ins Protokoll."""
        n = _nachweis()
        assert "erneut" in n["methode"] and "bestanden" in n["methode"]

    def test_jede_reparatur_traegt_ihre_begruendung(self):
        n = _nachweis()
        assert n["reparaturen"][0]["warum"]


class TestErklaerung:
    def test_keine_konformitaetsbehauptung(self):
        """
        Eine automatisierte Prüfung kann keine Konformität bescheinigen. Eine
        falsche Erklärung ist bei einem Compliance-Anbieter der teuerste
        Fehler überhaupt.
        """
        text = erklaerung_aus_nachweis(_nachweis(), "Muster GmbH", "info@beispiel.de")
        assert "vollständige Konformität wird deshalb nicht erklärt" in text
        assert "vollständig barrierefrei" not in text
        assert "konform" not in text.lower().replace("konformität", "")

    def test_bfsg_pflichtangaben_sind_enthalten(self):
        text = erklaerung_aus_nachweis(_nachweis(), "Muster GmbH", "info@beispiel.de")
        for pflicht in ("Geltungsbereich", "Stand der Bewertung",
                        "Nicht barrierefreie Inhalte", "Feedback und Kontakt"):
            assert pflicht in text, pflicht

    def test_offene_punkte_stehen_in_der_erklaerung(self):
        text = erklaerung_aus_nachweis(_nachweis(), "Muster GmbH", "info@beispiel.de")
        assert "nested-interactive" in text

    def test_bildbeschreibungen_werden_erwaehnt(self):
        """axe sieht sie nicht — die Erklärung soll sie trotzdem ausweisen."""
        text = erklaerung_aus_nachweis(_nachweis(), "Muster GmbH", "info@beispiel.de")
        assert "9 Bildbeschreibungen" in text.replace("**", "")

    def test_ohne_offene_punkte_wird_das_gesagt(self):
        n = _nachweis(messung_nachher={})
        text = erklaerung_aus_nachweis(n, "Muster GmbH", "info@beispiel.de")
        assert "keine offenen" in text

    def test_nachweis_url_erscheint_nur_wenn_vorhanden(self):
        ohne = erklaerung_aus_nachweis(_nachweis(), "M", "k@b.de")
        mit = erklaerung_aus_nachweis(_nachweis(), "M", "k@b.de",
                                      "https://complyo.de/nachweis/abc")
        assert "Nachprüfbarkeit" not in ohne
        assert "https://complyo.de/nachweis/abc" in mit


class TestToken:
    def test_stabil_fuer_dieselbe_site(self):
        """Der Link steht in der Erklärung — er darf sich nicht ändern."""
        assert nachweis_token("a-de", "geheim") == nachweis_token("a-de", "geheim")

    def test_verschieden_je_site(self):
        assert nachweis_token("a-de", "geheim") != nachweis_token("b-de", "geheim")

    def test_ohne_geheimnis_kein_token(self):
        """Lieber kein öffentlicher Nachweis als einer mit ratbarem Schlüssel."""
        assert nachweis_token("a-de", "") == ""

    def test_lang_genug_gegen_raten(self):
        assert len(nachweis_token("a-de", "geheim")) == 32
