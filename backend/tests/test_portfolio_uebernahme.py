"""Das Portfolio zeigt den Score, den die Seite hat, nicht den Platzhalter beim Anlegen.

Gemeldet am 06.10.2026: Die Portfolio-Karte zeigte fuer die beiden zuletzt
gescannten Seiten 0, obwohl die Analyse daneben 55 anzeigte. Zwei getrennte
Ursachen:

1) rru-chemnitz.de: Die Datenbank stand schon auf 55 (tracked_websites und
   score_history). Die Karte lud ihre Liste einmal beim Oeffnen und kannte den
   Scan danach nicht; sie zeigte den Platzhalter 0 vom Anlegen weiter.

2) zahnarztpraxis-mittweida.de: Drei Scans (bis 73) liefen, BEVOR die Seite
   getrackt wurde. save_website legte sie mit dem Platzhalter 0 und
   scan_count=1 an. Damit galt sie als "geprueft" und ging mit 0 ins Portfolio,
   die vorhandenen Scans blieben unberuehrt in scan_history liegen.

Der erste Teil ist Frontend (Quelltext-Waechter, wie test_fortschritt_kennung.py),
der zweite laeuft gegen die echte Route mit einer Attrappen-Verbindung, wie
test_website_jurisdiction.py.
"""

import datetime as dt
import os

import pytest

import website_routes
from website_routes import WebsiteCreate, _adresskern, save_website

FRONTEND = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "dashboard-react", "src")
)


def fquelle(*teile):
    return open(os.path.join(FRONTEND, *teile), encoding="utf-8").read()


# ---------------------------------------------------------------------------
# 1) Die Karte kennt Scans nach dem Oeffnen
# ---------------------------------------------------------------------------

class TestKarteAktualisiertSichNachScans:
    def test_liste_haengt_am_schluessel_der_kennzahlen(self):
        # Startseite und Rescan machen ['dashboard-metrics'] nach jedem Scan
        # ungueltig; ein Schluessel darunter wird damit mitgenommen.
        s = fquelle("components", "dashboard", "AgenturPortfolioKarte.tsx")
        assert "queryKey: ['dashboard-metrics', 'portfolio']" in s

    def test_liste_wird_nicht_nur_einmal_geladen(self):
        s = fquelle("components", "dashboard", "AgenturPortfolioKarte.tsx")
        assert "useQuery" in s
        # Der alte Weg: einmal im useEffect holen und in useState ablegen.
        assert "setWebsites(" not in s

    def test_liste_umgeht_die_buendelung(self):
        s = fquelle("components", "dashboard", "AgenturPortfolioKarte.tsx")
        assert "getTrackedWebsites({ frisch: true })" in s

    def test_die_scan_wege_machen_den_schluessel_ungueltig(self):
        # Ohne diese beiden Aufrufe wuerde die Karte nie auffrischen.
        for datei in ("WebsiteAnalysis.tsx", "DomainHeroSection.tsx"):
            s = fquelle("components", "dashboard", datei)
            assert "invalidateQueries({ queryKey: ['dashboard-metrics'] })" in s, datei


# ---------------------------------------------------------------------------
# 2) Beim Anlegen werden vorhandene Scans uebernommen
# ---------------------------------------------------------------------------

class FakeConn:
    def __init__(self, vorherige_scans=None):
        # vorherige_scans: (compliance_score, scan_timestamp, anzahl) des juengsten Scans
        self.vorherige_scans = vorherige_scans
        self.calls = []

    async def fetchrow(self, query, *args):
        self.calls.append((query, args))
        q = " ".join(query.split())
        if q.startswith("SELECT id, scan_count, is_primary"):
            return None  # noch nicht getrackt
        if "SELECT websites_max" in q:
            return {"websites_max": 10, "websites_count": 1}
        if "FROM scan_history" in q:
            if self.vorherige_scans is None:
                return None
            score, zeit, anzahl = self.vorherige_scans
            return {"compliance_score": score, "scan_timestamp": zeit, "anzahl": anzahl}
        if q.startswith("INSERT INTO tracked_websites"):
            return {
                "id": "11111111-1111-1111-1111-111111111111",
                "url": args[1],
                "last_score": args[2],
                "last_scan_date": args[3],
                "scan_count": args[6],
                "is_primary": args[4],
                "jurisdiction": args[5],
            }
        return None

    async def fetchval(self, query, *args):
        self.calls.append((query, args))
        q = " ".join(query.split())
        if "COUNT(*)" in q:
            return 1
        if "SELECT jurisdiction FROM user_limits" in q:
            return "de"
        return None

    async def execute(self, query, *args):
        self.calls.append((query, args))


