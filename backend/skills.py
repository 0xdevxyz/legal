"""Skills: Handlungsanweisungen je Befundtyp, mit Belegpflicht.

Ein Skill sagt, WIE ein Befundtyp repariert wird, wo das Verfahren sich
bewährt hat und wo es ausdrücklich nicht angewandt werden darf.

**Warum es hier eine Belegpflicht gibt und nicht nur eine Admin-Freigabe.**
Von 159 automatisch erzeugten Prüfregeln sind 124 wieder abgeschaltet worden.
Sie waren alle freigegeben worden — einem gut formulierten Satz sieht niemand
an, dass er erfunden ist. Die Freigabe allein fängt das nicht ab.

Der Unterschied ist im Bestand sichtbar: `knowledge/patterns/`
enthält nebeneinander `barrierefreiheit-check-patterns.md` („Häufigkeit: sehr
häufig", ein erfundenes `<img src="produkt.jpg">`) und
`haeufigste-befunde-patterns.md` (98× „SVG ohne title", aus echten Scans).
Beide `status: active`, von außen nicht zu unterscheiden.

Deshalb drei Regeln, die dieses Modul durchsetzt:

1. **Kein Skill ohne Belege.** Unter `BELEGE_MINDESTENS` echten Entscheidungen
   darf keiner `aktiv` werden. Ein Skill ohne Zahlen ist eine Meinung.
2. **Rückzug ist automatisch.** Fällt die Annahmequote unter
   `RUECKZUG_UNTER`, geht der Skill auf `zurueckgezogen`. Sonst sammelt sich
   an, was einmal galt.
3. **`niemals_bei` ist Pflicht.** Ein Verfahren ohne benannte Grenzen wird
   angewandt, wo es nicht hingehört.

Stand 05.09.2026: die Ablage enthält nur Vorschläge. Es gibt noch keinen
Befundtyp mit genug Entscheidungen — siehe `GET /api/admin/lernstand`.
"""

import logging
import os
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Dieselbe Schwelle wie im Lernstand. Bewusst dort UND hier benannt: die
# Auswertung meldet, ob die Belege reichen, dieses Modul setzt es durch.
BELEGE_MINDESTENS = 30

# Unter dieser Annahmequote wird ein aktiver Skill zurueckgezogen.
RUECKZUG_UNTER = 0.6

SKILL_VERZEICHNIS = os.getenv(
    "COMPLYO_SKILL_PFAD",
    os.path.join(os.getenv("KNOWLEDGE_VAULT_PATH", "/data/knowledge"), "skills"),
)

ZUSTAENDE = ("vorschlag", "aktiv", "zurueckgezogen")
VERFAHREN = ("mechanisch", "vorschlag", "nur-melden")

PFLICHTFELDER = ("befundtyp", "verfahren", "niemals_bei", "status")


def pruefe_form(skill: Dict[str, Any]) -> List[str]:
    """Formfehler eines Skills. Leere Liste = in Ordnung."""
    fehler: List[str] = []

    for feld in PFLICHTFELDER:
        if feld not in skill:
            fehler.append(f"Pflichtfeld fehlt: {feld}")

    if skill.get("status") not in ZUSTAENDE:
        fehler.append(f"Unbekannter Status: {skill.get('status')!r}")
    if skill.get("verfahren") not in VERFAHREN:
        fehler.append(f"Unbekanntes Verfahren: {skill.get('verfahren')!r}")

    grenzen = skill.get("niemals_bei")
    if not isinstance(grenzen, list) or not grenzen:
        # Der haeufigste und teuerste Fehler: ein Verfahren ohne benannte
        # Grenzen wird angewandt, wo es nicht hingehoert. Die drei
        # Ablehnungsgruende aus der Struktur-Reparatur waren genau das wert.
        fehler.append("niemals_bei muss mindestens eine Grenze nennen")

    return fehler


def _belege(skill: Dict[str, Any]) -> Tuple[int, Optional[float]]:
    b = skill.get("belege") or {}
    an = int(b.get("angenommen") or 0)
    ab = int(b.get("abgelehnt") or 0)
    entschieden = an + ab
    quote = round(an / entschieden, 3) if entschieden else None
    return entschieden, quote


