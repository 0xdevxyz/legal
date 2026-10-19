"""Prüfstufe für den Banner-Scan: was die Seite wirklich lädt, im echten Browser.

Der Banner-Scan (`CookieScanner.scan_website`) liest nur das HTML und sucht
bekannte Muster. Was ein Skript erst zur Laufzeit nachlädt, sieht er nicht.
Diese Stufe öffnet die Seite einmal wie ein Besucher ohne Einwilligung, schneidet
jeden Request mit und ordnet die Fremdhosts dem Dienstkatalog zu.

**Warum sie hinter dem Scan sitzt und nicht darin.** Der Browser braucht 15 bis
40 Sekunden und 150 bis 300 MiB. Liefe er im Request, hinge bei 100 gleichzeitigen
Nutzern jede Antwort an einer Schlange von Browsern, und das 2-GiB-Limit des
Backends wäre nach wenigen Minuten erreicht (so stand es 03.09.2026 beim
Preview-Scan, siehe scan_arbeiter.py). Deshalb:

1. Der HTML-Scan antwortet wie bisher sofort. Die Prüfstufe kommt NACH der
   Antwort und kann den Banner nie aufhalten oder zum Ausfall bringen.
2. Eigene kleine Schlange mit eigenen Arbeitern (Vorgabe 2). Die sechs Browser-
   Plätze des Backends gehören zuerst dem öffentlichen Scanner auf der Startseite;
   die Prüfstufe hält höchstens zwei davon und nimmt sie über denselben
   Semaphor, nie zusätzlich.
3. Doppelte Aufträge für dieselbe Seite fallen weg (laufend oder in der Schlange),
   ein frisches Ergebnis (10 Minuten) wird wiederverwendet.
4. Zeitbudget je Auftrag (75 s), danach wird der Browser beendet. Volle Schlange
   (200) heißt: ehrlich "voll" melden, der HTML-Scan gilt weiter.
5. Der Wochenlauf läuft nur, wenn die Schlange leer ist, höchstens sechs Seiten
   pro Stunde, und ändert nichts am Banner (nur Bericht).

**Genauigkeit vor Vollständigkeit.** Eine Zuordnung, die falsch ist, kostet mehr
Vertrauen als eine, die fehlt. Deshalb ordnet die Stufe strenger zu als der
Premium-Scanner:

- Nach Host (genaueste Domain gewinnt), nicht nach Teilstring in der URL.
- Eine Domain, die mehrere Dienste beanspruchen (google.com gehört im Katalog zu
  Maps, reCAPTCHA und DV360), wird nur über eine ausdrückliche Pfadregel
  zugeordnet, sonst landet sie in der Prüfliste.
- Breite Hosts (googleapis.com, amazonaws.com, cloudflare.com) ordnen nie von
  selbst zu.
- Cookie-Namen allein fügen nichts hinzu (NID, ts, sid gibt es bei mehreren
  Diensten). Sie erscheinen nur als Hinweis.
- Die Stufe FÜGT NUR HINZU. Was der HTML-Scan fand, bleibt, auch wenn der Browser
  es nicht sah (Dienste können erst nach Einwilligung oder nur in bestimmten
  Ländern laden).

Fail-open durchgehend: ohne Redis, ohne Browser, bei Zeitüberschreitung oder
Fehler bleibt das Ergebnis des HTML-Scans stehen.
"""

import asyncio
import itertools
import json
import logging
import os
import time
from collections import deque
from typing import Any, Deque, Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


def _int_env(name: str, vorgabe: int, minimum: int = 1) -> int:
    try:
        return max(minimum, int(os.getenv(name, str(vorgabe))))
    except ValueError:
        return vorgabe


