"""
Eine Selbstregistrierung muss auf einem Tarif landen, den es gibt.

Der Anlass ist der letzte Befund des Audit-Durchstichs: `RegisterRequest.plan`
stand auf `"ki"` — ein Rest aus einem frueheren Tarifmodell. Den Tarif kennt
heute nichts mehr: nicht `_resolve_modules` im Kaufweg, nicht der Modul-Zugang,
nicht die Tarifanzeige der Oberflaeche.

Die Folge war leise und vollstaendig: registrieren ging, anmelden ging, der
oeffentliche Scan lief — und danach beantwortete JEDER Modulaufruf mit 403.
Der Kunde sass in einem Konto, in dem nichts funktioniert, ohne dass irgendwo
stand, warum.

Dass es bisher niemandem aufgefallen ist, hat einen unangenehmen Grund: von
den fuenf Konten auf `ki` waren alle fuenf aus diesem Audit. Ueber die
Selbstregistrierung ist bis dahin nie jemand gekommen.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import auth_routes  # noqa: E402


class TestStandardtarif:
    def test_registrierung_ohne_tarifwahl_landet_auf_free(self):
        assert auth_routes.RegisterRequest.model_fields["plan"].default == "free"

    def test_der_alte_tarif_ist_weg(self):
        assert auth_routes.RegisterRequest.model_fields["plan"].default != "ki"

    def test_standardtarif_ist_bekannt(self):
        vorgabe = auth_routes.RegisterRequest.model_fields["plan"].default
        assert vorgabe in auth_routes.BEKANNTE_TARIFE


class TestBekannteTarife:
    def test_deckt_das_tarifmodell_ab(self):
        for tarif in ("free", "single", "monitor", "pro", "agency",
                      "expert", "update"):
            assert tarif in auth_routes.BEKANNTE_TARIFE, tarif

    def test_kennt_keine_erfundenen(self):
        for erfunden in ("ki", "ai", "premium", "basic"):
            assert erfunden not in auth_routes.BEKANNTE_TARIFE, erfunden

    def test_deckt_sich_mit_dem_kaufweg(self):
        """
        Die Vollzugangs-Tarife im Modul-Zugang muessen hier bekannt sein —
        sonst koennte jemand einen Tarif kaufen, den die Registrierung fuer
        ungueltig haelt.
        """
        from auth_service import _VOLLZUGANG_TARIFE
        for tarif in _VOLLZUGANG_TARIFE:
            assert tarif in auth_routes.BEKANNTE_TARIFE, tarif


class TestUnbekannteTarifeWerdenAbgefangen:
    def test_die_pruefung_steht_im_code(self):
        pfad = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "auth_routes.py")
        with open(pfad, encoding="utf-8") as fh:
            quelle = fh.read()
        assert "plan_type not in BEKANNTE_TARIFE" in quelle, \
            "Ein unbekannter Tarif landet wieder ungeprueft in user_limits"
        assert "plan_type = 'free'" in quelle
