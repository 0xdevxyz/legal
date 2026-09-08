"""
Scan-Kontext — belegte Tatsachen ueber die gepruefte Seite.

**Wozu.** Die meisten Rechtspflichten sind BEDINGT: der Ablehnen-Knopf ist erst
Pflicht, wenn es einen Consent-Banner gibt; der USA-Hinweis erst, wenn Daten in
die USA fliessen; der DSA-Transparenzbericht erst, wenn die Seite eine Plattform
ist. Der deklarative Check-Runner kannte diese Bedingungen nicht — er kannte nur
`applies_when.always` und eine Stichwortliste auf dem Seitentext. Beides trifft
die Bedingung nicht:

* `always: true` heisst "gilt fuer jede Website". Auf complyo.de selbst erzeugten
  acht so gestellte Pruefungen am 08.09.2026 sechs Befunde ueber einen
  Cookie-Banner, den es nicht gibt, und ueber Drittlandtransfers, die nicht
  stattfinden.
* Stichwoerter auf dem Seitentext treffen die Werbetexte. `cookie` traf jede
  Seite, die ueber Cookies SCHREIBT; `anzeigen` traf das Verb.

Dieses Modul sammelt darum die Tatsachen, die der Scan ohnehin schon erhebt, an
einer Stelle. Eine bedingte Pflicht nennt in `applies_when.requires` die
Tatsache, auf der sie beruht; ohne Beleg wird sie nicht geprueft.

**Richtung im Zweifel.** Eine Tatsache gilt nur als belegt, wenn sie belegt ist.
Ein unbekannter Name in `requires` fuehrt zum Ueberspringen, nicht zum Befund —
ein verpasster Fund ist hier billiger als ein erfundener (dieselbe Abwaegung wie
bei der Keyword-Mindestlaenge im Runner).
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, Iterable, Optional

logger = logging.getLogger(__name__)


# Namen aller bekannten Tatsachen. `applies_when.requires` darf nur diese
# nennen; alles andere ist ein Tippfehler oder eine Tatsache, die noch niemand
# erhebt — beides fuehrt zum Ueberspringen der Pruefung.
BEKANNTE_FAKTEN: "frozenset[str]" = frozenset({
    # Datenschutz / Cookies
    "consent_banner",      # ein Consent-/Cookie-Banner ist im Markup vorhanden
    "consent_tracking",    # einwilligungspflichtiges Tracking (analytics/marketing) belegt
    "drittland_usa",       # Datentransfer in die USA belegt
    "drittland_uk",        # Datentransfer ins Vereinigte Koenigreich belegt
    # Vertrieb
    "newsletter_formular",  # ein Newsletter-Anmeldeformular ist vorhanden
    # Noch nicht erhoben — hier bewusst benannt, damit Pruefungen, die darauf
    # beruhen, sichtbar warten statt auf Verdacht zu feuern.
    "plattform_ugc",       # Seite hostet nutzergenerierte Inhalte (DSA-Plattform)
    "plattform_werbung",   # Seite zeigt Werbung Dritter (DSA Art. 26)
})

# Tatsachen, fuer die es (noch) keinen Detektor gibt. Sie stehen in
# BEKANNTE_FAKTEN, damit `requires` sie nennen darf, sind aber nie True.
NICHT_ERHOBEN: "frozenset[str]" = frozenset({
    "plattform_ugc",
    "plattform_werbung",
})


_NEWSLETTER_WORT_RE = re.compile(
    r"newsletter|abonnier|subscribe|e-?mail-?verteiler", re.I
)


def _consent_banner(soup) -> bool:
    """Ist ein Consent-/Cookie-Banner im Markup? Nutzt den Detektor des Cookie-Checks."""
    try:
        from compliance_engine.checks.cookie_check import _find_consent_container
        return _find_consent_container(soup) is not None
    except Exception as e:  # pragma: no cover - Detektor darf den Scan nie kippen
        logger.warning(f"Kontext consent_banner nicht ermittelbar: {e}")
        return False


def _consent_tracking(soup, request_urls: Optional[Iterable[str]]) -> bool:
    """
    Wird einwilligungspflichtiges Tracking eingesetzt?

    Bevorzugt die echten Netzwerk-Requests aus dem Render; ohne Render der
    statische Rueckfall ueber die <script src>. Beides aus dem Tracker-Katalog,
    damit hier keine zweite Liste entsteht.
    """
    try:
        from compliance_engine.tracker_catalog import (
            match_tracking_request, match_tracking_script_src,
        )
    except Exception as e:  # pragma: no cover
        logger.warning(f"Kontext consent_tracking nicht ermittelbar: {e}")
        return False

    for u in (request_urls or []):
        if u and match_tracking_request(u):
            return True
    try:
        for tag in soup.find_all("script", src=True):
            if match_tracking_script_src(tag.get("src") or ""):
                return True
    except Exception:
        pass
    return False


def _drittlaender(html: str, request_urls: Optional[Iterable[str]]) -> "set[str]":
    """Laendercodes, in die nachweislich Daten abfliessen (Drittlandtransfer-SSOT)."""
    laender: "set[str]" = set()
    try:
        from compliance_engine.privacy_transfer_findings import detect_transfers
        for fund in detect_transfers(html=html or "", request_urls=request_urls):
            laender.update(fund.get("data_processing_countries") or [])
    except Exception as e:  # pragma: no cover
        logger.warning(f"Kontext Drittlaender nicht ermittelbar: {e}")
    return laender


def _newsletter_formular(soup) -> bool:
    """Gibt es ein Anmeldeformular mit E-Mail-Feld und Newsletter-Bezug?"""
    try:
        for form in soup.find_all("form"):
            hat_mail = form.find("input", attrs={"type": "email"}) is not None
            if not hat_mail:
                hat_mail = any(
                    "mail" in ((i.get("name") or "") + (i.get("id") or "")).lower()
                    for i in form.find_all("input")
                )
            if not hat_mail:
                continue
            if _NEWSLETTER_WORT_RE.search(form.get_text(separator=" ", strip=True)):
                return True
    except Exception:
        pass
    return False


def ermittle(
    soup,
    *,
    html: str = "",
    request_urls: Optional[Iterable[str]] = None,
) -> Dict[str, bool]:
    """
    Erhebt alle bekannten Tatsachen fuer EINE Seite.

    Gibt immer alle Namen aus BEKANNTE_FAKTEN zurueck — ein fehlender
    Schluessel und ein False sind fuer den Runner verschiedene Dinge (unbekannt
    vs. widerlegt), und diese Unterscheidung soll nicht davon abhaengen, ob ein
    Detektor gerade eine Ausnahme geworfen hat.
    """
    laender = _drittlaender(html or (str(soup) if soup is not None else ""), request_urls)
    fakten: Dict[str, bool] = {
        "consent_banner": _consent_banner(soup),
        "consent_tracking": _consent_tracking(soup, request_urls),
        "drittland_usa": "US" in laender,
        "drittland_uk": "GB" in laender,
        "newsletter_formular": _newsletter_formular(soup),
    }
    for name in NICHT_ERHOBEN:
        fakten[name] = False
    return fakten


def erfuellt(requires: Any, kontext: Optional[Dict[str, bool]]) -> "tuple[bool, str]":
    """
    Prueft `applies_when.requires` gegen den Kontext.

    Rueckgabe: (trifft_zu, grund). `grund` ist leer, wenn alles zutrifft, sonst
    der erste Name, an dem es scheitert — mit Praefix "unbekannt:", wenn die
    Tatsache gar nicht erhoben wird.
    """
    namen = [str(r).strip() for r in (requires or []) if str(r).strip()]
    if not namen:
        return True, ""
    if kontext is None:
        # Aufrufer ohne Kontext (Altpfad, Test): bedingte Pflichten sind hier
        # nicht entscheidbar. Nicht pruefen ist die sichere Richtung.
        return False, f"unbekannt:{namen[0]} (kein Scan-Kontext uebergeben)"
    for name in namen:
        if name not in BEKANNTE_FAKTEN:
            return False, f"unbekannt:{name}"
        if not kontext.get(name, False):
            return False, name
    return True, ""
