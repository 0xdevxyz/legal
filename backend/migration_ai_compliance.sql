-- Migration: Add AI Compliance Tables
-- Version: 1.0
-- Date: 2025-01-03
-- Description: Adds tables for ComploAI Guard (EU AI Act Compliance Module)

-- Run this script on existing Complyo databases to add AI Compliance features

\c complyo_db;

-- Begin Transaction
BEGIN;

-- AI Systems Registry
CREATE TABLE IF NOT EXISTS ai_systems (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    website_id UUID REFERENCES websites(id) ON DELETE SET NULL,
    
    -- System Information
    name VARCHAR(255) NOT NULL,
    description TEXT,
    vendor VARCHAR(255),
    purpose TEXT,
    deployment_date DATE,
    
    -- Risk Classification
    risk_category VARCHAR(50), -- 'prohibited', 'high', 'limited', 'minimal', 'pending'
    risk_reasoning TEXT,
    confidence_score FLOAT,
    
    -- Compliance Status
    compliance_score INTEGER DEFAULT 0,
    last_assessment_date TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) DEFAULT 'active', -- 'active', 'paused', 'archived'
    
    -- Metadata
    domain VARCHAR(255), -- HR, marketing, customer_service, etc.
    data_types JSONB, -- Types of data processed
    affected_persons JSONB, -- Who is affected
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- AI Compliance Scans
CREATE TABLE IF NOT EXISTS ai_compliance_scans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ai_system_id UUID NOT NULL REFERENCES ai_systems(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    scan_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Scores
    compliance_score INTEGER,
    overall_risk_score FLOAT,
    
    -- Assessment Results
    risk_assessment JSONB,
    documentation_status JSONB,
    findings JSONB,
    recommendations TEXT,
    
    -- Compliance Checks
    requirements_met JSONB, -- Which AI Act requirements are met
    requirements_failed JSONB, -- Which requirements failed
    
    -- Scan Metadata
    scan_duration_ms INTEGER,
    status VARCHAR(50) DEFAULT 'completed', -- 'pending', 'in_progress', 'completed', 'failed'
    error_message TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- AI Documentation
CREATE TABLE IF NOT EXISTS ai_documentation (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ai_system_id UUID NOT NULL REFERENCES ai_systems(id) ON DELETE CASCADE,
    
    -- Document Info
    document_type VARCHAR(100) NOT NULL, -- 'risk_assessment', 'data_governance', 'technical_docs', 'transparency_info', etc.
    title VARCHAR(255),
    content JSONB,
    file_url VARCHAR(500),
    
    -- Versioning
    version INTEGER DEFAULT 1,
    status VARCHAR(50) DEFAULT 'draft', -- 'draft', 'review', 'approved', 'published'
    
    -- Approval
    approved_by UUID REFERENCES users(id),
    approved_at TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- User Add-Ons (for tracking ComploAI Guard and Priority Support subscriptions)
CREATE TABLE IF NOT EXISTS user_addons (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Add-On Info
    addon_key VARCHAR(100) NOT NULL, -- 'comploai_guard', 'priority_support'
    addon_name VARCHAR(255),
    
    -- Subscription
    status VARCHAR(50) DEFAULT 'active', -- 'active', 'cancelled', 'expired'
    price_monthly DECIMAL(10, 2),
    stripe_subscription_id VARCHAR(255),
    
    -- Limits
    limits JSONB, -- e.g., {"ai_systems": 10}
    usage JSONB, -- Current usage tracking
    
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    cancelled_at TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(user_id, addon_key)
);

-- Create indexes for AI tables
CREATE INDEX IF NOT EXISTS idx_ai_systems_user_id ON ai_systems(user_id);
CREATE INDEX IF NOT EXISTS idx_ai_systems_risk_category ON ai_systems(risk_category);
CREATE INDEX IF NOT EXISTS idx_ai_systems_status ON ai_systems(status);
CREATE INDEX IF NOT EXISTS idx_ai_compliance_scans_ai_system_id ON ai_compliance_scans(ai_system_id);
CREATE INDEX IF NOT EXISTS idx_ai_compliance_scans_user_id ON ai_compliance_scans(user_id);
CREATE INDEX IF NOT EXISTS idx_ai_compliance_scans_created_at ON ai_compliance_scans(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_ai_documentation_ai_system_id ON ai_documentation(ai_system_id);
CREATE INDEX IF NOT EXISTS idx_ai_documentation_document_type ON ai_documentation(document_type);
CREATE INDEX IF NOT EXISTS idx_user_addons_user_id ON user_addons(user_id);
CREATE INDEX IF NOT EXISTS idx_user_addons_addon_key ON user_addons(addon_key);
CREATE INDEX IF NOT EXISTS idx_user_addons_status ON user_addons(status);

-- Apply updated_at triggers to new AI tables
DO $$
BEGIN
    -- Check if trigger function exists, if not skip (will use existing one)
    IF EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'update_updated_at_column') THEN
        -- Create triggers
        DROP TRIGGER IF EXISTS update_ai_systems_updated_at ON ai_systems;
        CREATE TRIGGER update_ai_systems_updated_at BEFORE UPDATE ON ai_systems
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

        DROP TRIGGER IF EXISTS update_ai_documentation_updated_at ON ai_documentation;
        CREATE TRIGGER update_ai_documentation_updated_at BEFORE UPDATE ON ai_documentation
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

        DROP TRIGGER IF EXISTS update_user_addons_updated_at ON user_addons;
        CREATE TRIGGER update_user_addons_updated_at BEFORE UPDATE ON user_addons
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
END$$;

-- Grant permissions for new tables
GRANT ALL PRIVILEGES ON TABLE ai_systems TO complyo_user;
GRANT ALL PRIVILEGES ON TABLE ai_compliance_scans TO complyo_user;
GRANT ALL PRIVILEGES ON TABLE ai_documentation TO complyo_user;
GRANT ALL PRIVILEGES ON TABLE user_addons TO complyo_user;

-- Commit Transaction
COMMIT;

-- Verification
SELECT 'Migration completed successfully!' AS status;
SELECT 'AI Compliance tables created:' AS info;
SELECT table_name FROM information_schema.tables 
WHERE table_name IN ('ai_systems', 'ai_compliance_scans', 'ai_documentation', 'user_addons')
AND table_schema = 'public';

