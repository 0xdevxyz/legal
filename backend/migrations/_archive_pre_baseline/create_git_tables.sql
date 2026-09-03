-- Migration: Create Git Integration Tables
-- Speichert Git-Credentials, verbundene Repos und PR-History
-- Datum: 2025-02-03

-- Tabelle für Git-Credentials (OAuth Tokens)
CREATE TABLE IF NOT EXISTS git_credentials (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    provider VARCHAR(20) NOT NULL, -- github, gitlab, bitbucket
    access_token TEXT NOT NULL,
    refresh_token TEXT,
    git_username VARCHAR(100),
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    
    -- Unique: Ein User kann pro Provider nur eine Verbindung haben
    CONSTRAINT unique_user_provider UNIQUE (user_id, provider)
);

-- Tabelle für verbundene Repositories
CREATE TABLE IF NOT EXISTS git_connected_repos (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    provider VARCHAR(20) NOT NULL,
    owner VARCHAR(100) NOT NULL,
    repo VARCHAR(100) NOT NULL,
    default_branch VARCHAR(50) DEFAULT 'main',
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    
    -- Unique: Ein Repo kann pro User nur einmal verbunden sein
    CONSTRAINT unique_user_repo UNIQUE (user_id, provider, owner, repo)
);

-- Tabelle für Pull Request History
CREATE TABLE IF NOT EXISTS git_pull_requests (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    repo_id INTEGER REFERENCES git_connected_repos(id),
    pr_number INTEGER,
    pr_url TEXT,
    branch_name VARCHAR(200),
    feature_ids TEXT[], -- Array von Feature-IDs
    scan_id VARCHAR(100),
    status VARCHAR(20) DEFAULT 'OPEN', -- OPEN, MERGED, CLOSED
    created_at TIMESTAMPTZ DEFAULT NOW(),
    merged_at TIMESTAMPTZ,
    closed_at TIMESTAMPTZ
);

-- Indizes für schnelle Lookups
CREATE INDEX IF NOT EXISTS idx_git_creds_user ON git_credentials(user_id);
CREATE INDEX IF NOT EXISTS idx_git_repos_user ON git_connected_repos(user_id);
CREATE INDEX IF NOT EXISTS idx_git_repos_active ON git_connected_repos(user_id, active);
CREATE INDEX IF NOT EXISTS idx_git_prs_user ON git_pull_requests(user_id);
CREATE INDEX IF NOT EXISTS idx_git_prs_repo ON git_pull_requests(repo_id);

-- Kommentare
COMMENT ON TABLE git_credentials IS 'OAuth-Tokens für Git-Provider (GitHub, GitLab)';
COMMENT ON TABLE git_connected_repos IS 'Mit Complyo verbundene Git-Repositories';
COMMENT ON TABLE git_pull_requests IS 'Historie der automatisch erstellten PRs';
