"""
Barrierefreiheit über ein ganzes Website-Portfolio.

Warum es das braucht
--------------------
Der Agentur-Tarif kostet 299 €, der Einzeltarif 49 €. Bei zwanzig Kundenseiten
sind das 980 € gegen 299 € — der Preis trägt sich nur, wenn die Arbeit auch wie
EIN Vorgang läuft und nicht wie zwanzig. Für Barrierefreiheit gab es bisher
keinen einzigen portfolioweiten Griff: zwanzig Websites hießen zwanzig Wechsel
der aktiven Site, zwanzig Worklists, zwanzig Mal dieselbe Frage.

Was gebündelt werden darf — und was nicht
-----------------------------------------
Die naheliegende Idee war, Entscheidungen über Websites hinweg
zusammenzufassen: einmal entscheiden, überall anwenden. Die Messung über 24
echte Kundenseiten (06.08.2026) hat sie widerlegt — **63 Farbpaare, kein
einziges kommt auf mehr als einer Website vor**. Marken haben eigene Farben;
eine websiteübergreifende Farbfreigabe wäre geraten, nicht abgeleitet. Sie
gibt es hier deshalb nicht.

Was sich sehr wohl bündeln lässt, ist die Alt-Text-Freigabe — nicht wegen
Wiederholung, sondern weil die Konfidenz die Arbeit sauber trennt. Im echten
Bestand gibt es genau zwei Werte: **0,900 für Vorschläge, bei denen Claude
Vision das Bild gesehen hat, und 0,700 für die Kontext-Heuristik**, die
Ergebnisse wie "Bild: Image 20" liefert — Texte, die ein Attribut füllen und
nichts erklären. Die Schwelle ist damit gemessen, nicht gesetzt.

Die Aufteilung also:
  - Sammelfreigabe portfolioweit: Alt-Texte ab einer Konfidenzschwelle,
    nichtssagende ausgeschlossen.
  - Farben: je Website in einem Zug, aber alle Websites in EINER Liste, nach
    Wirkung sortiert. Der Weg wird kurz, die Entscheidung bleibt beim Menschen.
"""
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from accessibility_fix_saver import AccessibilityFixSaver
from dependencies import get_current_user as get_required_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/accessibility/agency", tags=["accessibility-agency"])

db_pool = None

# Unterhalb dieser Konfidenz hat keine KI das Bild gesehen — der Vorschlag
# stammt aus der Kontext-Heuristik. Im Bestand liegt dazwischen nichts: 0,900
# oder 0,700, nichts dazwischen. Als Standard deshalb 0,9.
VISION_SCHWELLE = 0.9


class SammelfreigabeRequest(BaseModel):
    """Portfolioweite Alt-Text-Freigabe ab einer Konfidenzschwelle."""
    min_konfidenz: float = Field(
        VISION_SCHWELLE, ge=0.0, le=1.0,
        description="Nur Vorschläge ab dieser Konfidenz. 0,9 = Claude Vision.",
    )
    site_ids: Optional[List[str]] = Field(
        None, description="Auf diese Websites beschränken. Standard: alle eigenen."
    )


class FarbenFreigabeRequest(BaseModel):
    """Alle offenen Farbentscheidungen EINER Website in einem Zug."""
    site_id: str


async def _eigene_sites(user_id: Any) -> List[Dict[str, str]]:
    """Websites des Kontos, mit Kundenzuordnung falls hinterlegt.

    Die Zuordnung steht in `cookie_banner_configs` (dort legt der
    Agentur-Bereich sie an), die Website-Liste in `tracked_websites`.
    """
    if not db_pool:
        return []
    from cookie_compliance_routes import _url_to_site_id

    async with db_pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT url FROM tracked_websites WHERE user_id = $1 ORDER BY url", user_id
        )
        kunden = {
            r["site_id"]: r["client_name"]
            for r in await conn.fetch(
                """SELECT site_id, client_name FROM cookie_banner_configs
                   WHERE user_id = $1 AND client_name IS NOT NULL""",
                user_id,
            )
        }

    sites = []
    for r in rows:
        sid = _url_to_site_id(r["url"])
        if sid:
            sites.append({"site_id": sid, "url": r["url"],
                          "client_name": kunden.get(sid, "")})
    return sites


def _ist_brauchbar(fix: Dict[str, Any], schwelle: float) -> bool:
    """Taugt dieser Alt-Text für eine Freigabe ohne Einzelprüfung?"""
    from fix_patch_builder import ist_nichtssagend

    try:
        konfidenz = float(fix.get("confidence") or 0)
    except (TypeError, ValueError):
        return False
    if konfidenz < schwelle:
        return False
    # Doppelter Boden: auch ein hoch bewerteter Vorschlag darf nicht
    # nichtssagend sein. Kostet nichts und schliesst eine ganze Fehlerklasse aus.
    return not ist_nichtssagend(fix.get("suggested_alt") or "")


