"""Kein KI-Aufruf ohne Budget (15.09.2026).

Gemessen an diesem Tag: der complyo-Schluessel verbrauchte laut OpenRouter
0,196 USD, `ki:kosten:global` in Redis buchte im selben Zeitraum 0,141 USD.
Rund 30 % liefen an jeder Kontrolle vorbei, weil neun Aufrufstellen sich ihren
eigenen Zugang zum Anbieter gebaut hatten und den Deckel nie fragten. Ein
Deckel, den eine Aufrufstelle umgehen kann, ist kein Deckel.

Diese Tests halten den Zustand fest, den der Umbau hergestellt hat: es gibt
eine Engstelle (`ki_zugang.py`), und jede Datei, die trotzdem selbst zum
Anbieter spricht, muss hier namentlich stehen UND nachweislich am Budget
haengen. Eine neue Datei faellt durch, ohne dass jemand daran denken muss.
"""
import ast
import asyncio
import os
import re
import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

# Zeichen, an denen ein eigener Zugang zum Anbieter erkennbar ist.
EIGENER_ZUGANG = ("chat/completions", "api/v1/embeddings", "AsyncOpenAI(")

# Die Engstelle selbst.
ENGSTELLE = "ki_zugang.py"

# Aeltere Aufrufstellen, die ihren Zugang noch selbst aufbauen, aber
# nachweislich `ai_budget` fragen und buchen. Sie sind geduldet, nicht
# gewuenscht: wer eine davon anfasst, stellt sie auf ki_zugang um und streicht
# sie hier. Die Liste darf schrumpfen, nie wachsen.
GEDULDET_MIT_EIGENEM_BUDGET = {
    "ai_act_analyzer.py",
    "ai_document_generator.py",
    "ai_legal_classifier.py",
    "compliance_engine/ai_alt_text_generator.py",
    "compliance_engine/hybrid_validator.py",
    "legal_text_generator.py",
}

# Nicht ausgeliefert: Altbestand und Tests.
AUSGENOMMEN = ("tests/", "_archive", "__pycache__", "/venv/", "/.venv/")


def quelldateien():
    for pfad in sorted(BACKEND.rglob("*.py")):
        rel = pfad.relative_to(BACKEND).as_posix()
        if any(a in "/" + rel for a in AUSGENOMMEN):
            continue
        yield rel, pfad


def dateien_mit_eigenem_zugang():
    treffer = []
    for rel, pfad in quelldateien():
        try:
            text = pfad.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if any(z in text for z in EIGENER_ZUGANG):
            treffer.append(rel)
    return treffer


class TestNurEineEngstelle:
    def test_keine_unbekannte_stelle_spricht_selbst_mit_dem_anbieter(self):
        gefunden = set(dateien_mit_eigenem_zugang())
        erlaubt = GEDULDET_MIT_EIGENEM_BUDGET | {ENGSTELLE}
        neu = gefunden - erlaubt
        assert not neu, (
            "Diese Dateien bauen sich einen eigenen Zugang zum KI-Anbieter und "
            "umgehen damit den Budgetdeckel: " + ", ".join(sorted(neu)) +
            ". Ueber ki_zugang.chat() rufen."
        )

    def test_geduldete_liste_ist_nicht_verwaist(self):
        # Eine Ausnahmeliste, die auf nicht mehr existierende Dateien zeigt,
        # verdeckt spaeter echte Treffer.
        gefunden = set(dateien_mit_eigenem_zugang())
        verwaist = GEDULDET_MIT_EIGENEM_BUDGET - gefunden
        assert not verwaist, (
            "Diese Eintraege sind unnoetig geworden und gehoeren aus der Liste: "
            + ", ".join(sorted(verwaist))
        )

    @pytest.mark.parametrize("rel", sorted(GEDULDET_MIT_EIGENEM_BUDGET))
    def test_jede_geduldete_stelle_fragt_das_budget(self, rel):
        text = (BACKEND / rel).read_text(encoding="utf-8", errors="replace")
        assert "ai_budget" in text, f"{rel} steht auf der Ausnahmeliste, fragt aber kein Budget"
        assert "budget_frei" in text, f"{rel} bucht vielleicht, fragt aber nicht vorher"
        assert "kosten_buchen" in text, f"{rel} fragt vielleicht, bucht aber nicht"