AKTIV = os.getenv("COMPLYO_PRUEFSTUFE", "1") != "0"
ARBEITER_ANZAHL = _int_env("COMPLYO_PRUEFSTUFE_ARBEITER", 2)
SCHLANGE_MAX = _int_env("COMPLYO_PRUEFSTUFE_SCHLANGE", 200)
JOB_ZEIT_S = _int_env("COMPLYO_PRUEFSTUFE_ZEIT", 75, minimum=10)
WIEDERHOLSPERRE_S = _int_env("COMPLYO_PRUEFSTUFE_SPERRE", 600, minimum=0)
WOCHE_AKTIV = os.getenv("COMPLYO_PRUEFSTUFE_WOCHE", "1") != "0"
WOCHE_PRO_STUNDE = _int_env("COMPLYO_PRUEFSTUFE_WOCHE_PRO_STUNDE", 6)
WOCHE_ABSTAND_S = 7 * 24 * 3600
ERGEBNIS_TTL_S = 8 * 24 * 3600
KATALOG_TTL_S = 600
SPEICHER_MAX = 2000          # Ergebnisse im Prozess, älteste zuerst raus
# Reihenfolge: angemeldete Nutzer, anonyme Nutzer, Wochenlauf. Anonyme dürfen die
# Schlange nur bis zu drei Vierteln füllen, damit ein Strom fremder Adressen
# (der HTML-Scan ist ohne Konto erreichbar) angemeldeten Kunden nicht den Platz nimmt.
PRIO_NUTZER, PRIO_ANONYM, PRIO_WOCHE = 0, 1, 2
FEHLSCHLAG_SPERRE_S = 60

WARTEND, LAEUFT, FERTIG, FEHLGESCHLAGEN = "wartend", "laeuft", "fertig", "fehlgeschlagen"

# Hosts, die zu viele Zwecke bedienen, um allein einen Dienst zu belegen.
# googleapis.com liefert Maps, Fonts, Ajax-Bibliotheken und Speicher; wer von
# dort lädt, hat damit noch nicht Google Maps eingebunden.
BREITE_DOMAINS = {
    "google.com", "googleapis.com", "gstatic.com", "amazonaws.com",
    "cloudfront.net", "cloudflare.com", "azureedge.net", "akamaihd.net",
    "fastly.net",
    # Einzelne Hosts, die der Katalog einem Dienst zuschreibt, die aber viele
    # bedienen: www.gstatic.com steht bei firebase_auth und lieferte im Lauf
    # vom 19.10.2026 an breathhealingart.com "Firebase Auth" ohne Firebase.
    "www.gstatic.com", "ssl.gstatic.com", "apis.google.com",
}

# Hosts, die von diesem Dienst selbst stammen: nie Fremdhost, nie Prüfliste.
EIGENE_DIENSTHOSTS = {"complyo.de"}

# Dienste, deren Aufruf von der Umgebung des Browsers abhängt. WordPress lädt die
# Emoji-Grafiken von s.w.org nur, wenn der Browser keine Emoji-Schrift hat; ein
# Headless-Chromium im Container hat keine, ein echter Besucher meist doch. Ein
# Request allein belegt hier deshalb nichts; der HTML-Scan (das Skript steht im
# Quelltext) bleibt die Quelle.
UMGEBUNGSABHAENGIG = {"wordpress_emojis"}

# Katalogeinträge, die denselben Dienst in zwei Fassungen führen. Ist einer
# bekannt, ist der andere nicht "neu".
GLEICHWERTIG = [{"youtube", "youtube_embedded"}]

# Ausdrückliche Zuordnung dort, wo der Katalog nur den Host kennt, der Host aber
# mehrere Dienste bedient: (Host-Endung, Pfad-Präfix, Abfrage-Präfix, Dienst).
# Bewusst klein und einzeln belegt. Alles Weitere bleibt Prüfliste.
PFADREGELN: List[Tuple[str, str, str, str]] = [
    ("googletagmanager.com", "/gtag/js", "id=G-", "google_analytics_ga4"),
    ("googletagmanager.com", "/gtm.js", "id=GTM-", "google_tag_manager"),
    # GA4 sendet an /g/collect (auch region1.google-analytics.com), das alte
    # Universal Analytics an /collect, /j/collect und lädt /analytics.js.
    ("google-analytics.com", "/g/collect", "", "google_analytics_ga4"),
    ("google-analytics.com", "/analytics.js", "", "google_analytics_ua"),
    ("google.com", "/recaptcha", "", "google_recaptcha"),
    ("google.com", "/maps", "", "google_maps"),
    ("maps.googleapis.com", "/maps", "", "google_maps"),
]

