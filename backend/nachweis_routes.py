"""
Der öffentliche Prüfnachweis.

Warum öffentlich
----------------
Ein Nachweis, den nur der Betreiber sieht, ist kein Nachweis, sondern ein
Bericht. Der Wert entsteht erst, wenn ein Dritter ihn aufrufen kann: die
Prüfstelle, der Anwalt der Gegenseite, ein Besucher, der eine Barriere gemeldet
hat. Deshalb hängt der Link in der Barrierefreiheitserklärung, und deshalb
braucht er keine Anmeldung.

Was das nicht ist
-----------------
Kein Siegel. Ein Siegel behauptet ein Ergebnis; dieses Protokoll zeigt eine
Methode und **benennt seine eigenen Lücken**. Hugo vergibt ab Score 60 ein
Verifikations-Siegel — das ist eine Note, keine Nachprüfbarkeit.

Datensparsam
------------
Ausgeliefert werden Messwerte, Regelnamen und Begründungen. Keine
Kundendaten, keine E-Mail-Adressen, keine Nutzer-IDs. Der Zugriffsschlüssel ist
aus site_id und einem Server-Geheimnis abgeleitet: stabil (der Link in der
Erklärung darf nicht verfallen), aber nicht aus der Domain errechenbar.

Ohne konfiguriertes Geheimnis (`COMPLYO_NACHWEIS_SECRET`) liefert der Endpunkt
nichts aus. Lieber kein öffentlicher Nachweis als einer mit ratbarem Schlüssel.
"""
import json
import logging
import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse

from compliance_engine.nachweis_generator import (
    baue_nachweis, erklaerung_aus_nachweis, nachweis_token,
)
from compliance_engine.nachweis_seite import nachweis_als_html

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/nachweis", tags=["nachweis"])

db_pool = None


def _geheimnis() -> str:
    return os.getenv("COMPLYO_NACHWEIS_SECRET", "")


# Dieselbe Umformung wie `derive_site_id()`, nur in SQL: Domain aus der URL
# schaelen, Punkte zu Bindestrichen. VORWAERTS ist die Abbildung eindeutig.
_SITE_ID_AUS_URL = """
    replace(
        regexp_replace(
            regexp_replace(lower(url), '^https?://(www\\.)?', ''),
            '[/?#:].*$', ''),
        '.', '-')
"""


async def _site_url(conn, site_id: str) -> Optional[str]:
    """
    Die echte Adresse der Website — ermittelt, nie zurueckgerechnet.

    `derive_site_id()` bildet Punkt UND Bindestrich beide auf '-' ab. Die
    Kodierung ist damit verlustbehaftet: `bau-design.de` und `bau.design.de`
    ergeben dieselbe site_id. Wer sie umkehrt, raet — und der Nachweis ist ein
    oeffentliches Dokument, das in einer Barrierefreiheitserklaerung verlinkt
    wird. Die alte Umkehrung lieferte `https://loqal-io` (keine gueltige
    Adresse) und aus `bau-design-de` das fremde `bau.design.de`; ihr
    LIKE-Muster mit Platzhaltern konnte ausserdem die Domain einer ANDEREN
    Kundenseite treffen.

    Deshalb nur zwei Quellen, beide eindeutig:
      1. `tracked_websites`, ueber die VORWAERTS gerechnete site_id verglichen.
      2. die tatsaechlich gescannte Seitenadresse aus den Alt-Text-Befunden.

    Findet sich keine, gibt es keinen Nachweis. Ein oeffentliches Protokoll
    mit falscher Domain waere schlimmer als gar keins.
    """
    url = await conn.fetchval(
        f"""SELECT url FROM tracked_websites
            WHERE {_SITE_ID_AUS_URL} = $1
            ORDER BY is_primary DESC, created_at ASC
            LIMIT 1""",
        site_id,
    )
    if url:
        return url

    seite = await conn.fetchval(
        """SELECT page_url FROM accessibility_alt_text_fixes
           WHERE site_id = $1 AND page_url <> '' ORDER BY id LIMIT 1""",
        site_id,
    )
    if seite:
        from urllib.parse import urlsplit
        teile = urlsplit(seite)
        if teile.scheme in ("http", "https") and teile.netloc:
            return f"{teile.scheme}://{teile.netloc}"
    return None


