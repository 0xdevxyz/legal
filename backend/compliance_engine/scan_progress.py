"""
Echter Scan-Fortschritt fuer die Live-Anzeige im Dashboard.

Anlass: Die erste Fassung der Fortschrittsanzeige taktete sich an einer
ERWARTETEN Laufzeit entlang — beim ersten echten Scan stand sie bei der
Haelfte, als das Ergebnis kam, und die Anzeige sprang um. Eine Anzeige, die
nicht stimmt, ist schlimmer als keine.

Hier melden die Checks selbst, wenn sie fertig sind. Der Scanner wickelt jede
Pruef-Coroutine in `nach()`; die Mehrseiten-Pruefung registriert ihre
Unterseiten, sobald sie entdeckt sind (echte Zahlen, nicht geschaetzte).
Das Dashboard pollt den Stand ueber ein Token, das der Client selbst erzeugt
und mit der Analyse-Anfrage mitschickt.

In-Prozess-Speicher genuegt: das Backend laeuft als EIN uvicorn-Worker
(main_production). Sollte das je auf mehrere Worker gehen, muss dieser
Speicher nach Redis — der Kommentar hier ist die Erinnerung daran.
"""
import asyncio
import logging
import re
import time
from typing import Any, Awaitable, Dict, List, Optional

logger = logging.getLogger(__name__)

# Die statischen Pruefgruppen des Einzelseiten-Scans. Die Check-Namen hier
# muessen zu den Wrap-Aufrufen im Scanner passen — die Anzeige ist ein
# oeffentliches Versprechen, jede Zeile muss wirklich laufen.
STATISCHE_GRUPPEN: "List[tuple[str, List[str]]]" = [
    ("Rechtstexte & Pflichtangaben", [
        "Impressum",
        "AGB & Widerruf",
        "Shop-Pflichten (Button-Lösung, §312k)",
        "Werbekennzeichnung (UWG)",
        "Aktuelle Rechts-Checks (EUR-Lex)",
    ]),
    ("Datenschutz & Cookies", [
        "Datenschutzerklärung & Drittlandtransfer",
        "Cookie-Banner & Tracking (Netzwerk-Evidenz)",
    ]),
    ("Barrierefreiheit (BFSG)", [
        "axe-core & WCAG-Heuristiken (~100 Regeln)",
    ]),
    ("Technik & Sicherheit", [
        "SSL & Security-Header",
        "Kontaktformular (Art. 13)",
        "Social-Media-Plugins",
        "KI-Systeme & AI-Act-Transparenz",
    ]),
]

_TTL_SEKUNDEN = 900
_TOKEN_MUSTER = re.compile(r"^[A-Za-z0-9-]{8,64}$")

_stand: Dict[str, Dict[str, Any]] = {}


def _aufraeumen() -> None:
    jetzt = time.monotonic()
    for token in [t for t, s in _stand.items() if jetzt - s["_ts"] > _TTL_SEKUNDEN]:
        _stand.pop(token, None)


def token_gueltig(token: str) -> bool:
    return bool(token and _TOKEN_MUSTER.match(token))


def starte(token: str) -> None:
    """Registriert einen Scan mit den statischen Pruefgruppen."""
    if not token_gueltig(token):
        return
    _aufraeumen()
    _stand[token] = {
        "_ts": time.monotonic(),
        "phase": "Seite wird geladen",
        "fertig": False,
        "gruppen": [
            {"titel": titel, "checks": [{"name": n, "fertig": False} for n in namen]}
            for titel, namen in STATISCHE_GRUPPEN
        ],
    }


def setze_phase(token: Optional[str], phase: str) -> None:
    s = _stand.get(token or "")
    if s:
        s["phase"] = phase
        s["_ts"] = time.monotonic()


def registriere_checks(token: Optional[str], gruppe: str, namen: List[str]) -> None:
    """
    Haengt eine Gruppe mit echten Eintraegen an — z.B. die entdeckten
    Unterseiten. Erst NACH der Entdeckung aufrufen: die Anzeige soll die
    tatsaechlichen Seiten zeigen, keine Schaetzung.
    """
    s = _stand.get(token or "")
    if not s:
        return
    for g in s["gruppen"]:
        if g["titel"] == gruppe:
            vorhanden = {c["name"] for c in g["checks"]}
            g["checks"].extend(
                {"name": n, "fertig": False} for n in namen if n not in vorhanden
            )
            break
    else:
        s["gruppen"].append(
            {"titel": gruppe, "checks": [{"name": n, "fertig": False} for n in namen]}
        )
    s["_ts"] = time.monotonic()


def melde(token: Optional[str], gruppe: str, check: str) -> None:
    """Markiert einen Check als abgeschlossen."""
    s = _stand.get(token or "")
    if not s:
        return
    for g in s["gruppen"]:
        if g["titel"] == gruppe:
            for c in g["checks"]:
                if c["name"] == check:
                    c["fertig"] = True
                    s["_ts"] = time.monotonic()
                    return
    # Unbekannter Check: nachtragen statt verlieren — die Anzeige soll nie
    # weniger wissen als das Backend.
    registriere_checks(token, gruppe, [check])
    melde(token, gruppe, check)


def abschliessen(token: Optional[str]) -> None:
    """Alles fertig — auch Checks, deren Meldung verloren ging."""
    s = _stand.get(token or "")
    if not s:
        return
    for g in s["gruppen"]:
        for c in g["checks"]:
            c["fertig"] = True
    s["fertig"] = True
    s["phase"] = "Ergebnis wird zusammengestellt"
    s["_ts"] = time.monotonic()


def hole(token: str) -> Optional[Dict[str, Any]]:
    _aufraeumen()
    s = _stand.get(token)
    if not s:
        return None
    return {k: v for k, v in s.items() if not k.startswith("_")}


def nach(
    coro: "Awaitable[Any]", token: Optional[str], gruppe: str, check: str
) -> "Awaitable[Any]":
    """
    Wickelt eine Pruef-Coroutine: nach ihrem Ende (auch bei Fehler) gilt der
    Check als abgearbeitet. "Abgearbeitet" heisst durchlaufen, nicht bestanden
    — die Anzeige zeigt Arbeitsfortschritt, kein Ergebnis.
    """
    if not token:
        return coro

    async def _laeuft():
        try:
            return await coro
        finally:
            melde(token, gruppe, check)

    return _laeuft()
