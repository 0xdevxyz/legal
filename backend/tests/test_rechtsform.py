"""
Die Rechtsform des Betreibers, nicht die seines Hosters.

Ein Impressum nennt mehrere Unternehmen: den Betreiber, den Hoster, oft die
Agentur und die Bank. Die Pflichten des § 5 DDG treffen den Betreiber.

Im Bestandsdurchlauf vom 09.09.2026 bekam eine Zahnarztpraxis den Befund
"Vorstand/Aufsichtsrat nicht angegeben (AG/SE erkannt)". Ausloeser war der
Hosting-Absatz ihres eigenen Impressums: "IONOS SE". Die Erkennung suchte
case-insensitiv im ROHEN HTML nach \\bse\\b, traf das SE des Hosters und
erklaerte die Praxis zur Societas Europaea. IONOS ist Deutschlands groesster
Massenhoster; dieser Absatz steht in nahezu jedem Impressum.

Dieselbe Fehlerklasse wie "ki" -> "Kindermobiliar" im August, nur in den fest
verdrahteten Pruefungen statt in den deklarativen.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from compliance_engine.checks.impressum_check import (
    erkenne_rechtsform,
    im_handelsregister,
)


def impressum(betreiber: str, extra: str = "") -> str:
    """Ein Impressum im ueblichen deutschen Aufbau: Betreiber, dann Dritte."""
    return f"""
    <html><body>
      <h1>Impressum</h1>
      <h2>Angaben gemäß § 5 DDG</h2>
      <p>{betreiber}<br>Musterstraße 1<br>09648 Mittweida</p>
      <p>Telefon: 03727 12345<br>E-Mail: info@beispiel.de</p>
      {extra}
      <h2>Hosting</h2>
      <p>Anbieter der Website ist:</p>
      <p>IONOS SE<br>Elgendorfer Str. 57<br>56410 Montabaur</p>
      <h2>Bildnachweis</h2>
      <p>Fotos: Getty Images AG</p>
      <h2>Haftung für Inhalte</h2>
      <p>Als Diensteanbieter sind wir gemäß § 7 Abs.1 DDG verantwortlich.</p>
    </body></html>
    """


# --- Der reale Fall -------------------------------------------------------

ZAHNARZT = impressum("Zahnarztpraxis Dr. med. dent. Anna Muster")


class TestFremdeRechtsformZaehltNicht:
    def test_ionos_se_im_hosting_macht_keine_aktiengesellschaft(self):
        formen = erkenne_rechtsform(ZAHNARZT)
        assert formen["ag_se"] is False, "IONOS SE ist der Hoster, nicht der Betreiber"

    def test_getty_images_ag_im_bildnachweis_zaehlt_nicht(self):
        assert erkenne_rechtsform(ZAHNARZT)["ag_se"] is False

    def test_zahnarztpraxis_steht_nicht_im_handelsregister(self):
        assert im_handelsregister(erkenne_rechtsform(ZAHNARZT)) is False


class TestEigeneRechtsformWirdErkannt:
    @pytest.mark.parametrize("name,schluessel", [
        ("Muster Bau GmbH", "gmbh_ug"),
        ("Muster Handels UG (haftungsbeschränkt)", "gmbh_ug"),
        ("Muster Technik AG", "ag_se"),
        ("Muster Europa SE", "ag_se"),
        ("Muster Logistik KG", "ohg_kg"),
        ("Muster Handel OHG", "ohg_kg"),
        ("Muster Handel e.K.", "ohg_kg"),
        ("Turnverein Mittweida e.V.", "ev"),
        ("Muster und Partner GbR", "gbr"),
    ])
    def test_rechtsform_hinter_dem_namen(self, name, schluessel):
        formen = erkenne_rechtsform(impressum(name))
        assert formen[schluessel] is True, f"{name} nicht als {schluessel} erkannt"

    def test_ausgeschriebene_form_wird_erkannt(self):
        assert erkenne_rechtsform(impressum("Muster Aktiengesellschaft"))["ag_se"] is True

    def test_gmbh_steht_im_handelsregister(self):
        assert im_handelsregister(erkenne_rechtsform(impressum("Muster Bau GmbH"))) is True


class TestFreiberuflerUndKleinbetriebe:
    @pytest.mark.parametrize("name", [
        "Zahnarztpraxis Dr. Anna Muster",
        "Naturheilpraxis Sabine Decker",
        "Physiotherapie Müller",
        "Tennisclub Limbach",
        "Bauschlosserei Claus",
        "Konditorei Hörning",
    ])
    def test_kein_handelsregister_verlangt(self, name):
        formen = erkenne_rechtsform(impressum(name))
        assert im_handelsregister(formen) is False, f"{name} braucht keinen HR-Eintrag"

    def test_gbr_steht_nicht_im_handelsregister(self):
        formen = erkenne_rechtsform(impressum("Muster und Partner GbR"))
        assert formen["gbr"] is True
        assert im_handelsregister(formen) is False


class TestMarkupIstKeineAussage:
    def test_klassennamen_erzeugen_keine_rechtsform(self):
        # Klassen wie "elementor-widget-ag" oder Attribute mit "se" sind kein
        # Hinweis auf eine Aktiengesellschaft.
        html = """<html><body>
          <div class="wp-block-ag se-container" data-se="1" lang="se">
            <h1>Impressum</h1><p>Malerbetrieb Krause<br>Dorfstraße 3</p>
          </div></body></html>"""
        formen = erkenne_rechtsform(html)
        assert formen["ag_se"] is False
        assert im_handelsregister(formen) is False

    def test_kilogramm_ist_keine_kommanditgesellschaft(self):
        html = impressum("Hofladen Sommer", extra="<p>Mindestbestellmenge: 5 kg</p>")
        assert erkenne_rechtsform(html)["ohg_kg"] is False
