"""
Complyo Database Models - Production PostgreSQL Integration
Complete database schema for all platform features
"""

import asyncio
import asyncpg
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import uuid
import os
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UserSubscriptionStatus(Enum):
    TRIAL = "trial"
    ACTIVE = "active"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    SUSPENDED = "suspended"

class ScanStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class MonitoringFrequency(Enum):
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"

class AlertSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class DatabaseConfig:
    """Database configuration"""
    host: str = "localhost"
    port: int = 5432
    database: str = "complyo_production"
    user: str = "complyo_user"
    password: str = "complyo_password"
    min_connections: int = 5
    max_connections: int = 20
    ssl_mode: str = "prefer"
    
    @classmethod
    def from_env(cls):
        """Create config from environment variables"""
        return cls(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5432")),
            database=os.getenv("DB_NAME", "complyo_production"),
            user=os.getenv("DB_USER", "complyo_user"),
            password=os.getenv("DB_PASSWORD", "complyo_password"),
            min_connections=int(os.getenv("DB_MIN_CONNECTIONS", "5")),
            max_connections=int(os.getenv("DB_MAX_CONNECTIONS", "20"))
        )

class DatabaseManager:
    """Comprehensive database manager for Complyo platform"""
    
    def __init__(self, config: DatabaseConfig = None):
        """Initialize database manager"""
        
        self.config = config or DatabaseConfig.from_env()
        self.pool: Optional[asyncpg.Pool] = None
        self.is_connected = False
        
        # Database schema version for migrations
        self.schema_version = "1.0.0"
        
    async def connect(self) -> bool:
        """Connect to PostgreSQL database"""
        
        try:
            # Create connection pool
            dsn = f"postgresql://{self.config.user}:{self.config.password}@{self.config.host}:{self.config.port}/{self.config.database}"
            
            self.pool = await asyncpg.create_pool(
                dsn,
                min_size=self.config.min_connections,
                max_size=self.config.max_connections,
                command_timeout=30
            )
            
            # Test connection
            async with self.pool.acquire() as conn:
                await conn.execute("SELECT 1")
            
            self.is_connected = True
            logger.info(f"🗄️ Connected to PostgreSQL: {self.config.database}")
            
            # Initialize schema
            await self.initialize_schema()
            
            return True
            
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            self.is_connected = False
            return False
    
    async def disconnect(self):
        """Disconnect from database"""
        
        if self.pool:
            await self.pool.close()
            self.is_connected = False
            logger.info("🗄️ Database connection closed")
    
    async def initialize_schema(self):
        """Initialize database schema with all tables"""
        
        schema_sql = """
        -- Users table
        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            first_name VARCHAR(100) NOT NULL,
            last_name VARCHAR(100) NOT NULL,
            company_name VARCHAR(255),
            phone VARCHAR(50),
            website VARCHAR(255),
            subscription_status VARCHAR(20) DEFAULT 'trial',
            subscription_id VARCHAR(100),
            trial_expires_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            last_login_at TIMESTAMPTZ,
            email_verified BOOLEAN DEFAULT FALSE,
            email_verification_token VARCHAR(255),
            password_reset_token VARCHAR(255),
            password_reset_expires_at TIMESTAMPTZ,
            metadata JSONB DEFAULT '{}'
        );
        
        -- Websites table (monitoring targets)
        CREATE TABLE IF NOT EXISTS websites (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            url VARCHAR(500) NOT NULL,
            name VARCHAR(255) NOT NULL,
            monitoring_frequency VARCHAR(20) DEFAULT 'daily',
            is_active BOOLEAN DEFAULT TRUE,
            alert_thresholds JSONB DEFAULT '{}',
            notification_preferences JSONB DEFAULT '{}',
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            last_scan_at TIMESTAMPTZ,
            metadata JSONB DEFAULT '{}'
        );
        
        -- Compliance scans table
        CREATE TABLE IF NOT EXISTS compliance_scans (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            website_id UUID NOT NULL REFERENCES websites(id) ON DELETE CASCADE,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            scan_type VARCHAR(50) DEFAULT 'full',
            status VARCHAR(20) DEFAULT 'pending',
            overall_score DECIMAL(5,2),
            total_issues INTEGER DEFAULT 0,
            critical_issues INTEGER DEFAULT 0,
            warning_issues INTEGER DEFAULT 0,
            total_risk_euro INTEGER DEFAULT 0,
            scan_results JSONB DEFAULT '{}',
            technical_analysis JSONB DEFAULT '{}',
            recommendations JSONB DEFAULT '[]',
            started_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMPTZ,
            scan_duration_ms INTEGER,
            scanner_version VARCHAR(20),
            metadata JSONB DEFAULT '{}'
        );
        
        -- Compliance issues table
        CREATE TABLE IF NOT EXISTS compliance_issues (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            scan_id UUID NOT NULL REFERENCES compliance_scans(id) ON DELETE CASCADE,
            category VARCHAR(100) NOT NULL,
            subcategory VARCHAR(100),
            severity VARCHAR(20) NOT NULL,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            recommendation TEXT,
            legal_basis VARCHAR(255),
            risk_euro INTEGER DEFAULT 0,
            is_auto_fixable BOOLEAN DEFAULT FALSE,
            is_resolved BOOLEAN DEFAULT FALSE,
            resolved_at TIMESTAMPTZ,
            resolution_method VARCHAR(100),
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            metadata JSONB DEFAULT '{}'
        );
        
        -- Monitoring alerts table
        CREATE TABLE IF NOT EXISTS monitoring_alerts (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            website_id UUID NOT NULL REFERENCES websites(id) ON DELETE CASCADE,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            alert_type VARCHAR(50) NOT NULL,
            severity VARCHAR(20) NOT NULL,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            alert_data JSONB DEFAULT '{}',
            is_resolved BOOLEAN DEFAULT FALSE,
            resolved_at TIMESTAMPTZ,
            resolution_notes TEXT,
            triggered_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            acknowledged_at TIMESTAMPTZ,
            notification_sent BOOLEAN DEFAULT FALSE,
            metadata JSONB DEFAULT '{}'
        );
        
        -- Email messages table
        CREATE TABLE IF NOT EXISTS email_messages (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            message_id VARCHAR(255) UNIQUE NOT NULL,
            user_id UUID REFERENCES users(id) ON DELETE SET NULL,
            template_id VARCHAR(100),
            to_addresses JSONB NOT NULL,
            subject VARCHAR(500) NOT NULL,
            html_content TEXT,
            text_content TEXT,
            attachments JSONB DEFAULT '[]',
            priority VARCHAR(20) DEFAULT 'normal',
            status VARCHAR(20) DEFAULT 'pending',
            sent_at TIMESTAMPTZ,
            delivered_at TIMESTAMPTZ,
            opened_at TIMESTAMPTZ,
            clicked_at TIMESTAMPTZ,
            error_message TEXT,
            retry_count INTEGER DEFAULT 0,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            metadata JSONB DEFAULT '{}'
        );
        
        -- Subscriptions table (Stripe integration)
        CREATE TABLE IF NOT EXISTS subscriptions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            stripe_subscription_id VARCHAR(255) UNIQUE,
            stripe_customer_id VARCHAR(255),
            plan_name VARCHAR(100) NOT NULL,
            plan_type VARCHAR(50) NOT NULL,
            status VARCHAR(20) NOT NULL,
            current_period_start TIMESTAMPTZ,
            current_period_end TIMESTAMPTZ,
            amount_cents INTEGER NOT NULL,
            currency VARCHAR(3) DEFAULT 'EUR',
            trial_end TIMESTAMPTZ,
            canceled_at TIMESTAMPTZ,
            cancel_at_period_end BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            metadata JSONB DEFAULT '{}'
        );
        
        -- Payments table
        CREATE TABLE IF NOT EXISTS payments (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            subscription_id UUID REFERENCES subscriptions(id) ON DELETE SET NULL,
            stripe_payment_id VARCHAR(255) UNIQUE,
            stripe_invoice_id VARCHAR(255),
            amount_cents INTEGER NOT NULL,
            currency VARCHAR(3) DEFAULT 'EUR',
            status VARCHAR(20) NOT NULL,
            payment_method VARCHAR(50),
            description TEXT,
            paid_at TIMESTAMPTZ,
            refunded_at TIMESTAMPTZ,
            refund_amount_cents INTEGER DEFAULT 0,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            metadata JSONB DEFAULT '{}'
        );
        
        -- Expert consultations table
        CREATE TABLE IF NOT EXISTS expert_consultations (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            expert_id UUID REFERENCES users(id) ON DELETE SET NULL,
            consultation_type VARCHAR(50) NOT NULL,
            status VARCHAR(20) DEFAULT 'requested',
            title VARCHAR(255) NOT NULL,
            description TEXT,
            priority VARCHAR(20) DEFAULT 'medium',
            website_urls JSONB DEFAULT '[]',
            scheduled_at TIMESTAMPTZ,
            duration_minutes INTEGER DEFAULT 60,
            meeting_link VARCHAR(500),
            consultation_notes TEXT,
            follow_up_required BOOLEAN DEFAULT FALSE,
            follow_up_date TIMESTAMPTZ,
            completed_at TIMESTAMPTZ,
            rating INTEGER CHECK (rating >= 1 AND rating <= 5),
            feedback TEXT,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            metadata JSONB DEFAULT '{}'
        );
        
        -- Generated documents table (AI fixes, legal docs)
        CREATE TABLE IF NOT EXISTS generated_documents (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            scan_id UUID REFERENCES compliance_scans(id) ON DELETE SET NULL,
            document_type VARCHAR(100) NOT NULL,
            title VARCHAR(255) NOT NULL,
            content TEXT,
            file_format VARCHAR(20) DEFAULT 'html',
            file_size INTEGER,
            download_count INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT TRUE,
            expires_at TIMESTAMPTZ,
            generation_parameters JSONB DEFAULT '{}',
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            metadata JSONB DEFAULT '{}'
        );
        
        -- Analytics and tracking table
        CREATE TABLE IF NOT EXISTS analytics_events (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID REFERENCES users(id) ON DELETE SET NULL,
            session_id VARCHAR(255),
            event_type VARCHAR(100) NOT NULL,
            event_name VARCHAR(100) NOT NULL,
            event_data JSONB DEFAULT '{}',
            page_url VARCHAR(500),
            referrer VARCHAR(500),
            user_agent TEXT,
            ip_hash VARCHAR(255),
            country VARCHAR(2),
            city VARCHAR(100),
            timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            metadata JSONB DEFAULT '{}'
        );
        
        -- Cookie consent records table (TTDSG compliance)
        CREATE TABLE IF NOT EXISTS cookie_consents (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_identifier VARCHAR(255) NOT NULL,
            website_domain VARCHAR(255) NOT NULL,
            consent_id VARCHAR(255) UNIQUE NOT NULL,
            categories_consented JSONB NOT NULL,
            consent_string TEXT,
            ip_hash VARCHAR(255),
            user_agent_hash VARCHAR(255),
            consent_given_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMPTZ,
            withdrawn_at TIMESTAMPTZ,
            is_valid BOOLEAN DEFAULT TRUE,
            consent_version VARCHAR(20) DEFAULT '1.0',
            metadata JSONB DEFAULT '{}'
        );
        
        -- API keys and integrations table
        CREATE TABLE IF NOT EXISTS api_integrations (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            integration_type VARCHAR(50) NOT NULL,
            api_key_hash VARCHAR(255),
            configuration JSONB DEFAULT '{}',
            is_active BOOLEAN DEFAULT TRUE,
            last_used_at TIMESTAMPTZ,
            usage_count INTEGER DEFAULT 0,
            rate_limit_remaining INTEGER,
            rate_limit_reset_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            metadata JSONB DEFAULT '{}'
        );
        
        -- User optimization progress table (AI-guided process)
        CREATE TABLE IF NOT EXISTS user_optimization_progress (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            website_id UUID REFERENCES websites(id) ON DELETE CASCADE,
            analysis_id VARCHAR(255),
            progress_data JSONB DEFAULT '{}',
            completion_percentage INTEGER DEFAULT 0,
            current_step VARCHAR(255),
            started_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMPTZ,
            last_activity_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            metadata JSONB DEFAULT '{}',
            CONSTRAINT unique_user_optimization_progress UNIQUE (user_id)
        );
        
        -- Create indexes for performance
        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
        CREATE INDEX IF NOT EXISTS idx_users_subscription_status ON users(subscription_status);
        CREATE INDEX IF NOT EXISTS idx_websites_user_id ON websites(user_id);
        CREATE INDEX IF NOT EXISTS idx_websites_url ON websites(url);
        CREATE INDEX IF NOT EXISTS idx_compliance_scans_user_id ON compliance_scans(user_id);
        CREATE INDEX IF NOT EXISTS idx_compliance_scans_website_id ON compliance_scans(website_id);
        CREATE INDEX IF NOT EXISTS idx_compliance_scans_status ON compliance_scans(status);
        CREATE INDEX IF NOT EXISTS idx_compliance_scans_started_at ON compliance_scans(started_at);
        CREATE INDEX IF NOT EXISTS idx_compliance_issues_scan_id ON compliance_issues(scan_id);
        CREATE INDEX IF NOT EXISTS idx_compliance_issues_category ON compliance_issues(category);
        CREATE INDEX IF NOT EXISTS idx_compliance_issues_severity ON compliance_issues(severity);
        CREATE INDEX IF NOT EXISTS idx_monitoring_alerts_user_id ON monitoring_alerts(user_id);
        CREATE INDEX IF NOT EXISTS idx_monitoring_alerts_website_id ON monitoring_alerts(website_id);
        CREATE INDEX IF NOT EXISTS idx_monitoring_alerts_severity ON monitoring_alerts(severity);
        CREATE INDEX IF NOT EXISTS idx_monitoring_alerts_triggered_at ON monitoring_alerts(triggered_at);
        CREATE INDEX IF NOT EXISTS idx_email_messages_user_id ON email_messages(user_id);
        CREATE INDEX IF NOT EXISTS idx_email_messages_status ON email_messages(status);
        CREATE INDEX IF NOT EXISTS idx_email_messages_sent_at ON email_messages(sent_at);
        CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON subscriptions(user_id);
        CREATE INDEX IF NOT EXISTS idx_subscriptions_stripe_id ON subscriptions(stripe_subscription_id);
        CREATE INDEX IF NOT EXISTS idx_payments_user_id ON payments(user_id);
        CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);
        CREATE INDEX IF NOT EXISTS idx_expert_consultations_user_id ON expert_consultations(user_id);
        CREATE INDEX IF NOT EXISTS idx_expert_consultations_status ON expert_consultations(status);
        CREATE INDEX IF NOT EXISTS idx_generated_documents_user_id ON generated_documents(user_id);
        CREATE INDEX IF NOT EXISTS idx_analytics_events_user_id ON analytics_events(user_id);
        CREATE INDEX IF NOT EXISTS idx_analytics_events_timestamp ON analytics_events(timestamp);
        CREATE INDEX IF NOT EXISTS idx_cookie_consents_user_identifier ON cookie_consents(user_identifier);
        CREATE INDEX IF NOT EXISTS idx_cookie_consents_website_domain ON cookie_consents(website_domain);
        CREATE INDEX IF NOT EXISTS idx_api_integrations_user_id ON api_integrations(user_id);
        CREATE INDEX IF NOT EXISTS idx_user_optimization_progress_user_id ON user_optimization_progress(user_id);
        CREATE INDEX IF NOT EXISTS idx_user_optimization_progress_website_id ON user_optimization_progress(website_id);
        
        -- Update triggers for updated_at columns
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        
        DROP TRIGGER IF EXISTS update_users_updated_at ON users;
        CREATE TRIGGER update_users_updated_at 
            BEFORE UPDATE ON users 
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
            
        DROP TRIGGER IF EXISTS update_websites_updated_at ON websites;
        CREATE TRIGGER update_websites_updated_at 
            BEFORE UPDATE ON websites 
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
            
        DROP TRIGGER IF EXISTS update_subscriptions_updated_at ON subscriptions;
        CREATE TRIGGER update_subscriptions_updated_at 
            BEFORE UPDATE ON subscriptions 
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
            
        DROP TRIGGER IF EXISTS update_expert_consultations_updated_at ON expert_consultations;
        CREATE TRIGGER update_expert_consultations_updated_at 
            BEFORE UPDATE ON expert_consultations 
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
            
        DROP TRIGGER IF EXISTS update_generated_documents_updated_at ON generated_documents;
        CREATE TRIGGER update_generated_documents_updated_at 
            BEFORE UPDATE ON generated_documents 
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
            
        DROP TRIGGER IF EXISTS update_api_integrations_updated_at ON api_integrations;
        CREATE TRIGGER update_api_integrations_updated_at 
            BEFORE UPDATE ON api_integrations 
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        """
        
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(schema_sql)
            
            logger.info(f"✅ Database schema initialized (v{self.schema_version})")
            
        except Exception as e:
            logger.error(f"Schema initialization failed: {str(e)}")
            raise
    
    # ========== USER MANAGEMENT ==========
    
    async def create_user(self, user_data: Dict[str, Any]) -> Optional[str]:
        """Create new user and return user ID"""
        
        try:
            sql = """
            INSERT INTO users (email, password_hash, first_name, last_name, 
                             company_name, phone, website, trial_expires_at, metadata)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING id
            """
            
            trial_expires = datetime.now() + timedelta(days=7)
            
            async with self.pool.acquire() as conn:
                user_id = await conn.fetchval(
                    sql,
                    user_data["email"],
                    user_data["password_hash"],
                    user_data["first_name"],
                    user_data["last_name"],
                    user_data.get("company_name"),
                    user_data.get("phone"),
                    user_data.get("website"),
                    trial_expires,
                    json.dumps(user_data.get("metadata", {}))
                )
            
            logger.info(f"👤 User created: {user_data['email']}")
            return str(user_id)
            
        except Exception as e:
            logger.error(f"User creation failed: {str(e)}")
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email address"""
        
        try:
            sql = """
            SELECT id, email, password_hash, first_name, last_name, company_name,
                   phone, website, subscription_status, created_at, last_login_at,
                   email_verified, trial_expires_at, metadata
            FROM users WHERE email = $1
            """
            
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(sql, email)
            
            if row:
                return dict(row)
            return None
            
        except Exception as e:
            logger.error(f"User lookup failed: {str(e)}")
            return None
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        
        try:
            sql = """
            SELECT id, email, password_hash, first_name, last_name, company_name,
                   phone, website, subscription_status, created_at, last_login_at,
                   email_verified, trial_expires_at, metadata
            FROM users WHERE id = $1
            """
            
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(sql, user_id)
            
            if row:
                return dict(row)
            return None
            
        except Exception as e:
            logger.error(f"User lookup failed: {str(e)}")
            return None
    
    async def update_user(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """Update user information"""
        
        try:
            # Build dynamic UPDATE query
            set_clauses = []
            values = []
            param_count = 1
            
            for field, value in updates.items():
                if field in ["first_name", "last_name", "company_name", "phone", "website", 
                           "subscription_status", "last_login_at", "email_verified", "metadata"]:
                    set_clauses.append(f"{field} = ${param_count}")
                    if field == "metadata":
                        values.append(json.dumps(value))
                    else:
                        values.append(value)
                    param_count += 1
            
            if not set_clauses:
                return False
            
            values.append(user_id)  # For WHERE clause
            
            sql = f"""
            UPDATE users 
            SET {', '.join(set_clauses)}, updated_at = CURRENT_TIMESTAMP
            WHERE id = ${param_count}
            """
            
            async with self.pool.acquire() as conn:
                result = await conn.execute(sql, *values)
            
            return "UPDATE 1" in result
            
        except Exception as e:
            logger.error(f"User update failed: {str(e)}")
            return False
    
    # ========== WEBSITE MANAGEMENT ==========
    
    async def create_website(self, user_id: str, website_data: Dict[str, Any]) -> Optional[str]:
        """Create new website monitoring target"""
        
        try:
            sql = """
            INSERT INTO websites (user_id, url, name, monitoring_frequency,
                                alert_thresholds, notification_preferences, metadata)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id
            """
            
            async with self.pool.acquire() as conn:
                website_id = await conn.fetchval(
                    sql,
                    user_id,
                    website_data["url"],
                    website_data["name"],
                    website_data.get("monitoring_frequency", "daily"),
                    json.dumps(website_data.get("alert_thresholds", {})),
                    json.dumps(website_data.get("notification_preferences", {})),
                    json.dumps(website_data.get("metadata", {}))
                )
            
            logger.info(f"🌐 Website created: {website_data['url']}")
            return str(website_id)
            
        except Exception as e:
            logger.error(f"Website creation failed: {str(e)}")
            return None
    
    async def get_user_websites(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all websites for user"""
        
        try:
            sql = """
            SELECT id, url, name, monitoring_frequency, is_active, 
                   alert_thresholds, notification_preferences, created_at,
                   updated_at, last_scan_at, metadata
            FROM websites 
            WHERE user_id = $1 AND is_active = TRUE
            ORDER BY created_at DESC
            """
            
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(sql, user_id)
            
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Website lookup failed: {str(e)}")
            return []
    
    # ========== COMPLIANCE SCANS ==========
    
    async def create_compliance_scan(self, scan_data: Dict[str, Any]) -> Optional[str]:
        """Create new compliance scan record"""
        
        try:
            sql = """
            INSERT INTO compliance_scans (website_id, user_id, scan_type, overall_score,
                                        total_issues, critical_issues, warning_issues, 
                                        total_risk_euro, scan_results, technical_analysis,
                                        recommendations, completed_at, scan_duration_ms,
                                        scanner_version, metadata)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
            RETURNING id
            """
            
            async with self.pool.acquire() as conn:
                scan_id = await conn.fetchval(
                    sql,
                    scan_data.get("website_id"),
                    scan_data["user_id"],
                    scan_data.get("scan_type", "full"),
                    scan_data.get("overall_score"),
                    scan_data.get("total_issues", 0),
                    scan_data.get("critical_issues", 0),
                    scan_data.get("warning_issues", 0),
                    scan_data.get("total_risk_euro", 0),
                    json.dumps(scan_data.get("scan_results", {})),
                    json.dumps(scan_data.get("technical_analysis", {})),
                    json.dumps(scan_data.get("recommendations", [])),
                    datetime.now(),
                    scan_data.get("scan_duration_ms"),
                    scan_data.get("scanner_version", "3.0.0"),
                    json.dumps(scan_data.get("metadata", {}))
                )
            
            # Update website last_scan_at
            if scan_data.get("website_id"):
                await self.update_website_last_scan(scan_data["website_id"])
            
            logger.info(f"📊 Compliance scan created: {scan_id}")
            return str(scan_id)
            
        except Exception as e:
            logger.error(f"Scan creation failed: {str(e)}")
            return None
    
    async def get_user_scans(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get compliance scans for user"""
        
        try:
            sql = """
            SELECT cs.*, w.url as website_url, w.name as website_name
            FROM compliance_scans cs
            JOIN websites w ON cs.website_id = w.id
            WHERE cs.user_id = $1
            ORDER BY cs.started_at DESC
            LIMIT $2
            """
            
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(sql, user_id, limit)
            
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Scan lookup failed: {str(e)}")
            return []
    
    async def update_website_last_scan(self, website_id: str):
        """Update website last scan timestamp"""
        
        try:
            sql = "UPDATE websites SET last_scan_at = CURRENT_TIMESTAMP WHERE id = $1"
            
            async with self.pool.acquire() as conn:
                await conn.execute(sql, website_id)
                
        except Exception as e:
            logger.error(f"Website update failed: {str(e)}")
    
    # ========== MONITORING & ALERTS ==========
    
    async def create_monitoring_alert(self, alert_data: Dict[str, Any]) -> Optional[str]:
        """Create monitoring alert"""
        
        try:
            sql = """
            INSERT INTO monitoring_alerts (website_id, user_id, alert_type, severity,
                                         title, description, alert_data, metadata)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id
            """
            
            async with self.pool.acquire() as conn:
                alert_id = await conn.fetchval(
                    sql,
                    alert_data.get("website_id"),
                    alert_data["user_id"],
                    alert_data["alert_type"],
                    alert_data["severity"],
                    alert_data["title"],
                    alert_data.get("description"),
                    json.dumps(alert_data.get("alert_data", {})),
                    json.dumps(alert_data.get("metadata", {}))
                )
            
            logger.info(f"🚨 Alert created: {alert_data['alert_type']}")
            return str(alert_id)
            
        except Exception as e:
            logger.error(f"Alert creation failed: {str(e)}")
            return None
    
    async def get_user_alerts(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get monitoring alerts for user"""
        
        try:
            sql = """
            SELECT ma.*, w.url as website_url, w.name as website_name
            FROM monitoring_alerts ma
            JOIN websites w ON ma.website_id = w.id
            WHERE ma.user_id = $1
            ORDER BY ma.triggered_at DESC
            LIMIT $2
            """
            
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(sql, user_id, limit)
            
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Alert lookup failed: {str(e)}")
            return []
    
    # ========== EMAIL TRACKING ==========
    
    async def create_email_record(self, email_data: Dict[str, Any]) -> Optional[str]:
        """Create email delivery record"""
        
        try:
            sql = """
            INSERT INTO email_messages (message_id, user_id, template_id, to_addresses,
                                      subject, html_content, text_content, attachments,
                                      priority, status, metadata)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            RETURNING id
            """
            
            async with self.pool.acquire() as conn:
                record_id = await conn.fetchval(
                    sql,
                    email_data["message_id"],
                    email_data.get("user_id"),
                    email_data.get("template_id"),
                    json.dumps(email_data["to_addresses"]),
                    email_data["subject"],
                    email_data.get("html_content"),
                    email_data.get("text_content"),
                    json.dumps(email_data.get("attachments", [])),
                    email_data.get("priority", "normal"),
                    email_data.get("status", "pending"),
                    json.dumps(email_data.get("metadata", {}))
                )
            
            return str(record_id)
            
        except Exception as e:
            logger.error(f"Email record creation failed: {str(e)}")
            return None
    
    async def update_email_status(self, message_id: str, status: str, **kwargs):
        """Update email delivery status"""
        
        try:
            updates = {"status": status}
            
            if status == "sent":
                updates["sent_at"] = datetime.now()
            elif status == "delivered":
                updates["delivered_at"] = datetime.now()
            elif status == "opened":
                updates["opened_at"] = datetime.now()
            elif status == "clicked":
                updates["clicked_at"] = datetime.now()
            
            if "error_message" in kwargs:
                updates["error_message"] = kwargs["error_message"]
            
            # Build UPDATE query
            set_clauses = [f"{field} = ${i+1}" for i, field in enumerate(updates.keys())]
            values = list(updates.values()) + [message_id]
            
            sql = f"""
            UPDATE email_messages 
            SET {', '.join(set_clauses)}
            WHERE message_id = ${len(values)}
            """
            
            async with self.pool.acquire() as conn:
                await conn.execute(sql, *values)
                
        except Exception as e:
            logger.error(f"Email status update failed: {str(e)}")
    
    # ========== STATISTICS & ANALYTICS ==========
    
    async def get_user_statistics(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive user statistics"""
        
        try:
            stats = {}
            
            async with self.pool.acquire() as conn:
                # Website stats
                stats["websites"] = await conn.fetchval(
                    "SELECT COUNT(*) FROM websites WHERE user_id = $1 AND is_active = TRUE", 
                    user_id
                )
                
                # Scan stats
                scan_stats = await conn.fetchrow("""
                    SELECT COUNT(*) as total_scans,
                           AVG(overall_score) as avg_score,
                           SUM(total_issues) as total_issues
                    FROM compliance_scans WHERE user_id = $1
                """, user_id)
                
                stats.update(dict(scan_stats) if scan_stats else {})
                
                # Alert stats
                stats["open_alerts"] = await conn.fetchval("""
                    SELECT COUNT(*) FROM monitoring_alerts 
                    WHERE user_id = $1 AND is_resolved = FALSE
                """, user_id)
                
                # Email stats
                stats["emails_sent"] = await conn.fetchval("""
                    SELECT COUNT(*) FROM email_messages 
                    WHERE user_id = $1 AND status IN ('sent', 'delivered')
                """, user_id)
            
            return stats
            
        except Exception as e:
            logger.error(f"Statistics lookup failed: {str(e)}")
            return {}
    
    async def record_analytics_event(self, event_data: Dict[str, Any]) -> bool:
        """Record analytics event"""
        
        try:
            sql = """
            INSERT INTO analytics_events (user_id, session_id, event_type, event_name,
                                        event_data, page_url, referrer, user_agent,
                                        ip_hash, country, city, metadata)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            """
            
            async with self.pool.acquire() as conn:
                await conn.execute(
                    sql,
                    event_data.get("user_id"),
                    event_data.get("session_id"),
                    event_data["event_type"],
                    event_data["event_name"],
                    json.dumps(event_data.get("event_data", {})),
                    event_data.get("page_url"),
                    event_data.get("referrer"),
                    event_data.get("user_agent"),
                    event_data.get("ip_hash"),
                    event_data.get("country"),
                    event_data.get("city"),
                    json.dumps(event_data.get("metadata", {}))
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Analytics event failed: {str(e)}")
            return False
    
    # ========== DATABASE HEALTH ==========
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform database health check"""
        
        try:
            start_time = datetime.now()
            
            async with self.pool.acquire() as conn:
                # Test basic connectivity
                result = await conn.fetchval("SELECT 1")
                
                # Get connection pool stats
                pool_stats = {
                    "size": self.pool.get_size(),
                    "max_size": self.pool.get_max_size(),
                    "min_size": self.pool.get_min_size()
                }
                
                # Get database stats
                db_stats = await conn.fetchrow("""
                    SELECT 
                        (SELECT COUNT(*) FROM users) as total_users,
                        (SELECT COUNT(*) FROM websites) as total_websites,
                        (SELECT COUNT(*) FROM compliance_scans) as total_scans,
                        (SELECT COUNT(*) FROM monitoring_alerts WHERE is_resolved = FALSE) as open_alerts
                """)
            
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return {
                "status": "healthy",
                "connected": self.is_connected,
                "response_time_ms": round(response_time, 2),
                "schema_version": self.schema_version,
                "pool_stats": pool_stats,
                "database_stats": dict(db_stats) if db_stats else {},
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "connected": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

# Global database instance
db_manager = DatabaseManager()

# Initialize database on module import
async def init_database():
    """Initialize database connection"""
    success = await db_manager.connect()
    if success:
        logger.info("🗄️ Database initialization completed")
    else:
        logger.error("❌ Database initialization failed")
    return success