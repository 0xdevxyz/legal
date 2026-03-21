import os
import stripe
import json
import logging
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/payment", tags=["Payment"])

# Global references (set in main_production.py)
stripe_service = None
db_pool = None
auth_service = None

# Development Mode für Zahlungssimulation
DEV_MODE = os.getenv("DEV_MODE", "false").lower() in ("true", "1", "yes")
BYPASS_PAYMENT = os.getenv("BYPASS_PAYMENT", "false").lower() in ("true", "1", "yes")
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")

# Hard guard: DEV_MODE/BYPASS_PAYMENT must never be active in production
if (DEV_MODE or BYPASS_PAYMENT) and ENVIRONMENT == "production":
    raise RuntimeError(
        "CRITICAL: DEV_MODE or BYPASS_PAYMENT is enabled in production! "
        "Set DEV_MODE=false and BYPASS_PAYMENT=false in your production .env"
    )

# Environment variables
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://app.complyo.tech")

# Stripe Price IDs je Plan (im Stripe Dashboard anlegen)
# single:   19€/Monat × quantity (Anzahl Module)
# complete: 49€/Monat (Pauschal, alle 4 Module)
# expert:   39€/Monat (laufend) + einmalige Setup-Gebühr via price_data
# agency:   490€/Monat (25 Websites, White-Label)
STRIPE_PRICE_SINGLE_MODULE  = os.getenv("STRIPE_PRICE_SINGLE_MODULE")   # 19€/Monat
STRIPE_PRICE_COMPLETE       = os.getenv("STRIPE_PRICE_COMPLETE")         # 49€/Monat
STRIPE_PRICE_EXPERT_MONTHLY = os.getenv("STRIPE_PRICE_EXPERT_MONTHLY")  # 39€/Monat
STRIPE_PRICE_AGENCY_MONTHLY = os.getenv("STRIPE_PRICE_AGENCY_MONTHLY")  # 490€/Monat

# Alle 4 verfügbaren Module
ALL_MODULES = ['cookie', 'accessibility', 'legal_texts', 'monitoring']

logger.info(f"🔧 Payment Routes - DEV_MODE: {DEV_MODE}, BYPASS_PAYMENT: {BYPASS_PAYMENT}")


class CreateCheckoutRequest(BaseModel):
    plan_type: str        # 'single', 'complete', 'expert'
    modules: List[str] = []  # Pflicht bei 'single', wird bei 'complete'/'expert' auto-gesetzt


class CheckoutResponse(BaseModel):
    checkout_url: str
    session_id: str


async def get_current_user_from_auth_header(request: Request):
    """Get current user from Authorization header"""
    from auth_routes import get_current_user, security
    from fastapi.security import HTTPAuthorizationCredentials

    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    token = auth_header.replace('Bearer ', '')
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    return await get_current_user(credentials)


def _resolve_modules(plan_type: str, modules: List[str]) -> List[str]:
    """Gibt die aktiven Module für den Plan zurück."""
    if plan_type in ('complete', 'expert', 'agency'):
        return ALL_MODULES
    # single: nur die gewählten, validiert gegen bekannte IDs
    valid = [m for m in modules if m in ALL_MODULES]
    return valid


