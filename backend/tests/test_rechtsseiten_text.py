"""
Rechtstext im Dokument: Overlays, Abschnitte, Anker auf die eigene Seite.

Ergaenzt test_rechtsseiten_attrappen.py (Attrappen-Links, Inhaltsschranke). Der
Pruefstand vom 02.10.2026 hat zwei Seiten gezeigt, bei denen die Attrappen-Regeln
allein zu falschen Befunden fuehren:

- konditorei-limbach.de: Impressum und Datenschutz als Overlay (#impressumModal,
  #datenschutzModal), geoeffnet per Schaltflaeche, kein Link auf eine Seite. Die
  einzigen Treffer waren `mailto:impressum@...` und
  `https://www.datenschutz.sachsen.de` (die Landesbehoerde). Ohne diese
  Ergaenzung wird daraus "Kein Impressum-Link gefunden" samt sechs Folgebefunden
  und eine Datenschutzerklaerung, die als "nicht erreichbar" gilt.
- zahnarztpraxis-mittweida.de: alle Links zeigen auf `#rechtliches`, einen
  Abschnitt mit Impressum, Datenschutz und Cookies. Geprueft wurde bisher die
  ganze Startseite statt des Abschnitts.

Die Fixtures bilden die Struktur nach, nicht den Text der Kundenseiten.
"""
import os
import sys

import pytest
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))) 

from compliance_engine.checks.datenschutz_check import (  # noqa: E402
    _find_datenschutz_links, _looks_like_datenschutz, check_datenschutz_compliance,
)
from compliance_engine.checks.impressum_check import (  # noqa: E402
    _find_impressum_links, _looks_like_impressum, check_impressum_compliance,
)
from compliance_engine.checks.rechtsseiten_text import (  # noqa: E402
    finde_eingebetteten_text, fremder_host_ohne_klartext, gleiche_website,
)

BASIS = "https://beispiel-konditorei.test"

IMPRESSUM_TEXT = (
    "Angaben gemäß § 5 DDG. Konditorei Muster, Inhaberin: Erika Muster, "
    "Musterstraße 12, 09212 Musterstadt. Telefon: +49 3722 12345. "
    "E-Mail: <a href='mailto:impressum@beispiel-konditorei.test'>impressum@beispiel-konditorei.test</a>. "
    "Verantwortlich für den Inhalt nach § 18 Abs. 2 MStV: Erika Muster."
)
DATENSCHUTZ_TEXT = (
    "<h3>1. Verantwortlicher</h3><p>Konditorei Muster, Musterstraße 12, 09212 Musterstadt.</p>"
    "<h3>2. Hosting</h3><p>Die Verarbeitung erfolgt auf Grundlage von Art. 6 Abs. 1 lit. f DSGVO. "
    "Server-Logfiles werden nach sieben Tagen gelöscht (Speicherdauer).</p>"
    "<h3>3. Betroffenenrechte</h3><p>Sie haben das Recht auf Auskunft, Berichtigung, Löschung und "
    "Widerspruch. Beschwerde bei der Aufsichtsbehörde ist möglich.</p>"
    "<p>Personenbezogene Daten werden nur zum Betrieb der Website verarbeitet.</p>"
    "<h3>4. Schriftarten</h3><p>Die auf dieser Website verwendeten Schriftarten werden lokal "
    "bereitgestellt. Es erfolgt keine Verbindung zu Servern externer Schriftanbieter.</p>"
    "<h3>5. Verschlüsselung</h3><p>Diese Website nutzt aus Sicherheitsgründen eine "
    "TLS-Verschlüsselung. Telefonische Anfragen werden nicht über diese Website verarbeitet.</p>"
)

SEITE_MIT_OVERLAYS = f"""
<html><body>
  <main><p>Willkommen in der Konditorei.</p>
    <p>Fragen? <a href="mailto:impressum@beispiel-konditorei.test">impressum@beispiel-konditorei.test</a></p>
    <p>Die Landesbehörde: <a href="https://www.datenschutz.sachsen.de">www.datenschutz.sachsen.de</a></p>
  </main>
  <footer><div class="footer-legal">
    <button onclick="openLegal('impressumModal')">Impressum</button>
    <button onclick="openLegal('datenschutzModal')">Datenschutz</button>
  </div></footer>
  <div class="legal-overlay" id="impressumModal" role="dialog">
    <div class="legal-box"><button class="legal-close">✕</button>
      <h2>Impressum</h2><p>{IMPRESSUM_TEXT}</p></div>
  </div>
  <div class="legal-overlay" id="datenschutzModal" role="dialog">
    <div class="legal-box"><button class="legal-close">✕</button>
      <h2>Datenschutzerklärung</h2>{DATENSCHUTZ_TEXT}</div>
  </div>
</body></html>
"""