class TestEngstelleSelbst:
    def test_fragt_vor_dem_aufruf_und_bucht_danach(self):
        quelle = (BACKEND / ENGSTELLE).read_text(encoding="utf-8")
        baum = ast.parse(quelle)
        namen = {
            k.func.attr
            for k in ast.walk(baum)
            if isinstance(k, ast.Call) and isinstance(k.func, ast.Attribute)
        }
        assert "budget_frei" in namen, "ki_zugang fragt das Budget nicht"
        assert "kosten_buchen" in namen, "ki_zugang bucht die Kosten nicht"
        assert "kosten_eur" in namen, "ki_zugang rechnet die Kosten nicht aus"

    def test_setzt_immer_einen_app_namen(self):
        # Ohne X-Title steht der Posten in der Abrechnung des Anbieters als
        # "Unknown" und laesst sich keinem Zweck zuordnen. Genau daran ist der
        # Verbrauch am 15.09.2026 zuerst aufgefallen.
        import ki_zugang
        kopf = ki_zugang._kopfzeilen("Probe")
        assert kopf["X-Title"] == "Complyo Probe"


class TestBudgetSperrtWirklich:
    def _chat(self, monkeypatch, frei):
        import ki_zugang
        from compliance_engine import ai_budget

        async def fake_frei(*a, **k):
            return frei

        gebucht = []

        async def fake_buchen(user_id, betrag):
            gebucht.append(betrag)

        monkeypatch.setattr(ai_budget, "budget_frei", fake_frei)
        monkeypatch.setattr(ai_budget, "kosten_buchen", fake_buchen)
        monkeypatch.setenv("OPENROUTER_API_KEY", "testschluessel")
        return ki_zugang, gebucht

    def test_ohne_budget_kein_netzverkehr(self, monkeypatch):
        import aiohttp
        ki_zugang, _ = self._chat(monkeypatch, frei=False)

        class VerboteneSitzung:
            def __init__(self, *a, **k):
                raise AssertionError("Bei gesperrtem Budget darf kein Aufruf rausgehen")

        monkeypatch.setattr(aiohttp, "ClientSession", VerboteneSitzung)
        with pytest.raises(ki_zugang.BudgetErschoepft):
            asyncio.run(ki_zugang.chat(
                model="anthropic/claude-haiku-4.5",
                messages=[{"role": "user", "content": "x"}],
                zweck="Probe",
            ))

    def test_erfolg_bucht_die_echten_tokens(self, monkeypatch):
        import aiohttp
        ki_zugang, gebucht = self._chat(monkeypatch, frei=True)
        gesendet = {}

        class FakeAntwort:
            status = 200

            async def json(self):
                return {
                    "choices": [{"message": {"content": "hallo"}}],
                    "usage": {"prompt_tokens": 1000, "completion_tokens": 500},
                }

            async def __aenter__(self):
                return self

            async def __aexit__(self, *a):
                return False

        class FakeSitzung:
            def __init__(self, *a, **k):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *a):
                return False

            def post(self, url, headers=None, json=None, timeout=None):
                gesendet["url"] = url
                gesendet["kopf"] = headers
                return FakeAntwort()

        monkeypatch.setattr(aiohttp, "ClientSession", FakeSitzung)
        antwort = asyncio.run(ki_zugang.chat(
            model="anthropic/claude-haiku-4.5",
            messages=[{"role": "user", "content": "x"}],
            zweck="Probe",
        ))
        assert antwort.erfolg and antwort.inhalt == "hallo"
        assert antwort.prompt_tokens == 1000 and antwort.completion_tokens == 500
        # Haiku 4.5: 1000 * 0.000001 + 500 * 0.000005 = 0,0035 USD -> * 0,92
        assert gebucht and abs(gebucht[0] - 0.00322) < 1e-6, gebucht
        assert gesendet["kopf"]["X-Title"] == "Complyo Probe"

    def test_fehlschlag_bucht_nichts(self, monkeypatch):
        import aiohttp
        ki_zugang, gebucht = self._chat(monkeypatch, frei=True)

        class FakeAntwort:
            status = 500

            async def text(self):
                return "kaputt"

            async def __aenter__(self):
                return self

            async def __aexit__(self, *a):
                return False

        class FakeSitzung:
            def __init__(self, *a, **k):
                pass

            async def __aenter__(self):
                return self

            async def __aexit__(self, *a):
                return False

            def post(self, *a, **k):
                return FakeAntwort()

        monkeypatch.setattr(aiohttp, "ClientSession", FakeSitzung)
        antwort = asyncio.run(ki_zugang.chat(
            model="anthropic/claude-haiku-4.5",
            messages=[{"role": "user", "content": "x"}],
            zweck="Probe",
        ))
        assert antwort.erfolg is False
        assert "500" in (antwort.fehler or "")
        assert gebucht == [], "Ein fehlgeschlagener Aufruf darf nichts buchen"


