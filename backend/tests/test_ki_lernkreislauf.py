"""
Wächtertests für den KI-Lernkreislauf (Befunde vom 11.08.2026).

Hintergrund:
1) ai_legal_routes._classify_update_background las aus der nie existenten
   Tabelle monitored_websites; ein Pauschal-except schluckte den Fehler und
   die Klassifizierung fiel seit April still aus (ai_classifications leer,
   Dashboard bekam keine classification_id, Feedback-/Lernkreislauf stand).
2) ai_review_engine.generate_individual_solution lief IMMER gegen das LLM —
   der in main_production initialisierte Solution-Cache war eine Attrappe.
3) compliance_engine.hybrid_validator nutzte einen direkten anthropic-Client
   mit nie gesetztem ANTHROPIC_API_KEY — "KI für Grenzfälle" lief nie.
   Jetzt: OpenRouter (Key vorhanden), Fail-open auf Pattern-Fallback.
4) accessibility_alt_text_fixes speicherte approved/rejected + rejected_reason,
   wurde beim Generieren aber nie gelesen. Jetzt: Few-Shot-/Negativ-Beispiele
   im Prompt, fail-open bei DB-Fehlern.
5) AIModel-Enum benannte kimi-k2.5 als CLAUDE_SONNET/GPT4/GPT4_TURBO —
   jetzt ehrlich KIMI_K25 (alte Namen als deprecated Aliasse).
"""

import asyncio
import inspect
import json
import os
import types

import ai_review_engine
from compliance_engine import hybrid_validator as hv
from compliance_engine.ai_alt_text_generator import AIAltTextGenerator

BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def _run(coro):
    # asyncio.run() statt get_event_loop() — der globale Loop ist im
    # Gesamtlauf ggf. bereits geschlossen (siehe tests/test_ai_verification.py)
    return asyncio.run(coro)


# ============================================================================
# (a) Lernkreislauf-Riss: keine Query mehr auf monitored_websites
# ============================================================================

class TestKlassifizierungTabelle:
    def _source(self):
        with open(os.path.join(BACKEND_ROOT, "ai_legal_routes.py"), encoding="utf-8") as fh:
            return fh.read()

    def test_keine_query_auf_monitored_websites(self):
        """Die Tabelle monitored_websites gab es nie — jede Query darauf wirft."""
        src = self._source()
        assert "FROM monitored_websites" not in src, (
            "ai_legal_routes fragt wieder die nie existente Tabelle "
            "monitored_websites ab — das bricht die Hintergrund-Klassifizierung"
        )

    def test_background_task_nutzt_tracked_websites(self):
        src = self._source()
        start = src.find("async def _classify_update_background")
        assert start != -1, "_classify_update_background nicht gefunden"
        body = src[start:start + 6000]
        assert "FROM tracked_websites" in body, (
            "User-Context muss aus tracked_websites kommen (reale Tabelle)"
        )

    def test_teilschritte_haben_eigene_fehlerbehandlung(self):
        """
        Der alte Pauschal-except schluckte den Tabellenfehler und riss die
        komplette Klassifizierung mit ab. Die Teilschritte müssen getrennt
        abgesichert sein: User-Context-Fehler dürfen nicht zum Abbruch führen,
        Speicherfehler müssen als solche benannt im Log stehen.
        """
        src = self._source()
        start = src.find("async def _classify_update_background")
        body = src[start:src.find("# Export router", start)]
        assert body.count("except Exception") >= 3, (
            "Erwartet: eigene except-Blöcke je Teilschritt (Classifier laden, "
            "User-Context, KI-Aufruf, Speichern) statt eines Pauschal-except"
        )
        assert "klassifiziere ohne Kontext" in body, (
            "User-Context-Fehler muss abgefangen werden, ohne die "
            "Klassifizierung abzubrechen"
        )
        assert "ai_classifications" in body and "fehlgeschlagen" in body


# ============================================================================
# (b) Solution-Cache-Wiring in ai_review_engine
# ============================================================================

class _FakeSolutionCache:
    def __init__(self, cached=None):
        self.cached = cached
        self.get_calls = []
        self.store_calls = []

    async def get_cached_solution(self, category, title, description, use_fuzzy=True):
        self.get_calls.append({"category": category, "title": title,
                               "description": description})
        return self.cached

    async def store_solution(self, category, title, description, solution,
                             model=None):
        self.store_calls.append({"category": category, "title": title,
                                 "solution": solution, "model": model})
        return True


