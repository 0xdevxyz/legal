"""
Darf das Widget den Banner weglassen?

Die Regel steht an einer Stelle und nicht verstreut in Route und Widget. Sie ist
nur die ERSTE von zwei Schranken:

  1. Hier (Server): die Konfiguration erlaubt es. Der Scan ist abgeschlossen und
     hat keinen Dienst gefunden, der Kunde hat den Banner nicht erzwungen, es
     gibt keinen Tag Manager und keine selbst eingetragenen Dienste.
  2. Im Browser (cookie_banner_v2.js, pruefeAnlass): die Seite selbst hat nach
     dem Laden keinen Anlass gezeigt. Keine Cookies, kein Browser-Speicher, kein
     fremder Host, nichts vom Blocker zurueckgehalten.

Erst beides zusammen laesst den Banner weg. Die erste Schranke allein waere
zu schwach: der normale Scan liest nur das HTML und speichert nur Katalogtreffer
(cookie_compliance_routes.scan_website). "Dienste leer" heisst deshalb "nichts
aus dem Katalog gefunden", nicht "nichts gefunden". Gemessen am 08.10.2026 an
14 abgefragten Konfigurationen: vier mit abgeschlossenem Scan, davon zwei mit
leerer Dienste-Liste (steinhau-de, complyo-de). Ob dort wirklich nichts sitzt,
sagt erst die Pruefung im Browser.

Ohne abgeschlossenen Scan bleibt der Banner immer: osteopathie-limbach.de,
spedition-mahn.de und loqal.io sind aktiv, nie gescannt und haben ebenfalls
`services = []`. "Leer" heisst dort "nie nachgesehen".
"""
from typing import Any, Mapping


def banner_auto_aus_erlaubt(config: Mapping[str, Any], eigene_dienste: int = 0) -> bool:
    """True, wenn die Konfiguration die Selbstabschaltung zulaesst.

    Im Zweifel False: fehlt ein Feld, gilt es als "nicht erfuellt", und der
    Banner bleibt, wie er heute ist.
    """
    if config.get("is_active") is not True:
        return False
    if not config.get("scan_completed"):
        return False
    if config.get("services"):
        return False
    if config.get("banner_erzwingen"):
        return False
    # Ein Tag Manager kann beliebiges nachladen, was kein Scan der Startseite sieht.
    if config.get("gtm_enabled") or config.get("gtm_container_id"):
        return False
    # Wer selbst einen Dienst eingetragen hat, nutzt ihn.
    if eigene_dienste:
        return False
    return True
