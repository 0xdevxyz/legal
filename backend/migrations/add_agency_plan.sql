-- Migration: Agency-Plan hinzufügen
-- 490€/Monat, 25 Websites, alle 4 Module, White-Label

INSERT INTO subscription_plans (
    name, slug, price_monthly, price_yearly,
    max_websites, max_scans, max_fixes,
    features, is_active
)
SELECT
    'Agentur',
    'agency',
    490.00,
    4704.00,  -- 490 * 12 * 0.8 = 4704 (20% Jahresrabatt)
    25,
    -1,       -- unbegrenzte Scans
    -1,       -- unbegrenzte Fixes
    '{
        "basic_scan": true,
        "ai_fixes": true,
        "deep_scan": true,
        "priority_support": true,
        "white_label": true,
        "multi_site": true,
        "agency_reports": true,
        "all_modules": true
    }'::jsonb,
    true
WHERE NOT EXISTS (
    SELECT 1 FROM subscription_plans WHERE slug = 'agency'
);
