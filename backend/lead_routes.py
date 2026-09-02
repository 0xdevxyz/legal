"""
Lead Collection API for GDPR-Compliant Lead Generation
Handles lead collection, email verification, and statistics
Also provides Early-Access Waitlist endpoints with Double-Opt-In.
"""

from fastapi import APIRouter, HTTPException, Request, BackgroundTasks, Depends
from fastapi.responses import RedirectResponse, Response
from pydantic import BaseModel, EmailStr, validator
from typing import Optional, Dict, Any
import logging
import secrets
import hashlib
import hmac
import os
import re
import httpx
from dependencies import require_admin, get_client_ip
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from database_service import db_service
from email_service import email_service

_rate_limit_store: Dict[str, list] = defaultdict(list)
_RATE_LIMIT_MAX = 3
_RATE_LIMIT_WINDOW_MINUTES = 10

# Zeitfalle: schneller ausgefüllt als _MIN_FILL_SECONDS ist kein Mensch,
# älter als _MAX_FORM_AGE_SECONDS ist ein abgestandenes Formular.
_MIN_FILL_SECONDS = 4
_MAX_FORM_AGE_SECONDS = 6 * 3600

# Cloudflare Turnstile. Nicht gesetzt = Prüfung aus; Honeypot, Zeitfalle und
# Rate-Limit greifen unabhängig davon.
TURNSTILE_SECRET = os.getenv("TURNSTILE_SECRET", "")
TURNSTILE_VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"

# Early-Access-Kontingent. "Nur 100 Plaetze" ist eine Werbeaussage und muss
# gedeckt sein: der Zaehler unten liest echte Zeilen, keine Schaetzung.
EARLY_ACCESS_PLAETZE = int(os.getenv("EARLY_ACCESS_PLAETZE", "100"))

# Fassung des Angebots, das auf der Kampagnenseite steht. Wird je Anmeldung
# mitgeschrieben, damit spaeter belegbar ist, was wem zugesagt wurde.
EARLY_ACCESS_ANGEBOT = os.getenv("EARLY_ACCESS_ANGEBOT", "ea100-35eur-12m")

logger = logging.getLogger(__name__)

lead_router = APIRouter(prefix="/api/leads", tags=["leads"])

# ---------------------------------------------------------------------------
# Waitlist models
# ---------------------------------------------------------------------------