def suppe(html):
    return BeautifulSoup(html, "html.parser")


SEITE_MIT_ABSCHNITT = f"""
<html><body>
  <main><h1>Zahnarztpraxis</h1><p>Willkommen in unserer Praxis, wir freuen uns auf Sie.</p></main>
  <footer>
    <a href="#rechtliches">Impressum</a> <a href="#rechtliches">Datenschutz</a>
  </footer>
  <section id="rechtliches"><div class="container"><h2>Impressum &amp; Datenschutz</h2>
    <div id="impressum" class="legal-prose"><h2>Angaben gemäß § 5 DDG</h2><p>{IMPRESSUM_TEXT}</p></div>
    <div id="datenschutz" class="legal-prose"><h2>Datenschutzerklärung</h2>{DATENSCHUTZ_TEXT}</div>
    <div id="cookies" class="legal-prose"><h2>Cookie-Hinweis</h2><p>Wir setzen keine Cookies.</p></div>
  </div></section>
</body></html>
"""


class TestGleicheWebsite:
    @pytest.mark.parametrize("href", [
        "/datenschutz", "datenschutz.html", "https://beispiel.test/datenschutz",
        "https://www.beispiel.test/datenschutz", "https://recht.beispiel.test/x",
        "https://BEISPIEL.test:8443/x",
    ])
    def test_gehoert_dazu(self, href):
        assert gleiche_website(href, "https://www.beispiel.test/") is True

    @pytest.mark.parametrize("href", [
        "https://www.datenschutz.sachsen.de", "https://beispiel.test.evil.example/x",
        "https://anderebeispiel.test/x", "//fremd.example/datenschutz",
    ])
    def test_fremd(self, href):
        assert gleiche_website(href, "https://www.beispiel.test/") is False

    def test_oberdomain_gilt_auch(self):
        assert gleiche_website("https://www.beispiel.test/datenschutz", "https://shop.beispiel.test") is True


class TestFremderHost:
    def test_behoerde_mit_adresse_als_text_ist_keine_erklaerung(self):
        a = suppe('<a href="https://www.datenschutz.sachsen.de">www.datenschutz.sachsen.de</a>').a
        assert fremder_host_ohne_klartext(a, BASIS) is True

    def test_gehostete_erklaerung_mit_klarem_text_bleibt(self):
        a = suppe('<a href="https://app.generator.test/abc">Datenschutzerklärung</a>').a
        assert fremder_host_ohne_klartext(a, BASIS) is False

    def test_eigener_host_nie(self):
        a = suppe('<a href="/datenschutz">Hier klicken</a>').a
        assert fremder_host_ohne_klartext(a, BASIS) is False

    def test_ohne_basis_nie(self):
        a = suppe('<a href="https://www.datenschutz.sachsen.de">www.datenschutz.sachsen.de</a>').a
        assert fremder_host_ohne_klartext(a, None) is False


class TestKandidaten:
    def test_behoerde_ist_keine_datenschutzerklaerung(self):
        s = suppe('<a href="https://www.datenschutz.sachsen.de">www.datenschutz.sachsen.de</a>')
        assert _find_datenschutz_links(s, BASIS) == []

    def test_ohne_basis_bleibt_das_alte_verhalten(self):
        s = suppe('<a href="https://www.datenschutz.sachsen.de">Datenschutz</a>')
        assert len(_find_datenschutz_links(s)) == 1

    def test_gehostete_erklaerung_mit_klarem_text_bleibt(self):
        s = suppe('<a href="https://app.generator.test/abc">Datenschutzerklärung</a>')
        assert len(_find_datenschutz_links(s, BASIS)) == 1

    def test_fremder_impressum_link_mit_adresse_als_text(self):
        s = suppe('<a href="https://impressum.fremd.test/firma">impressum.fremd.test</a>')
        assert _find_impressum_links(s, BASIS) == []


