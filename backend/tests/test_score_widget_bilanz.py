"""
Wächter für Score-Korrektheit und Widget-Selbstüberwachung (11.08.2026).

Vier stille Fehler aus derselben Familie: Zahlen, die niemand nachrechnet.

1) Der Mehrseiten-Rescore vergaß die UNVERIFIED-Säulen des Erst-Scans —
   scheiterte z.B. axe, wurde die Barrierefreiheits-Säule beim Rescore wieder
   100/compliant. Genau die falsche Entwarnung, gegen die das
   UNVERIFIED-Prinzip gebaut wurde.
2) pillar_scores landete je nach Scan-Weg als Dict ODER Liste in
   score_history; der Leser wertete alles außer dem Dict als critical=0 —
   und weil asyncpg JSONB ohne Codec als STRING liefert, tatsächlich JEDE
   Zeile. Jetzt: Scanner schreibt EIN Format (Liste wie der
   Einzelseiten-Scan), der Leser versteht den gesamten Altbestand.
3) Die Widget-Bilanz addierte `verfehlt` über alle apply()-Läufe auf
   (initial + 1000ms + 3000ms + MutationObserver) — gemessen: verfehlt=63
   bei erwartet=2. Und `erwartet` kannte nur 4 von 5 Fix-Arten
   (dokument_fixes fehlte beidseitig), die Quote war strukturell falsch.
4) Das Fix-Manifest zählte counts.document_fixes VOR dem Filter (4 bei 3
   ausgelieferten Einträgen), und /api/widgets/track hatte keinen einzigen
   Aufrufer bei leerer Zieltabelle.
"""
import asyncio
import json
import os
import shutil
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _lese(*teile):
    with open(os.path.join(_BACKEND, *teile), encoding="utf-8") as fh:
        return fh.read()


# ============================================================================
# 1) Mehrseiten-Rescore: unverified-Säulen werden durchgereicht,
#    pillar_scores bleibt im Listenformat des Einzelseiten-Scans
# ============================================================================

class _Seite:
    def __init__(self, url, klasse="pflicht"):
        self.url = url
        self.klasse = klasse


class _Entdeckung:
    def __init__(self, seiten):
        self.seiten = seiten
        self.sitemap_gefunden = True
        self.hinweis = ""


def _unterseiten_issue():
    from compliance_engine.scanner import ComplianceIssue
    i = ComplianceIssue(
        category="barrierefreiheit", severity="warning",
        title="Bilder ohne Alt-Text", description="",
        risk_euro=100, recommendation="", legal_basis="",
    )
    i.metadata = {"page_url": "https://x.de/agb"}
    return i


def _multipage_lauf(monkeypatch, pillar_status_erst):
    """Führt scan_website_multipage mit gemocktem Erst-Scan/Discovery aus."""
    import compliance_engine.page_discovery as pd
    import compliance_engine.scanner as scanner_mod
    from compliance_engine.scanner import ComplianceScanner

    s = ComplianceScanner.__new__(ComplianceScanner)
    s.session = None

    erst = {
        "url": "https://x.de",
        "issues": [],
        "compliance_score": 50,
        "pillar_scores": [
            {"pillar": p, "score": 0 if st == "unverified" else 100, "status": st}
            for p, st in pillar_status_erst.items()
        ],
        "pillar_status": dict(pillar_status_erst),
    }

    async def fake_scan(url, progress_token=None):
        return dict(erst)

    async def fake_entdecke(url, session=None, max_seiten=10):
        return _Entdeckung([_Seite("https://x.de/agb")])

    async def fake_unterseite(url, klasse):
        return [_unterseiten_issue()]

    s.scan_website = fake_scan
    s._pruefe_unterseite = fake_unterseite
    monkeypatch.setattr(pd, "entdecke_seiten", fake_entdecke)

    aufrufe = {}

    def fake_compute(issues, unverified_pillars=None):
        aufrufe["unverified"] = set(unverified_pillars or [])
        return {
            "overall_score": 42,
            "pillar_scores": {"accessibility": 0, "legal": 100,
                              "gdpr": 100, "cookies": 100},
            "pillar_status": {"accessibility": "unverified", "legal": "compliant",
                              "gdpr": "compliant", "cookies": "compliant"},
        }

    monkeypatch.setattr(scanner_mod.ScoreCalculator,
                        "compute_with_status", fake_compute)

    ergebnis = asyncio.run(s.scan_website_multipage("https://x.de", max_seiten=5))
    return ergebnis, aufrufe