class TestPreiseSindBekannt:
    """Ein Deckel, der Phantomkosten zaehlt, sperrt zu frueh.

    `ai_budget.kosten_eur` rechnet unbekannte Modelle mit dem teuersten
    bekannten Satz. Das ist als Sicherung richtig, aber als Dauerzustand
    schaedlich: am 15.09.2026 buchte ein Einordnungsaufruf mit gpt-4o-mini
    0,018 USD statt 0,0008 USD, Faktor 20. Wer so misst, sperrt Aufrufe, die
    nichts gekostet haetten, und schaltet den Deckel am Ende ganz ab.
    """

    MODELLMUSTER = re.compile(
        r'"((?:anthropic|openai|moonshotai|google|meta-llama|mistralai)/[A-Za-z0-9.:\-]+)"'
        r'|"((?:gpt|text-embedding)-[A-Za-z0-9.\-]+)"'
    )

    def modelle_im_quelltext(self):
        gefunden = {}
        for rel, pfad in quelldateien():
            try:
                text = pfad.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for treffer in self.MODELLMUSTER.finditer(text):
                name = treffer.group(1) or treffer.group(2)
                gefunden.setdefault(name, set()).add(rel)
        return gefunden

    def test_jedes_benutzte_modell_hat_einen_preis(self):
        from compliance_engine import ai_budget

        gefunden = self.modelle_im_quelltext()
        # Die Preistabelle selbst nennt naturgemaess alle Namen.
        ohne_preis = {
            name: sorted(dateien - {"compliance_engine/ai_budget.py"})
            for name, dateien in gefunden.items()
            if name not in ai_budget.PREISE_USD_JE_TOKEN
        }
        ohne_preis = {n: d for n, d in ohne_preis.items() if d}
        assert not ohne_preis, (
            "Diese Modelle werden benutzt, stehen aber nicht in "
            "ai_budget.PREISE_USD_JE_TOKEN und werden deshalb mit dem "
            "teuersten bekannten Satz gerechnet: "
            + "; ".join(f"{n} (in {', '.join(d)})" for n, d in sorted(ohne_preis.items()))
        )

    def test_unbekanntes_modell_bleibt_teuer_gerechnet(self):
        # Die Sicherung selbst muss bleiben: ein Modell, das niemand
        # eingetragen hat, wird lieber zu teuer als zu billig gebucht.
        from compliance_engine import ai_budget

        teuer = ai_budget.kosten_eur("erfundenes/modell", 1_000_000, 0)
        haiku = ai_budget.kosten_eur("anthropic/claude-haiku-4.5", 1_000_000, 0)
        assert teuer > haiku

    def test_gpt_4o_mini_wird_realistisch_gerechnet(self):
        from compliance_engine import ai_budget

        # 2000 Prompt- + 800 Completion-Tokens, der uebliche Zuschnitt der
        # Wissens-Einordnung. Real rund 0,0008 USD, also weit unter einem Cent.
        kosten = ai_budget.kosten_eur("gpt-4o-mini", 2000, 800)
        assert kosten < 0.001, f"{kosten} EUR ist fuer gpt-4o-mini zu hoch gerechnet"
