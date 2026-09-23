"""Welcher Tarif zu einem Betrieb passt, abgeleitet aus seinen Pflichten.

Warum das hier steht und nicht in einer Preistabelle
----------------------------------------------------
complyo nimmt für sich in Anspruch, zu messen statt zu behaupten. Der Preis war
davon bisher ausgenommen: Er wurde gesetzt, und die Begründung suchte danach
den passenden Wettbewerber. Das ist dieselbe Denkrichtung, gegen die das
Produkt antritt.

Der Pflichten-Report misst bereits, was ein Betrieb an Pflichten trägt. Genau
das ist die Arbeit, die complyo ihm abnimmt, und damit der einzige ehrliche
Maßstab für den Tarif: **Wer mehr Pflichten hat, bekommt mehr abgenommen.**

Wie die Punktzahl entsteht
--------------------------
Eine Pflicht mit Status `applies` zählt voll, eine mit `check` halb. `check`
heißt: nach den Indizien im Profil wahrscheinlich einschlägig, aber nicht
belegt (etwa das BFSG bei einem Kleinstunternehmen, wo die Ausnahme für
Dienstleistungen greifen könnte, für Produktverkauf aber nicht). Halb zu zählen
bildet genau diese Unsicherheit ab, statt sie in eine Richtung aufzulösen.

Wo die Schwellen herkommen
--------------------------
Gemessen, nicht gesetzt. Am 23.09.2026 wurden alle 20.480 plausiblen Profile
durch den echten Katalog gerechnet (Beschäftigtenzahl und Umsatz nur in
Kombinationen, die es gibt). Die Spanne reicht von 4,0 bis 12,5 Punkten.

Entscheidend waren die Archetypen, weil die Vollzählung jede Ja-Nein-Angabe
gleich gewichtet und damit merkmalsreiche Profile überrepräsentiert:

    4,0  Handwerksbetrieb, 5 Leute, Visitenkartenseite
    4,5  Arztpraxis, 8 Leute, Online-Terminbuchung
    5,5  Restaurant, 12 Leute, Newsletter
    ----------------------------------------- Lücke
    8,5  Onlineshop, 15 Leute
    8,5  Agentur, 20 Leute, mit SaaS-Angebot
   10,5  Mittelständler, 120 Leute, Shop und KI

Zwischen 5,5 und 8,5 liegt nichts. Die untere Schwelle steht deshalb bei 6,5,
das ist zugleich das 10. Perzentil der Vollzählung. Die obere bei 10,0, dem
90. Perzentil.

Was diese Empfehlung NICHT ist
------------------------------
**Keine Sperre.** Sie schlägt vor und begründet; kaufen kann jeder, was er
will. Das Profil ist selbst angegeben, und wer sich kleiner macht, bekommt eine
kleinere Empfehlung. Eine Zahlschranke auf Grundlage einer Selbstauskunft wäre
sowohl übergriffig als auch leicht zu umgehen.

**Keine Aussage über die Zahl der Websites.** Die ist die zweite Dimension des
Tarifs und hat mit Pflichten nichts zu tun: Eine Agentur mit 25 Kundenseiten
braucht den Agenturtarif, auch wenn jede einzelne Seite schlank ist.

**Keine Preise.** Dieses Modul nennt Stufen, keine Beträge. Die Preisliste
ändert sich, der Zusammenhang zwischen Pflichtenlast und Stufe nicht.
"""

from typing import Any, Dict, List, Optional

# Statuswerte des Katalogs, hier nur lesend verwendet.
APPLIES = "applies"
CHECK = "check"

SCHLANK = "schlank"
VOLL = "voll"
VOLL_PLUS = "voll_plus"

# Gemessen am 23.09.2026, siehe Modulkopf.
SCHWELLE_VOLL = 6.5
SCHWELLE_VOLL_PLUS = 10.0

