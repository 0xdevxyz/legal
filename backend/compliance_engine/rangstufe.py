"""
Rangstufe statt Eurobetrag.

Bis zum 07.10.2026 trug jeder Befund einen Eurobetrag ("Anschrift fehlt im
Impressum: 2.000 EUR"), und der Bericht summierte daraus einen geschaetzten
Gesamtbetrag. Diese Betraege waren erfunden: es gibt keine Bussgeldpraxis
je Pflichtangabe, und was ein Betrieb bei einer Abmahnung zahlt, haengt vom
Streitwert ab, nicht vom Befund. Das Repo wusste das laengst (test_gesamtrisiko,
die Header-Befunde vom 18.09. auf 0 EUR). Fuer einen Compliance-Anbieter ist
eine erfundene Rechtsfolge in der Kundenansicht selbst ein Risiko nach
Paragraph 5 UWG: eine irrefuehrende Angabe ueber Rechtsfolgen.

Deshalb verlaesst kein Eurobetrag je Befund mehr das Backend. An seine Stelle
tritt eine Rangstufe aus zwei Achsen, beide aus Daten, die schon im Code liegen:

  Wichtigkeit  (Rechtsfolge)     severity plus "ganzes Element fehlt"
  Dringlichkeit (passiert es?)   bekannte Abmahnwelle, die den Befund trifft

    wichtig + dringend        -> sofort
    wichtig, nicht dringend   -> als_naechstes
    nicht wichtig             -> einplanen (Warnung)
    Empfehlung                -> hinweis   (info)

Jede Stufe traegt einen Satz Begruendung, der die Welle nennt, wenn eine
greift. Was im Abmahn-Radar an Euro steht (typische Forderung mit Quelle),
bleibt dort: das ist belegte Praxis einer konkreten Welle, kein Betrag je
Befund.
"""

from typing import Any, Dict, Iterable, List, Optional, Tuple

SOFORT = "sofort"
ALS_NAECHSTES = "als_naechstes"
EINPLANEN = "einplanen"
HINWEIS = "hinweis"

STUFEN: Tuple[str, ...] = (SOFORT, ALS_NAECHSTES, EINPLANEN, HINWEIS)

LABEL = {
    SOFORT: "Sofort",
    ALS_NAECHSTES: "Als Nächstes",
    EINPLANEN: "Einplanen",
    HINWEIS: "Hinweis",
}

# Sortierreihenfolge: kleiner zuerst.
ORDNUNG = {stufe: i for i, stufe in enumerate(STUFEN)}

# Schluessel, unter denen bisher Eurobetraege an Kunden gingen. Jeder davon
# wird aus Antworten entfernt, gleich auf welcher Ebene er steht.
EURO_SCHLUESSEL = frozenset({
    "risk_euro", "risk_euro_min", "risk_euro_max", "risk_range",
    "total_risk_euro", "estimated_risk_euro", "riskAmount",
    "total_risk_min", "total_risk_max", "total_risk_range",
    "rahmen_max", "rahmen_range", "risk_rahmen_max", "risk_gedeckelt",
    "risk_min", "risk_max", "privacy_risk_euro", "totalRiskEuro",
})


def ohne_eurobetraege(wert: Any) -> Any:
    """Entfernt alle Euro-Schluessel aus einem Antwortobjekt, rekursiv.

    Gibt eine Kopie zurueck; der Aufrufer behaelt sein Original (etwa fuer
    die interne Ablage), aber der Kunde sieht keinen Betrag.
    """
    if isinstance(wert, dict):
        return {
            k: ohne_eurobetraege(v)
            for k, v in wert.items()
            if k not in EURO_SCHLUESSEL
        }
    if isinstance(wert, list):
        return [ohne_eurobetraege(v) for v in wert]
    return wert


def _text(issue: Dict[str, Any]) -> str:
    # Nur Titel und Beschreibung. Die Kategorie zaehlt nicht als Stichwort:
    # sonst traefe die Impressum-Welle jeden Befund der Kategorie impressum,
    # auch "Keine AGB gefunden", und jede Stufe hiesse "Sofort".
    return " ".join(str(issue.get(k) or "") for k in ("title", "description")).lower()


