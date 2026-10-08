# -*- coding: utf-8 -*-
"""
Ein Rechtsseiten-Link muss zu einer Rechtsseite fuehren, sonst ist er keiner.

Gefunden am 02.10.2026 an einer Kundenseite: im Footer stand "Impressum",
der Link war ein mailto:. Der Scanner nahm den Link als Impressumsseite, der
Abruf von "mailto:" warf, das except schwieg, und das Impressum galt als
geprueft. Null Befunde fuer eine Seite, auf der kein Besucher ein Impressum
erreicht.

Dieselbe Luecke in drei Varianten, alle hier festgehalten:
  1. mailto:, tel:, javascript:, leeres # als Linkziel (Attrappe)
  2. #impressum ohne Impressumsabschnitt auf der Seite (Anker ins Leere)
  3. ein echter Link auf eine Seite, die kein Rechtstext ist (Kontaktseite,
     Generator eines Drittanbieters)

Und die Gegenprobe: ein Einseiter mit #impressum und echtem Abschnitt bleibt
ohne "fehlt"-Befund. Ein Fix, der Einseiter abstraft, waere ein neuer Fehler.

Alle Laeufe ohne KI (kein OPENROUTER_API_KEY). Das Ergebnis darf nicht davon
abhaengen, ob ein fremder Dienst antwortet.
"""

import asyncio
import os
import sys

import pytest
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from compliance_engine.checks import rechtsseiten_links as rl
from compliance_engine.checks.impressum_check import (
    _find_impressum_links,
    check_impressum_compliance,
)
from compliance_engine.checks.datenschutz_check import (
    _find_datenschutz_links,
    check_datenschutz_compliance,
)
from compliance_engine.checks.agb_check import _find_agb_links


IMPRESSUM_ABSCHNITT = """
<section id="impressum"><h2>Impressum</h2>
<p>Angaben gemäß § 5 DDG</p>
<p>Muster GmbH<br>Musterweg 1<br>04109 Leipzig</p>
<p>Vertreten durch: Max Mustermann (Geschäftsführer)</p>
<p>Kontakt: E-Mail info@muster-firma.de, Telefon: 0341 123456</p>
<p>Registergericht: Amtsgericht Leipzig, HRB 12345</p></section>
"""

DATENSCHUTZ_ABSCHNITT = """
<section id="datenschutz"><h2>Datenschutzerklärung</h2>
<p>Verantwortlicher im Sinne der DSGVO: Muster GmbH, Musterweg 1, 04109 Leipzig.</p>
<p>Zwecke der Verarbeitung: Bereitstellung der Website.</p>
<p>Rechtsgrundlage ist Art. 6 Abs. 1 lit. f DSGVO.</p>
<p>Speicherdauer: Server-Logs werden nach 7 Tagen gelöscht.</p>
<p>Ihre Betroffenenrechte: Auskunft, Berichtigung, Löschung.</p>
<p>Beschwerderecht bei einer Aufsichtsbehörde.</p></section>
"""

KONTAKTSEITE = ("<html><body><h1>Kontakt</h1>"
                "<p>Rufen Sie uns an: 0341 123456. Wir freuen uns auf Sie.</p></body></html>")


def _soup(html):
    return BeautifulSoup(html, "html.parser")


def _seite(footer, inhalt=""):
    return f"<html><body><h1>Muster GmbH</h1><p>Wir beraten.</p>{inhalt}<footer>{footer}</footer></body></html>"


class _Antwort:
    def __init__(self, status, text):
        self.status, self._text = status, text

    async def text(self):
        return self._text

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        return False