@router.get("/worklist")
async def agentur_worklist(
    current_user: Dict[str, Any] = Depends(get_required_user)
) -> Dict[str, Any]:
    """
    Eine Liste für alle Websites des Kontos.

    Liefert je Website die offenen Posten und zusätzlich alle offenen
    Farbentscheidungen in einer gemeinsamen, nach Wirkung sortierten Liste —
    damit der Weg durchs Portfolio einmal geht und nicht zwanzigmal.
    """
    user_id = current_user.get("user_id") or current_user.get("id")
    sites = await _eigene_sites(user_id)
    if not sites:
        return {"success": True, "sites": [], "kontrast_offen": [],
                "summe": {"websites": 0, "websites_mit_arbeit": 0,
                          "offen": 0, "stellen": 0}}

    saver = AccessibilityFixSaver(db_pool)
    je_site: List[Dict[str, Any]] = []
    kontrast_offen: List[Dict[str, Any]] = []

    for site in sites:
        sid = site["site_id"]
        try:
            alt_pending = await saver.get_review_queue(sid, status="pending")
            link_pending = await saver.get_link_fixes_for_site(sid, status="pending")
            kontrast = await saver.get_kontrast_entscheidungen(sid)
        except Exception as e:
            logger.warning(f"Portfolio: {sid} übersprungen ({e})")
            continue

        offene_farben = [e for e in kontrast if e.get("freigabe") == "pending"]
        for e in offene_farben:
            kontrast_offen.append({**e, "site_id": sid, "url": site["url"],
                                   "client_name": site["client_name"]})

        je_site.append({
            **site,
            "alt_texte_offen": len(alt_pending),
            "alt_texte_sammelbar": len(
                [f for f in alt_pending if _ist_brauchbar(f, VISION_SCHWELLE)]
            ),
            "links_offen": len(link_pending),
            "farben_offen": len(offene_farben),
            "farben_freigegeben": len([e for e in kontrast
                                       if e.get("freigabe") == "approved"]),
            # Die Zahl, die den Aufwand rechtfertigt: nicht wie viele Klicks,
            # sondern wie viele Fundstellen daran haengen.
            "stellen_offen": sum(int(e.get("stellen") or 0) for e in offene_farben),
            "offen_gesamt": len(alt_pending) + len(link_pending) + len(offene_farben),
        })

    kontrast_offen.sort(key=lambda e: -int(e.get("stellen") or 0))
    je_site.sort(key=lambda s: -s["offen_gesamt"])

    return {
        "success": True,
        "sites": je_site,
        "kontrast_offen": kontrast_offen,
        "summe": {
            "websites": len(je_site),
            "websites_mit_arbeit": len([s for s in je_site if s["offen_gesamt"]]),
            "offen": sum(s["offen_gesamt"] for s in je_site),
            "stellen": sum(s["stellen_offen"] for s in je_site),
            "alt_texte_sammelbar": sum(s["alt_texte_sammelbar"] for s in je_site),
        },
    }


@router.get("/sammelfreigabe/vorschau")
async def sammelfreigabe_vorschau(
    min_konfidenz: float = Query(VISION_SCHWELLE, ge=0.0, le=1.0),
    current_user: Dict[str, Any] = Depends(get_required_user)
) -> Dict[str, Any]:
    """
    Was eine Sammelfreigabe treffen würde — vor dem Klick, nicht danach.

    Eine Massenaktion ohne vorherige Auskunft darüber, was sie anfasst, ist
    genau die Art von Knopf, den man einmal drückt und danach bereut.
    """
    user_id = current_user.get("user_id") or current_user.get("id")
    saver = AccessibilityFixSaver(db_pool)

    trifft, bleibt, verworfen = 0, 0, 0
    websites = 0
    beispiele: List[Dict[str, Any]] = []

    for site in await _eigene_sites(user_id):
        try:
            offen = await saver.get_review_queue(site["site_id"], status="pending")
        except Exception:
            continue
        treffer = 0
        for fix in offen:
            if _ist_brauchbar(fix, min_konfidenz):
                treffer += 1
                if len(beispiele) < 5:
                    beispiele.append({
                        "site_id": site["site_id"],
                        "bild": fix.get("image_filename"),
                        "alt": fix.get("suggested_alt"),
                        "konfidenz": float(fix.get("confidence") or 0),
                    })
            elif float(fix.get("confidence") or 0) >= min_konfidenz:
                verworfen += 1          # hohe Konfidenz, aber nichtssagend
            else:
                bleibt += 1
        trifft += treffer
        if treffer:
            websites += 1

    return {
        "success": True,
        "min_konfidenz": min_konfidenz,
        "wird_freigegeben": trifft,
        "auf_websites": websites,
        "bleibt_zur_pruefung": bleibt,
        "wegen_nichtssagend_uebersprungen": verworfen,
        "beispiele": beispiele,
        "hinweis": (
            "Farben sind bewusst nicht dabei: 63 Farbpaare über 24 gemessene "
            "Websites, kein einziges auf mehr als einer. Eine "
            "websiteübergreifende Farbfreigabe wäre geraten, nicht abgeleitet."
        ),
    }


