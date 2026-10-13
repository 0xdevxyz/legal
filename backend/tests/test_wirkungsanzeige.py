"""
Die Wirkungsanzeige: Bewertung vorn, Auslieferung nur mit Zuschreibung.

Der Wirkungsscan (backend/compliance_engine/wirkungsscan.py) misst dieselbe
Seite zweimal. Seine Zahlen waren bis zum 02.10.2026 nirgends zu sehen: der
Endpunkt stand, das Dashboard rief ihn nie. Die Anzeige
(dashboard-react/.../WirkungsAnzeige.tsx) ist die erste Stelle, die sie
darstellt, und deshalb die erste, die sie falsch darstellen kann.

Zwei Regeln aus test_wirkungsscan.py gelten dort genauso, nur eine Schicht
weiter vorn. Die dortigen Waechter lesen ausschliesslich Python-Quellen; eine
Anzeige im Dashboard haetten sie nie bemerkt:

1. Die Hauptzahl bleibt die Bewertung der Website (ohne Widget). Die
   Auslieferungszahl (mit Widget) ist eine Aussage ueber complyo und steht
   daneben, nie davor.
2. Die Auslieferungszahl reist nie ohne ihre Zuschreibung. Ohne beobachtetes
   Skript ist jeder Unterschied Messrauschen.
"""
import datetime as dt
import os
import re
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

WURZEL = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ANZEIGE = os.path.join(WURZEL, "dashboard-react", "src", "components",
                       "accessibility", "WirkungsAnzeige.tsx")
SEITE = os.path.join(WURZEL, "dashboard-react", "src", "app", "accessibility",
                     "statement", "page.tsx")


def _lies(pfad):
    with open(pfad, encoding="utf-8") as fh:
        return fh.read()


def _zeile(**kw):
    basis = {"ohne_widget": 22, "mit_widget": 5, "lage": "wirksam",
             "gemessen_am": dt.datetime(2026, 10, 2, 9, 30),
             "widget_geladen": "true"}
    basis.update(kw)
    return basis


class TestVerlaufszeileTraegtDieZuschreibung:
    """Die Zeile im Verlauf ist dieselbe Behauptung wie ein einzelnes Ergebnis."""

    def test_beobachtetes_widget_liefert_beide_zahlen(self):
        from wirkungsscan_routes import _verlaufszeile
        z = _verlaufszeile(_zeile())
        assert z["widget_geladen"] is True
        assert (z["ohne_widget"], z["mit_widget"], z["behoben"]) == (22, 5, 17)

    def test_ohne_beobachtetes_widget_keine_auslieferungszahl(self):
        """Der Fall, der die Anzeige in eine falsche Wirkungsbehauptung triebe:
        panoart360.de trug kein complyo, die zwei Laeufe unterschieden sich um
        Rauschen, und eine Zeile "47 behoben" stand im Verlauf."""
        from wirkungsscan_routes import _verlaufszeile
        z = _verlaufszeile(_zeile(widget_geladen="false", mit_widget=4,
                                  lage="kein_widget"))
        assert z["widget_geladen"] is False
        assert "mit_widget" not in z and "behoben" not in z

    def test_alte_zeile_ohne_beobachtung_ist_unbekannt_nicht_nein(self):
        """Vor dem 20.09.2026 wurde die Beobachtung nicht gespeichert. Das ist
        weder "lief" noch "lief nicht", und die Lage dieser Zeilen darf nicht
        zurueckgerechnet werden: sie stammt aus der Fassung, die aus einem
        Unterschied auf ein laufendes Widget schloss."""
        from wirkungsscan_routes import _verlaufszeile
        z = _verlaufszeile(_zeile(widget_geladen=None, lage="verschlechterung"))
        assert z["widget_geladen"] is None
        assert "mit_widget" not in z and "behoben" not in z
        assert z["lage"] == "unbekannt", (
            "Die Lage einer unbeobachteten Zeile steht im Verlauf: sie stammt "
            "aus der Fassung, die aus einem Unterschied auf ein laufendes "
            "Widget schloss, und behauptet eine Wirkung, die niemand gemessen hat.")

    def test_die_bewertung_steht_immer_in_der_zeile(self):
        from wirkungsscan_routes import _verlaufszeile
        for roh in ("true", "false", None):
            assert _verlaufszeile(_zeile(widget_geladen=roh))["ohne_widget"] == 22

    def test_behoben_wird_nie_negativ(self):
        from wirkungsscan_routes import _verlaufszeile
        z = _verlaufszeile(_zeile(mit_widget=30))
        assert z["behoben"] == 0


