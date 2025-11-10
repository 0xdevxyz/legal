#!/bin/bash
# Initialize all database tables for Complyo

echo "🔧 Initializing all database tables..."

SQL_FILES=(
    "database_setup.sql"
    "init_auth_tables.sql"
    "init_user_limits.sql"
    "init_scan_history.sql"
    "init_legal_news_table.sql"
    "init_cookie_compliance.sql"
    "init_company_data.sql"
    "init_documents_table.sql"
    "init_website_structures.sql"
    "init_risk_matrix.sql"
    "init_erecht24_projects.sql"
    "init_legal_updates.sql"
    "init_score_history.sql"
    "migration_freemium_model.sql"
    "migration_ai_compliance.sql"
)

for file in "${SQL_FILES[@]}"; do
    if [ -f "/opt/projects/saas-project-2/backend/$file" ]; then
        echo "⏳ Executing $file..."
        docker exec complyo-postgres psql -U complyo_user -d complyo_db -f "/tmp/$file" 2>&1 | grep -E "CREATE|ALTER|ERROR" | head -5
    fi
done

# Separate handling for fix_jobs (has schema issues, need to fix first)
echo "⏳ Creating fix_jobs table with corrected schema..."
docker exec complyo-postgres psql -U complyo_user -d complyo_db << 'EOF'
-- Fix jobs table with corrected user_id type
CREATE TABLE IF NOT EXISTS fix_jobs (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    scan_id VARCHAR(255),
    issue_category VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    priority INTEGER DEFAULT 0,
    fix_data JSONB,
    generated_content TEXT,
    implementation_guide TEXT,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_fix_jobs_user_id ON fix_jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_fix_jobs_status ON fix_jobs(status);
CREATE INDEX IF NOT EXISTS idx_fix_jobs_created_at ON fix_jobs(created_at);
CREATE INDEX IF NOT EXISTS idx_fix_jobs_priority ON fix_jobs(priority DESC);

-- Cookie compliance stats
CREATE TABLE IF NOT EXISTS cookie_compliance_stats (
    id SERIAL PRIMARY KEY,
    website_id UUID,
    site_identifier VARCHAR(255) NOT NULL,
    date DATE DEFAULT CURRENT_DATE,
    consents_total INTEGER DEFAULT 0,
    consents_accepted INTEGER DEFAULT 0,
    consents_rejected INTEGER DEFAULT 0,
    consents_custom INTEGER DEFAULT 0,
    unique_visitors INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cookie_stats_site ON cookie_compliance_stats(site_identifier, date);
EOF

echo "✅ All tables initialized!"
