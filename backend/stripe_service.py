"""
Stripe Payment Service für Complyo
Handles subscriptions und one-time payments
"""
import stripe
import os
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from fastapi import HTTPException, Request
from pydantic import BaseModel

# Stripe Configuration
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "sk_test_...")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "whsec_...")

# Product IDs (diese würden in production aus Stripe geholt)
PRODUCTS = {
    "ai_automation": {
        "name": "AI Automation",
        "price_monthly": 3900,  # 39€ in cents
        "stripe_price_id": "price_ai_automation_monthly",
        "features": [
            "KI-gestützte Compliance-Checks",
            "Automatische Dokument-Generierung", 
            "24/7 Monitoring",
            "E-Mail Support"
        ]
    },
    "expert_service": {
        "name": "Expert Service",
        "price_onetime": 200000,  # 2000€ in cents
        "price_monthly": 3900,   # 39€ in cents  
        "stripe_price_onetime": "price_expert_setup",
        "stripe_price_monthly": "price_expert_monthly",
        "features": [
            "Alles aus AI Automation",
            "Persönliche Rechtsberatung",
            "Manuelle Compliance-Prüfung", 
            "Telefon & Video Support",
            "Abmahn-Versicherung inklusive"
        ]
    }
}

class PaymentRequest(BaseModel):
    product_type: str  # "ai_automation" or "expert_service"
    customer_email: str
    customer_name: str
    company_name: Optional[str] = None
    success_url: str
    cancel_url: str

class SubscriptionInfo(BaseModel):
    subscription_id: str
    customer_id: str
    status: str
    current_period_start: datetime
    current_period_end: datetime
    plan_name: str
    amount: int

