-- Add Lead Management Tables for GDPR Compliance
-- Run this after the main database_setup.sql

-- Add verification token tracking
CREATE TYPE verification_status AS ENUM ('pending', 'verified', 'expired', 'invalid');
CREATE TYPE lead_status AS ENUM ('new', 'verified', 'converted', 'unsubscribed');
CREATE TYPE consent_type AS ENUM ('marketing', 'analysis', 'report_download');

-- Leads table for GDPR-compliant lead management
CREATE TABLE IF NOT EXISTS leads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Contact Information
    email VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    company VARCHAR(255),
    
    -- Data Source & Context
    source VARCHAR(100) DEFAULT 'landing_page',
    url_analyzed VARCHAR(500),
    analysis_data JSONB,
    session_id VARCHAR(255),
    
    -- GDPR Compliance
    consent_given BOOLEAN DEFAULT FALSE,
    consent_timestamp TIMESTAMP WITH TIME ZONE,
    consent_ip_address INET,
    consent_user_agent TEXT,
    legal_basis VARCHAR(100) DEFAULT 'consent', -- GDPR Article 6
    
    -- Verification Status
    email_verified BOOLEAN DEFAULT FALSE,
    verification_token VARCHAR(255) UNIQUE,
    verification_sent_at TIMESTAMP WITH TIME ZONE,
    verification_expires_at TIMESTAMP WITH TIME ZONE,
    verified_at TIMESTAMP WITH TIME ZONE,
    
    -- Lead Status
    status lead_status DEFAULT 'new',
    
    -- Tracking
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_contacted TIMESTAMP WITH TIME ZONE,
    
    -- Data Retention
    data_retention_until TIMESTAMP WITH TIME ZONE,
    deletion_requested BOOLEAN DEFAULT FALSE,
    deletion_requested_at TIMESTAMP WITH TIME ZONE
);

-- Consent tracking table for detailed GDPR compliance
CREATE TABLE IF NOT EXISTS lead_consents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    consent_type consent_type NOT NULL,
    granted BOOLEAN NOT NULL,
    granted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    user_agent TEXT,
    withdrawal_requested BOOLEAN DEFAULT FALSE,
    withdrawn_at TIMESTAMP WITH TIME ZONE
);

-- Email verification attempts
CREATE TABLE IF NOT EXISTS email_verifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    verification_token VARCHAR(255) NOT NULL,
    status verification_status DEFAULT 'pending',
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    verified_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP + INTERVAL '24 hours'),
    attempts INTEGER DEFAULT 0,
    ip_address INET,
    user_agent TEXT
);

-- Marketing communications log (GDPR Article 7 - proof of consent)
CREATE TABLE IF NOT EXISTS communication_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lead_id UUID NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
    type VARCHAR(100) NOT NULL, -- 'verification', 'report', 'marketing', 'gdpr_notice'
    subject VARCHAR(255),
    content TEXT,
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    delivery_status VARCHAR(50) DEFAULT 'pending',
    opened BOOLEAN DEFAULT FALSE,
    clicked BOOLEAN DEFAULT FALSE,
    bounced BOOLEAN DEFAULT FALSE
);

-- Create indexes for performance
CREATE INDEX idx_leads_email ON leads(email);
CREATE INDEX idx_leads_verification_token ON leads(verification_token);
CREATE INDEX idx_leads_status ON leads(status);
CREATE INDEX idx_leads_created_at ON leads(created_at DESC);
CREATE INDEX idx_email_verifications_token ON email_verifications(verification_token);
CREATE INDEX idx_email_verifications_expires ON email_verifications(expires_at);
CREATE INDEX idx_lead_consents_lead_id ON lead_consents(lead_id);
CREATE INDEX idx_communication_log_lead_id ON communication_log(lead_id);

-- Add trigger for updated_at
CREATE TRIGGER update_leads_updated_at BEFORE UPDATE ON leads
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO complyo_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO complyo_user;

-- Sample GDPR-compliant data (for testing)
INSERT INTO leads (
    email, 
    name, 
    company, 
    source, 
    consent_given,
    consent_timestamp,
    legal_basis,
    verification_token,
    verification_expires_at,
    data_retention_until
) VALUES (
    'test@example.com',
    'Test User',
    'Test Company',
    'landing_page',
    TRUE,
    CURRENT_TIMESTAMP,
    'consent',
    gen_random_uuid()::text,
    CURRENT_TIMESTAMP + INTERVAL '24 hours',
    CURRENT_TIMESTAMP + INTERVAL '2 years'
) ON CONFLICT DO NOTHING;