"""
Add-On Payment Routes - ComploAI Guard & Priority Support
"""

from fastapi import APIRouter, HTTPException, Depends, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import stripe
import os
import logging
import json
import smtplib
from email.mime.text import MIMEText

from auth_service import AuthService
from database_service import db_service
from dependencies import get_current_user

router = APIRouter(prefix="/api/addons", tags=["Add-Ons"])
security = HTTPBearer()
logger = logging.getLogger(__name__)

SALES_EMAIL = os.getenv("SALES_EMAIL", "sales@complyo.de")

def _notify_sales(subject: str, body: str) -> None:
    """Send a plain-text notification email to the sales team. Silent on failure."""
    smtp_host = os.getenv("SMTP_HOST", "")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USERNAME", "")
    smtp_pass = os.getenv("SMTP_PASSWORD", "")
    if not all([smtp_host, smtp_user, smtp_pass]):
        logger.info(f"[DEMO] Sales notification (no SMTP): {subject} | {body}")
        return
    try:
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = smtp_user
        msg["To"] = SALES_EMAIL
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, [SALES_EMAIL], msg.as_string())
    except Exception as e:
        logger.error(f"Failed to send sales notification: {e}")

async def get_current_user_id(current_user: dict = Depends(get_current_user)):
    """
    Get current user ID. Nutzt die kanonische Auth-Dependency korrekt via Depends
    (vorher wurde get_current_user manuell mit 'credentials' aufgerufen, wodurch der
    request-Parameter falsch belegt war → 'Depends' object has no attribute 'credentials').
    """
    return current_user["id"]

# Stripe Configuration
stripe.api_key = os.getenv("STRIPE_API_KEY", "")
_addon_webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET_ADDONS", "")
if not _addon_webhook_secret:
    raise RuntimeError("STRIPE_WEBHOOK_SECRET_ADDONS environment variable is required!")
STRIPE_WEBHOOK_SECRET = _addon_webhook_secret
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://app.complyo.tech")

# ==================== PRICING CONFIGURATION ====================

MONTHLY_ADDONS = {
    "comploai_guard": {
        "name": "ComploAI Guard",
        "tagline": "EU AI Act Compliance Modul",
        "price_monthly": 99,
        "currency": "eur",
        "features": [
            "EU AI Act Compliance Checks",
            "Automatische Risiko-Klassifizierung",
            "10 KI-Systeme (Starter/Professional)",
            "25 KI-Systeme (Business)",
            "Unbegrenzt (Enterprise)",
            "AI-System-Inventory",
            "Automatische Dokumentations-Generierung",
            "AI Act PDF Reports",
            "Deadline-Tracking",
            "Compliance-Scores"
        ],
        "limits_by_plan": {
            "starter": {"ai_systems": 10},
            "professional": {"ai_systems": 10},
            "business": {"ai_systems": 25},
            "enterprise": {"ai_systems": -1}
        },
        "stripe_price_id": os.getenv("STRIPE_PRICE_COMPLOAI_GUARD", "price_1234"),  # Set in Stripe Dashboard
        "badge": "NEW",
        "discount_text": "Spare bis zu 50.000€ Bußgeld",
        "compatible_plans": ["starter", "professional", "business", "enterprise"]
    },
    "priority_support": {
        "name": "Priority Support",
        "tagline": "Erstklassiger Support rund um die Uhr",
        "price_monthly": 49,
        "currency": "eur",
        "features": [
            "24/7 Support (auch Wochenende)",
            "Response-Zeit < 2 Stunden",
            "Direkter Telefon-Support",
            "Dedizierter Support-Spezialist",
            "Slack/Teams-Integration",
            "Monatliches Compliance-Review (30 Min)",
            "Priorisierte Feature-Requests"
        ],
        "stripe_price_id": os.getenv("STRIPE_PRICE_PRIORITY_SUPPORT", "price_5678"),  # Set in Stripe Dashboard
        "badge": "PREMIUM",
        "compatible_plans": ["starter", "professional", "business", "enterprise"]
    },
    "agency_sites_extra": {
        "name": "Extra Sites Paket",
        "tagline": "25 weitere Client-Sites für Ihr Agentur-Dashboard",
        "price_monthly": 200,
        "currency": "eur",
        "features": [
            "25 zusätzliche verwaltete Sites",
            "Gleiche Features wie Basis-Paket",
            "Sofort aktiv nach Buchung",
        ],
        "limits_by_plan": {
            "agency": {"extra_sites": 25},
        },
        "stripe_price_id": os.getenv("STRIPE_PRICE_AGENCY_SITES_EXTRA", "price_agency_extra"),
        "badge": "ADD-ON",
        "compatible_plans": ["agency"],
    }
}