_ISSUE = {
    "category": "datenschutz",
    "title": "Fehlende Datenschutzerklärung",
    "description": "Auf der Seite wurde keine Datenschutzerklärung gefunden.",
}
_SCAN_CONTEXT = {"url": "https://example.de", "cms": "WordPress"}


class TestSolutionCacheWiring:
    def setup_method(self):
        self._orig_cache = ai_review_engine.solution_cache
        self._orig_json = ai_review_engine._call_ai_json
        self._orig_plain = ai_review_engine._call_ai

    def teardown_method(self):
        ai_review_engine.solution_cache = self._orig_cache
        ai_review_engine._call_ai_json = self._orig_json
        ai_review_engine._call_ai = self._orig_plain

    def _verbiete_llm(self):
        async def kein_llm(*args, **kwargs):
            raise AssertionError("LLM-Call trotz Cache-Hit")
        ai_review_engine._call_ai_json = kein_llm
        ai_review_engine._call_ai = kein_llm

    def test_cache_hit_ueberspringt_llm(self):
        """Cache-Hit (strukturiertes JSON) → LLM wird NICHT aufgerufen."""
        gespeichert = {"ai_solution": "Aus dem Cache", "steps": ["1. Tun"],
                       "code_snippet": "<!-- cache -->" * 5}
        fake = _FakeSolutionCache(cached={
            "solution": json.dumps(gespeichert, ensure_ascii=False),
            "match_type": "exact", "usage_count": 3, "success_rate": 0.9,
        })
        ai_review_engine.solution_cache = fake
        self._verbiete_llm()

        result = _run(ai_review_engine.generate_individual_solution(_ISSUE, _SCAN_CONTEXT))

        assert result is not None
        assert result["ai_solution"] == "Aus dem Cache"
        assert result["steps"] == ["1. Tun"]
        assert len(fake.get_calls) == 1
        assert fake.store_calls == []

    def test_cache_hit_mit_fliesstext_altbestand(self):
        """Fließtext im Cache (Altbestand) → wird als ai_solution verwendet."""
        fake = _FakeSolutionCache(cached={
            "solution": "1. Datenschutzerklärung erstellen\n2. Verlinken",
            "match_type": "fuzzy", "usage_count": 1, "success_rate": 0.8,
        })
        ai_review_engine.solution_cache = fake
        self._verbiete_llm()

        result = _run(ai_review_engine.generate_individual_solution(_ISSUE, _SCAN_CONTEXT))

        assert result is not None
        assert "Datenschutzerklärung erstellen" in result["ai_solution"]

    def test_cache_miss_ruft_llm_und_speichert(self):
        """Cache-Miss → LLM liefert, Ergebnis landet im Cache (store_solution)."""
        fake = _FakeSolutionCache(cached=None)
        ai_review_engine.solution_cache = fake

        async def fake_llm_json(prompt, model, max_tokens=800):
            return {"ai_solution": "Neu generiert",
                    "steps": ["1.", "2.", "3."], "code_snippet": "<code/>"}
        ai_review_engine._call_ai_json = fake_llm_json

        result = _run(ai_review_engine.generate_individual_solution(_ISSUE, _SCAN_CONTEXT))

        assert result["ai_solution"] == "Neu generiert"
        assert len(fake.store_calls) == 1
        gespeichert = json.loads(fake.store_calls[0]["solution"])
        assert gespeichert["ai_solution"] == "Neu generiert"

    def test_cache_kategorie_hat_namespace(self):
        """
        Die Review-Engine speichert JSON, public_routes speichert Fließtext.
        Der review:-Namespace verhindert, dass ein Fuzzy-Match dem jeweils
        anderen Verbraucher das falsche Format liefert.
        """
        fake = _FakeSolutionCache(cached=None)
        ai_review_engine.solution_cache = fake

        async def fake_llm_json(prompt, model, max_tokens=800):
            return {"ai_solution": "x"}
        ai_review_engine._call_ai_json = fake_llm_json

        _run(ai_review_engine.generate_individual_solution(_ISSUE, _SCAN_CONTEXT))

        assert fake.get_calls[0]["category"].startswith("review:")
        assert fake.store_calls[0]["category"].startswith("review:")

    def test_cache_fehler_ist_fail_open(self):
        """Wirft der Cache, muss der normale LLM-Weg weiterlaufen."""
        class KaputterCache:
            async def get_cached_solution(self, **kwargs):
                raise RuntimeError("DB weg")

            async def store_solution(self, **kwargs):
                raise RuntimeError("DB weg")

        ai_review_engine.solution_cache = KaputterCache()

        async def fake_llm_json(prompt, model, max_tokens=800):
            return {"ai_solution": "Trotzdem generiert"}
        ai_review_engine._call_ai_json = fake_llm_json

        result = _run(ai_review_engine.generate_individual_solution(_ISSUE, _SCAN_CONTEXT))
        assert result["ai_solution"] == "Trotzdem generiert"


