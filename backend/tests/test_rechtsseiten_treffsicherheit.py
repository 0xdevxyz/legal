"""
Die Treffsicherheits-Auswertung: Befunde gegen Etiketten.

Der Pruefstand zaehlt Haeufigkeiten. Dass ein Befund auf 12 von 24 Seiten steht,
sagt nichts darueber, ob er stimmt. Die Auswertung legt einen Lauf neben von Hand
gelesene Etiketten. Damit sie nicht selbst Scheinsicherheit erzeugt, sind hier die
Faelle gesperrt, in denen eine falsche Zaehlweise gut aussaehe:

- Ein "nicht gefunden" bei vorhandener Seite ist ein falscher Alarm, kein Treffer.
- Ein Befund auf einer Seite, die Etikett UND Check nicht gefunden haben, ist kein
  Feldfehler: dort gibt es keinen Text, den man falsch lesen koennte.
- Eine Behauptung zu einem Feld, das es fuer diese Rechtsform nicht gibt, ist falsch.
- Ein Feld ohne Befund ist "nicht beanstandet", auch wenn es eine echte Luecke ist:
  das ist ein verpasster Mangel und kostet Trefferquote.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tools import rechtsseiten_treffsicherheit as t  # noqa: E402


def feld(**kw):
    return kw


def wahrheit():
    return {"seiten": {
        "gut.test": {
            "impressum": {"ort": "seite", "felder": feld(name=True, email=True, telefon=False), "unsicher": []},
            "datenschutz": {"ort": "seite", "felder": feld(zwecke=True, beschwerderecht=False,
                                                           speicherdauer=True), "unsicher": ["speicherdauer"]},
        },
        "ohne.test": {
            "impressum": {"ort": "keine", "felder": {}, "unsicher": []},
            "datenschutz": {"ort": "keine", "felder": {}, "unsicher": []},
        },
        "overlay.test": {
            "impressum": {"ort": "inline", "felder": feld(name=True), "unsicher": []},
            "datenschutz": {"ort": "inline", "felder": feld(zwecke=True), "unsicher": []},
        },
    }}


def issue(titel, euro=1000, severity="critical", kategorie="impressum"):
    return {"category": kategorie, "title": titel, "risk_euro": euro, "severity": severity}


def lauf(**je_seite):
    return {"seiten": [{"url": f"https://{d}/", "issues": i, "score": 50} for d, i in je_seite.items()]}


class TestSeitenebene:
    def test_alles_gefunden(self):
        r = t.auswerten(wahrheit(), lauf(**{"gut.test": [], "ohne.test": [issue("Kein Impressum-Link gefunden")],
                                           "overlay.test": []}))
        s = r["impressum"]["seite"]
        assert sorted(s["richtig_gefunden"]) == ["gut.test", "overlay.test"]
        assert s["richtig_nicht_gefunden"] == ["ohne.test"]
        assert s["falscher_alarm"] == [] and s["verpasst"] == []

    def test_nicht_gefunden_bei_vorhandener_seite_ist_falscher_alarm(self):
        r = t.auswerten(wahrheit(), lauf(**{"gut.test": [], "ohne.test": [], "overlay.test":
                                           [issue("Kein Impressum-Link gefunden")]}))
        assert r["impressum"]["seite"]["falscher_alarm"] == ["overlay.test"]

    def test_gefunden_bei_fehlender_seite_ist_verpasst(self):
        r = t.auswerten(wahrheit(), lauf(**{"gut.test": [], "ohne.test": [], "overlay.test": []}))
        assert r["impressum"]["seite"]["verpasst"] == ["ohne.test"]

    def test_unbestaetigt_ist_gefunden_aber_gezaehlt(self):
        r = t.auswerten(wahrheit(), lauf(**{"gut.test": [issue("Inhaltsprüfung des Impressums nicht möglich", 0, "info")],
                                           "ohne.test": [issue("Kein Impressum-Link gefunden")], "overlay.test": []}))
        assert r["impressum"]["seite"]["unbestaetigt"] == ["gut.test"]

    def test_datenschutz_titel_sind_eigene(self):
        r = t.auswerten(wahrheit(), lauf(**{"gut.test": [], "ohne.test": [issue("Keine Datenschutzerklärung gefunden", 5000, kategorie="datenschutz")],
                                           "overlay.test": [issue("Datenschutz-Link führt zu keiner Datenschutzerklärung", 5000, kategorie="datenschutz")]}))
        assert r["datenschutz"]["seite"]["richtig_nicht_gefunden"] == ["ohne.test"]
        assert r["datenschutz"]["seite"]["falscher_alarm"] == ["overlay.test"]


class TestFeldebene:
    def test_richtige_und_falsche_behauptung(self):
        r = t.auswerten(wahrheit(), lauf(**{
            "gut.test": [issue("Telefonnummer fehlt im Impressum", 1500),      # Luecke: richtig
                         issue("E-Mail-Adresse fehlt im Impressum", 1500)],    # vorhanden: falsch
            "ohne.test": [issue("Kein Impressum-Link gefunden", 3000)],
            "overlay.test": []}))
        f = r["impressum"]["feld"]
        assert (f["telefon"]["richtig"], f["telefon"]["falsch"]) == (1, 0)
        assert (f["email"]["richtig"], f["email"]["falsch"]) == (0, 1)
        assert f["email"]["falsch_euro"] == 1500 and f["email"]["falsch_seiten"] == ["gut.test"]
        s = r["impressum"]["summe"]
        assert (s["behauptet"], s["richtig"], s["falsch"]) == (2, 1, 1)
        assert s["genauigkeit"] == 50 and s["trefferquote"] == 100

    def test_verpasste_luecke_kostet_trefferquote(self):
        r = t.auswerten(wahrheit(), lauf(**{"gut.test": [], "ohne.test": [issue("Kein Impressum-Link gefunden")],
                                           "overlay.test": []}))
        s = r["impressum"]["summe"]
        assert s["luecken"] == 1 and s["richtig"] == 0 and s["trefferquote"] == 0
        assert r["impressum"]["feld"]["telefon"]["verpasst_seiten"] == ["gut.test"]

    def test_folgebefunde_einer_fehlenden_seite_zaehlen_nicht_als_feldfehler(self):
        """Wo der Check die Seite nicht fand, gibt es keinen Text zu lesen."""
        r = t.auswerten(wahrheit(), lauf(**{"gut.test": [issue("Kein Impressum-Link gefunden"),
                                                        issue("Firmenname/Name fehlt im Impressum")],
                                           "ohne.test": [issue("Kein Impressum-Link gefunden")],
                                           "overlay.test": []}))
        assert r["impressum"]["seite"]["falscher_alarm"] == ["gut.test"]
        assert r["impressum"]["summe"]["behauptet"] == 0

    def test_behauptung_zu_einem_feld_ohne_etikett_ist_falsch(self):
        """Handelsregister bei einem Einzelunternehmen: es gibt keine Pflicht."""
        r = t.auswerten(wahrheit(), lauf(**{"gut.test": [issue("Handelsregister-Angabe nicht gefunden", 1000, "warning")],
                                           "ohne.test": [issue("Kein Impressum-Link gefunden")], "overlay.test": []}))
        f = r["impressum"]["feld"]["register"]
        assert (f["behauptet"], f["falsch"], f["luecken"]) == (1, 1, 0)

    def test_streng_laesst_unsichere_felder_weg(self):
        l = lauf(**{"gut.test": [issue("Speicherdauer fehlt", 2000, kategorie="datenschutz")],
                    "ohne.test": [issue("Keine Datenschutzerklärung gefunden", 5000, kategorie="datenschutz")],
                    "overlay.test": []})
        alle = t.auswerten(wahrheit(), l)["datenschutz"]["feld"]
        streng = t.auswerten(wahrheit(), l, nur_sichere=True)["datenschutz"]["feld"]
        assert alle["speicherdauer"]["falsch"] == 1
        assert "speicherdauer" not in streng

    def test_euro_der_falschen_behauptungen(self):
        l = lauf(**{"gut.test": [issue("Zwecke der Datenverarbeitung fehlen", 3000, kategorie="datenschutz")],
                    "ohne.test": [issue("Keine Datenschutzerklärung gefunden", 5000, kategorie="datenschutz")],
                    "overlay.test": []})
        s = t.auswerten(wahrheit(), l)["datenschutz"]["summe"]
        assert s["falsch"] == 1 and s["falsch_euro"] == 3000


class TestBericht:
    def test_bericht_nennt_laeufe_nebeneinander(self):
        e1 = t.auswerten(wahrheit(), lauf(**{"gut.test": [], "ohne.test": [issue("Kein Impressum-Link gefunden")], "overlay.test": []}))
        e2 = t.auswerten(wahrheit(), lauf(**{"gut.test": [], "ohne.test": [], "overlay.test": []}))
        text = t.bericht([("alt", e1), ("neu", e2)], details=True)
        assert "alt" in text and "neu" in text and "verpasst: ohne.test" in text

    def test_main_liest_dateien(self, tmp_path, capsys):
        import json
        (tmp_path / "w.json").write_text(json.dumps(wahrheit()))
        (tmp_path / "l.json").write_text(json.dumps(lauf(**{"gut.test": [], "ohne.test": [issue("Kein Impressum-Link gefunden")], "overlay.test": []})))
        assert t.main(["--wahrheit", str(tmp_path / "w.json"), "--lauf", f"x={tmp_path / 'l.json'}"]) == 0
        assert "Treffsicherheit" in capsys.readouterr().out
