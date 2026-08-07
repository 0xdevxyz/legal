"""
Waechter: die Wirkungsmeldung darf nicht am CSRF-Schutz scheitern.

Beim Ausrollen genau so passiert — der Endpunkt antwortete 403, und zwar
stillschweigend: das Widget meldet fail-silent, also haette niemand bemerkt,
dass die Selbstueberwachung nie ankommt. Erst der Blick ins Log nach dem
Neustart hat es gezeigt.

Der Fall ist derselbe wie bei der Consent-Meldung: cross-origin von der
Kundendomain, ohne Sitzungscookie, ohne Bearer-Token. Der
Double-Submit-Check kann dort nie aufgehen.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from csrf_middleware import EXEMPT_PATHS, EXEMPT_PREFIXES  # noqa: E402


class TestWidgetMeldungenKommenDurch:
    def test_wirkung_ist_ausgenommen(self):
        assert "/api/wirkung/".startswith(EXEMPT_PREFIXES) or \
            any("/api/wirkung/probe-de".startswith(p) for p in EXEMPT_PREFIXES)

    def test_konkreter_pfad_faellt_unter_die_ausnahme(self):
        pfad = "/api/wirkung/beispiel-de"
        assert pfad in EXEMPT_PATHS or pfad.startswith(EXEMPT_PREFIXES)

    def test_die_uebrigen_widget_meldungen_bleiben_ausgenommen(self):
        """Regression gegen ein zu eifriges Aufraeumen der Liste."""
        for pfad in ("/api/cookie-compliance/consent", "/api/ab-tests/track",
                     "/api/widgets/analytics"):
            assert pfad in EXEMPT_PATHS, pfad

    def test_geschuetzte_pfade_bleiben_geschuetzt(self):
        """Die Ausnahme darf nicht versehentlich mehr oeffnen als noetig."""
        for pfad in ("/api/accessibility/approve-kontrast",
                     "/api/accessibility/agency/sammelfreigabe",
                     "/api/v2/git/apply-approved-fixes"):
            assert pfad not in EXEMPT_PATHS
            assert not pfad.startswith(EXEMPT_PREFIXES), pfad
