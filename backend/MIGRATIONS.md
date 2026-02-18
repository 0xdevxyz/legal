# Datenbank-Migrations-Historie

Alle SQL-Dateien werden beim Backend-Start via `init_db()` automatisch ausgeführt (idempotent).

| Datei | Beschreibung |
|-------|-------------|
| `database_setup.sql` | Basis-Schema: users, websites, scan_results, compliance_fixes |
| `init_auth_tables.sql` | Auth: user_sessions, email_verifications |
| `init_user_limits.sql` | User-Limits: monthly_scans_limit, monthly_scans_used |
| `init_scan_history.sql` | Scan-Historie-Tabelle |
| `init_score_history.sql` | Compliance-Score-Verlauf |
| `init_legal_news_table.sql` | Legal News: RSS-Feed-Einträge |
| `init_legal_updates.sql` | Legal Updates für Websites |
| `init_ai_solution_cache.sql` | AI-Solution-Cache (70-85% API-Reduktion) |
| `init_cookie_compliance.sql` | Cookie Compliance: Configs, Logs, Stats |
| `init_erecht24_projects.sql` | eRecht24-Integration: Projekte, Texte |
| `init_risk_matrix.sql` | Compliance-Risiko-Matrix |
| `init_documents_table.sql` | Rechtsdokumente-Tabelle |
| `init_company_data.sql` | Unternehmensdaten für Nutzer |
| `init_website_structures.sql` | Website-Struktur-Analysen |
| `init_oauth_tables.sql` | OAuth2-Token-Tabellen |
| `add_lead_management.sql` | Lead-Management: Leads, Kommunikations-Log |
| `create_subscription_plans.sql` | Subscription-Pläne (Free, Basic, Pro, Enterprise) |
| `create_master_user.sql` | Initial-Admin-User |
| `database_optimization.sql` | Datenbank-Indizes und Performance-Optimierungen |
| `fix_domain_lock_logic.sql` | Domain-Lock-Logik-Fix |
| `migration_freemium_model.sql` | Freemium-Modell: Scan-Limits, Trial-Perioden |
| `migration_fix_jobs.sql` | Fix-Jobs-Queue für Hintergrundverarbeitung |
| `migration_ai_compliance.sql` | AI-Compliance: Scans, Systeme (EU AI Act) |
| `migration_ai_legal_classifier.sql` | AI Legal Classifier: Klassifikationen, Feedback |
| `migration_ai_notifications.sql` | AI-Benachrichtigungen für Legal Updates |
| `migration_domain_locks_v2.sql` | Domain-Locks V2 mit UUID-Support |
| `migration_erecht24_fixed.sql` | eRecht24-Fix: Spalten-Korrekturen |
| `migration_erecht24_full.sql` | eRecht24-Vollintegration: Webhooks, Cache |
| `migration_user_limits_uuid.sql` | User-Limits UUID-Migration |
| `update_complyo_plans.sql` | Subscription-Plan-Updates |
