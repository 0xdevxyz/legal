"""A/B-Testing für das Cookie-Banner: die drei fehlenden Tabellen anlegen.

Revision ID: 0005_cookie_ab_testing
Revises: 0004_pflichten_events

Hintergrund: `ab_test_routes.py` ist seit Langem registriert und wird vom
ausgelieferten Banner (`widgets/cookie_banner_v2.js`) bei jedem Seitenaufruf
über `/api/ab-tests/assign/{site_id}/{visitor_id}` abgefragt. Die zugehörigen
Tabellen fehlten in der DB — der Endpunkt fiel auf `has_test: false` zurück und
protokollierte dabei rund 100 Fehler pro Tag ("relation does not exist").
Revision 0003 hat sie bewusst ausgelassen, weil eine Produktentscheidung ausstand.
Diese ist am 29.07.2026 gefallen: das Feature wird gebaut.

Spalten sind aus den realen Queries in `ab_test_routes.py` abgeleitet:
- Sample/Confidence/Traffic-Split aus `ABTestCreate`
- `ON CONFLICT (test_id, visitor_hash)` → UNIQUE auf cookie_ab_assignments
- `ON CONFLICT (test_id, variant, date)` → UNIQUE auf cookie_ab_results
- `DELETE FROM cookie_ab_tests` verlässt sich auf Cascade in beiden Kindtabellen

Rein additiv (`CREATE TABLE IF NOT EXISTS`) — kein Eingriff in Bestandstabellen.
"""
from typing import Sequence, Union

from alembic import op

revision: str = '0005_cookie_ab_testing'
down_revision: Union[str, None] = '0004_pflichten_events'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Tests ---------------------------------------------------------------
    op.execute("""
        CREATE TABLE IF NOT EXISTS cookie_ab_tests (
            id                SERIAL PRIMARY KEY,
            site_id           VARCHAR(255) NOT NULL,
            name              VARCHAR(255) NOT NULL,
            description       TEXT,
            hypothesis        TEXT,
            variant_a_config  JSONB NOT NULL DEFAULT '{}'::jsonb,
            variant_b_config  JSONB NOT NULL DEFAULT '{}'::jsonb,
            traffic_split     INTEGER NOT NULL DEFAULT 50
                              CHECK (traffic_split BETWEEN 0 AND 100),
            min_sample_size   INTEGER NOT NULL DEFAULT 1000
                              CHECK (min_sample_size >= 100),
            confidence_level  DOUBLE PRECISION NOT NULL DEFAULT 0.95
                              CHECK (confidence_level BETWEEN 0.8 AND 0.99),
            status            VARCHAR(20) NOT NULL DEFAULT 'draft'
                              CHECK (status IN ('draft','running','paused','completed')),
            winner            VARCHAR(1) CHECK (winner IN ('A','B')),
            start_date        TIMESTAMPTZ,
            end_date          TIMESTAMPTZ,
            created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_cookie_ab_tests_site ON cookie_ab_tests (site_id)")
    # Der Assignment-Endpunkt sucht je Seitenaufruf nach dem laufenden Test.
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_cookie_ab_tests_site_running
            ON cookie_ab_tests (site_id) WHERE status = 'running'
    """)
    # start_ab_test/create_ab_test erlauben nur einen laufenden Test je Seite.
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_cookie_ab_tests_one_running
            ON cookie_ab_tests (site_id) WHERE status = 'running'
    """)

    # --- Zuordnung Besucher → Variante --------------------------------------
    op.execute("""
        CREATE TABLE IF NOT EXISTS cookie_ab_assignments (
            id            BIGSERIAL PRIMARY KEY,
            test_id       INTEGER NOT NULL
                          REFERENCES cookie_ab_tests(id) ON DELETE CASCADE,
            visitor_hash  VARCHAR(64) NOT NULL,
            variant       VARCHAR(1) NOT NULL CHECK (variant IN ('A','B')),
            assigned_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_cookie_ab_assignments UNIQUE (test_id, visitor_hash)
        )
    """)

    # --- Tagesaggregate je Variante -----------------------------------------
    op.execute("""
        CREATE TABLE IF NOT EXISTS cookie_ab_results (
            id                    BIGSERIAL PRIMARY KEY,
            test_id               INTEGER NOT NULL
                                  REFERENCES cookie_ab_tests(id) ON DELETE CASCADE,
            variant               VARCHAR(1) NOT NULL CHECK (variant IN ('A','B')),
            date                  DATE NOT NULL,
            impressions           INTEGER NOT NULL DEFAULT 0,
            accepted_all          INTEGER NOT NULL DEFAULT 0,
            accepted_partial      INTEGER NOT NULL DEFAULT 0,
            rejected_all          INTEGER NOT NULL DEFAULT 0,
            accepted_analytics    INTEGER NOT NULL DEFAULT 0,
            accepted_marketing    INTEGER NOT NULL DEFAULT 0,
            accepted_functional   INTEGER NOT NULL DEFAULT 0,
            avg_decision_time_ms  INTEGER,
            created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_cookie_ab_results UNIQUE (test_id, variant, date)
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_cookie_ab_results_test ON cookie_ab_results (test_id)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS cookie_ab_results")
    op.execute("DROP TABLE IF EXISTS cookie_ab_assignments")
    op.execute("DROP TABLE IF EXISTS cookie_ab_tests")
