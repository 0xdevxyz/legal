-- ============================================================================
-- A/B Testing System für Cookie Banner
-- ============================================================================
-- Ermoeglicht Tests verschiedener Banner-Varianten zur Optimierung der Opt-In-Rate
-- Erstellt: 2025
-- ============================================================================

-- ============================================================================
-- 1. A/B Test Definitionen
-- ============================================================================
CREATE TABLE IF NOT EXISTS cookie_ab_tests (
    id SERIAL PRIMARY KEY,
    site_id VARCHAR(255) NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    
    -- Test Metadaten
    name VARCHAR(255) NOT NULL,
    description TEXT,
    hypothesis TEXT,  -- Was wird getestet/erwartet?
    
    -- Varianten Konfiguration
    variant_a_config JSONB NOT NULL,  -- Basis-Variante (Control)
    variant_b_config JSONB NOT NULL,  -- Test-Variante
    
    -- Traffic Split
    traffic_split INTEGER DEFAULT 50 CHECK (traffic_split >= 0 AND traffic_split <= 100),  -- % fuer Variante A
    
    -- Test Status
    status VARCHAR(50) DEFAULT 'draft',  -- draft, running, paused, completed, cancelled
    winner VARCHAR(1),  -- 'A' oder 'B' (nach Test-Ende)
    
    -- Zeitraum
    start_date TIMESTAMPTZ,
    end_date TIMESTAMPTZ,
    
    -- Statistische Signifikanz
    min_sample_size INTEGER DEFAULT 1000,  -- Mindest-Stichprobe pro Variante
    confidence_level NUMERIC(4,2) DEFAULT 0.95,  -- 95% Konfidenz
    
    -- Metadaten
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT unique_active_test_per_site UNIQUE (site_id, status) 
        WHERE status = 'running'
);

CREATE INDEX IF NOT EXISTS idx_ab_test_site ON cookie_ab_tests(site_id);
CREATE INDEX IF NOT EXISTS idx_ab_test_status ON cookie_ab_tests(status);
CREATE INDEX IF NOT EXISTS idx_ab_test_user ON cookie_ab_tests(user_id);

COMMENT ON TABLE cookie_ab_tests IS 'A/B Test Definitionen fuer Cookie Banner Optimierung';
COMMENT ON COLUMN cookie_ab_tests.traffic_split IS 'Prozent des Traffics fuer Variante A (Rest geht zu B)';
COMMENT ON COLUMN cookie_ab_tests.winner IS 'Gewinner-Variante nach statistischer Auswertung';

-- ============================================================================
-- 2. A/B Test Ergebnisse (Aggregiert pro Tag)
-- ============================================================================
CREATE TABLE IF NOT EXISTS cookie_ab_results (
    id BIGSERIAL PRIMARY KEY,
    test_id INTEGER REFERENCES cookie_ab_tests(id) ON DELETE CASCADE,
    variant VARCHAR(1) NOT NULL CHECK (variant IN ('A', 'B')),
    date DATE NOT NULL,
    
    -- Metriken
    impressions INTEGER DEFAULT 0,       -- Banner angezeigt
    accepted_all INTEGER DEFAULT 0,      -- "Alle akzeptieren"
    accepted_partial INTEGER DEFAULT 0,  -- Individuelle Auswahl
    rejected_all INTEGER DEFAULT 0,      -- "Ablehnen"
    
    -- Kategorie-spezifisch
    accepted_analytics INTEGER DEFAULT 0,
    accepted_marketing INTEGER DEFAULT 0,
    accepted_functional INTEGER DEFAULT 0,
    
    -- Timing
    avg_decision_time_ms INTEGER,  -- Durchschnittliche Zeit bis zur Entscheidung
    
    -- Metadaten
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(test_id, variant, date)
);

CREATE INDEX IF NOT EXISTS idx_ab_results_test ON cookie_ab_results(test_id);
CREATE INDEX IF NOT EXISTS idx_ab_results_date ON cookie_ab_results(date DESC);

COMMENT ON TABLE cookie_ab_results IS 'Taegliche aggregierte Ergebnisse pro A/B Test Variante';

-- ============================================================================
-- 3. A/B Test Visitor Assignments
-- ============================================================================
CREATE TABLE IF NOT EXISTS cookie_ab_assignments (
    id BIGSERIAL PRIMARY KEY,
    test_id INTEGER REFERENCES cookie_ab_tests(id) ON DELETE CASCADE,
    visitor_hash VARCHAR(64) NOT NULL,  -- Hash des visitor_id fuer Konsistenz
    variant VARCHAR(1) NOT NULL CHECK (variant IN ('A', 'B')),
    assigned_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(test_id, visitor_hash)
);

CREATE INDEX IF NOT EXISTS idx_ab_assignments_test ON cookie_ab_assignments(test_id);
CREATE INDEX IF NOT EXISTS idx_ab_assignments_visitor ON cookie_ab_assignments(visitor_hash);

COMMENT ON TABLE cookie_ab_assignments IS 'Persistente Zuordnung von Besuchern zu Test-Varianten';

-- ============================================================================
-- 4. Statistik-Funktionen
-- ============================================================================

