-- Declarative Compliance Checks
-- ================================
-- Kern des "Gesetz -> automatische Prüfung"-Mechanismus.
--
-- Bisher waren Website-Prüfungen hartcodierte Python-Funktionen
-- (compliance_engine/checks/*.py). Eine neue Pflicht erforderte handgeschriebenen
-- Code. Diese Tabelle beschreibt Prüfungen DEKLARATIV als Daten; der generische
-- Runner (compliance_engine/declarative_check_runner.py) interpretiert sie beim Scan.
--
-- Der Legal-Change-Monitor kann so aus einer erkannten Gesetzesänderung per LLM
-- automatisch eine neue Prüfung erzeugen (check_generator.py), ohne Code-Deploy.

CREATE TABLE IF NOT EXISTS compliance_checks (
    id              SERIAL PRIMARY KEY,
    slug            TEXT NOT NULL UNIQUE,
    category        TEXT NOT NULL,              -- mappt auf Säule via ScoreCalculator (shop->legal, ...)
    title           TEXT NOT NULL,
    description     TEXT NOT NULL,
    recommendation  TEXT NOT NULL,
    legal_basis     TEXT NOT NULL,
    severity        TEXT NOT NULL DEFAULT 'warning'
                        CHECK (severity IN ('critical', 'warning', 'info')),
    risk_euro       INTEGER NOT NULL DEFAULT 1000,

    -- Gate: wann ist die Prüfung relevant? (JSON, AND über die Keys)
    --   {"site_type": "shop"}            -> nutzt detect_shop()
    --   {"keywords_any": ["abo","abonnement"]}
    --   {"keywords_all": [...]}
    --   {"always": true}
    applies_when    JSONB NOT NULL DEFAULT '{"always": true}'::jsonb,

    -- Detektion des Pflicht-Elements (JSON). type = "required_element":
    --   link_href_keywords []  -> Substrings in <a href>
    --   link_text_keywords []  -> Substrings in Linktext/aria-label/title
    --   url_paths []           -> Kandidatenpfade, die per HTTP 200 existieren müssen
    --   html_patterns []       -> Regex über das gesamte HTML (z.B. Inline-Button)
    --   content_requirements {} -> {label: regex} auf der Zielseite; fehlend -> "unvollständig"
    detection       JSONB NOT NULL,

    effective_date  DATE NOT NULL DEFAULT CURRENT_DATE,

    -- Lifecycle: pending_review (von KI erzeugt, wartet auf Admin-GO) | active | disabled
    status          TEXT NOT NULL DEFAULT 'pending_review'
                        CHECK (status IN ('pending_review', 'active', 'disabled')),
    auto_generated  BOOLEAN NOT NULL DEFAULT FALSE,
    source_legal_update_id INTEGER REFERENCES legal_updates(id) ON DELETE SET NULL,
    generation_notes TEXT,            -- LLM-Begründung / Provenienz
    version         INTEGER NOT NULL DEFAULT 1,

    reviewed_by     TEXT,
    reviewed_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_compliance_checks_status
    ON compliance_checks(status);
CREATE INDEX IF NOT EXISTS idx_compliance_checks_active
    ON compliance_checks(status, effective_date) WHERE status = 'active';
CREATE INDEX IF NOT EXISTS idx_compliance_checks_source
    ON compliance_checks(source_legal_update_id);

COMMENT ON TABLE compliance_checks IS
    'Deklarative, datengetriebene Compliance-Prüfungen. Vom Legal-Change-Monitor automatisch befüllbar.';

-- ---------------------------------------------------------------------------
-- Seed: Widerrufsbutton (§ 356a BGB ab 19.06.2026, RL (EU) 2023/2673)
-- ---------------------------------------------------------------------------
-- Handverifiziert -> direkt 'active'. Erste reale Prüfung im neuen Mechanismus.
-- Bewusst NUR Button-/Funktions-Indikatoren ("widerrufen"-Verb), KEINE
-- Belehrungs-Keywords -> kein Overlap mit dem bestehenden Widerrufsbelehrung-Check.
INSERT INTO compliance_checks
    (slug, category, title, description, recommendation, legal_basis,
     severity, risk_euro, applies_when, detection, effective_date,
     status, auto_generated, generation_notes)
VALUES (
    'widerrufsbutton',
    'shop',
    'Widerrufsbutton fehlt (wird Pflicht ab 19.06.2026)',
    'Ab dem 19.06.2026 müssen Online-Shops Verbrauchern eine leicht zugängliche, '
    'hervorgehoben platzierte elektronische Widerrufsfunktion ("Widerrufsbutton") '
    'bereitstellen — analog zum Kündigungsbutton. Ein erkannter Shop besitzt aktuell '
    'keinen solchen Button. Dies ist NICHT die Widerrufsbelehrung (Textseite), sondern '
    'eine interaktive Funktion zum direkten Widerruf in wenigen Klicks.',
    'Fügen Sie einen deutlich sichtbaren "Vertrag widerrufen"-Button ein, der ohne '
    'Login zu einem Widerrufsformular führt (Eingabe der Bestelldaten + Bestätigung). '
    'Platzierung: gut auffindbar, optisch abgehoben, max. wenige Klicks vom Vertrag entfernt.',
    '§ 356a BGB (ab 19.06.2026), Richtlinie (EU) 2023/2673 zur Änderung der RL 2011/83/EU',
    'warning',
    2500,
    '{"site_type": "shop"}'::jsonb,
    '{
        "type": "required_element",
        "link_text_keywords": ["vertrag widerrufen", "verträge widerrufen", "widerrufsbutton", "jetzt widerrufen", "hier widerrufen", "widerruf starten"],
        "link_href_keywords": ["widerrufsformular", "widerruf-button", "widerrufsbutton", "vertrag-widerrufen", "widerrufsfunktion", "withdraw-contract"],
        "html_patterns": ["vertr(a|ä)ge?\\s+(hier\\s+)?widerrufen", "widerruf(s)?[- ]?(button|funktion)", "jetzt\\s+widerrufen"],
        "url_paths": ["/widerrufsformular", "/widerruf-button", "/vertrag-widerrufen", "/widerruf/online"]
    }'::jsonb,
    '2026-06-19',
    'active',
    FALSE,
    'Seed: handverifiziert anhand IT-Recht-Kanzlei / Verbraucherzentrale (Frist 19.06.2026).'
)
ON CONFLICT (slug) DO NOTHING;

-- Risiko-Matrix-Eintrag für konsistente Risikodaten (eigene Kategorie, kein Overlap)
-- Idempotent via NOT EXISTS, da die Migration bei jedem Startup läuft.
INSERT INTO compliance_risk_matrix
    (issue_category, severity, market, risk_min_eur, risk_max_eur, bussgeld_max_eur,
     legal_basis, description, effective_date)
SELECT
    'widerrufsbutton', 'warning', 'DE', 1500, 3500, NULL,
    '§ 356a BGB (ab 19.06.2026), RL (EU) 2023/2673',
    'Fehlender elektronischer Widerrufsbutton im Online-Handel.',
    DATE '2026-06-19'
WHERE NOT EXISTS (
    SELECT 1 FROM compliance_risk_matrix
    WHERE issue_category = 'widerrufsbutton' AND market = 'DE'
);
