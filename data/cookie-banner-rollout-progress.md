# Cookie-Banner Rollout – Status nach Phase 1+2 Implementierung (2026-05-15)

## ERLEDIGTE TASKS

### Phase 1 (alle abgeschlossen):
- 1.1: `cookie_consent.js` → `cookie_consent.legacy.js` mit DEPRECATED-Header
        `CookieBannerManagement.tsx` → Redirect zur /cookie-compliance Page
- 1.2: Storage-Key-Dokumentation in `COOKIE_BANNER_FINAL_STATUS.md` korrigiert
        (`complyo_cookie_consent_date` → korrekt: `complyo_consent_date`)
- 1.3: `applyServerConfig()` in `cookie_banner_v2.js` erweitert:
        snake_case → camelCase Mapping (accept_all→acceptAll, reject_all→continueWithout etc.)
- 1.4: `sanitizeText(str)` Funktion eingefügt (vor ComplyoCookieBanner class)
        Alle `innerHTML`-Einbindungen in `createBanner()`, `renderSettingsHTML()`,
        `renderServiceGroupsTab()`, `renderServicesTab()` mit `sanitizeText()` gesichert
- 1.5: Duplizierte DEFAULT_CONFIG-Einträge entfernt (consent_mode_enabled, consent_mode_default,
        gtm_enabled, geo_restriction_enabled, age_verification_enabled, bannerless_mode)

### Phase 2 (teilweise abgeschlossen):
- 2.1: `CookieBannerDesigner.tsx` vollständig neu geschrieben:
  - 4 Layout-Optionen (banner_bottom, banner_top, box_modal, floating_widget)
  - 22 Farbpresets
  - Zweisprachige Texteingabe (DE + EN)
  - Neue Felder: privacy_policy_url, cookie_policy_url, imprint_url,
                  cookie_lifetime_days, consent_mode_enabled Toggle, gtm_container_id
  - Live-Preview für alle 4 Layouts
- 2.2: Live-Preview alle 4 Layouts im Designer implementiert (box_modal, floating_widget,
        banner_top, banner_bottom)
- 2.5: Legal-Links konfigurierbar: privacyPolicyUrl, cookiePolicyUrl, imprintUrl in
        DEFAULT_CONFIG + applyServerConfig() + createBanner() + renderSettingsHTML()

## NOCH ZU ERLEDIGEN:
- 2.3: `cookie-compliance.tsx` Onboarding-Flow:
  - `useRouter` von `next/router` → `next/navigation` umstellen
  - loading-State bei API-Calls nutzen
  - Schritt-Validierung ergänzen (URL in Schritt 1, mind. 1 Service optional in Schritt 2)
  - PROBLEM: Datei nutzt Chakra-UI-Komponenten (Box, VStack, etc.) – muss auf Tailwind umgestellt werden
             ODER Chakra-Imports belassen wenn Chakra im Projekt vorhanden ist
  - CHECK: Ist Chakra-UI im dashboard-react package.json?

- 2.4: E2E-Tests in `dashboard-react/tests/e2e/cookie-compliance.spec.ts`

## WICHTIGE DATEIÄNDERUNGEN:
1. `/home/clawd/saas/legal/backend/widgets/cookie_banner_v2.js` – mehrfach editiert
2. `/home/clawd/saas/legal/backend/widgets/cookie_consent.legacy.js` – neu (war cookie_consent.js)
3. `/home/clawd/saas/legal/dashboard-react/src/components/dashboard/CookieBannerManagement.tsx` – komplett neu
4. `/home/clawd/saas/legal/dashboard-react/src/components/cookie-compliance/CookieBannerDesigner.tsx` – komplett neu
5. `/home/clawd/saas/legal/md/COOKIE_BANNER_FINAL_STATUS.md` – Storage-Key-Fix
