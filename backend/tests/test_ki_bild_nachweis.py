"""
Nachweis KI-generierter Bilder (Art. 50 KI-VO).

Leitsatz des Checks und dieser Tests: ein Fund, den der Kunde nicht
nachvollziehen kann, kostet mehr Vertrauen als er wert ist. Jeder Test hier
prueft entweder einen echten Nachweis oder einen Fall, der ausdruecklich NICHT
gemeldet werden darf.
"""

import pytest
from bs4 import BeautifulSoup

from compliance_engine.checks.ki_bild_nachweis_check import (
    pruefe_bytes,
    hat_c2pa_ohne_ki_marker,
    sammle_bilder,
    _werkzeug_feld,
    _original_hinter_optimierer,
)


def _xmp(inhalt: bytes) -> bytes:
    """XMP-Paket, wie es in JPEG (APP1) und PNG (iTXt) steht."""
    return (
        b"\xff\xd8\xff\xe1\x00\x00http://ns.adobe.com/xap/1.0/\x00"
        b'<?xpacket begin="" id="W5M0MpCehiHzreSzNTczkc9d"?>'
        b'<x:xmpmeta xmlns:x="adobe:ns:meta/"><rdf:RDF>'
        + inhalt +
        b"</rdf:RDF></x:xmpmeta><?xpacket end=\"w\"?>"
    )


# ---------------- Was gemeldet werden MUSS ----------------

def test_iptc_marker_ist_nachweis():
    """Der standardisierte Marker, gesetzt von OpenAI, Google und Adobe."""
    daten = _xmp(
        b'<rdf:Description Iptc4xmpExt:DigitalSourceType='
        b'"http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia"/>'
    )
    fund = pruefe_bytes(daten)
    assert fund is not None
    assert fund["art"] == "iptc_digitalsourcetype"
    assert "trainedAlgorithmicMedia" in fund["nachweis"]
    assert fund["fundstelle"]


def test_composite_marker_ist_nachweis():
    """KI-Anteil in einem sonst echten Bild, etwa generatives Fuellen."""
    daten = _xmp(
        b'<rdf:Description Iptc4xmpExt:DigitalSourceType='
        b'"http://cv.iptc.org/newscodes/digitalsourcetype/'
        b'compositeWithTrainedAlgorithmicMedia"/>'
    )
    assert pruefe_bytes(daten) is not None


def test_stable_diffusion_parameterblock_ist_nachweis():
    daten = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\x25tEXtparameters\x00"
        b"ein prompt, highly detailed\nSteps: 30, Sampler: DPM++ 2M, CFG scale: 7"
    )
    fund = pruefe_bytes(daten)
    assert fund is not None and fund["art"] == "generator_parameter"


def test_erzeuger_im_werkzeugfeld_ist_nachweis():
    daten = _xmp(b'<rdf:Description xmp:CreatorTool="Adobe Firefly"/>')
    fund = pruefe_bytes(daten)
    assert fund is not None
    assert fund["art"] == "erzeuger_signatur"
    assert fund["erzeuger"] == "Adobe Firefly"


@pytest.mark.parametrize("werkzeug,erwartet", [
    (b"Midjourney v6", "Midjourney"),
    (b"DALL-E 3", "DALL-E"),
    (b"Stable Diffusion XL", "Stable Diffusion"),
    (b"OpenAI gpt-image-1", "OpenAI"),
])
def test_bekannte_erzeuger(werkzeug, erwartet):
    daten = _xmp(b'<rdf:Description xmp:CreatorTool="' + werkzeug + b'"/>')
    fund = pruefe_bytes(daten)
    assert fund is not None and fund["erzeuger"] == erwartet


# ---------------- Was NICHT gemeldet werden darf ----------------