async def _daten_fuer(site_id: str) -> Optional[Dict[str, Any]]:
    """Sammelt die gespeicherten Messungen und Reparaturen einer Site."""
    if not db_pool:
        return None

    async with db_pool.acquire() as conn:
        zeilen = await conn.fetch(
            """SELECT fix_type, payload, status, updated_at
               FROM accessibility_document_fixes
               WHERE site_id = $1 AND fix_type IN ('kontrast-css', 'struktur')""",
            site_id,
        )
        # Bildbeschreibungen sind eine eigene Messgroesse, kein axe-Befund:
        # axe prueft, OB ein alt-Attribut da ist, nicht ob es etwas taugt. Sie
        # gehoeren deshalb getrennt ausgewiesen — und sie sind fuer sich allein
        # schon ein Nachweis wert.
        alt = await conn.fetchrow(
            """SELECT COUNT(*) FILTER (WHERE status = 'approved') AS live,
                      COUNT(*) FILTER (WHERE status = 'pending')  AS offen,
                      COUNT(*) AS gesamt,
                      MAX(updated_at) AS zuletzt
               FROM accessibility_alt_text_fixes WHERE site_id = $1""",
            site_id,
        )
        url = await _site_url(conn, site_id)

    alt_live = int((alt and alt["live"]) or 0)
    alt_offen = int((alt and alt["offen"]) or 0)

    # Ohne ermittelbare Adresse kein oeffentliches Protokoll — siehe _site_url.
    if not url:
        logger.warning("Nachweis fuer %s ohne ermittelbare URL — nicht ausgeliefert",
                       site_id)
        return None

    # Eine Site, deren gesamte Arbeit aus Bildbeschreibungen besteht, hat hier
    # keine Zeile. Frueher hiess das 404: der wichtigste Beleg fehlte
    # ausgerechnet im einfachsten Kundenfall.
    if not zeilen and not (alt and alt["gesamt"]):
        return None

    vorher: Dict[str, int] = {}
    nachher: Dict[str, int] = {}
    fixes: List[Dict[str, Any]] = []
    vorbereitet: List[Dict[str, Any]] = []
    gemessen_am = None

    for z in zeilen:
        payload = z["payload"]
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except (ValueError, TypeError):
                continue
        if not isinstance(payload, dict):
            continue

        # Nur freigegebene Reparaturen zaehlen als behoben. Ein Protokoll ueber
        # Fixes, die nie live gingen, waere eine Faelschung.
        #
        # Eine noch nicht freigegebene Reparatur ist aber auch keine Null: die
        # Seite WURDE gemessen, und die Reparatur wurde im Browser nachgemessen
        # — sie wartet nur auf eine Entscheidung. Frueher fuehrte das zu 404;
        # eine Website, an der alles vorbereitet ist, hatte gar keinen
        # Nachweis. Jetzt steht der Befund als offen im Protokoll und die
        # geprueften Reparaturen daneben, ausdruecklich als "nicht live".
        if z["status"] != "approved":
            if z["fix_type"] == "struktur":
                for regel, werte in (payload.get("je_regel") or {}).items():
                    if isinstance(werte, (list, tuple)) and len(werte) == 2:
                        vorher[regel] = vorher.get(regel, 0) + int(werte[0])
                        nachher[regel] = nachher.get(regel, 0) + int(werte[0])
                        vorbereitet.append({
                            "regel": regel, "fundstellen": int(werte[0]),
                            "nachgemessen": int(werte[1]),
                        })
            elif z["fix_type"] == "kontrast-css":
                v = int(payload.get("vorher") or 0)
                vorher["color-contrast"] = vorher.get("color-contrast", 0) + v
                nachher["color-contrast"] = nachher.get("color-contrast", 0) + v
                if v:
                    vorbereitet.append({
                        "regel": "color-contrast", "fundstellen": v,
                        "nachgemessen": int(payload.get("nachher") or 0),
                    })
            if z["updated_at"] and (not gemessen_am or z["updated_at"] > gemessen_am):
                gemessen_am = z["updated_at"]
            continue

        if z["fix_type"] == "struktur":
            for regel, werte in (payload.get("je_regel") or {}).items():
                if isinstance(werte, (list, tuple)) and len(werte) == 2:
                    vorher[regel] = vorher.get(regel, 0) + int(werte[0])
                    nachher[regel] = nachher.get(regel, 0) + int(werte[1])
            fixes.extend(payload.get("fixes") or [])
        elif z["fix_type"] == "kontrast-css":
            vorher["color-contrast"] = int(payload.get("vorher") or 0)
            nachher["color-contrast"] = int(payload.get("nachher") or 0)
            for e in payload.get("entscheidungen") or []:
                if e.get("freigabe") != "approved":
                    continue
                fixes.append({
                    "regel": "color-contrast",
                    "attribut": "color",
                    "selector": (e.get("selektoren") or [""])[0],
                    "begruendung": (
                        f"{e.get('vordergrund')} auf {e.get('hintergrund')}: "
                        f"{e.get('ist_ratio')}:1 → {e.get('neue_ratio')}:1 "
                        f"({e.get('stellen')} Stellen)"
                    ),
                })
        if z["updated_at"] and (not gemessen_am or z["updated_at"] > gemessen_am):
            gemessen_am = z["updated_at"]

    # Kein Messwert UND keine Bildbeschreibung: es gibt nichts zu belegen.
    if not vorher and not (alt and alt["gesamt"]):
        return None

    if alt and alt["zuletzt"] and (not gemessen_am or alt["zuletzt"] > gemessen_am):
        gemessen_am = alt["zuletzt"]

    return {
        "site_url": url,
        "vorher": vorher,
        "nachher": nachher,
        "fixes": fixes,
        "vorbereitet": vorbereitet,
        "alt_live": alt_live,
        "alt_offen": alt_offen,
        "gemessen_am": gemessen_am.strftime("%Y-%m-%d %H:%M") if gemessen_am else None,
    }


