-- ============================================================================
-- User Company Data für Dokument-Generierung
-- Speichert Firmendaten für Impressum & Datenschutzerklärung
-- ============================================================================

CREATE TABLE IF NOT EXISTS user_company_data (
    user_id INTEGER PRIMARY KEY,
    company_name VARCHAR(255),
    legal_form VARCHAR(100),
    street VARCHAR(255),
    zip_city VARCHAR(100),
    phone VARCHAR(50),
    email VARCHAR(255),
    vat_id VARCHAR(50),
    represented_by VARCHAR(255),
    handelsregister VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user_limits(user_id)
);

-- Trigger für updated_at
DROP TRIGGER IF EXISTS trigger_company_data_updated_at ON user_company_data;
CREATE TRIGGER trigger_company_data_updated_at
    BEFORE UPDATE ON user_company_data
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();

-- Demo-Daten für User 1
INSERT INTO user_company_data (
    user_id, 
    company_name, 
    legal_form, 
    street, 
    zip_city, 
    phone, 
    email, 
    vat_id, 
    represented_by
) VALUES (
    1,
    'Complyo Demo GmbH',
    'GmbH',
    'Musterstraße 123',
    '10115 Berlin',
    '+49 30 123456',
    'info@complyo-demo.de',
    'DE123456789',
    'Max Mustermann'
)
ON CONFLICT (user_id) DO UPDATE SET
    company_name = EXCLUDED.company_name,
    legal_form = EXCLUDED.legal_form,
    street = EXCLUDED.street,
    zip_city = EXCLUDED.zip_city,
    phone = EXCLUDED.phone,
    email = EXCLUDED.email,
    vat_id = EXCLUDED.vat_id,
    represented_by = EXCLUDED.represented_by,
    updated_at = CURRENT_TIMESTAMP;

