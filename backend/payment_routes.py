from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
import stripe
import os
import logging
from auth_routes import get_current_active_user, database

# Stripe konfigurieren
stripe.api_key = os.environ.get("STRIPE_API_KEY", "sk_test_your_test_key")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "whsec_your_webhook_secret")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "https://app.complyo.tech")

router = APIRouter()
logger = logging.getLogger("payment")

# Models
class PaymentIntent(BaseModel):
    subscription_tier: str
    payment_type: str = "subscription"  # subscription oder onetime

class CheckoutSession(BaseModel):
    session_id: str
    checkout_url: str

# Preis-IDs (erstellen Sie diese in Ihrem Stripe-Dashboard)
PRICE_IDS = {
    "basic": "price_basic_monthly",  # 39€/Monat für KI-Automatisierung
    "expert_setup": "price_expert_setup",  # 2000€ einmalig für Experten-Service
    "expert": "price_expert_monthly",  # 39€/Monat für Experten-Service
}

@router.post("/create-checkout-session", response_model=CheckoutSession)
async def create_checkout_session(
    payment_intent: PaymentIntent,
    current_user = Depends(get_current_active_user)
):
    """Erstellt eine Stripe-Checkout-Session für Abonnement oder Einmalzahlung"""
    
    # Benutzerdaten für Stripe-Kunde abrufen
    user_email = current_user["email"]
    user_id = current_user["id"]
    
    # Stripe-Kunde finden oder erstellen
    customers = stripe.Customer.list(email=user_email, limit=1)
    if customers.data:
        customer = customers.data[0]
    else:
        customer = stripe.Customer.create(
            email=user_email,
            metadata={"complyo_user_id": user_id}
        )
    
    # Line-Items basierend auf Abonnement-Stufe und Zahlungsart einrichten
    line_items = []
    
    if payment_intent.subscription_tier == "basic":
        # KI-Automatisierung: 39€/Monat
        line_items.append({
            "price": PRICE_IDS["basic"],
            "quantity": 1
        })
        mode = "subscription"
        
    elif payment_intent.subscription_tier == "expert":
        if payment_intent.payment_type == "subscription":
            # Experten-Service laufendes Abonnement: 39€/Monat
            line_items.append({
                "price": PRICE_IDS["expert"],
                "quantity": 1
            })
            mode = "subscription"
        else:
            # Experten-Service Einrichtungsgebühr: 2000€ einmalig
            line_items.append({
                "price": PRICE_IDS["expert_setup"],
                "quantity": 1
            })
            mode = "payment"
    
    else:
        raise HTTPException(status_code=400, detail="Ungültige Abonnement-Stufe")
    
    # Checkout-Session erstellen
    success_url = f"{FRONTEND_URL}/payment/success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{FRONTEND_URL}/payment/cancel"
    
    session = stripe.checkout.Session.create(
        customer=customer.id,
        payment_method_types=["card"],
        line_items=line_items,
        mode=mode,
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            "complyo_user_id": user_id,
            "subscription_tier": payment_intent.subscription_tier,
            "payment_type": payment_intent.payment_type
        }
    )
    
    return {"session_id": session.id, "checkout_url": session.url}