class FakePool:
    def __init__(self, conn):
        self._conn = conn

    def acquire(self):
        conn = self._conn

        class _Ctx:
            async def __aenter__(self):
                return conn

            async def __aexit__(self, *a):
                return False

        return _Ctx()


@pytest.fixture
def user():
    return {"id": 5, "user_id": 5}


def _insert(conn):
    for query, args in conn.calls:
        if " ".join(query.split()).startswith("INSERT INTO tracked_websites"):
            return args
    raise AssertionError("kein INSERT abgesetzt")


ZEIT = dt.datetime(2026, 10, 6, 11, 44, 58)


@pytest.mark.asyncio
async def test_vorhandene_scans_werden_beim_anlegen_uebernommen(monkeypatch, user):
    """Der Fall zahnarztpraxis-mittweida.de: drei Scans, juengster 73, dann getrackt."""
    conn = FakeConn(vorherige_scans=(73.0, ZEIT, 3))
    monkeypatch.setattr(website_routes, "db_pool", FakePool(conn))

    ergebnis = await save_website(
        WebsiteCreate(url="https://zahnarztpraxis-mittweida.de", score=0), user=user
    )

    args = _insert(conn)
    assert args[2] == 73, "der Score des juengsten Scans gehoert an die neue Zeile"
    assert args[3] == ZEIT, "das Datum des juengsten Scans, nicht das des Anlegens"
    assert args[6] == 3, "so viele Scans lagen schon vor"
    assert ergebnis["website"]["last_score"] == 73


@pytest.mark.asyncio
async def test_ohne_vorherigen_scan_bleibt_es_beim_platzhalter(monkeypatch, user):
    conn = FakeConn(vorherige_scans=None)
    monkeypatch.setattr(website_routes, "db_pool", FakePool(conn))

    await save_website(WebsiteCreate(url="https://neu.example", score=0), user=user)

    args = _insert(conn)
    assert args[2] == 0
    assert args[6] == 1


@pytest.mark.asyncio
async def test_ein_mitgesendeter_echter_wert_wird_nicht_ueberschrieben(monkeypatch, user):
    conn = FakeConn(vorherige_scans=(73.0, ZEIT, 3))
    monkeypatch.setattr(website_routes, "db_pool", FakePool(conn))

    await save_website(WebsiteCreate(url="https://x.example", score=80), user=user)

    args = _insert(conn)
    assert args[2] == 80
    # Ein echter Wert braucht keine Nachfrage in scan_history.
    assert not any("FROM scan_history" in " ".join(q.split()) for q, _ in conn.calls)


@pytest.mark.asyncio
async def test_der_scan_wird_nur_dem_eigenen_konto_zugerechnet(monkeypatch, user):
    conn = FakeConn(vorherige_scans=(73.0, ZEIT, 1))
    monkeypatch.setattr(website_routes, "db_pool", FakePool(conn))

    await save_website(WebsiteCreate(url="https://x.example", score=0), user=user)

    abfrage = [a for q, a in conn.calls if "FROM scan_history" in " ".join(q.split())]
    assert abfrage and abfrage[0][0] == 5, "scan_history wird je Konto gelesen"


class TestAdresskern:
    @pytest.mark.parametrize("a", [
        "https://x.de", "http://x.de", "https://www.x.de/", "HTTPS://WWW.X.DE", "x.de//",
    ])
    def test_gleiche_seite_gleicher_kern(self, a):
        assert _adresskern(a) == "x.de"

    def test_andere_seite_anderer_kern(self):
        assert _adresskern("https://x.de") != _adresskern("https://y.de")
        assert _adresskern("https://shop.x.de") != _adresskern("https://x.de")