_ZWEITEBENE = {"co", "com", "org", "net", "gov", "ac", "edu"}


# --------------------------------------------------------------------------
# Zuordnung (reine Funktionen, ohne Browser und ohne Datenbank testbar)
# --------------------------------------------------------------------------

def host_von(url: str) -> str:
    try:
        return (urlparse(url).hostname or "").lower().rstrip(".")
    except Exception:
        return ""


def registrierbar(host: str) -> str:
    """Grobe registrierbare Domain (example.com, example.co.uk)."""
    teile = [t for t in host.split(".") if t]
    if len(teile) <= 2:
        return ".".join(teile)
    if len(teile[-1]) == 2 and teile[-2] in _ZWEITEBENE:
        return ".".join(teile[-3:])
    return ".".join(teile[-2:])


def ist_eigener_host(host: str, seitenhost: str) -> bool:
    if not host or not seitenhost:
        return False
    return registrierbar(host) == registrierbar(seitenhost)


def baue_index(katalog: List[dict]) -> Dict[str, Set[str]]:
    """Domain -> Dienstschlüssel. Nur echte Domains (mit Punkt)."""
    index: Dict[str, Set[str]] = {}
    for svc in katalog or []:
        key = svc.get("service_key")
        if not key:
            continue
        for dom in svc.get("domains", []) or []:
            d = (dom or "").lower().strip().rstrip(".")
            if d and "." in d and "/" not in d:
                index.setdefault(d, set()).add(key)
    return index


def _endungen(host: str) -> List[str]:
    """host, dann jede kürzere Endung bis zur zweiten Ebene, genaueste zuerst."""
    teile = host.split(".")
    return [".".join(teile[i:]) for i in range(0, max(1, len(teile) - 1))]


def zuordnen(url: str, index: Dict[str, Set[str]]) -> Tuple[str, Optional[str], List[str]]:
    """Ordnet eine Request-URL zu.

    Rückgabe (status, dienst, kandidaten) mit status eindeutig, mehrdeutig,
    breit oder unbekannt.
    """
    p = urlparse(url)
    host = (p.hostname or "").lower().rstrip(".")
    if not host:
        return "unbekannt", None, []
    pfad = p.path or "/"
    abfrage = p.query or ""

    for endung, pfad_start, abf_start, dienst in PFADREGELN:
        if (host == endung or host.endswith("." + endung)) and pfad.startswith(pfad_start) \
                and (not abf_start or abf_start in abfrage):
            return "eindeutig", dienst, [dienst]

    for endung in _endungen(host):
        keys = index.get(endung)
        if not keys:
            continue
        if endung in BREITE_DOMAINS:
            return "breit", None, sorted(keys)
        if len(keys) == 1:
            return "eindeutig", next(iter(keys)), sorted(keys)
        return "mehrdeutig", None, sorted(keys)
    return "unbekannt", None, []