class TestMultipageRescore:
    def test_unverified_saeulen_werden_durchgereicht(self, monkeypatch):
        """Scheitert axe im Erst-Scan, darf der Rescore nicht 100 rechnen."""
        _, aufrufe = _multipage_lauf(monkeypatch, {
            "accessibility": "unverified", "legal": "compliant",
            "gdpr": "compliant", "cookies": "compliant",
        })
        assert aufrufe["unverified"] == {"accessibility"}

    def test_ohne_unverified_ist_die_menge_leer(self, monkeypatch):
        _, aufrufe = _multipage_lauf(monkeypatch, {
            "accessibility": "partial", "legal": "compliant",
            "gdpr": "compliant", "cookies": "compliant",
        })
        assert aufrufe["unverified"] == set()

    def test_pillar_scores_bleibt_im_listenformat(self, monkeypatch):
        """
        EIN Format: dieselbe Liste [{pillar, score, status}] wie der
        Einzelseiten-Scan. Das rohe Dict {pillar: score} brach das Dashboard
        (.find() auf einem Dict) und erzeugte das zweite Format in
        score_history.
        """
        ergebnis, _ = _multipage_lauf(monkeypatch, {
            "accessibility": "unverified", "legal": "compliant",
            "gdpr": "compliant", "cookies": "compliant",
        })
        assert isinstance(ergebnis["pillar_scores"], list)
        for eintrag in ergebnis["pillar_scores"]:
            assert set(eintrag) == {"pillar", "score", "status"}
        saeulen = {e["pillar"]: e for e in ergebnis["pillar_scores"]}
        assert saeulen["accessibility"]["status"] == "unverified"
        assert saeulen["accessibility"]["score"] == 0

    def test_kein_rohes_dict_mehr_im_rescore(self):
        """Regressions-Stolperdraht direkt an der Quelle."""
        quelle = _lese("compliance_engine", "scanner.py")
        assert 'ergebnis["pillar_scores"] = _scores["pillar_scores"]' not in quelle


# ============================================================================
# 2) score_history-Leser: versteht den gesamten Altbestand
# ============================================================================

class TestScoreHistoryLeser:
    def test_zielformat_dict_mit_critical(self):
        from website_routes import _kritische_aus_pillar_scores
        assert _kritische_aus_pillar_scores(
            {"accessibility": 60, "critical_issues": 3}) == 3

    def test_altbestand_dict_ohne_critical(self):
        from website_routes import _kritische_aus_pillar_scores
        assert _kritische_aus_pillar_scores(
            {"gdpr": 76, "legal": 92, "cookies": 75, "accessibility": 0}) == 0

    def test_altbestand_listenform(self):
        from website_routes import _kritische_aus_pillar_scores
        assert _kritische_aus_pillar_scores(
            [{"pillar": "accessibility", "score": 60, "status": "partial"}]) == 0

    def test_asyncpg_liefert_jsonb_als_string(self):
        """
        Der eigentliche Befund: ohne set_type_codec kommt JSONB als str an —
        der frühere isinstance-Check lief damit auf JEDER Zeile ins Leere.
        """
        from website_routes import _kritische_aus_pillar_scores
        assert _kritische_aus_pillar_scores(
            json.dumps({"accessibility": 60, "critical_issues": 2})) == 2
        assert _kritische_aus_pillar_scores(
            json.dumps([{"pillar": "gdpr", "score": 18}])) == 0

    def test_muell_stuerzt_nicht_ab(self):
        from website_routes import _kritische_aus_pillar_scores
        assert _kritische_aus_pillar_scores(None) == 0
        assert _kritische_aus_pillar_scores("kein json {") == 0
        assert _kritische_aus_pillar_scores({"critical_issues": "quatsch"}) == 0


# ============================================================================
# 3) wirkung_routes: erwartet deckt alle FÜNF Arten ab
# ============================================================================

class _FakeConn:
    def __init__(self, ablage):
        self._ablage = ablage

    async def execute(self, sql, *args):
        self._ablage.append(args)


class _FakeAcquire:
    def __init__(self, ablage):
        self._ablage = ablage

    async def __aenter__(self):
        return _FakeConn(self._ablage)

    async def __aexit__(self, *exc):
        return False


class _FakePool:
    def __init__(self, ablage):
        self._ablage = ablage

    def acquire(self):
        return _FakeAcquire(self._ablage)


class _FakeRequest:
    def __init__(self, daten):
        self._roh = json.dumps(daten).encode()
        self.headers = {}

    async def body(self):
        return self._roh


def _melde(monkeypatch, erwartet):
    import wirkung_routes as wr
    ablage = []
    monkeypatch.setattr(wr, "db_pool", _FakePool(ablage))
    daten = {
        "pfad": "/leistungen/",
        "dokument_fixes": {"angewendet": 1, "verfehlt": 1, "unnoetig": 0},
        "erwartet": erwartet,
    }
    asyncio.run(wr.melde_wirkung("test-site", _FakeRequest(daten)))
    assert ablage, "INSERT wurde nicht abgesetzt"
    # Parameter-Reihenfolge: site_id, pfad, angewendet, verfehlt, erwartet, je_art
    return ablage[0]


