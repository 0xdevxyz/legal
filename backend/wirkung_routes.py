"""
Wirksamkeitsüberwachung im Betrieb — der ergänzende Unterschied.

Was der Scan nicht kann
-----------------------
Der Scan misst die Startseite zu einem Zeitpunkt. Er weiß nicht, ob die
Reparatur auf `/leistungen/` ankommt, ob sie nach dem Theme-Update von
vergangener Woche noch greift, oder ob der Kunde die Seite umgebaut hat.

Das Widget weiß es. Es läuft auf **jeder** Seite, bei **jedem** Aufruf, im
Browser eines echten Besuchers. Nach dem Anwenden kennt es eine Bilanz: wie
viele Reparaturen ein Ziel gefunden haben — und wie viele ins Leere liefen.

Der zweite Wert ist der eigentliche. Ein ausgelieferter Fix, dessen Selektor
nichts mehr trifft, ist genau das Bild eines Theme-Updates, das eine Klasse
umbenannt hat. Ohne diese Meldung fällt so etwas erst beim nächsten Scan auf,
womöglich Wochen später — und in der Zwischenzeit steht in der
Barrierefreiheitserklärung eine Zahl, die nicht mehr stimmt.

Was NICHT verarbeitet wird
--------------------------
Der Pfad der Seite und Zähler. Sonst nichts: keine IP, keine Kennung, kein
Verweis, kein Zeitstempel des Besuchers. Die Meldung sagt etwas über die
**Seite** aus, nicht über den Menschen davor — deshalb sind es keine
personenbezogenen Daten und deshalb braucht sie keine Einwilligung.

Für einen Anbieter, der Datenschutz verkauft, ist das keine Formalie: ein
Messwerkzeug, das nebenbei Besucher verfolgt, wäre das Ende der
Glaubwürdigkeit. Die Tabelle hat schlicht keine Spalte, in die ein Besucher
passen würde.
"""
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field

from dependencies import rate_limit

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/wirkung", tags=["wirkung"])

db_pool = None

SCHEMA = """
CREATE TABLE IF NOT EXISTS accessibility_wirkung (
    id           BIGSERIAL PRIMARY KEY,
    site_id      VARCHAR(100) NOT NULL,
    pfad         VARCHAR(200) NOT NULL,
    angewendet   INTEGER      NOT NULL DEFAULT 0,
    verfehlt     INTEGER      NOT NULL DEFAULT 0,
    erwartet     INTEGER      NOT NULL DEFAULT 0,
    je_art       JSONB        NOT NULL DEFAULT '{}'::jsonb,
    aufrufe      INTEGER      NOT NULL DEFAULT 1,
    zuerst       TIMESTAMP    NOT NULL DEFAULT NOW(),
    zuletzt      TIMESTAMP    NOT NULL DEFAULT NOW(),
    UNIQUE (site_id, pfad)
);
CREATE INDEX IF NOT EXISTS idx_wirkung_site ON accessibility_wirkung (site_id);
"""


class Zaehler(BaseModel):
    angewendet: int = Field(0, ge=0, le=100000)
    verfehlt: int = Field(0, ge=0, le=100000)
    # Ein Fix, der nichts zu tun hatte, weil die Seite den Zustand schon
    # mitbringt — etwa `landmark-main` auf einer Seite mit eigenem <main>.
    # Das ist KEIN Fehlschlag und darf keinen Regressionsalarm ausloesen.
    # Wer beides zusammenwirft, erzeugt eine Warnung, der niemand glaubt.
    unnoetig: int = Field(0, ge=0, le=100000)


class WirkungsMeldung(BaseModel):
    """Was das Widget nach dem Anwenden gesehen hat."""
    pfad: str = Field(..., max_length=200)
    alt_texte: Zaehler = Zaehler()
    link_labels: Zaehler = Zaehler()
    struktur: Zaehler = Zaehler()
    css_regeln: Zaehler = Zaehler()
    # Skip-Link und landmark-main liefen frueher ganz ausserhalb der Bilanz.
    # Blieb der Skip-Link mangels aufloesbarem Ziel aus, meldete das niemand —
    # ausgerechnet der Fall, fuer den diese Ueberwachung da ist.
    dokument_fixes: Zaehler = Zaehler()
    # Das Widget laeuft, aber unter einer Kennung, die complyo nicht kennt.
    # Dann ist die Seite eingebunden und bekommt trotzdem nie eine Reparatur.
    unbekannte_kennung: bool = False
    erwartet: Dict[str, int] = Field(default_factory=dict)