-- Berechnet die Conversion Rate fuer eine Variante
CREATE OR REPLACE FUNCTION calculate_conversion_rate(
    p_accepted INTEGER,
    p_impressions INTEGER
) RETURNS NUMERIC AS $$
BEGIN
    IF p_impressions = 0 THEN
        RETURN 0;
    END IF;
    RETURN ROUND((p_accepted::NUMERIC / p_impressions::NUMERIC) * 100, 2);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Berechnet den Z-Score fuer A/B Test Signifikanz
CREATE OR REPLACE FUNCTION calculate_z_score(
    p_rate_a NUMERIC,
    p_rate_b NUMERIC,
    p_n_a INTEGER,
    p_n_b INTEGER
) RETURNS NUMERIC AS $$
DECLARE
    pooled_rate NUMERIC;
    std_error NUMERIC;
    z_score NUMERIC;
BEGIN
    IF p_n_a = 0 OR p_n_b = 0 THEN
        RETURN 0;
    END IF;
    
    pooled_rate := (p_rate_a * p_n_a + p_rate_b * p_n_b) / (p_n_a + p_n_b);
    
    IF pooled_rate = 0 OR pooled_rate = 1 THEN
        RETURN 0;
    END IF;
    
    std_error := SQRT(pooled_rate * (1 - pooled_rate) * (1.0/p_n_a + 1.0/p_n_b));
    
    IF std_error = 0 THEN
        RETURN 0;
    END IF;
    
    z_score := (p_rate_a - p_rate_b) / std_error;
    
    RETURN ROUND(z_score, 4);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- ============================================================================
-- 5. View fuer Test-Auswertung
-- ============================================================================
CREATE OR REPLACE VIEW v_ab_test_summary AS
SELECT 
    t.id AS test_id,
    t.site_id,
    t.name,
    t.status,
    t.traffic_split,
    t.start_date,
    t.end_date,
    t.winner,
    
    -- Variante A Statistiken
    COALESCE(SUM(CASE WHEN r.variant = 'A' THEN r.impressions END), 0) AS variant_a_impressions,
    COALESCE(SUM(CASE WHEN r.variant = 'A' THEN r.accepted_all END), 0) AS variant_a_accepted,
    calculate_conversion_rate(
        COALESCE(SUM(CASE WHEN r.variant = 'A' THEN r.accepted_all END), 0)::INTEGER,
        COALESCE(SUM(CASE WHEN r.variant = 'A' THEN r.impressions END), 1)::INTEGER
    ) AS variant_a_rate,
    
    -- Variante B Statistiken
    COALESCE(SUM(CASE WHEN r.variant = 'B' THEN r.impressions END), 0) AS variant_b_impressions,
    COALESCE(SUM(CASE WHEN r.variant = 'B' THEN r.accepted_all END), 0) AS variant_b_accepted,
    calculate_conversion_rate(
        COALESCE(SUM(CASE WHEN r.variant = 'B' THEN r.accepted_all END), 0)::INTEGER,
        COALESCE(SUM(CASE WHEN r.variant = 'B' THEN r.impressions END), 1)::INTEGER
    ) AS variant_b_rate,
    
    -- Verbesserung (B vs A)
    CASE 
        WHEN COALESCE(SUM(CASE WHEN r.variant = 'A' THEN r.accepted_all END), 0) > 0 THEN
            ROUND(
                ((COALESCE(SUM(CASE WHEN r.variant = 'B' THEN r.accepted_all END), 0)::NUMERIC / 
                  NULLIF(COALESCE(SUM(CASE WHEN r.variant = 'B' THEN r.impressions END), 1), 0)) -
                 (COALESCE(SUM(CASE WHEN r.variant = 'A' THEN r.accepted_all END), 0)::NUMERIC / 
                  NULLIF(COALESCE(SUM(CASE WHEN r.variant = 'A' THEN r.impressions END), 1), 0))) /
                (COALESCE(SUM(CASE WHEN r.variant = 'A' THEN r.accepted_all END), 0)::NUMERIC / 
                 NULLIF(COALESCE(SUM(CASE WHEN r.variant = 'A' THEN r.impressions END), 1), 0)) * 100
            , 2)
        ELSE 0
    END AS improvement_percent

FROM cookie_ab_tests t
LEFT JOIN cookie_ab_results r ON t.id = r.test_id
GROUP BY t.id, t.site_id, t.name, t.status, t.traffic_split, t.start_date, t.end_date, t.winner;

COMMENT ON VIEW v_ab_test_summary IS 'Zusammenfassung aller A/B Tests mit Conversion Rates';

-- ============================================================================
-- 6. Trigger fuer automatische Aktualisierung
-- ============================================================================
CREATE OR REPLACE FUNCTION update_ab_test_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at := NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_ab_test_updated
    BEFORE UPDATE ON cookie_ab_tests
    FOR EACH ROW
    EXECUTE FUNCTION update_ab_test_timestamp();

-- ============================================================================
-- Installation abgeschlossen
-- ============================================================================
DO $$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE 'A/B Testing System installiert!';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Tabellen:';
    RAISE NOTICE '  ✓ cookie_ab_tests';
    RAISE NOTICE '  ✓ cookie_ab_results';
    RAISE NOTICE '  ✓ cookie_ab_assignments';
    RAISE NOTICE 'Views:';
    RAISE NOTICE '  ✓ v_ab_test_summary';
    RAISE NOTICE 'Funktionen:';
    RAISE NOTICE '  ✓ calculate_conversion_rate()';
    RAISE NOTICE '  ✓ calculate_z_score()';
    RAISE NOTICE '========================================';
END $$;

