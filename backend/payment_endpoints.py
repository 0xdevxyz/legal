"""
Payment API Endpoints für Complyo
Stripe Integration für Subscriptions
"""
from fastapi import APIRouter, HTTPException, Request, Header, Depends
from typing import Optional
from stripe_service import stripe_service, PaymentRequest, SubscriptionInfo

router = APIRouter(prefix="/api/payments", tags=["payments"])

@router.post("/create-checkout-session")
async def create_checkout_session(payment_request: PaymentRequest):
    """
    Create Stripe Checkout Session für AI Automation oder Expert Service
    
    Body:
    - product_type: "ai_automation" oder "expert_service"  
    - customer_email: E-Mail des Kunden
    - customer_name: Name des Kunden
    - company_name: Firmenname (optional)
    - success_url: URL nach erfolgreichem Payment
    - cancel_url: URL bei abgebrochenem Payment
    """
    return await stripe_service.create_checkout_session(payment_request)

@router.get("/subscription/{customer_id}")
async def get_subscription_info(customer_id: str) -> Optional[SubscriptionInfo]:
    """
    Get active subscription information für einen Kunden
    """
    return await stripe_service.get_subscription_info(customer_id)

@router.post("/cancel-subscription/{subscription_id}")
async def cancel_subscription(subscription_id: str):
    """
    Cancel subscription at period end
    """
    return await stripe_service.cancel_subscription(subscription_id)

@router.post("/reactivate-subscription/{subscription_id}")
async def reactivate_subscription(subscription_id: str):
    """
    Reactivate cancelled subscription
    """
    return await stripe_service.reactivate_subscription(subscription_id)

@router.post("/webhook")
async def stripe_webhook(request: Request, stripe_signature: str = Header(None, alias="stripe-signature")):
    """
    Stripe Webhook Handler
    Receives events from Stripe when payments succeed/fail
    """
    if not stripe_signature:
        raise HTTPException(status_code=400, detail="Missing stripe-signature header")
    
    return await stripe_service.handle_webhook(request, stripe_signature)

@router.get("/products")
async def get_products():
    """
    Get available products and pricing
    """
    from stripe_service import PRODUCTS
    
    return {
        "products": PRODUCTS,
        "currency": "EUR",
        "tax_included": False
    }