"""
Messprotokoll: was gepruft wurde und keine Abweichung zeigte.

Bis zum 13.10.2026 entstand der Kasten "N bestanden" im Dashboard aus
Abwesenheit: sechs grobe Kategorien galten als bestanden, wenn kein Befund
darin lag, dazu "Grundlegende Compliance-Anforderungen erfuellt" ab 50
Punkten. Fiel ein Check stumm aus, wurde daraus "Barrierefreiheit-Tools
implementiert". Das ist eine Zustandsbehauptung ohne Messung, also das
Gegenteil des Pruefnachweises, den complyo verkauft ("was wurde geprueft,
mit welchem Ergebnis").

axe-core liefert je Lauf die Liste der Regeln, die auf der Seite geprueft
wurden und keine Abweichung zeigten (`passes`), mit Regelkennung,
Beschreibung und Zahl der geprueften Elemente. Der Scanner behielt davon nur
die Zahl. Dieses Modul traegt die Liste durch den Scan:

1. `marker()` verpackt sie in einen Eintrag, der denselben Weg nimmt wie die
   Befunde (Kategorie barrierefreiheit, Schwere info, Betrag 0). So braucht
   keine Schicht dazwischen eine neue Signatur, auch nicht die Unterseiten.
2. `ziehe()` holt die Eintraege vor Bewertung und Zusammenfassung wieder
   heraus, damit sie weder gezaehlt noch angezeigt werden.
3. `positive_checks()` fasst sie ueber alle Seiten je Regel zusammen.

Wortwahl: "geprueft, keine Abweichung gefunden". Nie "erfuellt", "konform"
oder "bestanden": eine automatische Pruefung deckt nur einen Teil der
WCAG-Kriterien ab (siehe pillar_notes.accessibility).
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Iterable, List, Tuple

logger = logging.getLogger(__name__)

MARKER_QUELLE = "messprotokoll-axe"
MARKER_TITEL = "Geprüfte Regeln ohne Abweichung"
STATUS = "geprueft_ohne_abweichung"


def marker(page_url: str, regeln: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Ein Eintrag im Befundformat, der das Protokoll einer Seite traegt."""
    return {
        "category": "barrierefreiheit",
        "severity": "info",
        "title": MARKER_TITEL,
        "description": f"{len(regeln)} axe-core-Regeln geprüft, keine Abweichung gefunden.",
        "risk_euro": 0,
        "recommendation": "",
        "legal_basis": "WCAG 2.1",
        "auto_fixable": False,
        "is_missing": False,
        "metadata": {
            "source": MARKER_QUELLE,
            "page_url": page_url,
            "regeln": [
                {
                    "id": r.get("id", ""),
                    "help": r.get("help", ""),
                    "description": r.get("description", ""),
                    "help_url": r.get("help_url") or r.get("helpUrl", ""),
                    "tags": list(r.get("tags") or []),
                    "nodes": int(r.get("nodes") or 0),
                }
                for r in regeln
                if r.get("id")
            ],
        },
    }


def _lies(issue: Any, name: str, default: Any = None) -> Any:
    if isinstance(issue, dict):
        return issue.get(name, default)
    return getattr(issue, name, default)


def ist_marker(issue: Any) -> bool:
    meta = _lies(issue, "metadata") or {}
    return isinstance(meta, dict) and meta.get("source") == MARKER_QUELLE


def ziehe(issues: Iterable[Any]) -> Tuple[List[Any], List[Dict[str, Any]]]:
    """Trennt Protokolleintraege von Befunden.

    Returns:
        (befunde ohne Marker, protokollsaetze). Ein Protokollsatz ist
        {"page_url": ..., "regeln": [...]} je Seite.
    """
    befunde: List[Any] = []
    saetze: List[Dict[str, Any]] = []
    for issue in issues:
        if ist_marker(issue):
            meta = _lies(issue, "metadata") or {}
            saetze.append({
                "page_url": meta.get("page_url") or "",
                "regeln": list(meta.get("regeln") or []),
            })
        else:
            befunde.append(issue)
    return befunde, saetze


