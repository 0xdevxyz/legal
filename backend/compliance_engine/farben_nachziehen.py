"""Bannerfarben folgen der Website.

Anlass (Daniel, 10./20.11.2026): Die Farben des Banners sollen sich aus der Seite
ergeben, von complyos eigener Erkennung gelesen, nicht von Hand gesetzt. Der Scan
hat sie bisher nur beim ANLEGEN einer Konfiguration geschrieben. complyo.de stand
deshalb seit September auf Tuerkis, und jede Seite nach einem Relaunch haette es
auch getan.

Regel: Eine Konfiguration folgt der Website nur, wenn sie das Kennzeichen
`farben_automatisch` traegt. Es wird gesetzt, wenn der Scan die Konfiguration anlegt
oder jemand es einschaltet, und es faellt, sobald ein Mensch im Designer andere
Farben speichert (cookie_compliance_routes.py, POST /config). Eine von Hand
gewaehlte Farbe wird nie ueberschrieben.

Gegen Flackern: Eine Aenderung unterhalb der SCHWELLE (Summe der Kanalabstaende)
gilt als gleich. Die Erkennung schwankt von Lauf zu Lauf um ein paar Stufen
(Verlaeufe, Hover-Zustaende); ein Banner, das jede Woche einen Hauch anders
aussieht, ist schlimmer als eines, das eine Woche hinterherhinkt.

Jeder Fehler (fehlende Spalte, Datenbank) heisst nur: nicht nachgezogen. Der Scan
und die Auslieferung der Konfiguration laufen weiter.
"""
import logging
from typing import Any, Dict, List, Optional

from compliance_engine.markenfarben import _hex_zu_rgb, farbvorschlag

logger = logging.getLogger(__name__)

FELDER = ("primary_color", "accent_color", "text_color", "bg_color")

# Summe der drei Kanalabstaende (0 bis 765), unterhalb gilt eine Farbe als gleich.
SCHWELLE = 30


def _abstand(a: str, b: str) -> int:
    try:
        ra, rb = _hex_zu_rgb(a), _hex_zu_rgb(b)
    except ValueError:
        return 10 ** 6
    return sum(abs(x - y) for x, y in zip(ra, rb))


def vorschlag_aus_scan(gerendert: Optional[Dict[str, Any]]) -> Optional[Dict[str, str]]:
    """Die vier Bannerfarben aus dem Ergebnis der Erkennung, oder None.

    Haupt- und Akzentfarbe so, wie die Website sie zeigt: NICHT abgedunkelt. Der Banner
    waehlt die Schrift auf dem Knopf selbst (lesbareSchrift) und die Markenfarbe als
    Schrift selbst (lesbareMarkenschrift); ein Abdunkeln im Backend ist doppelt und
    verfaelscht die Marke (rru-chemnitz: Gelb #f0dc00 wuerde Olive #7e7401, am 20.11.2026
    im Trockenlauf gemessen; Daniels bestehende Konfigurationen tragen die rohen Farben).
    Text und Grund kommen aus farbvorschlag(), das sie auf Lesbarkeit gegeneinander prueft.

    None, wenn die Seite keine eigenen Farben hergab: dann bleibt es, wie es ist,
    statt auf die Standardfarben zurueckzufallen.
    """
    if not gerendert or not gerendert.get("scraped"):
        return None
    v = farbvorschlag(gerendert)
    if v.get("quelle") != "website":
        return None
    farben = {f: str(v["farben"][f]).lower() for f in FELDER}
    for f in ("primary_color", "accent_color"):
        roh = str(gerendert.get(f) or "").strip().lower()
        try:
            _hex_zu_rgb(roh)
        except ValueError:
            continue
        farben[f] = roh if roh.startswith("#") else "#" + roh
    return farben


def abweichende_felder(alt: Dict[str, Any], neu: Dict[str, str]) -> List[str]:
    """Felder, die sich um mehr als die SCHWELLE unterscheiden."""
    return [f for f in FELDER if _abstand(str(alt.get(f) or ""), neu[f]) > SCHWELLE]