class TestEndpunktLiefertDieZuschreibung:
    """Durch die Route, nicht am Hilfsmittel vorbei."""

    def test_verlauf_ueber_den_router(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        import wirkungsscan_routes as wr
        from dependencies import get_current_user

        class Verbindung:
            def __init__(self):
                self.sql = []

            async def fetch(self, sql, *args):
                self.sql.append(sql)
                if "tracked_websites" in sql:
                    return [{"url": "https://beispiel.test"}]
                return [_zeile(),
                        _zeile(widget_geladen="false", lage="kein_widget",
                               gemessen_am=dt.datetime(2026, 10, 1, 9, 30)),
                        _zeile(widget_geladen=None, lage="verschlechterung",
                               gemessen_am=dt.datetime(2026, 9, 12, 9, 30))]

        verbindung = Verbindung()

        class Erwerb:
            async def __aenter__(self):
                return verbindung

            async def __aexit__(self, *a):
                return False

        class Pool:
            def acquire(self):
                return Erwerb()

        app = FastAPI()
        app.include_router(wr.router)
        app.dependency_overrides[get_current_user] = lambda: {"user_id": 7}
        alt = wr.db_pool
        wr.db_pool = Pool()
        try:
            r = TestClient(app).get("/api/wirkungsscan/beispiel-test/verlauf")
        finally:
            wr.db_pool = alt

        assert r.status_code == 200
        zeilen = r.json()["messungen"]
        assert [z["widget_geladen"] for z in zeilen] == [True, False, None]
        assert zeilen[2]["lage"] == "unbekannt"
        assert "mit_widget" in zeilen[0]
        assert all("mit_widget" not in z for z in zeilen[1:]), (
            "Der Verlauf liefert eine Auslieferungszahl ohne beobachtetes Widget.")
        assert any("ergebnis->>'widget_geladen'" in s for s in verbindung.sql), (
            "Die Zuschreibung wird nicht aus der gespeicherten Messung gelesen.")


class TestDieAnzeigeHaeltDieFragenAuseinander:
    def test_die_anzeige_ist_eingebunden(self):
        assert "WirkungsAnzeige" in _lies(SEITE), (
            "Die Wirkungsanzeige steht nicht mehr auf der Nachweis-Seite. "
            "Dann ist der Wirkungsscan wieder ein Endpunkt, den niemand ruft.")

    def test_jede_auslieferungszahl_haengt_an_ihrer_zuschreibung(self):
        """Jede Stelle, die mit_widget darstellt, prueft vorher widget_geladen."""
        quelle = _lies(ANZEIGE)
        # Kommentare enthalten die Namen als Erklaerung, nicht als Darstellung.
        code = re.sub(r"/\*.*?\*/", "", quelle, flags=re.S)
        code = re.sub(r"^\s*//.*$", "", code, flags=re.M)

        stellen = [m.start() for m in re.finditer(r"\.mit_widget\b", code)]
        assert stellen, "Die Anzeige stellt die Auslieferung gar nicht dar."
        wahr = "widget_geladen === true"
        for pos in stellen:
            # Die naechste davor genannte Zuschreibung muss die bestaetigende
            # sein. "=== false" oder ein blosses Lesen des Feldes genuegt nicht.
            idx = code[:pos].rfind("widget_geladen")
            kontext = code[max(0, pos - 300):pos + 40]
            assert idx != -1 and code[idx:idx + len(wahr)] == wahr \
                and pos - idx < 700, (
                "Eine Auslieferungszahl steht ohne die Pruefung ihrer "
                "Zuschreibung:\n" + kontext
            )

    def test_die_bewertung_kommt_vor_der_auslieferung(self):
        quelle = _lies(ANZEIGE)
        bewertung = quelle.index("Bewertung Ihrer Website")
        auslieferung = quelle.index("Was Besucher heute vorfinden")
        assert bewertung < auslieferung, (
            "Die Auslieferung steht vor der Bewertung. Die Hauptzahl ist die "
            "Website ohne Widget.")

    def test_die_bewertung_ist_die_groessere_zahl(self):
        """Die Hauptzahl ist die Bewertung: sie traegt die groesste Schrift."""
        quelle = _lies(ANZEIGE)
        bewertung = quelle[quelle.index("Bewertung Ihrer Website"):
                           quelle.index("Was Besucher heute vorfinden")]
        auslieferung = quelle[quelle.index("Was Besucher heute vorfinden"):]
        assert "text-2xl" in bewertung
        assert "text-2xl" not in auslieferung.split("function VerlaufsTabelle")[0], (
            "Die Auslieferungszahl ist gleich gross oder groesser als die Bewertung.")

    def test_kein_wert_der_auslieferung_wird_als_bewertung_beschriftet(self):
        quelle = _lies(ANZEIGE)
        assert not re.search(r"(Score|Punktzahl|Note)", quelle), (
            "Die Anzeige spricht von Score, Note oder Punktzahl. Eine nackte "
            "Zahl ohne Aussage ist der Grund, warum niemand Scannern glaubt.")


class TestDieAuslieferungErreichtKeineBewertung:
    """Breitenprobe ueber das Dashboard: test_wirkungsscan.py liest nur Python.

    Die Anzeige ist die einzige Stelle im Frontend, die Zahlen des
    Wirkungsscans kennen darf. Taucht mit_widget in einer anderen Komponente
    auf, besteht die Gefahr, dass die Auslieferung in eine Kennzahl, eine
    Kachel oder eine Rangliste einfliesst, die eine Website bewertet.
    """

    def test_nur_die_wirkungsanzeige_kennt_mit_widget(self):
        funde = []
        for sub in ("dashboard-react", "landing-react"):
            for ordner, unter, namen in os.walk(os.path.join(WURZEL, sub)):
                unter[:] = [u for u in unter
                            if u not in ("node_modules", ".next", "test-results")]
                for name in namen:
                    if not name.endswith((".ts", ".tsx", ".js", ".jsx")):
                        continue
                    pfad = os.path.join(ordner, name)
                    if os.path.abspath(pfad) == os.path.abspath(ANZEIGE):
                        continue
                    with open(pfad, encoding="utf-8", errors="replace") as fh:
                        for nr, zeile in enumerate(fh, 1):
                            if "mit_widget" in zeile:
                                funde.append(f"  {os.path.relpath(pfad, WURZEL)}:{nr}")
        assert not funde, (
            "Die Auslieferungszahl des Wirkungsscans wird ausserhalb der "
            "Wirkungsanzeige verarbeitet:\n" + "\n".join(funde)
            + "\n\nVorher pruefen, ob dadurch eine Zahl entsteht, die die eigene "
            "Reparatur mitbewertet: dann waere sie eine Aussage ueber complyo "
            "und keine ueber die Website des Kunden."
        )
