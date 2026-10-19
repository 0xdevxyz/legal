"""
BFSG-Einordnung der Barrierefreiheitsbefunde nach Unternehmensprofil.

Das Barrierefreiheitsstaerkungsgesetz trifft eine Website nur, wenn drei
Dinge zusammenkommen: ein Angebot an Verbraucher, ein Vertragsschluss oder
eine Buchung ueber die Website (Dienstleistung im elektronischen
Geschaeftsverkehr, § 1 Abs. 3 Nr. 5, § 2 Nr. 26 BFSG) und ein Unternehmen,
das kein Kleinstunternehmen ist (unter 10 Beschaeftigte und bis 2 Mio. Euro
Umsatz, § 2 Nr. 17, Ausnahme fuer Dienstleistungen in § 3 Abs. 3).

Bis zum 13.10.2026 kannte der Scanner nur eine Seitenheuristik (Warenkorb,
Kasse, Buchung, Kundenkonto) und nutzte sie allein fuer die fehlende
Barrierefreiheitserklaerung. Alle uebrigen Befunde trugen feste Eurobetraege
und die Rechtsgrundlage "BFSG §12", auch auf der Praxisseite eines
Einzelunternehmers, den das Gesetz gar nicht erfasst. Das Unternehmensprofil
(company_profiles: employees, revenue, b2c, online_shop, digital_service)
gab es laengst, der Pflichtenradar wertete es bereits aus, der Scanner las es
nicht.

Was dieses Modul tut und was nicht:

- Es ordnet ein, es misst nicht. Ein fehlender Alt-Text bleibt ein
  fehlender Alt-Text; Schweregrad und Punktestand aendern sich nicht
  (Entscheidung Daniel, 13.10.2026: volle Zaehlung, Umbeschriftung).
- Es nimmt im Modus "nicht angezeigt" und "offen" den Eurobetrag heraus und
  schreibt die Rechtsgrundlage um. Ein Betrag behauptet ein bezifferbares
  Risiko; ohne Pflicht steht dort 0 (siehe test_security_header_einordnung).
- Es urteilt nicht. Ob das BFSG im Einzelfall greift, ist Rechtsberatung
  (RDG). Die Texte sagen "nach Ihren Angaben" und "pruefen", nie "Sie sind
  nicht betroffen". Die Logik ist dieselbe wie im Pflichtenradar
  (pflichten_katalog.py, Regel "bfsg"), damit Radar und Scan nie
  auseinanderlaufen.

Quellen: gesetze-im-internet.de/bfsg; Bundesfachstelle Barrierefreiheit,
FAQ 19, 23 und 24 (geprueft 07.10.2026).

Ort: neben pflichten_katalog.py, nicht in compliance_engine/. Der Pruefkern
soll keine deutschen Gesetze nennen (tests/test_rechtsraum_waechter.py); der
Scanner ruft dieses Modul nur im Rechtsraum "de" auf.
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, Iterable, List, Optional

from compliance_engine.score_calculator import ScoreCalculator

logger = logging.getLogger(__name__)

# Dieselben drei Stufen wie im Pflichtenradar.
GREIFT = "applies"
OFFEN = "check"
NICHT_ANGEZEIGT = "not_indicated"

PROFIL_PFAD = "/pflichten-report"
RECHTSGRUNDLAGE = "§ 1 Abs. 3 Nr. 5, § 2 Nr. 17 und 26, § 3 Abs. 3 BFSG"
QUELLE = ("Bundesfachstelle Barrierefreiheit, FAQ 19, 23 und 24; "
          "gesetze-im-internet.de/bfsg (geprüft 07.10.2026)")

HINWEIS = (
    "Einordnung nach Ihren Profilangaben und den Merkmalen der geprüften "
    "Seiten, keine Rechtsberatung. Die Messung der Barrierefreiheit ändert "
    "sich dadurch nicht: jede Abweichung von WCAG 2.1 AA bleibt ein Befund und "
    "zählt im Punktestand voll. Die Einordnung bestimmt nur, ob daran eine "
    "BFSG-Pflicht hängt."
)

_BESCHRIFTUNG = {
    GREIFT: "Barrierefreiheit (BFSG)",
    OFFEN: "Barrierefreiheit (WCAG 2.1 AA, BFSG-Einordnung offen)",
    NICHT_ANGEZEIGT: "Barrierefreiheit (WCAG 2.1 AA)",
}
_BESCHREIBUNG = {
    GREIFT: "gemessen gegen WCAG 2.1 AA; das BFSG greift nach Ihren Angaben",
    OFFEN: "gemessen gegen WCAG 2.1 AA; ob das BFSG greift, ist noch offen",
    NICHT_ANGEZEIGT: ("gemessen gegen WCAG 2.1 AA; eine BFSG-Pflicht ist nach "
                      "Ihren Angaben nicht angezeigt"),
}
_STUFEN_LABEL = {
    GREIFT: "BFSG greift wahrscheinlich",
    OFFEN: "BFSG-Einordnung offen, bitte prüfen",
    NICHT_ANGEZEIGT: "BFSG-Pflicht nach Ihren Angaben nicht angezeigt",
}

_BESCHAEFTIGTE = {"1-9": "1 bis 9", "10-49": "10 bis 49",
                  "50-249": "50 bis 249", "250+": "250 oder mehr"}
_UMSATZ = {"<=2m": "bis 2 Mio. €", "2-10m": "2 bis 10 Mio. €",
           "10-50m": "10 bis 50 Mio. €", ">50m": "über 50 Mio. €"}

_ERKLAERUNG_TITEL_ANFANG = "barrierefreiheitserklärung fehlt"
# "BFSG §12" oder "BFSG §14" samt Trennzeichen aus einer Rechtsgrundlage loesen.
_BFSG_ANKER_RE = re.compile(r"(,\s*)?\bBFSG\s*§\s*1[24]\b(,\s*)?")


def _profil_vollstaendig(profil: Optional[Dict[str, Any]]) -> bool:
    """Beschaeftigte und Umsatz sind die Pflichtfelder des Profils; ohne sie
    laesst sich die Kleinstunternehmer-Frage nicht beantworten."""
    return bool(profil) and bool(profil.get("employees")) and bool(profil.get("revenue"))


def _ja_nein(wert: Any) -> Optional[str]:
    if wert is None:
        return None
    return "ja" if bool(wert) else "nein"


def _katalog_bewertung(profil: Dict[str, Any]):
    """Die BFSG-Regel des Pflichtenradars, damit beide Wege dasselbe sagen."""
    try:
        from pflichten_katalog import PFLICHTEN
        regel = next(r for r in PFLICHTEN if r["id"] == "bfsg")
        return regel["evaluate"](profil)
    except Exception as e:  # pragma: no cover - Katalog ist Teil des Backends
        logger.warning("BFSG-Regel des Pflichtenradars nicht erreichbar: %s", e)
        return OFFEN, ["Auswertung fehlgeschlagen"], \
            "Die Einordnung konnte nicht automatisch vorgenommen werden, bitte selbst prüfen."


def einordnen(profil: Optional[Dict[str, Any]], *, seitenmerkmale: bool) -> Dict[str, Any]:
    """Ordnet ein, ob die Barrierefreiheitsbefunde unter das BFSG fallen.

    Args:
        profil: Antworten aus company_profiles oder None (kein Konto, kein
            Profil, oeffentlicher Vorschau-Scan).
        seitenmerkmale: Zeigt die Seite Bestell-, Buchungs- oder
            Kontomerkmale (shop_check plus Heuristik in barrierefreiheit_check)?

    Returns:
        Ein Woerterbuch fuer Scan-Ergebnis und Dashboard: status, label,
        gruende, text, kriterien, saeulen_beschriftung, profil_vorhanden.
    """
    profil = profil or {}
    profil_vorhanden = _profil_vollstaendig(profil)
    gruende: List[str] = []

    if not profil_vorhanden:
        status = OFFEN
        gruende.append("kein Unternehmensprofil hinterlegt (Beschäftigte, Umsatz, Verbraucherangebot)")
        text = (
            "Ob das BFSG Ihre Website erfasst, hängt von drei Angaben ab: Zahl "
            "der Beschäftigten, Jahresumsatz und ob Verbraucher über die Website "
            "Verträge schließen oder buchen. Ohne diese Angaben bleibt die "
            "Einordnung offen. Füllen Sie das Unternehmensprofil aus, dann ordnet "
            "complyo die Befunde ein."
        )
        kleinstunternehmen: Optional[bool] = None
    else:
        status, evidence, text = _katalog_bewertung(profil)
        gruende.extend(evidence)
        kleinstunternehmen = (profil.get("employees") == "1-9"
                              and profil.get("revenue") == "<=2m")
        if status == NICHT_ANGEZEIGT and seitenmerkmale:
            # Profil und Seite widersprechen sich: lieber nachfragen als
            # einordnen. Ein Buchungsknopf ist ein Indiz, kein Urteil.
            status = OFFEN
            gruende.append("die geprüften Seiten zeigen Bestell-, Buchungs- oder "
                           "Kontomerkmale, das Profil nennt keinen Online-Vertragsschluss")
            text = (
                "Nach Ihrem Profil richtet sich das Angebot nicht an Verbraucher "
                "oder es werden keine Verträge oder Buchungen über die Website "
                "geschlossen. Die geprüften Seiten zeigen aber Merkmale wie "
                "Bestellung, Buchung oder Kundenkonto. Bitte prüfen Sie das Profil; "
                "trifft es zu, gilt die Einordnung des Profils."
            )

    if seitenmerkmale:
        gruende.append("Seite zeigt Bestell-, Buchungs- oder Kontomerkmale")
    else:
        gruende.append("auf den geprüften Seiten keine Bestell-, Buchungs- oder Kontomerkmale")

    online_vertrag = None
    if profil_vorhanden:
        online_vertrag = bool(profil.get("online_shop")) or bool(profil.get("digital_service"))

    kriterien = [
        {"schluessel": "beschaeftigte", "label": "Beschäftigte",
         "wert": _BESCHAEFTIGTE.get(profil.get("employees")) if profil_vorhanden else None},
        {"schluessel": "umsatz", "label": "Jahresumsatz",
         "wert": _UMSATZ.get(profil.get("revenue")) if profil_vorhanden else None},
        {"schluessel": "verbraucher", "label": "Angebot an Verbraucher (B2C)",
         "wert": _ja_nein(profil.get("b2c")) if profil_vorhanden else None},
        {"schluessel": "online_vertrag", "label": "Vertrag, Kauf oder Buchung über die Website",
         "wert": _ja_nein(online_vertrag)},
        {"schluessel": "seitenmerkmale", "label": "Bestell-, Buchungs- oder Kontomerkmale auf der Seite",
         "wert": _ja_nein(seitenmerkmale)},
        {"schluessel": "kleinstunternehmen", "label": "Kleinstunternehmen (unter 10 Beschäftigte, bis 2 Mio. €)",
         "wert": _ja_nein(kleinstunternehmen)},
    ]

    return {
        "status": status,
        "label": _STUFEN_LABEL[status],
        "profil_vorhanden": profil_vorhanden,
        "profil_pfad": PROFIL_PFAD,
        "gruende": gruende,
        "text": text,
        "kriterien": kriterien,
        "saeulen_beschriftung": _BESCHRIFTUNG[status],
        "saeulen_beschreibung": _BESCHREIBUNG[status],
        "rechtsgrundlage": RECHTSGRUNDLAGE,
        "quelle": QUELLE,
        "hinweis": HINWEIS,
    }


# ---------------------------------------------------------------------------
# Anwendung auf die Befunde
# ---------------------------------------------------------------------------

def _lies(issue: Any, name: str, default: Any = None) -> Any:
    if isinstance(issue, dict):
        return issue.get(name, default)
    return getattr(issue, name, default)


def _setze(issue: Any, name: str, wert: Any) -> None:
    if isinstance(issue, dict):
        issue[name] = wert
    else:
        setattr(issue, name, wert)


def _metadata(issue: Any) -> Dict[str, Any]:
    meta = _lies(issue, "metadata") or {}
    if not isinstance(meta, dict):
        meta = {}
    _setze(issue, "metadata", meta)
    return meta


def ohne_bfsg_anker(rechtsgrundlage: str) -> str:
    """'WCAG 2.1 Level A (1.1.1), BFSG §12' -> 'WCAG 2.1 Level A (1.1.1)'."""
    text = _BFSG_ANKER_RE.sub(lambda m: ", " if (m.group(1) and m.group(2)) else "", rechtsgrundlage or "")
    text = text.strip().strip(",").strip()
    return text or "WCAG 2.1"


def _ist_erklaerung(issue: Any) -> bool:
    return (_lies(issue, "title") or "").strip().lower().startswith(_ERKLAERUNG_TITEL_ANFANG)


def _erklaerung_setzen(issue: Any, status: str) -> None:
    """Die Barrierefreiheitserklaerung ist die einzige reine BFSG-Pflicht
    unter den Befunden (§ 14). Sie folgt der Einordnung ganz."""
    if status == GREIFT:
        _setze(issue, "severity", "warning")
        _setze(issue, "risk_euro", 2000)
        _setze(issue, "title", "Barrierefreiheitserklärung fehlt (BFSG §14)")
    elif status == NICHT_ANGEZEIGT:
        _setze(issue, "severity", "info")
        _setze(issue, "risk_euro", 0)
        _setze(issue, "title", "Barrierefreiheitserklärung fehlt, nach Ihren Angaben keine BFSG-Pflicht")
    else:
        _setze(issue, "risk_euro", 0)
        _setze(issue, "title", "Barrierefreiheitserklärung fehlt, BFSG-Einordnung offen")


def anwenden(issues: Iterable[Any], einordnung: Optional[Dict[str, Any]]) -> List[Any]:
    """Schreibt die Einordnung in die Barrierefreiheitsbefunde.

    Idempotent: ein Befund, der schon diese Einordnung traegt, wird nicht
    noch einmal umgeschrieben (der Mehrseiten-Scan laeuft zweimal hier durch).
    Schweregrad bleibt, ausser bei der Barrierefreiheitserklaerung.
    """
    liste = list(issues)
    if not einordnung:
        return liste
    status = einordnung.get("status")
    if status not in _BESCHRIFTUNG:
        return liste

    for issue in liste:
        if ScoreCalculator.categorize(_lies(issue, "category") or "") != "accessibility":
            continue
        meta = _metadata(issue)
        if meta.get("bfsg_einordnung") == status:
            continue
        meta["bfsg_einordnung"] = status

        if _ist_erklaerung(issue):
            _erklaerung_setzen(issue, status)

        if status == GREIFT:
            continue

        _setze(issue, "risk_euro", 0)
        grundlage = _lies(issue, "legal_basis") or ""
        if status == NICHT_ANGEZEIGT:
            _setze(issue, "legal_basis",
                   f"{ohne_bfsg_anker(grundlage)} (BFSG nach Ihren Angaben nicht angezeigt)")
        else:
            _setze(issue, "legal_basis", f"{grundlage} (BFSG-Einordnung offen)".strip())
    return liste