def kennzeichen_nach_speichern(gespeichert: Optional[bool], eingabe: Optional[bool],
                               farben_geaendert: bool) -> Optional[bool]:
    """Was das Speichern im Designer mit dem Kennzeichen macht. None: unveraendert.

    Das Dashboard schickt beim Speichern die ganze Konfiguration zurueck, also auch
    `farben_automatisch` so, wie es geladen wurde. Dieses Echo darf eine Aenderung der
    Farben nicht aushebeln. Bewusst umgelegt ist der Schalter nur, wenn die Eingabe vom
    gespeicherten Wert abweicht.
    """
    if eingabe is not None and (gespeichert is None or bool(eingabe) != bool(gespeichert)):
        return bool(eingabe)
    if farben_geaendert:
        return False
    return None


async def lese_zustand(pool, site_id: str) -> Optional[Dict[str, Any]]:
    """Aktuelle Farben und Kennzeichen. None: keine Konfiguration; Ausnahme: Spalte fehlt."""
    row = await pool.fetchrow(
        "SELECT primary_color, accent_color, text_color, bg_color, farben_automatisch "
        "FROM cookie_banner_configs WHERE site_id = $1", site_id)
    return dict(row) if row else None


async def setze_automatisch(pool, site_id: str, wert: Optional[bool]) -> bool:
    """Schaltet das Kennzeichen. `None` heisst: nicht angefasst.

    Eigener Schreibvorgang statt eines Parameters im grossen UPDATE: ein
    Dashboard, das das Feld nicht kennt, darf es nicht ueberschreiben, und eine
    fehlende Spalte darf das Speichern der uebrigen Einstellungen nicht verhindern.
    """
    if wert is None or not site_id:
        return False
    try:
        res = await pool.execute(
            "UPDATE cookie_banner_configs SET farben_automatisch = $2 WHERE site_id = $1",
            site_id, bool(wert))
        return bool(res) and res != "UPDATE 0"
    except Exception as e:
        logger.warning("[Farben] Kennzeichen fuer %s nicht gespeichert: %s", site_id, e)
        return False


async def nachziehen(pool, site_id: str, gerendert: Optional[Dict[str, Any]],
                     anwenden: bool = True) -> Dict[str, Any]:
    """Zieht die Bannerfarben einer Konfiguration der Website nach.

    zustand:
      keine_konfiguration  es gibt keine Zeile
      spalte_fehlt         Migration 0039 noch nicht eingespielt (oder DB-Fehler)
      manuell              Kennzeichen aus: nie angefasst
      nicht_erkannt        die Seite gab keine eigenen Farben her: bleibt
      unveraendert         Abweichung unter der SCHWELLE
      vorschlag            weicht ab, wurde nicht geschrieben (anwenden=False)
      nachgezogen          geschrieben
    """
    try:
        zustand = await lese_zustand(pool, site_id)
    except Exception as e:
        logger.warning("[Farben] %s nicht lesbar (Spalte fehlt?): %s", site_id, e)
        return {"zustand": "spalte_fehlt"}
    if zustand is None:
        return {"zustand": "keine_konfiguration"}
    alt = {f: zustand.get(f) for f in FELDER}
    if not zustand.get("farben_automatisch"):
        return {"zustand": "manuell", "alt": alt}
    neu = vorschlag_aus_scan(gerendert)
    if neu is None:
        return {"zustand": "nicht_erkannt", "alt": alt}
    felder = abweichende_felder(alt, neu)
    if not felder:
        return {"zustand": "unveraendert", "alt": alt, "neu": neu}
    if not anwenden:
        return {"zustand": "vorschlag", "alt": alt, "neu": neu, "felder": felder}
    try:
        await pool.execute(
            "UPDATE cookie_banner_configs SET primary_color = $2, accent_color = $3, "
            "text_color = $4, bg_color = $5, updated_at = NOW() "
            "WHERE site_id = $1 AND farben_automatisch = TRUE",
            site_id, neu["primary_color"], neu["accent_color"],
            neu["text_color"], neu["bg_color"])
    except Exception as e:
        logger.warning("[Farben] %s nicht geschrieben: %s", site_id, e)
        return {"zustand": "spalte_fehlt", "alt": alt, "neu": neu}
    logger.info("[Farben] %s nachgezogen: %s", site_id,
                ", ".join(f"{f} {alt.get(f)} -> {neu[f]}" for f in felder))
    return {"zustand": "nachgezogen", "alt": alt, "neu": neu, "felder": felder}
