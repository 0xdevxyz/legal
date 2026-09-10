"""
Der Kern der Anmeldung: Passwoerter, Token, Sitzungen.

AuthService bekommt den Datenbank-Pool und optional Redis. Ohne Redis
funktioniert alles, nur die Sperrliste faellt weg, siehe unten.

Zwei Tokenarten mit verschiedener Lebensdauer:
- Access-Token, kurzlebig, signiert (HS256) und mit audience und issuer
  geprueft. Traegt eine `jti`, damit ein einzelnes Token widerrufbar bleibt.
- Refresh-Token, langlebig, liegt in `user_sessions` mit Geraet und IP, damit
  der Nutzer einzelne Sitzungen beenden kann.

Die `jti`-Sperrliste liegt in Redis (`_blacklist_jti`, `_is_jti_blacklisted`).
Fehlt Redis, laesst sich ein bereits ausgegebener Access-Token bis zu seinem
Ablauf nicht mehr zurueckziehen; `revoke_all_sessions` wirkt dann erst mit der
naechsten Erneuerung.

`cleanup_expired_sessions` raeumt abgelaufene Refresh-Token weg und will
regelmaessig aufgerufen werden.
"""


import os
import bcrypt as _bcrypt
import jwt
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict
from uuid import uuid4
import asyncpg
import logging
from fastapi import HTTPException

logger = logging.getLogger(__name__)

_MAX_ATTEMPTS = int(os.getenv("LOGIN_MAX_ATTEMPTS", "5"))
_LOCKOUT_SECONDS = int(os.getenv("LOGIN_LOCKOUT_SECONDS", "900"))  # 15 min

def _utcnow():
    return datetime.now(timezone.utc)


# Module, die es gibt, und die Tarife, die per Definition ALLE enthalten.
# Doppelt gefuehrt zu payment_routes/stripe_routes — dort wird beim Kauf
# geschrieben, hier beim Lesen geprueft.
_ALLE_MODULE = ['cookie', 'accessibility', 'legal_texts', 'monitoring']
_VOLLZUGANG_TARIFE = ('pro', 'agency', 'expert', 'update')


def _module_zugang(plan_type: str, gebuchte: list) -> list:
    """
    Welche Module ein Konto benutzen darf.

    Bisher kam die Antwort ausschliesslich aus `user_modules`. Der Tarif war
    dabei die eigentliche Wahrheit — `_resolve_modules()` im Kaufweg gibt fuer
    pro/agency/expert/update grundsaetzlich ALLE Module zurueck. Die Zeilen in
    `user_modules` sind nur die Buchhaltung dazu.

    Faellt diese Buchhaltung aus, sieht ein zahlender Kunde "Modul nicht
    aktiviert" — obwohl sein Tarif es einschliesst. Wege dorthin gibt es
    mehrere: ein verlorener Stripe-Webhook, eine Tarifaenderung von Hand, eine
    Migration, ein eingespieltes Backup. Genau dieser Fall ist im Kaufweg schon
    einmal aufgetreten.

    Deshalb hier abgeleitet statt nachgeschlagen: wer den Tarif hat, hat die
    Module. Zusaetzlich gebuchte Einzelmodule kommen dazu — ein Konto verliert
    durch diese Regel nie etwas.
    """
    zugang = list(gebuchte or [])
    if (plan_type or '').lower() in _VOLLZUGANG_TARIFE:
        for m in _ALLE_MODULE:
            if m not in zugang:
                zugang.append(m)
    return zugang


