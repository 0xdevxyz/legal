-- ============================================================================
-- Complyo Widget Analytics
-- ============================================================================
-- Datum: 2025-11-15
-- Beschreibung: Tracking von Widget-Nutzung für Insights und Upselling
-- ============================================================================

-- 1. Widget Analytics Haupttabelle
CREATE TABLE IF NOT EXISTS widget_analytics (
    id SERIAL PRIMARY KEY,
    
    -- Identifikation
    site_id VARCHAR(100) NOT NULL,
    session_id VARCHAR(100) NOT NULL,
    user_id UUID,  -- Optional, wenn eingeloggt
    
    -- Event-Daten
    event_type VARCHAR(50) NOT NULL,  -- 'feature_toggle', 'widget_open', 'widget_close'
    feature VARCHAR(50),  -- 'contrast', 'font_size', 'link_highlight', 'keyboard_nav'
    value JSONB,  -- Flexible Daten (z.B. {"size": 120, "enabled": true})
    
    -- Kontext
    page_url TEXT,
    user_agent TEXT,
    viewport_width INTEGER,
    viewport_height INTEGER,
    
    -- Timestamps
    timestamp TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

-- 2. Indizes für Performance
CREATE INDEX IF NOT EXISTS idx_widget_analytics_site_id ON widget_analytics(site_id);
CREATE INDEX IF NOT EXISTS idx_widget_analytics_session_id ON widget_analytics(session_id);
CREATE INDEX IF NOT EXISTS idx_widget_analytics_timestamp ON widget_analytics(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_widget_analytics_event_type ON widget_analytics(event_type);
CREATE INDEX IF NOT EXISTS idx_widget_analytics_feature ON widget_analytics(feature);

-- 3. Widget-Sessions Aggregat-Tabelle
CREATE TABLE IF NOT EXISTS widget_sessions (
    id SERIAL PRIMARY KEY,
    
    site_id VARCHAR(100) NOT NULL,
    session_id VARCHAR(100) UNIQUE NOT NULL,
    user_id UUID,
    
    -- Session-Daten
    started_at TIMESTAMP NOT NULL,
    last_activity_at TIMESTAMP NOT NULL,
    duration_seconds INTEGER,  -- Wird beim Session-Ende berechnet
    
    -- Nutzungs-Statistiken
    features_used JSONB,  -- Array von Features: ["contrast", "font_size"]
    events_count INTEGER DEFAULT 0,
    pages_visited INTEGER DEFAULT 1,
    
    -- Device-Info
    device_type VARCHAR(20),  -- 'mobile', 'tablet', 'desktop'
    browser VARCHAR(50),
    
    -- Status
    status VARCHAR(20) DEFAULT 'active',  -- 'active', 'ended'
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_widget_sessions_site_id ON widget_sessions(site_id);
CREATE INDEX IF NOT EXISTS idx_widget_sessions_started_at ON widget_sessions(started_at DESC);

-- 4. Funktion: Feature-Nutzung tracken
CREATE OR REPLACE FUNCTION track_widget_feature(
    p_site_id VARCHAR(100),
    p_session_id VARCHAR(100),
    p_feature VARCHAR(50),
    p_value JSONB DEFAULT NULL
)
RETURNS VOID AS $$
BEGIN
    -- Insert analytics event
    INSERT INTO widget_analytics (
        site_id, session_id, event_type, feature, value, timestamp
    ) VALUES (
        p_site_id, p_session_id, 'feature_toggle', p_feature, p_value, NOW()
    );
    
    -- Update session
    INSERT INTO widget_sessions (
        site_id, session_id, started_at, last_activity_at, 
        features_used, events_count
    ) VALUES (
        p_site_id, p_session_id, NOW(), NOW(),
        jsonb_build_array(p_feature), 1
    )
    ON CONFLICT (session_id) DO UPDATE SET
        last_activity_at = NOW(),
        features_used = (
            SELECT jsonb_agg(DISTINCT elem)
            FROM (
                SELECT jsonb_array_elements_text(widget_sessions.features_used) AS elem
                UNION
                SELECT p_feature
            ) AS combined
        ),
        events_count = widget_sessions.events_count + 1,
        updated_at = NOW();
END;
$$ LANGUAGE plpgsql;

-- 5. View: Feature-Popularität pro Site
CREATE OR REPLACE VIEW widget_feature_popularity AS
SELECT 
    site_id,
    feature,
    COUNT(*) as usage_count,
    COUNT(DISTINCT session_id) as unique_sessions,
    COUNT(DISTINCT DATE(timestamp)) as days_used,
    MAX(timestamp) as last_used
FROM widget_analytics
WHERE event_type = 'feature_toggle' AND feature IS NOT NULL
GROUP BY site_id, feature
ORDER BY site_id, usage_count DESC;

-- 6. View: Tägliche Widget-Nutzung
CREATE OR REPLACE VIEW widget_daily_stats AS
SELECT 
    site_id,
    DATE(timestamp) as date,
    COUNT(*) as total_events,
    COUNT(DISTINCT session_id) as unique_sessions,
    COUNT(DISTINCT feature) as features_used
FROM widget_analytics
WHERE event_type = 'feature_toggle'
GROUP BY site_id, DATE(timestamp)
ORDER BY date DESC;

-- 7. View: Session-Übersicht
CREATE OR REPLACE VIEW widget_session_overview AS
SELECT 
    ws.site_id,
    ws.session_id,
    ws.started_at,
    ws.duration_seconds,
    ws.features_used,
    ws.events_count,
    ws.device_type,
    COUNT(wa.id) as detailed_events
FROM widget_sessions ws
LEFT JOIN widget_analytics wa ON ws.session_id = wa.session_id
GROUP BY ws.id, ws.site_id, ws.session_id, ws.started_at, 
         ws.duration_seconds, ws.features_used, ws.events_count, ws.device_type
ORDER BY ws.started_at DESC;

-- 8. Funktion: Cleanup alte Analytics-Daten (nach 90 Tagen)
CREATE OR REPLACE FUNCTION cleanup_old_widget_analytics()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM widget_analytics
    WHERE timestamp < NOW() - INTERVAL '90 days';
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- 9. Kommentare für Dokumentation
COMMENT ON TABLE widget_analytics IS 'Detailliertes Tracking aller Widget-Events für Analytics und Upselling';
COMMENT ON TABLE widget_sessions IS 'Aggregierte Session-Daten für schnelle Übersicht';
COMMENT ON COLUMN widget_analytics.event_type IS 'feature_toggle=Feature an/aus, widget_open=Widget geöffnet, widget_close=Widget geschlossen';
COMMENT ON COLUMN widget_analytics.feature IS 'contrast, font_size, link_highlight, keyboard_nav, etc.';
COMMENT ON VIEW widget_feature_popularity IS 'Zeigt welche Features am beliebtesten sind pro Site';

-- ============================================================================
-- Migration abgeschlossen
-- ============================================================================

