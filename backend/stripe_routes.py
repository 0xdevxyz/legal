"""
Stripe Integration Routes für Freemium-Modell
Handles Checkout Sessions, Webhooks und Subscription Management
"""

import stripe
import os
import hmac
import hashlib
from fastapi import APIRouter, HTTPException, Depends, Request, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from typing import Optional
import logging
from datetime import datetime
import uuid

from database_service import DatabaseService

logger = logging.getLogger(__name__)

# Development Mode für Zahlungssimulation
DEV_MODE = os.getenv("DEV_MODE", "false").lower() in ("true", "1", "yes")
BYPASS_PAYMENT = os.getenv("BYPASS_PAYMENT", "false").lower() in ("true", "1", "yes")

# Stripe API Key aus Umgebungsvariablen
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_...")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_...")

# Stripe Price IDs (müssen in Stripe Dashboard erstellt werden)
STRIPE_PRICES = {
    "pro_monthly": os.getenv("STRIPE_PRICE_PRO_MONTHLY", None),
    "pro_yearly": os.getenv("STRIPE_PRICE_PRO_YEARLY", None),
}

logger.info(f"🔧 Payment System - DEV_MODE: {DEV_MODE}, BYPASS_PAYMENT: {BYPASS_PAYMENT}")

router = APIRouter(prefix="/api/stripe", tags=["stripe"])
db_service = DatabaseService()
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user from Authorization header using auth_routes"""
    from auth_routes import get_current_user as auth_get_user
    return await auth_get_user(credentials)

class CheckoutRequest(BaseModel):
    plan: str = "pro"  # 'pro' 
    billing_period: str = "monthly"  # 'monthly' or 'yearly'
    domain: Optional[str] = None  # Domain für Domain-Lock
    success_url: str
    cancel_url: str

class PortalRequest(BaseModel):
    return_url: str

@router.post("/create-checkout")
async def create_checkout_session(
    request: CheckoutRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Erstellt eine Stripe Checkout Session für das Upgrade
    Im DEV_MODE: Simuliert erfolgreiche Zahlung ohne echten Stripe-Call
    """
    try:
        user_id = current_user.get('uid')
        user_email = current_user.get('email')
        
        if not user_id or not user_email:
            raise HTTPException(status_code=401, detail="Unauthorized")
        
        # 🚀 DEV MODE: Simuliere Zahlung und aktiviere direkt
        if DEV_MODE or BYPASS_PAYMENT:
            logger.warning(f"⚠️ DEV_MODE: Simuliere Zahlung für User {user_id}")
            
            # Generiere Mock Session ID
            mock_session_id = f"cs_test_dev_{uuid.uuid4().hex[:24]}"
            mock_subscription_id = f"sub_dev_{uuid.uuid4().hex[:24]}"
            mock_customer_id = f"cus_dev_{uuid.uuid4().hex[:24]}"
            
            # Upgrade User direkt in der Datenbank
            async with db_service.pool.acquire() as conn:
                # Update user_limits zu PRO
                await conn.execute(
                    """
                    UPDATE user_limits
                    SET 
                        plan_type = $1,
                        fixes_limit = 999999,
                        websites_max = 999,
                        exports_max = 999
                    WHERE user_id = $2
                    """,
                    request.plan, user_id
                )
                
                # Unlock Domain falls vorhanden
                if request.domain:
                    logger.info(f"DEV_MODE: Unlocking domain {request.domain} for user {user_id}")
                    await conn.execute(
                        "SELECT unlock_domain($1, $2)",
                        user_id, request.domain
                    )
                
                # Insert Mock Subscription
                await conn.execute(
                    """
                    INSERT INTO subscriptions 
                    (user_id, stripe_customer_id, stripe_subscription_id, plan_type, status)
                    VALUES ($1, $2, $3, $4, 'active')
                    ON CONFLICT (stripe_subscription_id) 
                    DO UPDATE SET
                        status = 'active',
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    user_id, mock_customer_id, mock_subscription_id, request.plan
                )
            
            logger.info(f"✅ DEV_MODE: User {user_id} upgraded to {request.plan}" + 
                       (f" (domain: {request.domain})" if request.domain else ""))
            
            # Redirect direkt zur Success-URL
            success_url = request.success_url.replace("{CHECKOUT_SESSION_ID}", mock_session_id)
            return {
                'checkout_url': success_url,
                'session_id': mock_session_id,
                'dev_mode': True,
                'message': '⚠️ Entwicklungsmodus: Zahlung wurde simuliert'
            }
        
        # ✅ PRODUCTION MODE: Echter Stripe Checkout
        # Wähle passenden Price ID
        price_key = f"{request.plan}_{request.billing_period}"
        price_id = STRIPE_PRICES.get(price_key)
        
        if not price_id:
            logger.error(f"No Stripe Price ID found for {price_key}")
            price_id = STRIPE_PRICES["pro_monthly"]  # Fallback
        
        # Erstelle Checkout Session
        checkout_metadata = {
            'user_id': user_id,
            'plan': request.plan,
            'billing_period': request.billing_period
        }
        
        # Domain hinzufügen falls vorhanden
        if request.domain:
            checkout_metadata['domain'] = request.domain
            logger.info(f"Domain added to checkout metadata: {request.domain}")
        
        checkout_session = stripe.checkout.Session.create(
            customer_email=user_email,
            payment_method_types=['card', 'sepa_debit'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=request.success_url + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=request.cancel_url,
            metadata=checkout_metadata,
            subscription_data={
                'metadata': checkout_metadata  # Auch in Subscription Metadata speichern
            },
            allow_promotion_codes=True,
            billing_address_collection='required',
            locale='de'
        )
        
        logger.info(f"Created checkout session for user {user_id}: {checkout_session.id}")
        
        return {
            'checkout_url': checkout_session.url,
            'session_id': checkout_session.id
        }
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error creating checkout: {e}")
        raise HTTPException(status_code=500, detail=f"Stripe error: {str(e)}")
    except Exception as e:
        logger.error(f"Error creating checkout: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create-portal-session")
async def create_portal_session(
    request: PortalRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Erstellt eine Stripe Customer Portal Session für Subscription Management
    """
    try:
        user_id = current_user.get('uid')
        
        # Hole Stripe Customer ID aus DB
        async with db_service.pool.acquire() as conn:
            result = await conn.fetchrow(
                """
                SELECT stripe_customer_id 
                FROM subscriptions 
                WHERE user_id = $1 AND status = 'active'
                ORDER BY created_at DESC 
                LIMIT 1
                """,
                user_id
            )
            
            if not result or not result['stripe_customer_id']:
                raise HTTPException(
                    status_code=404, 
                    detail="No active subscription found"
                )
            
            customer_id = result['stripe_customer_id']
        
        # Erstelle Portal Session
        portal_session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=request.return_url,
        )
        
        return {'portal_url': portal_session.url}
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error creating portal: {e}")
        raise HTTPException(status_code=500, detail=f"Stripe error: {str(e)}")
    except Exception as e:
        logger.error(f"Error creating portal: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None)
):
    """
    Stripe Webhook Handler für Subscription Events
    """
    try:
        payload = await request.body()
        
        # Verify Stripe signature
        try:
            event = stripe.Webhook.construct_event(
                payload, stripe_signature, STRIPE_WEBHOOK_SECRET
            )
        except ValueError as e:
            logger.error(f"Invalid webhook payload: {e}")
            raise HTTPException(status_code=400, detail="Invalid payload")
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid webhook signature: {e}")
            raise HTTPException(status_code=400, detail="Invalid signature")
        
        logger.info(f"Received Stripe webhook: {event['type']}")
        
        # Handle different event types
        if event['type'] == 'checkout.session.completed':
            await handle_checkout_completed(event['data']['object'])
            
        elif event['type'] == 'customer.subscription.created':
            await handle_subscription_created(event['data']['object'])
            
        elif event['type'] == 'customer.subscription.updated':
            await handle_subscription_updated(event['data']['object'])
            
        elif event['type'] == 'customer.subscription.deleted':
            await handle_subscription_deleted(event['data']['object'])
            
        elif event['type'] == 'invoice.payment_succeeded':
            await handle_payment_succeeded(event['data']['object'])
            
        elif event['type'] == 'invoice.payment_failed':
            await handle_payment_failed(event['data']['object'])
        
        return {'status': 'success'}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def handle_checkout_completed(session):
    """Handle successful checkout - upgrade user and unlock domain"""
    try:
        user_id = session['metadata'].get('user_id')
        plan = session['metadata'].get('plan', 'pro')
        domain = session['metadata'].get('domain')  # Domain aus Metadata
        customer_id = session['customer']
        subscription_id = session['subscription']
        
        if not user_id:
            logger.error("No user_id in checkout session metadata")
            return
        
        async with db_service.pool.acquire() as conn:
            # Update user_limits zu PRO
            await conn.execute(
                """
                UPDATE user_limits
                SET 
                    plan_type = $1,
                    fixes_limit = 999999,
                    websites_max = 999,
                    exports_max = 999
                WHERE user_id = $2
                """,
                plan, user_id
            )
            
            # Unlock Domain falls vorhanden
            if domain:
                logger.info(f"Unlocking domain {domain} for user {user_id}")
                await conn.execute(
                    "SELECT unlock_domain($1, $2)",
                    user_id, domain
                )
                logger.info(f"✅ Domain {domain} unlocked for user {user_id}")
            
            # Insert/Update subscription
            await conn.execute(
                """
                INSERT INTO subscriptions 
                (user_id, stripe_customer_id, stripe_subscription_id, plan_type, status)
                VALUES ($1, $2, $3, $4, 'active')
                ON CONFLICT (stripe_subscription_id) 
                DO UPDATE SET
                    status = 'active',
                    updated_at = CURRENT_TIMESTAMP
                """,
                user_id, customer_id, subscription_id, plan
            )
            
        logger.info(f"✅ User {user_id} upgraded to {plan}" + (f" (domain: {domain})" if domain else ""))
        
    except Exception as e:
        logger.error(f"Error handling checkout completed: {e}")

