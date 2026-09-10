"""
Die Barrierefreiheitserklaerung als Seite.

Bis zum 11.09.2026 gab es die Erklaerung nur als Markdown in einer
JSON-Antwort; der Betreiber hatte nichts, was er verlinken konnte. Die Seite
hier ist oeffentlich und nimmt zwei Texte aus der Adresszeile entgegen. Drei
Zusagen stehen fest:

  1. Nichts aus der Adresszeile kommt als HTML durch. Der Umsetzer escaped
     zuerst und zeichnet danach aus.
  2. Die Seite haelt dieselben Regeln wie das Protokoll: `lang="de"`, keine
     fremden Schriften, kein Skript.
  3. GET-Aufrufe ohne Sitzung kommen an der CSRF-Schranke vorbei. Dreimal ist
     eine oeffentliche Route daran gescheitert, waehrend die Tests gruen
     waren; deshalb prueft dieser Test die Middleware, nicht nur die Liste.
"""
import os
import sys
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import nachweis_routes as nw  # noqa: E402
from compliance_engine.nachweis_generator import nachweis_token  # noqa: E402
from compliance_engine.nachweis_seite import (  # noqa: E402
    erklaerung_als_html, markdown_zu_html,
)
from csrf_middleware import CSRFMiddleware  # noqa: E402

GEHEIM = "test-geheimnis"
DATEN = {
    "site_url": "https://beispiel.de",
    "vorher": {"color-contrast": 4, "region": 2},
    "nachher": {"region": 2},
    "fixes": [],
    "vorbereitet": [],
    "alt_live": 3,
    "alt_offen": 1,
    "gemessen_am": "2026-09-11 08:00",
}


class TestUmsetzer:
    def test_rohes_html_bleibt_text(self):
        html = markdown_zu_html("Hallo <script>alert(1)</script> Welt")
        assert "<script" not in html
        assert "&lt;script&gt;" in html

    def test_ueberschriften_listen_absaetze(self):
        html = markdown_zu_html("# Titel\n\n## Abschnitt\n\nEin Absatz.\n\n- eins\n- zwei\n\n---\n")
        assert "<h1>Titel</h1>" in html
        assert "<h2>Abschnitt</h2>" in html
        assert "<p>Ein Absatz.</p>" in html
        assert "<ul><li>eins</li><li>zwei</li></ul>" in html
        assert "<hr>" in html

    def test_fett_wird_ausgezeichnet(self):
        assert "<strong>12 Abweichungen</strong>" in markdown_zu_html("Es gab **12 Abweichungen**.")

    def test_fett_schuetzt_nicht_vor_html(self):
        html = markdown_zu_html("**<b>x</b>**")
        assert "<b>" not in html and "<strong>&lt;b&gt;x&lt;/b&gt;</strong>" in html

    def test_kopfzeilen_bleiben_untereinander(self):
        html = markdown_zu_html("**Anbieter:** A\n**Stand:** B")
        assert "<br>" in html

    def test_adresse_wird_link_ohne_satzzeichen(self):
        html = markdown_zu_html("Einsehbar: https://complyo.de/nachweis/a-de/abc.")
        assert '<a href="https://complyo.de/nachweis/a-de/abc">https://complyo.de/nachweis/a-de/abc</a>.' in html

    def test_adresse_mit_anfuehrungszeichen_traegt_kein_attribut_aus(self):
        html = markdown_zu_html('https://x.de/" onmouseover="alert(1)')
        assert 'onmouseover="alert' not in html.split("</a>")[0].split("href=")[1].split(">")[0]

    def test_seite_ist_eigenstaendig(self):
        seite = erklaerung_als_html("# Erklärung\n\nText", "https://beispiel.de")
        assert '<html lang="de">' in seite
        assert "<script" not in seite
        assert "<link" not in seite
        assert "fonts.googleapis" not in seite
        assert "<h1>Erklärung</h1>" in seite
        assert "beispiel.de" in seite


def _app(monkeypatch):
    monkeypatch.setenv("COMPLYO_NACHWEIS_SECRET", GEHEIM)
    monkeypatch.setattr(nw, "_daten_fuer", AsyncMock(return_value=dict(DATEN)))
    import wirkung_routes
    monkeypatch.setattr(wirkung_routes, "wirkung_fuer_site", AsyncMock(return_value=None))
    app = FastAPI()
    app.add_middleware(CSRFMiddleware, enabled=True)
    app.include_router(nw.router)
    return TestClient(app)


class TestRoute:
    def test_pfad_existiert(self):
        pfade = [r.path for r in nw.router.routes]
        assert "/api/nachweis/{site_id}/{token}/erklaerung/seite" in pfade

    def test_seite_kommt_ohne_sitzung_an_der_csrf_schranke_vorbei(self, monkeypatch):
        client = _app(monkeypatch)
        token = nachweis_token("beispiel-de", GEHEIM)
        r = client.get(f"/api/nachweis/beispiel-de/{token}/erklaerung/seite")
        assert r.status_code == 200, r.text
        assert r.headers["content-type"].startswith("text/html")
        assert "max-age=900" in r.headers["cache-control"]
        assert r.headers["x-content-type-options"] == "nosniff"
        assert '<html lang="de">' in r.text
        assert "https://complyo.de/nachweis/beispiel-de/" + token in r.text
        assert "3 Bildbeschreibungen" in r.text

    def test_fremdtext_kommt_nicht_als_html_durch(self, monkeypatch):
        client = _app(monkeypatch)
        token = nachweis_token("beispiel-de", GEHEIM)
        r = client.get(
            f"/api/nachweis/beispiel-de/{token}/erklaerung/seite",
            params={"anbieter": "<script>alert(1)</script>Firma & Co",
                    "kontakt": "<img src=x onerror=alert(1)>"},
        )
        assert r.status_code == 200
        assert "<script" not in r.text
        assert "<img" not in r.text
        assert "Firma &amp; Co" in r.text

    def test_falscher_schluessel_gibt_nicht_gefunden(self, monkeypatch):
        client = _app(monkeypatch)
        r = client.get("/api/nachweis/beispiel-de/falsch/erklaerung/seite")
        assert r.status_code == 404
