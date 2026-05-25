# Kill List

> Psychologische Entlastung. Was weg ist, bleibt weg.
> Letzte Aktualisierung: 2026-05-24

---

## 1. Entfernte Features & Dateien

| Was | Wann | Warum nie wieder |
|-----|------|-----------------|
| `backend/widgets/accessibility.js` | Phase A 2026-05-24 | v6 ist der Standard. v4 war Experiment ohne Regressions-Tests. |
| `backend/widgets/accessibility_smart.js` | Phase A 2026-05-24 | "Smart" war Marketing-Name für nie fertiggestellten A/B-Versuch. |
| `backend/widgets/accessibility-v5.js` | Phase A 2026-05-24 | Durch v6 vollständig ersetzt. Kein aktiver Nutzer hatte v5-embed. |
| `backend/widgets/cookie_consent.legacy.js` | Phase A 2026-05-24 | cookie_banner_v2.js ist aktiv. Legacy war toter Code seit >3 Monaten. |
| `backend/widgets/cookie_consent.legacy.js.bak` | Phase A 2026-05-24 | .bak-Dateien haben im Repo nichts verloren. Das ist wozu Git da ist. |
| `backend/init_erecht24_projects.sql` | Phase A 2026-05-24 | eRecht24 vollständig migriert (Removal 2026-05-23). Tabellen existieren nicht mehr. |
| `backend/migration_erecht24_fixed.sql` | Phase A 2026-05-24 | Migration bereits eingespielt. Keine Rollback-Strategie. |
| `backend/migration_erecht24_full.sql` | Phase A 2026-05-24 | Dito. |
| `backend/migrations/migration_deprecate_erecht24.sql` | Phase A 2026-05-24 | Bereits eingespielt. |
| `backend/migrations/migration_deprecate_erecht24_rollback.sql` | Phase A 2026-05-24 | Rollback wäre Production-Katastrophe. DB ist migriert. |
| `backend/scripts/export_erecht24_data.py` | Phase A 2026-05-24 | Export für beendete einmalige Migration. Kein Wiederverwendungsfall. |
| `backend/sql/init_alt_text_fixes.sql.disabled` | Phase A 2026-05-24 | .disabled = wurde nie aktiviert. Inhalt ist in aktiver Migration. |
| `backend/fix_generator.py` | Phase C 2026-05-24 | Ersetzt durch `unified_fix_engine.py`. 1045 LOC Legacy. |
| `backend/compliance_engine/enhanced_fixer.py` | Phase C 2026-05-24 | Nie in `main_production.py` registriert. Experimentelle Erweiterung ohne Tests. |
| `backend/enhanced_fix_routes.py` | Phase C 2026-05-24 | Kein `include_router`-Eintrag. Orphaned seit Erstellung. |
| `database_service.use_fallback` | Phase E 2026-05-24 | War immer `False`. Branches waren Dead Code mit falschen Dummy-Daten. |
| In-Memory OAuth-State (`oauth_states: Dict`) | Phase E 2026-05-24 | Verliert State bei Restart. Race-condition bei horizontalem Scaling. Jetzt Redis. |
| In-Memory Rate-Limit (`_rate_limit_windows`) | Phase E 2026-05-24 | Kein Schutz bei Multi-Process/Multi-Instance. Jetzt Redis ZADD. |
| In-Memory ZIP-Storage (function-level dict) | Phase E 2026-05-24 | Kein Schutz bei Restart. Jetzt Filesystem (tempfile). |

---

## 2. Verworfene Libraries

| Library | Entfernt | Grund |
|---------|---------|-------|
| `python-jose` | War nie installiert | `PyJWT` ist der Standard im Projekt. |

---

## 3. Verworfene Ideen / Experimente

| Idee | Grund für Verwerfen |
|------|-------------------|
| eRecht24 API-Integration | Provider eingestellt, keine zuverlässige API. Eigene Legal-Text-Generierung ist besser. |
| In-Memory DB-Fallback | Produziert stille Fehler (Nutzer sieht keine Daten, kein 503). Fail-Fast ist korrekt. |
| "Smart" Accessibility Widget | Zu komplex, kein messbarer Mehrwert ggü. v6. |
| `enhanced_fix_routes.py` (v2-Fixes) | Kein dedizierter Business-Case, keine Tests, nie aktiviert. |

---

## 4. Bewusst NICHT gebaut (und warum nicht)

| Was | Warum nicht |
|-----|-------------|
| Auto-Deploy von Fixes ohne PR | Zu risikoreich. User hat kein Rollback ohne Git. PR-basiert bleibt Pflicht. |
| Eigener LLM (Fine-Tuning) | EFRE-Pfad, aber erst nach Stabilität. OpenRouter ist ausreichend für Phase 1. |
| WebSocket für Real-Time Scan | Scan dauert 5–15s. Polling mit Status-Endpoint ist ausreichend und einfacher. |
| Multi-Tenancy (separate DBs pro Kunde) | Kein KMU-Customer hat dieses Requirement. Row-Level-Security in einer DB ist ausreichend. |
