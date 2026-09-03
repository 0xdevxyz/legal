"""Fehlende Tabellen nachziehen, die beim Baseline-Cut (2026-07-17) verloren gingen.

Revision ID: 0003_missing_tables
Revises: 0002_company_profiles

Hintergrund: Der pg_dump-Baseline-Cut hat mehrere Tabellen nicht übernommen, die
aktiver Code weiterhin beschreibt/liest. Verifizierte Folgen vor dieser Revision:
- `POST /api/leads/collect` → 500 (`INSERT INTO leads`, Tabelle fehlt); zugleich
  fehlten `lead_consents`, `communication_log`, `email_verifications` aus demselben
  Lead-Flow (database_service.py).
- Fix-Audit/Backup: `audit_service.log_fix_application()` schrieb in
  `fix_application_audit` (fehlte), Rollback-Infos in `fix_backups` (fehlte).

Spalten sind aus den realen INSERT/SELECT-Aufrufen abgeleitet, nicht geraten.
Rein additiv (`CREATE TABLE IF NOT EXISTS`) — kein DROP/ALTER an Bestandstabellen,
weil die Live-DB Kundendaten enthält.

Nicht Teil dieser Revision (bewusst): `cookie_ab_tests`, `expert_service_requests`,
`git_*` — dort steht eine Produktentscheidung aus (Feature behalten oder Router
entfernen), siehe data/features/00_FEATURES_INDEX.md.
"""
from typing import Sequence, Union

from alembic import op

