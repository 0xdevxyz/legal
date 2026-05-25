CREATE TABLE IF NOT EXISTS subscription_plans (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
(
    'Expertenservice',
    'Komplette Überarbeitung durch Complyo — einmalige Zahlung',
    0, 3990,
    1, 999, 1,
    '["Vollständige Umsetzung durch Complyo", "WCAG 2.1 AA Zertifizierung", "Cookie-Banner Setup", "Rechtstexte erstellt", "Persönlicher Ansprechpartner"]'::jsonb
),
(
    'Updateservice',
    'Laufende Updates nach Expertenservice — monatlich kündbar',
    29, 0,
    1, 999, 1,
    '["Automatische Compliance-Updates", "Gesetzesänderungen werden umgesetzt", "Monatliche Scans", "Priority Support"]'::jsonb
) NOT NULL,
    description TEXT,
    price_monthly DECIMAL(10,2),
(
    'Expertenservice',
    'Komplette Überarbeitung durch Complyo — einmalige Zahlung',
    0, 3990,
    1, 999, 1,
    '["Vollständige Umsetzung durch Complyo", "WCAG 2.1 AA Zertifizierung", "Cookie-Banner Setup", "Rechtstexte erstellt", "Persönlicher Ansprechpartner"]'::jsonb
),
(
    'Updateservice',
    'Laufende Updates nach Expertenservice — monatlich kündbar',
    29, 0,
    1, 999, 1,
    '["Automatische Compliance-Updates", "Gesetzesänderungen werden umgesetzt", "Monatliche Scans", "Priority Support"]'::jsonb
),
    price_yearly DECIMAL(10,2),
(
    'Expertenservice',
    'Komplette Überarbeitung durch Complyo — einmalige Zahlung',
    0, 3990,
    1, 999, 1,
    '["Vollständige Umsetzung durch Complyo", "WCAG 2.1 AA Zertifizierung", "Cookie-Banner Setup", "Rechtstexte erstellt", "Persönlicher Ansprechpartner"]'::jsonb
),
(
    'Updateservice',
    'Laufende Updates nach Expertenservice — monatlich kündbar',
    29, 0,
    1, 999, 1,
    '["Automatische Compliance-Updates", "Gesetzesänderungen werden umgesetzt", "Monatliche Scans", "Priority Support"]'::jsonb
),
    stripe_price_id_monthly VARCHAR(255),
(
    'Expertenservice',
    'Komplette Überarbeitung durch Complyo — einmalige Zahlung',
    0, 3990,
    1, 999, 1,
    '["Vollständige Umsetzung durch Complyo", "WCAG 2.1 AA Zertifizierung", "Cookie-Banner Setup", "Rechtstexte erstellt", "Persönlicher Ansprechpartner"]'::jsonb
),
(
    'Updateservice',
    'Laufende Updates nach Expertenservice — monatlich kündbar',
    29, 0,
    1, 999, 1,
    '["Automatische Compliance-Updates", "Gesetzesänderungen werden umgesetzt", "Monatliche Scans", "Priority Support"]'::jsonb
),
    stripe_price_id_yearly VARCHAR(255),
(
    'Expertenservice',
    'Komplette Überarbeitung durch Complyo — einmalige Zahlung',
    0, 3990,
    1, 999, 1,
    '["Vollständige Umsetzung durch Complyo", "WCAG 2.1 AA Zertifizierung", "Cookie-Banner Setup", "Rechtstexte erstellt", "Persönlicher Ansprechpartner"]'::jsonb
),
(
    'Updateservice',
    'Laufende Updates nach Expertenservice — monatlich kündbar',
    29, 0,
    1, 999, 1,
    '["Automatische Compliance-Updates", "Gesetzesänderungen werden umgesetzt", "Monatliche Scans", "Priority Support"]'::jsonb
),
    stripe_product_id VARCHAR(255),
(
    'Expertenservice',
    'Komplette Überarbeitung durch Complyo — einmalige Zahlung',
    0, 3990,
    1, 999, 1,
    '["Vollständige Umsetzung durch Complyo", "WCAG 2.1 AA Zertifizierung", "Cookie-Banner Setup", "Rechtstexte erstellt", "Persönlicher Ansprechpartner"]'::jsonb
),
(
    'Updateservice',
    'Laufende Updates nach Expertenservice — monatlich kündbar',
    29, 0,
    1, 999, 1,
    '["Automatische Compliance-Updates", "Gesetzesänderungen werden umgesetzt", "Monatliche Scans", "Priority Support"]'::jsonb
),
    features JSONB,
    max_websites INTEGER,
    max_scans_per_month INTEGER,
    max_team_members INTEGER,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
),
(
    'Expertenservice',
    'Komplette Überarbeitung durch Complyo — einmalige Zahlung',
    0, 3990,
    1, 999, 1,
    '["Vollständige Umsetzung durch Complyo", "WCAG 2.1 AA Zertifizierung", "Cookie-Banner Setup", "Rechtstexte erstellt", "Persönlicher Ansprechpartner"]'::jsonb
),
(
    'Updateservice',
    'Laufende Updates nach Expertenservice — monatlich kündbar',
    29, 0,
    1, 999, 1,
    '["Automatische Compliance-Updates", "Gesetzesänderungen werden umgesetzt", "Monatliche Scans", "Priority Support"]'::jsonb
);

