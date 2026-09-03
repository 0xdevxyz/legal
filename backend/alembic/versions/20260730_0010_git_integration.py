"""Git-Integration: die drei Tabellen des GitHub-PR-Kanals anlegen.

Revision ID: 0010_git_integration
Revises: 0009_fix_review_columns

Hintergrund: `git_routes.py` + `git_service/` (OAuth, Repo verbinden,
Branch+Patches+PR, PR-Tracking) waren fertig implementiert, aber ohne Tabellen —
der Router war deshalb seit 29.07. stillgelegt. Entscheidung des Betreibers
(29.07.): Der PR-Weg ist der strategische Auslieferungskanal — die KI schreibt
nie selbst in die Kundenseite, der Kunde merged den PR.

Spalten sind aus den realen Queries abgeleitet (_save_git_credentials,
_save_connected_repo, _get_connected_repo, _save_pr_record).

`access_token`/`refresh_token` werden von der Anwendung **Fernet-verschlüsselt**
abgelegt (git_token_crypto.py, Schlüssel GIT_TOKEN_ENC_KEY) — die Spalten sind
bewusst TEXT, nie Klartext-Tokens.

Rein additiv (`CREATE TABLE IF NOT EXISTS`).
"""
from typing import Sequence, Union

from alembic import op

revision: str = '0010_git_integration'
down_revision: Union[str, None] = '0009_fix_review_columns'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS git_credentials (
            id            SERIAL PRIMARY KEY,
            user_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            provider      VARCHAR(20) NOT NULL CHECK (provider IN ('github','gitlab')),
            access_token  TEXT NOT NULL,   -- Fernet-verschluesselt
            refresh_token TEXT,            -- Fernet-verschluesselt
            git_username  VARCHAR(255),
            created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at    TIMESTAMPTZ,
            CONSTRAINT uq_git_credentials UNIQUE (user_id, provider)
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS git_connected_repos (
            id             SERIAL PRIMARY KEY,
            user_id        INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            provider       VARCHAR(20) NOT NULL CHECK (provider IN ('github','gitlab')),
            owner          VARCHAR(255) NOT NULL,
            repo           VARCHAR(255) NOT NULL,
            default_branch VARCHAR(255) NOT NULL DEFAULT 'main',
            active         BOOLEAN NOT NULL DEFAULT TRUE,
            created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at     TIMESTAMPTZ,
            CONSTRAINT uq_git_connected_repos UNIQUE (user_id, provider, owner, repo)
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS git_pull_requests (
            id          SERIAL PRIMARY KEY,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            repo_id     INTEGER NOT NULL REFERENCES git_connected_repos(id) ON DELETE CASCADE,
            pr_number   INTEGER,
            pr_url      TEXT,
            branch_name VARCHAR(255),
            feature_ids TEXT[],
            scan_id     VARCHAR(128),
            status      VARCHAR(20) NOT NULL DEFAULT 'OPEN'
                        CHECK (status IN ('OPEN','MERGED','CLOSED','DRAFT')),
            created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at  TIMESTAMPTZ
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_git_prs_user ON git_pull_requests (user_id, created_at DESC)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS git_pull_requests")
    op.execute("DROP TABLE IF EXISTS git_connected_repos")
    op.execute("DROP TABLE IF EXISTS git_credentials")