def test_c2pa_ohne_ki_marker_ist_kein_nachweis():
    """
    Leica M11-P, Sony und Nikon signieren echte Kamerafotos mit C2PA. Ein
    Manifest allein ist Herkunft, nicht KI. Genau hier wuerde ein zu eifriger
    Check einem Fotografen unterstellen, seine Fotos seien generiert.
    """
    daten = b"\xff\xd8\xff\xeb" + b"jumbc2pa" + b"c2pa.claim" + b"leica camera ag"
    assert pruefe_bytes(daten) is None
    assert hat_c2pa_ohne_ki_marker(daten) is True


def test_c2pa_mit_ki_marker_ist_nachweis():
    daten = b"\xff\xd8\xff\xeb" + b"jumbc2pa" + b"c2pa.claim" + b"trainedAlgorithmicMedia"
    assert pruefe_bytes(daten) is not None
    assert hat_c2pa_ohne_ki_marker(daten) is False


def test_gluehwuermchen_foto_ist_kein_firefly():
    """
    Das Loch der ersten Fassung: die freie Suche nach "firefly" traf die
    Bildbeschreibung eines Naturfotos.
    """
    daten = _xmp(
        b'<rdf:Description dc:description="Fireflies at night, Canon EOS R5" '
        b'xmp:CreatorTool="Adobe Lightroom Classic"/>'
    )
    assert pruefe_bytes(daten) is None


def test_fotograf_namens_gemini_ist_kein_nachweis():
    """dc:creator ist der Urheber, nicht das Werkzeug."""
    daten = _xmp(
        b'<rdf:Description dc:creator="Gemini Studios" '
        b'xmp:CreatorTool="Capture One"/>'
    )
    assert pruefe_bytes(daten) is None


def test_photoshop_allein_ist_kein_nachweis():
    daten = _xmp(b'<rdf:Description xmp:CreatorTool="Adobe Photoshop 26.0"/>')
    assert pruefe_bytes(daten) is None


def test_blosses_algorithmicmedia_ist_kein_nachweis():
    """
    "algorithmicMedia" meint prozedural erzeugte Grafik (Diagramme, Fraktale)
    und belegt kein trainiertes Modell.
    """
    daten = _xmp(
        b'<rdf:Description Iptc4xmpExt:DigitalSourceType='
        b'"http://cv.iptc.org/newscodes/digitalsourcetype/algorithmicMedia"/>'
    )
    assert pruefe_bytes(daten) is None


def test_kamerafoto_ohne_metadaten_ist_still():
    daten = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01" + b"\x00" * 2000
    assert pruefe_bytes(daten) is None
    assert hat_c2pa_ohne_ki_marker(daten) is False


def test_leere_datei_ist_still():
    assert pruefe_bytes(b"") is None
    assert pruefe_bytes(None) is None


def test_dateiname_ist_kein_nachweis():
    """Ein Bild namens ki-generiert.png beweist nichts ueber seinen Inhalt."""
    daten = b"\x89PNG\r\n\x1a\n" + b"ki-generiert-midjourney.png" + b"\x00" * 500
    assert pruefe_bytes(daten) is None


def test_werkzeugfeld_ohne_treffer():
    assert _werkzeug_feld(_xmp(b'<rdf:Description xmp:CreatorTool="GIMP 2.10"/>')) is None


# ---------------- Bildsammlung ----------------

def test_sammelt_src_srcset_und_og_image():
    html = """
    <html><head><meta property="og:image" content="/social.jpg"></head><body>
      <img src="/bilder/eins.png">
      <img data-src="/bilder/lazy.webp">
      <picture><source srcset="/bilder/gross.jpg 960w, /bilder/klein.jpg 480w"></picture>
      <img src="data:image/gif;base64,R0lGOD">
      <img src="/skript.js">
      <img src="/icon.svg">
    </body></html>
    """
    bilder = sammle_bilder("https://kunde.de/seite", BeautifulSoup(html, "html.parser"))
    assert "https://kunde.de/bilder/eins.png" in bilder
    assert "https://kunde.de/bilder/lazy.webp" in bilder
    assert "https://kunde.de/bilder/gross.jpg" in bilder
    assert "https://kunde.de/bilder/klein.jpg" in bilder
    assert "https://kunde.de/social.jpg" in bilder
    # data:-URI und Nicht-Bilder fallen heraus
    assert not any(b.startswith("data:") for b in bilder)
    assert not any(b.endswith(".js") for b in bilder)
    assert not any(b.endswith(".svg") for b in bilder)


