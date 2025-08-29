-- Workflow Database Tables for Complyo
-- Complete user journey tracking and workflow management

-- User journeys table (Complete workflow tracking)
CREATE TABLE IF NOT EXISTS user_journeys (
    id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    journey_data JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_user_journey (user_id)
);

-- User assessments table (Skill level, preferences, etc.)
CREATE TABLE IF NOT EXISTS user_assessments (
    id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    assessment_type VARCHAR(100) NOT NULL,
    answers JSON NOT NULL,
    skill_level VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_user_assessment (user_id, assessment_type)
);

-- Compliance certificates table (Generated certificates)
CREATE TABLE IF NOT EXISTS compliance_certificates (
    id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    certificate_id VARCHAR(100) UNIQUE NOT NULL,
    journey_data JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NULL,
    is_valid BOOLEAN DEFAULT TRUE
);

-- Monitoring configs table (24/7 monitoring settings)
CREATE TABLE IF NOT EXISTS monitoring_configs (
    id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    website_url VARCHAR(500) NOT NULL,
    frequency ENUM('hourly', 'daily', 'weekly', 'monthly') DEFAULT 'daily',
    active BOOLEAN DEFAULT TRUE,
    last_check TIMESTAMP NULL,
    next_check TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_monitoring_config (user_id, website_url)
);

-- Workflow step completions table (Individual step tracking)
CREATE TABLE IF NOT EXISTS workflow_step_completions (
    id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    journey_id VARCHAR(255),
    step_id VARCHAR(100) NOT NULL,
    stage VARCHAR(50) NOT NULL,
    validation_data JSON,
    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    retry_count INT DEFAULT 0,
    success BOOLEAN DEFAULT TRUE,
    validation_message TEXT,
    INDEX idx_user_journey (user_id, journey_id),
    INDEX idx_step_stage (step_id, stage)
);

-- Support interactions table (User help and support)
CREATE TABLE IF NOT EXISTS support_interactions (
    id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    journey_id VARCHAR(255) NULL,
    step_id VARCHAR(100) NULL,
    interaction_type ENUM('help_request', 'chat', 'email', 'call') DEFAULT 'help_request',
    subject VARCHAR(200),
    message TEXT,
    status ENUM('open', 'in_progress', 'resolved', 'closed') DEFAULT 'open',
    priority ENUM('low', 'medium', 'high', 'urgent') DEFAULT 'medium',
    assigned_to VARCHAR(255) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP NULL,
    INDEX idx_user_status (user_id, status),
    INDEX idx_created_priority (created_at, priority)
);

-- Journey analytics table (Performance metrics and insights)
CREATE TABLE IF NOT EXISTS journey_analytics (
    id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    journey_id VARCHAR(255) NOT NULL,
    skill_level VARCHAR(50),
    total_time_minutes INT,
    completion_rate DECIMAL(5,2),
    total_failures INT DEFAULT 0,
    most_difficult_step VARCHAR(100),
    satisfaction_score DECIMAL(3,2) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_journey_metrics (journey_id, completion_rate),
    INDEX idx_skill_performance (skill_level, total_time_minutes)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_journeys_user_id ON user_journeys(user_id);
CREATE INDEX IF NOT EXISTS idx_user_journeys_created ON user_journeys(created_at);
CREATE INDEX IF NOT EXISTS idx_user_assessments_user_id ON user_assessments(user_id);
CREATE INDEX IF NOT EXISTS idx_user_assessments_type ON user_assessments(assessment_type);
CREATE INDEX IF NOT EXISTS idx_compliance_certificates_user_id ON compliance_certificates(user_id);
CREATE INDEX IF NOT EXISTS idx_compliance_certificates_valid ON compliance_certificates(is_valid);
CREATE INDEX IF NOT EXISTS idx_monitoring_configs_active ON monitoring_configs(active);
CREATE INDEX IF NOT EXISTS idx_monitoring_configs_next_check ON monitoring_configs(next_check);

-- Insert sample data for testing
INSERT IGNORE INTO user_journeys (id, user_id, journey_data) VALUES 
('journey_demo_001', 'demo_user', JSON_OBJECT(
    'user_id', 'demo_user',
    'website_url', 'https://example-website.de',
    'skill_level', 'beginner',
    'current_stage', 'onboarding',
    'current_step', 'welcome_tour',
    'completed_steps', JSON_ARRAY(),
    'failed_attempts', JSON_OBJECT(),
    'start_date', '2024-01-01T10:00:00',
    'estimated_completion', '2024-01-08T10:00:00',
    'actual_completion', NULL,
    'satisfaction_score', NULL,
    'support_interactions', JSON_ARRAY()
));

INSERT IGNORE INTO user_assessments (id, user_id, assessment_type, answers, skill_level) VALUES
('assessment_demo_001', 'demo_user', 'skill_assessment', JSON_OBJECT(
    'website_experience', 'basic',
    'html_css_knowledge', false,
    'cms_experience', 'wordpress',
    'gdpr_knowledge', false,
    'technical_comfort', 3
), 'beginner');

-- Add workflow-specific triggers for updated_at
DELIMITER //

CREATE TRIGGER IF NOT EXISTS update_user_journeys_updated_at 
    BEFORE UPDATE ON user_journeys 
    FOR EACH ROW 
    BEGIN 
        SET NEW.updated_at = CURRENT_TIMESTAMP; 
    END//

CREATE TRIGGER IF NOT EXISTS update_user_assessments_updated_at 
    BEFORE UPDATE ON user_assessments 
    FOR EACH ROW 
    BEGIN 
        SET NEW.updated_at = CURRENT_TIMESTAMP; 
    END//

CREATE TRIGGER IF NOT EXISTS update_monitoring_configs_updated_at 
    BEFORE UPDATE ON monitoring_configs 
    FOR EACH ROW 
    BEGIN 
        SET NEW.updated_at = CURRENT_TIMESTAMP; 
    END//

DELIMITER ;

-- Workflow completion views for analytics
CREATE OR REPLACE VIEW workflow_completion_stats AS
SELECT 
    skill_level,
    COUNT(*) as total_journeys,
    AVG(total_time_minutes) as avg_completion_time,
    AVG(completion_rate) as avg_completion_rate,
    AVG(satisfaction_score) as avg_satisfaction
FROM journey_analytics
WHERE completion_rate > 0
GROUP BY skill_level;

CREATE OR REPLACE VIEW step_difficulty_analysis AS
SELECT 
    most_difficult_step,
    COUNT(*) as failure_count,
    AVG(total_failures) as avg_failures_per_journey
FROM journey_analytics
WHERE most_difficult_step IS NOT NULL
GROUP BY most_difficult_step
ORDER BY failure_count DESC;

-- Grant necessary permissions (adjust as needed)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON user_journeys TO 'complyo_user'@'%';
-- GRANT SELECT, INSERT, UPDATE, DELETE ON user_assessments TO 'complyo_user'@'%';
-- GRANT SELECT, INSERT, UPDATE, DELETE ON compliance_certificates TO 'complyo_user'@'%';
-- GRANT SELECT, INSERT, UPDATE, DELETE ON monitoring_configs TO 'complyo_user'@'%';
-- GRANT SELECT, INSERT, UPDATE, DELETE ON workflow_step_completions TO 'complyo_user'@'%';
-- GRANT SELECT, INSERT, UPDATE, DELETE ON support_interactions TO 'complyo_user'@'%';
-- GRANT SELECT, INSERT, UPDATE, DELETE ON journey_analytics TO 'complyo_user'@'%';