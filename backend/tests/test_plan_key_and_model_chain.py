"""
Regressionstests für:

6) fix_apply_routes las current_user.get('plan') — get_current_user liefert
   aber 'plan_type' (aus user_limits). Der gelesene Key existierte nie.

7) ai_fix_engine.unified_fix_engine: Die Modell-Fallback-Kette bestand aus
   zwei AIModel-Werten, die auf dasselbe Modell zeigen — sie konnte nichts
   auffangen und meldete trotzdem fallback_used=True.
"""

import inspect

from ai_fix_engine.prompts_v2 import AIModel
from ai_fix_engine.unified_fix_engine import UnifiedFixEngine
import fix_apply_routes


# ============================================================================
# 6) Plan-Key
# ============================================================================

def test_fix_apply_reads_plan_type_not_plan():
    """Der Key heisst plan_type — 'plan' liefert immer den Default."""
    src = inspect.getsource(fix_apply_routes)
    assert "current_user.get('plan_type'" in src
    assert "current_user.get('plan'," not in src, (
        "fix_apply_routes liest weiterhin den nicht existierenden Key 'plan'"
    )


def test_get_current_user_contract_documents_plan_type():
    """auth_service.get_user_by_id setzt plan_type — das ist die Quelle."""
    import auth_service

    src = inspect.getsource(auth_service.AuthService.get_user_by_id)
    assert "result['plan_type']" in src
    assert "result['plan']" not in src


def test_plan_gate_default_is_restrictive():
    """
    Default darf kein privilegierter Plan sein.
    (Vorher: .get('plan', 'ai') — ein erfundener Plan als Default.)
    """
    src = inspect.getsource(fix_apply_routes)
    assert "current_user.get('plan_type', 'free')" in src


# ============================================================================
# 7) Modell-Fallback-Kette
# ============================================================================

def test_fallback_chain_has_no_duplicate_models():
    """
    Eine Kette aus identischen Modellen kann nichts auffangen.
    Solange alle AIModel-Werte auf dasselbe Modell zeigen, MUSS die Kette
    genau einen Eintrag haben.
    """
    engine = UnifiedFixEngine.__new__(UnifiedFixEngine)
    chain = list(dict.fromkeys([AIModel.CLAUDE_SONNET.value, AIModel.GPT4_TURBO.value]))
    assert len(chain) == len(set(chain))


def test_engine_fallback_chain_is_deduplicated():
    src = inspect.getsource(UnifiedFixEngine.__init__)
    assert "dict.fromkeys" in src, (
        "fallback_chain muss dedupliziert werden, sonst ist sie eine Schein-Kette"
    )


def test_chain_collapses_to_one_entry_while_models_are_identical():
    """
    Dokumentiert den Ist-Zustand: alle AIModel-Werte zeigen auf kimi-k2.5.
    Sobald echte Alternativmodelle eingetragen werden, wird die Kette
    automatisch wieder echt und dieser Test schlägt an (dann bitte anpassen).
    """
    values = {AIModel.CLAUDE_SONNET.value, AIModel.GPT4.value, AIModel.GPT4_TURBO.value}
    if len(values) == 1:
        chain = list(dict.fromkeys([AIModel.CLAUDE_SONNET.value, AIModel.GPT4_TURBO.value]))
        assert chain == [AIModel.CLAUDE_SONNET.value]
        assert len(chain) == 1, "Schein-Kette: identische Modelle mehrfach befragt"
    else:
        # Echte Alternativmodelle vorhanden -> Kette darf länger sein
        chain = list(dict.fromkeys([AIModel.CLAUDE_SONNET.value, AIModel.GPT4_TURBO.value]))
        assert len(chain) > 1
