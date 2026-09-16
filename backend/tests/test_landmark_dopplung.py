"""Der ARIA-Checker-Sammelbefund weicht axe ueber die ganze Site, nicht nur je Seite.

Gemessen am 16.09.2026 auf panoart360.de: axe sprach auf der Startseite und
/referenzen ueber Landmarks ("Kein <main>-Bereich vorhanden"), auf
/impressum, /impressum.html und dem Blogartikel lief axe entweder ohne
Landmark-Befund oder gar nicht — dort stand der grobe ARIA-Checker-Sammel-
befund ("N Landmark-Regions fehlen") unveraendert daneben. Im
zusammengefuehrten Mehrseiten-Bericht sah das nach zwei verschiedenen
Mängeln aus, obwohl axe bereits das praezisere Bild geliefert hatte.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from compliance_engine.scanner import (
    ComplianceIssue, _unterdruecke_globale_landmark_dopplung,
)


def _axe_landmark(page):
    return ComplianceIssue(
        category="barrierefreiheit", severity="info", title="Kein <main>-Bereich vorhanden",
        description="", risk_euro=0, recommendation="r", legal_basis="l",
        metadata={"feature_id": "LANDMARKS", "page_url": page},
    )


def _heuristik_landmark(n, page):
    return ComplianceIssue(
        category="barrierefreiheit", severity="info", title=f"{n} Landmark-Regions fehlen",
        description="", risk_euro=0, recommendation="r", legal_basis="l",
        metadata={"page_url": page},
    )


def _anderer_befund(page):
    return ComplianceIssue(
        category="barrierefreiheit", severity="warning", title="Zu geringer Farbkontrast",
        description="", risk_euro=500, recommendation="r", legal_basis="l",
        metadata={"page_url": page},
    )


class TestGlobaleLandmarkDopplung:
    def test_der_gemessene_fall_von_panoart360(self):
        """axe auf Startseite/referenzen, Sammelbefund auf drei anderen Seiten."""
        issues = [
            _axe_landmark("https://panoart360.de"),
            _heuristik_landmark(1, "https://panoart360.de/impressum"),
            _heuristik_landmark(1, "https://panoart360.de/impressum.html"),
            _axe_landmark("https://panoart360.de/referenzen"),
            _heuristik_landmark(4, "https://panoart360.de/blog/ki-texte-seo-2026"),
        ]
        ergebnis = _unterdruecke_globale_landmark_dopplung(issues)
        titel = [i.title for i in ergebnis]
        assert "Kein <main>-Bereich vorhanden" in titel
        assert not any("Landmark-Regions fehlen" in t for t in titel)
        assert len(ergebnis) == 2

    def test_ohne_jeden_axe_landmark_befund_bleibt_die_heuristik_stehen(self):
        """Hat axe nirgends zu Landmarks gesprochen, ist der Sammelbefund die
        einzige Evidenz und darf nicht verschwinden."""
        issues = [_heuristik_landmark(2, "https://x.de/impressum")]
        ergebnis = _unterdruecke_globale_landmark_dopplung(issues)
        assert len(ergebnis) == 1
        assert "Landmark-Regions fehlen" in ergebnis[0].title

    def test_andere_befunde_bleiben_unberuehrt(self):
        issues = [_axe_landmark("https://x.de"), _anderer_befund("https://x.de/kontakt")]
        ergebnis = _unterdruecke_globale_landmark_dopplung(issues)
        assert len(ergebnis) == 2

    def test_axe_landmark_befunde_selbst_bleiben_alle_erhalten(self):
        """Unterdrueckt wird nur der grobe Sammelbefund, nicht axes eigene
        (praezisere) Fundstellen."""
        issues = [_axe_landmark("https://x.de"), _axe_landmark("https://x.de/referenzen")]
        ergebnis = _unterdruecke_globale_landmark_dopplung(issues)
        assert len(ergebnis) == 2

    def test_regex_greift_nicht_bei_aehnlichen_titeln(self):
        """Nur der exakte Sammelbefund-Titel wird erkannt, keine Teilstrings."""
        anderer = ComplianceIssue(
            category="barrierefreiheit", severity="warning",
            title="2 Landmark-Regions fehlen und weitere Maengel",
            description="", risk_euro=800, recommendation="r", legal_basis="l",
            metadata={"page_url": "https://x.de"},
        )
        issues = [_axe_landmark("https://x.de"), anderer]
        ergebnis = _unterdruecke_globale_landmark_dopplung(issues)
        assert len(ergebnis) == 2

    def test_leere_liste_bleibt_leer(self):
        assert _unterdruecke_globale_landmark_dopplung([]) == []