class AuthService:
    def __init__(self, db_pool: asyncpg.Pool, redis_client=None):
        self.db_pool = db_pool
        self.redis = redis_client

        self.jwt_secret = os.getenv("JWT_SECRET")
        if not self.jwt_secret:
            raise RuntimeError("❌ CRITICAL: JWT_SECRET environment variable is required!")
        self.jwt_issuer = os.getenv("FRONTEND_URL", "https://complyo.de")
        self.jwt_audience = "complyo-api"
        self.access_token_expire = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
        self.refresh_token_expire = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "30")) * 24 * 60
    
    async def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email address"""
        async with self.db_pool.acquire() as conn:
            user = await conn.fetchrow(
                "SELECT id, email, full_name, company, password_hash, is_active, is_verified, created_at FROM users WHERE email = $1",
                email
            )
            return dict(user) if user else None
    
    async def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Get user by ID including plan_type and active_modules"""
        async with self.db_pool.acquire() as conn:
            user = await conn.fetchrow(
                "SELECT id, email, full_name, company, is_active, is_verified, created_at, onboarding_completed, role FROM users WHERE id = $1",
                user_id
            )
            if not user:
                return None

            result = dict(user)

            # plan_type + plan_limits aus user_limits
            limits = await conn.fetchrow(
                "SELECT plan_type, websites_max, exports_max FROM user_limits WHERE user_id = $1",
                user_id
            )
            if limits:
                result['plan_type'] = limits['plan_type']
                result['plan_limits'] = {
                    'websites_max': limits['websites_max'],
                    'exports_max':  limits['exports_max'],
                }
            else:
                result['plan_type'] = 'free'
                result['plan_limits'] = {'websites_max': 1, 'exports_max': 10}

            # aktive Module
            modules = await conn.fetch(
                """
                SELECT module_id FROM user_modules
                WHERE user_id = $1 AND status = 'active'
                  AND (expires_at IS NULL OR expires_at > NOW())
                """,
                user_id
            )
            result['active_modules'] = _module_zugang(
                result['plan_type'], [r['module_id'] for r in modules])

            return result
    
    async def register_user(self, email: str, password: str, full_name: str, company: str = None) -> Dict:
        """Register a new user"""
        try:
            # Hash password with bcrypt
            password_hash = _bcrypt.hashpw(password.encode(), _bcrypt.gensalt()).decode()
            
            # Insert user
            async with self.db_pool.acquire() as conn:
                user = await conn.fetchrow(
                    """
                    INSERT INTO users (email, password_hash, full_name, company)
                    VALUES ($1, $2, $3, $4)
                    RETURNING id, email, full_name, company, created_at
                    """,
                    email, password_hash, full_name, company
                )

            logger.info(f"User registered: {email}")
            return dict(user)
        except asyncpg.UniqueViolationError:
            logger.warning(f"Registration failed: Email already exists {email}")
            raise ValueError("Email already registered")
        except Exception as e:
            logger.error(f"Registration error: {e}")
            raise
    
    async def authenticate(self, email: str, password: str) -> Optional[Dict]:
        """Authenticate user with email and password, enforcing brute-force lockout."""
        lockout_key = f"login_fail:{email.lower()}"

        if self.redis:
            try:
                attempts = await self.redis.get(lockout_key)
                if attempts and int(attempts) >= _MAX_ATTEMPTS:
                    ttl = await self.redis.ttl(lockout_key)
                    logger.warning(f"Account locked: {email} ({attempts} attempts, {ttl}s remaining)")
                    raise HTTPException(
                        status_code=429,
                        detail=f"Account temporarily locked due to too many failed attempts. Try again in {ttl} seconds."
                    )
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Redis lockout check failed: {e}")

        async with self.db_pool.acquire() as conn:
            user = await conn.fetchrow(
                "SELECT id, email, full_name, company, password_hash, is_active, is_verified, created_at FROM users WHERE email = $1 AND is_active = TRUE",
                email
            )

        if not user:
            if self.redis:
                try:
                    await self.redis.incr(lockout_key)
                    await self.redis.expire(lockout_key, _LOCKOUT_SECONDS)
                except Exception:
                    pass
            logger.warning(f"Authentication failed: User not found {email}")
            return None

        if not _bcrypt.checkpw(password.encode(), user['password_hash'].encode()):
            if self.redis:
                try:
                    await self.redis.incr(lockout_key)
                    await self.redis.expire(lockout_key, _LOCKOUT_SECONDS)
                except Exception:
                    pass
            logger.warning(f"Authentication failed: Invalid password for {email}")
            return None

        if self.redis:
            try:
                await self.redis.delete(lockout_key)
            except Exception:
                pass

        logger.info(f"User authenticated: {email}")
        user_dict = dict(user)
        del user_dict['password_hash']
        return user_dict
    
    def create_access_token(self, user_id) -> str:
        """Create JWT access token with jti, iat, nbf claims"""
        now = _utcnow()
        now_ts = int(now.timestamp())
        expire_seconds = self.access_token_expire * 60
        jti = str(uuid4())
        payload = {
            "id": str(user_id),
            "user_id": str(user_id),
            "jti": jti,
            "iat": now_ts,
            "nbf": now_ts - 30,
            "exp": now + timedelta(minutes=self.access_token_expire),
            "iss": self.jwt_issuer,
            "aud": self.jwt_audience,
            "type": "access"
        }
        token = jwt.encode(payload, self.jwt_secret, algorithm="HS256")

        if self.redis:
            import asyncio
            uid = int(user_id)
            set_key = f"jwt:user_jtis:{uid}"
            max_ttl = expire_seconds + 60
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.ensure_future(self._register_jti_in_set(set_key, jti, max_ttl))
            except Exception:
                pass

        return token

    async def _register_jti_in_set(self, set_key: str, jti: str, ttl: int):
        """Add jti to user's active-JTI set in Redis (best-effort)."""
        if not self.redis:
            return
        try:
            await self.redis.sadd(set_key, jti)
            await self.redis.expire(set_key, ttl)
        except Exception as e:
            logger.warning(f"Redis SADD jti failed: {e}")

    async def _blacklist_jti(self, jti: str, ttl_seconds: int):
        """Put jti on the Redis blacklist with TTL = remaining token lifetime."""
        if not self.redis:
            return
        try:
            await self.redis.setex(f"jwt:blacklist:{jti}", ttl_seconds, "1")
        except Exception as e:
            logger.warning(f"Redis blacklist jti failed: {e}")

    async def _is_jti_blacklisted(self, jti: str) -> bool:
        """Return True if jti is on the Redis blacklist."""
        if not self.redis:
            return False
        try:
            result = await self.redis.get(f"jwt:blacklist:{jti}")
            return result is not None
        except Exception as e:
            logger.warning(f"Redis blacklist check failed: {e}")
            return False
    
    # -- Zwischentoken fuer den zweiten Faktor --------------------------------
    #
    # Zwischen "Passwort stimmt" und "zweiter Faktor stimmt" braucht der Client
    # etwas, das die halbe Anmeldung belegt, ohne schon Zugriff zu geben.
    #
    # Die Audience ist bewusst eine ANDERE (`complyo-mfa`). `get_current_user`
    # in dependencies.py prueft auf `complyo-api` und weist dieses Token damit
    # ab. Ohne diese Trennung waere das Zwischentoken ein vollwertiger
    # Zugriffsschluessel — der zweite Faktor waere umgangen, indem man ihn
    # einfach nicht eingibt.
    MFA_AUDIENCE = "complyo-mfa"
    MFA_GUELTIG_SEKUNDEN = 300

    def create_mfa_token(self, user_id) -> str:
        now = _utcnow()
        payload = {
            "user_id": str(user_id),
            "sub": str(user_id),
            "jti": str(uuid4()),
            "iat": now,
            "nbf": now,
            "exp": now + timedelta(seconds=self.MFA_GUELTIG_SEKUNDEN),
            "iss": self.jwt_issuer,
            "aud": self.MFA_AUDIENCE,
        }
        return jwt.encode(payload, self.jwt_secret, algorithm="HS256")

    def verify_mfa_token(self, token: str) -> Optional[int]:
        try:
            payload = jwt.decode(
                token, self.jwt_secret, algorithms=["HS256"],
                audience=self.MFA_AUDIENCE, issuer=self.jwt_issuer,
            )
            return int(payload.get("user_id") or payload.get("sub"))
        except (jwt.InvalidTokenError, TypeError, ValueError) as e:
            logger.warning("MFA-Zwischentoken ungueltig: %s", e)
            return None

    async def setze_passwort(self, user_id: int, passwort: str) -> None:
        """
        Neues Passwort setzen und alle Sitzungen beenden.

        Das Beenden gehoert dazu und nicht in den Aufrufer: wer sein Passwort
        aendert, tut das oft genau deshalb, weil er einen Mitleser vermutet.
        Ein Wechsel, nach dem die fremde Sitzung weiterlaeuft, ist keiner.
        """
        hash_wert = _bcrypt.hashpw(passwort.encode(), _bcrypt.gensalt()).decode()
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                "UPDATE users SET password_hash = $1, updated_at = NOW() WHERE id = $2",
                hash_wert, user_id,
            )
        await self.beende_sitzungskette(user_id)

    async def create_refresh_token(self, user_id, user_agent: str = None, ip_address: str = None) -> str:
        """Create and store refresh token with session metadata"""
        token = secrets.token_urlsafe(64)
        user_id = int(user_id)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=self.refresh_token_expire)
        
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO user_sessions (user_id, refresh_token, expires_at, user_agent, ip_address)
                VALUES ($1, $2, $3, $4, $5)
                """,
                user_id, token, expires_at, user_agent, ip_address
            )
        
        return token
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"], audience=self.jwt_audience, issuer=self.jwt_issuer)
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
    
    async def refresh_access_token(self, refresh_token: str, user_agent: str = None, ip_address: str = None) -> Optional[tuple]:
        """
        Access-Token erneuern, Refresh-Token dabei drehen — mit Erkennung der
        Wiederverwendung.

        Bis zum 10.09.2026 stand "reuse-detection" nur in dieser Zeile. Der
        gedrehte Token wurde per DELETE entfernt, und ein zweiter Aufruf damit
        fand nichts mehr: eine Warnung ins Log, `None` zurueck, fertig. Genau
        das ist aber der Abdruck eines gestohlenen Tokens. Wer eine Kopie hat,
        loest sie irgendwann ein — entweder vor dem echten Nutzer (dann findet
        DESSEN Aufruf nichts mehr) oder danach. In beiden Faellen blieben alle
        anderen Sitzungen des Kontos bestehen, samt der frisch ausgegebenen des
        Angreifers.

        Jetzt wird der gedrehte Token nicht geloescht, sondern mit `revoked_at`
        entwertet und bis zu seinem Ablauf aufgehoben. Taucht er wieder auf, ist
        die Sitzungskette kompromittiert: ALLE Sitzungen des Kontos fallen, und
        alle ausgegebenen Access-Token kommen auf die Sperrliste. Der Nutzer
        muss sich neu anmelden — das ist der Preis, und er ist gegenueber einem
        stillen Mitleser der guenstigere.

        Aufgeraeumt werden die entwerteten Zeilen von `cleanup_expired_sessions`
        ueber `expires_at`, also spaetestens 30 Tage nach der Drehung.
        """
        async with self.db_pool.acquire() as conn:
            session = await conn.fetchrow(
                """
                SELECT user_id, expires_at, revoked_at FROM user_sessions
                WHERE refresh_token = $1
                """,
                refresh_token
            )

        if not session:
            # Unbekannt: entweder frei erfunden oder so alt, dass die Zeile
            # bereits abgeraeumt ist. Ohne user_id gibt es hier nichts zu
            # sperren; das faengt der Ratenzaehler an der Route ab.
            logger.warning("Refresh-Token unbekannt — abgelaufen, aufgeraeumt oder erfunden")
            return None

        user_id = session['user_id']

        if session['revoked_at'] is not None:
            # Der harte Fall. Dieser Token wurde bereits gedreht oder beim
            # Abmelden entwertet; ein zweiter Einloeseversuch kann nicht vom
            # rechtmaessigen Inhaber kommen.
            logger.error(
                "Wiederverwendung eines entwerteten Refresh-Tokens: user_id=%s, "
                "ip=%s, agent=%s — alle Sitzungen werden beendet",
                user_id, ip_address, user_agent
            )
            await self.beende_sitzungskette(user_id)
            return None

        if session['expires_at'] < datetime.now(timezone.utc):
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    "DELETE FROM user_sessions WHERE refresh_token = $1",
                    refresh_token
                )
            return None

        async with self.db_pool.acquire() as conn:
            # Entwerten, nicht loeschen: die Zeile ist ab jetzt der Koeder, an
            # dem eine Wiederverwendung auffaellt. Die Bedingung
            # `revoked_at IS NULL` macht daraus einen atomaren Schritt — zwei
            # gleichzeitige Erneuerungen mit demselben Token koennen nicht
            # beide gewinnen.
            entwertet = await conn.execute(
                "UPDATE user_sessions SET revoked_at = NOW() "
                "WHERE refresh_token = $1 AND revoked_at IS NULL",
                refresh_token
            )
        if entwertet.endswith(" 0"):
            logger.error(
                "Wettlauf um denselben Refresh-Token: user_id=%s — Sitzungen werden beendet",
                user_id
            )
            await self.beende_sitzungskette(user_id)
            return None

        new_access_token = self.create_access_token(user_id)
        new_refresh_token = await self.create_refresh_token(user_id, user_agent=user_agent, ip_address=ip_address)

        return new_access_token, new_refresh_token

    async def beende_sitzungskette(self, user_id: int):
        """
        Antwort auf eine erkannte Wiederverwendung: alle Sitzungen loeschen und
        alle noch laufenden Access-Token sperren.

        Ohne den zweiten Teil behielte ein Angreifer bis zu 15 Minuten Zugriff —
        so lange gilt ein Access-Token, und der fragt die Datenbank nicht.
        """
        await self.revoke_all_sessions(user_id)
        await self.blacklist_all_user_jtis(user_id, self.access_token_expire * 60 + 60)

    async def revoke_refresh_token(self, refresh_token: str):
        """
        Abmelden. Entwertet statt zu loeschen, aus demselben Grund wie bei der
        Drehung: taucht der Token nach dem Abmelden wieder auf, hat ihn jemand
        anders. Aufgeraeumt wird ueber `expires_at`.
        """
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                "UPDATE user_sessions SET revoked_at = NOW() "
                "WHERE refresh_token = $1 AND revoked_at IS NULL",
                refresh_token
            )

    async def revoke_all_sessions(self, user_id: int):
        """Delete all sessions for a user (logout-all or reuse-attack response)."""
        async with self.db_pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM user_sessions WHERE user_id = $1",
                user_id
            )
        logger.info(f"All sessions revoked for user_id={user_id}")

    async def blacklist_all_user_jtis(self, user_id: int, ttl_seconds: int):
        """Blacklist every jti stored in jwt:user_jtis:{user_id} Redis set."""
        if not self.redis:
            return
        set_key = f"jwt:user_jtis:{user_id}"
        try:
            members = await self.redis.smembers(set_key)
            for jti in members:
                await self._blacklist_jti(jti, ttl_seconds)
            await self.redis.delete(set_key)
        except Exception as e:
            logger.warning(f"Redis blacklist-all failed for user_id={user_id}: {e}")

    async def cleanup_expired_sessions(self):
        """Remove expired sessions from database"""
        async with self.db_pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM user_sessions WHERE expires_at < CURRENT_TIMESTAMP"
            )
        logger.info(f"Cleaned up expired sessions: {result}")