async def handle_subscription_created(subscription):
    """Handle subscription creation"""
    try:
        customer_id = subscription['customer']
        subscription_id = subscription['id']
        user_id = subscription['metadata'].get('user_id')
        
        if not user_id:
            logger.warning("No user_id in subscription metadata")
            return
        
        async with db_service.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO subscriptions 
                (user_id, stripe_customer_id, stripe_subscription_id, plan_type, status)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (stripe_subscription_id) 
                DO UPDATE SET
                    status = EXCLUDED.status,
                    updated_at = CURRENT_TIMESTAMP
                """,
                user_id, customer_id, subscription_id, 'pro', 'active'
            )
            
        logger.info(f"Subscription created for user {user_id}")
        
    except Exception as e:
        logger.error(f"Error handling subscription created: {e}")

async def handle_subscription_updated(subscription):
    """Handle subscription update"""
    try:
        subscription_id = subscription['id']
        status = subscription['status']
        
        async with db_service.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE subscriptions
                SET status = $1, updated_at = CURRENT_TIMESTAMP
                WHERE stripe_subscription_id = $2
                """,
                status, subscription_id
            )
            
        logger.info(f"Subscription {subscription_id} updated to {status}")
        
    except Exception as e:
        logger.error(f"Error handling subscription updated: {e}")

