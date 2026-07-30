-- ============================================
-- AI Legal Classifier & Learning System
-- Migration für intelligente Gesetzesänderungs-Klassifizierung
-- ============================================

-- Tabelle für AI-Klassifizierungen
CREATE TABLE IF NOT EXISTS ai_classifications (
    id SERIAL PRIMARY KEY,
    update_id VARCHAR(255) NOT NULL,  -- Referenz zu legal_updates oder legal_changes
    user_id INTEGER,  -- Optional: User-spezifische Klassifizierung
    
    -- Klassifizierungs-Ergebnis
    action_required BOOLEAN NOT NULL DEFAULT false,
    confidence VARCHAR(20) NOT NULL,  -- high, medium, low
    severity VARCHAR(20) NOT NULL,  -- critical, high, medium, low, info
    impact_score DECIMAL(3,1) NOT NULL,  -- 0.0 - 10.0
    
    -- Primary Action
    primary_action_type VARCHAR(50) NOT NULL,
    primary_action_priority INTEGER NOT NULL,
    primary_action_title TEXT NOT NULL,
    primary_action_description TEXT NOT NULL,
    primary_button_text VARCHAR(100) NOT NULL,
    primary_button_color VARCHAR(20) NOT NULL,
    primary_button_icon VARCHAR(50) NOT NULL,
    estimated_time VARCHAR(50),
    requires_paid_plan BOOLEAN DEFAULT false,
    
    -- Weitere Actions (JSON-Array)
    recommended_actions JSONB,
    
    -- Erklärungen
    reasoning TEXT NOT NULL,
    user_impact TEXT NOT NULL,
    consequences_if_ignored TEXT,
    
    -- Metadata
    model_version VARCHAR(50) DEFAULT 'v1.0',
    classified_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Index für schnelle Abfragen
    UNIQUE(update_id, user_id)
);

CREATE INDEX idx_ai_classifications_update ON ai_classifications(update_id);
CREATE INDEX idx_ai_classifications_user ON ai_classifications(user_id);
CREATE INDEX idx_ai_classifications_action_required ON ai_classifications(action_required);
CREATE INDEX idx_ai_classifications_severity ON ai_classifications(severity);
CREATE INDEX idx_ai_classifications_classified_at ON ai_classifications(classified_at DESC);