def test_bilder_werden_entdoppelt():
    html = '<img src="/a.png"><img src="/a.png"><img src="/a.png">'
    bilder = sammle_bilder("https://kunde.de/", BeautifulSoup(html, "html.parser"))
    assert bilder == ["https://kunde.de/a.png"]


# ---------------- Bildoptimierer verstecken das Original ----------------

def test_next_js_original_wird_mitgeprueft():
    """
    Auf complyo.de selbst waren von drei Bildern zwei unpruefbar: Next.js
    liefert /_next/image?url=... und rechnet die Datei ohne Metadaten neu.
    """
    html = '<img src="/_next/image/?url=%2Flogo-dark-trim.png&w=256&q=75">'
    bilder = sammle_bilder("https://complyo.de/", BeautifulSoup(html, "html.parser"))
    assert "https://complyo.de/logo-dark-trim.png" in bilder
    assert any("/_next/image" in b for b in bilder)


@pytest.mark.parametrize("url,erwartet", [
    ("https://x.de/_next/image?url=%2Fa%2Fb.png&w=64",  "https://x.de/a/b.png"),
    ("https://x.de/cdn-cgi/image/w=64/?url=%2Fc.jpg",   "https://x.de/c.jpg"),
    ("https://x.de/bilder/normal.jpg",                  None),
    ("https://x.de/_next/image?w=64",                   None),
])
def test_original_hinter_optimierer(url, erwartet):
    assert _original_hinter_optimierer(url) == erwartet


def test_endungslose_bild_url_bleibt_drin():
    """Ein <img> ohne Dateiendung ist trotzdem ein Bild (CDN, Media-Proxy)."""
    html = '<img src="/media/12345"><img src="/bild.php?id=7">'
    bilder = sammle_bilder("https://kunde.de/", BeautifulSoup(html, "html.parser"))
    assert "https://kunde.de/media/12345" in bilder
    assert "https://kunde.de/bild.php?id=7" in bilder


# ---------------- Ganze Kette, ohne Netz ----------------

import compliance_engine.checks.ki_bild_nachweis_check as modul
from compliance_engine.checks.ki_bild_nachweis_check import check_ki_bild_nachweis

KI_BILD = _xmp(
    b'<rdf:Description Iptc4xmpExt:DigitalSourceType='
    b'"http://cv.iptc.org/newscodes/digitalsourcetype/trainedAlgorithmicMedia" '
    b'xmp:CreatorTool="Midjourney v6"/>'
)
FOTO = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01" + b"\x00" * 3000


@pytest.fixture
def netz(monkeypatch):
    """Bildabruf ohne Netz: Dateiname entscheidet ueber den Inhalt."""
    async def falsch(url, session):
        return KI_BILD if "ki" in url else FOTO
    monkeypatch.setattr(modul, "lade_kopf", falsch)


@pytest.mark.asyncio
async def test_ki_bild_ohne_kennzeichnung_wird_gemeldet(netz):
    html = '<body><h1>Unsere Leistungen</h1><img src="/bilder/ki-titel.png"></body>'
    issues = await check_ki_bild_nachweis(
        "https://kunde.de/leistungen", BeautifulSoup(html, "html.parser")
    )
    assert len(issues) == 1
    iss = issues[0]
    assert iss["severity"] == "warning"
    assert "Midjourney" in iss["title"]
    assert "ki-titel.png" in iss["title"]
    assert iss["legal_basis"].startswith("Art. 50 Abs. 4")
    assert iss["metadata"]["nachweis_art"] == "iptc_digitalsourcetype"
    assert iss["metadata"]["page_url"] == "https://kunde.de/leistungen"
    assert iss["metadata"]["fundstelle"]
    # Die Pflicht gilt nur bedingt, das muss im Text stehen
    assert "Deepfake" in iss["description"]


