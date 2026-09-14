# -*- coding: utf-8 -*-
"""
Wächtertests: Rechtsquellen fallen nicht mehr still aus (14.09.2026)

Der Befund, aus dem diese Datei entstanden ist: von 13 aktiven RSS-Quellen
der Rechtsänderungs-Überwachung hatten drei seit ihrer Anlage keinen einzigen
Eintrag in `legal_news` erzeugt, und der Tageslauf meldete trotzdem jeden
Morgen "Feed fetch completed / 11 Feeds verarbeitet".

  * EU Parlament Digitales antwortet mit HTTP 202 ("angenommen, Inhalt
    folgt"). Der Abruf buchte das als `❌ HTTP 202` und brach ab.
  * EDPB News und Datenschutz.org leiten ihre alte Feed-Adresse auf eine
    HTML-Seite um. Ergebnis: HTTP 200, null lesbare Einträge — protokolliert
    als "✅ 0 neue Items gespeichert", also als Erfolg.

Beide Male war der Statuscode das einzige Kriterium, und beide Male war er
das falsche. Die Überwachung ist ein verkauftes Merkmal: eine stumme Quelle
heißt, eine Rechtsänderung wird nicht bemerkt.

Gegenprobe zu jedem Test gefahren (alte Fassung eingesetzt, Test fällt um).
Netz und Datenbank sind durchgehend gemockt.
"""

import importlib
import os
import sys
from unittest.mock import AsyncMock, MagicMock

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import news_service as ns


# ---------------------------------------------------------------------------
# Hilfsmittel
# ---------------------------------------------------------------------------