-- Tabelle für Feedback zu Klassifizierungen
CREATE TABLE IF NOT EXISTS ai_classification_feedback (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    update_id VARCHAR(255) NOT NULL,
    classification_id INTEGER REFERENCES ai_classifications(id) ON DELETE CASCADE,
    
    -- Feedback-Art
    feedback_type VARCHAR(50) NOT NULL,  -- implicit_click, explicit_helpful, etc.
    user_action VARCHAR(50),  -- view_detail, click_primary_button, etc.
    
    -- Timing
    time_to_action INTEGER,  -- Sekunden bis zur Aktion
    
    -- Context
    context_data JSONB,  -- Zusätzliche Kontext-Informationen
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_feedback_user ON ai_classification_feedback(user_id);
CREATE INDEX idx_feedback_update ON ai_classification_feedback(update_id);
CREATE INDEX idx_feedback_classification ON ai_classification_feedback(classification_id);
CREATE INDEX idx_feedback_type ON ai_classification_feedback(feedback_type);
CREATE INDEX idx_feedback_created ON ai_classification_feedback(created_at DESC);


-- Tabelle für Learning Cycles
CREATE TABLE IF NOT EXISTS ai_learning_cycles (
    id SERIAL PRIMARY KEY,
    insights_count INTEGER NOT NULL,
    suggestions JSONB NOT NULL,  -- Optimierungs-Vorschläge
    learned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_learning_cycles_learned_at ON ai_learning_cycles(learned_at DESC);


-- Erweitere die legal_updates Tabelle um Klassifizierungs-Info
ALTER TABLE legal_updates 
ADD COLUMN IF NOT EXISTS classification_id INTEGER REFERENCES ai_classifications(id),
ADD COLUMN IF NOT EXISTS auto_classified BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS classification_override BOOLEAN DEFAULT false;  -- Admin kann überschreiben


-- Erweitere die legal_changes Tabelle (falls vorhanden)
DO $$ 
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'legal_changes') THEN
        ALTER TABLE legal_changes 
        ADD COLUMN IF NOT EXISTS classification_id INTEGER REFERENCES ai_classifications(id),
        ADD COLUMN IF NOT EXISTS auto_classified BOOLEAN DEFAULT false;
    END IF;
END $$;


-- View für Dashboard: Klassifizierungs-Performance
CREATE OR REPLACE VIEW v_classification_performance AS
SELECT 
    ac.id,
    ac.update_id,
    ac.action_required,
    ac.confidence,
    ac.severity,
    ac.impact_score,
    ac.primary_action_type,
    
    -- Feedback-Stats
    COUNT(f.id) as total_feedback,
    SUM(CASE WHEN f.feedback_type IN ('explicit_helpful', 'action_completed') THEN 1 ELSE 0 END) as positive_feedback,
    SUM(CASE WHEN f.feedback_type IN ('explicit_not_helpful', 'explicit_wrong') THEN 1 ELSE 0 END) as negative_feedback,
    SUM(CASE WHEN f.user_action IS NOT NULL THEN 1 ELSE 0 END) as engaged_users,
    AVG(f.time_to_action) as avg_time_to_action,
    
    -- Performance-Score
    CASE 
        WHEN COUNT(f.id) = 0 THEN 0
        ELSE (
            SUM(CASE WHEN f.feedback_type IN ('explicit_helpful', 'action_completed') THEN 1 ELSE 0 END)::float - 
            SUM(CASE WHEN f.feedback_type IN ('explicit_not_helpful', 'explicit_wrong') THEN 1 ELSE 0 END)::float
        ) / COUNT(f.id)
    END as performance_score,
    
    ac.classified_at
FROM ai_classifications ac
LEFT JOIN ai_classification_feedback f ON ac.id = f.classification_id
GROUP BY ac.id
ORDER BY ac.classified_at DESC;


-- View für Learning Insights
CREATE OR REPLACE VIEW v_learning_insights AS
SELECT 
    ac.primary_action_type,
    ac.severity,
    ac.confidence,
    
    COUNT(*) as total_classifications,
    AVG(ac.impact_score) as avg_impact_score,
    
    -- Feedback-Metriken
    COUNT(f.id) as total_feedback,
    AVG(CASE WHEN f.feedback_type IN ('explicit_helpful', 'action_completed') THEN 1 ELSE 0 END) as success_rate,
    AVG(f.time_to_action) as avg_response_time,
    
    -- Engagement
    SUM(CASE WHEN f.user_action IS NOT NULL THEN 1 ELSE 0 END)::float / NULLIF(COUNT(DISTINCT f.user_id), 0) as engagement_rate
    
FROM ai_classifications ac
LEFT JOIN ai_classification_feedback f ON ac.id = f.classification_id
WHERE ac.classified_at >= NOW() - INTERVAL '30 days'
GROUP BY ac.primary_action_type, ac.severity, ac.confidence
HAVING COUNT(*) >= 5  -- Mindestens 5 Samples
ORDER BY success_rate DESC NULLS LAST;


-- Archiv-Tabelle für alte Gesetzesänderungen
CREATE TABLE IF NOT EXISTS legal_updates_archive (
    LIKE legal_updates INCLUDING ALL
);

-- Füge Archivierungs-Timestamp hinzu
ALTER TABLE legal_updates_archive 
ADD COLUMN IF NOT EXISTS archived_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

CREATE INDEX idx_legal_updates_archive_archived_at ON legal_updates_archive(archived_at DESC);


-- Funktion zum automatischen Archivieren alter Updates
CREATE OR REPLACE FUNCTION archive_old_legal_updates()
RETURNS INTEGER AS $$
DECLARE
    archived_count INTEGER;
BEGIN
    -- Archiviere Updates älter als 6 Monate die nicht action_required sind
    WITH archived AS (
        INSERT INTO legal_updates_archive
        SELECT *, NOW() as archived_at
        FROM legal_updates
        WHERE published_at < NOW() - INTERVAL '6 months'
        AND (action_required = false OR action_required IS NULL)
        AND id NOT IN (SELECT DISTINCT update_id FROM ai_classification_feedback WHERE created_at >= NOW() - INTERVAL '3 months')
        RETURNING id
    )
    DELETE FROM legal_updates
    WHERE id IN (SELECT id FROM archived)
    RETURNING COUNT(*) INTO archived_count;
    
    RETURN archived_count;
END;
$$ LANGUAGE plpgsql;


-- Funktion: Hole Top-Updates mit KI-Klassifizierung
CREATE OR REPLACE FUNCTION get_classified_legal_updates(
    p_user_id INTEGER,
    p_limit INTEGER DEFAULT 6,
    p_include_info_only BOOLEAN DEFAULT false
)
RETURNS TABLE (
    id INTEGER,
    update_type VARCHAR,
    title TEXT,
    description TEXT,
    severity VARCHAR,
    published_at TIMESTAMP,
    effective_date TIMESTAMP,
    url TEXT,
    
    -- Klassifizierungs-Daten
    action_required BOOLEAN,
    confidence VARCHAR,
    impact_score DECIMAL,
    primary_action_type VARCHAR,
    primary_button_text VARCHAR,
    primary_button_color VARCHAR,
    primary_button_icon VARCHAR,
    reasoning TEXT,
    user_impact TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        lu.id,
        lu.update_type,
        lu.title,
        lu.description,
        lu.severity,
        lu.published_at,
        lu.effective_date,
        lu.url,
        
        -- Klassifizierung (falls vorhanden)
        -- Konvertiere lu.action_required von TEXT zu BOOLEAN
        COALESCE(ac.action_required, CASE WHEN lu.action_required IS NOT NULL AND lu.action_required::text != '' THEN true ELSE false END) as action_required,
        ac.confidence,
        ac.impact_score,
        ac.primary_action_type,
        ac.primary_button_text,
        ac.primary_button_color,
        ac.primary_button_icon,
        ac.reasoning,
        ac.user_impact
        
    FROM legal_updates lu
    LEFT JOIN ai_classifications ac ON lu.id::varchar = ac.update_id AND (ac.user_id = p_user_id OR ac.user_id IS NULL)
    WHERE (p_include_info_only OR COALESCE(ac.action_required, CASE WHEN lu.action_required IS NOT NULL AND lu.action_required::text != '' THEN true ELSE false END, false) = true)
    ORDER BY 
        COALESCE(ac.action_required, CASE WHEN lu.action_required IS NOT NULL AND lu.action_required::text != '' THEN true ELSE false END, false) DESC,
        COALESCE(ac.impact_score, 5.0) DESC,
        lu.published_at DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;


-- Trigger: Automatische Klassifizierung neuer Updates
CREATE OR REPLACE FUNCTION trigger_auto_classification()
RETURNS TRIGGER AS $$
BEGIN
    -- Markiere für Auto-Klassifizierung (wird von Background-Job verarbeitet)
    NEW.auto_classified := false;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER legal_updates_auto_classify
    BEFORE INSERT ON legal_updates
    FOR EACH ROW
    EXECUTE FUNCTION trigger_auto_classification();


-- Statistik-Funktion für Dashboard
CREATE OR REPLACE FUNCTION get_legal_updates_stats(p_user_id INTEGER)
RETURNS JSON AS $$
DECLARE
    result JSON;
BEGIN
    SELECT json_build_object(
        'total_updates', COUNT(*),
        'action_required', SUM(CASE WHEN COALESCE(ac.action_required, lu.action_required, false) THEN 1 ELSE 0 END),
        'critical', SUM(CASE WHEN lu.severity = 'critical' THEN 1 ELSE 0 END),
        'high_impact', SUM(CASE WHEN COALESCE(ac.impact_score, 0) >= 8.0 THEN 1 ELSE 0 END),
        'pending_actions', (
            SELECT COUNT(*) 
            FROM ai_classifications ac2
            LEFT JOIN ai_classification_feedback f ON ac2.id = f.classification_id AND f.user_id = p_user_id
            WHERE (ac2.user_id = p_user_id OR ac2.user_id IS NULL)
            AND ac2.action_required = true
            AND f.id IS NULL
        ),
        'avg_impact_score', AVG(COALESCE(ac.impact_score, 5.0))
    ) INTO result
    FROM legal_updates lu
    LEFT JOIN ai_classifications ac ON lu.id::varchar = ac.update_id AND (ac.user_id = p_user_id OR ac.user_id IS NULL)
    WHERE lu.published_at >= NOW() - INTERVAL '3 months';
    
    RETURN result;
END;
$$ LANGUAGE plpgsql;


-- Index-Optimierung
CREATE INDEX IF NOT EXISTS idx_legal_updates_published_at ON legal_updates(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_legal_updates_action_required ON legal_updates(action_required);
CREATE INDEX IF NOT EXISTS idx_legal_updates_severity ON legal_updates(severity);


-- Kommentare für bessere Dokumentation
COMMENT ON TABLE ai_classifications IS 'KI-gestützte Klassifizierungen von Gesetzesänderungen mit automatischer Handlungsempfehlung';
COMMENT ON TABLE ai_classification_feedback IS 'User-Feedback zu KI-Klassifizierungen für selbstlernendes System';
COMMENT ON TABLE ai_learning_cycles IS 'Protokoll der ML-Learning-Cycles für kontinuierliche Verbesserung';
COMMENT ON TABLE legal_updates_archive IS 'Archiv für alte Gesetzesänderungen (>6 Monate)';

COMMENT ON FUNCTION get_classified_legal_updates IS 'Holt Legal Updates mit KI-Klassifizierung für einen User';
COMMENT ON FUNCTION get_legal_updates_stats IS 'Dashboard-Statistiken für Legal Updates eines Users';
COMMENT ON FUNCTION archive_old_legal_updates IS 'Archiviert automatisch alte Updates zur Performance-Optimierung';


-- Initiale Beispiel-Daten (Optional - für Testing)
-- DO $$
-- BEGIN
--     IF NOT EXISTS (SELECT 1 FROM legal_updates LIMIT 1) THEN
--         INSERT INTO legal_updates (update_type, title, description, severity, action_required, source, published_at)
--         VALUES 
--         ('REGULATION_CHANGE', 'Cookie-Banner: Neue Anforderungen ab 2025', 
--          'Die Cookie-Banner-Richtlinien werden verschärft. Vorausgewählte Optionen sind nicht mehr erlaubt.',
--          'high', true, 'EU-Kommission', NOW() - INTERVAL '2 days'),
--         ('COURT_RULING', 'BGH-Urteil zur Impressumspflicht',
--          'BGH bestätigt: Impressum muss von jeder Unterseite mit maximal 2 Klicks erreichbar sein.',
--          'medium', true, 'BGH', NOW() - INTERVAL '5 days'),
--         ('NEW_LAW', 'BFSG: Barrierefreiheit wird Pflicht',
--          'Ab Juni 2025 müssen digitale Dienste barrierefrei sein (WCAG 2.1 AA).',
--          'critical', true, 'Bundestag', NOW() - INTERVAL '1 week');
--     END IF;
-- END $$;


-- Abschluss-Log
DO $$
BEGIN
    RAISE NOTICE '✅ AI Legal Classifier Migration completed successfully';
    RAISE NOTICE '📊 Tables: ai_classifications, ai_classification_feedback, ai_learning_cycles';
    RAISE NOTICE '📦 Views: v_classification_performance, v_learning_insights';
    RAISE NOTICE '⚡ Functions: get_classified_legal_updates, get_legal_updates_stats, archive_old_legal_updates';
END $$;

