"""Der Lernstand muss sagen, wann seine eigenen Zahlen nichts wert sind.

Drei Angaben sind wichtiger als die Zahlen selbst, und alle drei verhindern
eine konkrete Fehldeutung:

- `belege_reichen`: aus drei Zustimmungen wird sonst eine 100-Prozent-Quote.
- `gruende_erfassbar`: ohne den Vermerk sieht eine Ablehnungsquote ohne
  Gruende aus wie "niemand hatte einen Grund" statt wie "hier kann keiner
  erfasst werden" — Link- und Dokumentfixes haben die Spalte gar nicht.
- `konfidenz_angenommen` neben `konfidenz_abgelehnt`: trennen die Werte
  nicht, taugt die Konfidenz nicht als Vorfilter.
"""

import datetime as dt
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import lernstand as ls


class Zeile(dict):
    """asyncpg-Record-Ersatz: Zugriff per []."""


class FakeConn:
    """Liefert je Tabelle vorbereitete Zeilen."""

    def __init__(self, je_tabelle=None, gruende=None, regeln=None, kontrast=None):
        self.je_tabelle = je_tabelle or {}
        self.gruende = gruende or []
        # Zeilen fuer die Kontrast-Abfrage (SELECT payload, created_at).
        self.kontrast = kontrast or []
        self.regeln = regeln or Zeile(
            erzeugt=0, aktiv=0, abgeschaltet=0, wartet=0, mit_grund=0)
        self.abfragen = []

    async def fetch(self, sql, *params):
        self.abfragen.append(sql)
        if "SELECT payload" in sql:
            return self.kontrast
        if "status = 'rejected'" in sql and "GROUP BY 1 ORDER BY 2 DESC" in sql:
            return self.gruende
        for tabelle, zeilen in self.je_tabelle.items():
            if f"FROM {tabelle}" in sql:
                return zeilen
        return []

    async def fetchrow(self, sql, *params):
        return self.regeln

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False


class FakePool:
    def __init__(self, conn):
        self._conn = conn

    def acquire(self):
        return self._conn


def zeile(typ="x", vor=0, an=0, ab=0, offen=0, ausgeliefert=0,
          k_an=None, k_ab=None, zuletzt=None):
    return Zeile(typ=typ, vorgeschlagen=vor, angenommen=an, abgelehnt=ab,
                 offen=offen, ausgeliefert=ausgeliefert,
                 konfidenz_angenommen=k_an, konfidenz_abgelehnt=k_ab,
                 zuletzt=zuletzt or dt.datetime(2026, 9, 4))


class TestQuote:
    def test_ohne_entscheidung_keine_quote(self):
        """None, nicht 0.0 — "keine Entscheidung" ist nicht "alles abgelehnt"."""
        assert ls._quote(0, 0) is None

    def test_quote_wird_gerundet(self):
        assert ls._quote(2, 1) == 0.667

    def test_offene_zaehlen_nicht_mit(self):
        assert ls._quote(3, 0) == 1.0


