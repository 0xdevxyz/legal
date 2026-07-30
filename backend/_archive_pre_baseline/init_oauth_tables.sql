-- OAuth Providers Tabelle für Google & Apple Sign-In

CREATE TABLE IF NOT EXISTS oauth_providers (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL,  -- 'google' oder 'apple'
    provider_user_id VARCHAR(255) NOT NULL,  -- Google ID oder Apple User ID
    provider_email VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Ein User kann nur einmal mit einem Provider verknüpft sein
    UNIQUE(provider, provider_user_id)
);

-- OAuth State Tokens für CSRF-Protection
CREATE TABLE IF NOT EXISTS oauth_states (
    id SERIAL PRIMARY KEY,
    state_token VARCHAR(255) UNIQUE NOT NULL,
    provider VARCHAR(50) NOT NULL,
    redirect_url VARCHAR(512),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL
);

-- Indexes
CREATE INDEX idx_oauth_providers_user ON oauth_providers(user_id);
CREATE INDEX idx_oauth_providers_provider ON oauth_providers(provider, provider_user_id);
CREATE INDEX idx_oauth_states_token ON oauth_states(state_token);

-- Auto-delete expired OAuth states (Cleanup)
CREATE OR REPLACE FUNCTION cleanup_expired_oauth_states()
RETURNS TRIGGER AS $$
BEGIN
    DELETE FROM oauth_states WHERE expires_at < CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_cleanup_oauth_states
    BEFORE INSERT ON oauth_states
    EXECUTE FUNCTION cleanup_expired_oauth_states();

-- Kommentare
COMMENT ON TABLE oauth_providers IS 'Verknüpfungen zwischen Usern und OAuth Providern (Google, Apple)';
COMMENT ON TABLE oauth_states IS 'Temporäre State-Tokens für OAuth2 CSRF-Protection';
COMMENT ON COLUMN oauth_providers.provider_user_id IS 'Unique ID from OAuth provider (Google: sub, Apple: sub)';