ONETIME_ADDONS = {
    "expert_ai_audit": {
        "name": "Expert AI Act Audit",
        "price": 2999,
        "currency": "eur",
        "description": "Vollständiges AI Act Audit durch zertifizierte Compliance-Experten",
        "includes": [
            "Audit aller KI-Systeme (bis zu 20)",
            "Detaillierte Risiko-Analyse",
            "Rechtsgutachten",
            "Handlungsempfehlungen",
            "3 Stunden Beratungsgespräch",
            "Follow-up nach 3 Monaten"
        ],
        "duration": "2-3 Wochen",
        "stripe_price_id": os.getenv("STRIPE_PRICE_EXPERT_AUDIT", "price_9999")
    },
    "implementation_support": {
        "name": "AI Act Implementation Support",
        "price": 1999,
        "currency": "eur",
        "description": "4 Wochen Begleitung bei der Umsetzung der AI Act Anforderungen",
        "includes": [
            "Wöchentliche 2h Consulting-Calls",
            "Review der Dokumentation",
            "Template-Bereitstellung",
            "Schulung des Teams",
            "Email-Support während Laufzeit"
        ],
        "duration": "4 Wochen",
        "stripe_price_id": os.getenv("STRIPE_PRICE_IMPLEMENTATION", "price_8888")
    },
    "custom_integration": {
        "name": "Custom Integration",
        "price": 3999,
        "currency": "eur",
        "description": "Maßgeschneiderte Integration in Ihre bestehenden Systeme",
        "includes": [
            "API-Integration in Ihre Tools",
            "SSO/SAML Setup",
            "Custom Webhooks",
            "Dedizierter Entwickler (20h)",
            "3 Monate Wartung inklusive"
        ],
        "duration": "4-6 Wochen",
        "stripe_price_id": os.getenv("STRIPE_PRICE_CUSTOM_INTEGRATION", "price_7777")
    }
}

# ==================== REQUEST/RESPONSE MODELS ====================

class AddAddonRequest(BaseModel):
    addon_key: str
    user_plan: Optional[str] = "professional"  # To determine limits

class CheckoutResponse(BaseModel):
    checkout_url: str
    session_id: str

class AddonStatusResponse(BaseModel):
    addon_key: str
    addon_name: str
    status: str
    price_monthly: float
    limits: Dict[str, Any]
    started_at: str
    expires_at: Optional[str]

# ==================== ENDPOINTS ====================

@router.get("/catalog")
async def get_addons_catalog():
    """
    Hole den kompletten Add-on-Katalog
    """
    return {
        "monthly_addons": MONTHLY_ADDONS,
        "onetime_addons": ONETIME_ADDONS
    }

@router.get("/my-addons")
async def get_my_addons(
    user_id: int = Depends(get_current_user_id)
):
    """
    Hole alle aktiven Add-ons des Users
    """
    addons = await db_service.get_user_addons(user_id)
    
    return {
        "addons": addons,
        "total_monthly_cost": sum(a['price_monthly'] for a in addons if a['status'] == 'active')
    }

@router.post("/subscribe/{addon_key}", response_model=CheckoutResponse)
async def subscribe_to_addon(
    addon_key: str,
    data: AddAddonRequest,
    user_id: int = Depends(get_current_user_id)
):
    """
    Abonniere ein monatliches Add-on
    """
    
    # Check if addon exists
    if addon_key not in MONTHLY_ADDONS:
        raise HTTPException(
            status_code=404,
            detail=f"Add-on '{addon_key}' nicht gefunden"
        )
    
    addon = MONTHLY_ADDONS[addon_key]
    
    # Check if already subscribed
    has_addon = await db_service.check_user_addon(user_id, addon_key)
    if has_addon:
        raise HTTPException(
            status_code=400,
            detail=f"Sie haben '{addon['name']}' bereits abonniert"
        )
    
    # Get user email for Stripe
    async with db_service.get_connection() as conn:
        user_row = await conn.fetchrow("SELECT email FROM users WHERE id = $1", user_id)
    user_email = user_row["email"] if user_row else ""

    # Determine limits based on user plan
    user_plan = data.user_plan or "professional"
    limits = addon.get("limits_by_plan", {}).get(user_plan, {})
    
    # Create Stripe checkout session
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card', 'sepa_debit'],
            mode='subscription',
            customer_email=user_email,
            line_items=[{
                'price': addon['stripe_price_id'],
                'quantity': 1,
            }],
            metadata={
                'user_id': user_id,
                'addon_key': addon_key,
                'addon_name': addon['name'],
                'limits': json.dumps(limits)
            },
            success_url=f"{FRONTEND_URL}/dashboard/addons?success=true&session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{FRONTEND_URL}/dashboard/addons?canceled=true",
            allow_promotion_codes=True,
            billing_address_collection='required',
            locale='de'
        )
        
        return CheckoutResponse(
            checkout_url=checkout_session.url,
            session_id=checkout_session.id
        )
    
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error creating checkout: {e}")
        raise HTTPException(
            status_code=500,
            detail="Fehler beim Erstellen der Checkout-Session"
        )