# ============================================================================
# (c) hybrid_validator: OpenRouter statt totem anthropic-Client, Fail-open
# ============================================================================

class TestHybridValidatorOpenRouter:
    def test_openrouter_statt_anthropic(self):
        src = inspect.getsource(hv)
        assert "openrouter.ai/api/v1/chat/completions" in src, (
            "hybrid_validator muss über OpenRouter gehen (OPENROUTER_API_KEY "
            "ist gesetzt, ANTHROPIC_API_KEY war es nie)"
        )
        assert "import anthropic" not in src, (
            "Der direkte anthropic-Client lief nie (Key fehlt im Deployment)"
        )
        assert "anthropic.Anthropic(" not in src
        assert 'os.getenv("OPENROUTER_API_KEY"' in src

    def _validator_ohne_init(self, api_key=""):
        v = hv.HybridValidator.__new__(hv.HybridValidator)
        v.api_key = api_key
        v.model = hv.VALIDATOR_MODEL
        v.uncertain_threshold = 0.6
        v.confident_threshold = 0.85
        return v

    def test_ohne_key_faellt_auf_pattern_zurueck(self):
        """Kein Key + unsicheres Pattern → Pattern-Ergebnis, kein Netz-Call."""
        v = self._validator_ohne_init(api_key="")

        class _StubAnalyzer:
            def _validate_field(self, field_name, field_config, text, soup):
                return types.SimpleNamespace(
                    found=False, confidence=0.3, extracted_value=None)
        v.analyzer = _StubAnalyzer()

        result = _run(v.validate_field("email", {}, "irgendein Text"))

        assert result.method_used == hv.ValidationMethod.PATTERN_ONLY
        assert result.found is False
        # Confidence wird reduziert, weil keine KI absichern konnte
        assert result.confidence < 0.3

    def test_ki_fehler_faellt_auf_pattern_zurueck(self, monkeypatch):
        """HTTP-Fehler beim OpenRouter-Call → Fail-open aufs Pattern-Ergebnis."""
        v = self._validator_ohne_init(api_key="test-key")

        class _KaputteSession:
            def __init__(self, *args, **kwargs):
                raise RuntimeError("kein Netz im Test")
        monkeypatch.setattr(hv.aiohttp, "ClientSession", _KaputteSession)

        pattern_result = types.SimpleNamespace(
            found=True, confidence=0.5, extracted_value="mail@example.de")
        result = _run(v._ai_validate_field("email", {}, "Text", pattern_result, None))

        assert result["found"] is True
        assert result["value"] == "mail@example.de"
        assert "KI-Error" in result["reasoning"]


# ============================================================================
# (d) Alt-Text-Lernschleife: Freigaben/Ablehnungen fließen in den Prompt
# ============================================================================

class _FakeAcquireCtx:
    def __init__(self, conn):
        self._conn = conn

    async def __aenter__(self):
        return self._conn

    async def __aexit__(self, *args):
        return False


class _FakePool:
    def __init__(self, conn):
        self._conn = conn

    def acquire(self):
        return _FakeAcquireCtx(self._conn)


class _FakeConn:
    """Liefert je nach Query Freigaben oder Ablehnungsgründe."""

    def __init__(self):
        self.queries = []

    async def fetch(self, query, *params):
        self.queries.append((query, params))
        if "'approved'" in query:
            return [
                {"suggested_alt": "Logo der Spedition Mahn in Rot"},
                {"suggested_alt": "LKW-Flotte auf dem Betriebshof"},
            ]
        if "'rejected'" in query:
            return [
                {"rejected_reason": "Zu generisch, Firmenname fehlt"},
            ]
        return []


