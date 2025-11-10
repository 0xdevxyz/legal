import os
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from typing import Dict, Any
import stripe
import logging
import uuid

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/payment", tags=["Payment"])

# Global references (set in main_production.py)
stripe_service = None
db_pool = None
auth_service = None

# Development Mode für Zahlungssimulation
DEV_MODE = os.getenv("DEV_MODE", "false").lower() in ("true", "1", "yes")
BYPASS_PAYMENT = os.getenv("BYPASS_PAYMENT", "false").lower() in ("true", "1", "yes")

# Environment variables
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://app.complyo.tech")

logger.info(f"🔧 Payment Routes - DEV_MODE: {DEV_MODE}, BYPASS_PAYMENT: {BYPASS_PAYMENT}")

class CreateCheckoutRequest(BaseModel):
    plan_type: str  # 'ki' oder 'expert'

class CheckoutResponse(BaseModel):
    checkout_url: str
    session_id: str

async def get_current_user_from_auth_header(request: Request):
    """Get current user from Authorization header"""
    from auth_routes import get_current_user, security
    from fastapi.security import HTTPAuthorizationCredentials
    
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized"
        )
    
    token = auth_header.replace('Bearer ', '')
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    return await get_current_user(credentials)

@router.post("/create-checkout", response_model=CheckoutResponse)
async def create_checkout(
    request: Request,
    data: CreateCheckoutRequest
):
    """
    Create Stripe checkout session for AI or Expert Plan
    Im DEV_MODE: Simuliert erfolgreiche Zahlung ohne echten Stripe-Call
    """
    try:
        # Get current user
        current_user = await get_current_user_from_auth_header(request)
        user_id = current_user['id']
        
        # 🚀 DEV MODE: Simuliere Zahlung und aktiviere direkt
        if DEV_MODE or BYPASS_PAYMENT:
            logger.warning(f"⚠️ DEV_MODE: Simuliere Zahlung für User {user_id}, Plan {data.plan_type}")
            
            # Generiere Mock Session ID
            mock_session_id = f"cs_test_dev_{uuid.uuid4().hex[:24]}"
            mock_subscription_id = f"sub_dev_{uuid.uuid4().hex[:24]}"
            
            # Upgrade User direkt in der Datenbank
            async with db_pool.acquire() as conn:
                # Create or update subscription record
                await conn.execute(
                    """
                    INSERT INTO subscriptions (
                        user_id, plan_id, stripe_subscription_id,
                        status, start_date, money_back_guarantee_end_date
                    )
                    VALUES (
                        $1, $2, $3, 'active', CURRENT_TIMESTAMP,
                        CURRENT_TIMESTAMP + INTERVAL '14 days'
                    )
                    ON CONFLICT (user_id) DO UPDATE
                    SET plan_id = $2,
                        stripe_subscription_id = $3,
                        status = 'active',
                        start_date = CURRENT_TIMESTAMP,
                        money_back_guarantee_end_date = CURRENT_TIMESTAMP + INTERVAL '14 days',
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    user_id, data.plan_type, mock_subscription_id
                )
                
                # Update user_limits
                websites_max = 1
                exports_max = -1 if data.plan_type == 'expert' else 10
                
                await conn.execute(
                    """
                    UPDATE user_limits
                    SET plan_type = $1,
                        websites_max = $2,
                        exports_max = $3,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = $4
                    """,
                    data.plan_type, websites_max, exports_max, user_id
                )
                
                logger.info(f"✅ DEV_MODE: Subscription activated for user {user_id}, plan {data.plan_type}")
            
            # Redirect direkt zur Success-URL
            success_url = f"{FRONTEND_URL}/dashboard?payment=success&session_id={mock_session_id}&dev_mode=true"
            
            return CheckoutResponse(
                checkout_url=success_url,
                session_id=mock_session_id
            )
        
        # ✅ PRODUCTION MODE: Echter Stripe Checkout
        # Create checkout session
        session = await stripe_service.create_plan_checkout_session(
            user_id=user_id,
            plan_type=data.plan_type,
            success_url=f"{FRONTEND_URL}/dashboard?payment=success&session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{FRONTEND_URL}/subscription?payment=cancelled"
        )
        
        return CheckoutResponse(
            checkout_url=session['checkout_url'],
            session_id=session['session_id']
        )
    except Exception as e:
        logger.error(f"Checkout creation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fehler beim Erstellen der Checkout-Session"
        )

@router.post("/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks"""
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
    logger.info(f"Received Stripe webhook: {event_type}")
    
    if event_type == 'checkout.session.completed':
        await handle_checkout_completed(event['data']['object'])
    elif event_type == 'customer.subscription.updated':
        await handle_subscription_updated(event['data']['object'])
    elif event_type == 'customer.subscription.deleted':
        await handle_subscription_cancelled(event['data']['object'])
    elif event_type == 'invoice.payment_failed':
        await handle_payment_failed(event['data']['object'])
    else:
        logger.info(f"Unhandled event type: {event_type}")
    
    return {"status": "success"}

async def handle_checkout_completed(session):
    """Handle successful checkout"""
    user_id = int(session['metadata']['user_id'])
    plan_type = session['metadata']['plan_type']
    subscription_id = session.get('subscription')
    
    logger.info(f"Checkout completed for user {user_id}, plan {plan_type}")
    
    try:
        async with db_pool.acquire() as conn:
            # Create or update subscription record
            await conn.execute(
                """
                INSERT INTO subscriptions (
                    user_id, plan_id, stripe_subscription_id,
                    status, start_date, money_back_guarantee_end_date
                )
                VALUES (
                    $1, $2, $3, 'active', CURRENT_TIMESTAMP,
                    CURRENT_TIMESTAMP + INTERVAL '14 days'
                )
                ON CONFLICT (user_id) DO UPDATE
                SET plan_id = $2,
                    stripe_subscription_id = $3,
                    status = 'active',
                    start_date = CURRENT_TIMESTAMP,
                    money_back_guarantee_end_date = CURRENT_TIMESTAMP + INTERVAL '14 days',
                    updated_at = CURRENT_TIMESTAMP
                """,
                user_id, plan_type, subscription_id
            )
            
            # Update user_limits
            websites_max = 1
            exports_max = -1 if plan_type == 'expert' else 10
            
            await conn.execute(
                """
                UPDATE user_limits
                SET plan_type = $1,
                    websites_max = $2,
                    exports_max = $3,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = $4
                """,
                plan_type, websites_max, exports_max, user_id
            )
            
            logger.info(f"Subscription activated for user {user_id}")
    except Exception as e:
        logger.error(f"Error handling checkout completed: {e}")
        raise

async def handle_subscription_updated(subscription):
    """Handle subscription updates"""
    try:
        user_id = int(subscription['metadata'].get('user_id', 0))
        if not user_id:
            logger.warning("No user_id in subscription metadata")
            return
        
        status = subscription['status']
        
        async with db_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE subscriptions
                SET status = $1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE stripe_subscription_id = $2
                """,
                status, subscription['id']
            )
        
        logger.info(f"Subscription updated for user {user_id}: {status}")
    except Exception as e:
        logger.error(f"Error handling subscription update: {e}")

async def handle_subscription_cancelled(subscription):
    """Handle subscription cancellation"""
    try:
        user_id = int(subscription['metadata'].get('user_id', 0))
        if not user_id:
            logger.warning("No user_id in subscription metadata")
            return
        
        async with db_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE subscriptions
                SET status = 'cancelled',
                    end_date = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE stripe_subscription_id = $1
                """,
                subscription['id']
            )
            
            # Reset user limits to free tier
            await conn.execute(
                """
                UPDATE user_limits
                SET plan_type = 'free',
                    websites_max = 0,
                    exports_max = 0,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = $1
                """,
                user_id
            )
        
        logger.info(f"Subscription cancelled for user {user_id}")
    except Exception as e:
        logger.error(f"Error handling subscription cancellation: {e}")

async def handle_payment_failed(invoice):
    """Handle failed payment"""
    try:
        subscription_id = invoice.get('subscription')
        if not subscription_id:
            return
        
        async with db_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE subscriptions
                SET status = 'past_due',
                    updated_at = CURRENT_TIMESTAMP
                WHERE stripe_subscription_id = $1
                """,
                subscription_id
            )
        
        logger.warning(f"Payment failed for subscription {subscription_id}")
    except Exception as e:
        logger.error(f"Error handling payment failure: {e}")

@router.get("/subscription-status")
async def get_subscription_status(request: Request):
    """Get current user's subscription status"""
    try:
        current_user = await get_current_user_from_auth_header(request)
        user_id = current_user['id']
        
        status = await stripe_service.get_subscription_status(user_id)
        return status
    except Exception as e:
        logger.error(f"Error getting subscription status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fehler beim Abrufen des Subscription-Status"
        )

@router.get("/health")
async def payment_health():
    """Health check for payment service"""
    return {
        "status": "healthy",
        "service": "payment",
        "stripe_service_initialized": stripe_service is not None,
        "webhook_secret_configured": STRIPE_WEBHOOK_SECRET is not None
    }
