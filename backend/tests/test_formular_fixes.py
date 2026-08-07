"""
Tests für Formularfelder, Seitentitel und ARIA-Elternrollen.

Alle Beispiele stammen aus den echten Fundstellen der Bestandsmessung vom
06.08.2026 — inklusive des Falls, der die Zielgröße verschoben hat: einer der
fünf `label`-Verstöße war ein Honeypot und brauchte nie ein Label.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from compliance_engine.formular_fixes import (  # noqa: E402
    beschriftung_fuer_feld, ist_honeypot, titel_aus_seite,
)


class TestHoneypot:
    def test_echter_fall_wird_erkannt(self):
        """fv-wolkenburg.de: <input name="spamify_hp_5147404f" tabindex="-1">."""
        assert ist_honeypot("spamify_hp_5147404f", "spamify-hp-field", "-1")

    def test_honeypot_bekommt_kein_label_sondern_aria_hidden(self):
        r = beschriftung_fuer_feld({
            "name": "spamify_hp_5147404f", "class": "spamify-hp-field",
            "tabindex": "-1",
        })
        assert r["honeypot"] is True
        assert r["label"] is None

    def test_uebliche_koedernamen(self):
        for name in ("honeypot", "url_check", "leave-blank", "comment_url"):
            assert ist_honeypot(name), name

    def test_sprechendes_feld_ist_kein_koeder(self):
        """Auch mit tabindex=-1 nicht: der Name sagt, wozu es da ist."""
        assert not ist_honeypot("email", "", "-1")
        assert not ist_honeypot("nachricht", "form-field", "")


class TestFeldbeschriftung:
    def test_suchfeld_mit_vorbelegung(self):
        """naturheilzentrum-freitag.de: <input id="s" value="Enter Keyword">."""
        r = beschriftung_fuer_feld({"name": "s", "type": "text",
                                    "value": "Enter Keyword"})
        assert r["label"] == "Enter Keyword"

    def test_feldname_wird_uebersetzt(self):
        """doener-bistro-baku.de: <select name="anlass">."""
        r = beschriftung_fuer_feld({"name": "anlass"})
        assert r["label"] == "Anlass"
        assert r["quelle"] == "Feldname"

    def test_eingabetyp_schlaegt_nichtssagenden_namen(self):
        """reinhardt.coffee: name="field2" mit data-val-type="email"."""
        r = beschriftung_fuer_feld({"name": "field2", "data-val-type": "email"})
        assert r["label"] == "E-Mail-Adresse"

    def test_platzhalter_hat_vorrang(self):
        r = beschriftung_fuer_feld({"name": "field1", "placeholder": "Ihr Name"})
        assert r["label"] == "Ihr Name" and r["quelle"] == "placeholder"

    def test_text_davor_als_letzte_quelle(self):
        r = beschriftung_fuer_feld({"name": "field4"}, umgebungstext="Ihre Nachricht:")
        assert r["label"] == "Ihre Nachricht"
        assert r["konfidenz"] <= 0.6

    def test_zusammengesetzter_name(self):
        assert beschriftung_fuer_feld({"name": "kontakt_telefon"})["label"] == "Telefonnummer"

    def test_ohne_jeden_hinweis_kein_vorschlag(self):
        """Ein falsch benanntes Feld schickt Nutzer in die Irre."""
        assert beschriftung_fuer_feld({"name": "field1", "type": "text"}) is None

    def test_leerer_umgebungstext_hilft_nicht(self):
        assert beschriftung_fuer_feld({"name": "xy"}, umgebungstext="   ") is None

    def test_zu_langer_umgebungstext_wird_verworfen(self):
        lang = "Bitte fuellen Sie dieses Formular vollstaendig aus " * 3
        assert beschriftung_fuer_feld({"name": "xy"}, umgebungstext=lang) is None




class TestSeitentitel:
    def test_h1_wird_zum_titel(self):
        assert titel_aus_seite("Bäckerei Müller — Frische seit 1920", "", "x.de") \
            == "Bäckerei Müller — Frische seit 1920"

    def test_og_titel_als_zweite_wahl(self):
        assert titel_aus_seite("", "Ferienpark Waldenburg", "x.de") == "Ferienpark Waldenburg"

    def test_domain_als_letzter_ausweg(self):
        assert titel_aus_seite("", "", "www.boehme-energie.com") == "boehme-energie.com"

    def test_zu_lange_ueberschrift_wird_verworfen(self):
        assert titel_aus_seite("x" * 200, "", "beispiel.de") == "beispiel.de"

    def test_ohne_alles_kein_titel(self):
        assert titel_aus_seite("", "", "") is None


class TestEigeneAttribute:
    def test_zweck_steht_im_attributnamen(self):
        """rhino.cafe: <select update-hours hrs-min="0" hrs-max="24"> — kein name."""
        r = beschriftung_fuer_feld({"update-hours": "", "hrs-min": "0", "hrs-max": "24"})
        assert r["label"] == "Stunden"

    def test_minuten_ebenso(self):
        r = beschriftung_fuer_feld({"update-minutes": "", "minute-step": "15"})
        assert r["label"] == "Minuten"

    def test_bekannter_name_schlaegt_das_attribut(self):
        r = beschriftung_fuer_feld({"name": "anlass", "update-hours": ""})
        assert r["label"] == "Anlass"


class TestWasBewusstOffenBleibt:
    def test_der_grund_steht_im_modul(self):
        """
        `aria-required-parent` wird nicht behoben — und zwar nicht aus
        Vergesslichkeit. Der Grund muss im Quelltext stehen, sonst ruestet ihn
        jemand nach und bricht die Theme-Skripte.
        """
        import compliance_engine.formular_fixes as m
        assert "doppelt vergebene" in (m.__doc__ or "")
        assert "role=\"tablist\"" in (m.__doc__ or "") or "tablist" in (m.__doc__ or "")
