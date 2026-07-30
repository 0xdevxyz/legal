-- Rescan-Flagging für tracked_websites
-- =====================================
-- Der Legal-Change-Monitor markiert betroffene Websites nach einer erkannten
-- Gesetzesänderung zum erneuten Scan (compliance_engine/legal_update_integration.py
-- -> _flag_websites_for_rescan). Die dafür nötigen Spalten fehlten bisher, wodurch
-- das Flagging mit "column rescan_required does not exist" fehlschlug.
--
-- Idempotent via ADD COLUMN IF NOT EXISTS — läuft bei jedem Startup gefahrlos.

ALTER TABLE tracked_websites
    ADD COLUMN IF NOT EXISTS rescan_required     BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE tracked_websites
    ADD COLUMN IF NOT EXISTS rescan_reason       TEXT;

-- Verweist auf legal_updates(id) (INTEGER). Bewusst ohne harten FK, damit das
-- Löschen eines Legal-Updates das Flag nicht blockiert; SET NULL via App-Logik.
ALTER TABLE tracked_websites
    ADD COLUMN IF NOT EXISTS rescan_triggered_by INTEGER;

ALTER TABLE tracked_websites
    ADD COLUMN IF NOT EXISTS rescan_flagged_at   TIMESTAMP;

CREATE INDEX IF NOT EXISTS idx_tracked_websites_rescan
    ON tracked_websites(rescan_required) WHERE rescan_required = TRUE;

COMMENT ON COLUMN tracked_websites.rescan_required IS
    'Vom Legal-Change-Monitor gesetzt: Website soll wegen einer Gesetzesänderung neu gescannt werden.';