@pytest.mark.asyncio
async def test_gekennzeichnetes_ki_bild_ist_nur_ein_hinweis(netz):
    html = ('<body><img src="/bilder/ki-titel.png">'
            '<p>Bildquelle: KI-generiert</p></body>')
    issues = await check_ki_bild_nachweis(
        "https://kunde.de/", BeautifulSoup(html, "html.parser")
    )
    assert len(issues) == 1
    assert issues[0]["severity"] == "info"
    assert issues[0]["risk_euro"] == 0


@pytest.mark.asyncio
async def test_echte_fotos_erzeugen_nichts(netz):
    html = '<body><img src="/bilder/team.jpg"><img src="/bilder/haus.jpg"></body>'
    issues = await check_ki_bild_nachweis(
        "https://kunde.de/", BeautifulSoup(html, "html.parser")
    )
    assert issues == []


@pytest.mark.asyncio
async def test_gleiches_bild_auf_mehreren_seiten_ist_ein_befund(netz):
    """Ein Logo auf zehn Unterseiten darf nicht zehn Befunde erzeugen."""
    html = '<body><img src="/bilder/ki-logo.png"></body>'
    gesehen = set()
    erste = await check_ki_bild_nachweis(
        "https://kunde.de/", BeautifulSoup(html, "html.parser"), bereits_geprueft=gesehen
    )
    zweite = await check_ki_bild_nachweis(
        "https://kunde.de/kontakt", BeautifulSoup(html, "html.parser"), bereits_geprueft=gesehen
    )
    assert len(erste) == 1
    assert zweite == []


# ---------------- SSRF: der Scanner darf kein Proxy sein ----------------
# Die Bild-URLs stammen aus dem HTML der GEPRUEFTEN Seite. Wer complyo auf
# seine eigene Domain loslaesst, bestimmt damit, welche Adressen der Server
# aus dem internen Docker-Netz heraus abruft.

@pytest.mark.asyncio
@pytest.mark.parametrize("ziel", [
    "http://169.254.169.254/latest/meta-data/",   # Cloud-Metadaten
    "http://127.0.0.1:8000/admin",                # Loopback
    "http://10.0.0.5/bild.png",                   # privates Netz
    "http://localhost/bild.png",
])
async def test_interne_ziele_werden_nicht_abgerufen(ziel, monkeypatch):
    gerufen = []

    class Sitzung:
        def get(self, url, **kwargs):
            gerufen.append(url)
            raise AssertionError(f"Es haette keine Anfrage geben duerfen: {url}")

    assert await modul.lade_kopf(ziel, Sitzung()) is None
    assert gerufen == []


@pytest.mark.asyncio
async def test_umleitung_ins_interne_netz_wird_gestoppt(monkeypatch):
    """
    Der Fall, den allow_redirects=True offen gelassen haette: der fremde Server
    antwortet mit 302 auf die Cloud-Metadaten.
    """
    class Antwort:
        status = 302
        headers = {"Location": "http://169.254.169.254/latest/meta-data/"}
        content_type = "image/png"
        async def __aenter__(self): return self
        async def __aexit__(self, *a): return False

    gerufen = []

    class Sitzung:
        def get(self, url, **kwargs):
            gerufen.append(url)
            return Antwort()

    ergebnis = await modul.lade_kopf("https://example.com/bild.png", Sitzung())
    assert ergebnis is None
    # Die erste Anfrage darf stattfinden, die Umleitung ins interne Netz nicht.
    assert gerufen == ["https://example.com/bild.png"]