def _keine_antwort() -> Response:
    """Eine 204-Antwort — ohne Koerper.

    `JSONResponse(status_code=204, content=None)` sieht harmlos aus, schreibt
    aber `null` in den Koerper und uvicorn wirft dann bei JEDER Meldung
    "Response content longer than Content-Length". Im Log stand das nach dem
    Ausrollen sofort; nach aussen blieb es unsichtbar, weil das Widget
    fail-silent meldet. Eine Statistik, die stillschweigend Fehler produziert,
    ist schlimmer als keine.
    """
    return Response(status_code=204, headers={"Access-Control-Allow-Origin": "*"})


def _pfad_saeubern(pfad: str) -> str:
    """
    Nur der Pfad, ohne Parameter und Anker.

    In Abfrageparametern stehen regelmaessig Suchbegriffe, Warenkorb-Inhalte
    oder Tracking-Kennungen — alles Dinge, die hier nichts verloren haben. Das
    Widget schickt sie ohnehin nicht mit; hier wird es zusaetzlich erzwungen,
    weil ein oeffentlicher Endpunkt sich nicht auf seinen Aufrufer verlassen
    darf.
    """
    p = (pfad or "/").split("?")[0].split("#")[0].strip()
    if not p.startswith("/"):
        p = "/" + p
    return p[:200]


