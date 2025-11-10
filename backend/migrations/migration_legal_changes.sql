-- Migration: Legal Change Monitoring System
-- Erstellt Tabellen für automatische Gesetzesänderungs-Überwachung

-- Tabelle für erkannte Gesetzesänderungen
CREATE TABLE IF NOT EXISTS legal_changes (
    id VARCHAR(255) PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    affected_areas TEXT[] NOT NULL,  -- Array von Bereichen (cookie_compliance, datenschutz, etc.)
    severity VARCHAR(50) NOT NULL,  -- critical, high, medium, low, info
    effective_date TIMESTAMP NOT NULL,
    source TEXT NOT NULL,
    source_url TEXT,
    requirements TEXT[],  -- Array von Anforderungen
    detected_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Tabelle für Impact Analysis (welche Kunden sind betroffen)
CREATE TABLE IF NOT EXISTS legal_change_impacts (
    id SERIAL PRIMARY KEY,
    legal_change_id VARCHAR(255) REFERENCES legal_changes(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    is_affected BOOLEAN NOT NULL,
    affected_components TEXT[],
    urgency VARCHAR(50),
    risks TEXT[],
    estimated_effort VARCHAR(100),
    recommendation TEXT,
    analyzed_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'pending',  -- pending, acknowledged, in_progress, completed, dismissed
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(legal_change_id, user_id)
);

-- Tabelle für generierte Compliance Fixes
CREATE TABLE IF NOT EXISTS compliance_fixes (
    id SERIAL PRIMARY KEY,
    legal_change_id VARCHAR(255) REFERENCES legal_changes(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    affected_area VARCHAR(100) NOT NULL,
    fix_type VARCHAR(50) NOT NULL,  -- automated, semi-automated, manual
    description TEXT NOT NULL,
    code_changes JSONB,
    config_changes JSONB,
    manual_steps TEXT[],
    priority INTEGER DEFAULT 5,
    status VARCHAR(50) DEFAULT 'pending',  -- pending, applied, failed, skipped
    applied_at TIMESTAMP,
    applied_by UUID REFERENCES users(id),
    result TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Tabelle für Monitoring-Logs
CREATE TABLE IF NOT EXISTS legal_monitoring_logs (
    id SERIAL PRIMARY KEY,
    scan_date TIMESTAMP DEFAULT NOW(),
    changes_detected INTEGER DEFAULT 0,
    sources_checked TEXT[],
    status VARCHAR(50) DEFAULT 'completed',  -- completed, failed, partial
    error_message TEXT,
    execution_time_seconds FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Tabelle für User Notifications zu Gesetzesänderungen
CREATE TABLE IF NOT EXISTS legal_change_notifications (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    legal_change_id VARCHAR(255) REFERENCES legal_changes(id) ON DELETE CASCADE,
    notification_type VARCHAR(50) NOT NULL,  -- email, in_app, both
    sent_at TIMESTAMP DEFAULT NOW(),
    read_at TIMESTAMP,
    clicked_at TIMESTAMP,
    status VARCHAR(50) DEFAULT 'sent',  -- sent, read, clicked, dismissed
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indices für Performance
CREATE INDEX IF NOT EXISTS idx_legal_changes_effective_date ON legal_changes(effective_date);
CREATE INDEX IF NOT EXISTS idx_legal_changes_severity ON legal_changes(severity);
CREATE INDEX IF NOT EXISTS idx_legal_changes_is_active ON legal_changes(is_active);

CREATE INDEX IF NOT EXISTS idx_legal_change_impacts_user_id ON legal_change_impacts(user_id);
CREATE INDEX IF NOT EXISTS idx_legal_change_impacts_legal_change_id ON legal_change_impacts(legal_change_id);
CREATE INDEX IF NOT EXISTS idx_legal_change_impacts_status ON legal_change_impacts(status);
CREATE INDEX IF NOT EXISTS idx_legal_change_impacts_is_affected ON legal_change_impacts(is_affected);

CREATE INDEX IF NOT EXISTS idx_compliance_fixes_user_id ON compliance_fixes(user_id);
CREATE INDEX IF NOT EXISTS idx_compliance_fixes_legal_change_id ON compliance_fixes(legal_change_id);
CREATE INDEX IF NOT EXISTS idx_compliance_fixes_status ON compliance_fixes(status);
CREATE INDEX IF NOT EXISTS idx_compliance_fixes_priority ON compliance_fixes(priority);

CREATE INDEX IF NOT EXISTS idx_legal_change_notifications_user_id ON legal_change_notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_legal_change_notifications_status ON legal_change_notifications(status);

-- Beispiel-Eintrag für Testing
INSERT INTO legal_changes (
    id,
    title,
    description,
    affected_areas,
    severity,
    effective_date,
    source,
    source_url,
    requirements
) VALUES (
    'dsgvo-update-2025-01',
    'DSGVO: Verschärfte Cookie-Banner-Pflicht',
    'Ab 01.01.2025 müssen Cookie-Banner eine deutlichere Ablehnen-Option anbieten. Die Buttons müssen gleich prominent sein.',
    ARRAY['cookie_compliance', 'datenschutz'],
    'high',
    '2025-01-01 00:00:00',
    'EU-Urteil C-xxx/24',
    'https://eur-lex.europa.eu/...',
    ARRAY[
        'Ablehnen-Button muss gleich prominent wie Akzeptieren-Button sein',
        'Keine Dark Patterns erlaubt',
        'Klare und verständliche Sprache'
    ]
) ON CONFLICT (id) DO NOTHING;

-- Trigger für updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_legal_changes_updated_at BEFORE UPDATE ON legal_changes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_legal_change_impacts_updated_at BEFORE UPDATE ON legal_change_impacts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_compliance_fixes_updated_at BEFORE UPDATE ON compliance_fixes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Erfolgsmeldung
SELECT 'Legal Change Monitoring System successfully installed!' as status;