@router.post("/sammelfreigabe")
async def sammelfreigabe(
    request: SammelfreigabeRequest,
    current_user: Dict[str, Any] = Depends(get_required_user)
) -> Dict[str, Any]:
    """Gibt die Alt-Texte ab der Konfidenzschwelle über das Portfolio frei."""
    user_id = current_user.get("user_id") or current_user.get("id")

    sites = await _eigene_sites(user_id)
    if request.site_ids:
        erlaubt = {s["site_id"] for s in sites}
        fremd = set(request.site_ids) - erlaubt
        if fremd:
            raise HTTPException(status_code=403, detail="Kein Zugriff auf diese Website")
        sites = [s for s in sites if s["site_id"] in set(request.site_ids)]

    saver = AccessibilityFixSaver(db_pool)
    freigegeben = 0
    je_site: Dict[str, int] = {}
    for site in sites:
        try:
            offen = await saver.get_review_queue(site["site_id"], status="pending")
        except Exception as e:
            logger.warning(f"Sammelfreigabe: {site['site_id']} übersprungen ({e})")
            continue
        for fix in offen:
            if not _ist_brauchbar(fix, request.min_konfidenz):
                continue
            fix_id = fix.get("id")
            if fix_id is None:
                continue
            try:
                await saver.set_status(fix_id=fix_id, status="approved", user_id=user_id)
            except PermissionError:
                continue
            freigegeben += 1
            je_site[site["site_id"]] = je_site.get(site["site_id"], 0) + 1

    logger.info(f"Sammelfreigabe user={user_id}: {freigegeben} Alt-Texte "
                f"auf {len(je_site)} Website(s), Schwelle {request.min_konfidenz}")
    return {
        "success": True,
        "freigegeben": freigegeben,
        "auf_websites": len(je_site),
        "je_website": je_site,
        "min_konfidenz": request.min_konfidenz,
    }


@router.post("/farben-freigeben")
async def farben_freigeben(
    request: FarbenFreigabeRequest,
    current_user: Dict[str, Any] = Depends(get_required_user)
) -> Dict[str, Any]:
    """
    Alle offenen Farbentscheidungen EINER Website in einem Zug.

    Die Website bleibt die Einheit — nicht das Portfolio. Farben gehören zur
    Marke, und wer sie ändert, sollte die Seite vor Augen haben. Der Gewinn
    liegt darin, dass die Agentur dafür nicht mehr die aktive Website wechseln
    und eine eigene Worklist öffnen muss.

    Vorschläge, die die Vorgabe nicht erreichen, sind nicht dabei: sie stehen
    gar nicht als lösbar in der Liste.
    """
    user_id = current_user.get("user_id") or current_user.get("id")
    sites = {s["site_id"] for s in await _eigene_sites(user_id)}
    if request.site_id not in sites:
        raise HTTPException(status_code=403, detail="Kein Zugriff auf diese Website")

    saver = AccessibilityFixSaver(db_pool)
    entscheidungen = await saver.get_kontrast_entscheidungen(request.site_id)
    offen = [e for e in entscheidungen
             if e.get("freigabe") == "pending" and e.get("loesbar")]

    freigegeben, stellen = 0, 0
    for e in offen:
        ergebnis = await saver.set_kontrast_freigabe(
            request.site_id, index=e["index"], status="approved", user_id=user_id
        )
        if ergebnis.get("ok"):
            freigegeben += 1
            stellen += int(e.get("stellen") or 0)

    return {
        "success": True,
        "site_id": request.site_id,
        "freigegeben": freigegeben,
        "stellen": stellen,
        "nicht_loesbar": len([e for e in entscheidungen
                              if e.get("freigabe") == "pending" and not e.get("loesbar")]),
    }


def init_agentur_a11y_routes(pool) -> None:
    global db_pool
    db_pool = pool
    logger.info("✅ Agentur-A11y-Routen bereit")