@router.post("/create-checkout", response_model=CheckoutResponse)
async def create_checkout(request: Request, data: CreateCheckoutRequest):
    """
    Erstellt eine Stripe Checkout Session.

    Pläne:
      single   → 19€/Monat × Anzahl gewählter Module
      complete → 49€/Monat (alle 4 Module)
      expert   → 2.990€ Setup (einmalig) + 39€/Monat
    """
    current_user = await get_current_user_from_auth_header(request)
    user_id: int = current_user['id']
    user_email: str = current_user['email']
    user_name: str = current_user.get('full_name', '')

    plan_type = data.plan_type
    active_modules = _resolve_modules(plan_type, data.modules)

    if plan_type == 'single' and not active_modules:
        raise HTTPException(status_code=400, detail="Mindestens ein Modul muss gewählt werden.")

    if plan_type not in ('single', 'complete', 'expert', 'agency'):
        raise HTTPException(status_code=400, detail=f"Unbekannter Plan: {plan_type}")

    # ─── DEV MODE ────────────────────────────────────────────────────────────
    if DEV_MODE or BYPASS_PAYMENT:
        logger.warning(f"⚠️  DEV_MODE: Simuliere Zahlung für User {user_id}, Plan {plan_type}")

        mock_session_id      = f"cs_test_dev_{uuid.uuid4().hex[:24]}"
        mock_subscription_id = f"sub_dev_{uuid.uuid4().hex[:24]}"

        _websites_max = 25 if plan_type == 'agency' else -1

        async with db_pool.acquire() as conn:
            # user_limits aktualisieren
            await conn.execute(
                """
                UPDATE user_limits
                SET plan_type    = $1,
                    websites_max = $3,
                    updated_at   = CURRENT_TIMESTAMP
                WHERE user_id = $2
                """,
                plan_type, user_id, _websites_max
            )

            # subscription eintragen
            await conn.execute(
                """
                INSERT INTO subscriptions
                    (user_id, plan_type, stripe_subscription_id, status)
                VALUES ($1, $2, $3, 'active')
                ON CONFLICT (stripe_subscription_id) DO UPDATE
                    SET status = 'active', updated_at = CURRENT_TIMESTAMP
                """,
                user_id, plan_type, mock_subscription_id
            )

            # Module aktivieren
            await _activate_modules(conn, user_id, active_modules, mock_subscription_id)

        logger.info(f"✅ DEV_MODE: User {user_id} → {plan_type} {active_modules}")
        success_url = f"{FRONTEND_URL}/dashboard?payment=success&session_id={mock_session_id}&dev_mode=true"
        return CheckoutResponse(checkout_url=success_url, session_id=mock_session_id)

    # ─── PRODUCTION: Stripe Checkout ─────────────────────────────────────────
    try:
        customer_id = await stripe_service.get_or_create_customer(user_id, user_email, user_name)

        success_url = f"{FRONTEND_URL}/dashboard?payment=success&session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url  = f"{FRONTEND_URL}/register?plan={plan_type}&payment=cancelled"

        metadata = {
            'user_id':   str(user_id),
            'plan_type': plan_type,
            'modules':   json.dumps(active_modules),
        }

        if plan_type == 'single':
            if not STRIPE_PRICE_SINGLE_MODULE:
                raise HTTPException(500, "STRIPE_PRICE_SINGLE_MODULE nicht konfiguriert")
            session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=['card', 'sepa_debit'],
                mode='subscription',
                line_items=[{
                    'price':    STRIPE_PRICE_SINGLE_MODULE,
                    'quantity': len(active_modules),   # 19€ × Anzahl Module
                }],
                success_url=success_url,
                cancel_url=cancel_url,
                metadata=metadata,
                subscription_data={'metadata': metadata},
                allow_promotion_codes=True,
                billing_address_collection='required',
                locale='de',
            )

        elif plan_type == 'complete':
            if not STRIPE_PRICE_COMPLETE:
                raise HTTPException(500, "STRIPE_PRICE_COMPLETE nicht konfiguriert")
            session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=['card', 'sepa_debit'],
                mode='subscription',
                line_items=[{'price': STRIPE_PRICE_COMPLETE, 'quantity': 1}],
                success_url=success_url,
                cancel_url=cancel_url,
                metadata=metadata,
                subscription_data={'metadata': metadata},
                allow_promotion_codes=True,
                billing_address_collection='required',
                locale='de',
            )

        elif plan_type == 'expert':
            if not STRIPE_PRICE_EXPERT_MONTHLY:
                raise HTTPException(500, "STRIPE_PRICE_EXPERT_MONTHLY nicht konfiguriert")
            session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=['card', 'sepa_debit'],
                mode='subscription',
                # Einmalige Setup-Gebühr als invoice_item vor der Subscription
                invoice_creation=None,  # Stripe handhabt dies intern
                line_items=[{'price': STRIPE_PRICE_EXPERT_MONTHLY, 'quantity': 1}],
                subscription_data={
                    'metadata': metadata,
                    # 2.990€ Einrichtungsgebühr als Add-on beim ersten Invoice
                    'add_invoice_items': [{
                        'price_data': {
                            'currency': 'eur',
                            'product_data': {'name': 'Expertenservice Setup-Gebühr'},
                            'unit_amount': 299000,  # 2.990,00 € in Cent
                        },
                        'quantity': 1,
                    }],
                },
                success_url=success_url,
                cancel_url=cancel_url,
                metadata=metadata,
                allow_promotion_codes=True,
                billing_address_collection='required',
                locale='de',
            )

        elif plan_type == 'agency':
            if not STRIPE_PRICE_AGENCY_MONTHLY:
                raise HTTPException(500, "STRIPE_PRICE_AGENCY_MONTHLY nicht konfiguriert")
            session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=['card', 'sepa_debit'],
                mode='subscription',
                line_items=[{'price': STRIPE_PRICE_AGENCY_MONTHLY, 'quantity': 1}],
                success_url=success_url,
                cancel_url=cancel_url,
                metadata=metadata,
                subscription_data={'metadata': metadata},
                allow_promotion_codes=True,
                billing_address_collection='required',
                locale='de',
            )

        logger.info(f"Stripe Checkout erstellt für User {user_id}: {session.id}")
        return CheckoutResponse(checkout_url=session.url, session_id=session.id)

    except stripe.error.StripeError as e:
        logger.error(f"Stripe-Fehler: {e}")
        raise HTTPException(status_code=500, detail=f"Stripe-Fehler: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Checkout-Fehler: {e}")
        raise HTTPException(status_code=500, detail="Fehler beim Erstellen der Checkout-Session")


