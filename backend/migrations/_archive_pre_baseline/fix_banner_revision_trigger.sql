-- Fix: increment_banner_revision() referenzierte OLD.config / NEW.config,
-- aber cookie_banner_configs hat keine Spalte "config" (Tabelle wurde auf
-- Einzelspalten umgebaut). Dadurch schlug JEDES UPDATE mit
--   record "old" has no field "config"
-- fehl — u.a. der Cookie-Scan, der services + scan_completed_at speichert.
-- Das verursachte die Endlosschleife in der Cookie-Ersteinrichtung.
--
-- Neue Logik: Revision + Snapshot bei jeder inhaltlichen Änderung, wobei
-- volatile/tracking-Felder ignoriert werden (revision, updated_at, created_at,
-- scan_completed_at, last_scan_url).

CREATE OR REPLACE FUNCTION increment_banner_revision()
RETURNS trigger
LANGUAGE plpgsql
AS $function$
DECLARE
    old_content jsonb;
    new_content jsonb;
BEGIN
    old_content := to_jsonb(OLD)
        - 'revision' - 'updated_at' - 'created_at'
        - 'scan_completed_at' - 'last_scan_url';
    new_content := to_jsonb(NEW)
        - 'revision' - 'updated_at' - 'created_at'
        - 'scan_completed_at' - 'last_scan_url';

    IF old_content IS DISTINCT FROM new_content THEN
        NEW.revision := COALESCE(OLD.revision, 0) + 1;
        NEW.updated_at := NOW();

        INSERT INTO cookie_banner_revisions (site_id, revision, config_snapshot, services_snapshot, changed_by)
        VALUES (NEW.site_id, NEW.revision, row_to_json(NEW)::jsonb, NEW.services, NEW.user_id);
    END IF;

    RETURN NEW;
END;
$function$;
