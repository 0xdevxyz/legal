"""Der Barrierefreiheits-Befund muss auf einen Knopf zeigen, den es gibt.

Gemeldet am 09.09.: "wenn ich auf den Button zum KI-Fix klicke, bekomme ich
einen Fehler — keine Fehlermeldung, es scrollt nur nach oben."

Nachgemessen: es verliess ueberhaupt keine Anfrage den Browser (nginx-Log: 0
Aufrufe auf /api/fix-jobs und /api/v2/fixes/*), und `fix_jobs` hatte noch nie
eine Zeile. Der Knopf im Barrierefreiheits-Block warf nur ein Fenster-Ereignis,
das zur Saeule "Barrierefreiheit" scrollte — daher das Springen nach oben. Die
Anleitung darueber sagte dann, man solle dort "KI-Fix starten" klicken. Diesen
Knopf gibt es fuer Barrierefreiheit nicht und kann es nicht geben:
usesDedicatedSolution() blendet den generischen KI-Fix fuer jeden solchen
Befund aus, weil das Widget der vorgesehene Weg ist.

Ein Verweis auf einen Knopf, den die eigene Ausblendlogik entfernt, faellt
keinem Test auf, der beide Seiten einzeln prueft. Dieser hier prueft den Weg.
"""

import os
import re

import pytest

BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_FRONTEND = os.path.join(BACKEND, "..", "dashboard-react")

ohne_frontend = pytest.mark.skipif(
    not os.path.isdir(_FRONTEND),
    reason="Frontend-Quelltext liegt nicht neben backend/ (z. B. im Container) — laeuft in CI",
)


def fquelle(*teile):
    return open(os.path.join(_FRONTEND, "src", *teile), encoding="utf-8").read()


def a11y_block(s: str) -> str:
    """Nur der Barrierefreiheits-Block der Handlungsschritte, ohne Kommentare.

    Kommentare fliegen raus, weil dieser Waechter pruefen soll, was der Nutzer
    LIEST — die Begruendung im Quelltext darf den alten Wortlaut ruhig nennen.
    """
    start = s.index("Barrierefreiheit beheben:")
    ende = s.index("</button>", start)
    block = s[start:ende]
    return re.sub(r"\{/\*.*?\*/\}", "", block, flags=re.S)


@ohne_frontend
class TestWegAusDemBefund:
    def test_knopf_fuehrt_zur_freigabeliste(self):
        block = a11y_block(fquelle("components", "dashboard", "ComplianceIssueCard.tsx"))
        assert "router.push('/accessibility/worklist')" in block

    def test_kein_verweis_auf_einen_ausgeblendeten_knopf(self):
        block = a11y_block(fquelle("components", "dashboard", "ComplianceIssueCard.tsx"))
        assert "KI-Fix starten" not in block

    def test_knopf_wirft_kein_ereignis_mehr_ins_leere(self):
        block = a11y_block(fquelle("components", "dashboard", "ComplianceIssueCard.tsx"))
        assert "scroll-to-pillar" not in block

    def test_das_ziel_gibt_es_wirklich(self):
        pfad = os.path.join(_FRONTEND, "src", "app", "accessibility", "worklist", "page.tsx")
        assert os.path.isfile(pfad), "Der Knopf zeigt auf eine Route ohne Seite"

    def test_generischer_ki_fix_bleibt_fuer_barrierefreiheit_ausgeblendet(self):
        """Die Ausblendung ist gewollt — sie ist der Grund, warum die Anleitung
        nicht auf den KI-Fix zeigen darf."""
        s = fquelle("components", "dashboard", "ComplianceIssueCard.tsx")
        assert "!usesDedicatedSolution(issue)" in s
        regel = s[s.index("const usesDedicatedSolution"):]
        regel = regel[:regel.index("\n};")]
        assert "category.includes('accessibility')" in regel
        assert "category.includes('barriere')" in regel