STUFEN: Dict[str, Dict[str, str]] = {
    SCHLANK: {
        "name": "schlank",
        "beschreibung": (
            "Wenige Pflichten, und die wenigen sind die, die jede geschäftliche "
            "Website trifft. Einzelne Säulen oder die laufende Überwachung reichen."
        ),
    },
    VOLL: {
        "name": "voll",
        "beschreibung": (
            "Mehrere Pflichten aus verschiedenen Rechtsgebieten treffen zusammen. "
            "Hier lohnt das vollständige Paket, weil der Aufwand sonst auf mehrere "
            "Einzellösungen verteilt wird und niemand den Überblick behält."
        ),
    },
    VOLL_PLUS: {
        "name": "voll_plus",
        "beschreibung": (
            "Viele Pflichten, darunter solche mit eigenen Fristen und eigener "
            "Dokumentation. Zum vollständigen Paket kommen Zusatzbausteine, und ab "
            "hier lohnt ein Gespräch statt einer Selbstbedienung."
        ),
    },
}


def punkte(counts: Dict[str, int]) -> float:
    """Pflichtenpunkte aus den Zählern des Reports.

    `applies` voll, `check` halb. Siehe Modulkopf zur Begründung.
    """
    trifft = int(counts.get(APPLIES, 0) or 0)
    pruefen = int(counts.get(CHECK, 0) or 0)
    return trifft + pruefen / 2


def stufe(punktzahl: float) -> str:
    if punktzahl >= SCHWELLE_VOLL_PLUS:
        return VOLL_PLUS
    if punktzahl >= SCHWELLE_VOLL:
        return VOLL
    return SCHLANK


def _treiber(items: List[Dict[str, Any]], hoechstens: int = 4) -> List[Dict[str, Any]]:
    """Die Pflichten, die die Empfehlung tragen, nach Risiko sortiert.

    Ohne diese Liste wäre die Empfehlung eine Zahl ohne Begründung, und damit
    genau die Sorte Aussage, die das Produkt seinen Kunden nicht durchgehen
    lässt.
    """
    tragend = [i for i in items if i.get("status") in (APPLIES, CHECK)]
    tragend.sort(key=lambda i: (
        0 if i.get("status") == APPLIES else 1,
        -(i.get("risk_range") or [0, 0])[1],
    ))
    return [
        {
            "id": i.get("id"),
            "title": i.get("title"),
            "status": i.get("status"),
            "law": i.get("law"),
            "deadline": i.get("deadline"),
        }
        for i in tragend[:hoechstens]
    ]


def empfehlung(report: Dict[str, Any],
               websites: Optional[int] = None) -> Dict[str, Any]:
    """Tarifempfehlung aus einem Pflichten-Report.

    `report` ist die Rückgabe von `pflichten_katalog.evaluate_pflichten()`.
    `websites` ist die Zahl der betreuten Websites, falls bekannt; sie
    entscheidet die zweite Dimension und wird hier nur als Hinweis
    weitergereicht.

    Funktioniert auch auf dem gekürzten Report des Free-Tarifs: die Zähler sind
    dort vollständig, nur die Einzelposten sind es nicht. Die Punktzahl stimmt
    also, die Begründung ist kürzer.
    """
    counts = report.get("counts") or {}
    p = punkte(counts)
    s = stufe(p)

    hinweise = []
    if websites is not None and websites > 1:
        hinweise.append(
            f"Für {websites} betreute Websites entscheidet die Zahl der Projekte "
            "den Tarif, nicht die Pflichtenlast."
        )
    if report.get("locked"):
        hinweise.append(
            "Die Punktzahl stammt aus dem vollständigen Katalog; sichtbar sind "
            "im Free-Tarif nur die ersten Einordnungen."
        )

    return {
        "punkte": round(p, 1),
        "stufe": s,
        "stufe_name": STUFEN[s]["name"],
        "beschreibung": STUFEN[s]["beschreibung"],
        "treiber": _treiber(report.get("items") or []),
        "schwellen": {
            "voll_ab": SCHWELLE_VOLL,
            "voll_plus_ab": SCHWELLE_VOLL_PLUS,
        },
        "hinweise": hinweise,
        "grundlage": (
            "Selbstauskunft im Firmenprofil, ausgewertet gegen den Pflichtenkatalog. "
            "Eine Empfehlung, keine Voraussetzung: buchbar ist jeder Tarif."
        ),
    }
