"""
Der Tarif entscheidet ueber den Modulzugang, nicht die Buchhaltung.

Beim Oberflaechen-Durchlauf als Pro-Kunde stand auf der Seite
"Barrierefreiheitserklaerung generieren" die Meldung:

    Accessibility-Modul nicht aktiviert fuer diesen Account.

Der Tarif war `pro`. `_resolve_modules()` im Kaufweg gibt fuer
pro/agency/expert/update grundsaetzlich ALLE Module zurueck — der Tarif
enthaelt sie also per Definition. Gelesen wurde aber ausschliesslich
`user_modules`, und dort fehlten die Zeilen.

Wege in diesen Zustand gibt es mehrere: ein verlorener Stripe-Webhook, eine
Tarifaenderung von Hand, eine Migration, ein eingespieltes Backup. Der
Kunde zahlt und sieht "nicht aktiviert" — der teuerste denkbare Zustand fuer
ein Abo-Produkt, und keiner, der sich von aussen erklaeren laesst.

Deshalb jetzt abgeleitet statt nachgeschlagen. Zusaetzlich gebuchte
Einzelmodule bleiben erhalten: ein Konto verliert durch diese Regel nie etwas.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from auth_service import _ALLE_MODULE, _module_zugang  # noqa: E402


class TestVollzugangsTarife:
    def test_pro_bekommt_alle_module_ohne_zeilen(self):
        assert set(_module_zugang("pro", [])) == set(_ALLE_MODULE)

    def test_agentur_ebenso(self):
        assert "accessibility" in _module_zugang("agency", [])

    def test_expert_und_update_ebenso(self):
        for tarif in ("expert", "update"):
            assert "accessibility" in _module_zugang(tarif, []), tarif

    def test_grossschreibung_stoert_nicht(self):
        assert "cookie" in _module_zugang("PRO", [])


class TestEingeschraenkteTarife:
    def test_free_bekommt_nichts_geschenkt(self):
        assert _module_zugang("free", []) == []

    def test_single_behaelt_genau_das_gebuchte(self):
        assert _module_zugang("single", ["cookie"]) == ["cookie"]

    def test_leerer_tarif_verhaelt_sich_wie_free(self):
        assert _module_zugang("", ["cookie"]) == ["cookie"]
        assert _module_zugang(None, []) == []


class TestNiemandVerliertEtwas:
    def test_gebuchte_module_bleiben_immer_erhalten(self):
        """
        Die Regel darf nur hinzufuegen. Ein Konto, das ein Modul gebucht hat,
        muss es behalten — auch bei einem Tarif, den diese Regel nicht kennt.
        """
        for tarif in ("free", "single", "pro", "agency", "quatsch", ""):
            assert "cookie" in _module_zugang(tarif, ["cookie"]), tarif

    def test_keine_doppelten_eintraege(self):
        z = _module_zugang("pro", ["accessibility", "cookie"])
        assert len(z) == len(set(z))


class TestZweiterLeserZiehtMit:
    """
    `database_service.check_user_module()` ist der eigentliche Tuersteher —
    die Meldung im Durchlauf kam von dort. Wenn nur der eine Leser abgeleitet
    haette, waere der Fehler geblieben.
    """

    def test_tuersteher_kennt_die_ableitung(self):
        pfad = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "database_service.py")
        with open(pfad, encoding="utf-8") as fh:
            quelle = fh.read()
        assert "_tarif_schliesst_modul_ein" in quelle
        assert "_VOLLZUGANG_TARIFE" in quelle

    def test_liste_und_tuersteher_stimmen_ueberein(self):
        from database_service import DatabaseService
        assert set(DatabaseService._ALLE_MODULE) == set(_ALLE_MODULE)
