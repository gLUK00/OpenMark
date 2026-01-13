-- PostgreSQL initialization script for OpenMark
-- This script is executed when the PostgreSQL container is first started

-- Create auth_users table
CREATE TABLE IF NOT EXISTS auth_users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(64) NOT NULL,
    role VARCHAR(50) DEFAULT 'user',
    email VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    active BOOLEAN DEFAULT TRUE
);

-- Create revoked_tokens table for JWT blacklist
CREATE TABLE IF NOT EXISTS revoked_tokens (
    id SERIAL PRIMARY KEY,
    token_hash VARCHAR(64) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    revoked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create annotations table
CREATE TABLE IF NOT EXISTS annotations (
    id SERIAL PRIMARY KEY,
    document_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255),
    page_number INTEGER,
    annotation_type VARCHAR(50) NOT NULL,
    content TEXT,
    position_data JSONB,
    color VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create statistics table
CREATE TABLE IF NOT EXISTS statistics (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    documents_viewed INTEGER DEFAULT 0,
    notes_created INTEGER DEFAULT 0,
    highlights_created INTEGER DEFAULT 0,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create history table
CREATE TABLE IF NOT EXISTS history (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    document_id VARCHAR(255) NOT NULL,
    document_context TEXT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_auth_users_username ON auth_users(username);
CREATE INDEX IF NOT EXISTS idx_auth_users_email ON auth_users(email);
CREATE INDEX IF NOT EXISTS idx_revoked_tokens_token_hash ON revoked_tokens(token_hash);
CREATE INDEX IF NOT EXISTS idx_revoked_tokens_expires ON revoked_tokens(expires_at);
CREATE INDEX IF NOT EXISTS idx_annotations_document ON annotations(document_id);
CREATE INDEX IF NOT EXISTS idx_annotations_user ON annotations(user_id);
CREATE INDEX IF NOT EXISTS idx_statistics_user ON statistics(user_id);
CREATE INDEX IF NOT EXISTS idx_history_user ON history(user_id);
CREATE INDEX IF NOT EXISTS idx_history_document ON history(document_id);
CREATE INDEX IF NOT EXISTS idx_history_timestamp ON history(timestamp DESC);

-- Insert default users (password hashes are SHA-256)
-- admin123 -> 240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9
-- user123  -> e606e38b0d8c19b24cf0ee3808183162ea7cd63ff7912dbb22b5e803286b4446
INSERT INTO auth_users (username, password_hash, role, email) VALUES
    ('admin', '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9', 'admin', 'admin@openmark.local'),
    ('user', 'e606e38b0d8c19b24cf0ee3808183162ea7cd63ff7912dbb22b5e803286b4446', 'user', 'user@openmark.local')
ON CONFLICT (username) DO NOTHING;

-- Function to cleanup expired revoked tokens
CREATE OR REPLACE FUNCTION cleanup_expired_tokens()
RETURNS void AS $$
BEGIN
    DELETE FROM revoked_tokens WHERE expires_at < CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;

-- Create a scheduled job for token cleanup (requires pg_cron extension in production)
-- For development, you can run manually: SELECT cleanup_expired_tokens();
