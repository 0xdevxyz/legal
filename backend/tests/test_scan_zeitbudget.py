"""
Wächter gegen den Totalausfall vom 01.09.2026 (zua-zwickau.de).

Der Mehrseiten-Scan brauchte 389 s, der Endpunkt brach bei 300 s ab — der Kunde
bekam für diese Website überhaupt kein Ergebnis, sondern einen Fehler. Gemessen
wurde: 315 der 320 s steckten in EINEM Check je Unterseite. Der
Barrierefreiheits-Check startete für JEDE Unterseite einen eigenen, vollständigen
Crawl derselben Website (88 Abrufe je Seite), weil "eine Session ist da" als
Auftrag galt, die halbe Website nachzuladen.

Drei Dinge müssen halten:

1) Der Barrierefreiheits-Check crawlt NICHT, nur weil er eine Session bekommt.
   Der seitenweite Crawl braucht ein ausdrückliches seitenweit=True.
2) Ein einzelner hängender Check reißt weder seine Seite noch den Scan mit.
3) Läuft die Frist ab, kommt ein TEILERGEBNIS mit ehrlichem Hinweis zurück —
   kein leeres Ergebnis und keine Exception.
"""
import asyncio
import os
import sys

import pytest
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class _Seite:
    def __init__(self, url, klasse="pflichtseite"):
        self.url = url
        self.klasse = klasse


class _Entdeckung:
    def __init__(self, seiten):
        self.seiten = seiten
        self.sitemap_gefunden = False
        self.hinweis = ""


# ============================================================================
# 1) Ursache: eine Session ist kein Auftrag zum Crawlen
# ============================================================================

class TestKeinCrawlOhneAnsage:
    def test_session_allein_loest_keinen_seitenweiten_crawl_aus(self, monkeypatch):
        import compliance_engine.checks.barrierefreiheit_check as bc

        gerufen = []

        async def darf_nicht(*a, **kw):
            gerufen.append(a)
            return []

        monkeypatch.setattr(bc, "_discover_pages", darf_nicht)
        soup = BeautifulSoup("<html lang='de'><head><title>T</title></head>"
                             "<body><h1>x</h1></body></html>", "html.parser")

        asyncio.run(bc.check_barrierefreiheit_compliance(
            "https://x.de/impressum", soup, session=object()))

        assert gerufen == [], (
            "Der Barrierefreiheits-Check hat einen seitenweiten Crawl gestartet, "
            "obwohl nur eine Session mitgegeben wurde — genau der Fehler, der den "
            "Scan von 51 s auf 389 s gebracht hat."
        )

    def test_seitenweit_true_crawlt_weiterhin(self, monkeypatch):
        """Die Option bleibt benutzbar — sie ist nur nicht mehr der Standard."""
        import compliance_engine.checks.barrierefreiheit_check as bc

        gerufen = []

        async def merke(url, session, *a, **kw):
            gerufen.append(url)
            return []

        monkeypatch.setattr(bc, "_discover_pages", merke)
        soup = BeautifulSoup("<html lang='de'><head><title>T</title></head>"
                             "<body><h1>x</h1></body></html>", "html.parser")

        asyncio.run(bc.check_barrierefreiheit_compliance(
            "https://x.de/impressum", soup, session=object(), seitenweit=True))

        assert gerufen == ["https://x.de/impressum"]


# ============================================================================
# 2) Ein hängender Check kostet seinen Befund, nicht die Seite
# ============================================================================