def _wcag_kriterien(tags: Iterable[str]) -> List[str]:
    try:
        from compliance_engine.axe_scanner import AXE_TAG_TO_WCAG
    except Exception:  # pragma: no cover
        return []
    kriterien = []
    for tag in tags:
        krit = AXE_TAG_TO_WCAG.get(tag)
        if krit and krit not in kriterien:
            kriterien.append(krit)
    return kriterien


def _rechtspflicht(tags: Iterable[str]) -> bool:
    try:
        from compliance_engine.axe_scanner import ist_rechtspflicht
        return bool(ist_rechtspflicht(list(tags)))
    except Exception:  # pragma: no cover
        return any(str(t).startswith("wcag") for t in tags)


def _uebersetzt(rule_id: str, help_text: str, description: str) -> Tuple[str, str]:
    try:
        from compliance_engine.axe_translations import uebersetze
        return uebersetze(rule_id, help_text, description)
    except Exception:  # pragma: no cover
        return (help_text or rule_id, description or "")


def verletzte_regeln(issues: Iterable[Any]) -> set:
    """axe-Regelkennungen, zu denen ein Befund vorliegt (metadata.axe_rule_id)."""
    kennungen = set()
    for issue in issues:
        meta = _lies(issue, "metadata") or {}
        if isinstance(meta, dict) and meta.get("axe_rule_id"):
            kennungen.add(meta["axe_rule_id"])
    return kennungen


def positive_checks(saetze: Iterable[Dict[str, Any]], *, seiten_gesamt: int,
                    ausser: Iterable[str] = ()) -> List[Dict[str, Any]]:
    """Fasst die Protokollsaetze aller Seiten je Regel zusammen.

    Jeder Eintrag sagt, auf wie vielen der geprueften Seiten die Regel lief
    und wie viele Elemente dabei gemessen wurden. Rechtspflichten (WCAG-Tags)
    stehen vor Best-Practice-Regeln. `ausser` nennt Regeln, zu denen auf
    irgendeiner Seite ein Befund vorliegt: eine Regel, die auf der Startseite
    bestand und auf /kontakt verletzt ist, hat eine Abweichung und gehoert
    nicht in die Liste "keine Abweichung gefunden".
    """
    ausgeschlossen = set(ausser or ())
    je_regel: Dict[str, Dict[str, Any]] = {}
    for satz in saetze:
        seite = satz.get("page_url") or ""
        for regel in satz.get("regeln") or []:
            rid = regel.get("id")
            if not rid or rid in ausgeschlossen:
                continue
            eintrag = je_regel.setdefault(rid, {
                "help": regel.get("help", ""),
                "description": regel.get("description", ""),
                "help_url": regel.get("help_url", ""),
                "tags": list(regel.get("tags") or []),
                "seiten": set(),
                "elemente": 0,
            })
            eintrag["seiten"].add(seite)
            eintrag["elemente"] += int(regel.get("nodes") or 0)

    ergebnis: List[Dict[str, Any]] = []
    for rid, e in je_regel.items():
        titel, beschreibung = _uebersetzt(rid, e["help"], e["description"])
        seiten = len(e["seiten"])
        ergebnis.append({
            "category": "barrierefreiheit",
            "id": rid,
            "title": titel,
            "description": beschreibung,
            "status": STATUS,
            "icon": "✓",
            "seiten": seiten,
            "seiten_gesamt": max(int(seiten_gesamt or 0), seiten),
            "elemente": e["elemente"],
            "wcag": _wcag_kriterien(e["tags"]),
            "rechtspflicht": _rechtspflicht(e["tags"]),
            "help_url": e["help_url"],
            "wortlaut": (
                f"geprüft auf {seiten} von {max(int(seiten_gesamt or 0), seiten)} Seiten "
                f"({e['elemente']} Elemente), keine Abweichung gefunden"
            ),
        })

    ergebnis.sort(key=lambda x: (not x["rechtspflicht"], -x["seiten"], -x["elemente"], x["id"]))
    return ergebnis

