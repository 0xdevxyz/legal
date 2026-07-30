-- ============================================================================
-- Complyo Risk Matrix: Abmahnrisiko-Berechnung
-- Basiert auf: DSGVO, TMG, TTDSG, BFSG, UWG, UrhG
-- ============================================================================

-- Haupttabelle: Compliance Risk Matrix
CREATE TABLE IF NOT EXISTS compliance_risk_matrix (
    id SERIAL PRIMARY KEY,
    issue_category VARCHAR(100) NOT NULL UNIQUE,
    severity VARCHAR(50) NOT NULL,
    market VARCHAR(10) DEFAULT 'DE',
    risk_min_eur NUMERIC(10,2) NOT NULL,
    risk_max_eur NUMERIC(10,2) NOT NULL,
    bussgeld_max_eur NUMERIC(10,2),
    legal_basis TEXT NOT NULL,
    description TEXT,
    effective_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Vollständige Risk-Matrix mit allen Abmahnkategorien
INSERT INTO compliance_risk_matrix (issue_category, severity, market, risk_min_eur, risk_max_eur, bussgeld_max_eur, legal_basis, description, effective_date) VALUES

-- ============================================================================
-- SÄULE 1: RECHTSTEXTE (TMG)
-- ============================================================================
('impressum', 'critical', 'DE', 1500, 5000, NULL, '§5 TMG', 'Fehlendes oder unvollständiges Impressum', '2007-03-01'),
('agb', 'critical', 'DE', 1000, 4000, NULL, 'BGB §§305ff', 'Fehlerhafte oder fehlende Allgemeine Geschäftsbedingungen', '2002-01-01'),
('widerrufsbelehrung', 'critical', 'DE', 1500, 5000, NULL, 'BGB §355', 'Fehlende oder fehlerhafte Widerrufsbelehrung', '2014-06-13'),
('contact', 'warning', 'DE', 300, 1000, NULL, '§5 TMG Abs. 1', 'Fehlende oder schwer auffindbare Kontaktinformationen', '2007-03-01'),

-- ============================================================================
-- SÄULE 2: DSGVO (Datenschutz)
-- ============================================================================
('datenschutz', 'critical', 'DE', 2500, 8000, 50000, 'DSGVO Art. 13-14, 83', 'Fehlende oder unzureichende Datenschutzerklärung', '2018-05-25'),
('tracking', 'critical', 'DE', 2000, 8000, 50000, 'DSGVO Art. 6, 7, 83', 'Tracking ohne Einwilligung (Analytics, Profiling)', '2018-05-25'),
('datenverarbeitung', 'warning', 'DE', 1500, 5000, 50000, 'DSGVO Art. 13-14, 83', 'Unklare Darlegung der Datenverarbeitung', '2018-05-25'),

-- ============================================================================
-- SÄULE 3: COOKIE COMPLIANCE (TTDSG)
-- ============================================================================
('cookies', 'critical', 'DE', 1000, 3000, 50000, 'TTDSG §25, DSGVO Art. 83', 'Fehlender oder fehlerhafter Cookie-Consent-Banner', '2021-12-01'),

-- ============================================================================
-- SÄULE 4: BARRIEREFREIHEIT (BFSG)
-- ============================================================================
('barrierefreiheit', 'critical', 'DE', 2000, 10000, 100000, 'BFSG §12-15', 'Fehlende Barrierefreiheit (Tastaturbedienung, Kontraste, Screenreader)', '2025-06-29'),
('kontraste', 'warning', 'DE', 500, 2000, 100000, 'BFSG §12', 'Unzureichende Farbkontraste für Screenreader', '2025-06-29'),
('tastaturbedienung', 'warning', 'DE', 500, 2000, 100000, 'BFSG §12', 'Fehlende Tastaturbedienbarkeit', '2025-06-29'),

-- ============================================================================
-- WEITERE COMPLIANCE-KATEGORIEN
-- ============================================================================

-- Wettbewerbsrecht / Irreführende Werbung
('irrefuehrende_werbung', 'critical', 'DE', 2000, 8000, NULL, 'UWG §5', 'Irreführende Werbeaussagen oder Produktdarstellung', '2004-07-08'),
('pruefsiegel', 'warning', 'DE', 1000, 4000, NULL, 'UWG §5', 'Unzulässige Verwendung von Prüfsiegeln ohne Nachweis', '2004-07-08'),
('schleichwerbung', 'warning', 'DE', 1500, 5000, NULL, 'UWG §5a, TMG §6', 'Fehlende Kennzeichnung von Werbung/Sponsored Content', '2004-07-08'),

-- Preisangaben (E-Commerce)
('preisangaben', 'critical', 'DE', 1000, 4000, NULL, 'PAngV §1-7', 'Fehlerhafte Preisangaben (Grundpreis, Endpreis, Rabatte)', '2022-05-28'),
('grundpreis', 'warning', 'DE', 800, 3000, NULL, 'PAngV §2', 'Fehlende oder fehlerhafte Grundpreisangaben', '2022-05-28'),

-- Urheber- und Markenrechte
('urheberrecht', 'critical', 'DE', 600, 5000, NULL, 'UrhG §97', 'Verwendung fremder Bilder/Texte ohne Lizenz', '1965-09-09'),
('markenrecht', 'critical', 'DE', 1000, 8000, NULL, 'MarkenG §14', 'Verletzung fremder Markenrechte', '1995-01-01'),

-- Produktkennzeichnung & Verpackung
('produktkennzeichnung', 'warning', 'DE', 500, 3000, 100000, 'ProdSG, EnVKG', 'Fehlende CE-Kennzeichnung, Energieeffizienz-Labels', '2021-11-26'),
('verpackungsgesetz', 'warning', 'DE', 1000, 10000, 200000, 'VerpackG §34', 'Fehlende Registrierung im Verpackungsregister', '2019-01-01'),

-- Verbraucherrechte
('kuendigungsbutton', 'critical', 'DE', 1500, 5000, NULL, 'BGB §312k', 'Fehlender Kündigungsbutton für langfristige Verträge', '2022-07-01'),
('rueckgabe', 'warning', 'DE', 1000, 4000, NULL, 'BGB §346ff', 'Fehlerhafte Rückgabebedingungen (z.B. nur Gutschein statt Rückzahlung)', '2002-01-01'),

-- Grenzüberschreitender Handel (EU)
('eu_verbraucherrechte', 'warning', 'DE', 1500, 5000, NULL, 'EU-Verbraucherrechterichtlinie', 'Fehlerhafte Umsetzung EU-Verbraucherrechte', '2014-06-13')

ON CONFLICT (issue_category) DO UPDATE SET
    severity = EXCLUDED.severity,
    risk_min_eur = EXCLUDED.risk_min_eur,
    risk_max_eur = EXCLUDED.risk_max_eur,
    bussgeld_max_eur = EXCLUDED.bussgeld_max_eur,
    legal_basis = EXCLUDED.legal_basis,
    description = EXCLUDED.description,
    updated_at = CURRENT_TIMESTAMP;

-- Indizes für schnelle Abfragen
CREATE INDEX IF NOT EXISTS idx_risk_matrix_category ON compliance_risk_matrix(issue_category);
CREATE INDEX IF NOT EXISTS idx_risk_matrix_severity ON compliance_risk_matrix(severity);
CREATE INDEX IF NOT EXISTS idx_risk_matrix_market ON compliance_risk_matrix(market);

-- Trigger für updated_at
CREATE OR REPLACE FUNCTION update_risk_matrix_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_risk_matrix_updated_at ON compliance_risk_matrix;
CREATE TRIGGER trigger_risk_matrix_updated_at
    BEFORE UPDATE ON compliance_risk_matrix
    FOR EACH ROW
    EXECUTE FUNCTION update_risk_matrix_timestamp();

-- View für die 4 Hauptsäulen
CREATE OR REPLACE VIEW complyo_main_pillars AS
SELECT 
    CASE 
        WHEN issue_category IN ('barrierefreiheit', 'kontraste', 'tastaturbedienung') THEN 'Barrierefreiheit'
        WHEN issue_category IN ('cookies') THEN 'Cookie Compliance'
        WHEN issue_category IN ('impressum', 'agb', 'widerrufsbelehrung', 'contact') THEN 'Rechtstexte'
        WHEN issue_category IN ('datenschutz', 'tracking', 'datenverarbeitung') THEN 'DSGVO'
        ELSE 'Weitere'
    END as pillar,
    issue_category,
    severity,
    risk_min_eur,
    risk_max_eur,
    bussgeld_max_eur,
    legal_basis,
    description
FROM compliance_risk_matrix
ORDER BY 
    CASE 
        WHEN issue_category IN ('barrierefreiheit', 'kontraste', 'tastaturbedienung') THEN 1
        WHEN issue_category IN ('cookies') THEN 2
        WHEN issue_category IN ('impressum', 'agb', 'widerrufsbelehrung', 'contact') THEN 3
        WHEN issue_category IN ('datenschutz', 'tracking', 'datenverarbeitung') THEN 4
        ELSE 5
    END,
    severity DESC;