def bewerte(
    requests: List[dict],
    cookies: List[dict],
    seiten_url: str,
    katalog_index: Dict[str, Set[str]],
    bekannte_keys: List[str],
) -> Dict[str, Any]:
    """Wertet einen Browser-Lauf aus. Wirft nie bei kaputten Einzeleinträgen.

    `bekannte_keys` sind die Dienste, die der HTML-Scan (bzw. die gespeicherte
    Konfiguration) schon hat.
    """
    seitenhost = host_von(seiten_url)
    belege: Dict[str, Dict[str, Any]] = {}
    mehrdeutig: Dict[str, List[str]] = {}
    breit: Dict[str, int] = {}
    unbekannt: Dict[str, int] = {}
    umgebung: Dict[str, int] = {}
    eigene = 0

    for r in requests or []:
        url = r.get("url") if isinstance(r, dict) else getattr(r, "url", "")
        host = host_von(url or "")
        if not host:
            continue
        if ist_eigener_host(host, seitenhost):
            eigene += 1
            continue
        if registrierbar(host) in EIGENE_DIENSTHOSTS:
            continue
        status, dienst, kandidaten = zuordnen(url, katalog_index)
        if status == "eindeutig" and dienst in UMGEBUNGSABHAENGIG:
            umgebung[dienst] = umgebung.get(dienst, 0) + 1
            continue
        if status == "eindeutig" and dienst:
            b = belege.setdefault(dienst, {"hosts": {}, "anzahl": 0})
            b["hosts"][host] = b["hosts"].get(host, 0) + 1
            b["anzahl"] += 1
        elif status == "mehrdeutig":
            mehrdeutig[host] = kandidaten
        elif status == "breit":
            breit[host] = breit.get(host, 0) + 1
        else:
            unbekannt[host] = unbekannt.get(host, 0) + 1

    browser_keys = sorted(belege)
    bekannt = set(bekannte_keys or [])
    # Zweite Fassung desselben Dienstes: gilt als bestätigt, nicht als neu.
    gleichwertig_bekannt = {
        k for k in browser_keys
        for gruppe in GLEICHWERTIG if k in gruppe and (gruppe - {k}) & bekannt
    }
    # Mehrdeutige Hosts bestätigen höchstens, was ohnehin schon bekannt ist.
    bestaetigt_mehrdeutig = sorted({k for ks in mehrdeutig.values() for k in ks if k in bekannt})

    cookie_namen = []
    for c in cookies or []:
        n = c.get("name") if isinstance(c, dict) else getattr(c, "name", "")
        if n and n not in cookie_namen:
            cookie_namen.append(n)

    return {
        "browser_keys": browser_keys,
        "bestaetigt": sorted((set(browser_keys) & bekannt) | gleichwertig_bekannt),
        "neu": sorted(set(browser_keys) - bekannt - gleichwertig_bekannt),
        "nur_umgebungsabhaengig": umgebung,
        "nur_html": sorted(bekannt - set(browser_keys) - set(bestaetigt_mehrdeutig)),
        "mehrdeutig": {h: ks for h, ks in sorted(mehrdeutig.items())[:30]},
        "breite_hosts": dict(sorted(breit.items(), key=lambda x: -x[1])[:20]),
        "unbekannte_fremdhosts": dict(sorted(unbekannt.items(), key=lambda x: -x[1])[:30]),
        "belege": {k: {"hosts": dict(sorted(v["hosts"].items(), key=lambda x: -x[1])[:5]),
                       "anzahl": v["anzahl"]} for k, v in belege.items()},
        "requests_gesamt": len(requests or []),
        "requests_eigene": eigene,
        "cookies_gesamt": len(cookie_namen),
        "cookie_namen": cookie_namen[:30],
    }


# --------------------------------------------------------------------------
# Zustand: im Prozess, gespiegelt nach Redis (nur Anzeige, nie Voraussetzung)
# --------------------------------------------------------------------------

db_pool = None  # wird in main_production gesetzt; immer zur Laufzeit lesen

_queue: Optional["asyncio.PriorityQueue"] = None
_arbeiter: List["asyncio.Task"] = []
_woche_task: Optional["asyncio.Task"] = None
_zaehler = itertools.count()
_jobs: Dict[str, Dict[str, Any]] = {}          # site_id -> aktueller/letzter Auftrag
_dauern: Deque[float] = deque(maxlen=20)
_katalog_cache: Dict[str, Any] = {"zeit": 0.0, "katalog": [], "index": {}}
_woche_starts: Deque[float] = deque()


def laeuft() -> bool:
    return bool(_arbeiter)


def wartend_anzahl() -> int:
    return _queue.qsize() if _queue else 0


def _mittlere_dauer() -> float:
    return (sum(_dauern) / len(_dauern)) if _dauern else 25.0


def _wartezeit_s(position: int) -> int:
    return int((position / max(1, ARBEITER_ANZAHL) + 1) * _mittlere_dauer())