@router.get("/payment/verify/{session_id}")
async def verify_payment(
    session_id: str,
    current_user = Depends(get_current_active_user)
):
    """Überprüft eine Checkout-Session und aktualisiert das Benutzerabonnement, wenn bezahlt"""
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        
        # Überprüfen, ob die Session diesem Benutzer gehört
        if session.metadata.get("complyo_user_id") != current_user["id"]:
            raise HTTPException(status_code=403, detail="Unautorisierter Zugriff auf diese Zahlungssitzung")
        
        # Zahlungsstatus prüfen
        if session.payment_status != "paid":
            return {"status": "pending", "message": "Zahlung wurde noch nicht abgeschlossen"}
        
        # Benutzerabonnement basierend auf Zahlung aktualisieren
        subscription_tier = session.metadata.get("subscription_tier")
        
        query = """
        UPDATE users SET subscription_tier = :tier_id
        WHERE id = :user_id
        RETURNING id, email, subscription_tier
        """
        values = {"tier_id": subscription_tier, "user_id": current_user["id"]}
        
        result = await database.fetch_one(query=query, values=values)
        
        # Zusätzlichen Eintrag für Experten-Setup erstellen, falls zutreffend
        if subscription_tier == "expert" and session.metadata.get("payment_type") == "payment":
            # Experten-Setup-Zahlung in einer separaten Tabelle erfassen
            setup_query = """
            INSERT INTO expert_setups(user_id, payment_id, status)
            VALUES (:user_id, :payment_id, 'paid')
            """
            setup_values = {
                "user_id": current_user["id"],
                "payment_id": session.payment_intent
            }
            await database.execute(query=setup_query, values=setup_values)
            
            # TODO: Experten-Onboarding-Prozess auslösen
            # - Compliance-Team benachrichtigen
            # - Erstes Beratungsgespräch planen
            # - Kundendatensatz im CRM erstellen
        
        return {
            "status": "success",
            "message": "Zahlung erfolgreich und Abonnement aktualisiert",
            "subscription": {
                "tier": result["subscription_tier"],
                "user_id": result["id"]
            }
        }
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe-Fehler: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Stripe-Fehler: {str(e)}")

@router.post("/webhook")
async def stripe_webhook(request: Request, background_tasks: BackgroundTasks):
    """Behandelt Stripe-Webhook-Events"""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Ungültige Payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Ungültige Signatur")
    
    # Spezifische Event-Typen behandeln
    if event.type == "checkout.session.completed":
        session = event.data.object
        logger.info(f"Zahlung erfolgreich für Session {session.id}")
        
        # Benutzer-ID aus Metadaten abrufen
        complyo_user_id = session.metadata.get("complyo_user_id")
        if not complyo_user_id:
            logger.error(f"Keine Complyo-Benutzer-ID in Session {session.id} gefunden")
            return {"status": "error", "message": "Keine Benutzer-ID in Metadaten"}
        
        # Verarbeitung basierend auf Modus (Abonnement vs. Einmalzahlung)
        if session.mode == "subscription":
            # Abonnementzahlung - Abonnement-Updates werden durch subscription.updated behandelt
            logger.info(f"Abonnement erstellt für Benutzer {complyo_user_id}")
            
        elif session.mode == "payment":
            # Einmalzahlung für Experten-Setup
            tier = session.metadata.get("subscription_tier")
            if tier == "expert":
                # Benutzer-Stufe aktualisieren und Experten-Setup-Zahlung erfassen
                query = """
                UPDATE users SET subscription_tier = :tier_id
                WHERE id = :user_id
                """
                values = {"tier_id": tier, "user_id": complyo_user_id}
                background_tasks.add_task(database.execute, query=query, values=values)
                
                # Expert-Setup erfassen
                setup_query = """
                INSERT INTO expert_setups(user_id, payment_id, status)
                VALUES (:user_id, :payment_id, 'paid')
                ON CONFLICT (user_id) DO UPDATE SET 
                payment_id = :payment_id, status = 'paid'
                """
                setup_values = {
                    "user_id": complyo_user_id,
                    "payment_id": session.payment_intent
                }
                background_tasks.add_task(database.execute, query=setup_query, values=setup_values)
    
    return {"status": "success"}

# DB-Init-Funktion - rufen Sie diese auf, wenn Ihre App startet
async def init_db():
    # expert_setups-Tabelle erstellen, falls nicht vorhanden
    query = """
    CREATE TABLE IF NOT EXISTS expert_setups (
        user_id VARCHAR(50) PRIMARY KEY REFERENCES users(id),
        payment_id VARCHAR(100) NOT NULL,
        status VARCHAR(20) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    await database.execute(query=query)