async def handle_subscription_deleted(subscription):
    """Handle subscription cancellation"""
    try:
        subscription_id = subscription['id']
        customer_id = subscription['customer']
        
        async with db_service.pool.acquire() as conn:
            # Get user_id
            result = await conn.fetchrow(
                "SELECT user_id FROM subscriptions WHERE stripe_subscription_id = $1",
                subscription_id
            )
            
            if not result:
                logger.warning(f"No subscription found for {subscription_id}")
                return
            
            user_id = result['user_id']
            
            # Downgrade to free plan
            await conn.execute(
                """
                UPDATE user_limits
                SET 
                    plan_type = 'free',
                    fixes_limit = 1,
                    websites_max = 1,
                    exports_max = 5
                WHERE user_id = $1
                """,
                user_id
            )
            
            # Update subscription status
            await conn.execute(
                """
                UPDATE subscriptions
                SET status = 'canceled', updated_at = CURRENT_TIMESTAMP
                WHERE stripe_subscription_id = $1
                """,
                subscription_id
            )
            
        logger.info(f"User {user_id} downgraded to free (subscription canceled)")
        
    except Exception as e:
        logger.error(f"Error handling subscription deleted: {e}")

async def handle_payment_succeeded(invoice):
    """Handle successful payment"""
    try:
        subscription_id = invoice.get('subscription')
        
        if subscription_id:
            async with db_service.pool.acquire() as conn:
                await conn.execute(
                    """
                    UPDATE subscriptions
                    SET status = 'active', updated_at = CURRENT_TIMESTAMP
                    WHERE stripe_subscription_id = $1
                    """,
                    subscription_id
                )
                
        logger.info(f"Payment succeeded for subscription {subscription_id}")
        
    except Exception as e:
        logger.error(f"Error handling payment succeeded: {e}")

async def handle_payment_failed(invoice):
    """Handle failed payment"""
    try:
        subscription_id = invoice.get('subscription')
        
        if subscription_id:
            async with db_service.pool.acquire() as conn:
                await conn.execute(
                    """
                    UPDATE subscriptions
                    SET status = 'past_due', updated_at = CURRENT_TIMESTAMP
                    WHERE stripe_subscription_id = $1
                    """,
                    subscription_id
                )
                
        logger.warning(f"Payment failed for subscription {subscription_id}")
        
    except Exception as e:
        logger.error(f"Error handling payment failed: {e}")