def _speicher_aufraeumen() -> None:
    if len(_jobs) <= SPEICHER_MAX:
        return
    fertig = sorted((j["beendet"], s) for s, j in _jobs.items() if j.get("beendet"))
    for _, s in fertig[: len(_jobs) - SPEICHER_MAX]:
        _jobs.pop(s, None)


async def _redis():
    try:
        from dependencies import get_redis
        return await get_redis()
    except Exception:
        return None


async def _spiegeln(job: Dict[str, Any]) -> None:
    r = await _redis()
    if r is None:
        return
    try:
        await r.set(f"cookie:pruefung:{job['site_id']}", json.dumps(_oeffentlich(job), default=str),
                    ex=ERGEBNIS_TTL_S)
        if job.get("zustand") == FERTIG:
            await r.set(f"cookie:pruefung:zuletzt:{job['site_id']}", str(time.time()), ex=ERGEBNIS_TTL_S)
    except Exception as e:
        logger.debug(f"Pruefstufe: Spiegelung nach Redis fehlgeschlagen: {e}")


def _oeffentlich(job: Dict[str, Any]) -> Dict[str, Any]:
    """Was nach außen geht: kein Pool, keine internen Marken."""
    return {k: job.get(k) for k in (
        "site_id", "url", "zustand", "angewendet", "hinzugefuegt", "fehler",
        "gestellt", "gestartet", "beendet", "dauer_s", "bewertung", "quelle",
    ) if k in job}


async def status(site_id: str) -> Optional[Dict[str, Any]]:
    j = _jobs.get(site_id)
    if j:
        out = _oeffentlich(j)
        if j.get("zustand") == WARTEND:
            out["geschaetzte_wartezeit_s"] = _wartezeit_s(wartend_anzahl())
        return out
    r = await _redis()
    if r is not None:
        try:
            raw = await r.get(f"cookie:pruefung:{site_id}")
            if raw:
                return json.loads(raw)
        except Exception:
            pass
    return None


# --------------------------------------------------------------------------
# Katalog
# --------------------------------------------------------------------------

def _als_objekt(v, vorgabe):
    while isinstance(v, str):
        try:
            v = json.loads(v)
        except Exception:
            return vorgabe
    return v if v is not None else vorgabe


async def _katalog_laden(pool) -> Tuple[List[dict], Dict[str, Set[str]]]:
    jetzt = time.time()
    if _katalog_cache["katalog"] and jetzt - _katalog_cache["zeit"] < KATALOG_TTL_S:
        return _katalog_cache["katalog"], _katalog_cache["index"]
    rows = await pool.fetch(
        "SELECT service_key, name, category, provider, template FROM cookie_services WHERE is_active = true"
    )
    katalog = []
    for r in rows:
        tmpl = _als_objekt(r["template"], {}) or {}
        domains = tmpl.get("domains") if isinstance(tmpl, dict) and isinstance(tmpl.get("domains"), list) else []
        katalog.append({
            "service_key": r["service_key"], "name": r["name"],
            "category": r["category"] or "functional", "provider": r["provider"] or "",
            "domains": [d for d in domains if isinstance(d, str)],
            "cookie_patterns": [],
        })
    _katalog_cache.update(zeit=jetzt, katalog=katalog, index=baue_index(katalog))
    return katalog, _katalog_cache["index"]


# --------------------------------------------------------------------------
# Banner-Konfiguration: nur hinzufügen, nie entfernen
# --------------------------------------------------------------------------

async def _bestehende_dienste(pool, site_id: str) -> Optional[List[str]]:
    row = await pool.fetchrow("SELECT services FROM cookie_banner_configs WHERE site_id = $1", site_id)
    if row is None:
        return None
    v = _als_objekt(row["services"], [])
    return [k for k in v if isinstance(k, str)] if isinstance(v, list) else []