class _Session:
    """
    Nachbau von aiohttp fuer den Test: antwortet je Pfad, alles andere 404.
    mailto:/javascript: werfen wie der echte Client.
    """

    def __init__(self, seiten=None, wirft=()):
        self.seiten = seiten or {}
        self.wirft = tuple(wirft)
        self.abrufe = []

    def get(self, url, **_):
        self.abrufe.append(url)
        if url.startswith(("mailto:", "tel:", "javascript:")):
            raise ValueError(f"nicht-http: {url}")
        if any(url.startswith(w) for w in self.wirft):
            raise ConnectionError("Verbindung abgebrochen")
        for pfad, html in self.seiten.items():
            if url == pfad or url.rstrip("/") == pfad.rstrip("/"):
                return _Antwort(200, html)
        return _Antwort(404, "<html><body>404</body></html>")


@pytest.fixture(autouse=True)
def ohne_ki(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)


def _titel(befunde):
    return [b["title"] for b in befunde]


# ---------------------------------------------------------------------------
# 1. Attrappen sind keine Kandidaten
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("href", [
    "mailto:info@firma.de?subject=Impressum", "tel:+4934112345",
    "javascript:void(0)", "javascript:;", "#", "", "data:text/html,x",
])
def test_attrappe_ist_kein_seitenlink(href):
    assert rl.seitenlink_art(href) == rl.ART_ATTRAPPE
    assert not rl.ist_seitenlink(href)


@pytest.mark.parametrize("href,art", [
    ("/impressum", rl.ART_SEITE), ("impressum.html", rl.ART_SEITE),
    ("https://firma.de/impressum", rl.ART_SEITE), ("#impressum", rl.ART_ANKER),
])
def test_seite_und_anker_bleiben_kandidaten(href, art):
    assert rl.seitenlink_art(href) == art


@pytest.mark.parametrize("finder,text", [
    (_find_impressum_links, "Impressum"),
    (_find_datenschutz_links, "Datenschutz"),
    (_find_agb_links, "AGB"),
])
@pytest.mark.parametrize("href", ["mailto:info@firma.de", "javascript:void(0)", "tel:0341"])
def test_finder_ignorieren_attrappen(finder, text, href):
    suppe = _soup(f'<a href="{href}">{text}</a>')
    assert finder(suppe) == []


def test_attrappen_werden_fuer_den_befundtext_gesammelt():
    suppe = _soup('<a href="mailto:info@firma.de">Impressum</a><a href="/kontakt">Kontakt</a>')
    liste = rl.attrappen(suppe, text_keywords=("impressum",))
    assert liste == [("mailto:info@firma.de", "Impressum")]
    satz = rl.attrappen_satz(liste)
    assert "mailto:" in satz and "Impressum" in satz
    assert rl.attrappen_satz([]) == ""


# ---------------------------------------------------------------------------
# 2. Impressum
# ---------------------------------------------------------------------------

def test_mailto_impressum_meldet_fehlendes_impressum():
    html = _seite('<a href="mailto:info@firma.de?subject=Impressum">Impressum</a>')
    befunde = asyncio.run(check_impressum_compliance("https://firma.de/", _soup(html), _Session()))
    titel = _titel(befunde)
    assert "Kein Impressum-Link gefunden" in titel
    haupt = next(b for b in befunde if b["title"] == "Kein Impressum-Link gefunden")
    assert "mailto:" in haupt["description"], "der Kunde soll lesen, was an seinem Footer falsch ist"
    assert not any("nicht abschliessend geprueft" in t for t in titel)


def test_mailto_abruf_wird_gar_nicht_versucht():
    html = _seite('<a href="mailto:info@firma.de">Impressum</a>')
    s = _Session()
    asyncio.run(check_impressum_compliance("https://firma.de/", _soup(html), s))
    assert not any(u.startswith("mailto:") for u in s.abrufe)


def test_anker_ohne_abschnitt_ist_kein_impressum():
    html = _seite('<a href="#impressum">Impressum</a>')
    s = _Session()
    befunde = asyncio.run(check_impressum_compliance("https://firma.de/", _soup(html), s))
    assert "Impressum-Link führt zu keiner Impressumsseite" in _titel(befunde)
    assert s.abrufe == [], "ein Anker zeigt auf die Seite, die schon da ist"


