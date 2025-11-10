CREATE TABLE IF NOT EXISTS subscription_plans (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price_monthly DECIMAL(10,2),
    price_yearly DECIMAL(10,2),
    stripe_price_id_monthly VARCHAR(255),
    stripe_price_id_yearly VARCHAR(255),
    stripe_product_id VARCHAR(255),
    features JSONB,
    max_websites INTEGER,
    max_scans_per_month INTEGER,
    max_team_members INTEGER,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Insert default plans
INSERT INTO subscription_plans (
    name, description, 
    price_monthly, price_yearly,
    max_websites, max_scans_per_month, max_team_members,
    features
) VALUES
(
    'Kostenlose Analyse', 
    'Für erste Einschätzung',
    0, 0,
    1, 1, 1,
    '["Vollständiger Compliance-Scan", "Abmahnrisiko in Euro", "PDF-Report", "Handlungsempfehlungen"]'::jsonb
),
(
    'KI-Automatisierung',
    'Der intelligente Weg',
    39, 390,
    10, 100, 5,
    '["Automatische Rechtstexte", "24h-Umsetzungsgarantie", "Monatliche Re-Scans", "Live-Dashboard"]'::jsonb
),
(
    'Experten-Service',
    'Die Profi-Lösung',
    39, 390,
    999, 999, 999,
    '["Persönliche Anwalts-Betreuung", "Branchenspezifische Compliance", "Custom-Integration", "Quartalsweise Reviews", "Direkte Experten-Hotline"]'::jsonb
)
ON CONFLICT DO NOTHING;