class TestErwartetSumme:
    def test_dokument_fixes_zaehlen_zum_soll(self, monkeypatch):
        """Vorher: 4 von 5 Arten — jede Quote angewendet/erwartet war falsch."""
        args = _melde(monkeypatch, {
            "alt_texte": 2, "link_labels": 0, "struktur": 1,
            "css_regeln": 3, "dokument_fixes": 2,
        })
        assert args[4] == 8

    def test_fremde_schluessel_blasen_das_soll_nicht_auf(self, monkeypatch):
        """Der Endpunkt ist öffentlich — nur bekannte Arten zählen."""
        args = _melde(monkeypatch, {"alt_texte": 1, "totalfremd": 999})
        assert args[4] == 1

    def test_das_widget_schickt_das_soll_auch(self):
        """Beidseitig heißt beidseitig: die Gegenstelle im Widget."""
        js = _lese("widgets", "a11y_remediation.js")
        block = js[js.index("erwartet: {"):]
        block = block[:block.index("}")]
        assert "dokument_fixes" in block


# ============================================================================
# 4) widget_routes: Manifest-counts nach dem Filter, track-Route entfernt
# ============================================================================

class _FakeSaver:
    def __init__(self, pool):
        pass

    async def get_fixes_for_site(self, site_id, status="approved"):
        return []

    async def get_document_fixes_for_site(self, site_id, status="approved"):
        return [
            {"fix_type": "skip-link", "payload": {"label": "Zum Inhalt springen"}},
            {"fix_type": "struktur", "payload": {"fixes": [], "css_rules": []}},
            {"fix_type": "css-rule",
             "payload": {"selector": "a", "declarations": "color:#000"}},
            {"fix_type": "kontrast-css", "payload": {"rules": []}},
        ]

    async def get_link_fixes_for_site(self, site_id, status="approved"):
        return []


class TestFixManifest:
    def test_counts_zaehlen_die_gefilterte_liste(self, monkeypatch):
        """
        css-rule/kontrast-css werden separat als css_rules ausgeliefert.
        counts.document_fixes muss zur AUSGELIEFERTEN Liste passen — vorher
        stand da die Rohzahl (4 bei 2 Einträgen im Manifest).
        """
        import widget_routes as wroutes
        monkeypatch.setattr(wroutes, "AccessibilityFixSaver", _FakeSaver)
        monkeypatch.setattr(wroutes, "db_pool", object())
        antwort = asyncio.run(
            wroutes.get_fix_manifest("x-de", _FakeRequest({})))
        manifest = json.loads(antwort.body)
        assert manifest["counts"]["document_fixes"] == len(manifest["document_fixes"])
        assert manifest["counts"]["document_fixes"] == 2
        arten = {f["fix_type"] for f in manifest["document_fixes"]}
        assert "css-rule" not in arten and "kontrast-css" not in arten

    def test_track_route_ist_ersatzlos_entfernt(self):
        """Kein Aufrufer im ganzen Repo, Zieltabelle nach Monaten leer."""
        import widget_routes as wroutes
        pfade = {getattr(r, "path", "") for r in wroutes.router.routes}
        assert "/api/widgets/track" not in pfade
        assert not hasattr(wroutes, "WidgetTrackingEvent")


# ============================================================================
# 5) Widget-Bilanz: idempotent über apply()-Läufe (Node-gestützt)
# ============================================================================

_NODE = shutil.which("node")
_KEIN_NODE = ("node fehlt im Testcontainer — der Funktionstest läuft überall, "
              "wo node installiert ist (z.B. auf dem Host)")


def _js():
    return _lese("widgets", "a11y_remediation.js")


def _bilanz_block():
    """Extrahiert die in sich geschlossene Bilanz-Maschinerie des Widgets."""
    js = _js()
    start = js.index("// ---- Wirkungsbilanz")
    ende = js.index("// ---- Ende Wirkungsbilanz")
    return js[start:ende]


class TestBilanzQuelltext:
    """Läuft immer — auch ohne node."""

    def test_apply_beginnt_jeden_lauf_frisch(self):
        js = _js()
        block = js[js.index("function apply()"):js.index("var scheduled")]
        assert "beginneLauf()" in block
        assert "pruefeCssRegeln()" in block

    def test_css_regel_ohne_treffer_zaehlt_verfehlt(self):
        """
        trifft==0 war früher Niemandsland: weder angewendet noch verfehlt —
        ein Theme-Update, das den Selektor zerlegt, blieb unsichtbar.
        """
        js = _js()
        block = js[js.index("function pruefeCssRegeln()"):]
        block = block[:block.index("\n  }")]
        assert "trifft > 0" in block
        assert "zaehltVerfehlt('css_regeln'" in block
        # kein drittes Niemandsland mehr (frueher: else if (trifft < 0))
        assert "trifft < 0" not in block

    def test_verfehlt_laeuft_ueber_eindeutige_kennungen(self):
        js = _js()
        for kennung in ("'struktur:' + i", "'css:' + i", "'link:' + idx"):
            assert kennung in js, kennung

    def test_dokument_fixes_sind_in_der_bilanz(self):
        js = _js()
        for id_ in ("'skip-link'", "'landmark-main'", "'html-lang'"):
            assert "zaehltAngewendet('dokument_fixes', " + id_ in js, id_


