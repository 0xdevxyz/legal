"""
Eine Pruefung sieht dort nach, worueber sie etwas behauptet.

Bis zum 09.09.2026 durchsuchte jede deklarative Pruefung den gesamten
Seitenquelltext, egal was ihr Titel sagte. Dieselbe Pruefung irrte dadurch an
einem einzigen Tag in beide Richtungen:

  "Das Cookie-Consent-Banner informiert nicht ueber die Gueltigkeitsdauer"
  verlangte woertlich "6 Monate" irgendwo auf der Seite. Ein Banner, das
  "12 Monate" sagt, fiel durch. Nach dem Aufweichen des Musters traf es den
  Fliesstext "...16 Jahre alt sind und Ihre Einwilligung..." und sprach frei,
  ohne je im Banner gewesen zu sein.

Beide Faelle stehen hier als Test. Dazu der Grundsatz, der den Suchraum mit
`requires` teilt: laesst sich der Raum nicht bestimmen, wird NICHT geprueft.
Ein fehlender Suchraum belegt kein fehlendes Element.
"""

import asyncio
import os
import sys

import pytest
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from compliance_engine import declarative_check_runner as runner
from compliance_engine.check_spec_rules import SUCHRAEUME, detection_scope_unbekannt


DAUER_MUSTER = [r"\d{1,3}\s*(tage?n?|wochen?|monate?n?|jahre?n?)"]


def check(scope=None, muster=None, slug="dauer"):
    detection = {"type": "required_element", "html_patterns": muster or DAUER_MUSTER}
    if scope:
        detection["scope"] = scope
    return {
        "id": 1, "slug": slug, "category": "cookie",
        "title": "Banner nennt die Gültigkeitsdauer nicht",
        "description": "Keine Angabe zur Gültigkeitsdauer im Banner.",
        "recommendation": "Dauer im Banner nennen.",
        "legal_basis": "DSK-Orientierungshilfe",
        "severity": "info", "risk_euro": 0,
        "applies_when": {"requires": ["consent_banner"]},
        "detection": detection,
    }


# Eine Seite mit Banner OHNE Dauerangabe — aber mit der Altersangabe im
# Fliesstext, an der die ungenaue Suche haengen blieb.
SEITE_MIT_FALLE = """
<body>
  <main>
    <p>Wir verarbeiten Daten von Personen, die mindestens 16 Jahre alt sind
       und Ihre Einwilligung erteilt haben.</p>
  </main>
  <div class="cookie-banner">
    <p>Wir verwenden Cookies.</p>
    <button>Alle akzeptieren</button>
    <button>Nur essenzielle Cookies akzeptieren</button>
  </div>
</body>
"""

# Banner MIT Dauerangabe, und zwar nicht mit den empfohlenen sechs Monaten.
SEITE_MIT_ANGABE = """
<body>
  <main><p>Willkommen.</p></main>
  <div class="cookie-banner">
    <p>Wir verwenden Cookies. Ihre Einwilligung gilt 12 Monate.</p>
    <button>Alle akzeptieren</button>
    <button>Ablehnen</button>
  </div>
</body>
"""

SEITE_OHNE_BANNER = """
<body><main><p>Die Einwilligung gilt 6 Monate, steht hier im Fließtext.</p></main></body>
"""


def lauf(html, c):
    soup = BeautifulSoup(html, "html.parser")
    return asyncio.run(
        runner._run_single_check(c, "https://beispiel.de", soup, str(soup).lower(), None, raeume={})
    )


class TestSuchraumVerhindertFehlFreispruch:
    def test_ohne_suchraum_spricht_der_fliesstext_frei(self):
        """Der alte Zustand, hier als Beleg festgehalten."""
        befunde = lauf(SEITE_MIT_FALLE, check(scope=None))
        assert befunde == [], "ohne Suchraum trifft das Muster den Fließtext"

    def test_mit_suchraum_wird_der_fehlende_hinweis_gefunden(self):
        befunde = lauf(SEITE_MIT_FALLE, check(scope="consent_banner"))
        assert len(befunde) == 1
        assert "Gültigkeitsdauer" in befunde[0]["title"]

    def test_die_fundstelle_steht_im_befund(self):
        befund = lauf(SEITE_MIT_FALLE, check(scope="consent_banner"))[0]
        # Ohne diese Angabe weiß der Leser nicht, wo der Scanner nachgesehen hat.
        assert "Consent-Banner" in befund["description"]


class TestSuchraumVerhindertFehlalarm:
    def test_zwoelf_monate_im_banner_genuegen(self):
        """Die sechs Monate sind eine Empfehlung, keine Vorgabe."""
        assert lauf(SEITE_MIT_ANGABE, check(scope="consent_banner")) == []


class TestFehlenderRaumIstKeinBefund:
    def test_ohne_banner_wird_nicht_geprueft(self):
        assert lauf(SEITE_OHNE_BANNER, check(scope="consent_banner")) == []

    def test_unbekannter_raum_wird_uebersprungen(self):
        assert lauf(SEITE_MIT_FALLE, check(scope="fussbereich")) == []


class TestSeitenraumBleibtVorgabe:
    def test_ohne_angabe_wird_die_seite_durchsucht(self):
        c = check(scope=None, muster=[r"impressum"])
        assert lauf("<body><p>Nur ein Satz ohne das gesuchte Wort.</p></body>", c) != []
        assert lauf("<body><p>Unser Impressum finden Sie unten.</p></body>", c) == []

    def test_seite_ist_ein_gueltiger_name(self):
        assert lauf(SEITE_MIT_FALLE, check(scope="seite")) == []


class TestVokabular:
    def test_regel_kennt_die_raeume(self):
        assert detection_scope_unbekannt({"scope": "consent_banner"}) is None
        assert detection_scope_unbekannt({"scope": "seite"}) is None
        assert detection_scope_unbekannt({}) is None
        assert detection_scope_unbekannt({"scope": "fussbereich"}) == "fussbereich"

    def test_runner_und_regel_teilen_dieselbe_liste(self):
        assert runner.SUCHRAEUME is SUCHRAEUME

    def test_prompt_nennt_jeden_suchraum(self):
        from compliance_engine.check_generator import GENERATION_PROMPT
        assert "{suchraum_liste}" not in GENERATION_PROMPT
        for name in SUCHRAEUME:
            assert name in GENERATION_PROMPT, f"Suchraum '{name}' fehlt im Prompt"

    def test_generator_lehnt_unbekannten_raum_ab(self):
        from compliance_engine.check_generator import _validate_spec
        spec = {
            "slug": "x", "category": "cookie", "title": "t", "description": "d",
            "recommendation": "r", "legal_basis": "l", "severity": "warning",
            "risk_euro": 1000, "applies_when": {"requires": ["consent_banner"]},
            "detection": {"type": "required_element", "scope": "fussbereich",
                          "html_patterns": ["xyz-spezifisch"]},
        }
        err = _validate_spec(spec)
        assert err is not None and "Suchraum" in err