async def _activate_modules(conn, user_id: int, modules: List[str], subscription_id: str):
    """Aktiviert Module in user_modules (idempotent per UPSERT)."""
    for module_id in modules:
        await conn.execute(
            """
            INSERT INTO user_modules
                (user_id, module_id, status, stripe_subscription_id)
            VALUES ($1, $2, 'active', $3)
            ON CONFLICT (user_id, module_id) DO UPDATE
                SET status                  = 'active',
                    stripe_subscription_id  = $3,
                    cancelled_at            = NULL,
                    updated_at              = NOW()
            """,
            user_id, module_id, subscription_id
        )


# ─── Webhook ─────────────────────────────────────────────────────────────────

@router.post("/webhook")
async def stripe_webhook(request: Request):
    """Stripe Webhook: aktiviert/deaktiviert Pläne und Module"""
    payload    = await request.body()
    sig_header = request.headers.get('stripe-signature')

    if not sig_header:
        raise HTTPException(400, "Missing stripe-signature header")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except ValueError:
        raise HTTPException(400, "Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(400, "Invalid signature")

    event_type = event['type']
    logger.info(f"Stripe Webhook: {event_type}")

    if event_type == 'checkout.session.completed':
        await _handle_checkout_completed(event['data']['object'])
    elif event_type == 'customer.subscription.updated':
        await _handle_subscription_updated(event['data']['object'])
    elif event_type == 'customer.subscription.deleted':
        await _handle_subscription_cancelled(event['data']['object'])
    elif event_type == 'invoice.payment_failed':
        await _handle_payment_failed(event['data']['object'])
    else:
        logger.info(f"Unhandled event: {event_type}")

    return {"status": "success"}


async def _handle_checkout_completed(session: Dict[str, Any]):
    """Checkout erfolgreich → Plan + Module aktivieren."""
    try:
        user_id         = int(session['metadata']['user_id'])
        plan_type       = session['metadata']['plan_type']
        modules_json    = session['metadata'].get('modules', '[]')
        active_modules  = json.loads(modules_json)
        subscription_id = session.get('subscription', '')

        logger.info(f"Checkout completed: user={user_id}, plan={plan_type}, modules={active_modules}")
        _websites_max = 25 if plan_type == 'agency' else -1

        async with db_pool.acquire() as conn:
            # user_limits aktualisieren
            await conn.execute(
                """
                UPDATE user_limits
                SET plan_type    = $1,
                    websites_max = $3,
                    updated_at   = CURRENT_TIMESTAMP
                WHERE user_id = $2
                """,
                plan_type, user_id, _websites_max
            )

            # Subscription eintragen
            await conn.execute(
                """
                INSERT INTO subscriptions
                    (user_id, plan_type, stripe_subscription_id, status)
                VALUES ($1, $2, $3, 'active')
                ON CONFLICT (stripe_subscription_id) DO UPDATE
                    SET status = 'active', updated_at = CURRENT_TIMESTAMP
                """,
                user_id, plan_type, subscription_id
            )

            # Module aktivieren
            await _activate_modules(conn, user_id, active_modules, subscription_id)

        logger.info(f"✅ User {user_id} → {plan_type}, Module: {active_modules}")

    except Exception as e:
        logger.error(f"Fehler bei checkout.session.completed: {e}")
        raise


async def _handle_subscription_updated(subscription: Dict[str, Any]):
    """Subscription-Status in DB synchronisieren."""
    try:
        sub_status = subscription['status']
        sub_id     = subscription['id']

        async with db_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE subscriptions
                SET status = $1, updated_at = CURRENT_TIMESTAMP
                WHERE stripe_subscription_id = $2
                """,
                sub_status, sub_id
            )

        logger.info(f"Subscription {sub_id} → {sub_status}")

    except Exception as e:
        logger.error(f"Fehler bei subscription.updated: {e}")


async def _handle_subscription_cancelled(subscription: Dict[str, Any]):
    """Subscription gekündigt → auf Free downgraden + Module deaktivieren."""
    try:
        sub_id  = subscription['id']
        user_id = int(subscription['metadata'].get('user_id', 0))

        if not user_id:
            logger.warning("subscription.deleted ohne user_id in metadata")
            return

        async with db_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE subscriptions
                SET status = 'cancelled', updated_at = CURRENT_TIMESTAMP
                WHERE stripe_subscription_id = $1
                """,
                sub_id
            )
            await conn.execute(
                """
                UPDATE user_limits
                SET plan_type  = 'free',
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = $1
                """,
                user_id
            )
            # Alle Module dieses Users deaktivieren
            await conn.execute(
                """
                UPDATE user_modules
                SET status       = 'cancelled',
                    cancelled_at = NOW(),
                    updated_at   = NOW()
                WHERE user_id = $1 AND stripe_subscription_id = $2
                """,
                user_id, sub_id
            )

        logger.info(f"User {user_id} → free (Subscription {sub_id} cancelled)")

    except Exception as e:
        logger.error(f"Fehler bei subscription.deleted: {e}")