@router.post("/purchase/{addon_key}", response_model=CheckoutResponse)
async def purchase_onetime_addon(
    addon_key: str,
    user_id: int = Depends(get_current_user_id)
):
    """
    Kaufe ein einmaliges Add-on
    """
    
    # Check if addon exists
    if addon_key not in ONETIME_ADDONS:
        raise HTTPException(
            status_code=404,
            detail=f"Add-on '{addon_key}' nicht gefunden"
        )
    
    addon = ONETIME_ADDONS[addon_key]
    
    # Get user email
    async with db_service.get_connection() as conn:
        user_row = await conn.fetchrow("SELECT email FROM users WHERE id = $1", user_id)
    user_email = user_row["email"] if user_row else ""

    # Create Stripe checkout session for one-time payment
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card', 'sepa_debit'],
            mode='payment',
            customer_email=user_email,
            line_items=[{
                'price': addon['stripe_price_id'],
                'quantity': 1,
            }],
            metadata={
                'user_id': user_id,
                'addon_key': addon_key,
                'addon_name': addon['name'],
                'addon_type': 'onetime'
            },
            success_url=f"{FRONTEND_URL}/dashboard/addons?success=true&session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{FRONTEND_URL}/dashboard/addons?canceled=true",
            allow_promotion_codes=True,
            billing_address_collection='required',
            locale='de'
        )
        
        return CheckoutResponse(
            checkout_url=checkout_session.url,
            session_id=checkout_session.id
        )
    
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error creating checkout: {e}")
        raise HTTPException(
            status_code=500,
            detail="Fehler beim Erstellen der Checkout-Session"
        )

@router.post("/cancel/{addon_key}")
async def cancel_addon(
    addon_key: str,
    user_id: int = Depends(get_current_user_id)
):
    """
    Kündige ein Add-on
    """
    
    # Check if user has this addon
    has_addon = await db_service.check_user_addon(user_id, addon_key)
    if not has_addon:
        raise HTTPException(
            status_code=404,
            detail="Add-on nicht gefunden oder bereits gekündigt"
        )
    
    # Get addon details to cancel Stripe subscription
    addons = await db_service.get_user_addons(user_id)
    addon = next((a for a in addons if a['addon_key'] == addon_key), None)
    
    if not addon:
        raise HTTPException(status_code=404, detail="Add-on nicht gefunden")
    
    # Cancel in Stripe if subscription exists
    if addon.get('stripe_subscription_id'):
        try:
            stripe.Subscription.modify(
                addon['stripe_subscription_id'],
                cancel_at_period_end=True
            )
        except stripe.error.StripeError as e:
            logger.error(f"Error canceling Stripe subscription: {e}")
            # Continue anyway to cancel in our database
    
    # Cancel in database
    success = await db_service.cancel_user_addon(user_id, addon_key)
    
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Fehler beim Kündigen des Add-ons"
        )
    
    return {
        "message": f"Add-on '{addon['addon_name']}' erfolgreich gekündigt",
        "addon_key": addon_key,
        "status": "cancelled"
    }

# ==================== WEBHOOKS ====================

