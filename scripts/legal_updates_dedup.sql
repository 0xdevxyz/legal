-- ============================================================================
-- legal_updates_dedup.sql — Einmalige Bereinigung der legal_updates-Duplikate
-- ============================================================================
-- HINTERGRUND: Die Duplikat-Erkennung in legal_change_monitor._save_change_to_db
-- verglich title + published_at::date = heute. Dadurch wurde dieselbe Änderung
-- an jedem Folgetag erneut gespeichert (Stand 2026-08-11: 719 Zeilen,
-- 330 eindeutige Titel, 389 Duplikate; Spitzenreiter 83× identisch).
--
-- Der Code-Fix (Titel-Vergleich ohne Datumsfenster) verhindert NEUE Duplikate;
-- dieses Skript räumt die BESTEHENDEN auf.
--
-- AUSFÜHRUNG: NUR durch den Orchestrator, z.B.:
--   docker exec -i complyo-postgres psql -U complyo_user -d complyo_db \
--     -v ON_ERROR_STOP=1 < scripts/legal_updates_dedup.sql
--
-- IDEMPOTENT: Ein zweiter Lauf findet keine Duplikate mehr und ändert nichts.
-- Alles läuft in EINER Transaktion — bei Fehlern bleibt die DB unverändert.
--
-- ABHÄNGIGE TABELLEN (per \d legal_updates ermittelt, 2026-08-11):
--   compliance_checks.source_legal_update_id         (ON DELETE SET NULL)  -> umhängen
--   rule_changelog.triggered_by_legal_update_id      (ON DELETE SET NULL)  -> umhängen
--   pflichten_events.legal_update_id                 (ON DELETE CASCADE,
--       UNIQUE (legal_update_id, rule_id))           -> umhängen, Rest löschen
--   user_legal_notifications.legal_update_id         (ON DELETE CASCADE,
--       UNIQUE (user_id, legal_update_id, website_id)) -> umhängen, Rest löschen
--   ai_classifications: legal_updates.classification_id ist ein AUSGEHENDER FK;
--       Stand 2026-08-11 ist er in 0 Zeilen gesetzt -> nichts umzuhängen.
--       Kontroll-SELECT am Ende prüft das erneut.
-- ============================================================================

BEGIN;

-- ----------------------------------------------------------------------------
-- Schritt 0: Kontrollzahlen VORHER (nur Ausgabe, keine Änderung)
-- ----------------------------------------------------------------------------
SELECT 'VORHER' AS phase,
       (SELECT count(*) FROM legal_updates)                                AS legal_updates,
       (SELECT count(DISTINCT lower(trim(title))) FROM legal_updates)      AS eindeutige_titel,
       (SELECT count(*) FROM user_legal_notifications)                     AS notifications,
       (SELECT count(*) FROM pflichten_events)                             AS pflichten_events,
       (SELECT count(*) FROM rule_changelog)                               AS rule_changelog,
       (SELECT count(*) FROM compliance_checks)                            AS compliance_checks;

-- ----------------------------------------------------------------------------
-- Schritt (a): Sicherungskopie der Original-Tabelle.
-- CREATE TABLE IF NOT EXISTS: Beim ersten Lauf wird die Kopie angelegt; ein
-- zweiter Lauf überschreibt die Sicherung NICHT (Backup bleibt der Urzustand).
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS legal_updates_backup_20260811 AS
    SELECT * FROM legal_updates;

-- ----------------------------------------------------------------------------
-- Schritt (b1): Mapping Duplikat -> behaltene Zeile.
-- Behalten wird je normalisiertem Titel (lower(trim(title))) die Zeile mit
-- MIN(id) — also der ÄLTESTE Eintrag (der, der die ursprüngliche
-- Benachrichtigungswelle ausgelöst hat).
-- Temp-Tabelle fällt mit COMMIT automatisch weg (ON COMMIT DROP).
-- ----------------------------------------------------------------------------
CREATE TEMP TABLE tmp_lu_dedup ON COMMIT DROP AS
SELECT lu.id AS dup_id, k.keep_id
FROM legal_updates lu
JOIN (
    SELECT lower(trim(title)) AS norm_title, MIN(id) AS keep_id
    FROM legal_updates
    GROUP BY lower(trim(title))
) k ON lower(trim(lu.title)) = k.norm_title
WHERE lu.id <> k.keep_id;

SELECT 'MAPPING' AS phase, count(*) AS zu_loeschende_duplikate FROM tmp_lu_dedup;