class WaitlistJoinRequest(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    phone: Optional[str] = None
    consent: bool
    website: Optional[str] = None          # Honeypot – bleibt bei Menschen leer
    source: Optional[str] = "early-access"
    form_ts: Optional[int] = None          # Zeitfalle, ms seit Epoch (clientseitig gesetzt)
    turnstile_token: Optional[str] = None  # cf-turnstile-response

    # Herkunft. Ohne diese Felder landet jede Anmeldung im selben Topf und eine
    # bezahlte Kampagne laesst sich nicht auswerten.
    campaign: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    utm_content: Optional[str] = None
    utm_term: Optional[str] = None
    landing_path: Optional[str] = None

    @validator("name")
    def validate_name(cls, v):
        if v is not None:
            v = v.strip()[:120]
        return v or None

    @validator("phone")
    def validate_phone(cls, v):
        if v is not None:
            v = v.strip()
            if v and not re.match(r'^[\+\d\s\-\(\)]{1,40}$', v):
                raise ValueError("Ungültiges Telefon-Format")
            return v[:40] if v else None
        return None

    @validator("consent")
    def validate_consent(cls, v):
        if not v:
            raise ValueError("Einwilligung ist erforderlich")
        return v

    @validator("source")
    def validate_source(cls, v):
        """Saeubert die Quelle, statt sie zu verwerfen.

        Vorher stand hier eine Allowlist aus drei Werten und alles andere fiel
        still auf "early-access" zurueck. Fuer eine Anzeigenkampagne ist das
        genau das falsche Verhalten: die Information, welche Seite den Lead
        gebracht hat, ging dabei verloren. Statt einer Allowlist begrenzt jetzt
        ein Zeichensatz, was in die Spalte darf - das haelt Fremdeingaben
        genauso zuverlaessig heraus, ohne echte Quellen wegzuwerfen.
        """
        return _sauberer_kurztext(v, 40) or "early-access"

    @validator("campaign", "utm_source", "utm_medium", "utm_campaign",
               "utm_content", "utm_term")
    def validate_herkunft(cls, v):
        return _sauberer_kurztext(v, 120)

    @validator("landing_path")
    def validate_landing_path(cls, v):
        """Nur ein Pfad auf der eigenen Seite.

        Der Wert steuert nach der Bestaetigung ein Redirect. Ohne diese Pruefung
        waere das eine offene Weiterleitung: ein praeparierter Link koennte den
        Bestaetigungsklick auf eine fremde Domain schicken. Deshalb muss der
        Wert mit genau einem Schraegstrich beginnen - "https://boese.example"
        faellt damit raus, und der Lookahead sperrt zusaetzlich "//boese":
        zwei Schraegstriche waeren eine protokollrelative URL, die der Browser
        als fremde Domain aufloest, obwohl der Wert wie ein Pfad aussieht.
        """
        if not v:
            return None
        v = v.strip()[:200]
        if not re.match(r'^/(?!/)[A-Za-z0-9/_\-]*$', v):
            return None
        return v


class WaitlistJoinResponse(BaseModel):
    status: str
    message: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sauberer_kurztext(v, max_len: int):
    """Laesst durch, was in eine Herkunftsspalte gehoert, und wirft den Rest weg.

    Google Ads und Meta haengen ihre Parameter ungefiltert an die Ziel-URL, und
    die landen von dort in der Datenbank. Erlaubt sind deshalb nur Zeichen, die
    in einer Kampagnenkennung vorkommen; alles andere - Anfuehrungszeichen,
    spitze Klammern, Zeilenumbrueche - faellt heraus, bevor es gespeichert und
    spaeter im Admin-Bereich wieder angezeigt wird.

    Rueckgabe None statt Leerstring: die Spalten sind nullable, und "nicht
    angegeben" soll sich in der Auswertung von "leer uebermittelt" unterscheiden.
    """
    if v is None:
        return None
    v = re.sub(r'[^A-Za-z0-9._\-]', '', str(v).strip())[:max_len]
    return v or None


def _hash_ip(ip: str) -> str:
    salt = os.getenv("SECRET_SALT", "complyo-salt-2026")
    return hashlib.sha256(f"{ip}{salt}".encode()).hexdigest()


def unsubscribe_token_for(email: str) -> str:
    """Leitet den Abmelde-Token deterministisch aus E-Mail + JWT_SECRET ab (HMAC-SHA256).

    Bewusst kein DB-Feld: der Token muss ohne Migration in bereits versandte
    E-Mails eingebettet werden können. Deterministisch heisst, derselbe
    Abmeldelink bleibt dauerhaft gültig — genau das erwartet ein Empfänger,
    der eine alte Mail wieder aufmacht.
    """
    secret = os.getenv("JWT_SECRET") or ""
    if not secret:
        # Ohne Secret gibt es keinen prüfbaren Token — dann darf auch nichts
        # abgemeldet werden (fail closed statt fail open).
        raise RuntimeError("JWT_SECRET fehlt — Unsubscribe-Token nicht ableitbar")
    return hmac.new(
        secret.encode(),
        f"unsubscribe:{email.strip().lower()}".encode(),
        hashlib.sha256,
    ).hexdigest()


def _verify_unsubscribe_token(email: str, token: Optional[str]) -> bool:
    """Konstantzeit-Vergleich; jeder Fehlerfall bedeutet 'ungültig'."""
    if not token:
        return False
    try:
        erwartet = unsubscribe_token_for(email)
    except RuntimeError as e:
        logger.error(f"Unsubscribe-Token nicht prüfbar: {e}")
        return False
    return hmac.compare_digest(erwartet, token)


def _fill_time_plausible(form_ts: Optional[int]) -> bool:
    """Prüft, wie lange das Formular offen war.

    Ein Bot, der direkt auf den Endpoint POSTet, schickt gar kein form_ts —
    das allein ist schon ein Ausschlusskriterium.
    """
    if not form_ts:
        return False
    elapsed = datetime.now(timezone.utc).timestamp() - (form_ts / 1000)
    return _MIN_FILL_SECONDS <= elapsed <= _MAX_FORM_AGE_SECONDS


async def _verify_turnstile(token: Optional[str], remote_ip: str) -> bool:
    """Fragt Cloudflare, ob das Turnstile-Token echt ist."""
    if not TURNSTILE_SECRET:
        return True          # nicht konfiguriert
    if not token:
        return False
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.post(
                TURNSTILE_VERIFY_URL,
                data={
                    "secret": TURNSTILE_SECRET,
                    "response": token,
                    "remoteip": remote_ip,
                },
            )
        return bool(resp.json().get("success"))
    except Exception as e:
        # Cloudflare nicht erreichbar: lieber durchlassen als echte Anmeldungen
        # verlieren. Honeypot, Zeitfalle und Rate-Limit greifen weiterhin.
        logger.warning(f"Turnstile nicht erreichbar, Prüfung übersprungen: {e}")
        return True


def _check_rate_limit(ip_hash: str) -> bool:
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(minutes=_RATE_LIMIT_WINDOW_MINUTES)
    _rate_limit_store[ip_hash] = [
        ts for ts in _rate_limit_store[ip_hash] if ts > window_start
    ]
    if len(_rate_limit_store[ip_hash]) >= _RATE_LIMIT_MAX:
        return False
    _rate_limit_store[ip_hash].append(now)
    return True


# ---------------------------------------------------------------------------
# Waitlist endpoints
# ---------------------------------------------------------------------------

@lead_router.post("/waitlist", response_model=WaitlistJoinResponse)
async def join_waitlist(
    payload: WaitlistJoinRequest,
    http_request: Request,
    background_tasks: BackgroundTasks,
):
    """
    Early-Access Waitlist Anmeldung (DSGVO-konform, Double-Opt-In)
    """
    # Honeypot. 204 statt Fehler: der Bot soll nicht lernen, was ihn verrät.
    if payload.website:
        return Response(status_code=204)

    # get_client_ip statt request.client.host: hinter nginx ist letzteres immer
    # die Gateway-IP. Rate-Limit und ip_hash haetten dann fuer ALLE Besucher
    # denselben Wert — nach drei Anmeldungen in zehn Minuten waere das Formular
    # fuer jeden weiteren Besucher mit 429 dicht. Bei bezahltem Traffic faellt
    # das erst auf, wenn die Anzeigen schon laufen. Genau dieser Fehler hat am
    # 12.08.2026 den Landing-Scanner lahmgelegt; der Helfer kennt seither
    # TRUSTED_PROXIES und meldet eine unbekannte Proxy-IP von sich aus.
    client_ip = get_client_ip(http_request)
    ip_hash = _hash_ip(client_ip)
    user_agent = http_request.headers.get("user-agent", "")[:500]

    # Zeitfalle – ebenfalls stillschweigend
    if not _fill_time_plausible(payload.form_ts):
        logger.info("Waitlist: Zeitfalle ausgelöst")
        return Response(status_code=204)

    # Turnstile
    if not await _verify_turnstile(payload.turnstile_token, client_ip):
        logger.info("Waitlist: Turnstile fehlgeschlagen")
        return Response(status_code=204)

    if not _check_rate_limit(ip_hash):
        raise HTTPException(
            status_code=429,
            detail="Zu viele Anfragen. Bitte versuchen Sie es später erneut.",
        )

    confirm_token = secrets.token_urlsafe(32)
    token_expires = datetime.now(timezone.utc) + timedelta(days=7)
    now = datetime.now(timezone.utc)

    try:
        async with db_service.get_connection() as conn:
            existing = await conn.fetchrow(
                "SELECT id, confirmed_at FROM waitlist_leads WHERE email = $1",
                payload.email.lower(),
            )

        if existing:
            logger.info(f"Waitlist duplicate for {payload.email}")
            return WaitlistJoinResponse(
                status="already_registered",
                message="Diese E-Mail steht bereits auf der Warteliste.",
            )

        # angebot kommt bewusst NICHT aus dem Request: der Preis, der zugesagt
        # wird, ist eine Servereigenschaft. Kaeme er vom Client, koennte sich
        # jeder ein eigenes Angebot in die Datenbank schreiben.
        angebot = EARLY_ACCESS_ANGEBOT if payload.campaign else None

        async with db_service.get_connection() as conn:
            await conn.execute(
                """
                INSERT INTO waitlist_leads
                    (email, name, phone, consent_given_at, confirm_token,
                     confirm_token_expires_at, source, ip_hash, user_agent,
                     created_at, campaign, utm_source, utm_medium, utm_campaign,
                     utm_content, utm_term, landing_path, angebot)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                        $11, $12, $13, $14, $15, $16, $17, $18)
                """,
                payload.email.lower(),
                payload.name,
                payload.phone,
                now,
                confirm_token,
                token_expires,
                payload.source or "early-access",
                ip_hash,
                user_agent,
                now,
                payload.campaign,
                payload.utm_source,
                payload.utm_medium,
                payload.utm_campaign,
                payload.utm_content,
                payload.utm_term,
                payload.landing_path,
                angebot,
            )

        frontend_url = os.getenv("FRONTEND_URL", "https://complyo.de")
        confirm_url = f"{frontend_url}/api/leads/waitlist/confirm?token={confirm_token}"

        background_tasks.add_task(
            email_service.send_waitlist_confirmation,
            payload.email.lower(),
            payload.name or "",
            confirm_url,
        )

        # Herkunft in einer Zeile, damit die Meldung ohne Datenbankblick sagt,
        # welche Anzeige den Eintrag gebracht hat.
        herkunft = " / ".join(
            t for t in (
                payload.campaign,
                payload.utm_source,
                payload.utm_medium,
                payload.utm_campaign,
                payload.utm_content,
            ) if t
        )

        background_tasks.add_task(
            email_service.send_waitlist_admin_notification,
            payload.email.lower(),
            payload.name or "",
            payload.phone or "",
            payload.source or "early-access",
            herkunft,
            angebot or "",
        )

        logger.info(f"Waitlist registration pending confirmation: {payload.email}")
        return WaitlistJoinResponse(
            status="pending_confirmation",
            message="Danke! Wir haben dir eine Bestätigungsmail geschickt.",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Waitlist join error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Fehler beim Speichern. Bitte versuchen Sie es erneut.",
        )


@lead_router.get("/waitlist/plaetze")
async def waitlist_plaetze():
    """Wie viele Early-Access-Plaetze noch frei sind.

    Bewusst ohne Auth, im Unterschied zu /api/leads/stats: dort standen
    Geschaeftszahlen offen im Netz, hier geht genau eine Zahl heraus, die
    ohnehin gross auf der Werbeseite steht. Sie muss oeffentlich sein, weil die
    Seite sie ungeloggt anzeigen soll - und sie muss aus der Datenbank kommen,
    weil "nur noch X Plaetze" sonst eine unbelegte Werbeaussage waere.

    Gezaehlt werden vergebene Plaetze, nicht Anmeldungen: die Gesamtzahl der
    Leads ist eine Geschaeftszahl und bleibt drin.
    """
    try:
        async with db_service.get_connection() as conn:
            vergeben = int(
                await conn.fetchval(
                    "SELECT COUNT(*) FROM waitlist_leads WHERE platz_nr IS NOT NULL"
                )
                or 0
            )
    except Exception as e:
        # Der Zaehler darf die Seite nicht mitreissen. Faellt er aus, zeigt das
        # Frontend das Angebot ohne Zahl an, statt gar nichts anzuzeigen.
        logger.error(f"Waitlist-Plaetze nicht lesbar: {e}", exc_info=True)
        raise HTTPException(status_code=503, detail="Zaehler nicht verfuegbar")

    return {
        "gesamt": EARLY_ACCESS_PLAETZE,
        "vergeben": vergeben,
        "frei": max(0, EARLY_ACCESS_PLAETZE - vergeben),
    }


@lead_router.get("/waitlist/confirm")
async def confirm_waitlist(token: str, background_tasks: BackgroundTasks):
    """
    Double-Opt-In Bestätigung via E-Mail-Link
    """
    frontend_url = os.getenv("FRONTEND_URL", "https://complyo.de")
    try:
        async with db_service.get_connection() as conn:
            lead = await conn.fetchrow(
                """
                SELECT id, email, name, phone, source, confirm_token_expires_at,
                       confirmed_at, angebot, landing_path, platz_nr,
                       campaign, utm_source, utm_medium, utm_campaign, utm_content
                FROM waitlist_leads
                WHERE confirm_token = $1
                """,
                token,
            )

        if not lead:
            logger.warning(f"Waitlist confirm: unknown token {token[:8]}…")
            return RedirectResponse(url=f"{frontend_url}/?confirmed=0", status_code=302)

        # Zurueck auf die Seite, von der die Anmeldung kam. Vorher landete jeder
        # auf der Startseite - wer ueber eine Anzeige kam, sah nach dem Klick
        # etwas anderes als das, wofuer er sich angemeldet hatte. Der Pfad ist
        # beim Speichern gegen offene Weiterleitungen geprueft worden.
        ziel = lead["landing_path"] or "/"

        expires_at = lead["confirm_token_expires_at"]
        if expires_at and datetime.now(timezone.utc) > expires_at:
            logger.warning(f"Waitlist confirm: expired token {token[:8]}…")
            return RedirectResponse(url=f"{frontend_url}{ziel}?confirmed=0", status_code=302)

        # Platznummer erst hier, nicht schon bei der Anmeldung: ein Eintrag, der
        # nie bestaetigt wird, darf keinen der 100 Plaetze blockieren.
        # nextval ist race-frei, zwei gleichzeitige Bestaetigungen koennen also
        # nicht dieselbe Nummer ziehen. Wer ueber dem Kontingent liegt, bleibt
        # auf der Warteliste, bekommt aber keinen Platz - und damit auch nicht
        # den zugesagten Preis.
        platz_nr = None
        async with db_service.get_connection() as conn:
            if lead["angebot"]:
                gezogen = int(
                    await conn.fetchval("SELECT nextval('waitlist_platz_seq')") or 0
                )
                if 0 < gezogen <= EARLY_ACCESS_PLAETZE:
                    platz_nr = gezogen

            await conn.execute(
                """
                UPDATE waitlist_leads
                SET confirmed_at = $1, confirm_token = NULL,
                    confirm_token_expires_at = NULL,
                    platz_nr = COALESCE(platz_nr, $3)
                WHERE id = $2
                """,
                datetime.now(timezone.utc),
                lead["id"],
                platz_nr,
            )

        # Zweite Meldung an uns: erst der Klick im Bestaetigungslink macht aus
        # einer Formulareingabe einen Interessenten, den man anschreiben darf.
        # Ohne diese Mail saehe man nur Anmeldungen und wuesste nie, welche davon
        # bestaetigt wurden — genau die Zahl, an der sich das Interesse ablesen
        # laesst.
        herkunft = " / ".join(
            t for t in (
                lead["campaign"], lead["utm_source"], lead["utm_medium"],
                lead["utm_campaign"], lead["utm_content"],
            ) if t
        )
        background_tasks.add_task(
            email_service.send_waitlist_admin_notification,
            lead["email"],
            lead["name"] or "",
            lead["phone"] or "",
            lead["source"] or "",
            herkunft,
            lead["angebot"] or "",
            True,
            platz_nr,
        )

        logger.info(f"Waitlist confirmed for lead {lead['id']} (Platz {platz_nr})")
        ziel_url = f"{frontend_url}{ziel}?confirmed=1"
        if platz_nr:
            ziel_url += f"&platz={platz_nr}"
        return RedirectResponse(url=ziel_url, status_code=302)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Waitlist confirm error: {e}", exc_info=True)
        return RedirectResponse(url=f"{frontend_url}/?confirmed=0", status_code=302)


# TODO (future): GET /api/leads/waitlist — Admin-only CSV-Export der Warteliste


# ---------------------------------------------------------------------------
# Legacy lead endpoints (unchanged)
# ---------------------------------------------------------------------------

class LeadCollectionRequest(BaseModel):
    name: str
    email: EmailStr
    company: Optional[str] = None
    url: str
    analysis_data: Dict[str, Any]
    session_id: str
    language: Optional[str] = "de"

class LeadCollectionResponse(BaseModel):
    success: bool
    verified: bool
    requires_verification: bool
    message: str
    lead_id: Optional[str] = None

@lead_router.post("/collect", response_model=LeadCollectionResponse)
async def collect_lead(
    request: LeadCollectionRequest,
    http_request: Request,
    background_tasks: BackgroundTasks
):
    """
    Collect a new lead with GDPR consent and send verification email
    
    This endpoint:
    1. Validates the lead data
    2. Stores lead in database with GDPR compliance
    3. Sends double opt-in verification email (German law requirement)
    4. Returns success status
    """
    try:
        # Einwilligungsnachweis: hier muss die IP des Besuchers stehen, nicht die
        # des Gateways. Hinter nginx liefert request.client.host immer 172.22.0.x,
        # und ein Audit-Trail, in dem bei jedem Lead dieselbe interne Proxy-IP
        # steht, belegt gar nichts. get_client_ip wertet X-Forwarded-For nur aus,
        # wenn die Anfrage von einem Proxy aus TRUSTED_PROXIES kommt; dem blanken
        # Header zu glauben waere das andere Extrem, denn der Client setzt ihn selbst.
        client_ip = get_client_ip(http_request)
        user_agent = http_request.headers.get("user-agent", "unknown")
        
        # Validate required fields
        if not request.name.strip():
            raise HTTPException(status_code=400, detail="Name is required")
        
        if not request.email.strip():
            raise HTTPException(status_code=400, detail="Email is required")
        
        logger.info(f"Processing lead collection for {request.email}")
        
        # Check if lead already exists
        existing_lead = await db_service.get_lead_by_email(request.email)
        
        if existing_lead:
            if existing_lead.get('email_verified'):
                # Lead already verified - send report immediately
                logger.info(f"Lead {request.email} already verified, sending report")
                
                # Send report in background
                background_tasks.add_task(
                    email_service.send_compliance_report,
                    request.email,
                    request.name,
                    request.analysis_data,
                    {
                        'name': request.name,
                        'email': request.email,
                        'company': request.company or ''
                    }
                )
                
                return LeadCollectionResponse(
                    success=True,
                    verified=True,
                    requires_verification=False,
                    message=f"Report wird sofort an {request.email} gesendet!",
                    lead_id=existing_lead['id']
                )
            else:
                # Lead exists but not verified - resend verification
                logger.info(f"Lead {request.email} exists but not verified, resending verification")
                
                verification_token = existing_lead.get('verification_token')
                if verification_token:
                    background_tasks.add_task(
                        email_service.send_verification_email,
                        request.email,
                        request.name,
                        verification_token,
                        request.language
                    )
                
                return LeadCollectionResponse(
                    success=True,
                    verified=False,
                    requires_verification=True,
                    message=f"Bestätigungs-E-Mail wurde erneut an {request.email} gesendet",
                    lead_id=existing_lead['id']
                )
        
        # Create new lead with GDPR compliance
        lead_data = {
            'name': request.name.strip(),
            'email': request.email.strip().lower(),
            'company': request.company.strip() if request.company else None,
            'source': 'landing_page',
            'url_analyzed': request.url,
            'analysis_data': request.analysis_data,
            'session_id': request.session_id,
            'consent_ip_address': client_ip,
            'consent_user_agent': user_agent,
            'language': request.language
        }
        
        lead_id, verification_token = await db_service.create_lead(lead_data)
        
        logger.info(f"Created new lead {lead_id} for {request.email}")
        
        # Send verification email in background
        background_tasks.add_task(
            email_service.send_verification_email,
            request.email,
            request.name,
            verification_token,
            request.language
        )
        
        return LeadCollectionResponse(
            success=True,
            verified=False,
            requires_verification=True,
            message=f"Bestätigungs-E-Mail wurde an {request.email} gesendet. Bitte prüfen Sie Ihr Postfach.",
            lead_id=lead_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error collecting lead: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Fehler beim Speichern Ihrer Daten. Bitte versuchen Sie es erneut."
        )

@lead_router.get("/verify/{token}")
async def verify_email(
    token: str,
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Verify email address using verification token (Double Opt-In)
    
    After successful verification:
    1. Updates lead status to verified
    2. Sends compliance report PDF via email
    3. Returns success page
    """
    try:
        # Audit-Trail der Double-Opt-In-Bestaetigung, dieselbe Begruendung wie in
        # collect_lead: hinter nginx ist request.client.host die Gateway-IP.
        client_ip = get_client_ip(request)
        user_agent = request.headers.get("user-agent", "unknown")
        
        logger.info(f"Processing email verification for token: {token[:8]}...")
        
        # Get lead by verification token
        lead = await db_service.get_lead_by_verification_token(token)
        
        if not lead:
            raise HTTPException(
                status_code=404,
                detail="Ungültiger oder abgelaufener Verifizierungslink"
            )
        
        # Check if already verified
        if lead.get('email_verified'):
            return {
                "success": True,
                "message": "E-Mail bereits verifiziert. Report wurde bereits gesendet.",
                "already_verified": True
            }
        
        # Verify email
        success = await db_service.verify_email(token, client_ip, user_agent)
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail="Verifizierung fehlgeschlagen. Token möglicherweise abgelaufen."
            )
        
        logger.info(f"Email verified successfully for {lead['email']}")
        
        # Send compliance report in background
        background_tasks.add_task(
            email_service.send_compliance_report,
            lead['email'],
            lead['name'],
            lead.get('analysis_data', {}),
            {
                'name': lead['name'],
                'email': lead['email'],
                'company': lead.get('company', '')
            }
        )
        
        return {
            "success": True,
            "message": "E-Mail erfolgreich verifiziert! Ihr Compliance-Report wird in Kürze an Ihre E-Mail-Adresse gesendet.",
            "email": lead['email'],
            "report_sent": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying email: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Fehler bei der Verifizierung. Bitte kontaktieren Sie den Support."
        )

@lead_router.get("/stats")
async def get_lead_statistics(admin: dict = Depends(require_admin)):
    """
    Lead-Statistiken — Admin-only.

    Waren bis 2026-07-17 ohne jede Auth abrufbar ("public ... for transparency"):
    Gesamt-/Verified-/Converted-Zahlen sind Geschäftszahlen und gehören nicht
    an die Öffentlichkeit. Kein Aufrufer im Dashboard/Landing hängt daran.
    """
    try:
        stats = await db_service.get_lead_statistics()
        
        return {
            "success": True,
            "statistics": stats,
            "timestamp": datetime.now().isoformat(),
            "gdpr_compliant": True
        }
        
    except Exception as e:
        logger.error(f"Error getting lead statistics: {e}")
        # Return default stats on error
        return {
            "success": True,
            "statistics": {
                "total_leads": 0,
                "verified_leads": 0,
                "converted_leads": 0,
                "gdpr_compliant": True
            },
            "timestamp": datetime.now().isoformat()
        }

class UnsubscribeRequest(BaseModel):
    email: EmailStr
    token: Optional[str] = None


@lead_router.post("/unsubscribe")
async def unsubscribe_lead(request: UnsubscribeRequest):
    """
    Abmeldung von Marketing-Kommunikation (Art. 7 DSGVO).

    Bis 2026-07-17 genügte eine beliebige E-Mail-Adresse — jeder konnte jeden
    abmelden. Analog zu GET /verify/{token} ist jetzt ein Token Pflicht; er wird
    per HMAC aus E-Mail + JWT_SECRET abgeleitet (siehe unsubscribe_token_for)
    und gehört in den Abmeldelink der versendeten Mails.

    Die Signatur bleibt {email, token} — Aufrufer ohne gültigen Token: 403.
    """
    email = request.email

    if not _verify_unsubscribe_token(email, request.token):
        logger.warning(f"Unsubscribe mit ungültigem/fehlendem Token für {email}")
        raise HTTPException(
            status_code=403,
            detail="Ungültiger oder fehlender Abmelde-Token.",
        )

    try:
        success = await db_service.update_lead_status_by_email(email, 'unsubscribed')
        
        if success:
            logger.info(f"Lead {email} unsubscribed from communications")
            return {
                "success": True,
                "message": "Sie wurden erfolgreich von weiteren E-Mails abgemeldet."
            }
        else:
            raise HTTPException(
                status_code=404,
                detail="E-Mail-Adresse nicht gefunden"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unsubscribing lead: {e}")
        raise HTTPException(
            status_code=500,
            detail="Fehler beim Abmelden. Bitte versuchen Sie es erneut."
        )

