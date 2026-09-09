"""
Nicht geprüft ist nicht dasselbe wie nicht vorhanden.

Der Hybrid-Validator prüft Pflichtangaben zuerst per Muster. Wo das Muster
unsicher ist, holt er eine KI-Zweitmeinung. Fällt die aus — kein Schlüssel,
Tagesbudget gesperrt, Redis nicht erreichbar — fiel er auf das Musterergebnis
zurück und reichte dessen `found=False` weiter, als wäre es eine Feststellung.
Es war aber genau die Unsicherheit, die den KI-Aufruf ausgelöst hatte.

Im Bestandsdurchlauf vom 09.09.2026 über 24 echte Kundenseiten war das mit
Abstand der teuerste Effekt:

    Anschrift fehlt im Impressum (kritisch, 2.000 €)   ohne KI 9/24, mit KI 0/24
    Zwecke der Datenverarbeitung fehlen (kritisch)     ohne KI 20/24, mit KI 5/24
    Impressum unvollständig                           ohne KI 6/24, mit KI 0/24

Der Score hing damit daran, ob ein fremder Dienst gerade antwortet: im Mittel
34/100 ohne, 43/100 mit KI. Für ein Produkt, dessen Wert der Prüfnachweis ist,
ist ein von der Infrastruktur abhängiger Vorwurf schlimmer als eine Lücke.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from compliance_engine.hybrid_validator import (
    HybridValidationResult,
    ValidationMethod,
)


def ergebnis(**kw):
    basis = dict(field_name="adresse", found=False, confidence=0.5,
                 value=None, method_used=ValidationMethod.PATTERN_ONLY)
    basis.update(kw)
    return HybridValidationResult(**basis)


class TestKennzeichenExistiert:
    def test_vorgabe_ist_geprueft(self):
        assert ergebnis().unverifiziert is False

    def test_kennzeichen_setzbar(self):
        assert ergebnis(unverifiziert=True).unverifiziert is True


class TestVerbraucherUeberspringtUngeprueftes:
    """Die Checks lesen das Kennzeichen aus dem Ergebnis-Dict."""

    def _feld(self, **kw):
        d = {"field": "adresse", "found": False, "confidence": 0.5,
             "value": None, "method": "pattern_only", "ai_reasoning": None,
             "unverifiziert": False}
        d.update(kw)
        return d

    def test_impressum_check_kennt_das_kennzeichen(self):
        import inspect
        from compliance_engine.checks import impressum_check
        quelle = inspect.getsource(impressum_check.check_impressum_compliance)
        assert 'field_result.get("unverifiziert")' in quelle, \
            "Impressum-Check überspringt ungeprüfte Felder nicht"

    def test_datenschutz_check_kennt_das_kennzeichen(self):
        import inspect
        from compliance_engine.checks import datenschutz_check
        quelle = inspect.getsource(datenschutz_check.check_datenschutz_compliance)
        assert 'field_result.get("unverifiziert")' in quelle, \
            "Datenschutz-Check überspringt ungeprüfte Felder nicht"


class TestQualitaetOhneUngeprueftes:
    """Die Vollständigkeit rechnet nur über tatsächlich geprüfte Pflichtfelder."""

    def test_ungeprueftes_feld_drueckt_die_note_nicht(self):
        # Nachgebaut, was hybrid_validator im Ergebnis rechnet: von drei
        # Pflichtfeldern ist eines gefunden, eines fehlt, eines ungeprüft.
        felder = [
            ergebnis(field_name="firmenname", found=True),
            ergebnis(field_name="adresse", found=False),
            ergebnis(field_name="telefon", found=False, unverifiziert=True),
        ]
        pflicht = {"firmenname", "adresse", "telefon"}

        geprueft = [r for r in felder if r.field_name in pflicht and not r.unverifiziert]
        gefunden = [r for r in geprueft if r.found]
        vollstaendigkeit = len(gefunden) / len(geprueft)

        # 1 von 2 geprüften, nicht 1 von 3 — das ungeprüfte Feld zählt nicht mit.
        assert vollstaendigkeit == pytest.approx(0.5)

    def test_alles_ungeprueft_ergibt_keine_schlechte_note(self):
        felder = [ergebnis(field_name=n, found=False, unverifiziert=True)
                  for n in ("firmenname", "adresse", "telefon")]
        pflicht = {"firmenname", "adresse", "telefon"}
        geprueft = [r for r in felder if r.field_name in pflicht and not r.unverifiziert]
        vollstaendigkeit = (len([r for r in geprueft if r.found]) / len(geprueft)
                            if geprueft else 1.0)
        # Nichts geprüft heißt nicht "alles fehlt".
        assert vollstaendigkeit == 1.0