def _saeule(issue: Dict[str, Any]) -> Optional[str]:
    try:
        from .score_calculator import ScoreCalculator
        return ScoreCalculator.categorize(str(issue.get("category") or ""))
    except Exception:
        return None


def welle_fuer(issue: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Die bekannte Abmahnwelle, die diesen Befund trifft, oder None.

    Trifft nur, wenn ein Stichwort der Welle im Befund steht UND die Welle
    dieselbe Saeule betrifft. Das Stichwort allein ("consent" in einem
    Barrierefreiheits-Befund) waere die Fehlerklasse "ki" -> "Kindermobiliar".
    """
    try:
        from abmahnwellen import ABMAHNWELLEN
    except Exception:
        return None
    text = _text(issue)
    saeule = _saeule(issue)
    for welle in ABMAHNWELLEN:
        if saeule and welle.get("scan_pillar") and welle["scan_pillar"] != saeule:
            continue
        if any(w.lower() in text for w in welle.get("stichwoerter", ())):
            return welle
    return None


def ist_wichtig(issue: Dict[str, Any]) -> bool:
    """Rechtsfolge erster Ordnung: kritisch, oder ein ganzes Pflichtelement fehlt."""
    schwere = str(issue.get("severity") or "").lower()
    if schwere == "critical":
        return True
    return schwere == "warning" and bool(issue.get("is_missing"))


def rang_bestimmen(issue: Dict[str, Any]) -> Dict[str, str]:
    """Stufe, Anzeigename und Begruendung fuer einen Befund."""
    schwere = str(issue.get("severity") or "").lower()
    if schwere not in ("critical", "warning"):
        return {
            "rang": HINWEIS,
            "rang_label": LABEL[HINWEIS],
            "rang_begruendung": "Empfehlung oder Hinweis, keine gesetzliche Pflicht.",
        }

    welle = welle_fuer(issue)
    wichtig = ist_wichtig(issue)

    if wichtig and welle:
        return {
            "rang": SOFORT,
            "rang_label": LABEL[SOFORT],
            "rang_begruendung": (
                f"Gesetzliche Pflicht, und dazu läuft eine bekannte Abmahn- oder "
                f"Bußgeldwelle: {welle['titel']}."
            ),
        }
    if wichtig:
        return {
            "rang": ALS_NAECHSTES,
            "rang_label": LABEL[ALS_NAECHSTES],
            "rang_begruendung": (
                "Gesetzliche Pflicht. Derzeit ist keine Abmahnwelle bekannt, "
                "die genau diesen Punkt betrifft."
            ),
        }
    if welle:
        return {
            "rang": EINPLANEN,
            "rang_label": LABEL[EINPLANEN],
            "rang_begruendung": (
                f"Verbesserung mit Rechtsbezug. Eine bekannte Welle betrifft das "
                f"Thema: {welle['titel']}."
            ),
        }
    return {
        "rang": EINPLANEN,
        "rang_label": LABEL[EINPLANEN],
        "rang_begruendung": "Verbesserung mit Rechtsbezug, keine fehlende Pflichtangabe.",
    }


def rang_anreichern(issues: Iterable[Any]) -> List[Any]:
    """Haengt rang, rang_label und rang_begruendung an jeden Befund (Dicts).

    Nicht-Dicts (Altformat: reiner Text) bleiben unveraendert. Idempotent:
    ein Befund, der die Felder schon traegt, wird neu bewertet, nicht doppelt.
    """
    ergebnis = []
    for issue in issues or []:
        if isinstance(issue, dict):
            neu = dict(issue)
            neu.update(rang_bestimmen(issue))
            ergebnis.append(neu)
        else:
            ergebnis.append(issue)
    return ergebnis


def nach_rang_sortiert(issues: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Sofort zuerst, Hinweise zuletzt; innerhalb der Stufe bleibt die Reihenfolge."""
    return sorted(issues, key=lambda i: ORDNUNG.get(i.get("rang"), len(STUFEN)))
