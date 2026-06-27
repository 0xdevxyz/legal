-- Migration: backfill_user_data_in_generated_documents.sql
-- Zweck: Bestehende Dokumente haben kein metadata->'user_data', weil der
--        Generator dies früher nicht persistiert hat. Ohne user_data
--        überspringt legal_change_monitor / regenerate_affected_users diese
--        Dokumente beim Auto-Update ("Keine user_data — skip").
-- Lösung: user_data aus der Stammdaten-Tabelle user_company_data nachtragen.
-- Idempotent: setzt nur dort, wo user_data fehlt oder leer ist.
-- Quelle der Wahrheit für neue Dokumente ist legal_text_generator._save.

BEGIN;

UPDATE generated_documents gd
SET metadata = jsonb_set(
        COALESCE(gd.metadata, '{}'::jsonb),
        '{user_data}',
        jsonb_strip_nulls(jsonb_build_object(
            'company_name',        ucd.company_name,
            'legal_form',          ucd.legal_form,
            'address',             ucd.street,
            'zip_city',            ucd.zip_city,
            'phone',               ucd.phone,
            'email',               ucd.email,
            'vat_id',              ucd.vat_id,
            'represented_by',      ucd.represented_by,
            'registration_number', ucd.handelsregister
        )),
        true
    )
FROM user_company_data ucd
WHERE gd.user_id = ucd.user_id
  AND ucd.company_name IS NOT NULL
  AND (
        NOT (gd.metadata ? 'user_data')
        OR gd.metadata->'user_data' IS NULL
        OR gd.metadata->'user_data' = '{}'::jsonb
      );

-- Kontrolle: wie viele aktive Dokumente haben weiterhin KEIN user_data
-- (z.B. weil für den User keine Stammdaten hinterlegt sind)?
-- Diese werden beim nächsten manuellen Generieren automatisch befüllt.
--
--   SELECT user_id, document_type
--   FROM generated_documents
--   WHERE (metadata->>'is_active')::boolean IS NOT FALSE
--     AND (NOT (metadata ? 'user_data') OR metadata->'user_data' = '{}'::jsonb);

COMMIT;