@pytest.mark.skipif(_NODE is None, reason=_KEIN_NODE)
class TestBilanzVerhalten:
    def _node_lauf(self, quelle):
        lauf = subprocess.run([_NODE, "-e", quelle],
                              capture_output=True, text=True, timeout=30)
        assert lauf.returncode == 0, lauf.stderr or lauf.stdout
        return lauf.stdout

    def test_datei_ist_gueltiges_javascript(self):
        pfad = os.path.join(_BACKEND, "widgets", "a11y_remediation.js")
        lauf = subprocess.run([_NODE, "--check", pfad],
                              capture_output=True, text=True, timeout=30)
        assert lauf.returncode == 0, lauf.stderr

    def test_zaehlung_ist_idempotent_ueber_laeufe(self):
        """
        Der Kernbefund: verfehlt=63 bei erwartet=2, weil jeder Timer- und
        Observer-Lauf denselben fehlenden Selektor erneut zählte.
        """
        harness = _bilanz_block() + """
function pruefe(c, m) { if (!c) { console.error('FEHLER: ' + m); process.exit(1); } }
// Lauf 1: Ziel fehlt — zaehlt genau einmal, auch bei Doppelaufruf im Lauf
beginneLauf();
if (zaehltVerfehlt('struktur', 'struktur:0')) bilanz.struktur.verfehlt++;
if (zaehltVerfehlt('struktur', 'struktur:0')) bilanz.struktur.verfehlt++;
pruefe(bilanz.struktur.verfehlt === 1, 'gleicher Lauf zaehlt nicht doppelt');
// Lauf 2 und 3 (1000ms/3000ms): immer noch genau 1, nicht 2, nicht 3
beginneLauf();
if (zaehltVerfehlt('struktur', 'struktur:0')) bilanz.struktur.verfehlt++;
beginneLauf();
if (zaehltVerfehlt('struktur', 'struktur:0')) bilanz.struktur.verfehlt++;
pruefe(bilanz.struktur.verfehlt === 1, 'verfehlt darf ueber Laeufe nicht aufaddieren');
console.log('OK');
"""
        assert "OK" in self._node_lauf(harness)

    def test_angewendet_loest_verfehlt_ab_und_bleibt(self):
        harness = _bilanz_block() + """
function pruefe(c, m) { if (!c) { console.error('FEHLER: ' + m); process.exit(1); } }
// Lauf 1: verfehlt. Lauf 2: SPA-Hydration bringt das Ziel — angewendet.
beginneLauf();
if (zaehltVerfehlt('css_regeln', 'css:0')) bilanz.css_regeln.verfehlt++;
beginneLauf();
if (zaehltAngewendet('css_regeln', 'css:0')) bilanz.css_regeln.angewendet++;
pruefe(bilanz.css_regeln.angewendet === 1 && bilanz.css_regeln.verfehlt === 0,
       'angewendet loest verfehlt ab');
// Lauf 3: Rerender entfernt das Ziel wieder — bleibt trotzdem angekommen
beginneLauf();
if (zaehltVerfehlt('css_regeln', 'css:0')) bilanz.css_regeln.verfehlt++;
pruefe(bilanz.css_regeln.verfehlt === 0, 'einmal angekommen bleibt angekommen');
// unnoetig faellt nie auf Angewendetes zurueck (landmark-main nach Lauf 1)
beginneLauf();
if (zaehltAngewendet('dokument_fixes', 'landmark-main')) bilanz.dokument_fixes.angewendet++;
beginneLauf();
if (zaehltUnnoetig('dokument_fixes', 'landmark-main')) bilanz.dokument_fixes.unnoetig++;
pruefe(bilanz.dokument_fixes.unnoetig === 0 && bilanz.dokument_fixes.angewendet === 1,
       'angewendet gewinnt gegen unnoetig');
console.log('OK');
"""
        assert "OK" in self._node_lauf(harness)

    def test_widget_bricht_ohne_dom_sauber_ab(self):
        """Ganze Datei ausführen: ohne Skript-Tag kein Fehler, kein Effekt."""
        harness = ("var document = { currentScript: null, "
                   "querySelectorAll: function () { return []; } };\n"
                   + _js()
                   + "\nconsole.log('OK');")
        assert "OK" in self._node_lauf(harness)