async def anwenden(pool, site_id: str, neu: List[str]) -> List[str]:
    """Fügt Dienste zur Konfiguration hinzu. Rückgabe: wirklich ergänzte Schlüssel.

    Lesen, vereinigen, nur schreiben, wenn sich zwischenzeitlich nichts geändert
    hat (der HTML-Scan kann gleichzeitig dieselbe Zeile setzen).
    """
    if not neu:
        return []
    for _ in range(3):
        bestehend = await _bestehende_dienste(pool, site_id)
        if bestehend is None:
            return []  # keine Konfiguration, nichts zu ergänzen
        zusatz = [k for k in neu if k not in bestehend]
        if not zusatz:
            return []
        res = await pool.execute(
            "UPDATE cookie_banner_configs SET services = $2::jsonb, updated_at = NOW() "
            "WHERE site_id = $1 AND services = $3::jsonb",
            site_id, json.dumps(bestehend + zusatz), json.dumps(bestehend),
        )
        if str(res).endswith(" 1"):
            return zusatz
    logger.warning(f"Pruefstufe: {site_id} nach drei Versuchen nicht ergaenzt (parallele Aenderung)")
    return []


# --------------------------------------------------------------------------
# Warteschlange und Arbeiter
# --------------------------------------------------------------------------

async def einreihen(
    site_id: str,
    url: str,
    pool=None,
    html_keys: Optional[List[str]] = None,
    anwenden_ja: bool = True,
    prio: int = PRIO_NUTZER,
    quelle: str = "nutzer",
) -> Dict[str, Any]:
    """Auftrag annehmen. Wirft nie; die Antwort sagt, was passiert.

    zustand: wartend | laeuft | fertig | aus | voll | ausgelastet
    """
    if not AKTIV or _queue is None or not _arbeiter:
        return {"zustand": "aus"}

    jetzt = time.time()
    j = _jobs.get(site_id)

    if j and j["zustand"] in (WARTEND, LAEUFT):
        # Läuft oder wartet schon: nicht doppelt. Wer jetzt Anwendung will,
        # bekommt sie auf demselben Auftrag.
        if anwenden_ja:
            j["anwenden"] = True
        if html_keys is not None:
            j["html_keys"] = list(html_keys)
        if prio < j["prio"] and j["zustand"] == WARTEND:
            j["prio"] = prio
            j["seq"] = next(_zaehler)
            try:
                _queue.put_nowait((prio, j["seq"], j))
            except asyncio.QueueFull:
                pass  # bleibt an alter Stelle
        return {"zustand": j["zustand"], "bereits_im_auftrag": True,
                "geschaetzte_wartezeit_s": _wartezeit_s(wartend_anzahl())}

    if j and j["zustand"] == FEHLGESCHLAGEN and j.get("beendet") and jetzt - j["beendet"] < FEHLSCHLAG_SPERRE_S:
        # Eine Seite, die gerade gescheitert ist (blockt Bots, antwortet nicht), nicht
        # sofort wieder anfassen: hundert Klicks wären hundert verlorene Browser.
        return {"zustand": FEHLGESCHLAGEN, "zwischengespeichert": True}

    if j and j["zustand"] == FERTIG and j.get("beendet") and jetzt - j["beendet"] < WIEDERHOLSPERRE_S:
        # Frisches Ergebnis. Fehlt nur noch die Anwendung, ohne neuen Browser nachholen.
        if anwenden_ja and not j.get("angewendet") and j.get("bewertung") and pool is not None:
            try:
                zusatz = await anwenden(pool, site_id, j["bewertung"]["neu"])
                j["angewendet"] = True
                j["hinzugefuegt"] = zusatz
            except Exception as e:
                logger.warning(f"Pruefstufe: Nachtraegliche Anwendung fuer {site_id} fehlgeschlagen: {e}")
        return {"zustand": FERTIG, "zwischengespeichert": True}

    if _queue.full() or (prio == PRIO_ANONYM and _queue.qsize() >= SCHLANGE_MAX * 3 // 4):
        logger.warning(f"Pruefstufe: Schlange voll ({_queue.qsize()}/{SCHLANGE_MAX}), {site_id} nicht angenommen")
        return {"zustand": "voll"}

    job = {
        "site_id": site_id, "url": url, "pool": pool, "html_keys": list(html_keys or []),
        "anwenden": bool(anwenden_ja), "prio": prio, "quelle": quelle, "zustand": WARTEND,
        "gestellt": jetzt, "angewendet": False, "hinzugefuegt": [], "seq": next(_zaehler),
    }
    _jobs[site_id] = job
    _speicher_aufraeumen()
    try:
        _queue.put_nowait((prio, job["seq"], job))
    except asyncio.QueueFull:
        _jobs.pop(site_id, None)
        return {"zustand": "voll"}
    position = _queue.qsize()
    return {"zustand": WARTEND, "position": position, "geschaetzte_wartezeit_s": _wartezeit_s(position)}


async def _browser_lauf(url: str, katalog: List[dict]):
    from compliance_engine.deep_cookie_scanner import DeepCookieScanner
    return await DeepCookieScanner(0, url, catalog=katalog).scan()


def _browser_semaphor():
    """Der Browser-Semaphor des Backends. Zur Laufzeit lesen, nicht binden."""
    from compliance_engine import browser_renderer
    return browser_renderer._browser_semaphore


async def _eine_runde(job: Dict[str, Any]) -> None:
    """Ein Auftrag von Anfang bis Ende. Wirft nur CancelledError."""
    site_id = job["site_id"]
    job["zustand"] = LAEUFT
    job["gestartet"] = time.time()
    try:
        pool = job.get("pool") or db_pool
        if pool is None:
            raise RuntimeError("keine Datenbankverbindung")
        katalog, index = await _katalog_laden(pool)

        async with _browser_semaphor():
            ergebnis = await asyncio.wait_for(_browser_lauf(job["url"], katalog), timeout=JOB_ZEIT_S)

        if getattr(ergebnis, "error", None):
            raise RuntimeError(f"Browser-Scan: {ergebnis.error}")

        bekannt = await _bestehende_dienste(pool, site_id)
        if bekannt is None:
            bekannt = list(job.get("html_keys") or [])
        else:
            bekannt = sorted(set(bekannt) | set(job.get("html_keys") or []))

        bew = bewerte(
            [{"url": r.url} for r in ergebnis.requests],
            [{"name": c.name} for c in ergebnis.cookies],
            job["url"], index, bekannt,
        )
        job["bewertung"] = bew

        if job.get("anwenden") and bew["neu"]:
            zusatz = await anwenden(pool, site_id, bew["neu"])
            job["hinzugefuegt"] = zusatz
            job["angewendet"] = True
        elif job.get("anwenden"):
            job["angewendet"] = True

        job["zustand"] = FERTIG
        if bew["neu"] or bew["mehrdeutig"] or bew["unbekannte_fremdhosts"]:
            logger.info(
                f"[Pruefstufe] {site_id}: neu={bew['neu']} angewendet={job['hinzugefuegt']} "
                f"mehrdeutig={list(bew['mehrdeutig'])[:5]} unbekannt={list(bew['unbekannte_fremdhosts'])[:5]}"
            )
        if job.get("quelle") == "woche" and bew["neu"]:
            logger.warning(f"[Pruefstufe] ABWEICHUNG {site_id}: Browser sieht {bew['neu']}, Banner kennt sie nicht")
    except asyncio.CancelledError:
        job["zustand"] = FEHLGESCHLAGEN
        job["fehler"] = "Dienst wurde neu gestartet."
        raise
    except asyncio.TimeoutError:
        job["zustand"] = FEHLGESCHLAGEN
        job["fehler"] = f"Zeitbudget von {JOB_ZEIT_S} s ueberschritten."
        logger.warning(f"[Pruefstufe] {site_id}: Zeitbudget ueberschritten")
    except Exception as e:
        job["zustand"] = FEHLGESCHLAGEN
        job["fehler"] = "Die Pruefung im Browser ist fehlgeschlagen."
        logger.warning(f"[Pruefstufe] {site_id} fehlgeschlagen: {e}")
    finally:
        job["beendet"] = time.time()
        job["dauer_s"] = round(job["beendet"] - job["gestartet"], 1)
        if job["zustand"] == FERTIG:
            _dauern.append(job["dauer_s"])
        job["pool"] = None  # nichts Unnötiges festhalten
        await _spiegeln(job)


async def _schleife(nummer: int) -> None:
    logger.info(f"Pruefstufe-Arbeiter {nummer} bereit")
    while True:
        prio, seq, job = await _queue.get()
        try:
            # Veraltete Einträge (Priorität angehoben, neuer Eintrag steht schon) überspringen.
            if job["seq"] != seq or job["zustand"] != WARTEND:
                continue
            await _eine_runde(job)
        except asyncio.CancelledError:
            raise
        except Exception as e:  # darf den Arbeiter nie beenden
            logger.error(f"Pruefstufe-Arbeiter {nummer}: unerwarteter Fehler: {e}", exc_info=True)
        finally:
            _queue.task_done()


async def _woche_schleife() -> None:
    """Prüft die aktiven Seiten einmal pro Woche, leise und nur zur Beobachtung."""
    await asyncio.sleep(600)
    while True:
        try:
            await _woche_runde()
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.warning(f"Pruefstufe-Wochenlauf: {e}")
        await asyncio.sleep(600)


async def _woche_runde() -> None:
    pool = db_pool
    r = await _redis()
    # Ohne Redis wüssten wir nicht, was schon dran war: lieber gar nicht scannen.
    if pool is None or r is None or _queue is None:
        return
    jetzt = time.time()
    while _woche_starts and jetzt - _woche_starts[0] > 3600:
        _woche_starts.popleft()
    frei = WOCHE_PRO_STUNDE - len(_woche_starts)
    if frei <= 0 or _queue.qsize() >= ARBEITER_ANZAHL:
        return  # Nutzer zuerst
    rows = await pool.fetch(
        "SELECT site_id, last_scan_url FROM cookie_banner_configs "
        "WHERE is_active = true AND last_scan_url IS NOT NULL AND last_scan_url <> '' ORDER BY site_id"
    )
    for row in rows:
        if frei <= 0:
            break
        sid = row["site_id"]
        j = _jobs.get(sid)
        if j and j["zustand"] in (WARTEND, LAEUFT):
            continue
        try:
            zuletzt = await r.get(f"cookie:pruefung:zuletzt:{sid}")
        except Exception:
            return
        if zuletzt and jetzt - float(zuletzt) < WOCHE_ABSTAND_S:
            continue
        antwort = await einreihen(sid, row["last_scan_url"], pool=pool, anwenden_ja=False,
                                  prio=PRIO_WOCHE, quelle="woche")
        if antwort.get("zustand") == WARTEND:
            _woche_starts.append(jetzt)
            frei -= 1


async def starte() -> None:
    """Schlange und Arbeiter hochfahren. Mehrfacher Aufruf ist harmlos."""
    global _queue, _woche_task
    if not AKTIV or _arbeiter:
        return
    _queue = asyncio.PriorityQueue(maxsize=SCHLANGE_MAX)
    for i in range(ARBEITER_ANZAHL):
        _arbeiter.append(asyncio.create_task(_schleife(i + 1)))
    if WOCHE_AKTIV:
        _woche_task = asyncio.create_task(_woche_schleife())
    logger.info(f"{ARBEITER_ANZAHL} Pruefstufe-Arbeiter gestartet, Schlange max {SCHLANGE_MAX}, "
                f"Wochenlauf {'an' if WOCHE_AKTIV else 'aus'}")


async def beende() -> None:
    """Arbeiter anhalten, offene Aufträge ehrlich als nicht gelaufen ablegen."""
    global _queue, _woche_task
    tasks = list(_arbeiter) + ([_woche_task] if _woche_task else [])
    for t in tasks:
        t.cancel()
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)
    _arbeiter.clear()
    _woche_task = None
    for j in _jobs.values():
        if j["zustand"] in (WARTEND, LAEUFT):
            j["zustand"] = FEHLGESCHLAGEN
            j["fehler"] = "Dienst wurde neu gestartet."
    _queue = None
