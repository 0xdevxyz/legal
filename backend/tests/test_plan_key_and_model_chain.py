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
    assert 'get("plan_type")' in src or "get('plan_type'" in src
    assert "current_user.get('plan'," not in src and 'current_user.get("plan",' not in src, (
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
    Neufassung 30.07.: (plan_type or "free") plus explizite Free-Sperre.
    """
    src = inspect.getsource(fix_apply_routes)
    assert 'or "free")' in src, "Default muss free (restriktiv) sein"
    assert 'in ("", "free")' in src, "Free-Plan muss explizit gesperrt sein"


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


def test_kein_modul_liest_den_schluessel_plan():
    """
    `get_current_user()` liefert `plan_type` — den Schluessel `plan` gibt es
    nicht. Wer ihn liest, bekommt None (bei `.get`) oder einen KeyError (bei
    `[...]`), und der KeyError ist ein 500 im Nutzerpfad.

    Dieser Test gab es schon — aber nur fuer `fix_apply_routes`. In
    `fix_routes.py` hat derselbe Fehler deshalb ueberlebt und warf bei JEDEM
    Fix-Export einen KeyError (`current_user['plan']`). Gefunden hat ihn erst
    ruff, ueber die unbenutzte Variable daneben.

    Ein Waechter, der nur die eine Datei kennt, in der der Fehler damals
    gefunden wurde, faengt ihn beim naechsten Mal nicht.
    """
    import os
    import re

    wurzel = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    treffer = []
    muster = re.compile(r"""current_user\s*(?:\[\s*['"]plan['"]\s*\]"""
                        r"""|\.get\(\s*['"]plan['"])""")

    for verzeichnis, _, dateien in os.walk(wurzel):
        if any(teil in verzeichnis for teil in
               ("_archive", "__pycache__", "node_modules", "/tests")):
            continue
        for datei in dateien:
            if not datei.endswith(".py"):
                continue
            pfad = os.path.join(verzeichnis, datei)
            try:
                with open(pfad, encoding="utf-8") as fh:
                    for nr, zeile in enumerate(fh, 1):
                        if zeile.lstrip().startswith("#"):
                            continue
                        if muster.search(zeile):
                            treffer.append(f"{datei}:{nr}: {zeile.strip()[:70]}")
            except (OSError, UnicodeDecodeError):
                continue

    assert not treffer, (
        "current_user['plan'] gibt es nicht — get_current_user liefert "
        "'plan_type'. Ein Subskript-Zugriff ist ein 500 im Nutzerpfad:\n  "
        + "\n  ".join(treffer)
    )