class StripeService:
    
    def __init__(self):
        self.stripe = stripe
        
    async def create_checkout_session(self, payment_request: PaymentRequest) -> Dict:
        """Create Stripe Checkout Session für Subscription oder One-time Payment"""
        
        try:
            product = PRODUCTS.get(payment_request.product_type)
            if not product:
                raise HTTPException(status_code=400, detail="Invalid product type")
            
            # Create or get customer
            customer = await self._get_or_create_customer(
                payment_request.customer_email,
                payment_request.customer_name,
                payment_request.company_name
            )
            
            # Determine line items based on product type
            line_items = []
            
            if payment_request.product_type == "ai_automation":
                # Monthly subscription only
                line_items.append({
                    'price': product["stripe_price_id"],
                    'quantity': 1,
                })
                mode = "subscription"
                
            elif payment_request.product_type == "expert_service":
                # One-time setup + monthly subscription
                line_items.extend([
                    {
                        'price': product["stripe_price_onetime"],
                        'quantity': 1,
                    },
                    {
                        'price': product["stripe_price_monthly"], 
                        'quantity': 1,
                    }
                ])
                mode = "subscription"
            
            # Create checkout session
            session = stripe.checkout.Session.create(
                customer=customer.id,
                payment_method_types=['card', 'sepa_debit'],
                line_items=line_items,
                mode=mode,
                success_url=payment_request.success_url + "?session_id={CHECKOUT_SESSION_ID}",
                cancel_url=payment_request.cancel_url,
                automatic_tax={'enabled': True},
                tax_id_collection={'enabled': True},
                customer_update={
                    'address': 'auto',
                    'name': 'auto'
                },
                invoice_creation={'enabled': True},
                metadata={
                    'product_type': payment_request.product_type,
                    'company_name': payment_request.company_name or '',
                }
            )
            
            return {
                "session_id": session.id,
                "session_url": session.url,
                "customer_id": customer.id,
                "product_type": payment_request.product_type,
                "amount": sum([item.get('amount', 0) for item in line_items])
            }
            
        except stripe.error.StripeError as e:
            raise HTTPException(status_code=400, detail=f"Stripe error: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
    
    async def _get_or_create_customer(self, email: str, name: str, company_name: Optional[str]) -> stripe.Customer:
        """Get existing customer or create new one"""
        
        # Search for existing customer
        customers = stripe.Customer.list(email=email, limit=1)
        
        if customers.data:
            customer = customers.data[0]
            # Update customer info if needed
            stripe.Customer.modify(
                customer.id,
                name=name,
                metadata={'company_name': company_name or ''}
            )
            return customer
        else:
            # Create new customer
            return stripe.Customer.create(
                email=email,
                name=name,
                metadata={'company_name': company_name or ''}
            )
    
    async def get_subscription_info(self, customer_id: str) -> Optional[SubscriptionInfo]:
        """Get active subscription info for customer"""
        
        try:
            subscriptions = stripe.Subscription.list(
                customer=customer_id,
                status='active',
                limit=1
            )
            
            if not subscriptions.data:
                return None
                
            sub = subscriptions.data[0]
            
            return SubscriptionInfo(
                subscription_id=sub.id,
                customer_id=sub.customer,
                status=sub.status,
                current_period_start=datetime.fromtimestamp(sub.current_period_start),
                current_period_end=datetime.fromtimestamp(sub.current_period_end),
                plan_name=sub.items.data[0].price.nickname or "Unknown Plan",
                amount=sub.items.data[0].price.unit_amount
            )
            
        except stripe.error.StripeError as e:
            raise HTTPException(status_code=400, detail=f"Stripe error: {str(e)}")
    
    async def cancel_subscription(self, subscription_id: str) -> Dict:
        """Cancel subscription at period end"""
        
        try:
            subscription = stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=True
            )
            
            return {
                "subscription_id": subscription.id,
                "status": subscription.status,
                "cancel_at_period_end": subscription.cancel_at_period_end,
                "current_period_end": datetime.fromtimestamp(subscription.current_period_end)
            }
            
        except stripe.error.StripeError as e:
            raise HTTPException(status_code=400, detail=f"Stripe error: {str(e)}")
    
    async def reactivate_subscription(self, subscription_id: str) -> Dict:
        """Reactivate cancelled subscription"""
        
        try:
            subscription = stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=False
            )
            
            return {
                "subscription_id": subscription.id,
                "status": subscription.status,
                "cancel_at_period_end": subscription.cancel_at_period_end
            }
            
        except stripe.error.StripeError as e:
            raise HTTPException(status_code=400, detail=f"Stripe error: {str(e)}")
    
    async def handle_webhook(self, request: Request, signature: str) -> Dict:
        """Handle Stripe webhook events"""
        
        try:
            body = await request.body()
            event = stripe.Webhook.construct_event(
                body, signature, STRIPE_WEBHOOK_SECRET
            )
            
            if event['type'] == 'checkout.session.completed':
                session = event['data']['object']
                await self._handle_successful_payment(session)
                
            elif event['type'] == 'customer.subscription.created':
                subscription = event['data']['object']
                await self._handle_subscription_created(subscription)
                
            elif event['type'] == 'customer.subscription.updated':
                subscription = event['data']['object']
                await self._handle_subscription_updated(subscription)
                
            elif event['type'] == 'customer.subscription.deleted':
                subscription = event['data']['object']
                await self._handle_subscription_cancelled(subscription)
                
            elif event['type'] == 'invoice.payment_succeeded':
                invoice = event['data']['object']
                await self._handle_payment_succeeded(invoice)
                
            elif event['type'] == 'invoice.payment_failed':
                invoice = event['data']['object']
                await self._handle_payment_failed(invoice)
            
            return {"status": "success", "event_type": event['type']}
            
        except ValueError as e:
            raise HTTPException(status_code=400, detail="Invalid payload")
        except stripe.error.SignatureVerificationError as e:
            raise HTTPException(status_code=400, detail="Invalid signature")
    
    async def _handle_successful_payment(self, session):
        """Handle successful checkout session"""
        print(f"✅ Payment successful for session {session['id']}")
        # Hier würden wir den User Account aktivieren
        # await activate_user_account(session['customer'])
    
    async def _handle_subscription_created(self, subscription):
        """Handle new subscription"""
        print(f"🔄 New subscription created: {subscription['id']}")
        # Hier würden wir Subscription in DB speichern
        # await save_subscription_to_db(subscription)
    
    async def _handle_subscription_updated(self, subscription):
        """Handle subscription updates"""
        print(f"📝 Subscription updated: {subscription['id']}")
        # Hier würden wir Subscription in DB aktualisieren
    
    async def _handle_subscription_cancelled(self, subscription):
        """Handle subscription cancellation"""
        print(f"❌ Subscription cancelled: {subscription['id']}")
        # Hier würden wir Account deaktivieren
    
    async def _handle_payment_succeeded(self, invoice):
        """Handle successful recurring payment"""
        print(f"💰 Payment succeeded for invoice {invoice['id']}")
        # Hier würden wir Account Status verlängern
    
    async def _handle_payment_failed(self, invoice):
        """Handle failed payment"""
        print(f"⚠️ Payment failed for invoice {invoice['id']}")
        # Hier würden wir User benachrichtigen

# Global instance
stripe_service = StripeService()