@router.get("/{site_id}/{token}")
async def oeffentlicher_nachweis(site_id: str, token: str) -> JSONResponse:
    """
    Das Prüfprotokoll einer Website — ohne Anmeldung abrufbar.

    Der Token muss zur site_id passen; ein falscher gibt 404, nicht 403. Ob es
    zu einer Domain überhaupt einen Nachweis gibt, ist selbst eine Auskunft.
    """
    geheim = _geheimnis()
    if not geheim:
        logger.warning("COMPLYO_NACHWEIS_SECRET nicht gesetzt — Nachweis deaktiviert")
        raise HTTPException(status_code=404, detail="Nicht gefunden")

    import hmac
    if not hmac.compare_digest(token, nachweis_token(site_id, geheim)):
        raise HTTPException(status_code=404, detail="Nicht gefunden")

    daten = await _daten_fuer(site_id)
    if not daten:
        raise HTTPException(status_code=404, detail="Nicht gefunden")

    nachweis = baue_nachweis(
        site_id=site_id,
        site_url=daten["site_url"],
        messung_vorher=daten["vorher"],
        messung_nachher=daten["nachher"],
        fixes=daten["fixes"],
        alt_texte_live=daten["alt_live"],
        alt_texte_offen=daten["alt_offen"],
        vorbereitet=daten["vorbereitet"],
        gemessen_am=daten["gemessen_am"],
    )

    # Betriebsdaten aus dem Widget: was auf echten Seitenaufrufen tatsaechlich
    # ankommt. Der Scan misst einen Zeitpunkt und eine Seite; das hier misst
    # laufend und alle. Fehlt es, steht das ausdruecklich da statt einer Null.
    from wirkung_routes import wirkung_fuer_site
    nachweis["im_betrieb"] = await wirkung_fuer_site(site_id) or {
        "hinweis": "Noch keine Betriebsdaten — das Widget hat sich noch nicht gemeldet.",
    }

    return JSONResponse(
        content=nachweis,
        headers={
            "Access-Control-Allow-Origin": "*",
            # Kurz cachen: der Nachweis aendert sich nur mit einem neuen Scan,
            # muss aber nach einer Reparatur zeitnah stimmen.
            "Cache-Control": "public, max-age=900",
        },
    )