FEED_XML = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>Testquelle</title>
<item><title>DSGVO: neues Urteil zum Auskunftsanspruch</title>
<link>https://example.org/a</link>
<description>Ein Urteil zur DSGVO.</description>
<pubDate>Mon, 08 Sep 2026 09:00:00 +0200</pubDate></item>
</channel></rss>"""

# So sieht eine umgeleitete Feed-Adresse aus: gültiges HTTP, gültiges HTML,
# kein Feed. Genau das liefern EDPB News und Datenschutz.org seit Monaten.
HTML_STATT_FEED = "<!DOCTYPE html><html><body><h1>News</h1></body></html>"


def antwort(status, text="", headers=None, url="https://example.org/feed"):
    r = MagicMock()
    r.status_code = status
    r.text = text
    r.headers = headers or {}
    r.url = url
    return r


class RequestsAttrappe:
    """Ersetzt `requests` im Modul und protokolliert jeden Abruf."""

    def __init__(self, *antworten):
        self.antworten = list(antworten)
        self.aufrufe = []
        self.compat = ns.requests.compat  # urljoin echt lassen

    def get(self, url, **kwargs):
        self.aufrufe.append(url)
        if len(self.antworten) > 1:
            return self.antworten.pop(0)
        return self.antworten[0]


@pytest.fixture()
def dienst(monkeypatch):
    """NewsService ohne Datenbank und ohne Wartezeiten."""
    # Wartezeiten auf 0: die Anzahl der Versuche wird geprüft, nicht die Uhr.
    monkeypatch.setattr(ns, "WARTEPLAN_202", (0, 0, 0))
    d = ns.NewsService(None)
    # Speichern wird nicht geprüft — dafür gibt es die Dedup-Tests.
    d._save_news_item = AsyncMock(return_value=True)
    return d


async def hole(dienst, name="Testquelle", url="https://example.org/feed",
               keywords=None):
    return await dienst._fetch_and_parse_feed(
        1, name, url, "Testkategorie", keywords if keywords is not None else ["DSGVO"]
    )


# ---------------------------------------------------------------------------
# HTTP 202 — angenommen, Inhalt folgt
# ---------------------------------------------------------------------------

class TestZwischenantwort202:
    @pytest.mark.asyncio
    async def test_202_wird_wiederholt_und_liefert_dann_den_feed(self, dienst, monkeypatch):
        """Der eigentliche Fehler: 202 ist keine Absage, sondern ein 'gleich'."""
        attrappe = RequestsAttrappe(antwort(202), antwort(200, FEED_XML))
        monkeypatch.setattr(ns, "requests", attrappe)

        ergebnis = await hole(dienst)

        assert len(attrappe.aufrufe) == 2, "202 muss einen zweiten Abruf auslösen"
        assert ergebnis.ok, f"202 darf kein Fehler sein, war: {ergebnis.fehler}"
        assert ergebnis.eintraege == 1
        assert ergebnis.neue_items == 1

    @pytest.mark.asyncio
    async def test_202_hat_eine_obergrenze(self, dienst, monkeypatch):
        """Wiederholen ohne Grenze wäre eine Endlosschleife im Tageslauf."""
        attrappe = RequestsAttrappe(antwort(202))
        monkeypatch.setattr(ns, "requests", attrappe)

        ergebnis = await hole(dienst)

        assert len(attrappe.aufrufe) == len(ns.WARTEPLAN_202) + 1
        assert not ergebnis.ok
        assert "202" in ergebnis.fehler

    @pytest.mark.asyncio
    async def test_dauerhaftes_202_ist_ein_fehler_und_kein_stilles_null(self, dienst, monkeypatch):
        """
        Die Quelle darf nicht als 'verarbeitet, 0 neu' durchgehen. Genau diese
        Verwechslung hat die Quelle EU Parlament unsichtbar gemacht.
        """
        attrappe = RequestsAttrappe(antwort(202))
        monkeypatch.setattr(ns, "requests", attrappe)

        ergebnis = await hole(dienst)

        assert ergebnis.neue_items == 0
        assert ergebnis.fehler, "stumme Quelle muss einen Fehlertext tragen"

    @pytest.mark.asyncio
    async def test_bot_abwehr_wird_nicht_endlos_wiederholt(self, dienst, monkeypatch):
        """
        Nicht jedes 202 meint "Inhalt folgt". europarl.europa.eu antwortet
        seit jeher mit 202 und leerem Rumpf, weil eine AWS-WAF davorsteht
        (`x-amzn-waf-action: challenge`). Dagegen hilft kein Wiederholen.
        Wer beides gleich behandelt, ersetzt einen stillen Ausfall durch ein
        ewiges Warten — und meldet einen Befund, der zu nichts auffordert.
        """
        attrappe = RequestsAttrappe(
            antwort(202, headers={"x-amzn-waf-action": "challenge"}))
        monkeypatch.setattr(ns, "requests", attrappe)

        ergebnis = await hole(dienst)

        assert len(attrappe.aufrufe) == 1, "Bot-Abwehr sofort erkennen, nicht wiederholen"
        assert not ergebnis.ok
        assert "Bot-Schutz" in ergebnis.fehler
        assert "abschalten" in ergebnis.fehler, "der Befund muss eine Handlung nennen"

    @pytest.mark.asyncio
    async def test_echtes_202_wird_weiter_wiederholt(self, dienst, monkeypatch):
        """Die Unterscheidung darf die Wiederholung nicht abschaffen."""
        attrappe = RequestsAttrappe(antwort(202), antwort(200, FEED_XML))
        monkeypatch.setattr(ns, "requests", attrappe)

        ergebnis = await hole(dienst)

        assert len(attrappe.aufrufe) == 2
        assert ergebnis.ok

    def test_warteplan_ist_nicht_leer(self):
        """Ein leerer Warteplan wäre der alte Zustand unter neuem Namen."""
        assert len(ns.WARTEPLAN_202) >= 1
        assert all(w > 0 for w in ns.WARTEPLAN_202)


# ---------------------------------------------------------------------------
# Weitere Statuscodes, die keine Fehler sind
# ---------------------------------------------------------------------------

class TestWeitereStatuscodes:
    @pytest.mark.asyncio
    async def test_204_ist_kein_fehler(self, dienst, monkeypatch):
        """204 heißt 'kein Inhalt'. Nichts zu lesen, aber nichts kaputt."""
        monkeypatch.setattr(ns, "requests", RequestsAttrappe(antwort(204)))
        ergebnis = await hole(dienst)
        assert ergebnis.ok, f"204 darf kein Fehler sein, war: {ergebnis.fehler}"
        assert ergebnis.status == 204
        assert ergebnis.neue_items == 0

    @pytest.mark.asyncio
    async def test_304_ist_kein_fehler(self, dienst, monkeypatch):
        monkeypatch.setattr(ns, "requests", RequestsAttrappe(antwort(304)))
        ergebnis = await hole(dienst)
        assert ergebnis.ok, f"304 darf kein Fehler sein, war: {ergebnis.fehler}"
        assert ergebnis.status == 304

    @pytest.mark.asyncio
    async def test_umleitung_wird_gefolgt_statt_abgebrochen(self, dienst, monkeypatch):
        """
        `requests` folgt Umleitungen selbst. Bleibt ausnahmsweise eine stehen,
        ist sie eine Wegbeschreibung und kein Fehler.
        """
        attrappe = RequestsAttrappe(
            antwort(301, headers={"Location": "https://example.org/neu.xml"}),
            antwort(200, FEED_XML),
        )
        monkeypatch.setattr(ns, "requests", attrappe)

        ergebnis = await hole(dienst)

        assert attrappe.aufrufe[-1] == "https://example.org/neu.xml"
        assert ergebnis.ok and ergebnis.eintraege == 1

    @pytest.mark.asyncio
    async def test_umleitungsschleife_endet(self, dienst, monkeypatch):
        attrappe = RequestsAttrappe(
            antwort(302, headers={"Location": "https://example.org/ring"}))
        monkeypatch.setattr(ns, "requests", attrappe)

        ergebnis = await hole(dienst)

        assert len(attrappe.aufrufe) == ns.UMLEITUNGEN_MAX + 1
        assert not ergebnis.ok

    @pytest.mark.asyncio
    async def test_404_bleibt_ein_fehler(self, dienst, monkeypatch):
        """Die Korrektur darf nicht dazu führen, dass echte Fehler verschwinden."""
        monkeypatch.setattr(ns, "requests", RequestsAttrappe(antwort(404, "weg")))
        ergebnis = await hole(dienst)
        assert not ergebnis.ok
        assert "404" in ergebnis.fehler


# ---------------------------------------------------------------------------
# HTTP 200 ohne lesbaren Inhalt — der zweite stille Ausfall
# ---------------------------------------------------------------------------

class TestQuelleOhneInhalt:
    @pytest.mark.asyncio
    async def test_html_statt_feed_ist_ein_fehler(self, dienst, monkeypatch):
        """
        EDPB News und Datenschutz.org: Statuscode 200, Inhalt eine HTML-Seite.
        Früher protokolliert als '✅ 0 neue Items gespeichert' — als Erfolg.
        """
        monkeypatch.setattr(ns, "requests", RequestsAttrappe(antwort(200, HTML_STATT_FEED)))

        ergebnis = await hole(dienst)

        assert not ergebnis.ok, "200 ohne lesbaren Feed muss auffallen"
        assert ergebnis.eintraege == 0
        assert "lesbar" in ergebnis.fehler

    @pytest.mark.asyncio
    async def test_lebende_quelle_ohne_neues_ist_kein_fehler(self, dienst, monkeypatch):
        """
        Der Gegenfall, der NICHT alarmieren darf: Feed liest sich, alle Items
        sind schon gespeichert (so verhält sich BayLDA seit März).
        """
        monkeypatch.setattr(ns, "requests", RequestsAttrappe(antwort(200, FEED_XML)))
        dienst._save_news_item = AsyncMock(return_value=False)  # alles bekannt

        ergebnis = await hole(dienst)

        assert ergebnis.ok
        assert ergebnis.neue_items == 0
        assert ergebnis.eintraege == 1, "die gelesenen Einträge zählen, nicht die neuen"


# ---------------------------------------------------------------------------
# Der Gesamtlauf darf einen Ausfall nicht als Erfolg buchen
# ---------------------------------------------------------------------------

class TestGesamtlauf:
    @pytest.mark.asyncio
    async def test_gescheiterte_quelle_zaehlt_nicht_als_verarbeitet(self, monkeypatch):
        """
        '11 Feeds verarbeitet' bei drei toten Quellen war die Zahl, die den
        Ausfall verdeckt hat.
        """
        quellen = [
            {"id": 1, "name": "Gute Quelle", "url": "https://example.org/a",
             "category": "k", "keywords": ["DSGVO"], "last_fetch": None,
             "fetch_frequency_hours": 24},
            {"id": 2, "name": "Stumme Quelle", "url": "https://example.org/b",
             "category": "k", "keywords": ["DSGVO"], "last_fetch": None,
             "fetch_frequency_hours": 24},
        ]
        conn = AsyncMock()
        conn.fetch = AsyncMock(return_value=quellen)
        conn.execute = AsyncMock(return_value="UPDATE 1")
        pool = MagicMock()
        pool.acquire = MagicMock()
        pool.acquire.return_value.__aenter__ = AsyncMock(return_value=conn)
        pool.acquire.return_value.__aexit__ = AsyncMock(return_value=False)

        dienst = ns.NewsService(pool)

        async def abruf(feed_id, name, url, kategorie, keywords):
            if name == "Gute Quelle":
                return ns.Abrufergebnis(neue_items=2, eintraege=10, status=200)
            return ns.Abrufergebnis(status=200, fehler="kein lesbarer Feed")

        dienst._fetch_and_parse_feed = abruf

        ergebnis = await dienst.fetch_all_feeds()

        assert ergebnis["processed"] == 1, "nur die Quelle, die wirklich las"
        assert ergebnis["failed"] == 1
        assert ergebnis["new_items"] == 2
        assert "Stumme Quelle" in ergebnis["leere_quellen"]
        assert any("Stumme Quelle" in e for e in ergebnis["errors"])


# ---------------------------------------------------------------------------
# Betriebswächter: eine dauerhaft leere Quelle wird auffällig
# ---------------------------------------------------------------------------

@pytest.fixture()
def waechter(tmp_path, monkeypatch):
    monkeypatch.setenv("WAECHTER_STATE_PFAD", str(tmp_path / "state.json"))
    import cronjobs.betriebswaechter as m
    importlib.reload(m)
    return m


class TestWaechterBewertetQuelle:
    """
    Die Entscheidung, auf die es ankommt: ein Feed, der sich liest und nur
    selten etwas veröffentlicht, ist gesund. Ein Feed, der HTTP 200 und
    nichts Lesbares liefert, ist kaputt. Wer beide gleich behandelt, baut
    entweder eine Fehlalarm-Maschine oder einen Wächter, der schweigt.
    """

    def test_dauerhaftes_202_wird_gemeldet(self, waechter):
        befund = waechter.bewerte_quelle(
            "EU Parlament Digitales", 0, 0, 0, "HTTP 202 auch nach 4 Abrufen")
        assert befund is not None
        schluessel, text = befund
        assert "EU Parlament" in schluessel and "202" in text

    def test_200_ohne_lesbaren_feed_wird_gemeldet(self, waechter):
        befund = waechter.bewerte_quelle("EDPB News", 0, 200, 0, "")
        assert befund is not None
        schluessel, text = befund
        assert schluessel.startswith("quelle-leer:")
        assert "kein" in text.lower() or "0 Eintr" in text

    def test_selten_veroeffentlichende_quelle_ist_kein_alarm(self, waechter):
        """
        BayLDA: 20 Einträge im Feed, der neueste von März, 12 Stück längst
        gespeichert. 30 Tage Stille sind hier die Wahrheit, kein Ausfall.
        """
        assert waechter.bewerte_quelle("BayLDA Datenschutz", 12, 200, 20, "") is None

    def test_feed_liest_sich_aber_nichts_kam_je_an(self, waechter):
        """Einträge da, Zieltabelle leer — dann liegt es am Filter, nicht am Netz."""
        befund = waechter.bewerte_quelle("Neue Quelle", 0, 200, 20, "")
        assert befund is not None
        assert befund[0].startswith("quelle-ohne-treffer:")
        assert "keywords" in befund[1]

    def test_204_ist_kein_alarm(self, waechter):
        assert waechter.bewerte_quelle("Stille Quelle", 5, 204, 0, "") is None

    def test_404_wird_gemeldet(self, waechter):
        befund = waechter.bewerte_quelle("Tote Quelle", 3, 404, 0, "")
        assert befund is not None and "404" in befund[1]

    def test_jede_meldung_nennt_die_quelle_beim_namen(self, waechter):
        """
        Ein Befund ohne Namen zwingt zum Suchen. Der Wächter soll sagen,
        welche Quelle stumm ist, nicht dass eine stumm ist.
        """
        for argumente in [
            ("Quelle A", 0, 0, 0, "HTTP 202"),
            ("Quelle B", 0, 200, 0, ""),
            ("Quelle C", 0, 200, 20, ""),
            ("Quelle D", 1, 500, 0, ""),
        ]:
            befund = waechter.bewerte_quelle(*argumente)
            assert befund is not None
            assert argumente[0] in befund[0] and argumente[0] in befund[1]

    def test_schwellen_sind_gesetzt(self, waechter):
        """Ohne Schwelle prüft die Funktion nichts — dann wäre sie Dekoration."""
        assert waechter.QUELLEN_LEER_TAGE >= 1
        assert waechter.QUELLEN_STILLE_TAGE >= 1
        assert waechter.QUELLEN_STILLE_TAGE <= waechter.QUELLEN_LEER_TAGE


class TestWaechterIstVerdrahtet:
    def test_pruefung_haengt_in_main(self, waechter):
        """
        Ein Wächter, der nicht aufgerufen wird, bewacht nichts. Diese Falle
        ist im Haus bekannt (Wächter-Abdeckung), deshalb festgenagelt.
        """
        import inspect
        quelltext = inspect.getsource(waechter.main)
        assert "pruefe_rechtsquellen" in quelltext

    def test_pruefung_nutzt_denselben_abruf_wie_der_dienst(self, waechter):
        """
        Ein Wächter, der anders abruft als das Produkt, bewacht seinen
        eigenen Code. Deshalb NewsService._abrufen und keine zweite Fassung.
        """
        import inspect
        quelltext = inspect.getsource(waechter.pruefe_rechtsquellen)
        assert "_abrufen" in quelltext
        assert "legal_news" in quelltext, "gezählt wird die Zieltabelle"
