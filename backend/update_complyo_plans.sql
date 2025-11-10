-- Complyo Subscription Plans Update
-- Entfernt Test-Pläne und erstellt die echten Complyo-Pläne

-- Alte Test-Pläne entfernen
DELETE FROM subscription_plans;

-- AI Plan (39€ netto/Monat)
INSERT INTO subscription_plans (
    id, 
    stripe_product_id, 
    name, 
    description, 
    price_monthly, 
    price_yearly, 
    features, 
    is_active
) VALUES (
    'price_ai_monthly',
    'prod_complyo_ai',
    'AI Plan',
    'Automatische Compliance-Prüfung mit KI-Unterstützung',
    39.00,
    39.00,
    '["Automatische DSGVO-Prüfung", "KI-basierte Analyse", "Monatliche Reports", "E-Mail-Support", "Bis zu 5 Websites", "Compliance-Dashboard"]'::json,
    true
);

-- Expert Plan (2.000€ einmalig + 39€/Monat)
-- Hinweis: Stripe unterstützt keine Kombination aus Einmalzahlung + Abo in einem Produkt
-- Lösung: Zwei separate Stripe-Produkte oder Custom Checkout Flow
-- Variante 1: Nur monatliche Zahlung (Expert Service wird separat abgerechnet)
INSERT INTO subscription_plans (
    id, 
    stripe_product_id, 
    name, 
    description, 
    price_monthly, 
    price_yearly, 
    features, 
    is_active
) VALUES (
    'price_expert_monthly',
    'prod_complyo_expert',
    'Expert Plan',
    'Persönliche Beratung + KI-Analyse (2.000€ Setup-Gebühr + 39€/Monat)',
    39.00,
    39.00,
    '["Alle AI-Plan Features", "Persönlicher Compliance-Berater", "Individuelle Beratung", "Setup & Onboarding (2.000€ einmalig)", "Prioritäts-Support", "Unbegrenzte Websites", "Quarterly Review Calls", "Custom Compliance-Lösungen"]'::json,
    true
);

-- Metadaten-Tabelle für einmalige Setup-Gebühren (für Expert Plan)
CREATE TABLE IF NOT EXISTS plan_setup_fees (
    plan_id VARCHAR(255) PRIMARY KEY REFERENCES subscription_plans(id),
    setup_fee DECIMAL(10,2) NOT NULL,
    setup_fee_description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Setup-Gebühr für Expert Plan
INSERT INTO plan_setup_fees (plan_id, setup_fee, setup_fee_description)
VALUES (
    'price_expert_monthly',
    2000.00,
    'Einmalige Setup- und Onboarding-Gebühr für persönliche Beratung'
)
ON CONFLICT (plan_id) DO UPDATE SET
    setup_fee = EXCLUDED.setup_fee,
    setup_fee_description = EXCLUDED.setup_fee_description;

-- Bestätigung
SELECT 
    sp.id,
    sp.name,
    sp.price_monthly,
    COALESCE(psf.setup_fee, 0) as setup_fee,
    sp.description
FROM subscription_plans sp
LEFT JOIN plan_setup_fees psf ON sp.id = psf.plan_id
WHERE sp.is_active = true
ORDER BY sp.price_monthly;