@router.post("/webhook")
async def addon_webhook(request: Request):
    """
    Handle Stripe webhooks for add-ons
    """
    
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    
    if not sig_header:
        raise HTTPException(400, "Missing stripe-signature header")
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        logger.error(f"Invalid payload: {e}")
        raise HTTPException(400, "Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid signature: {e}")
        raise HTTPException(400, "Invalid signature")
    
    # Handle events
    event_type = event['type']
    logger.info(f"Received Add-on Stripe webhook: {event_type}")
    
    if event_type == 'checkout.session.completed':
        await handle_addon_checkout_completed(event['data']['object'])
    elif event_type == 'customer.subscription.updated':
        await handle_addon_subscription_updated(event['data']['object'])
    elif event_type == 'customer.subscription.deleted':
        await handle_addon_subscription_cancelled(event['data']['object'])
    elif event_type == 'invoice.payment_failed':
        await handle_addon_payment_failed(event['data']['object'])
    elif event_type == 'invoice.payment_succeeded':
        await handle_addon_payment_succeeded(event['data']['object'])
    else:
        logger.info(f"Unhandled event type: {event_type}")
    
    return {"status": "success"}

async def handle_addon_checkout_completed(session):
    """Handle successful add-on checkout"""
    
    user_id = session['metadata']['user_id']
    addon_key = session['metadata']['addon_key']
    addon_name = session['metadata']['addon_name']
    addon_type = session['metadata'].get('addon_type', 'monthly')
    
    logger.info(f"Add-on checkout completed: user={user_id}, addon={addon_key}")
    
    if addon_type == 'monthly':
        # Monthly subscription
        subscription_id = session.get('subscription')
        limits = json.loads(session['metadata'].get('limits', '{}'))
        
        addon_config = MONTHLY_ADDONS.get(addon_key, {})
        price = addon_config.get('price_monthly', 0)
        
        # Create add-on in database
        await db_service.create_user_addon(
            user_id=user_id,
            addon_key=addon_key,
            addon_name=addon_name,
            price_monthly=price,
            limits=limits,
            stripe_subscription_id=subscription_id
        )
        
        logger.info(f"Created monthly add-on subscription: {addon_key} for user {user_id}")
    
    else:
        # One-time purchase — notify sales team
        addon_config = ONETIME_ADDONS.get(addon_key, {})
        price = addon_config.get("price", 0)
        customer_email = session.get("customer_details", {}).get("email", "unbekannt")
        _notify_sales(
            subject=f"Neue One-Time-Buchung: {addon_name}",
            body=(
                f"Neues One-Time-Addon gebucht:\n\n"
                f"Addon: {addon_name} ({addon_key})\n"
                f"Preis: {price}€\n"
                f"User-ID: {user_id}\n"
                f"Kunden-Email: {customer_email}\n"
                f"Stripe Session: {session.get('id', 'n/a')}\n"
            )
        )
        logger.info(f"One-time add-on purchased: {addon_key} by user {user_id}")

async def handle_addon_subscription_updated(subscription):
    """Handle add-on subscription updates"""
    subscription_id = subscription['id']
    status = subscription.get('status', 'unknown')
    try:
        async with db_service.get_connection() as conn:
            await conn.execute(
                """
                UPDATE user_addons
                SET status = $1
                WHERE stripe_subscription_id = $2
                """,
                status,
                subscription_id
            )
        logger.info(f"Add-on subscription updated: {subscription_id} → {status}")
    except Exception as e:
        logger.error(f"Error updating add-on subscription {subscription_id}: {e}")

async def handle_addon_subscription_cancelled(subscription):
    """Handle add-on subscription cancellation"""
    subscription_id = subscription['id']
    try:
        async with db_service.get_connection() as conn:
            await conn.execute(
                """
                UPDATE user_addons
                SET status = 'cancelled', cancelled_at = NOW()
                WHERE stripe_subscription_id = $1
                """,
                subscription_id
            )
        logger.info(f"Add-on subscription cancelled: {subscription_id}")
    except Exception as e:
        logger.error(f"Error cancelling add-on subscription {subscription_id}: {e}")

async def handle_addon_payment_failed(invoice):
    """Handle failed add-on payment"""
    subscription_id = invoice.get('subscription')
    if not subscription_id:
        logger.warning(f"Add-on payment_failed invoice {invoice['id']} has no subscription")
        return
    try:
        async with db_service.get_connection() as conn:
            await conn.execute(
                """
                UPDATE user_addons
                SET status = 'past_due'
                WHERE stripe_subscription_id = $1
                """,
                subscription_id
            )
        logger.warning(f"Add-on payment failed for subscription {subscription_id} — status set to past_due")
    except Exception as e:
        logger.error(f"Error handling payment_failed for subscription {subscription_id}: {e}")

async def handle_addon_payment_succeeded(invoice):
    """Handle successful add-on payment"""
    logger.info(f"Add-on payment succeeded: {invoice['id']}")
    # Subscription stays active