class TestEingebetteterText:
    def test_findet_beide_overlays_getrennt(self):
        s = suppe(SEITE_MIT_OVERLAYS)
        imp = finde_eingebetteten_text(s, "impressum", _looks_like_impressum)
        ds = finde_eingebetteten_text(s, "datenschutz", _looks_like_datenschutz)
        assert imp and "Erika Muster" in imp
        assert ds and "Betroffenenrechte" in ds
        assert "Betroffenenrechte" not in imp and "Erika Muster, Inhaberin" not in ds

    def test_abschnitt_mit_unterbereichen_waehlt_den_kleinsten(self):
        """Zahnarztseite: #rechtliches enthaelt #impressum, #datenschutz, #cookies."""
        s = suppe(SEITE_MIT_ABSCHNITT)
        imp = finde_eingebetteten_text(s, "impressum", _looks_like_impressum)
        ds = finde_eingebetteten_text(s, "datenschutz", _looks_like_datenschutz)
        assert imp and "Betroffenenrechte" not in imp, "Impressum enthaelt die Erklaerung"
        assert ds and "Erika Muster, Inhaberin" not in ds, "Erklaerung enthaelt das Impressum"
        assert "Willkommen" not in imp and "Willkommen" not in ds

    def test_umschliessender_bereich_verwischt_nicht(self):
        html = ('<div class="legal" id="legal-impressum-datenschutz">'
                + SEITE_MIT_OVERLAYS + "</div>")
        imp = finde_eingebetteten_text(suppe(html), "impressum", _looks_like_impressum)
        assert imp and "Betroffenenrechte" not in imp

    def test_fusszeile_mit_dem_wort_ist_keine_seite(self):
        s = suppe('<footer id="impressum"><h3>Impressum</h3><a href="/impressum">Impressum</a> | '
                  '<a href="/datenschutz">Datenschutz</a></footer>')
        assert finde_eingebetteten_text(s, "impressum", _looks_like_impressum) is None

    def test_cookie_dialog_ist_keine_datenschutzerklaerung(self):
        dialog = ('<div id="privacy-settings"><h2>Datenschutz-Einstellungen</h2><p>'
                  + "Wir verarbeiten personenbezogene Daten fuer Statistik und Komfort. " * 20
                  + "Rechtsgrundlage ist Ihre Einwilligung, Art. 6 DSGVO.</p></div>")
        assert finde_eingebetteten_text(suppe(dialog), "datenschutz", _looks_like_datenschutz) is None

    def test_zu_kurz_ist_keine_seite(self):
        s = suppe('<div id="impressumModal"><h2>Impressum</h2><p>Siehe Kontakt.</p></div>')
        assert finde_eingebetteten_text(s, "impressum", _looks_like_impressum) is None

    def test_ohne_kennung_kein_treffer(self):
        s = suppe(f'<section><h2>Impressum</h2><p>{IMPRESSUM_TEXT}</p></section>')
        assert finde_eingebetteten_text(s, "impressum", _looks_like_impressum) is None, (
            "Ohne Kennung (id/class) ist ein Abschnitt mit der Ueberschrift kein "
            "gesichertes Impressum.")


# --- durch die Checks --------------------------------------------------------

class _Antwort:
    def __init__(self, status, text):
        self.status, self._t = status, text

    async def text(self):
        return self._t

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False


class _Sitzung:
    """Beantwortet jeden Abruf; protokolliert, was abgerufen wurde."""

    def __init__(self, status=404, text=""):
        self.status, self.text, self.abgerufen = status, text, []

    def get(self, url, **kw):
        self.abgerufen.append(url)
        return _Antwort(self.status, self.text)


class _Validator:
    """Stellt fest, ob die Pflichtangaben im uebergebenen Text stehen."""

    def __init__(self, *a, **k):
        pass

    async def validate_page(self, page_type, text_content, url, **kw):
        low = text_content.lower()
        if page_type == "impressum":
            felder = {"firmenname": "konditorei muster", "adresse": "musterstraße",
                      "plz_ort": "09212", "email": "@", "telefon": "telefon"}
        else:
            felder = {"verantwortlicher": "verantwortlicher", "zwecke": "betrieb der website",
                      "rechtsgrundlage": "art. 6", "speicherdauer": "speicherdauer",
                      "betroffenenrechte": "betroffenenrechte", "beschwerderecht": "beschwerde"}
        return {"quality": "good", "results": [
            {"field": f, "found": k in low, "confidence": 0.9, "value": None,
             "method": "pattern_only", "ai_reasoning": None, "unverifiziert": False}
            for f, k in felder.items()]}



class _Spaeher:
    """Wie _Validator, merkt sich aber, welchen Text er bekommen hat."""
    gesehen = []

    def __init__(self, *a, **k):
        self._echt = _Validator()

    async def validate_page(self, page_type, text_content, url, **kw):
        _Spaeher.gesehen.append((page_type, text_content))
        return await self._echt.validate_page(page_type, text_content, url, **kw)


@pytest.fixture
def validator(monkeypatch):
    import compliance_engine.hybrid_validator as hv
    monkeypatch.setattr(hv, "HybridValidator", _Validator)


