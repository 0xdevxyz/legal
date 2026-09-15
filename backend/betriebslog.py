"""Was im Zugriffslog steht, und was nicht.

Gemessen am 15.09.2026: von rund 2.500 Zeilen Backend-Log in 13 Stunden waren
1.558 ein erfolgreiches `GET /health`. Der Gesundheitswaechter laeuft jede
Minute, dazu der Docker-Healthcheck. Alles andere ersaeuft darin, und ein Log,
in dem der echte Befund nicht mehr auffaellt, ist kein Betriebsprotokoll mehr.

Eigenes Modul und nicht ein paar Zeilen in main_production, damit die
Entscheidung ohne Datenbank, ohne Netz und ohne den Import der ganzen
Anwendung pruefbar ist. Ein Filter, der nur im Zusammenbau getestet werden
kann, wird nicht getestet.
"""
import logging

# Nur diese Pfade, exakt. Ein Praefixvergleich wuerde /healthcheck und
# /api/health/detail mitverschlucken, also Routen, deren Abrufe man sehen will.
STILLE_ZUGRIFFSPFADE = ("/health", "/api/health")


class GesundheitsabrufeStumm(logging.Filter):
    """Unterdrueckt ERFOLGREICHE Gesundheitsabrufe im uvicorn-Zugriffslog.

    Bewusst nur die erfolgreichen: ein /health, das 4xx oder 5xx antwortet, ist
    genau das Signal, auf das es hier ankommt, und bleibt sichtbar. Ein Filter,
    der auch den kaputten Fall verschweigt, waere ein Waechter, der schweigt.

    Defensiv gegenueber der Formatierung von uvicorn: passt die Form der
    Log-Argumente nicht auf das erwartete Fuenftupel (client, methode, pfad,
    http_version, status), wird NICHT gefiltert. Lieber eine Zeile zuviel als
    eine verlorene.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        args = record.args
        if not isinstance(args, tuple) or len(args) != 5:
            return True
        pfad, status = args[2], args[4]
        try:
            if int(status) >= 400:
                return True
        except (TypeError, ValueError):
            return True
        return str(pfad).split("?")[0] not in STILLE_ZUGRIFFSPFADE


def installieren() -> GesundheitsabrufeStumm:
    """Haengt den Filter an uvicorn.access. Mehrfachaufruf haengt nicht doppelt."""
    zugriffslogger = logging.getLogger("uvicorn.access")
    for vorhanden in zugriffslogger.filters:
        if isinstance(vorhanden, GesundheitsabrufeStumm):
            return vorhanden
    filter_ = GesundheitsabrufeStumm()
    zugriffslogger.addFilter(filter_)
    return filter_
