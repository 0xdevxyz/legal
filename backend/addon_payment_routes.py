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

from auth_service import AuthService
from database_service import db_service

router = APIRouter(prefix="/api/addons", tags=["Add-Ons"])
security = HTTPBearer()
logger = logging.getLogger(__name__)

async def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user ID from JWT token"""
    from auth_routes import get_current_user
    user = await get_current_user(credentials)
    return user["user_id"]

# Stripe Configuration
stripe.api_key = os.getenv("STRIPE_API_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET_ADDONS", "")
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
        "discount_text": "Spare bis zu 35 Mio. € Strafe",
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
    # Note: You should fetch user email from database
    user_email = f"user_{user_id}@complyo.tech"  # Placeholder
    
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
    user_email = f"user_{user_id}@complyo.tech"  # Placeholder
    
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
        # One-time purchase
        # TODO: Handle one-time add-on purchase (e.g., send email to sales team)
        logger.info(f"One-time add-on purchased: {addon_key} by user {user_id}")

async def handle_addon_subscription_updated(subscription):
    """Handle add-on subscription updates"""
    # TODO: Update add-on status if needed
    logger.info(f"Add-on subscription updated: {subscription['id']}")

async def handle_addon_subscription_cancelled(subscription):
    """Handle add-on subscription cancellation"""
    subscription_id = subscription['id']
    
    # Find and cancel the add-on in database
    # Note: This requires querying by stripe_subscription_id
    logger.info(f"Add-on subscription cancelled: {subscription_id}")
    # TODO: Implement cancellation by stripe_subscription_id

async def handle_addon_payment_failed(invoice):
    """Handle failed add-on payment"""
    logger.warning(f"Add-on payment failed: {invoice['id']}")
    # TODO: Send notification to user

async def handle_addon_payment_succeeded(invoice):
    """Handle successful add-on payment"""
    logger.info(f"Add-on payment succeeded: {invoice['id']}")
    # Subscription stays active