@pytest.fixture
def spaeher(monkeypatch):
    import compliance_engine.hybrid_validator as hv
    _Spaeher.gesehen = []
    monkeypatch.setattr(hv, "HybridValidator", _Spaeher)
    return _Spaeher


def titel(issues):
    return [i["title"] for i in issues]


@pytest.mark.asyncio
async def test_overlay_datenschutz_wird_gelesen_nicht_vermisst(validator):
    s = _Sitzung()
    issues = await check_datenschutz_compliance(BASIS, suppe(SEITE_MIT_OVERLAYS), s)
    t = titel(issues)
    assert "Keine Datenschutzerklärung gefunden" not in t
    assert "Datenschutzerklärung nicht erreichbar" not in t
    assert "Betroffenenrechte fehlen" not in t, (
        "Der Abschnitt steht im Overlay; gelesen wurde offenbar eine andere Seite.")
    assert not any("sachsen.de" in u for u in s.abgerufen), (
        "Die Landesbehoerde wurde als Datenschutzerklaerung der Praxis abgerufen.")


@pytest.mark.asyncio
async def test_overlay_datenschutz_prueft_trotzdem_den_inhalt(validator):
    """Gegenprobe: eine Erklaerung OHNE Betroffenenrechte darf nicht gut aussehen."""
    html = SEITE_MIT_OVERLAYS.replace("Betroffenenrechte", "Hinweise").replace("Beschwerde", "Anfrage")
    issues = await check_datenschutz_compliance(BASIS, suppe(html), _Sitzung())
    assert "Betroffenenrechte fehlen" in titel(issues), (
        "Der eingebettete Text wird nicht inhaltlich geprueft: der Fix versteckt echte Maengel.")


@pytest.mark.asyncio
async def test_overlay_impressum_wird_gelesen_nicht_vermisst(validator):
    s = _Sitzung()
    issues = await check_impressum_compliance(BASIS, suppe(SEITE_MIT_OVERLAYS), s)
    t = titel(issues)
    assert "Kein Impressum-Link gefunden" not in t, t
    assert not any("fehlt" in x and "Name" in x for x in t), t
    assert not any("mailto" in u for u in s.abgerufen)


@pytest.mark.asyncio
async def test_overlay_impressum_prueft_trotzdem_den_inhalt(validator):
    html = SEITE_MIT_OVERLAYS.replace("Telefon: +49 3722 12345.", "")
    issues = await check_impressum_compliance(BASIS, suppe(html), _Sitzung())
    assert any("Telefon" in x for x in titel(issues)), titel(issues)


@pytest.mark.asyncio
async def test_anker_auf_abschnitt_liest_den_abschnitt_nicht_die_ganze_seite(spaeher):
    """Zahnarztseite: alle Links zeigen auf #rechtliches."""
    s = suppe(SEITE_MIT_ABSCHNITT)
    await check_impressum_compliance(BASIS, s, _Sitzung())
    await check_datenschutz_compliance(BASIS, s, _Sitzung())
    texte = dict(spaeher.gesehen)
    assert "Erika Muster" in texte["impressum"] and "Willkommen" not in texte["impressum"], (
        "Geprueft wurde die ganze Seite statt des Impressum-Abschnitts.")
    assert "Betroffenenrechte" in texte["datenschutz"] and "Willkommen" not in texte["datenschutz"], (
        "Geprueft wurde die ganze Seite statt der Datenschutzerklaerung.")


@pytest.mark.asyncio
async def test_anker_ohne_abschnitt_bleibt_eine_attrappe(validator):
    """Gegenprobe: der Anker allein macht keinen Rechtstext."""
    html = ('<html><body><main><p>Willkommen.</p></main><footer>'
            '<a href="#impressum">Impressum</a></footer></body></html>')
    issues = await check_impressum_compliance(BASIS, suppe(html), _Sitzung())
    assert any(i["severity"] == "critical" and "Impressum" in i["title"] for i in issues)


@pytest.mark.asyncio
async def test_ohne_text_und_ohne_link_bleibt_der_befund(validator):
    """Wer wirklich nichts hat, bekommt weiter den Befund."""
    s = suppe("<html><body><p>Hallo</p><a href='mailto:a@b.test'>Impressum</a></body></html>")
    issues = await check_impressum_compliance(BASIS, s, _Sitzung())
    assert "Kein Impressum-Link gefunden" in titel(issues)
    issues = await check_datenschutz_compliance(BASIS, suppe("<html><body><p>Hallo</p></body></html>"), _Sitzung())
    assert "Keine Datenschutzerklärung gefunden" in titel(issues)