def darf_aktiv_sein(skill: Dict[str, Any]) -> Tuple[bool, str]:
    """Darf dieser Skill den Zustand `aktiv` tragen?

    Gibt (ja/nein, Begruendung) zurueck. Die Begruendung ist fuer Menschen —
    sie steht in der Pruefliste, wenn ein Skill zurueckgewiesen wird.
    """
    if pruefe_form(skill):
        return False, "Formfehler: " + "; ".join(pruefe_form(skill))

    entschieden, quote = _belege(skill)
    if entschieden < BELEGE_MINDESTENS:
        return False, (
            f"Nur {entschieden} Entscheidungen belegt, mindestens "
            f"{BELEGE_MINDESTENS} noetig. Ein Skill ohne Zahlen ist eine Meinung."
        )
    if quote is not None and quote < RUECKZUG_UNTER:
        return False, (
            f"Annahmequote {quote:.0%} liegt unter {RUECKZUG_UNTER:.0%} — "
            "das Verfahren liegt zu oft daneben."
        )
    return True, f"{entschieden} Entscheidungen, Annahmequote {quote:.0%}"


def zustand_nach_belegen(skill: Dict[str, Any]) -> str:
    """Welchen Zustand sollte dieser Skill nach heutiger Datenlage haben?

    Der Rueckzug ist bewusst automatisch: sonst sammelt sich an, was einmal
    galt. Ein zurueckgezogener Skill verschwindet nicht, er landet in der
    Pruefliste.
    """
    erlaubt, _ = darf_aktiv_sein(skill)
    aktuell = skill.get("status")

    if aktuell == "aktiv" and not erlaubt:
        return "zurueckgezogen"
    if aktuell == "vorschlag" and erlaubt:
        # Die Belege reichen — aber aktiv wird ein Skill erst durch eine
        # Freigabe. Automatik darf hochstufen wollen, nicht hochstufen.
        return "vorschlag"
    return aktuell or "vorschlag"


def belege_aus_lernstand(befundtyp: str, lernstand: Dict[str, Any]) -> Dict[str, Any]:
    """Zieht die Belege eines Befundtyps aus dem Lernstand.

    Die Zahlen werden NICHT von Hand gepflegt. Ein handgeschriebener Beleg
    waere wieder nur eine Behauptung — und genau die soll die Belegpflicht
    ausschliessen.
    """
    for e in lernstand.get("befundtypen") or []:
        if e.get("befundtyp") != befundtyp:
            continue
        gruende = e.get("ablehngruende") or []
        return {
            "vorgeschlagen": e.get("vorgeschlagen"),
            "angenommen": e.get("angenommen"),
            "abgelehnt": e.get("abgelehnt"),
            "haeufigster_ablehngrund": gruende[0]["grund"] if gruende else None,
            "stand": e.get("zuletzt"),
        }
    return {}


def lade_alle(verzeichnis: Optional[str] = None) -> List[Dict[str, Any]]:
    """Liest alle Skills aus der Ablage. Fehlerhafte werden gemeldet, nicht
    stillschweigend uebersprungen."""
    pfad = verzeichnis or SKILL_VERZEICHNIS
    if not os.path.isdir(pfad):
        return []

    skills: List[Dict[str, Any]] = []
    for name in sorted(os.listdir(pfad)):
        if not name.endswith(".md"):
            continue
        try:
            skill = _lies_frontmatter(os.path.join(pfad, name))
        except Exception as e:
            logger.warning(f"Skill {name} nicht lesbar: {e}")
            continue
        if skill is None:
            continue
        skill["datei"] = name
        skill["formfehler"] = pruefe_form(skill)
        skills.append(skill)
    return skills


def _lies_frontmatter(pfad: str) -> Optional[Dict[str, Any]]:
    import yaml
    with open(pfad, encoding="utf-8") as f:
        inhalt = f.read()
    if not inhalt.startswith("---"):
        return None
    ende = inhalt.index("\n---", 3)
    return yaml.safe_load(inhalt[3:ende]) or None
