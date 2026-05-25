-- Migration: create_alt_text_review_queue.sql
-- AUDIT-15: Alt-Text Review Queue für KI-generierte Alt-Texte
-- Applied: 2026-05-01

CREATE TABLE IF NOT EXISTS alt_text_review_queue (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    site_id VARCHAR(255) NOT NULL,
    image_src TEXT NOT NULL,
    suggested_alt TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    approved_alt TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    reviewed_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_alt_text_queue_user ON alt_text_review_queue (user_id, status);