-- Insert default plans
INSERT INTO subscription_plans (
    name, description, 
    price_monthly, price_yearly,
    max_websites, max_scans_per_month, max_team_members,
    features
),
(
    'Expertenservice',
    'Komplette Überarbeitung durch Complyo — einmalige Zahlung',
    0, 3990,
    1, 999, 1,
    '["Vollständige Umsetzung durch Complyo", "WCAG 2.1 AA Zertifizierung", "Cookie-Banner Setup", "Rechtstexte erstellt", "Persönlicher Ansprechpartner"]'::jsonb
),
(
    'Updateservice',
    'Laufende Updates nach Expertenservice — monatlich kündbar',
    29, 0,
    1, 999, 1,
    '["Automatische Compliance-Updates", "Gesetzesänderungen werden umgesetzt", "Monatliche Scans", "Priority Support"]'::jsonb
) VALUES
(
    'Kostenlos', 
    '1 Domain, 1 Fix — zum Kennenlernen',
    0, 0,
    1, 1, 1,
    '["Vollständiger Compliance-Scan", "Abmahnrisiko in Euro", "1 automatischer Fix", "Handlungsempfehlungen"]'::jsonb
),
(
    'Expertenservice',
    'Komplette Überarbeitung durch Complyo — einmalige Zahlung',
    0, 3990,
    1, 999, 1,
    '["Vollständige Umsetzung durch Complyo", "WCAG 2.1 AA Zertifizierung", "Cookie-Banner Setup", "Rechtstexte erstellt", "Persönlicher Ansprechpartner"]'::jsonb
),
(
    'Updateservice',
    'Laufende Updates nach Expertenservice — monatlich kündbar',
    29, 0,
    1, 999, 1,
    '["Automatische Compliance-Updates", "Gesetzesänderungen werden umgesetzt", "Monatliche Scans", "Priority Support"]'::jsonb
),
(
    'Einzelne Säule',
    '1 Compliance-Bereich nach Wahl',
    19, 0,
    1, 50, 1,
    '["1 Bereich: Cookie ODER Barrierefreiheit ODER Rechtliche Texte ODER Monitoring", "Automatische Fixes", "E-Mail Support"]'::jsonb
),
(
    'Expertenservice',
    'Komplette Überarbeitung durch Complyo — einmalige Zahlung',
    0, 3990,
    1, 999, 1,
    '["Vollständige Umsetzung durch Complyo", "WCAG 2.1 AA Zertifizierung", "Cookie-Banner Setup", "Rechtstexte erstellt", "Persönlicher Ansprechpartner"]'::jsonb
),
(
    'Updateservice',
    'Laufende Updates nach Expertenservice — monatlich kündbar',
    29, 0,
    1, 999, 1,
    '["Automatische Compliance-Updates", "Gesetzesänderungen werden umgesetzt", "Monatliche Scans", "Priority Support"]'::jsonb
),
(
    'Pro-Paket',
    'Alle 4 Compliance-Bereiche, 1 Domain',
    49, 490,
    1, 999, 3,
    '["Cookie & DSGVO", "Barrierefreiheit", "Rechtliche Texte", "Monitoring & Scan", "eRecht24 Integration", "Priority Support", "API-Zugriff"]'::jsonb
),
(
    'Expertenservice',
    'Komplette Überarbeitung durch Complyo — einmalige Zahlung',
    0, 3990,
    1, 999, 1,
    '["Vollständige Umsetzung durch Complyo", "WCAG 2.1 AA Zertifizierung", "Cookie-Banner Setup", "Rechtstexte erstellt", "Persönlicher Ansprechpartner"]'::jsonb
),
(
    'Updateservice',
    'Laufende Updates nach Expertenservice — monatlich kündbar',
    29, 0,
    1, 999, 1,
    '["Automatische Compliance-Updates", "Gesetzesänderungen werden umgesetzt", "Monatliche Scans", "Priority Support"]'::jsonb
),
(
    'Agentur',
    '25 Domains, alle 4 Bereiche',
    299, 2990,
    25, 999, 10,
    '["Alle 4 Compliance-Bereiche", "25 Domains", "Agentur-Dashboard", "Multi-Site Übersicht", "White-Label Option", "Priority Support", "API-Zugriff", "Dedizierter Ansprechpartner"]'::jsonb
),
(
    'Expertenservice',
    'Komplette Überarbeitung durch Complyo — einmalige Zahlung',
    0, 3990,
    1, 999, 1,
    '["Vollständige Umsetzung durch Complyo", "WCAG 2.1 AA Zertifizierung", "Cookie-Banner Setup", "Rechtstexte erstellt", "Persönlicher Ansprechpartner"]'::jsonb
),
(
    'Updateservice',
    'Laufende Updates nach Expertenservice — monatlich kündbar',
    29, 0,
    1, 999, 1,
    '["Automatische Compliance-Updates", "Gesetzesänderungen werden umgesetzt", "Monatliche Scans", "Priority Support"]'::jsonb
)
ON CONFLICT DO NOTHING;