@pytest.mark.asyncio
class TestEhrlichkeitsvermerke:
    async def test_wenige_entscheidungen_gelten_nicht_als_beleg(self):
        conn = FakeConn({"accessibility_alt_text_fixes": [zeile(vor=3, an=3)]})
        d = await ls.erhebe_lernstand(FakePool(conn))
        e = d["befundtypen"][0]
        assert e["annahmequote"] == 1.0
        assert e["belege_reichen"] is False, "3 Zustimmungen sind kein Beleg"
        assert d["aussagekraeftig"] is False

    async def test_genug_entscheidungen_gelten_als_beleg(self):
        conn = FakeConn({"accessibility_alt_text_fixes": [zeile(vor=40, an=31, ab=9)]})
        d = await ls.erhebe_lernstand(FakePool(conn))
        assert d["befundtypen"][0]["belege_reichen"] is True
        assert d["aussagekraeftig"] is True

    async def test_verkabelte_wege_koennen_gruende_erfassen(self):
        """Alt-Texte und Linktexte sind seit 04.09. beide verdrahtet."""
        conn = FakeConn({
            "accessibility_alt_text_fixes": [zeile(vor=10, an=8, ab=2)],
            "accessibility_link_fixes": [zeile(vor=5, an=4, ab=1)],
        })
        d = await ls.erhebe_lernstand(FakePool(conn))
        nach_typ = {e["befundtyp"]: e for e in d["befundtypen"]}
        assert nach_typ["bild-ohne-alt-text"]["gruende_erfassbar"] is True
        assert nach_typ["linktext-ohne-bedeutung"]["gruende_erfassbar"] is True
        assert d["ohne_grunderfassung"] == []

    async def test_ohne_entscheidung_ist_etwas_anderes_als_ohne_grund(self, monkeypatch):
        """Zwei verschiedene Luecken, die nicht verwechselt werden duerfen.

        Ein Fixtyp, der beim Anlegen direkt auf `approved` gesetzt wird, hat
        keine Entscheidung: eine Ablehnungsquote von 0 % heisst dort nicht
        "niemand lehnt ab", sondern "niemand wird gefragt". Eine Grundspalte
        waere fuer ihn eine Spalte ohne Schreiber.

        Geprueft wird die MECHANIK, nicht die Tagesliste. Seit 04.09.2026 ist
        OHNE_ENTSCHEIDUNG leer, weil alle Dokumentarten zur Freigabe kommen —
        aber sobald wieder ein Typ ohne Rueckfrage angewandt wird, muss der
        Lernstand ihn so ausweisen.
        """
        monkeypatch.setattr(ls, "OHNE_ENTSCHEIDUNG", {"dokument:skip-link"})
        conn = FakeConn({"accessibility_document_fixes": [
            zeile(typ="skip-link", vor=6, an=6),
            zeile(typ="struktur", vor=4, an=4),
        ]})
        d = await ls.erhebe_lernstand(FakePool(conn))
        nach_typ = {e["befundtyp"]: e for e in d["befundtypen"]}

        assert nach_typ["dokument:skip-link"]["entscheidbar"] is False
        assert "dokument:skip-link" in d["ohne_entscheidung"]
        # ... und taucht deshalb NICHT unter "Grund fehlt" auf: dort waere er
        # eine Aufgabe, die niemand erledigen sollte.
        assert "dokument:skip-link" not in d["ohne_grunderfassung"]

        # Gegenprobe: der andere Typ ist entscheidbar und kann Gruende erfassen.
        assert nach_typ["dokument:struktur"]["entscheidbar"] is True
        assert nach_typ["dokument:struktur"]["gruende_erfassbar"] is True

    async def test_heute_ist_jede_dokumentart_entscheidbar(self):
        """Der Stand nach der Produktentscheidung vom 04.09.: mehr sinnvolle
        Freigabeklicks statt stiller Automatik."""
        assert ls.OHNE_ENTSCHEIDUNG == set()

    async def test_konfidenz_wird_getrennt_ausgewiesen(self):
        """Nur nebeneinander sieht man, ob sie ueberhaupt trennt."""
        conn = FakeConn({"accessibility_alt_text_fixes":
                         [zeile(vor=10, an=7, ab=3, k_an=0.91, k_ab=0.88)]})
        d = await ls.erhebe_lernstand(FakePool(conn))
        e = d["befundtypen"][0]
        assert e["konfidenz_angenommen"] == 0.91
        assert e["konfidenz_abgelehnt"] == 0.88


@pytest.mark.asyncio
class TestAblehngruende:
    async def test_gruende_werden_gezaehlt(self):
        conn = FakeConn(
            {"accessibility_alt_text_fixes": [zeile(vor=10, an=6, ab=4)]},
            gruende=[Zeile(grund="Zu allgemein, sagt nichts aus", anzahl=3),
                     Zeile(grund="Zu lang", anzahl=1)],
        )
        d = await ls.erhebe_lernstand(FakePool(conn))
        g = d["befundtypen"][0]["ablehngruende"]
        assert g[0]["grund"] == "Zu allgemein, sagt nichts aus"
        assert g[0]["anzahl"] == 3

    async def test_ohne_grundspalte_bleibt_die_liste_leer(self):
        conn = FakeConn({"accessibility_link_fixes": [zeile(vor=5, ab=5)]})
        d = await ls.erhebe_lernstand(FakePool(conn))
        assert d["befundtypen"][0]["ablehngruende"] == []


@pytest.mark.asyncio
class TestDokumentfixes:
    async def test_typ_kommt_aus_der_spalte(self):
        """Dokumentfixes tragen mehrere Arten in einer Tabelle."""
        conn = FakeConn({"accessibility_document_fixes": [
            zeile(typ="skip-link", vor=6, an=6),
            zeile(typ="landmark-main", vor=6, an=6),
        ]})
        d = await ls.erhebe_lernstand(FakePool(conn))
        typen = {e["befundtyp"] for e in d["befundtypen"]}
        assert typen == {"dokument:skip-link", "dokument:landmark-main"}


