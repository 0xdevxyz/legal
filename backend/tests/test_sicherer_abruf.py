"""
Der gemeinsame Abrufweg des Scanners (Sicherheitsreview 2026-08-31).

Vier Stellen holten vorher mit eigener Logik und allow_redirects=True Daten,
deren Adresse aus der geprueften Seite stammt. Diese Tests halten fest, was
dabei nicht passieren darf.
"""

import pytest

from compliance_engine.sicherer_abruf import hole, Abruf, MAX_UMLEITUNGEN


class Antwort:
    """Minimale aiohttp-Antwort."""

    def __init__(self, status=200, headers=None, body=b"", url="https://example.com/"):
        self.status = status
        self.headers = headers or {}
        self._body = body
        self.url = url

    async def read(self):
        return self._body

    @property
    def content(self):
        aussen = self

        class Leser:
            async def read(self, n=None):
                return aussen._body[:n] if n else aussen._body

        return Leser()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False


class Sitzung:
    """Zeichnet auf, welche Adressen tatsaechlich angefragt wurden."""

    def __init__(self, antworten):
        self.antworten = antworten
        self.gerufen = []

    def get(self, url, **kwargs):
        self.gerufen.append(url)
        antwort = self.antworten.get(url)
        if antwort is None:
            raise AssertionError(f"Unerwartete Anfrage: {url}")
        return antwort


# ---------------- Die Schranke ----------------

@pytest.mark.asyncio
@pytest.mark.parametrize("ziel", [
    "http://169.254.169.254/latest/meta-data/",   # Cloud-Metadaten
    "http://127.0.0.1:8000/admin",                # Loopback
    "http://10.0.0.5/",                           # privates Netz
    "http://192.168.1.1/",
    "http://localhost/",
    "file:///etc/passwd",                         # falsches Schema
])
async def test_gesperrte_ziele_werden_nicht_angefragt(ziel):
    sitzung = Sitzung({})
    assert await hole(sitzung, ziel) is None
    assert sitzung.gerufen == []


@pytest.mark.asyncio
async def test_umleitung_ins_interne_netz_wird_gestoppt():
    """
    Der Kern des Befunds: der fremde Server bestimmt das Umleitungsziel. Mit
    allow_redirects=True fuehrt aiohttp die interne Anfrage aus, bevor sie
    jemand pruefen kann.
    """
    start = "https://example.com/a"
    sitzung = Sitzung({start: Antwort(302, {"Location": "http://169.254.169.254/"})})
    assert await hole(sitzung, start) is None
    assert sitzung.gerufen == [start]


@pytest.mark.asyncio
async def test_erlaubte_umleitung_wird_verfolgt():
    sitzung = Sitzung({
        "https://example.com/a": Antwort(301, {"Location": "https://example.com/b"}),
        "https://example.com/b": Antwort(200, {"Content-Type": "text/html"}, b"<html>ok</html>"),
    })
    abruf = await hole(sitzung, "https://example.com/a")
    assert abruf is not None
    assert abruf.status == 200
    assert "ok" in abruf.text()
    assert sitzung.gerufen == ["https://example.com/a", "https://example.com/b"]


@pytest.mark.asyncio
async def test_umleitungsschleife_endet():
    sitzung = Sitzung({
        "https://example.com/a": Antwort(302, {"Location": "https://example.com/a"}),
    })
    assert await hole(sitzung, "https://example.com/a") is None
    assert len(sitzung.gerufen) == MAX_UMLEITUNGEN + 1


# ---------------- Verhalten, auf das die Aufrufer bauen ----------------

@pytest.mark.asyncio
async def test_fehlerstatus_ist_kein_none():
    """
    Der Scanner unterscheidet "nicht erreichbar" von "antwortet mit 404".
    Faellt das zusammen, gilt eine 404-Seite als ungeprueft statt als Mangel.
    """
    sitzung = Sitzung({"https://example.com/x": Antwort(404, {}, b"weg")})
    abruf = await hole(sitzung, "https://example.com/x")
    assert abruf is not None and abruf.status == 404


@pytest.mark.asyncio
async def test_max_bytes_begrenzt_den_koerper():
    sitzung = Sitzung({"https://example.com/gross.png": Antwort(200, {}, b"x" * 5000)})
    abruf = await hole(sitzung, "https://example.com/gross.png", max_bytes=100)
    assert len(abruf.body) == 100


@pytest.mark.asyncio
async def test_verbindungsfehler_gibt_none():
    class Kaputt:
        def get(self, url, **kwargs):
            raise OSError("Verbindung abgelehnt")

    assert await hole(Kaputt(), "https://example.com/") is None


def test_content_type_ohne_parameter():
    abruf = Abruf(200, "https://x.de/", {"Content-Type": "image/png; charset=binary"})
    assert abruf.content_type == "image/png"
    assert Abruf(200, "https://x.de/", {}).content_type == ""


def test_text_vertraegt_kaputte_kodierung():
    abruf = Abruf(200, "https://x.de/", {}, b"\xff\xfe kaputt")
    assert "kaputt" in abruf.text()
