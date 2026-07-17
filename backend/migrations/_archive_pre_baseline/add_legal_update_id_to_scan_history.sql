ALTER TABLE scan_history
ADD COLUMN IF NOT EXISTS legal_update_id INTEGER REFERENCES legal_updates(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_scan_history_legal_update
ON scan_history(legal_update_id) WHERE legal_update_id IS NOT NULL;

COMMENT ON COLUMN scan_history.legal_update_id IS
'Optional: ID der Gesetzesänderung, die diesen Scan ausgelöst hat';