-- ----------------------------------------------------------------------------
-- Schritt (b2): compliance_checks umhängen (FK wäre ON DELETE SET NULL —
-- ohne Umhängen ginge die Herkunft "aus welchem Update wurde dieser Check
-- generiert" verloren).
-- ----------------------------------------------------------------------------
UPDATE compliance_checks cc
SET source_legal_update_id = m.keep_id
FROM tmp_lu_dedup m
WHERE cc.source_legal_update_id = m.dup_id;

-- ----------------------------------------------------------------------------
-- Schritt (b3): rule_changelog umhängen (FK wäre ON DELETE SET NULL —
-- Umhängen erhält die Nachvollziehbarkeit, welches Update den Regel-Bump
-- ausgelöst hat).
-- ----------------------------------------------------------------------------
UPDATE rule_changelog rc
SET triggered_by_legal_update_id = m.keep_id
FROM tmp_lu_dedup m
WHERE rc.triggered_by_legal_update_id = m.dup_id;

-- ----------------------------------------------------------------------------
-- Schritt (b4): pflichten_events.
-- UNIQUE (legal_update_id, rule_id): Je (keep_id, rule_id), das beim Keeper
-- noch FEHLT, wird genau EIN Duplikat-Event umgehängt (DISTINCT ON verhindert,
-- dass zwei Duplikat-Events auf dasselbe Unique-Paar umgehängt werden).
-- Alle danach noch auf Duplikate zeigenden Events sind inhaltlich mehrfach
-- vorhanden und werden gelöscht (ON DELETE CASCADE hätte sie sonst beim
-- Löschen der Duplikate ohnehin mitgerissen).
-- ----------------------------------------------------------------------------
WITH kandidaten AS (
    SELECT DISTINCT ON (m.keep_id, pe.rule_id) pe.id, m.keep_id
    FROM pflichten_events pe
    JOIN tmp_lu_dedup m ON pe.legal_update_id = m.dup_id
    WHERE NOT EXISTS (
        SELECT 1 FROM pflichten_events pk
        WHERE pk.legal_update_id = m.keep_id
          AND pk.rule_id = pe.rule_id
    )
    ORDER BY m.keep_id, pe.rule_id, pe.id
)
UPDATE pflichten_events pe
SET legal_update_id = k.keep_id
FROM kandidaten k
WHERE pe.id = k.id;

DELETE FROM pflichten_events pe
USING tmp_lu_dedup m
WHERE pe.legal_update_id = m.dup_id;

-- ----------------------------------------------------------------------------
-- Schritt (b5): user_legal_notifications.
-- UNIQUE (user_id, legal_update_id, website_id): Gleiche Logik wie bei
-- pflichten_events — je (user_id, keep_id, website_id), das beim Keeper noch
-- fehlt, EINE Duplikat-Notification umhängen (die älteste, MIN(id));
-- die restlichen Duplikat-Notifications sind die eigentliche
-- Benachrichtigungs-Flut und werden gelöscht.
-- ----------------------------------------------------------------------------
WITH kandidaten AS (
    SELECT DISTINCT ON (n.user_id, m.keep_id, n.website_id) n.id, m.keep_id
    FROM user_legal_notifications n
    JOIN tmp_lu_dedup m ON n.legal_update_id = m.dup_id
    WHERE NOT EXISTS (
        SELECT 1 FROM user_legal_notifications nk
        WHERE nk.legal_update_id = m.keep_id
          AND nk.user_id IS NOT DISTINCT FROM n.user_id
          AND nk.website_id IS NOT DISTINCT FROM n.website_id
    )
    ORDER BY n.user_id, m.keep_id, n.website_id, n.id
)
UPDATE user_legal_notifications n
SET legal_update_id = k.keep_id
FROM kandidaten k
WHERE n.id = k.id;

DELETE FROM user_legal_notifications n
USING tmp_lu_dedup m
WHERE n.legal_update_id = m.dup_id;

-- ----------------------------------------------------------------------------
-- Schritt (b6): Duplikat-Zeilen in legal_updates löschen.
-- Alle Referenzen sind jetzt umgehängt bzw. bereinigt; die verbliebenen
-- CASCADE-/SET-NULL-Regeln greifen ins Leere.
-- ----------------------------------------------------------------------------
DELETE FROM legal_updates lu
USING tmp_lu_dedup m
WHERE lu.id = m.dup_id;

-- ----------------------------------------------------------------------------
-- Schritt (c): Kontrollzahlen NACHHER.
-- Erwartung: legal_updates = eindeutige_titel (keine Duplikate mehr);
-- verwaiste_klassifikationen dokumentiert nur den ai_classifications-Stand
-- (erwartet 0 Referenzen, siehe Kopf-Kommentar).
-- ----------------------------------------------------------------------------
SELECT 'NACHHER' AS phase,
       (SELECT count(*) FROM legal_updates)                                AS legal_updates,
       (SELECT count(DISTINCT lower(trim(title))) FROM legal_updates)      AS eindeutige_titel,
       (SELECT count(*) FROM user_legal_notifications)                     AS notifications,
       (SELECT count(*) FROM pflichten_events)                             AS pflichten_events,
       (SELECT count(*) FROM rule_changelog)                               AS rule_changelog,
       (SELECT count(*) FROM compliance_checks)                            AS compliance_checks,
       (SELECT count(*) FROM legal_updates WHERE classification_id IS NOT NULL) AS updates_mit_classification;

-- Verbliebene Duplikate (MUSS 0 Zeilen liefern):
SELECT 'RESTKONTROLLE' AS phase, lower(trim(title)) AS titel, count(*) AS anzahl
FROM legal_updates
GROUP BY lower(trim(title))
HAVING count(*) > 1;

COMMIT;