@router.post("/{site_id}", dependencies=[Depends(rate_limit("wirkung", 120, 60))])
async def melde_wirkung(site_id: str, request: Request) -> Response:
    """
    Nimmt die Bilanz eines Seitenaufrufs entgegen.

    Oeffentlich, weil das Widget auf fremden Domains laeuft und dort keine
    Anmeldung haben kann. Missbrauch waere hoechstens verfaelschte Statistik —
    es gibt nichts zu lesen und nichts auszuloesen. Rate-Limit trotzdem.

    Der Koerper wird SELBST geparst statt ueber ein Pydantic-Argument: das
    Widget schickt `text/plain`, weil `application/json` kein CORS-sicherer
    Inhaltstyp ist und einen Preflight ausloest — den `sendBeacon` nicht kann.
    Mit einem Body-Modell wuerde FastAPI den Inhaltstyp pruefen und die Meldung
    mit 422 abweisen. Beim ersten Live-Test auf einer Kundenseite ist genau das
    passiert (dort noch als CORS-Fehler im Browser).

    Antwortet immer 204: die Messung darf die Seite des Kunden nie stoeren,
    auch nicht durch eine Fehlermeldung im Netzwerk-Reiter.
    """
    try:
        roh = await request.body()
        meldung = WirkungsMeldung.model_validate_json(roh)
    except Exception:
        # Unbrauchbarer Koerper: verwerfen, nicht meckern.
        return _keine_antwort()

    if not db_pool:
        return _keine_antwort()

    arten = {
        "alt_texte": meldung.alt_texte,
        "link_labels": meldung.link_labels,
        "struktur": meldung.struktur,
        "css_regeln": meldung.css_regeln,
        "dokument_fixes": meldung.dokument_fixes,
    }
    angewendet = sum(z.angewendet for z in arten.values())
    # `unnoetig` fliesst bewusst in KEINE der beiden Summen: es ist weder
    # geleistete Arbeit noch ein Fehlschlag, sondern die Feststellung, dass
    # nichts zu tun war.
    verfehlt = sum(z.verfehlt for z in arten.values())
    # `erwartet` deckt dieselben FUENF Arten ab wie die Bilanz — inklusive
    # dokument_fixes. Vorher fehlten sie auf beiden Seiten (Widget schickte
    # vier Arten, hier wurde blind summiert): jede Quote angewendet/erwartet
    # war damit strukturell falsch, sobald dokumentweite Fixes im Spiel waren.
    # Nur bekannte Arten zaehlen — der Endpunkt ist oeffentlich, fremde
    # Schluessel duerfen das Soll nicht aufblasen.
    erwartet = sum(
        int(meldung.erwartet[name])
        for name in arten
        if isinstance(meldung.erwartet.get(name), int)
    )

    import json as _json
    _inhalt = {
        name: {"angewendet": z.angewendet, "verfehlt": z.verfehlt,
               "unnoetig": z.unnoetig}
        for name, z in arten.items()
    }
    if meldung.unbekannte_kennung:
        _inhalt["unbekannte_kennung"] = True
        # Laut ins Log: hier hat jemand complyo eingebaut und bekommt nichts.
        # Auf loqal.io stand eine Scan-Kennung im Skript-Tag statt der
        # Site-ID; die Seite haette auch nach jeder Freigabe nie eine
        # Reparatur erhalten, und niemand konnte es bemerken.
        logger.warning(
            "Widget meldet sich unter unbekannter Kennung %r (Pfad %s) — "
            "diese Website bekommt keine Reparaturen ausgeliefert",
            site_id, _pfad_saeubern(meldung.pfad))
    je_art = _json.dumps(_inhalt)

    try:
        async with db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO accessibility_wirkung
                    (site_id, pfad, angewendet, verfehlt, erwartet, je_art)
                VALUES ($1, $2, $3, $4, $5, $6::jsonb)
                ON CONFLICT (site_id, pfad) DO UPDATE SET
                    angewendet = EXCLUDED.angewendet,
                    verfehlt   = EXCLUDED.verfehlt,
                    erwartet   = EXCLUDED.erwartet,
                    je_art     = EXCLUDED.je_art,
                    aufrufe    = accessibility_wirkung.aufrufe + 1,
                    zuletzt    = NOW()
                """,
                site_id, _pfad_saeubern(meldung.pfad),
                angewendet, verfehlt, erwartet, je_art,
            )
    except Exception as e:
        # Fail-silent nach aussen, laut im Log: eine kaputte Statistik darf
        # niemals eine Kundenseite beeintraechtigen.
        logger.warning(f"Wirkungsmeldung {site_id} nicht gespeichert: {e}")

    return _keine_antwort()


@router.options("/{site_id}")
async def wirkung_preflight(site_id: str) -> Response:
    return Response(status_code=204, headers={
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "content-type",
        "Access-Control-Max-Age": "86400",
    })


async def falsch_eingebaute_kennungen(grenze: int = 50) -> List[Dict[str, Any]]:
    """
    Kennungen, unter denen sich ein Widget meldet, die complyo aber nicht kennt.

    Das ist der Betriebsblick auf einen Fund, den nur das Widget liefern kann:
    jemand hat complyo eingebaut, das Skript laeuft, und trotzdem kommt nichts
    an — weil im `data-site-id` etwas anderes steht als die Site-ID. Ein
    Scanner koennte das nie feststellen; er ist nicht dabei, wenn die Seite
    geladen wird.

    Fuer den Betrieb ist es eine Warnliste, fuer den Vertrieb ein Beleg: das
    Produkt merkt, wenn es selbst falsch eingebaut ist.
    """
    if not db_pool:
        return []
    async with db_pool.acquire() as conn:
        zeilen = await conn.fetch(
            """SELECT site_id, count(*) AS pfade, sum(aufrufe) AS aufrufe,
                      max(zuletzt) AS zuletzt
               FROM accessibility_wirkung
               WHERE je_art ? 'unbekannte_kennung'
               GROUP BY site_id ORDER BY sum(aufrufe) DESC LIMIT $1""",
            grenze,
        )
    return [
        {"site_id": z["site_id"], "seiten": z["pfade"], "aufrufe": z["aufrufe"],
         "zuletzt": z["zuletzt"].strftime("%Y-%m-%d %H:%M")}
        for z in zeilen
    ]


async def wirkung_fuer_site(site_id: str) -> Optional[Dict[str, Any]]:
    """
    Zusammenfassung fuer den Pruefnachweis und das Dashboard.

    Gibt None zurueck, wenn noch nichts gemeldet wurde — dann steht im
    Nachweis "noch keine Betriebsdaten" statt einer geschoenten Null.
    """
    if not db_pool:
        return None
    async with db_pool.acquire() as conn:
        zeilen = await conn.fetch(
            """SELECT pfad, angewendet, verfehlt, erwartet, aufrufe, zuletzt
               FROM accessibility_wirkung WHERE site_id = $1
               ORDER BY zuletzt DESC LIMIT 500""",
            site_id,
        )
    if not zeilen:
        return None

    seiten = len(zeilen)
    angewendet = sum(z["angewendet"] for z in zeilen)
    verfehlt = sum(z["verfehlt"] for z in zeilen)
    mit_verfehlt = [z for z in zeilen if z["verfehlt"] > 0]

    return {
        "seiten_beobachtet": seiten,
        "aufrufe": sum(z["aufrufe"] for z in zeilen),
        "reparaturen_angewendet": angewendet,
        "ziele_verfehlt": verfehlt,
        "zuletzt_bestaetigt": max(z["zuletzt"] for z in zeilen).strftime("%Y-%m-%d %H:%M"),
        # Nur Pfade, keine ganzen URLs — der Nachweis ist oeffentlich.
        "seiten_mit_verfehlten_zielen": [
            {"pfad": z["pfad"], "verfehlt": z["verfehlt"]} for z in mit_verfehlt[:10]
        ],
    }


async def init_wirkung_routes(pool) -> None:
    global db_pool
    db_pool = pool
    if pool:
        try:
            async with pool.acquire() as conn:
                await conn.execute(SCHEMA)
            logger.info("✅ Wirkungsueberwachung bereit")
        except Exception as e:
            logger.error(f"Wirkungs-Tabelle nicht angelegt: {e}")