class TestCheckZeitbudget:
    def test_haengender_check_beendet_die_seite_nicht(self, monkeypatch):
        import compliance_engine.scanner as sm
        from compliance_engine.scanner import ComplianceScanner

        s = ComplianceScanner.__new__(ComplianceScanner)
        s.session = None
        s._startseiten_html = None
        monkeypatch.setattr(ComplianceScanner, "CHECK_ZEITBUDGET", 0.2)

        async def haengt(*a, **kw):
            await asyncio.sleep(30)
            return []

        async def liefert(*a, **kw):
            return [{
                "category": "datenschutz", "severity": "warning",
                "title": "Befund der schnellen Prüfung", "description": "",
                "risk_euro": 100, "recommendation": "", "legal_basis": "",
            }]

        async def fake_fetch(self_, url):
            return {"url": url, "status_code": 200,
                    "content": "<html><body>x</body></html>", "headers": {}}

        monkeypatch.setattr(ComplianceScanner, "_fetch_page", fake_fetch)
        import compliance_engine.checks.barrierefreiheit_check as bc
        import compliance_engine.checks.ki_bild_nachweis_check as kb
        import compliance_engine.checks.shop_check as sh
        import compliance_engine.declarative_check_runner as dc
        monkeypatch.setattr(bc, "check_barrierefreiheit_compliance_smart", haengt)
        monkeypatch.setattr(kb, "check_ki_bild_nachweis", haengt)
        monkeypatch.setattr(sh, "check_shop_compliance", haengt)
        monkeypatch.setattr(dc, "run_declarative_checks", liefert)

        issues = asyncio.run(s._pruefe_unterseite("https://x.de/kontakt", "interaktion"))

        titel = [i.title for i in issues]
        assert "Befund der schnellen Prüfung" in titel, (
            "Der schnelle Check muss liefern, auch wenn drei andere hängen."
        )


# ============================================================================
# 3) Frist abgelaufen → Teilergebnis, nicht Totalausfall
# ============================================================================

class TestTeilergebnis:
    def _lauf(self, monkeypatch, zeitbudget, dauer_je_seite):
        import compliance_engine.page_discovery as pd
        from compliance_engine.scanner import ComplianceScanner

        s = ComplianceScanner.__new__(ComplianceScanner)
        s.session = None
        s._startseiten_html = "<html></html>"
        monkeypatch.setattr(ComplianceScanner, "MEHRSEITEN_MINDESTZEIT", 0.1)

        async def fake_scan(url, progress_token=None):
            return {"url": url, "issues": [], "compliance_score": 50,
                    "pillar_scores": [], "pillar_status": {}}

        async def fake_entdecke(url, html=None, session=None, max_seiten=10):
            return _Entdeckung([_Seite(f"https://x.de/s{n}") for n in range(4)])

        async def langsam(url, klasse):
            await asyncio.sleep(dauer_je_seite)
            return []

        s.scan_website = fake_scan
        s._pruefe_unterseite = langsam
        monkeypatch.setattr(pd, "entdecke_seiten", fake_entdecke)

        return asyncio.run(s.scan_website_multipage(
            "https://x.de", max_seiten=4, zeitbudget=zeitbudget))

    def test_abgelaufene_frist_liefert_ergebnis_statt_fehler(self, monkeypatch):
        ergebnis = self._lauf(monkeypatch, zeitbudget=0.0, dauer_je_seite=30)

        assert ergebnis.get("url") == "https://x.de"
        assert "error" not in ergebnis
        seiten = ergebnis.get("pages_scanned") or {}
        assert seiten.get("unvollstaendig") is True, (
            "Ein Teilergebnis muss sich als solches ausweisen — sonst liest der "
            "Kunde 'geprüft, alles sauber', wo nichts geprüft wurde."
        )
        assert len(seiten.get("nicht_geprueft") or []) == 4
        assert "nicht geprueft werden" in (seiten.get("zeitnot_hinweis") or "")

    def test_reicht_die_zeit_bleibt_das_ergebnis_vollstaendig(self, monkeypatch):
        ergebnis = self._lauf(monkeypatch, zeitbudget=30.0, dauer_je_seite=0)

        seiten = ergebnis.get("pages_scanned") or {}
        assert seiten.get("unvollstaendig") is None
        assert seiten.get("total") == 5  # Startseite + 4 Unterseiten