@router.get("/{site_id}/{token}/seite", response_class=HTMLResponse)
async def nachweis_seite(site_id: str, token: str) -> HTMLResponse:
    """
    Die lesbare Fassung — das, was man einer Pruefstelle schickt.

    Eigenstaendige Seite ohne fremde Schriften, ohne Analyse-Skript, ohne
    Rahmenwerk. Ein Nachweis, der selbst Daten an Dritte abgibt, waere ein
    schlechter Witz; einer ueber Barrierefreiheit, der selbst nicht
    barrierefrei ist, waere schlimmer.
    """
    antwort = await oeffentlicher_nachweis(site_id, token)
    return HTMLResponse(
        content=nachweis_als_html(json.loads(antwort.body)),
        headers={"Cache-Control": "public, max-age=900",
                 "X-Content-Type-Options": "nosniff"},
    )


def _fremdtext(wert: str, grenze: int = 200) -> str:
    """
    Text aus der Abfragezeichenkette entschaerfen.

    `anbieter` und `kontakt` kommen ungeprueft von aussen und landen in einem
    Markdown-Text, den der Betreiber anschliessend in seine Website einsetzt.
    Markdown-Darsteller lassen rohes HTML meist durch — ein praeparierter Link
    ("hier ist Ihre Erklaerung") koennte so ein Skript in eine fremde Seite
    tragen. Ausgerechnet ueber das Dokument, das Vertrauen herstellen soll.

    Deshalb: spitze Klammern und Zeilenumbrueche raus, Laenge begrenzt.
    """
    if not wert:
        return ""
    sauber = wert.replace("<", "").replace(">", "")
    sauber = " ".join(sauber.split())
    return sauber[:grenze]


@router.get("/{site_id}/{token}/erklaerung")
async def oeffentliche_erklaerung(
    site_id: str, token: str, anbieter: str = "", kontakt: str = ""
) -> JSONResponse:
    """Die Barrierefreiheitserklärung als Markdown — aus derselben Messung."""
    antwort = await oeffentlicher_nachweis(site_id, token)
    nachweis = json.loads(antwort.body)

    basis = os.getenv("COMPLYO_PUBLIC_URL", "https://complyo.de").rstrip("/")
    text = erklaerung_aus_nachweis(
        nachweis,
        anbieter=_fremdtext(anbieter) or nachweis["site_url"],
        kontakt=_fremdtext(kontakt) or "über das Kontaktformular dieser Website",
        nachweis_url=f"{basis}/nachweis/{site_id}/{token}",
    )
    return JSONResponse(
        content={"markdown": text, "gemessen_am": nachweis["gemessen_am"]},
        headers={"Access-Control-Allow-Origin": "*",
                 "Cache-Control": "public, max-age=900"},
    )


def init_nachweis_routes(pool) -> None:
    global db_pool
    db_pool = pool
    if not _geheimnis():
        logger.warning(
            "COMPLYO_NACHWEIS_SECRET fehlt — der oeffentliche Pruefnachweis "
            "bleibt aus. Ohne Geheimnis waere der Zugriffsschluessel ratbar."
        )
    else:
        logger.info("✅ Oeffentlicher Pruefnachweis bereit")