def test_einseiter_mit_abschnitt_bleibt_ohne_fehlt_befund():
    html = _seite('<a href="#impressum">Impressum</a>', IMPRESSUM_ABSCHNITT)
    befunde = asyncio.run(check_impressum_compliance("https://firma.de/", _soup(html), _Session()))
    titel = _titel(befunde)
    assert "Kein Impressum-Link gefunden" not in titel
    assert "Impressum-Link führt zu keiner Impressumsseite" not in titel
    assert "Impressum-Seite nicht erreichbar" not in titel
    assert not any(b["severity"] == "critical" and b["is_missing"] for b in befunde)


def test_link_auf_kontaktseite_ist_kein_impressum():
    html = _seite('<a href="/kontakt">Impressum</a>')
    s = _Session({"https://firma.de/kontakt": KONTAKTSEITE})
    befunde = asyncio.run(check_impressum_compliance("https://firma.de/", _soup(html), s))
    titel = _titel(befunde)
    assert "Impressum-Link führt zu keiner Impressumsseite" in titel
    assert not any("nicht abschliessend geprueft" in t for t in titel), (
        "die Kontaktseite darf nicht als Impressum vermessen werden")


def test_link_auf_fremden_generator_ist_kein_impressum():
    html = _seite('<a href="https://www.e-recht24.de/impressum-generator.html">Impressum</a>')
    generator = ("<html><body><h1>Impressum-Generator</h1><p>Erstellen Sie Ihr Impressum. "
                 "info@e-recht24.de, 10115 Berlin</p></body></html>")
    s = _Session({"https://www.e-recht24.de/impressum-generator.html": generator})
    befunde = asyncio.run(check_impressum_compliance("https://firma.de/", _soup(html), s))
    assert "Impressum-Link führt zu keiner Impressumsseite" in _titel(befunde)


def test_externes_impressum_ohne_werkzeugpfad_wird_gelesen():
    """Ein Konzern-Impressum auf einer anderen Domain ist zulaessig."""
    html = _seite('<a href="https://konzern.de/impressum">Impressum</a>')
    s = _Session({"https://konzern.de/impressum": f"<html><body>{IMPRESSUM_ABSCHNITT}</body></html>"})
    befunde = asyncio.run(check_impressum_compliance("https://firma.de/", _soup(html), s))
    assert "Impressum-Link führt zu keiner Impressumsseite" not in _titel(befunde)


def test_404_hinter_dem_link_ist_ein_befund():
    html = _seite('<a href="/impressum">Impressum</a>')
    befunde = asyncio.run(check_impressum_compliance("https://firma.de/", _soup(html), _Session()))
    treffer = [b for b in befunde if b["title"] == "Impressum-Seite nicht erreichbar"]
    assert len(treffer) == 1
    assert "404" in treffer[0]["description"]
    assert treffer[0]["severity"] == "critical"


def test_abbruch_beim_laden_ist_kein_stiller_durchlauf():
    html = _seite('<a href="/impressum">Impressum</a>')
    s = _Session(wirft=("https://firma.de/impressum",))
    befunde = asyncio.run(check_impressum_compliance("https://firma.de/", _soup(html), s))
    treffer = [b for b in befunde if b["title"] == "Inhaltsprüfung des Impressums nicht möglich"]
    assert len(treffer) == 1
    assert treffer[0]["severity"] == "info" and treffer[0]["risk_euro"] == 0


def test_echtes_impressum_wird_weiterhin_geprueft():
    html = _seite('<a href="/impressum">Impressum</a>')
    s = _Session({"https://firma.de/impressum": f"<html><body>{IMPRESSUM_ABSCHNITT}</body></html>"})
    befunde = asyncio.run(check_impressum_compliance("https://firma.de/", _soup(html), s))
    titel = _titel(befunde)
    for t in ("Kein Impressum-Link gefunden", "Impressum-Link führt zu keiner Impressumsseite",
              "Impressum-Seite nicht erreichbar", "Inhaltsprüfung des Impressums nicht möglich"):
        assert t not in titel


