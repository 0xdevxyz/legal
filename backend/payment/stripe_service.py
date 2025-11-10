import os
import stripe
from typing import Optional, Dict, Any, List
from datetime import datetime
import asyncpg

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY")

class StripeService:
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
    
    async def create_customer(self, user_id: int, email: str, name: str) -> Dict[str, Any]:
        """Create a Stripe customer and save to database"""
        try:
            # Create Stripe customer
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata={"user_id": str(user_id)}
            )
            
            # Save to database
            async with self.db_pool.acquire() as connection:
                await connection.execute(
                    """
                    INSERT INTO stripe_customers (user_id, stripe_customer_id, email)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (user_id) DO UPDATE SET 
                        stripe_customer_id = $2,
                        email = $3,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    user_id, customer.id, email
                )
            
            return {"customer_id": customer.id, "success": True}
        except Exception as e:
            print(f"Error creating Stripe customer: {e}")
            raise
    
    async def get_or_create_customer(self, user_id: int, email: str, name: str) -> str:
        """Get existing Stripe customer or create new one"""
        async with self.db_pool.acquire() as connection:
            customer = await connection.fetchrow(
                "SELECT stripe_customer_id FROM stripe_customers WHERE user_id = $1",
                user_id
            )
            
            if customer:
                return customer['stripe_customer_id']
            else:
                result = await self.create_customer(user_id, email, name)
                return result['customer_id']
    
    async def create_checkout_session(
        self, 
        user_id: int, 
        price_id: str, 
        success_url: str, 
        cancel_url: str,
        email: str,
        name: str
    ) -> Dict[str, Any]:
        """Create a Stripe checkout session for subscription (legacy method)"""
        try:
            # Get or create customer
            customer_id = await self.get_or_create_customer(user_id, email, name)
            
            # Create checkout session
            checkout_session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=['card'],
                mode='subscription',
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    'user_id': str(user_id)
                }
            )
            
            return {
                "checkout_url": checkout_session.url,
                "session_id": checkout_session.id,
                "success": True
            }
        except Exception as e:
            print(f"Error creating checkout session: {e}")
            raise
    
    async def create_plan_checkout_session(
        self,
        user_id: int,
        plan_type: str,  # 'ki' oder 'expert'
        success_url: str,
        cancel_url: str
    ) -> Dict[str, Any]:
        """Create a Stripe checkout session for AI or Expert Plan"""
        try:
            # Get user info
            async with self.db_pool.acquire() as conn:
                user = await conn.fetchrow(
                    "SELECT email, full_name FROM users WHERE id = $1",
                    user_id
                )
            
            if not user:
                raise Exception("User not found")
            
            # Get or create customer
            customer_id = await self.get_or_create_customer(user_id, user['email'], user['full_name'])
            
            # Get plan from database
            async with self.db_pool.acquire() as conn:
                plan = await conn.fetchrow(
                    "SELECT * FROM subscription_plans WHERE plan_type = $1 AND is_active = TRUE",
                    plan_type
                )
            
            if not plan:
                raise Exception(f"Plan {plan_type} not found")
            
            # Create line items
            line_items = []
            mode = 'subscription'
            
            # Expert Plan: Add setup fee
            if plan_type == 'expert':
                # Get setup fee
                async with self.db_pool.acquire() as conn:
                    setup_fee = await conn.fetchrow(
                        "SELECT * FROM plan_setup_fees WHERE plan_id = $1",
                        plan['id']
                    )
                
                if setup_fee:
                    # One-time setup fee
                    line_items.append({
                        'price_data': {
                            'currency': 'eur',
                            'product_data': {
                                'name': 'Expert Plan Setup Fee',
                                'description': setup_fee.get('description', 'Einmalige Einrichtungsgebühr')
                            },
                            'unit_amount': int(setup_fee['amount'] * 100)  # Convert to cents
                        },
                        'quantity': 1
                    })
            
            # Monthly subscription
            line_items.append({
                'price': plan['stripe_price_id'],
                'quantity': 1
            })
            
            # Create checkout session
            session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=['card', 'sepa_debit'],
                line_items=line_items,
                mode=mode,
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    'user_id': str(user_id),
                    'plan_type': plan_type
                },
                subscription_data={
                    'metadata': {
                        'user_id': str(user_id),
                        'plan_type': plan_type
                    }
                } if mode == 'subscription' else None
            )
            
            return {
                'checkout_url': session.url,
                'session_id': session.id,
                'success': True
            }
        except Exception as e:
            print(f"Error creating plan checkout session: {e}")
            raise
    
    async def create_portal_session(self, user_id: int, return_url: str) -> Dict[str, Any]:
        """Create a customer portal session for subscription management"""
        try:
            async with self.db_pool.acquire() as connection:
                customer = await connection.fetchrow(
                    "SELECT stripe_customer_id FROM stripe_customers WHERE user_id = $1",
                    user_id
                )
                
                if not customer:
                    raise Exception("No Stripe customer found for user")
                
                # Create portal session
                portal_session = stripe.billing_portal.Session.create(
                    customer=customer['stripe_customer_id'],
                    return_url=return_url
                )
                
                return {
                    "portal_url": portal_session.url,
                    "success": True
                }
        except Exception as e:
            print(f"Error creating portal session: {e}")
            raise
    
    async def get_subscription_status(self, user_id: int) -> Dict[str, Any]:
        """Get current subscription status for a user"""
        try:
            async with self.db_pool.acquire() as connection:
                subscription = await connection.fetchrow(
                    """
                    SELECT s.*, sp.name as plan_name, sp.features
                    FROM subscriptions s
                    JOIN subscription_plans sp ON s.plan_id = sp.id
                    WHERE s.user_id = $1 AND s.status IN ('active', 'trialing')
                    ORDER BY s.created_at DESC
                    LIMIT 1
                    """,
                    user_id
                )
                
                if not subscription:
                    return {
                        "has_subscription": False,
                        "plan": "free",
                        "status": "inactive"
                    }
                
                return {
                    "has_subscription": True,
                    "subscription_id": subscription['stripe_subscription_id'],
                    "plan": subscription['plan_name'],
                    "plan_id": subscription['plan_id'],
                    "status": subscription['status'],
                    "features": subscription['features'],
                    "current_period_end": subscription['current_period_end'].isoformat() if subscription['current_period_end'] else None,
                    "cancel_at": subscription['cancel_at'].isoformat() if subscription['cancel_at'] else None
                }
        except Exception as e:
            print(f"Error getting subscription status: {e}")
            raise
    
    async def get_payment_history(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get payment history for a user"""
        try:
            async with self.db_pool.acquire() as connection:
                payments = await connection.fetch(
                    """
                    SELECT * FROM payment_history
                    WHERE user_id = $1
                    ORDER BY created_at DESC
                    LIMIT $2
                    """,
                    user_id, limit
                )
                
                return [{
                    "id": p['id'],
                    "amount": float(p['amount']),
                    "currency": p['currency'],
                    "status": p['status'],
                    "description": p['description'],
                    "created_at": p['created_at'].isoformat()
                } for p in payments]
        except Exception as e:
            print(f"Error getting payment history: {e}")
            raise
    
    async def handle_checkout_completed(self, session: Dict[str, Any]) -> None:
        """Handle successful checkout session"""
        try:
            user_id = int(session['metadata']['user_id'])
            customer_id = session['customer']
            subscription_id = session['subscription']
            
            # Get subscription details from Stripe
            subscription = stripe.Subscription.retrieve(subscription_id)
            
            # Save subscription to database
            async with self.db_pool.acquire() as connection:
                await connection.execute(
                    """
                    INSERT INTO subscriptions (
                        user_id, stripe_subscription_id, stripe_customer_id, 
                        plan_id, status, current_period_start, current_period_end
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                    ON CONFLICT (stripe_subscription_id) DO UPDATE SET
                        status = $5,
                        current_period_start = $6,
                        current_period_end = $7,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    user_id,
                    subscription_id,
                    customer_id,
                    subscription['items']['data'][0]['price']['id'],
                    subscription['status'],
                    datetime.fromtimestamp(subscription['current_period_start']),
                    datetime.fromtimestamp(subscription['current_period_end'])
                )
                
                # Update user plan
                await connection.execute(
                    """
                    UPDATE users 
                    SET plan = (
                        SELECT name FROM subscription_plans 
                        WHERE id = $2
                    )
                    WHERE id = $1
                    """,
                    user_id, subscription['items']['data'][0]['price']['id']
                )
        except Exception as e:
            print(f"Error handling checkout completed: {e}")
            raise
    
    async def handle_subscription_updated(self, subscription: Dict[str, Any]) -> None:
        """Handle subscription update events"""
        try:
            async with self.db_pool.acquire() as connection:
                # Update subscription in database
                await connection.execute(
                    """
                    UPDATE subscriptions SET
                        status = $2,
                        plan_id = $3,
                        current_period_start = $4,
                        current_period_end = $5,
                        cancel_at = $6,
                        canceled_at = $7,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE stripe_subscription_id = $1
                    """,
                    subscription['id'],
                    subscription['status'],
                    subscription['items']['data'][0]['price']['id'],
                    datetime.fromtimestamp(subscription['current_period_start']),
                    datetime.fromtimestamp(subscription['current_period_end']),
                    datetime.fromtimestamp(subscription['cancel_at']) if subscription.get('cancel_at') else None,
                    datetime.fromtimestamp(subscription['canceled_at']) if subscription.get('canceled_at') else None
                )
                
                # Get user_id
                sub_record = await connection.fetchrow(
                    "SELECT user_id FROM subscriptions WHERE stripe_subscription_id = $1",
                    subscription['id']
                )
                
                if sub_record:
                    # Update user plan based on subscription status
                    if subscription['status'] in ['canceled', 'unpaid']:
                        plan_name = 'free'
                    else:
                        plan_record = await connection.fetchrow(
                            "SELECT name FROM subscription_plans WHERE id = $1",
                            subscription['items']['data'][0]['price']['id']
                        )
                        plan_name = plan_record['name'] if plan_record else 'free'
                    
                    await connection.execute(
                        "UPDATE users SET plan = $2 WHERE id = $1",
                        sub_record['user_id'], plan_name
                    )
        except Exception as e:
            print(f"Error handling subscription update: {e}")
            raise
    
    async def handle_invoice_paid(self, invoice: Dict[str, Any]) -> None:
        """Handle successful invoice payment"""
        try:
            async with self.db_pool.acquire() as connection:
                # Get user_id from customer
                customer = await connection.fetchrow(
                    "SELECT user_id FROM stripe_customers WHERE stripe_customer_id = $1",
                    invoice['customer']
                )
                
                if customer:
                    # Save payment record
                    await connection.execute(
                        """
                        INSERT INTO payment_history (
                            user_id, stripe_invoice_id, amount, currency, 
                            status, description, payment_method_type
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                        """,
                        customer['user_id'],
                        invoice['id'],
                        invoice['amount_paid'] / 100,  # Convert from cents
                        invoice['currency'],
                        'succeeded',
                        f"Subscription payment - {invoice['lines']['data'][0]['description']}",
                        'card'
                    )
        except Exception as e:
            print(f"Error handling invoice payment: {e}")
            raise
    
    async def get_available_plans(self) -> List[Dict[str, Any]]:
        """Get all available subscription plans with setup fees"""
        try:
            async with self.db_pool.acquire() as connection:
                plans = await connection.fetch(
                    """
                    SELECT 
                        sp.*,
                        COALESCE(psf.setup_fee, 0) as setup_fee,
                        psf.setup_fee_description
                    FROM subscription_plans sp
                    LEFT JOIN plan_setup_fees psf ON sp.id = psf.plan_id
                    WHERE sp.is_active = TRUE 
                    ORDER BY sp.price_monthly ASC NULLS LAST
                    """
                )
                
                return [{
                    "id": p['id'],
                    "product_id": p['stripe_product_id'],
                    "name": p['name'],
                    "description": p['description'],
                    "price_monthly": float(p['price_monthly']) if p['price_monthly'] else None,
                    "price_yearly": float(p['price_yearly']) if p['price_yearly'] else None,
                    "setup_fee": float(p['setup_fee']) if p['setup_fee'] else 0,
                    "setup_fee_description": p['setup_fee_description'],
                    "features": p['features'],
                    "is_annual": p['price_yearly'] is not None and p['price_monthly'] is None
                } for p in plans]
        except Exception as e:
            print(f"Error getting available plans: {e}")
            raise