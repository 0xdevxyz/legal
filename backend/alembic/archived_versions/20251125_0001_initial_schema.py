"""Initial schema - Import existing database structure

Revision ID: 0001
Revises: 
Create Date: 2025-11-25

This migration represents the existing database schema.
It is used as a baseline for future migrations.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Create initial database schema.
    
    Note: This migration assumes uuid-ossp extension is already installed.
    If not, run: CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    """
    
    # Create ENUM types
    op.execute("CREATE TYPE IF NOT EXISTS subscription_tier AS ENUM ('free', 'pro', 'enterprise')")
    op.execute("CREATE TYPE IF NOT EXISTS subscription_status AS ENUM ('active', 'cancelled', 'expired', 'trial')")
    op.execute("CREATE TYPE IF NOT EXISTS scan_frequency AS ENUM ('daily', 'weekly', 'monthly', 'manual')")
    op.execute("CREATE TYPE IF NOT EXISTS website_status AS ENUM ('active', 'paused', 'error')")
    op.execute("CREATE TYPE IF NOT EXISTS scan_type AS ENUM ('manual', 'scheduled', 'api')")
    op.execute("CREATE TYPE IF NOT EXISTS team_role AS ENUM ('owner', 'admin', 'member', 'viewer')")
    
    # Users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), primary_key=True),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255)),
        sa.Column('company_name', sa.String(255)),
        sa.Column('phone_number', sa.String(50)),
        sa.Column('subscription_tier', sa.Enum('free', 'pro', 'enterprise', name='subscription_tier'), server_default='free'),
        sa.Column('subscription_status', sa.Enum('active', 'cancelled', 'expired', 'trial', name='subscription_status'), server_default='trial'),
        sa.Column('subscription_end_date', sa.DateTime(timezone=True)),
        sa.Column('trial_end_date', sa.DateTime(timezone=True)),
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('is_verified', sa.Boolean, server_default='false'),
        sa.Column('is_superuser', sa.Boolean, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('last_login', sa.DateTime(timezone=True)),
        sa.Column('monthly_scans_limit', sa.Integer, server_default='10'),
        sa.Column('monthly_scans_used', sa.Integer, server_default='0'),
        sa.Column('total_scans', sa.Integer, server_default='0'),
        sa.Column('api_key', sa.String(255), unique=True),
        sa.Column('failed_login_attempts', sa.Integer, server_default='0'),
        sa.Column('account_locked_until', sa.DateTime(timezone=True)),
        sa.Column('two_factor_enabled', sa.Boolean, server_default='false'),
        sa.Column('two_factor_secret', sa.String(255)),
    )
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_api_key', 'users', ['api_key'])
    
    # User Sessions table
    op.create_table(
        'user_sessions',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('refresh_token', sa.String(500), unique=True, nullable=False),
        sa.Column('expires_at', sa.DateTime, nullable=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('NOW()')),
        sa.Column('is_revoked', sa.Boolean, server_default='false'),
    )
    op.create_index('idx_user_sessions_user_id', 'user_sessions', ['user_id'])
    op.create_index('idx_user_sessions_token', 'user_sessions', ['refresh_token'])
    op.create_index('idx_user_sessions_expires_at', 'user_sessions', ['expires_at'])
    
    # Websites table
    op.create_table(
        'websites',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('url', sa.String(500), nullable=False),
        sa.Column('name', sa.String(255)),
        sa.Column('scan_frequency', sa.Enum('daily', 'weekly', 'monthly', 'manual', name='scan_frequency'), server_default='weekly'),
        sa.Column('auto_fix_enabled', sa.Boolean, server_default='false'),
        sa.Column('notification_enabled', sa.Boolean, server_default='true'),
        sa.Column('last_scan_date', sa.DateTime(timezone=True)),
        sa.Column('last_score', sa.Float),
        sa.Column('status', sa.Enum('active', 'paused', 'error', name='website_status'), server_default='active'),
        sa.Column('favicon_url', sa.String(500)),
        sa.Column('screenshot_url', sa.String(500)),
        sa.Column('technology_stack', postgresql.JSONB),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('idx_websites_user_id', 'websites', ['user_id'])
    op.create_index('idx_websites_url', 'websites', ['url'])
    
    # Scan History table
    op.create_table(
        'scan_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('scan_id', sa.String(255)),
        sa.Column('user_id', postgresql.UUID(as_uuid=True)),
        sa.Column('website_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('url', sa.String(500)),
        sa.Column('scan_date', sa.DateTime, server_default=sa.text('NOW()')),
        sa.Column('overall_score', sa.Float),
        sa.Column('compliance_score', sa.Float),
        sa.Column('legal_score', sa.Float),
        sa.Column('cookie_score', sa.Float),
        sa.Column('accessibility_score', sa.Float),
        sa.Column('privacy_score', sa.Float),
        sa.Column('issues_count', sa.Integer, server_default='0'),
        sa.Column('critical_issues', sa.Integer, server_default='0'),
        sa.Column('warnings_count', sa.Integer, server_default='0'),
        sa.Column('results', postgresql.JSONB),
        sa.Column('scan_data', postgresql.JSONB),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('NOW()')),
    )
    op.create_index('idx_scan_history_user_id', 'scan_history', ['user_id'])
    op.create_index('idx_scan_history_website_id', 'scan_history', ['website_id'])
    op.create_index('idx_scan_history_scan_date', 'scan_history', ['scan_date'])
    op.create_index('idx_scan_history_scan_id', 'scan_history', ['scan_id'])
    
    # Fix Jobs table
    op.create_table(
        'fix_jobs',
        sa.Column('job_id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('scan_id', sa.String(255)),
        sa.Column('issue_id', sa.String(255)),
        sa.Column('issue_category', sa.String(100)),
        sa.Column('issue_data', postgresql.JSONB),
        sa.Column('status', sa.String(50), server_default='pending'),
        sa.Column('priority', sa.Integer, server_default='0'),
        sa.Column('progress_percent', sa.Integer, server_default='0'),
        sa.Column('current_step', sa.Text),
        sa.Column('result', sa.Text),
        sa.Column('generated_content', sa.Text),
        sa.Column('implementation_guide', sa.Text),
        sa.Column('error_message', sa.Text),
        sa.Column('estimated_duration_seconds', sa.Integer, server_default='60'),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('NOW()')),
        sa.Column('started_at', sa.DateTime),
        sa.Column('completed_at', sa.DateTime),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('NOW()')),
    )
    op.create_index('idx_fix_jobs_user_id', 'fix_jobs', ['user_id'])
    op.create_index('idx_fix_jobs_status', 'fix_jobs', ['status'])
    op.create_index('idx_fix_jobs_created_at', 'fix_jobs', ['created_at'])
    op.create_index('idx_fix_jobs_priority', 'fix_jobs', ['priority'], postgresql_ops={'priority': 'DESC'})
    
    # Teams table
    op.create_table(
        'teams',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('owner_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    
    # Team Members table
    op.create_table(
        'team_members',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), primary_key=True),
        sa.Column('team_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('teams.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', sa.Enum('owner', 'admin', 'member', 'viewer', name='team_role'), server_default='member'),
        sa.Column('joined_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.UniqueConstraint('team_id', 'user_id'),
    )
    op.create_index('idx_team_members_user_id', 'team_members', ['user_id'])
    op.create_index('idx_team_members_team_id', 'team_members', ['team_id'])
    
    # Legal News table
    op.create_table(
        'legal_news',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('summary', sa.Text),
        sa.Column('content', sa.Text),
        sa.Column('url', sa.String(500)),
        sa.Column('source', sa.String(255)),
        sa.Column('source_url', sa.String(500)),
        sa.Column('published_date', sa.DateTime),
        sa.Column('fetched_date', sa.DateTime, server_default=sa.text('NOW()')),
        sa.Column('category', sa.String(100)),
        sa.Column('news_type', sa.String(50), server_default='general'),
        sa.Column('impact_level', sa.String(50)),
        sa.Column('affected_sectors', postgresql.ARRAY(sa.Text)),
        sa.Column('tags', postgresql.ARRAY(sa.Text)),
        sa.Column('is_featured', sa.Boolean, server_default='false'),
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('NOW()')),
    )
    op.create_index('idx_legal_news_published_date', 'legal_news', ['published_date'])
    op.create_index('idx_legal_news_category', 'legal_news', ['category'])
    
    # Create update_updated_at function and triggers
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)
    
    op.execute("""
        CREATE TRIGGER update_users_updated_at 
        BEFORE UPDATE ON users
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)
    
    op.execute("""
        CREATE TRIGGER update_websites_updated_at 
        BEFORE UPDATE ON websites
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)


def downgrade() -> None:
    """Drop all tables and types."""
    # Drop triggers first
    op.execute("DROP TRIGGER IF EXISTS update_websites_updated_at ON websites")
    op.execute("DROP TRIGGER IF EXISTS update_users_updated_at ON users")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column()")
    
    # Drop tables in reverse order (respecting foreign keys)
    op.drop_table('legal_news')
    op.drop_table('team_members')
    op.drop_table('teams')
    op.drop_table('fix_jobs')
    op.drop_table('scan_history')
    op.drop_table('websites')
    op.drop_table('user_sessions')
    op.drop_table('users')
    
    # Drop ENUM types
    op.execute("DROP TYPE IF EXISTS team_role")
    op.execute("DROP TYPE IF EXISTS scan_type")
    op.execute("DROP TYPE IF EXISTS website_status")
    op.execute("DROP TYPE IF EXISTS scan_frequency")
    op.execute("DROP TYPE IF EXISTS subscription_status")
    op.execute("DROP TYPE IF EXISTS subscription_tier")