class _KaputterPool:
    def acquire(self):
        raise RuntimeError("DB nicht erreichbar")


class TestAltTextLernschleife:
    def test_lernbeispiele_landen_im_prompt(self):
        conn = _FakeConn()
        gen = AIAltTextGenerator(api_key="test", db_pool=_FakePool(conn))

        examples = _run(gen._load_learning_examples(site_id="spedition-mahn-de"))
        assert examples["approved"] == [
            "Logo der Spedition Mahn in Rot",
            "LKW-Flotte auf dem Betriebshof",
        ]
        assert examples["rejected_reasons"] == ["Zu generisch, Firmenname fehlt"]
        # site_id-Weg parametrisiert die Query mit der Site
        assert all(p == ("spedition-mahn-de",) for _, p in conn.queries)

        prompt = gen._build_prompt("Startseite der Spedition", "de", examples)
        assert "FREIGEGEBENE" in prompt
        assert "Logo der Spedition Mahn in Rot" in prompt
        assert "ABGELEHNT" in prompt
        assert "Zu generisch, Firmenname fehlt" in prompt

    def test_host_zuordnung_ohne_site_id(self):
        conn = _FakeConn()
        gen = AIAltTextGenerator(api_key="test", db_pool=_FakePool(conn))

        examples = _run(gen._load_learning_examples(
            site_host=gen._host_from_url("https://www.spedition-mahn.de/img/logo.png")))

        assert examples["approved"], "Host-basierte Zuordnung muss Beispiele liefern"
        # Muster matchen Domain mit und ohne www.
        _, params = conn.queries[0]
        assert "%//spedition-mahn.de%" in params
        assert "%//www.spedition-mahn.de%" in params

    def test_db_fehler_ist_fail_open(self):
        gen = AIAltTextGenerator(api_key="test", db_pool=_KaputterPool())
        examples = _run(gen._load_learning_examples(site_id="egal"))
        assert examples == {"approved": [], "rejected_reasons": []}

        # Prompt ohne Beispiele enthält keine leeren Beispielblöcke
        prompt = gen._build_prompt(None, "de", examples)
        assert "FREIGEGEBENE" not in prompt
        assert "ABGELEHNT" not in prompt

    def test_ohne_site_kein_db_zugriff(self):
        gen = AIAltTextGenerator(api_key="test", db_pool=_KaputterPool())
        examples = _run(gen._load_learning_examples())
        assert examples == {"approved": [], "rejected_reasons": []}


# ============================================================================
# (e) Ehrliche Modellnamen + Metrik-Verdrahtung
# ============================================================================

class TestModellnamenUndMetriken:
    def test_aimodel_heisst_ehrlich_kimi(self):
        from ai_fix_engine.prompts_v2 import AIModel
        assert AIModel.KIMI_K25.value == "moonshotai/kimi-k2.5"
        # Alte Namen sind nur noch deprecated Aliasse desselben Members
        assert AIModel.CLAUDE_SONNET is AIModel.KIMI_K25
        assert AIModel.GPT4 is AIModel.KIMI_K25
        assert AIModel.GPT4_TURBO is AIModel.KIMI_K25

    def test_pricing_kennt_das_echte_modell(self):
        from ai_fix_engine.prompts_v2 import AIModel
        from ai_fix_engine.unified_fix_engine import AIApiClient
        client = AIApiClient()
        assert AIModel.KIMI_K25.value in client.pricing
        # Die alten Claude-/GPT-4-Preise (3/15, 30/60, 10/30) waren Fiktion
        preis = client.pricing[AIModel.KIMI_K25.value]
        assert preis["input"] < 3.0 and preis["output"] < 15.0

    def test_openrouter_zaehler_ist_verdrahtet(self):
        """Die echten Verbraucher müssen openrouter_requests_total zählen."""
        src_review = inspect.getsource(ai_review_engine)
        assert "openrouter_requests_total" in src_review
        assert '_openrouter_counter.labels(status="success").inc()' in src_review

        import compliance_engine.ai_alt_text_generator as altgen
        src_alt = inspect.getsource(altgen)
        assert "openrouter_requests_total" in src_alt
        assert '_openrouter_counter.labels(status="success").inc()' in src_alt

        src_hv = inspect.getsource(hv)
        assert "openrouter_requests_total" in src_hv
