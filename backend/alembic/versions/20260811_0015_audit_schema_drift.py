"""audit_schema_drift: Spalten nachziehen, die der Code erwartet, die DB aber nie bekam

Schema-Drift-Audit 2026-08-11: Mehrere Routen lesen/schreiben Spalten, die in
keiner Migration angelegt wurden (historisch teils per Hand-SQL geplant, nie
eingespielt). Betroffene Endpunkte scheitern heute still (Best-Effort-Wrapper)
oder mit 500. Diese Revision ist REIN ADDITIV: jede Spalte via
ADD COLUMN IF NOT EXISTS, Typen und Defaults aus den Verwendungsstellen im
Code abgeleitet (Referenzen als Kommentar je Spalte, Stand Working Tree
2026-08-11).

Zwei Sonderfaelle:
- scan_history.website_id: integer in der DB, aber der Code bindet
  tracked_websites.id (uuid) -> jeder INSERT mit website_id scheitert, die
  Spalte ist in allen Zeilen NULL (lesend verifiziert am 2026-08-11:
  27 Zeilen, 0 mit website_id IS NOT NULL). Typwechsel auf uuid via
  USING NULL::uuid, abgesichert durch einen Guard, der bei vorhandenen
  Werten abbricht statt sie zu verwerfen.
- cookie_consent_logs.expires_at: Default von now() + '3 years' auf
  now() + '24 months' vereinheitlicht (Retention-Linie 24 Monate, vgl.
  leads.data_retention_days = 730). ALTER COLUMN SET DEFAULT ist
  metadata-only, Bestandszeilen bleiben unveraendert.

HINWEIS Ausfuehrung: Die DB steht auf 0011, die Tabellen aus 0012/0013 wurden
manuell eingespielt -> vor dem Upgrade `alembic stamp 0013_wirkungsscan`,
dann `alembic upgrade head` (macht 0014 + diese Revision).

Revision ID: 0015_audit_schema_drift
Revises: 0014_gdpr_deletion_requests
Create Date: 2026-08-11
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0015_audit_schema_drift"
down_revision: Union[str, None] = "0014_gdpr_deletion_requests"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 1) cookie_banner_configs — Feature-Spalten, die die Cookie-Routen
    #    bereits lesen/schreiben, die aber nie migriert wurden.
    # ------------------------------------------------------------------
    op.execute(
        """
        ALTER TABLE cookie_banner_configs
            -- widget_routes.py:422 (SELECT ... language FROM cookie_banner_configs);
            -- Modell-Default 'de', max_length=10 (cookie_compliance_routes.py:256);
            -- Typ analog cookie_consent_logs.language VARCHAR(10).
            ADD COLUMN IF NOT EXISTS language VARCHAR(10) DEFAULT 'de',

            -- cookie_compliance_routes.py:618-619 (SET requires_reconsent = false),
            -- 1104-1107 (CASE ... THEN true ELSE requires_reconsent END),
            -- 3487 (row['requires_reconsent'] or False) -> boolean, Default false.
            ADD COLUMN IF NOT EXISTS requires_reconsent BOOLEAN DEFAULT false,

            -- cookie_compliance_routes.py:487ff compute_config_hash (sha256-Hex,
            -- 64 Zeichen), geschrieben in 1104-1124. In der Produktions-DB
            -- bereits vorhanden (VARCHAR(64), Hand-SQL) -> hier nur fuer
            -- frisch migrierte DBs; auf Prod ein No-Op.
            ADD COLUMN IF NOT EXISTS config_hash VARCHAR(64),

            -- cookie_compliance_routes.py:3518 (SELECT bannerless_mode),
            -- 3526 (row['bannerless_mode'] if row else False) -> boolean, Default false.
            ADD COLUMN IF NOT EXISTS bannerless_mode BOOLEAN DEFAULT false,

            -- cookie_compliance_routes.py:2633-2634 (SELECT), 2657 (or False),
            -- 2689 (UPDATE ... COALESCE($2, tcf_enabled)) -> boolean, Default false.
            ADD COLUMN IF NOT EXISTS tcf_enabled BOOLEAN DEFAULT false,

            -- cookie_compliance_routes.py:2650-2652 (json.loads bei str),
            -- 2700 (json.dumps(...) als Bind) -> JSONB, Default leere Liste.
            ADD COLUMN IF NOT EXISTS tcf_vendors JSONB DEFAULT '[]'::jsonb,

            -- cookie_compliance_routes.py:2477 (SELECT), 2507 (or False),
            -- 2539 (UPDATE ... COALESCE) -> boolean, Default false.
            ADD COLUMN IF NOT EXISTS age_verification_enabled BOOLEAN DEFAULT false,

            -- cookie_compliance_routes.py:2478 (SELECT), 2508 (or 16),
            -- 2540 (UPDATE ... COALESCE) -> integer, Default 16 (Code-Fallback).
            ADD COLUMN IF NOT EXISTS age_verification_min_age INTEGER DEFAULT 16,

            -- cookie_compliance_routes.py:2800 (SELECT), 2828 (or False),
            -- 2861 (UPDATE ... COALESCE) -> boolean, Default false.
            ADD COLUMN IF NOT EXISTS geo_restriction_enabled BOOLEAN DEFAULT false,

            -- cookie_compliance_routes.py:2801/2829/2862; Bind ist
            -- data.get('countries') als Python-Liste ohne json.dumps ->
            -- asyncpg bindet Listen als Postgres-Array, also TEXT[] (kein JSONB).
            ADD COLUMN IF NOT EXISTS geo_countries TEXT[] DEFAULT '{}'::text[],

            -- cookie_compliance_routes.py:2897 (SELECT), 2917 (or False),
            -- 2949 (UPDATE ... COALESCE) -> boolean, Default false.
            ADD COLUMN IF NOT EXISTS forwarding_enabled BOOLEAN DEFAULT false,

            -- cookie_compliance_routes.py:2898/2918/2950; Bind ist
            -- data.get('target_sites') als Python-Liste -> TEXT[] wie geo_countries.
            ADD COLUMN IF NOT EXISTS forwarding_target_sites TEXT[] DEFAULT '{}'::text[]
        """
    )

    # ------------------------------------------------------------------
    # 2) cookie_custom_services — Katalog filtert auf is_active, das
    #    Update setzt updated_at; beide Spalten fehlen (Tabelle aus 0003).
    # ------------------------------------------------------------------
    op.execute(
        """
        ALTER TABLE cookie_custom_services
            -- cookie_compliance_routes.py:1378 (WHERE ... AND is_active = true),
            -- 1494 (SELECT ... is_active) -> boolean, Default true
            -- (Bestandszeilen sollen sichtbar bleiben).
            ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT true,

            -- cookie_compliance_routes.py:1494 (SELECT ... updated_at),
            -- 1581 (UPDATE ... updated_at=now()) -> timestamptz, Default now().
            ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT now()
        """
    )

    # ------------------------------------------------------------------
    # 3) leads — DSGVO-Loeschvormerkung (Art. 17), vom Retention-Cleanup
    #    vorausgesetzt.
    # ------------------------------------------------------------------
    op.execute(
        """
        ALTER TABLE leads
            -- database_service.py:343 (WHERE ... AND deletion_requested = FALSE),
            -- 358 (SET deletion_requested = TRUE) -> boolean, Default false.
            ADD COLUMN IF NOT EXISTS deletion_requested BOOLEAN DEFAULT false,

            -- database_service.py:359 (deletion_requested_at = $1, datetime) ->
            -- timestamptz, NULL solange kein Antrag vorliegt.
            ADD COLUMN IF NOT EXISTS deletion_requested_at TIMESTAMPTZ
        """
    )

    # ------------------------------------------------------------------
    # 4) legal_updates — Auto-Archivierung prueft heute per
    #    information_schema, ob 'archived' existiert, und tut sonst nichts.
    # ------------------------------------------------------------------
    op.execute(
        """
        ALTER TABLE legal_updates
            -- ai_legal_routes.py:136 (WHERE archived = FALSE),
            -- 148 (SET archived = TRUE) -> boolean, Default false.
            ADD COLUMN IF NOT EXISTS archived BOOLEAN DEFAULT false,

            -- ai_legal_routes.py:148 (archived_at = NOW()) -> timestamptz,
            -- NULL solange nicht archiviert.
            ADD COLUMN IF NOT EXISTS archived_at TIMESTAMPTZ
        """
    )

    # ------------------------------------------------------------------
    # 5) scan_history — legal_update_id + Typreparatur website_id.
    # ------------------------------------------------------------------
    # public_routes.py:524/565 (INSERT ... legal_update_id, Bind ist
    # Optional[int], public_routes.py:63); legal_updates.id ist integer
    # (serial, per \d legal_updates verifiziert). Vorlage:
    # migrations/_archive_pre_baseline/add_legal_update_id_to_scan_history.sql
    op.execute(
        """
        ALTER TABLE scan_history
            ADD COLUMN IF NOT EXISTS legal_update_id INTEGER
                REFERENCES legal_updates(id) ON DELETE SET NULL
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_scan_history_legal_update
            ON scan_history (legal_update_id) WHERE legal_update_id IS NOT NULL
        """
    )
    op.execute(
        """
        COMMENT ON COLUMN scan_history.legal_update_id IS
            'Optional: ID der Gesetzesänderung, die diesen Scan ausgelöst hat'
        """
    )

    # website_id: DB-Typ integer, aber der Code bindet tracked_websites.id
    # (uuid) — public_routes.py:485-529 (fetchval RETURNING id bzw.
    # website['id'] -> INSERT $3). Dadurch schlug jeder INSERT mit
    # website_id fehl; lesend verifiziert 2026-08-11: alle 27 Zeilen NULL.
    # Guard: bricht ab, falls doch Werte vorhanden sind (USING NULL::uuid
    # wuerde sie sonst stillschweigend verwerfen). Idempotent: wechselt nur,
    # wenn der Typ noch integer ist.
    op.execute(
        """
        DO $$
        BEGIN
            IF (
                SELECT atttypid
                FROM pg_attribute
                WHERE attrelid = 'scan_history'::regclass
                  AND attname = 'website_id'
            ) = 'integer'::regtype THEN
                IF EXISTS (SELECT 1 FROM scan_history WHERE website_id IS NOT NULL) THEN
                    RAISE EXCEPTION
                        'scan_history.website_id enthaelt Werte — Typwechsel integer->uuid abgebrochen (Audit-Annahme "alle NULL" verletzt, bitte manuell migrieren)';
                END IF;
                ALTER TABLE scan_history
                    ALTER COLUMN website_id TYPE uuid USING NULL::uuid;
            END IF;
        END $$;
        """
    )

    # ------------------------------------------------------------------
    # 6) cookie_consent_logs — Retention-Vereinheitlichung auf 24 Monate
    #    (bisheriger Default: now() + '3 years'). Nur Default, keine Daten.
    # ------------------------------------------------------------------
    op.execute(
        """
        ALTER TABLE cookie_consent_logs
            ALTER COLUMN expires_at SET DEFAULT (now() + interval '24 months')
        """
    )


def downgrade() -> None:
    # Default zurueck auf den alten Stand (3 Jahre).
    op.execute(
        """
        ALTER TABLE cookie_consent_logs
            ALTER COLUMN expires_at SET DEFAULT (now() + interval '3 years')
        """
    )

    # website_id zurueck auf integer — gleicher Guard wie im Upgrade:
    # nur wenn keine Werte vorhanden sind (uuid-Werte liessen sich nicht
    # verlustfrei nach integer ueberfuehren).
    op.execute(
        """
        DO $$
        BEGIN
            IF (
                SELECT atttypid
                FROM pg_attribute
                WHERE attrelid = 'scan_history'::regclass
                  AND attname = 'website_id'
            ) = 'uuid'::regtype THEN
                IF EXISTS (SELECT 1 FROM scan_history WHERE website_id IS NOT NULL) THEN
                    RAISE EXCEPTION
                        'scan_history.website_id enthaelt uuid-Werte — Downgrade auf integer abgebrochen';
                END IF;
                ALTER TABLE scan_history
                    ALTER COLUMN website_id TYPE integer USING NULL::integer;
            END IF;
        END $$;
        """
    )

    op.execute("DROP INDEX IF EXISTS idx_scan_history_legal_update")
    op.execute("ALTER TABLE scan_history DROP COLUMN IF EXISTS legal_update_id")

    op.execute(
        """
        ALTER TABLE legal_updates
            DROP COLUMN IF EXISTS archived_at,
            DROP COLUMN IF EXISTS archived
        """
    )

    op.execute(
        """
        ALTER TABLE leads
            DROP COLUMN IF EXISTS deletion_requested_at,
            DROP COLUMN IF EXISTS deletion_requested
        """
    )

    op.execute(
        """
        ALTER TABLE cookie_custom_services
            DROP COLUMN IF EXISTS updated_at,
            DROP COLUMN IF EXISTS is_active
        """
    )

    # config_hash wird BEWUSST NICHT entfernt: Die Spalte existierte in der
    # Produktions-DB schon VOR dieser Revision (Hand-SQL, Drift) und traegt
    # dort Live-Daten (Reconsent-Hashes). Ein Drop im Downgrade wuerde
    # Bestandsdaten zerstoeren, die diese Revision nicht angelegt hat.
    op.execute(
        """
        ALTER TABLE cookie_banner_configs
            DROP COLUMN IF EXISTS forwarding_target_sites,
            DROP COLUMN IF EXISTS forwarding_enabled,
            DROP COLUMN IF EXISTS geo_countries,
            DROP COLUMN IF EXISTS geo_restriction_enabled,
            DROP COLUMN IF EXISTS age_verification_min_age,
            DROP COLUMN IF EXISTS age_verification_enabled,
            DROP COLUMN IF EXISTS tcf_vendors,
            DROP COLUMN IF EXISTS tcf_enabled,
            DROP COLUMN IF EXISTS bannerless_mode,
            DROP COLUMN IF EXISTS requires_reconsent,
            DROP COLUMN IF EXISTS language
        """
    )