# ---------------------------------------------------------------------------
# 3. Datenschutz
# ---------------------------------------------------------------------------

def test_javascript_datenschutz_meldet_fehlende_erklaerung():
    html = _seite('<a href="javascript:void(0)">Datenschutz</a>')
    befunde = asyncio.run(check_datenschutz_compliance("https://firma.de/", _soup(html), _Session()))
    haupt = next(b for b in befunde if b["title"] == "Keine Datenschutzerklärung gefunden")
    assert "javascript:" in haupt["description"]


def test_datenschutz_link_auf_kontaktseite_ist_keine_erklaerung():
    html = _seite('<a href="/kontakt">Datenschutz</a>')
    s = _Session({"https://firma.de/kontakt": KONTAKTSEITE})
    befunde = asyncio.run(check_datenschutz_compliance("https://firma.de/", _soup(html), s))
    titel = _titel(befunde)
    assert "Datenschutz-Link führt zu keiner Datenschutzerklärung" in titel
    assert not any("nicht abschliessend geprueft" in t for t in titel)


def test_datenschutz_404_ist_ein_befund():
    html = _seite('<a href="/datenschutz">Datenschutz</a>')
    befunde = asyncio.run(check_datenschutz_compliance("https://firma.de/", _soup(html), _Session()))
    assert "Datenschutzerklärung nicht erreichbar" in _titel(befunde)


def test_einseiter_datenschutz_bleibt_ohne_fehlt_befund():
    html = _seite('<a href="#datenschutz">Datenschutz</a>', DATENSCHUTZ_ABSCHNITT)
    befunde = asyncio.run(check_datenschutz_compliance("https://firma.de/", _soup(html), _Session()))
    titel = _titel(befunde)
    assert "Keine Datenschutzerklärung gefunden" not in titel
    assert "Datenschutz-Link führt zu keiner Datenschutzerklärung" not in titel


# ---------------------------------------------------------------------------
# 4. Direkt-URL-Fallback: eine Catch-all-Seite ist kein Rechtstext
# ---------------------------------------------------------------------------

def test_catch_all_startseite_gilt_nicht_als_impressum():
    """
    Ohne Link probiert der Check /impressum direkt. Liefert der Server fuer
    jeden Pfad die Startseite (mit dem Wort "Impressum" im Footer und einer
    E-Mail), ist das trotzdem kein Impressum.
    """
    start = _seite('<a href="mailto:info@firma.de">Impressum</a> ' * 10)

    class CatchAll(_Session):
        def get(self, url, **_):
            self.abrufe.append(url)
            return _Antwort(200, start)

    befunde = asyncio.run(check_impressum_compliance("https://firma.de/", _soup(start), CatchAll()))
    assert "Kein Impressum-Link gefunden" in _titel(befunde)


# ---------------------------------------------------------------------------
# 5. Pruefstand: --ki aus schaltet die KI wirklich ab
# ---------------------------------------------------------------------------

def test_pruefstand_ki_aus_wirkt_im_scan(monkeypatch):
    from compliance_engine import ai_budget
    import tools.pruefstand as ps

    gesehen = {}

    class FalscherScanner:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_):
            return False

        async def scan_website(self, url):
            gesehen[url] = ai_budget.ki_ist_aus()
            return {"compliance_score": 1, "issues": []}

    import compliance_engine.scanner as scanner_modul
    monkeypatch.setattr(scanner_modul, "ComplianceScanner", FalscherScanner)

    sem = asyncio.Semaphore(1)
    asyncio.run(ps.eine_seite("https://aus.de", sem, "aus"))
    asyncio.run(ps.eine_seite("https://an.de", sem, "an"))
    assert gesehen == {"https://aus.de": True, "https://an.de": False}
    assert ai_budget.ki_ist_aus() is False, "der Schalter darf nicht am Prozess kleben"
