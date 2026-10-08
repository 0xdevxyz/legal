"""Der Live-Fortschritt haengt an der Kennung des Servers, nicht am Client-Token.

Seit dem entkoppelten Vollscan (04.09.) gibt das Dashboard den Auftrag ab und
bekommt eine `kennung` zurueck. Der Scanner meldet seinen Fortschritt NUR
darunter — das Backend haelt das ausdruecklich so fest ("Die Kennung ist
zugleich das Fortschritts-Token").

Das Frontend erzeugte aber weiter ein eigenes Token VOR der Anfrage und liess
`ScanProgressPanel` dieses pollen. Unter dem schrieb nach der Entkopplung
niemand mehr: die Live-Pruefliste im Backoffice blieb bis zum Ergebnis leer,
uebrig waren die Ueberschrift und "Pruefumgebung wird vorbereitet ...".

Der Fehler war unsichtbar, weil beide Seiten fuer sich stimmten und der
synchrone Rueckfall (ohne Redis) das alte Verhalten behielt. Dieser Waechter
prueft deshalb die NAHTSTELLE, nicht die beiden Seiten.
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def quelle(*teile):
    return open(os.path.join(BACKEND, *teile), encoding="utf-8").read()


class TestBackendMeldetDieKennung:
    def test_auftrag_startet_den_fortschritt_unter_der_kennung(self):
        s = quelle("main_production.py")
        assert "_fortschritt.starte(kennung)" in s

    def test_auftrag_nennt_den_fortschrittspfad_mit_der_kennung(self):
        s = quelle("main_production.py")
        assert 'f"/api/v2/analyze-progress/{kennung}"' in s

    def test_arbeiter_reicht_die_kennung_als_token_weiter(self):
        """Ohne das schreibt der Scanner unter gar kein Token."""
        s = quelle("compliance_engine", "scan_arbeiter.py")
        assert "scan_token_eingang=kennung" in s

    def test_kennung_passt_ins_token_muster(self):
        from compliance_engine import scan_auftraege, scan_progress
        assert scan_progress.token_gueltig(scan_auftraege.neue_kennung())


_FRONTEND = os.path.join(BACKEND, "..", "dashboard-react")
ohne_frontend = pytest.mark.skipif(
    not os.path.isdir(_FRONTEND),
    reason="Frontend-Quelltext liegt nicht neben backend/ (z. B. im Container) — laeuft in CI",
)


def fquelle(*teile):
    return open(os.path.join(_FRONTEND, "src", *teile), encoding="utf-8").read()


@ohne_frontend
class TestFrontendUebernimmtDieKennung:
    def test_analyze_website_meldet_die_kennung(self):
        s = fquelle("lib", "api.ts")
        assert "onKennung?: (kennung: string) => void" in s
        # Die Meldung muss VOR dem Abholen stehen: holeV2Ergebnis kehrt erst
        # nach bis zu 420 s zurueck, danach braucht niemand mehr Fortschritt.
        assert s.index("onKennung?.(kennung)") < s.index("return await holeV2Ergebnis(kennung)")

    def test_hero_reicht_die_kennung_an_das_panel(self):
        s = fquelle("components", "dashboard", "DomainHeroSection.tsx")
        assert "analyzeWebsite(domain, legalUpdateId, token, setScanToken)" in s

    def test_hook_reicht_die_kennung_durch(self):
        s = fquelle("hooks", "useCompliance.ts")
        # Seit dem Seitenwechsel-Fix (PR 20) meldet der Hook die Seite mit, fuer
        # die der Abruf lief; die Kennung geht weiter unveraendert an analyzeWebsite.
        assert "onKennung?: (kennung: string, url: string) => void" in s
        assert "onKennung(kennung, trimmedUrl)" in s

    def test_rescan_zeichnet_bei_neuer_kennung_neu(self):
        """Eine Ref allein loest kein Rendern aus — das Panel haette die
        Kennung sonst nie zu sehen bekommen."""
        s = fquelle("components", "dashboard", "WebsiteAnalysis.tsx")
        # Die Kennung liegt als ZUSTAND vor (der Lauf traegt Seite und Token), und
        # das Panel bekommt sie von dort, nie aus der Ref. Der Lauf haengt an der
        # Seite, fuer die er gestartet wurde: wer waehrend des Scans die Seite
        # wechselt, soll unter der neuen nicht den Fortschritt der alten sehen.
        assert "useState<{ url: string; token: string | null } | null>(null)" in s
        assert "setScanLauf((alt) =>" in s  # die Kennung des Servers ersetzt das Client-Token
        assert "<ScanProgressPanel url={scanLauf!.url} token={scanToken} />" in s
        assert "token={scanTokenRef.current}" not in s

    def test_panel_pollt_den_fortschrittspfad(self):
        s = fquelle("components", "dashboard", "ScanProgressPanel.tsx")
        assert "/api/v2/analyze-progress/${token}" in s