async def _handle_payment_failed(invoice: Dict[str, Any]):
    """Zahlung fehlgeschlagen → Subscription auf past_due."""
    try:
        sub_id = invoice.get('subscription')
        if not sub_id:
            return

        async with db_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE subscriptions
                SET status = 'past_due', updated_at = CURRENT_TIMESTAMP
                WHERE stripe_subscription_id = $1
                """,
                sub_id
            )

        logger.warning(f"Zahlung fehlgeschlagen für Subscription {sub_id}")

    except Exception as e:
        logger.error(f"Fehler bei invoice.payment_failed: {e}")


# ─── Status & Portal ──────────────────────────────────────────────────────────

@router.get("/subscription-status")
async def get_subscription_status(request: Request):
    """Gibt den aktuellen Subscription-Status des Users zurück."""
    try:
        current_user = await get_current_user_from_auth_header(request)
        user_id = current_user['id']

        async with db_pool.acquire() as conn:
            sub = await conn.fetchrow(
                """
                SELECT plan_type, status, created_at
                FROM subscriptions
                WHERE user_id = $1 AND status IN ('active', 'trialing')
                ORDER BY created_at DESC LIMIT 1
                """,
                user_id
            )

            modules = await conn.fetch(
                """
                SELECT um.module_id, m.name
                FROM user_modules um
                JOIN modules m ON um.module_id = m.id
                WHERE um.user_id = $1 AND um.status = 'active'
                """,
                user_id
            )

        if not sub:
            return {"has_subscription": False, "plan": "free", "modules": []}

        return {
            "has_subscription": True,
            "plan":    sub['plan_type'],
            "status":  sub['status'],
            "modules": [{"id": m['module_id'], "name": m['name']} for m in modules],
        }

    except Exception as e:
        logger.error(f"Fehler bei subscription-status: {e}")
        raise HTTPException(500, "Fehler beim Abrufen des Subscription-Status")


@router.get("/health")
async def payment_health():
    return {
        "status": "healthy",
        "service": "payment",
        "stripe_service_initialized": stripe_service is not None,
        "webhook_secret_configured": STRIPE_WEBHOOK_SECRET is not None,
        "prices_configured": {
            "single_module":  STRIPE_PRICE_SINGLE_MODULE is not None,
            "complete":       STRIPE_PRICE_COMPLETE is not None,
            "expert_monthly": STRIPE_PRICE_EXPERT_MONTHLY is not None,
        }
    }
