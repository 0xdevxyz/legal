-- ============================================================================
-- Complyo Expert Service Requests
-- ============================================================================
-- Datum: 2025-11-15
-- Beschreibung: Tracking von Expertservice-Anfragen
-- ============================================================================

-- 1. Sequence für Request-IDs (muss VORHER erstellt werden)
CREATE SEQUENCE IF NOT EXISTS expert_request_seq START 1;

-- 2. Expertservice-Anfragen Tabelle
CREATE TABLE IF NOT EXISTS expert_service_requests (
    id SERIAL PRIMARY KEY,
    
    -- Identifikation
    request_id VARCHAR(100) UNIQUE NOT NULL DEFAULT ('EXP-' || TO_CHAR(NOW(), 'YYYYMMDD') || '-' || LPAD(nextval('expert_request_seq')::TEXT, 4, '0')),
    user_id UUID REFERENCES users(id),
    
    -- Website-Daten
    site_id VARCHAR(100),
    site_url TEXT NOT NULL,
    scan_id VARCHAR(100),
    
    -- Kontakt-Daten
    contact_name VARCHAR(200),
    contact_email VARCHAR(200) NOT NULL,
    contact_phone VARCHAR(50),
    company_name VARCHAR(200),
    
    -- Service-Details
    service_type VARCHAR(50) DEFAULT 'accessibility',  -- 'accessibility', 'full_compliance', 'custom'
    priority VARCHAR(20) DEFAULT 'normal',  -- 'normal', 'urgent'
    estimated_price DECIMAL(10,2) DEFAULT 3000.00,
    
    -- Projekt-Details
    issues_count INTEGER,
    alt_text_count INTEGER,
    pages_count INTEGER,
    additional_notes TEXT,
    
    -- Status-Tracking
    status VARCHAR(30) DEFAULT 'pending',  -- 'pending', 'contacted', 'in_progress', 'completed', 'cancelled'
    assigned_to VARCHAR(100),
    
    -- Timestamps
    requested_at TIMESTAMP DEFAULT NOW(),
    contacted_at TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    -- Internal Notes
    internal_notes TEXT,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 3. Indizes
CREATE INDEX IF NOT EXISTS idx_expert_requests_user_id ON expert_service_requests(user_id);
CREATE INDEX IF NOT EXISTS idx_expert_requests_status ON expert_service_requests(status);
CREATE INDEX IF NOT EXISTS idx_expert_requests_requested_at ON expert_service_requests(requested_at DESC);
CREATE INDEX IF NOT EXISTS idx_expert_requests_site_id ON expert_service_requests(site_id);

-- 4. Trigger: Auto-Update updated_at
CREATE OR REPLACE FUNCTION update_expert_request_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_update_expert_request_timestamp ON expert_service_requests;
CREATE TRIGGER trigger_update_expert_request_timestamp
    BEFORE UPDATE ON expert_service_requests
    FOR EACH ROW
    EXECUTE FUNCTION update_expert_request_timestamp();

-- 5. View: Offene Anfragen
CREATE OR REPLACE VIEW expert_requests_pending AS
SELECT 
    request_id,
    user_id,
    site_url,
    contact_email,
    service_type,
    priority,
    estimated_price,
    issues_count,
    status,
    requested_at,
    EXTRACT(EPOCH FROM (NOW() - requested_at))/3600 as hours_waiting
FROM expert_service_requests
WHERE status IN ('pending', 'contacted')
ORDER BY 
    CASE priority
        WHEN 'urgent' THEN 1
        WHEN 'normal' THEN 2
        ELSE 3
    END,
    requested_at ASC;

-- 6. Funktion: Statistiken
CREATE OR REPLACE FUNCTION get_expert_service_stats(p_days INTEGER DEFAULT 30)
RETURNS TABLE (
    total_requests BIGINT,
    pending_requests BIGINT,
    completed_requests BIGINT,
    total_revenue DECIMAL,
    avg_completion_time_hours DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::BIGINT as total_requests,
        COUNT(*) FILTER (WHERE status IN ('pending', 'contacted'))::BIGINT as pending_requests,
        COUNT(*) FILTER (WHERE status = 'completed')::BIGINT as completed_requests,
        COALESCE(SUM(estimated_price) FILTER (WHERE status = 'completed'), 0) as total_revenue,
        COALESCE(AVG(EXTRACT(EPOCH FROM (completed_at - requested_at))/3600) FILTER (WHERE completed_at IS NOT NULL), 0)::DECIMAL as avg_completion_time_hours
    FROM expert_service_requests
    WHERE requested_at > NOW() - INTERVAL '1 day' * p_days;
END;
$$ LANGUAGE plpgsql;

-- 7. Kommentare
COMMENT ON TABLE expert_service_requests IS 'Expertservice-Anfragen von Kunden';
COMMENT ON COLUMN expert_service_requests.request_id IS 'Eindeutige Request-ID im Format EXP-YYYYMMDD-0001';
COMMENT ON COLUMN expert_service_requests.status IS 'pending=wartend, contacted=kontaktiert, in_progress=in Bearbeitung, completed=fertig, cancelled=abgebrochen';
COMMENT ON COLUMN expert_service_requests.service_type IS 'accessibility=nur Barrierefreiheit, full_compliance=alle 4 Säulen, custom=individuell';

-- ============================================================================
-- Migration abgeschlossen
-- ============================================================================

