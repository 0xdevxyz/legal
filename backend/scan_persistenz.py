"""Was von einem Scan in scan_history gehoert, an einer Stelle.

Anlass (25.09.2026): scan_history hat seit dem Anfang fuenf Spalten fuer die
Saeulenwerte, und in allen 51 Zeilen der Produktionsdatenbank waren sie leer.
Gelesen wurden sie die ganze Zeit, von `_latest_scan_pillars` im
Pflichten-Report. Der Leser prueft auf None und laesst die Angabe dann weg,
also hat nie etwas gebrannt: die Funktion ist nicht gescheitert, sie hat nur
nie etwas geliefert.

Drei verschiedene INSERTs schreiben in diese Tabelle (public_routes.py und
zweimal main_production.py), jeder mit eigener Spaltenliste. Genau so entsteht
so ein Loch, und genau so wuerde es beim vierten INSERT wieder entstehen.
Deshalb liegt die Zuordnung hier, einmal, mit einem Waechtertest daneben.
"""
from typing import Any, Dict, Optional, Tuple

# Saeulenname im Scanergebnis -> Spalte in scan_history.
#
# Die Namen gehen auseinander: die Saeule heisst "gdpr", die Spalte
# "privacy_score". Wer das Paar trennt, verliert eine Haelfte.
SAEULE_ZU_SPALTE = {
    "accessibility": "accessibility_score",
    "gdpr": "privacy_score",
    "legal": "legal_score",
    "cookies": "cookie_score",
}

# Reihenfolge der Werte, die `werte_fuer_insert` zurueckgibt, und damit die
# Reihenfolge, in der die Spalten im SQL stehen muessen.
SPALTEN_REIHENFOLGE = (
    "overall_score",
    "accessibility_score",
    "privacy_score",
    "legal_score",
    "cookie_score",
    "jurisdiction",
)


def _saeulenwerte(scan_result: Dict[str, Any]) -> Dict[str, Optional[float]]:
    roh = scan_result.get("pillar_scores") or []
    werte: Dict[str, Optional[float]] = {}
    for eintrag in roh:
        if not isinstance(eintrag, dict):
            continue
        saeule = eintrag.get("pillar")
        spalte = SAEULE_ZU_SPALTE.get(saeule)
        if not spalte:
            continue
        punkte = eintrag.get("score")
        if punkte is None:
            # Eine ungeprueft gebliebene Saeule hat keinen Wert. Sie bleibt
            # leer, statt als Null zu erscheinen: "nicht gemessen" und "null
            # Punkte" sind zwei verschiedene Aussagen, und die zweite waere
            # eine Behauptung ueber die Website des Kunden.
            continue
        try:
            werte[spalte] = float(punkte)
        except (TypeError, ValueError):
            continue
    return werte


def werte_fuer_insert(
    scan_result: Dict[str, Any],
    overall: Optional[float] = None,
) -> Tuple[Optional[float], Optional[float], Optional[float],
           Optional[float], Optional[float], Optional[str]]:
    """Die sechs Werte in der Reihenfolge von SPALTEN_REIHENFOLGE.

    `overall` ueberschreibt den Gesamtwert aus dem Ergebnis. public_routes.py
    rechnet ihn selbst (gleichgewichtetes Mittel der Saeulen) und schreibt
    diesen, nicht den des Scanners; die beiden koennen auseinandergehen, und
    dann gilt der, den der Kunde auch angezeigt bekommt.
    """
    werte = _saeulenwerte(scan_result)
    gesamt = overall if overall is not None else scan_result.get("compliance_score")
    try:
        gesamt = float(gesamt) if gesamt is not None else None
    except (TypeError, ValueError):
        gesamt = None

    rechtsraum = scan_result.get("jurisdiction") or None

    return (
        gesamt,
        werte.get("accessibility_score"),
        werte.get("privacy_score"),
        werte.get("legal_score"),
        werte.get("cookie_score"),
        rechtsraum,
    )


def spaltenliste() -> str:
    """Die sechs Spaltennamen fuer das SQL, in derselben Reihenfolge."""
    return ", ".join(SPALTEN_REIHENFOLGE)
