"""
Waechter fuer die Kette Scan -> Worklist -> Auslieferung beim Kontrast-Fix.

Ein Fix-Generator ohne Antriebsstrang ist wertlos. Die Kette hat vier Glieder,
jedes in einer anderen Datei, und keines davon faellt beim Testen der Teile
auf, wenn es reisst:

    axe_scanner.scan_page(mit_kontrast_fixes=True)
        -> AxeScanResult.kontrast_fixes
    barrierefreiheit_check._run_axe_core_safe
        -> Befund mit metadata.source == "complyo-kontrast-fix"
    accessibility_post_scan_processor._derive_document_fixes
        -> document_fix vom Typ "kontrast-css", Status 'pending'
    widget_routes.get_fix_manifest
        -> css_rules im Manifest, die die Channels anwenden

Statische Waechter nach dem Muster von test_git_integration_auth.py: sie
brauchen weder Browser noch Datenbank und schlagen an, sobald jemand ein Glied
umbenennt oder herausnimmt.
"""
import os
import re
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _lese(*pfad: str) -> str:
    with open(os.path.join(_BACKEND, *pfad), encoding="utf-8") as fh:
        return fh.read()


class TestGliedEinsScanner:
    def test_scan_page_kann_kontrast_fixes_erzeugen(self):
        src = _lese("compliance_engine", "axe_scanner.py")
        assert "mit_kontrast_fixes" in src
        assert "verifizierte_kontrast_fixes" in src

    def test_run_axe_scan_schaltet_sie_standardmaessig_ein(self):
        """Ausgeschaltet waere der Fix gebaut und nie benutzt."""
        src = _lese("compliance_engine", "axe_scanner.py")
        m = re.search(r"async def run_axe_scan\((.*?)\) ->", src, re.S)
        assert m, "run_axe_scan nicht gefunden"
        assert re.search(r"mit_kontrast_fixes:\s*bool\s*=\s*True", m.group(1))

    def test_ergebnis_traegt_das_feld(self):
        from compliance_engine.axe_scanner import AxeScanResult
        assert "kontrast_fixes" in AxeScanResult.__dataclass_fields__


class TestGliedZweiCheck:
    def test_check_reicht_die_fixes_als_befund_weiter(self):
        src = _lese("compliance_engine", "checks", "barrierefreiheit_check.py")
        assert "complyo-kontrast-fix" in src
        assert "als_css_regeln" in src

    def test_befund_erzeugt_keinen_falschen_rechtsdruck(self):
        """Der Traeger-Befund ist ein Hinweis, kein zusaetzlicher Verstoss."""
        src = _lese("compliance_engine", "checks", "barrierefreiheit_check.py")
        block = src[src.index("complyo-kontrast-fix") - 1800:src.index("complyo-kontrast-fix")]
        assert '"severity": "info"' in block
        assert '"risk_euro": 0' in block


class TestGliedDreiProzessor:
    def test_prozessor_macht_daraus_einen_dokumentweiten_fix(self):
        src = _lese("accessibility_post_scan_processor.py")
        assert "kontrast-css" in src
        assert "_kontrast_fix_aus_issues" in src

    def test_kontrast_geht_nicht_automatisch_live(self):
        """
        Farbe ist Gestaltung. Ein Skip-Link ergaenzt etwas Unsichtbares, eine
        geaenderte Linkfarbe sieht der Betreiber sofort — also erst freigeben.
        """
        src = _lese("accessibility_post_scan_processor.py")
        block = src[src.index("_kontrast_fix_aus_issues"):]
        block = block[:block.index("# ====")] if "# ====" in block else block
        assert '"status": "pending"' in block

    def test_saver_respektiert_den_status_des_fixes(self):
        src = _lese("accessibility_fix_saver.py")
        assert "fix.get('status') or status" in src

    def test_status_wird_beim_konflikt_nachgezogen(self):
        """Sonst bleibt nach einem erneuten Scan ein alter Freigabestand stehen."""
        src = _lese("accessibility_fix_saver.py")
        assert "status = EXCLUDED.status" in src


class TestGliedVierManifest:
    def test_manifest_faltet_die_regeln_in_css_rules(self):
        src = _lese("widget_routes.py")
        assert "kontrast-css" in src
        block = src[src.index("css_rules = ["):]
        assert 'payload"].get("rules")' in block[:900]

    def test_kontrast_taucht_nicht_doppelt_als_document_fix_auf(self):
        src = _lese("widget_routes.py")
        assert '("css-rule", "kontrast-css")' in src

    def test_manifest_liefert_nur_freigegebenes(self):
        """
        Der Sicherungsgurt der ganzen Kette: solange niemand zustimmt, aendert
        sich auf der Kundenseite nichts.
        """
        src = _lese("widget_routes.py")
        block = src[src.index("get_fix_manifest"):]
        block = block[:block.index("etag =")]
        assert "get_document_fixes_for_site(site_id, status='approved')" in block


class TestFormatPasstZumRuntime:
    def test_runtime_erwartet_selector_und_declarations(self):
        src = _lese("widgets", "a11y_remediation.js")
        assert "r.selector" in src and "r.declarations" in src

    def test_generator_liefert_genau_das(self):
        from compliance_engine.kontrast_fixes import als_css_regeln
        regeln = als_css_regeln([{
            "loesbar": True, "bestaetigt": True, "vorschlag": "#6a6a6a",
            "selektoren": [".a", ".b"],
        }])
        assert [set(r) for r in regeln] == [{"selector", "declarations"}] * 2
