-- Migration: Add AI Compliance Notifications and Scheduled Scans
-- Version: 1.1
-- Date: 2025-02-07

BEGIN;

-- AI Compliance Notifications Table
CREATE TABLE IF NOT EXISTS ai_compliance_notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    ai_system_id UUID REFERENCES ai_systems(id) ON DELETE CASCADE,
    
    -- Notification Type
    notification_type VARCHAR(50) NOT NULL, -- 'compliance_alert', 'scan_reminder', 'high_risk_alert', 'scan_completed'
    severity VARCHAR(20) DEFAULT 'info', -- 'info', 'warning', 'critical'
    
    -- Content
    title VARCHAR(255) NOT NULL,
    message TEXT,
    metadata JSONB, -- Additional data like scores, findings, etc.
    
    -- Status
    is_read BOOLEAN DEFAULT FALSE,
    is_email_sent BOOLEAN DEFAULT FALSE,
    email_sent_at TIMESTAMP WITH TIME ZONE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    read_at TIMESTAMP WITH TIME ZONE
);

-- AI Compliance Alert Settings (per user)
CREATE TABLE IF NOT EXISTS ai_compliance_alert_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Email Notification Settings
    email_on_compliance_drop BOOLEAN DEFAULT TRUE,
    email_on_high_risk BOOLEAN DEFAULT TRUE,
    email_on_scan_reminder BOOLEAN DEFAULT TRUE,
    email_on_scan_completed BOOLEAN DEFAULT FALSE,
    
    -- Thresholds
    compliance_drop_threshold INTEGER DEFAULT 10, -- Alert if score drops by X points
    scan_reminder_days INTEGER DEFAULT 30, -- Remind after X days without scan
    
    -- In-App Notifications
    inapp_notifications BOOLEAN DEFAULT TRUE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(user_id)
);

-- AI Scheduled Scans Table
CREATE TABLE IF NOT EXISTS ai_scheduled_scans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    ai_system_id UUID NOT NULL REFERENCES ai_systems(id) ON DELETE CASCADE,
    
    -- Schedule Configuration
    schedule_type VARCHAR(20) NOT NULL, -- 'daily', 'weekly', 'monthly'
    schedule_day INTEGER, -- Day of week (0-6) for weekly, day of month (1-31) for monthly
    schedule_hour INTEGER DEFAULT 9, -- Hour to run (0-23)
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    last_run_at TIMESTAMP WITH TIME ZONE,
    next_run_at TIMESTAMP WITH TIME ZONE,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(ai_system_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_ai_notifications_user_id ON ai_compliance_notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_ai_notifications_is_read ON ai_compliance_notifications(is_read);
CREATE INDEX IF NOT EXISTS idx_ai_notifications_created_at ON ai_compliance_notifications(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_ai_scheduled_scans_next_run ON ai_scheduled_scans(next_run_at) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_ai_scheduled_scans_user ON ai_scheduled_scans(user_id);

COMMIT;