@pytest.mark.asyncio
class TestRobustheit:
    async def test_ein_teilausfall_verliert_nur_diesen_teil(self):
        """Sonst kostet eine fehlende Tabelle die ganze Auswertung."""
        class KaputteConn(FakeConn):
            async def fetch(self, sql, *params):
                if "accessibility_link_fixes" in sql:
                    raise RuntimeError("Tabelle weg")
                return await super().fetch(sql, *params)

        conn = KaputteConn({"accessibility_alt_text_fixes": [zeile(vor=10, an=10)]})
        d = await ls.erhebe_lernstand(FakePool(conn))
        assert len(d["befundtypen"]) == 1
        assert any("accessibility_link_fixes" in f for f in d["fehler"])

    async def test_leere_datenlage_faellt_nicht_um(self):
        d = await ls.erhebe_lernstand(FakePool(FakeConn()))
        assert d["befundtypen"] == []
        assert d["entscheidungen_gesamt"] == 0
        assert d["aussagekraeftig"] is False

    async def test_sortierung_nach_haeufigkeit(self):
        conn = FakeConn({"accessibility_alt_text_fixes": [zeile(vor=5, an=5)],
                         "accessibility_link_fixes": [zeile(vor=99, an=99)]})
        d = await ls.erhebe_lernstand(FakePool(conn))
        assert d["befundtypen"][0]["vorgeschlagen"] == 99


@pytest.mark.asyncio
class TestPruefregeln:
    async def test_abgeschaltete_regeln_werden_mitgezaehlt(self):
        """159 erzeugt, 124 abgeschaltet — ohne diese Zahl sieht die
        Regelerzeugung erfolgreicher aus, als sie ist."""
        conn = FakeConn(regeln=Zeile(erzeugt=159, aktiv=35, abgeschaltet=124,
                                     wartet=0, mit_grund=0))
        d = await ls.erhebe_lernstand(FakePool(conn))
        r = d["pruefregeln"]
        assert r["erzeugt"] == 159
        assert r["abgeschaltet"] == 124
        assert r["annahmequote"] == 0.22
        assert r["abschaltungen_mit_grund"] == 0


@pytest.mark.asyncio
class TestKontraste:
    """Kontraste zaehlen je Farbpaar, nicht je Website.

    `accessibility_document_fixes` haelt EINE Zeile je Website; darin steckt
    eine Liste von Farbpaaren im JSONB-Payload, und entschieden wird je Paar.
    Die Tabellenabfrage zaehlte deshalb Websites — eine Website mit zwoelf
    Farbpaaren, von denen zwei abgelehnt wurden, erschien als eine einzige
    Zeile mit Status 'pending'.
    """

    def _payload(self, *freigaben):
        eintraege = []
        for f in freigaben:
            e = {"freigabe": f[0]}
            if len(f) > 1 and f[1]:
                e["ablehngrund"] = f[1]
            eintraege.append(e)
        return Zeile(payload={"entscheidungen": eintraege},
                     created_at=dt.datetime(2026, 9, 4))

    async def test_farbpaare_werden_gezaehlt_nicht_zeilen(self):
        conn = FakeConn(kontrast=[
            self._payload(("approved",), ("approved",), ("rejected", "Passt nicht zur Marke")),
            self._payload(("pending",), ("approved",)),
        ])
        d = await ls.erhebe_lernstand(FakePool(conn))
        k = next(e for e in d["befundtypen"] if e["befundtyp"] == ls.KONTRAST_TYP)
        assert k["vorgeschlagen"] == 5    # nicht 2 Zeilen
        assert k["angenommen"] == 3
        assert k["abgelehnt"] == 1
        assert k["offen"] == 1

    async def test_grund_aus_dem_eintrag(self):
        """Der Grund steckt im Payload, nicht in einer Spalte — wer nur nach
        der Spalte sucht, meldet faelschlich 'nicht erfassbar'."""
        conn = FakeConn(kontrast=[
            self._payload(("rejected", "Passt nicht zur Marke"),
                          ("rejected", "Passt nicht zur Marke"),
                          ("rejected", "Kontrast reicht trotzdem nicht")),
        ])
        d = await ls.erhebe_lernstand(FakePool(conn))
        k = next(e for e in d["befundtypen"] if e["befundtyp"] == ls.KONTRAST_TYP)
        assert k["gruende_erfassbar"] is True
        assert k["ablehngruende"][0] == {"grund": "Passt nicht zur Marke", "anzahl": 2}

    async def test_ohne_zeilen_kein_eintrag(self):
        d = await ls.erhebe_lernstand(FakePool(FakeConn()))
        assert not [e for e in d["befundtypen"] if e["befundtyp"] == ls.KONTRAST_TYP]

    async def test_payload_als_zeichenkette_wird_gelesen(self):
        """asyncpg liefert JSONB je nach Codec als dict oder als Text."""
        import json
        conn = FakeConn(kontrast=[Zeile(
            payload=json.dumps({"entscheidungen": [{"freigabe": "approved"}]}),
            created_at=dt.datetime(2026, 9, 4))])
        d = await ls.erhebe_lernstand(FakePool(conn))
        k = next(e for e in d["befundtypen"] if e["befundtyp"] == ls.KONTRAST_TYP)
        assert k["angenommen"] == 1