revision: str = '0003_missing_tables'
down_revision: Union[str, None] = '0002_company_profiles'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Lead-Flow (database_service.py) -----------------------------------
    # id ist ein UUID-String (str(uuid.uuid4())), daher VARCHAR, nicht uuid/serial.
    op.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id VARCHAR(64) PRIMARY KEY,
            email VARCHAR(320) NOT NULL,
            name VARCHAR(255),
            company VARCHAR(255),
            source VARCHAR(100) DEFAULT 'landing_page',
            url_analyzed TEXT,
            analysis_data JSONB,
            session_id VARCHAR(128),
            consent_given BOOLEAN DEFAULT FALSE,
            consent_timestamp TIMESTAMP WITH TIME ZONE,
            consent_ip_address VARCHAR(64),
            consent_user_agent TEXT,
            legal_basis VARCHAR(50) DEFAULT 'consent',
            verification_token VARCHAR(128),
            verification_sent_at TIMESTAMP WITH TIME ZONE,
            verification_expires_at TIMESTAMP WITH TIME ZONE,
            data_retention_until TIMESTAMP WITH TIME ZONE,
            status VARCHAR(30) DEFAULT 'new',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_leads_email ON leads (email)")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_leads_verification_token "
               "ON leads (verification_token) WHERE verification_token IS NOT NULL")
    op.execute("CREATE INDEX IF NOT EXISTS idx_leads_status ON leads (status)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_leads_retention ON leads (data_retention_until)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS lead_consents (
            id SERIAL PRIMARY KEY,
            lead_id VARCHAR(64) NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
            consent_type VARCHAR(50) NOT NULL,
            granted BOOLEAN NOT NULL DEFAULT FALSE,
            ip_address VARCHAR(64),
            user_agent TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_lead_consents_lead ON lead_consents (lead_id)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS communication_log (
            id SERIAL PRIMARY KEY,
            lead_id VARCHAR(64) NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
            type VARCHAR(50),
            subject VARCHAR(500),
            content TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_communication_log_lead ON communication_log (lead_id)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS email_verifications (
            id SERIAL PRIMARY KEY,
            lead_id VARCHAR(64) NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
            verification_token VARCHAR(128),
            status VARCHAR(30) DEFAULT 'pending',
            verified_at TIMESTAMP WITH TIME ZONE,
            ip_address VARCHAR(64),
            user_agent TEXT,
            expires_at TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_email_verifications_token "
               "ON email_verifications (verification_token)")

    # --- Fix-Audit / Backup (audit_service.py) -----------------------------
    # rollback_available wird vom Reader (fix-audit-log) gelesen; in dieser einen
    # Tabelle geführt, damit Writer (fix_application_audit) und Reader dieselbe
    # Quelle nutzen. Der frühere Reader las die nie geschriebene Geistertabelle
    # `fix_audit_trail` — der Code-Fix dazu zeigt jetzt hierher.
    op.execute("""
        CREATE TABLE IF NOT EXISTS fix_application_audit (
            id VARCHAR(64) PRIMARY KEY,
            user_id INTEGER,
            fix_id VARCHAR(128),
            fix_category VARCHAR(100),
            fix_type VARCHAR(100),
            action_type VARCHAR(50),
            deployment_method VARCHAR(50),
            applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            ip_address VARCHAR(64),
            user_agent TEXT,
            success BOOLEAN DEFAULT TRUE,
            user_confirmed BOOLEAN DEFAULT FALSE,
            backup_id VARCHAR(64),
            error_message TEXT,
            rollback_available BOOLEAN DEFAULT FALSE,
            metadata JSONB DEFAULT '{}'::jsonb
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_fix_audit_user ON fix_application_audit (user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_fix_audit_fix ON fix_application_audit (fix_id)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS fix_backups (
            backup_id VARCHAR(64) PRIMARY KEY,
            user_id INTEGER,
            audit_id VARCHAR(64),
            backup_location TEXT,
            deployment_method VARCHAR(50),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP WITH TIME ZONE,
            is_restored BOOLEAN DEFAULT FALSE,
            restored_at TIMESTAMP WITH TIME ZONE,
            metadata JSONB DEFAULT '{}'::jsonb
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_fix_backups_user ON fix_backups (user_id)")

    # --- Weitere beim Baseline-Cut verlorene Tabellen (vom Schema-Wächter gefunden) ---
    # Alle fünf werden von aktiven Endpunkten beschrieben/gelesen, existierten aber
    # weder in der Baseline noch live -> stille 500 bzw. leere Ergebnisse.

    # website_crawler.py: Cache der gecrawlten Seitenstruktur (ON CONFLICT website_id).
    op.execute("""
        CREATE TABLE IF NOT EXISTS website_structures (
            website_id VARCHAR(128) PRIMARY KEY,
            url TEXT,
            structure_data JSONB,
            cms_type VARCHAR(64),
            cms_version VARCHAR(64),
            cms_confidence DOUBLE PRECISION,
            has_legal_pages BOOLEAN,
            tracking_services JSONB,
            accessibility_score DOUBLE PRECISION,
            technology_stack JSONB,
            crawled_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            is_stale BOOLEAN DEFAULT FALSE
        )
    """)

    # widget_routes.py / public_routes.py: Widget-Analytics/Tracking.
    op.execute("""
        CREATE TABLE IF NOT EXISTS widget_events (
            id SERIAL PRIMARY KEY,
            site_id VARCHAR(128),
            widget_type VARCHAR(64),
            event_name VARCHAR(128),
            event_data JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_widget_events_site ON widget_events (site_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_widget_events_created ON widget_events (created_at)")

    # cookie_compliance_routes.py: kundenspezifische Dienste im Consent-Katalog
    # (domains/cookies werden per ::jsonb geschrieben).
    op.execute("""
        CREATE TABLE IF NOT EXISTS cookie_custom_services (
            id SERIAL PRIMARY KEY,
            site_id VARCHAR(128) NOT NULL,
            user_id INTEGER,
            service_key VARCHAR(128) NOT NULL,
            name VARCHAR(255),
            category VARCHAR(64),
            provider VARCHAR(255),
            description TEXT,
            domains JSONB,
            cookies JSONB,
            legal_basis VARCHAR(64),
            privacy_url TEXT,
            cookie_lifetime VARCHAR(64),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (site_id, service_key)
        )
    """)

    # user_routes.py: Firmendaten des Nutzers (ON CONFLICT user_id) — Quelle u.a.
    # für den user_data-Backfill des Rechtstext-Generators.
    op.execute("""
        CREATE TABLE IF NOT EXISTS user_company_data (
            user_id INTEGER PRIMARY KEY,
            company_name VARCHAR(255),
            tax_id VARCHAR(64),
            company_address TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # legal_notification_routes.py: Benachrichtigungseinstellungen.
    # notify_areas wird als rohe Python-Liste übergeben -> Postgres-Array TEXT[].
    op.execute("""
        CREATE TABLE IF NOT EXISTS user_legal_notification_settings (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL UNIQUE,
            email_enabled BOOLEAN DEFAULT TRUE,
            in_app_enabled BOOLEAN DEFAULT TRUE,
            push_enabled BOOLEAN DEFAULT FALSE,
            min_severity VARCHAR(20) DEFAULT 'medium',
            notify_areas TEXT[] DEFAULT ARRAY['dsgvo','ttdsg','cookie','impressum','barrierefreiheit','ai_act'],
            instant_for_critical BOOLEAN DEFAULT TRUE,
            digest_frequency VARCHAR(20) DEFAULT 'daily',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # widget_routes.py: zwischengespeichertes Ergebnis des Widget-Cookie-Scans
    # (ON CONFLICT site_id -> ein aktueller Stand je Site).
    op.execute("""
        CREATE TABLE IF NOT EXISTS cookie_scan_results (
            site_id VARCHAR(128) PRIMARY KEY,
            url TEXT,
            scanned_at TIMESTAMP WITH TIME ZONE,
            cookies JSONB,
            services JSONB,
            has_cmp BOOLEAN,
            cmp_name VARCHAR(128),
            config_hash VARCHAR(128),
            scan_duration_ms INTEGER,
            error TEXT
        )
    """)

    # fix_routes.py: Akzeptanz-/Ablehn-Metriken je Fix-Job (fetchrow + RETURNING,
    # also kein Best-Effort — fehlende Tabelle = 500).
    op.execute("""
        CREATE TABLE IF NOT EXISTS fix_acceptance_metrics (
            id SERIAL PRIMARY KEY,
            fix_job_id UUID,
            fix_type VARCHAR(100),
            handler_used VARCHAR(100),
            generated_at TIMESTAMP WITH TIME ZONE,
            presented_to_user_at TIMESTAMP WITH TIME ZONE,
            user_decision VARCHAR(50),
            decision_at TIMESTAMP WITH TIME ZONE,
            time_to_decision_seconds INTEGER,
            rejection_reason TEXT
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_fix_acceptance_job ON fix_acceptance_metrics (fix_job_id)")


def downgrade() -> None:
    # Reihenfolge wegen FK: abhängige Tabellen zuerst.
    for tbl in (
        "communication_log",
        "email_verifications",
        "lead_consents",
        "leads",
        "fix_backups",
        "fix_application_audit",
        "website_structures",
        "widget_events",
        "cookie_custom_services",
        "user_company_data",
        "user_legal_notification_settings",
        "cookie_scan_results",
        "fix_acceptance_metrics",
    ):
        op.execute(f"DROP TABLE IF EXISTS {tbl}")
