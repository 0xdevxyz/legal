/**
 * ============================================================================
 * Complyo Cookie Banner v2.0
 * ============================================================================
 * DSGVO-konformes Cookie-Consent-Management
 * 
 * Features:
 * - Granulares Consent-Management (Notwendig, Funktional, Statistik, Marketing)
 * - 3 Layouts: Banner (Bottom/Top), Box (Modal), Floating Widget
 * - Vollständig anpassbar (Farben, Texte, Position)
 * - Barrierefreiheit (WCAG 2.2 Level AA)
 * - Multi-Language Support
 * - Content Blocker Integration
 * - Responsive Design
 * 
 * © 2025 Complyo - All rights reserved
 * ============================================================================
 */

(function() {
    'use strict';
    
    // ========================================================================
    // Configuration & Constants
    // ========================================================================
    
    const VERSION = '2.0.0';
    const API_BASE = 'https://api.complyo.tech';
    const CONSENT_STORAGE_KEY = 'complyo_cookie_consent';
    const CONSENT_DATE_KEY = 'complyo_consent_date';
    const VISITOR_ID_KEY = 'complyo_visitor_id';
    
    // Supported Languages (Phase 7)
    const SUPPORTED_LANGUAGES = ['de', 'en', 'fr', 'es', 'it', 'nl', 'pl', 'pt', 'sv', 'da', 'fi', 'no', 'cs', 'hu', 'ro', 'el', 'ru'];
    
    // Default Configuration
    const DEFAULT_CONFIG = {
        // Design
        layout: 'box_modal', // banner_bottom, banner_top, box_modal, floating_widget
        primaryColor: '#7c3aed',
        accentColor: '#9333ea',
        textColor: '#333333',
        bgColor: '#ffffff',
        buttonStyle: 'rounded', // rounded, square, pill
        position: 'bottom',
        widthMode: 'full', // full, boxed, compact
        
        // Behavior
        autoBlockScripts: true,
        respectDNT: true,
        cookieLifetimeDays: 365,
        showBranding: true,
        
        // Google Consent Mode v2 (Pflicht seit Maerz 2024)
        consent_mode_enabled: true,
        consent_mode_default: {
            ad_storage: 'denied',
            analytics_storage: 'denied',
            ad_user_data: 'denied',
            ad_personalization: 'denied'
        },
        
        // Google Tag Manager
        gtm_enabled: false,
        gtm_container_id: null,
        
        // Geo-Restriction
        geo_restriction_enabled: false,
        geo_countries: [],
        
        // Age Verification (Jugendschutz)
        age_verification_enabled: false,
        age_verification_min_age: 16,
        
        // Bannerless Mode
        bannerless_mode: false,
        
        // Services
        consent_mode_enabled: true,
        consent_mode_default: {
            ad_storage: 'denied',
            analytics_storage: 'denied',
            ad_user_data: 'denied',
            ad_personalization: 'denied'
        },
        
        // Google Tag Manager
        gtm_enabled: false,
        gtm_container_id: null,
        
        // Geo-Restriction
        geo_restriction_enabled: false,
        geo_countries: [],
        
        // Age Verification (Jugendschutz)
        age_verification_enabled: false,
        age_verification_min_age: 16,
        
        // Bannerless Mode
        bannerless_mode: false,
        
        // Services
        services: [],
        
        // Texts (default German) - synchronisiert mit Dashboard
        texts: {
            title: 'Datenschutz-Präferenz',
            description: 'Wir benötigen Ihre Einwilligung, bevor Sie unsere Website weiter besuchen können.\n\nWenn Sie unter 16 Jahre alt sind und Ihre Einwilligung zu optionalen Services geben möchten, müssen Sie Ihre Erziehungsberechtigten um Erlaubnis bitten.\n\nWir verwenden Cookies und andere Technologien auf unserer Website. Einige von ihnen sind essenziell, während andere uns helfen, diese Website und Ihre Erfahrung zu verbessern. Personenbezogene Daten können verarbeitet werden (z. B. IP-Adressen), z. B. für personalisierte Anzeigen und Inhalte oder die Messung von Anzeigen und Inhalten. Weitere Informationen über die Verwendung Ihrer Daten finden Sie in unserer Datenschutzerklärung. Es besteht keine Verpflichtung, in die Verarbeitung Ihrer Daten einzuwilligen, um dieses Angebot zu nutzen. Sie können Ihre Auswahl jederzeit unter Einstellungen widerrufen oder anpassen. Bitte beachten Sie, dass aufgrund individueller Einstellungen möglicherweise nicht alle Funktionen der Website verfügbar sind.',
            description2: 'Einige Services verarbeiten personenbezogene Daten in den USA. Mit Ihrer Einwilligung zur Nutzung dieser Services willigen Sie auch in die Verarbeitung Ihrer Daten in den USA gemäß Art. 49 (1) lit. a DSGVO ein. Der EuGH stuft die USA als ein Land mit unzureichendem Datenschutz nach EU-Standards ein. Es besteht beispielsweise die Gefahr, dass US-Behörden personenbezogene Daten in Überwachungsprogrammen verarbeiten, ohne dass für Europäerinnen und Europäer eine Klagemöglichkeit besteht.',
            ageNotice: '',
            acceptAll: 'Alle akzeptieren',
            continueWithout: 'Nur essenzielle Cookies akzeptieren',
            settingsLink: 'Individuelle Datenschutzeinstellungen',
            acceptSelected: 'Speichern',
            settings: 'Einstellungen',
            privacyPolicy: 'Datenschutzerklärung',
            cookiePolicy: 'Über Cookies',
            imprint: 'Impressum',
            necessary: 'Essenziell',
            functional: 'Funktional',
            analytics: 'Statistiken',
            marketing: 'Externe Medien',
            necessaryDesc: 'Essenzielle Services ermöglichen grundlegende Funktionen und sind für das ordnungsgemäße Funktionieren der Website erforderlich.',
            functionalDesc: 'Funktionale Cookies speichern Ihre Präferenzen wie Sprache und Region für ein verbessertes Nutzungserlebnis.',
            analyticsDesc: 'Statistik-Cookies helfen Webseiten-Besitzern zu verstehen, wie Besucher mit Webseiten interagieren, indem Informationen anonym gesammelt und gemeldet werden.',
            marketingDesc: 'Inhalte von Videoplattformen und Social-Media-Plattformen werden standardmäßig blockiert. Wenn externe Services akzeptiert werden, ist für den Zugriff auf diese Inhalte keine manuelle Einwilligung mehr erforderlich.',
            serviceCount: 'Service',
            learnMore: 'Erfahren Sie mehr über diesen Anbieter',
            expand: 'Informationen anzeigen',
            collapse: 'Informationen ausblenden'
        }
    };
    
    // ========================================================================
    // ComplyoCookieBanner Class
    // ========================================================================
    
    class ComplyoCookieBanner {
        constructor(config = {}) {
            this.siteId = this.getSiteIdFromScript();
            this.config = { ...DEFAULT_CONFIG, ...config };
            this.consent = this.loadConsent();
            this.visitorId = this.getOrCreateVisitorId();
            this.modalOpen = false;
            this.settingsOpen = false;
            this.serviceDetails = {}; // Store service information
            this.selectedServices = {}; // Track individual service selections
            
            // Initialize
            this.init();
        }
        
        // ====================================================================
        // Initialization
        // ====================================================================
        
        getSiteIdFromScript() {
            const script = document.currentScript || 
                          document.querySelector('script[data-site-id]') ||
                          document.querySelector('script[src*="cookie-compliance.js"]');
            
            if (script) {
                return script.getAttribute('data-site-id') || 
                       script.getAttribute('data-complyo-site-id') ||
                       new URL(script.src).searchParams.get('site_id');
            }
            
            console.warn('[Complyo] Site ID not found. Using default.');
            return 'demo-site';
        }
        
        getOrCreateVisitorId() {
            let visitorId = localStorage.getItem(VISITOR_ID_KEY);
            if (!visitorId) {
                visitorId = this.generateUUID();
                localStorage.setItem(VISITOR_ID_KEY, visitorId);
            }
            return visitorId;
        }
        
        generateUUID() {
            return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
                const r = Math.random() * 16 | 0;
                const v = c === 'x' ? r : (r & 0x3 | 0x8);
                return v.toString(16);
            });
        }
        
        /**
         * Generates a privacy-friendly browser fingerprint
         * 
         * This is NOT a tracking fingerprint - it's a pseudonymized device identifier
         * used for consent documentation (GDPR requirement).
         * 
         * We only use non-identifying characteristics:
         * - Language
         * - Screen resolution
         * - Timezone offset
         * - Hardware concurrency
         * - Platform type
         * 
         * This creates a hash that is:
         * - Consistent across sessions (same device = same hash)
         * - Not unique enough for cross-site tracking
         * - Privacy-compliant as per GDPR guidelines
         */
        generateFingerprint() {
            try {
                const components = [
                    // Language
                    navigator.language || 'unknown',
                    
                    // Screen characteristics (not exact dimensions for privacy)
                    Math.round(screen.width / 100) * 100 + 'x' + Math.round(screen.height / 100) * 100,
                    screen.colorDepth || 24,
                    
                    // Timezone
                    new Date().getTimezoneOffset(),
                    
                    // Hardware (rough category, not exact)
                    navigator.hardwareConcurrency ? 
                        (navigator.hardwareConcurrency <= 2 ? 'low' : 
                         navigator.hardwareConcurrency <= 4 ? 'medium' : 'high') : 'unknown',
                    
                    // Platform type (generic, not specific)
                    navigator.platform ? navigator.platform.split(' ')[0] : 'unknown',
                    
                    // Touch capability
                    'ontouchstart' in window || navigator.maxTouchPoints > 0 ? 'touch' : 'no-touch',
                    
                    // Cookie support
                    navigator.cookieEnabled ? 'cookies' : 'no-cookies',
                ];
                
                // Create hash from components
                const data = components.join('|');
                return this.hashString(data);
                
            } catch (error) {
                console.warn('[Complyo] Fingerprint generation failed:', error);
                return null;
            }
        }
        
        /**
         * Simple string hash function (FNV-1a inspired)
         * Not cryptographic, but sufficient for fingerprinting
         */
        hashString(str) {
            let hash = 2166136261; // FNV offset basis
            for (let i = 0; i < str.length; i++) {
                hash ^= str.charCodeAt(i);
                hash += (hash << 1) + (hash << 4) + (hash << 7) + (hash << 8) + (hash << 24);
            }
            // Convert to hex string
            return ('00000000' + (hash >>> 0).toString(16)).slice(-8) + 
                   ('00000000' + ((hash >>> 0) ^ 0x9e3779b9).toString(16)).slice(-8);
        }
        
        /**
         * Gets the device fingerprint (cached for performance)
         */
        getDeviceFingerprint() {
            if (!this._deviceFingerprint) {
                this._deviceFingerprint = this.generateFingerprint();
            }
            return this._deviceFingerprint;
        }
        
        async init() {
            // ✅ Initialize Google Consent Mode v2 FIRST (before any Google scripts load)
            // This MUST happen before gtag.js or analytics.js loads
            this.initGoogleConsentMode();
            
            // Check Do Not Track
            if (this.config.respectDNT && this.isDNTEnabled()) {
                console.log('[Complyo] Do Not Track detected. Banner not shown.');
                // Still update consent mode for DNT users
                this.updateGoogleConsentMode({ necessary: true, functional: false, analytics: false, marketing: false });
                return;
            }
            
            // Load configuration from server if site_id exists
            if (this.siteId && this.siteId !== 'demo-site') {
                await this.loadServerConfig();
            }
            
            // ✅ Phase 2: Check Geo-Restriction
            if (this.config.geo_restriction_enabled && this.config.geo_countries?.length > 0) {
                const shouldShow = await this.checkGeoRestriction();
                if (!shouldShow) {
                    console.log('[Complyo] Geo-restriction: Banner not shown in this region');
                    return;
                }
            }
            
            // ✅ Phase 6: Check for Bannerless Mode
            if (this.config.bannerless_mode) {
                console.log('[Complyo] Bannerless mode enabled - only content blockers active');
                // In bannerless mode, we don't show a banner but content blockers are still active
                // The consent will be set to "only necessary" automatically
                this.consent = {
                    necessary: true,
                    functional: false,
                    analytics: false,
                    marketing: false,
                    bannerless: true
                };
                this.updateGoogleConsentMode(this.consent);
                return;
            }
            
            // Wait for DOM
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', () => this.onDOMReady());
            } else {
                this.onDOMReady();
            }
        }
        
        /**
         * ✅ Phase 2: Geo-Restriction Check
         */
        async checkGeoRestriction() {
            try {
                const response = await fetch(`${API_BASE}/api/cookie-compliance/geo-check`);
                if (response.ok) {
                    const data = await response.json();
                    const visitorCountry = data.country_code;
                    const allowedCountries = this.config.geo_countries || [];
                    
                    // Check if visitor's country is in the allowed list
                    return allowedCountries.includes(visitorCountry);
                }
            } catch (error) {
                console.warn('[Complyo] Geo-check failed, showing banner:', error);
            }
            // Default: show banner on error
            return true;
        }
        
        /**
         * ✅ Phase 1: Age Verification Check
         */
        async checkAgeVerification() {
            if (!this.config.age_verification_enabled) {
                return true; // Age verification disabled
            }
            
            // Check if already verified
            const verified = localStorage.getItem('complyo_age_verified');
            if (verified) {
                return true;
            }
            
            // Show age verification modal
            return new Promise((resolve) => {
                this.showAgeVerificationModal(resolve);
            });
        }
        
        showAgeVerificationModal(callback) {
            const minAge = this.config.age_verification_min_age || 16;
            
            const modal = document.createElement('div');
            modal.className = 'complyo-age-modal';
            modal.innerHTML = `
                <style>
                    .complyo-age-modal {
                        position: fixed; inset: 0; z-index: 1000000;
                        background: rgba(0,0,0,0.8);
                        display: flex; align-items: center; justify-content: center;
                        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                    }
                    .complyo-age-content {
                        background: white; border-radius: 12px; padding: 32px;
                        max-width: 400px; text-align: center;
                    }
                    .complyo-age-icon { font-size: 48px; margin-bottom: 16px; }
                    .complyo-age-title { font-size: 20px; font-weight: 600; margin-bottom: 8px; color: #1f2937; }
                    .complyo-age-text { color: #6b7280; margin-bottom: 24px; font-size: 14px; }
                    .complyo-age-buttons { display: flex; gap: 12px; justify-content: center; }
                    .complyo-age-btn {
                        padding: 12px 24px; border-radius: 8px; font-weight: 500;
                        cursor: pointer; border: none; font-size: 14px;
                    }
                    .complyo-age-btn-yes { background: ${this.config.primaryColor || '#7c3aed'}; color: white; }
                    .complyo-age-btn-no { background: #e5e7eb; color: #374151; }
                </style>
                <div class="complyo-age-content">
                    <div class="complyo-age-icon">🔒</div>
                    <div class="complyo-age-title">Altersverifikation</div>
                    <div class="complyo-age-text">
                        Um diese Website zu nutzen, müssen Sie mindestens ${minAge} Jahre alt sein.
                    </div>
                    <div class="complyo-age-buttons">
                        <button class="complyo-age-btn complyo-age-btn-yes" data-age="yes">
                            Ich bin ${minAge}+ Jahre alt
                        </button>
                        <button class="complyo-age-btn complyo-age-btn-no" data-age="no">
                            Ich bin jünger
                        </button>
                    </div>
                </div>
            `;
            
            document.body.appendChild(modal);
            
            modal.querySelector('[data-age="yes"]').addEventListener('click', () => {
                localStorage.setItem('complyo_age_verified', 'true');
                modal.remove();
                callback(true);
            });
            
            modal.querySelector('[data-age="no"]').addEventListener('click', () => {
                modal.remove();
                callback(false);
                // Optionally redirect to another page
                // window.location.href = '/age-restricted';
            });
        }
        
        /**
         * ✅ Phase 6: Check if Reconsent is Required
         */
        async checkReconsentRequired() {
            if (!this.consent || !this.consent.configHash) {
                return false; // No previous consent to compare
            }
            
            try {
                const response = await fetch(
                    `${API_BASE}/api/cookie-compliance/reconsent-check/${this.siteId}?config_hash=${this.consent.configHash}`
                );
                if (response.ok) {
                    const data = await response.json();
                    return data.requires_reconsent;
                }
            } catch (error) {
                console.warn('[Complyo] Reconsent check failed:', error);
            }
            return false;
        }
        
        async loadServerConfig() {
            try {
                // Check for A/B test variant first
                const abTestVariant = await this.checkABTest();
                
                if (abTestVariant && abTestVariant.config) {
                    // Use A/B test config
                    console.log(`[Complyo] A/B Test active - Variant ${abTestVariant.variant}`);
                    this.abTest = {
                        testId: abTestVariant.test_id,
                        variant: abTestVariant.variant
                    };
                    this.applyServerConfig(abTestVariant.config);
                } else {
                    // Use regular config
                const response = await fetch(`${API_BASE}/api/cookie-compliance/config/${this.siteId}`);
                if (response.ok) {
                    const data = await response.json();
                    if (data.success && data.data) {
                        this.applyServerConfig(data.data);
                        }
                    }
                }
                
                // Load detailed service information
                await this.loadServiceDetails();
            } catch (error) {
                console.warn('[Complyo] Could not load server config:', error);
            }
        }
        
        async checkABTest() {
            try {
                const response = await fetch(
                    `${API_BASE}/api/ab-tests/assign/${this.siteId}/${this.visitorId}`
                );
                
                if (response.ok) {
                    const data = await response.json();
                    if (data.success && data.has_test) {
                        return {
                            test_id: data.test_id,
                            variant: data.variant,
                            config: data.config
                        };
                    }
                }
            } catch (error) {
                console.warn('[Complyo] Could not check A/B test:', error);
            }
            return null;
        }
        
        async trackABTestResult(action) {
            if (!this.abTest) return;
            
            try {
                const result = {
                    test_id: this.abTest.testId,
                    variant: this.abTest.variant,
                    impressions: action === 'impression' ? 1 : 0,
                    accepted_all: action === 'accept_all' ? 1 : 0,
                    accepted_partial: action === 'accept_partial' ? 1 : 0,
                    rejected_all: action === 'reject_all' ? 1 : 0,
                    accepted_analytics: 0,
                    accepted_marketing: 0,
                    accepted_functional: 0,
                    avg_decision_time_ms: this.getDecisionTime()
                };
                
                await fetch(`${API_BASE}/api/ab-tests/track`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(result)
                });
            } catch (error) {
                console.warn('[Complyo] Could not track A/B result:', error);
            }
        }
        
        getDecisionTime() {
            if (!this.bannerShownAt) return 0;
            return Date.now() - this.bannerShownAt;
        }
        
        async loadServiceDetails() {
            // Lade NUR Services die für diese spezifische Website konfiguriert wurden
            // (d.h. nach einem Scan gefunden wurden)
            const configuredServices = this.config.services || [];
            
            // Wenn keine Services konfiguriert sind, zeige nichts
            if (!configuredServices || configuredServices.length === 0) {
                console.log('[Complyo] Keine gescannten Services für diese Website');
                this.serviceDetails = {};
                return;
            }
            
            try {
                const servicesResponse = await fetch(`${API_BASE}/api/cookie-compliance/services`);
                if (servicesResponse.ok) {
                    const servicesData = await servicesResponse.json();
                    if (servicesData.success && servicesData.services) {
                        // Filtere nur Services die für DIESE Website konfiguriert sind
                        servicesData.services
                            .filter(service => configuredServices.includes(service.service_key))
                            .forEach(service => {
                                if (!this.serviceDetails[service.category]) {
                                    this.serviceDetails[service.category] = [];
                                }
                                // Parse cookies if it's a JSON string
                                let cookies = service.cookies || [];
                                if (typeof cookies === 'string') {
                                    try {
                                        cookies = JSON.parse(cookies);
                                    } catch (e) {
                                        cookies = [];
                                    }
                                }
                                this.serviceDetails[service.category].push({
                                    ...service,
                                    cookies: cookies
                                });
                            });
                        console.log('[Complyo] Gescannte Services geladen:', this.serviceDetails);
                    }
                }
            } catch (error) {
                console.warn('[Complyo] Could not load service details:', error);
            }
        }
        
        applyServerConfig(serverConfig) {
            // Merge server config with local config
            this.config.layout = serverConfig.layout || this.config.layout;
            this.config.primaryColor = serverConfig.primary_color || this.config.primaryColor;
            this.config.accentColor = serverConfig.accent_color || this.config.accentColor;
            this.config.textColor = serverConfig.text_color || this.config.textColor;
            this.config.bgColor = serverConfig.bg_color || this.config.bgColor;
            this.config.buttonStyle = serverConfig.button_style || this.config.buttonStyle;
            this.config.position = serverConfig.position || this.config.position;
            this.config.widthMode = serverConfig.width_mode || this.config.widthMode;
            this.config.showBranding = serverConfig.show_branding !== false;
            this.config.services = serverConfig.services || [];
            
            // Phase 6 features
            this.config.bannerless_mode = serverConfig.bannerless_mode || false;
            this.config.age_verification_enabled = serverConfig.age_verification_enabled || false;
            this.config.age_verification_min_age = serverConfig.age_verification_min_age || 16;
            this.config.geo_restriction_enabled = serverConfig.geo_restriction_enabled || false;
            this.config.geo_countries = serverConfig.geo_countries || [];
            
            // ✅ Phase 7: Auto-detect language and merge texts
            const browserLang = this.detectLanguage();
            this.currentLanguage = browserLang;
            
            // Load translations if available
            if (window.COMPLYO_TRANSLATIONS && window.COMPLYO_TRANSLATIONS[browserLang]) {
                this.config.texts = { ...this.config.texts, ...window.COMPLYO_TRANSLATIONS[browserLang] };
            }
            
            // Override with server texts if available
            if (serverConfig.texts && serverConfig.texts[browserLang]) {
                this.config.texts = { ...this.config.texts, ...serverConfig.texts[browserLang] };
            } else if (serverConfig.texts && serverConfig.texts['de']) {
                this.config.texts = { ...this.config.texts, ...serverConfig.texts['de'] };
            }
        }
        
        /**
         * ✅ Phase 7: Detect browser language
         */
        detectLanguage() {
            // Priority 1: URL parameter
            const urlParams = new URLSearchParams(window.location.search);
            const urlLang = urlParams.get('lang') || urlParams.get('language');
            if (urlLang && SUPPORTED_LANGUAGES.includes(urlLang)) {
                return urlLang;
            }
            
            // Priority 2: HTML lang attribute
            const htmlLang = document.documentElement.lang?.split('-')[0];
            if (htmlLang && SUPPORTED_LANGUAGES.includes(htmlLang)) {
                return htmlLang;
            }
            
            // Priority 3: Browser language
            const browserLang = navigator.language?.split('-')[0] || 'de';
            if (SUPPORTED_LANGUAGES.includes(browserLang)) {
                return browserLang;
            }
            
            // Default: German
            return 'de';
        }
        
        /**
         * ✅ Phase 7: Get translated text
         */
        t(key, params = {}) {
            let text = this.config.texts[key] || key;
            
            // Replace placeholders
            Object.keys(params).forEach(param => {
                text = text.replace(new RegExp(`\\{${param}\\}`, 'g'), params[param]);
            });
            
            return text;
        }
        
        isDNTEnabled() {
            return navigator.doNotTrack === '1' || 
                   window.doNotTrack === '1' || 
                   navigator.msDoNotTrack === '1';
        }
        
        async onDOMReady() {
            console.log('[Complyo] onDOMReady - Site-ID:', this.siteId);
            
            // ✅ Phase 1: Age Verification Check
            if (this.config.age_verification_enabled) {
                const ageVerified = await this.checkAgeVerification();
                if (!ageVerified) {
                    console.log('[Complyo] Age verification failed - content blocked');
                    return;
                }
            }
            
            // ✅ WICHTIG: Prüfe ob die Website überhaupt Cookies verwendet
            const configuredServices = this.config.services || [];
            const hasTrackingServices = Array.isArray(configuredServices) && configuredServices.length > 0;
            
            console.log('[Complyo] Konfigurierte Services:', configuredServices);
            
            // Wenn KEINE Services konfiguriert sind → KEIN Banner nötig!
            // Das ist korrekt: Wenn keine Tracking-Cookies, braucht man keinen Banner
            if (!hasTrackingServices) {
                console.log('[Complyo] ✅ Keine Tracking-Services konfiguriert - kein Banner erforderlich');
                console.log('[Complyo] ℹ️ Ihre Website verwendet nur essenzielle Cookies');
                // Setze automatisch "nur notwendige" Cookies als Consent
                const autoConsent = {
                    necessary: true,
                    functional: false,
                    analytics: false,
                    marketing: false,
                    services: [],
                    timestamp: new Date().toISOString(),
                    auto: true // Markiere als automatisch gesetzt
                };
                this.consent = autoConsent;
                this.applyConsent(autoConsent);
                return; // Kein Banner, kein Floating-Button
            }
            
            // ✅ Phase 6: Check if reconsent is required due to config changes
            if (this.consent) {
                const needsReconsent = await this.checkReconsentRequired();
                if (needsReconsent) {
                    console.log('[Complyo] Config changed - requesting new consent');
                    this.consent = null;
                    localStorage.removeItem(CONSENT_STORAGE_KEY);
                }
            }
            
            // Ab hier: Website HAT Tracking-Services → Banner erforderlich
            if (this.consent) {
                console.log('[Complyo] Consent vorhanden:', this.consent);
                this.applyConsent(this.consent);
                this.triggerConsentEvent(this.consent);
                this.renderFloatingButton();
            } else {
                console.log('[Complyo] Kein Consent - zeige Banner');
                this.render();
            }
        }
        
        // ====================================================================
        // Consent Management
        // ====================================================================
        
        loadConsent() {
            try {
                const stored = localStorage.getItem(CONSENT_STORAGE_KEY);
                if (stored) {
                    const consent = JSON.parse(stored);
                    const consentDate = localStorage.getItem(CONSENT_DATE_KEY);
                    
                    // Check if consent is expired
                    if (consentDate) {
                        const daysElapsed = (Date.now() - new Date(consentDate).getTime()) / (1000 * 60 * 60 * 24);
                        if (daysElapsed > this.config.cookieLifetimeDays) {
                            console.log('[Complyo] Consent expired. Requesting new consent.');
                            return null;
                        }
                    }
                    
                    return consent;
                }
            } catch (error) {
                console.warn('[Complyo] Error loading consent:', error);
            }
            return null;
        }
        
        saveConsent(consent) {
            localStorage.setItem(CONSENT_STORAGE_KEY, JSON.stringify(consent));
            localStorage.setItem(CONSENT_DATE_KEY, new Date().toISOString());
            this.consent = consent;
            
            // Log to server
            this.logConsentToServer(consent);
            
            // Apply consent
            this.applyConsent(consent);
            
            // Trigger event for content blocker
            this.triggerConsentEvent(consent);
        }
        
        async logConsentToServer(consent) {
            try {
                // Get device fingerprint for pseudonymized tracking
                const deviceFingerprint = this.getDeviceFingerprint();
                
                await fetch(`${API_BASE}/api/cookie-compliance/consent`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        site_id: this.siteId,
                        visitor_id: this.visitorId,
                        consent_categories: {
                            necessary: true,
                            functional: consent.functional || false,
                            analytics: consent.analytics || false,
                            marketing: consent.marketing || false
                        },
                        services_accepted: consent.services || [],
                        language: navigator.language.split('-')[0],
                        banner_shown: true,
                        // Privacy-friendly device fingerprint (alternative to IP hash)
                        device_fingerprint: deviceFingerprint
                    })
                });
            } catch (error) {
                console.warn('[Complyo] Error logging consent:', error);
            }
        }
        
        applyConsent(consent) {
            // Store consent in window for other scripts to access
            window.complyoConsent = consent;
            
            // ✅ Google Consent Mode v2 Update
            this.updateGoogleConsentMode(consent);
            
            // ✅ Google Tag Manager dataLayer Event
            this.pushDataLayerEvent(consent);
            
            // Enable cookies based on consent
            if (consent.analytics) {
                this.enableCategory('analytics');
            }
            if (consent.marketing) {
                this.enableCategory('marketing');
            }
            if (consent.functional) {
                this.enableCategory('functional');
            }
        }
        
        /**
         * ========================================================================
         * Google Consent Mode v2 Integration
         * ========================================================================
         * Required since March 2024 for Google services (Analytics, Ads, etc.)
         * 
         * Consent Types:
         * - ad_storage: Advertising cookies
         * - analytics_storage: Analytics cookies
         * - ad_user_data: Data sharing with Google Ads
         * - ad_personalization: Personalized advertising
         * - functionality_storage: Functional cookies
         * - personalization_storage: Personalization cookies
         * - security_storage: Security cookies (always granted)
         */
        initGoogleConsentMode() {
            // Initialize gtag if not present
            window.dataLayer = window.dataLayer || [];
            function gtag() { dataLayer.push(arguments); }
            window.gtag = window.gtag || gtag;
            
            // Set default consent state (denied until user consents)
            const defaultConsent = this.config.consent_mode_default || {
                'ad_storage': 'denied',
                'analytics_storage': 'denied',
                'ad_user_data': 'denied',
                'ad_personalization': 'denied',
                'functionality_storage': 'denied',
                'personalization_storage': 'denied',
                'security_storage': 'granted' // Always granted
            };
            
            gtag('consent', 'default', {
                ...defaultConsent,
                'wait_for_update': 500 // Wait 500ms for consent update
            });
            
            console.log('[Complyo] Google Consent Mode v2 initialized (default: denied)');
        }
        
        updateGoogleConsentMode(consent) {
            if (!this.config.consent_mode_enabled) return;
            
            // Map Complyo consent categories to Google Consent Mode
            const consentUpdate = {
                'ad_storage': consent.marketing ? 'granted' : 'denied',
                'analytics_storage': consent.analytics ? 'granted' : 'denied',
                'ad_user_data': consent.marketing ? 'granted' : 'denied',
                'ad_personalization': consent.marketing ? 'granted' : 'denied',
                'functionality_storage': consent.functional ? 'granted' : 'denied',
                'personalization_storage': consent.functional ? 'granted' : 'denied',
                'security_storage': 'granted'
            };
            
            // Update Google Consent Mode
            if (typeof gtag === 'function') {
                gtag('consent', 'update', consentUpdate);
                console.log('[Complyo] Google Consent Mode v2 updated:', consentUpdate);
            }
        }
        
        /**
         * ========================================================================
         * Google Tag Manager Integration
         * ========================================================================
         * Push consent events to dataLayer for GTM triggers
         */
        pushDataLayerEvent(consent) {
            window.dataLayer = window.dataLayer || [];
            
            // Push consent update event
            dataLayer.push({
                'event': 'complyo_consent_update',
                'complyo_consent': {
                    'necessary': true,
                    'functional': consent.functional || false,
                    'analytics': consent.analytics || false,
                    'marketing': consent.marketing || false
                },
                'complyo_services': consent.services || [],
                'complyo_timestamp': new Date().toISOString()
            });
            
            // Push individual category events for easier GTM triggers
            if (consent.analytics) {
                dataLayer.push({ 'event': 'complyo_analytics_granted' });
            }
            if (consent.marketing) {
                dataLayer.push({ 'event': 'complyo_marketing_granted' });
            }
            if (consent.functional) {
                dataLayer.push({ 'event': 'complyo_functional_granted' });
            }
            
            console.log('[Complyo] GTM dataLayer events pushed');
        }
        
        enableCategory(category) {
            console.log(`[Complyo] Enabling ${category} cookies`);
            // This will be picked up by the content blocker
        }
        
        triggerConsentEvent(consent) {
            // Trigger custom event for content blocker and other scripts
            const event = new CustomEvent('complyoConsent', {
                detail: {
                    consent: consent,
                    categories: {
                        necessary: true,
                        functional: consent.functional || false,
                        analytics: consent.analytics || false,
                        marketing: consent.marketing || false
                    },
                    services: consent.services || [],
                    // ✅ Include Google Consent Mode status
                    googleConsentMode: {
                        ad_storage: consent.marketing ? 'granted' : 'denied',
                        analytics_storage: consent.analytics ? 'granted' : 'denied',
                        ad_user_data: consent.marketing ? 'granted' : 'denied',
                        ad_personalization: consent.marketing ? 'granted' : 'denied'
                    }
                }
            });
            window.dispatchEvent(event);
            document.dispatchEvent(event);
        }
        
        // ====================================================================
        // Rendering
        // ====================================================================
        
        render() {
            // Inject styles
            this.injectStyles();
            
            // Create banner element
            const container = this.createBanner();
            document.body.appendChild(container);
            
            // Track banner shown time for A/B test
            this.bannerShownAt = Date.now();
            
            // Track A/B test impression
            if (this.abTest) {
                this.trackABTestResult('impression');
            }
            
            // Animate in
            requestAnimationFrame(() => {
                // Animate backdrop if exists
                const backdrop = container.querySelector('.complyo-backdrop');
                if (backdrop) {
                    backdrop.classList.add('complyo-show');
                }
                
                // Animate banner
                const banner = container.querySelector('.complyo-box-layout, .complyo-banner-layout');
                if (banner) {
                    banner.classList.add('complyo-show');
                }
                
                container.classList.add('complyo-show');
            });
            
            // Bind events
            this.bindEvents(container);
        }
        
        injectStyles() {
            if (document.getElementById('complyo-cookie-banner-styles')) {
                return; // Already injected
            }
            
            const style = document.createElement('style');
            style.id = 'complyo-cookie-banner-styles';
            style.textContent = this.getStyles();
            document.head.appendChild(style);
        }
        
        getStyles() {
            const { primaryColor, accentColor, textColor, bgColor, layout, position } = this.config;
            
            return `
                /* Complyo Cookie Banner Styles v${VERSION} - Modern Edition */
                .complyo-cookie-banner {
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                    font-size: 14px;
                    line-height: 1.6;
                    box-sizing: border-box;
                }
                
                .complyo-cookie-banner * {
                    box-sizing: border-box;
                }
                
                /* Banner Layout (Bottom/Top) - Modern Glassmorphism */
                .complyo-banner-layout {
                    position: fixed;
                    left: 0;
                    right: 0;
                    z-index: 999999;
                    background: linear-gradient(135deg, ${bgColor}f5 0%, ${bgColor}fa 100%);
                    backdrop-filter: blur(20px) saturate(180%);
                    -webkit-backdrop-filter: blur(20px) saturate(180%);
                    color: ${textColor};
                    padding: 28px;
                    box-shadow: 0 -8px 32px rgba(0, 0, 0, 0.12), 0 -2px 8px rgba(0, 0, 0, 0.08);
                    border-top: 1px solid rgba(255, 255, 255, 0.2);
                    opacity: 0;
                    transition: opacity 0.4s ease-out, transform 0.4s cubic-bezier(0.4, 0, 0.2, 1);
                }
                
                .complyo-banner-layout.complyo-position-bottom {
                    bottom: 0;
                    transform: translateY(100%);
                }
                
                .complyo-banner-layout.complyo-position-bottom.complyo-show {
                    opacity: 1;
                    transform: translateY(0);
                    animation: slideUpFade 0.5s cubic-bezier(0.4, 0, 0.2, 1);
                }
                
                .complyo-banner-layout.complyo-position-top {
                    top: 0;
                    transform: translateY(-100%);
                    border-top: none;
                    border-bottom: 1px solid rgba(255, 255, 255, 0.2);
                }
                
                .complyo-banner-layout.complyo-position-top.complyo-show {
                    opacity: 1;
                    transform: translateY(0);
                    animation: slideDownFade 0.5s cubic-bezier(0.4, 0, 0.2, 1);
                }
                
                @keyframes slideUpFade {
                    0% {
                        transform: translateY(100%);
                        opacity: 0;
                    }
                    100% {
                        transform: translateY(0);
                        opacity: 1;
                    }
                }
                
                @keyframes slideDownFade {
                    0% {
                        transform: translateY(-100%);
                        opacity: 0;
                    }
                    100% {
                        transform: translateY(0);
                        opacity: 1;
                    }
                }
                
                /* Box/Modal Layout - Clean & Professional */
                .complyo-box-layout {
                    position: fixed;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%) scale(0.95);
                    background: ${bgColor};
                    color: ${textColor};
                    border-radius: 12px;
                    padding: 48px 52px;
                    max-width: 720px;
                    width: 92%;
                    max-height: 88vh;
                    overflow-y: auto;
                    box-shadow: 0 24px 72px rgba(0, 0, 0, 0.15), 0 8px 16px rgba(0, 0, 0, 0.1);
                    z-index: 1000000;
                    opacity: 0;
                    transition: opacity 0.3s ease-out, transform 0.3s ease-out;
                }
                
                .complyo-box-layout.complyo-show {
                    opacity: 1;
                    transform: translate(-50%, -50%) scale(1);
                }
                
                /* Backdrop for modal */
                .complyo-backdrop {
                    position: fixed;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: rgba(0, 0, 0, 0.65);
                    backdrop-filter: blur(4px);
                    -webkit-backdrop-filter: blur(4px);
                    z-index: 999998;
                    opacity: 0;
                    transition: opacity 0.35s ease-out;
                }
                
                .complyo-backdrop.complyo-show {
                    opacity: 1;
                }
                
                /* Content */
                .complyo-content {
                    max-width: 1200px;
                    margin: 0 auto;
                }
                
                .complyo-box-layout .complyo-content {
                    max-width: 100%;
                }
                
                .complyo-title {
                    margin: 0 0 28px 0;
                    font-size: 26px;
                    font-weight: 700;
                    color: ${textColor};
                    text-align: center;
                    letter-spacing: -0.02em;
                    line-height: 1.3;
                }
                
                .complyo-description {
                    margin: 0 0 18px 0;
                    color: ${textColor};
                    opacity: 0.88;
                    line-height: 1.75;
                    font-size: 15px;
                    text-align: left;
                    white-space: pre-line;
                }
                
                .complyo-description a {
                    color: ${primaryColor};
                    text-decoration: underline;
                    font-weight: 500;
                }
                
                .complyo-description a:hover {
                    color: ${accentColor};
                }
                
                .complyo-age-notice {
                    margin: 24px 0 0 0;
                    padding: 16px 20px;
                    background: #f9fafb;
                    border-left: 4px solid ${primaryColor};
                    font-size: 13.5px;
                    color: ${textColor};
                    opacity: 0.85;
                    line-height: 1.65;
                    border-radius: 4px;
                }
                
                /* Buttons - Clean & Professional */
                .complyo-actions {
                    display: flex;
                    flex-direction: column;
                    gap: 14px;
                    margin-top: 36px;
                }
                
                .complyo-btn {
                    padding: 17px 32px;
                    border: none;
                    font-size: 16px;
                    font-weight: 600;
                    cursor: pointer;
                    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
                    width: 100%;
                    text-align: center;
                    letter-spacing: -0.01em;
                }
                
                .complyo-btn:focus {
                    outline: 3px solid ${primaryColor};
                    outline-offset: 2px;
                }
                
                .complyo-btn-rounded {
                    border-radius: 10px;
                }
                
                .complyo-btn-square {
                    border-radius: 6px;
                }
                
                .complyo-btn-pill {
                    border-radius: 100px;
                }
                
                .complyo-btn-primary {
                    background: ${primaryColor};
                    color: white;
                    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
                }
                
                .complyo-btn-primary:hover {
                    background: ${accentColor};
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
                    transform: translateY(-1px);
                }
                
                .complyo-btn-primary:active {
                    transform: translateY(0);
                    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
                }
                
                .complyo-btn-secondary {
                    background: white;
                    color: ${primaryColor};
                    border: 2px solid ${primaryColor};
                }
                
                .complyo-btn-secondary:hover {
                    background: ${primaryColor};
                    color: white;
                    transform: translateY(-1px);
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
                }
                
                .complyo-btn-secondary:active {
                    transform: translateY(0);
                }
                
                .complyo-btn-link {
                    background: transparent;
                    color: ${primaryColor};
                    padding: 14px;
                    font-weight: 500;
                    text-decoration: underline;
                    font-size: 15px;
                }
                
                .complyo-btn-link:hover {
                    color: ${accentColor};
                    background: rgba(0, 0, 0, 0.02);
                }
                
                .complyo-btn-link:active {
                    background: rgba(0, 0, 0, 0.04);
                }
                
                /* Settings Modal */
                .complyo-settings-modal {
                    position: fixed;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%) scale(0.9);
                    background: ${bgColor};
                    color: ${textColor};
                    border-radius: 16px;
                    padding: 32px;
                    max-width: 700px;
                    width: 90%;
                    max-height: 80vh;
                    overflow-y: auto;
                    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                    z-index: 1000000;
                    opacity: 0;
                    transition: opacity 0.3s ease-out, transform 0.3s ease-out;
                }
                
                .complyo-settings-modal.complyo-show {
                    opacity: 1;
                    transform: translate(-50%, -50%) scale(1);
                }
                
                .complyo-settings-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 24px;
                }
                
                .complyo-settings-title {
                    font-size: 24px;
                    font-weight: 600;
                    margin: 0;
                }
                
                .complyo-close-btn {
                    background: none;
                    border: none;
                    font-size: 24px;
                    cursor: pointer;
                    color: ${textColor};
                    opacity: 0.6;
                    padding: 4px;
                    line-height: 1;
                }
                
                .complyo-close-btn:hover {
                    opacity: 1;
                }
                
                /* Cookie Categories */
                .complyo-category {
                    margin-bottom: 20px;
                    padding: 16px;
                    background: rgba(0, 0, 0, 0.02);
                    border-radius: 8px;
                    border: 1px solid rgba(0, 0, 0, 0.05);
                }
                
                .complyo-category-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 8px;
                }
                
                .complyo-category-info {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }
                
                .complyo-category-name {
                    font-weight: 600;
                    font-size: 16px;
                }
                
                .complyo-service-count {
                    display: inline-block;
                    background: ${primaryColor};
                    color: white;
                    font-size: 11px;
                    font-weight: 600;
                    padding: 2px 8px;
                    border-radius: 12px;
                    min-width: 20px;
                    text-align: center;
                }
                
                .complyo-category-desc {
                    font-size: 13px;
                    opacity: 0.8;
                    margin: 0 0 12px 0;
                    line-height: 1.5;
                }
                
                /* Services List */
                .complyo-services-list {
                    margin-top: 12px;
                    padding-left: 0;
                    border-left: 2px solid rgba(0, 0, 0, 0.08);
                    margin-left: 8px;
                }
                
                .complyo-service-item {
                    padding: 12px 16px;
                    margin-bottom: 8px;
                    background: white;
                    border-radius: 6px;
                    border: 1px solid rgba(0, 0, 0, 0.06);
                }
                
                .complyo-service-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 6px;
                }
                
                .complyo-service-info {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    flex: 1;
                }
                
                .complyo-service-name {
                    font-weight: 500;
                    font-size: 14px;
                    color: ${textColor};
                }
                
                .complyo-cookie-count {
                    display: inline-block;
                    background: rgba(0, 0, 0, 0.06);
                    color: ${textColor};
                    font-size: 10px;
                    font-weight: 600;
                    padding: 2px 6px;
                    border-radius: 10px;
                    opacity: 0.7;
                }
                
                .complyo-service-desc {
                    font-size: 12px;
                    opacity: 0.7;
                    margin: 4px 0;
                    line-height: 1.4;
                }
                
                .complyo-service-link {
                    font-size: 11px;
                    color: ${primaryColor};
                    text-decoration: none;
                    font-weight: 500;
                    display: inline-block;
                    margin-top: 4px;
                }
                
                .complyo-service-link:hover {
                    text-decoration: underline;
                }
                
                /* Toggle Switch */
                .complyo-toggle {
                    position: relative;
                    display: inline-block;
                    width: 48px;
                    height: 24px;
                }
                
                .complyo-toggle-small {
                    width: 40px;
                    height: 20px;
                }
                
                .complyo-toggle-small .complyo-toggle-slider {
                    height: 20px;
                }
                
                .complyo-toggle-small .complyo-toggle-slider:before {
                    height: 14px;
                    width: 14px;
                    left: 3px;
                    bottom: 3px;
                }
                
                .complyo-toggle-small input:checked + .complyo-toggle-slider:before {
                    transform: translateX(20px);
                }
                
                .complyo-toggle input {
                    opacity: 0;
                    width: 0;
                    height: 0;
                }
                
                .complyo-toggle-slider {
                    position: absolute;
                    cursor: pointer;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background-color: #ccc;
                    transition: 0.3s;
                    border-radius: 24px;
                }
                
                .complyo-toggle-slider:before {
                    position: absolute;
                    content: "";
                    height: 18px;
                    width: 18px;
                    left: 3px;
                    bottom: 3px;
                    background-color: white;
                    transition: 0.3s;
                    border-radius: 50%;
                }
                
                .complyo-toggle input:checked + .complyo-toggle-slider {
                    background-color: ${primaryColor};
                }
                
                .complyo-toggle input:checked + .complyo-toggle-slider:before {
                    transform: translateX(24px);
                }
                
                .complyo-toggle input:disabled + .complyo-toggle-slider {
                    opacity: 0.5;
                    cursor: not-allowed;
                }
                
                /* Footer Links */
                .complyo-footer {
                    margin-top: 32px;
                    padding-top: 24px;
                    border-top: 1px solid rgba(0, 0, 0, 0.08);
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    gap: 16px;
                    flex-wrap: wrap;
                }
                
                .complyo-footer a {
                    color: ${textColor};
                    text-decoration: none;
                    font-size: 14px;
                    opacity: 0.7;
                    transition: opacity 0.2s ease;
                }
                
                .complyo-footer a:hover {
                    opacity: 1;
                    text-decoration: underline;
                    color: ${primaryColor};
                }
                
                /* Branding */
                .complyo-branding {
                    margin-top: 16px;
                    text-align: center;
                    font-size: 12px;
                    opacity: 0.6;
                }
                
                .complyo-branding a {
                    color: ${primaryColor};
                    text-decoration: none;
                }
                
                .complyo-branding a:hover {
                    text-decoration: underline;
                }
                
                /* Responsive */
                @media (max-width: 768px) {
                    .complyo-banner-layout {
                        padding: 24px 20px;
                    }
                    
                    .complyo-box-layout {
                        padding: 36px 28px;
                        width: 94%;
                        max-height: 90vh;
                    }
                    
                    .complyo-title {
                        font-size: 22px;
                        margin-bottom: 22px;
                    }
                    
                    .complyo-description {
                        font-size: 14px;
                        line-height: 1.7;
                    }
                    
                    .complyo-age-notice {
                        font-size: 13px;
                        padding: 14px 16px;
                    }
                    
                    .complyo-btn {
                        padding: 15px 24px;
                        font-size: 15px;
                    }
                    
                    .complyo-actions {
                        margin-top: 28px;
                        gap: 12px;
                    }
                    
                    .complyo-footer {
                        margin-top: 28px;
                        padding-top: 20px;
                        font-size: 13px;
                        gap: 12px;
                    }
                }
                
                @media (max-width: 480px) {
                    .complyo-box-layout {
                        padding: 28px 24px;
                        width: 96%;
                    }
                    
                    .complyo-title {
                        font-size: 20px;
                    }
                    
                    .complyo-description {
                        font-size: 13.5px;
                    }
                }
                
                /* Accessibility */
                .complyo-cookie-banner:focus-within {
                    outline: 2px solid ${primaryColor};
                    outline-offset: 4px;
                }
                
                .complyo-btn:focus {
                    outline: 2px solid ${primaryColor};
                    outline-offset: 2px;
                }
            `;
        }
        
        createBanner() {
            const layout = this.config.layout;
            const isBox = layout === 'box_modal';
            
            // Create container
            const container = document.createElement('div');
            container.className = 'complyo-cookie-banner';
            container.setAttribute('role', 'dialog');
            container.setAttribute('aria-labelledby', 'complyo-banner-title');
            container.setAttribute('aria-describedby', 'complyo-banner-desc');
            container.setAttribute('aria-modal', isBox ? 'true' : 'false');
            
            // Add backdrop for modal
            if (isBox) {
                const backdrop = document.createElement('div');
                backdrop.className = 'complyo-backdrop';
                backdrop.id = 'complyo-backdrop';
                container.appendChild(backdrop);
            }
            
            // Create banner
            const banner = document.createElement('div');
            banner.className = isBox ? 'complyo-box-layout' : 'complyo-banner-layout';
            banner.classList.add(`complyo-position-${this.config.position}`);
            banner.id = 'complyo-banner';
            
            // Content
            banner.innerHTML = `
                <div class="complyo-content">
                    <h2 id="complyo-banner-title" class="complyo-title">${this.config.texts.title}</h2>
                    <p id="complyo-banner-desc" class="complyo-description">
                        ${this.config.texts.description}
                    </p>
                    <p class="complyo-description">
                        ${this.config.texts.description2}
                    </p>
                    ${this.config.texts.ageNotice ? `
                        <div class="complyo-age-notice">
                            ${this.config.texts.ageNotice}
                        </div>
                    ` : ''}
                    <div class="complyo-actions">
                        <button 
                            id="complyo-accept-all" 
                            class="complyo-btn complyo-btn-primary complyo-btn-${this.config.buttonStyle}"
                            aria-label="${this.config.texts.acceptAll}"
                        >
                            ${this.config.texts.acceptAll}
                        </button>
                        <button 
                            id="complyo-reject-all" 
                            class="complyo-btn complyo-btn-secondary complyo-btn-${this.config.buttonStyle}"
                            aria-label="${this.config.texts.continueWithout}"
                        >
                            ${this.config.texts.continueWithout}
                        </button>
                        <button 
                            id="complyo-settings" 
                            class="complyo-btn complyo-btn-link"
                            aria-label="${this.config.texts.settingsLink}"
                        >
                            ${this.config.texts.settingsLink}
                        </button>
                    </div>
                    <div class="complyo-footer">
                        <a href="/datenschutz" target="_blank" rel="noopener">${this.config.texts.privacyPolicy}</a>
                        <span style="opacity: 0.5;">•</span>
                        <a href="/cookie-richtlinie" target="_blank" rel="noopener">${this.config.texts.cookiePolicy}</a>
                        <span style="opacity: 0.5;">•</span>
                        <a href="/impressum" target="_blank" rel="noopener">${this.config.texts.imprint}</a>
                    </div>
                    ${this.config.showBranding ? `
                        <div class="complyo-branding">
                            Powered by <a href="https://complyo.tech" target="_blank" rel="noopener">Complyo</a>
                        </div>
                    ` : ''}
                </div>
            `;
            
            container.appendChild(banner);
            
            return container;
        }
        
        bindEvents(banner) {
            // Accept all
            const acceptBtn = banner.querySelector('#complyo-accept-all');
            acceptBtn.addEventListener('click', () => this.acceptAll());
            
            // Reject all
            const rejectBtn = banner.querySelector('#complyo-reject-all');
            rejectBtn.addEventListener('click', () => this.rejectAll());
            
            // Settings
            const settingsBtn = banner.querySelector('#complyo-settings');
            settingsBtn.addEventListener('click', () => this.openSettings());
            
            // Backdrop click (close modal)
            const backdrop = banner.querySelector('#complyo-backdrop');
            if (backdrop) {
                backdrop.addEventListener('click', () => this.acceptAll());
            }
        }
        
        // ====================================================================
        // Actions
        // ====================================================================
        
        acceptAll() {
            const consent = {
                necessary: true,
                functional: true,
                analytics: true,
                marketing: true,
                services: this.config.services,
                timestamp: new Date().toISOString()
            };
            
            // Track A/B test result
            if (this.abTest) {
                this.trackABTestResult('accept_all');
            }
            
            this.saveConsent(consent);
            this.hideBanner();
        }
        
        rejectAll() {
            const consent = {
                necessary: true,
                functional: false,
                analytics: false,
                marketing: false,
                services: [],
                timestamp: new Date().toISOString()
            };
            
            // Track A/B test result
            if (this.abTest) {
                this.trackABTestResult('reject_all');
            }
            
            this.saveConsent(consent);
            this.hideBanner();
        }
        
        openSettings() {
            this.settingsOpen = true;
            this.renderSettingsModal();
        }
        
        saveCustom(selections) {
            const consent = {
                necessary: true,
                functional: selections.functional || false,
                analytics: selections.analytics || false,
                marketing: selections.marketing || false,
                services: selections.services || [],
                timestamp: new Date().toISOString()
            };
            
            // Track A/B test result
            if (this.abTest) {
                this.trackABTestResult('accept_partial');
            }
            
            this.saveConsent(consent);
            this.closeSettings();
            this.hideBanner();
        }
        
        hideBanner() {
            const banner = document.querySelector('.complyo-cookie-banner');
            if (banner) {
                banner.classList.remove('complyo-show');
                setTimeout(() => {
                    banner.remove();
                    // Zeige Floating Button nach Banner-Schließung
                    this.renderFloatingButton();
                }, 300);
            }
        }
        
        closeSettings() {
            const modal = document.getElementById('complyo-settings-modal');
            const backdrop = document.getElementById('complyo-settings-backdrop');
            
            if (modal) {
                modal.style.opacity = '0';
                modal.style.transform = 'translate(-50%, -50%) scale(0.95)';
                setTimeout(() => modal.remove(), 300);
            }
            
            if (backdrop) {
                backdrop.style.opacity = '0';
                setTimeout(() => backdrop.remove(), 300);
            }
            
            this.settingsOpen = false;
        }
        
        renderSettingsModal() {
            const { primaryColor, accentColor, bgColor, textColor } = this.config;
            this.activeSettingsTab = 'service-groups';
            this.selectedServices = this.selectedServices || {};
            this.expandedItems = {};
            
            // Initialize selections from existing consent or default
            if (this.consent) {
                this.categorySelections = {
                    necessary: true,
                    functional: this.consent.functional || false,
                    analytics: this.consent.analytics || false,
                    marketing: this.consent.marketing || false
                };
            } else {
                this.categorySelections = {
                    necessary: true,
                    functional: false,
                    analytics: false,
                    marketing: false
                };
            }
            
            // Inject Borlabs-style CSS
            this.injectSettingsStyles();
            
            // Create backdrop
            const backdrop = document.createElement('div');
            backdrop.id = 'complyo-settings-backdrop';
            backdrop.className = 'cps-backdrop';
            document.body.appendChild(backdrop);
            
            // Create modal
            const modal = document.createElement('div');
            modal.id = 'complyo-settings-modal';
            modal.className = 'cps-modal';
            modal.setAttribute('role', 'dialog');
            modal.setAttribute('aria-labelledby', 'complyo-settings-title');
            modal.setAttribute('aria-modal', 'true');
            
            modal.innerHTML = this.renderSettingsHTML();
            document.body.appendChild(modal);
            
            // Animate in
            requestAnimationFrame(() => {
                backdrop.classList.add('cps-show');
                modal.classList.add('cps-show');
            });
            
            // Bind all events
            this.bindSettingsEvents(modal, backdrop);
        }
        
        injectSettingsStyles() {
            if (document.getElementById('complyo-settings-styles')) return;
            
            const { primaryColor, accentColor } = this.config;
            const style = document.createElement('style');
            style.id = 'complyo-settings-styles';
            style.textContent = `
                /* Complyo Settings Modal - Borlabs Style */
                .cps-backdrop {
                    position: fixed;
                    inset: 0;
                    background: rgba(0, 0, 0, 0.5);
                    z-index: 999998;
                    opacity: 0;
                    transition: opacity 0.3s ease;
                }
                .cps-backdrop.cps-show { opacity: 1; }
                
                .cps-modal {
                    position: fixed;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%) scale(0.95);
                    background: #fff;
                    border-radius: 0;
                    width: 95%;
                    max-width: 900px;
                    max-height: 90vh;
                    display: flex;
                    flex-direction: column;
                    z-index: 999999;
                    opacity: 0;
                    transition: all 0.3s ease;
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                    box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                    border: 1px solid #e5e7eb;
                }
                .cps-modal.cps-show {
                    opacity: 1;
                    transform: translate(-50%, -50%) scale(1);
                }
                
                /* Header */
                .cps-header {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    padding: 20px 24px;
                    border-bottom: 1px solid #e5e7eb;
                    background: #fff;
                }
                .cps-header-left {
                    display: flex;
                    align-items: center;
                    gap: 12px;
                }
                .cps-logo {
                    width: 36px;
                    height: 36px;
                    background: ${primaryColor};
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-weight: bold;
                    font-size: 16px;
                }
                .cps-title {
                    font-size: 18px;
                    font-weight: 600;
                    color: #1f2937;
                    margin: 0;
                }
                .cps-header-links {
                    display: flex;
                    gap: 16px;
                }
                .cps-header-links a {
                    color: #6b7280;
                    text-decoration: none;
                    font-size: 13px;
                }
                .cps-header-links a:hover {
                    color: ${primaryColor};
                }
                
                /* Description */
                .cps-description {
                    padding: 16px 24px;
                    background: #f9fafb;
                    border-bottom: 1px solid #e5e7eb;
                    font-size: 13px;
                    color: #6b7280;
                    line-height: 1.6;
                    white-space: pre-line;
                    max-height: 200px;
                    overflow-y: auto;
                }
                
                /* Tabs */
                .cps-tabs {
                    display: flex;
                    border-bottom: 1px solid #e5e7eb;
                    background: #fff;
                }
                .cps-tab {
                    flex: 1;
                    padding: 14px 16px;
                    background: transparent;
                    border: none;
                    font-size: 13px;
                    font-weight: 500;
                    color: #6b7280;
                    cursor: pointer;
                    transition: all 0.2s;
                    border-bottom: 3px solid transparent;
                    text-align: center;
                }
                .cps-tab:hover {
                    background: #f9fafb;
                    color: #374151;
                }
                .cps-tab.cps-active {
                    background: ${primaryColor};
                    color: white;
                    border-bottom-color: ${primaryColor};
                }
                
                /* Tab Content */
                .cps-content {
                    flex: 1;
                    overflow-y: auto;
                    max-height: calc(90vh - 280px);
                    background: #fff;
                }
                .cps-tab-panel {
                    display: none;
                    padding: 0;
                }
                .cps-tab-panel.cps-active {
                    display: block;
                }
                
                /* Actions Bar (Alle auswählen/abwählen) */
                .cps-actions-bar {
                    display: flex;
                    justify-content: flex-end;
                    gap: 8px;
                    padding: 12px 24px;
                    border-bottom: 1px solid #e5e7eb;
                    background: #f9fafb;
                }
                .cps-action-btn {
                    padding: 6px 12px;
                    font-size: 12px;
                    border: 1px solid #d1d5db;
                    background: #fff;
                    color: #374151;
                    border-radius: 4px;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    gap: 4px;
                }
                .cps-action-btn:hover {
                    background: #f3f4f6;
                }
                
                /* Search Bar */
                .cps-search-bar {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    padding: 12px 24px;
                    border-bottom: 1px solid #e5e7eb;
                    background: #fff;
                }
                .cps-search-input {
                    flex: 1;
                    max-width: 400px;
                    padding: 8px 12px;
                    border: 1px solid #d1d5db;
                    border-radius: 4px;
                    font-size: 13px;
                    outline: none;
                }
                .cps-search-input:focus {
                    border-color: ${primaryColor};
                }
                .cps-search-count {
                    font-size: 13px;
                    color: #6b7280;
                }
                
                /* Category/Service Item */
                .cps-item {
                    border-bottom: 1px solid #e5e7eb;
                }
                .cps-item:last-child {
                    border-bottom: none;
                }
                .cps-item-header {
                    display: flex;
                    align-items: flex-start;
                    padding: 16px 24px;
                    gap: 12px;
                }
                .cps-item-checkbox {
                    margin-top: 2px;
                }
                .cps-item-checkbox input[type="checkbox"] {
                    width: 18px;
                    height: 18px;
                    accent-color: ${primaryColor};
                    cursor: pointer;
                }
                .cps-item-content {
                    flex: 1;
                }
                .cps-item-title {
                    font-size: 14px;
                    font-weight: 600;
                    color: #1f2937;
                    margin: 0 0 4px 0;
                }
                .cps-item-desc {
                    font-size: 13px;
                    color: #6b7280;
                    line-height: 1.5;
                    margin: 0;
                }
                .cps-item-actions {
                    display: flex;
                    align-items: center;
                    gap: 12px;
                }
                .cps-expand-btn {
                    background: none;
                    border: none;
                    color: ${primaryColor};
                    font-size: 12px;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    gap: 4px;
                    white-space: nowrap;
                }
                .cps-expand-btn:hover {
                    text-decoration: underline;
                }
                
                /* Toggle Switch */
                .cps-toggle {
                    position: relative;
                    width: 48px;
                    height: 26px;
                    flex-shrink: 0;
                }
                .cps-toggle input {
                    opacity: 0;
                    width: 0;
                    height: 0;
                }
                .cps-toggle-slider {
                    position: absolute;
                    cursor: pointer;
                    inset: 0;
                    background: #d1d5db;
                    border-radius: 26px;
                    transition: 0.3s;
                }
                .cps-toggle-slider:before {
                    position: absolute;
                    content: "";
                    height: 20px;
                    width: 20px;
                    left: 3px;
                    bottom: 3px;
                    background: white;
                    border-radius: 50%;
                    transition: 0.3s;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
                }
                .cps-toggle input:checked + .cps-toggle-slider {
                    background: ${primaryColor};
                }
                .cps-toggle input:checked + .cps-toggle-slider:before {
                    transform: translateX(22px);
                }
                .cps-toggle input:disabled + .cps-toggle-slider {
                    opacity: 0.6;
                    cursor: not-allowed;
                }
                
                /* Expanded Details */
                .cps-item-details {
                    display: none;
                    padding: 0 24px 16px 54px;
                    background: #f9fafb;
                }
                .cps-item-details.cps-expanded {
                    display: block;
                }
                .cps-details-section {
                    margin-bottom: 12px;
                }
                .cps-details-title {
                    font-size: 12px;
                    font-weight: 600;
                    color: #374151;
                    margin-bottom: 8px;
                }
                .cps-details-row {
                    display: flex;
                    padding: 6px 0;
                    font-size: 12px;
                    border-bottom: 1px solid #e5e7eb;
                }
                .cps-details-row:last-child {
                    border-bottom: none;
                }
                .cps-details-label {
                    width: 180px;
                    color: #6b7280;
                    flex-shrink: 0;
                }
                .cps-details-value {
                    color: #1f2937;
                    word-break: break-word;
                }
                .cps-details-value a {
                    color: ${primaryColor};
                    text-decoration: none;
                }
                .cps-details-value a:hover {
                    text-decoration: underline;
                }
                
                /* History Tab */
                .cps-history-table {
                    width: 100%;
                    border-collapse: collapse;
                    font-size: 13px;
                }
                .cps-history-table th {
                    background: ${primaryColor};
                    color: white;
                    padding: 12px 16px;
                    text-align: left;
                    font-weight: 500;
                }
                .cps-history-table td {
                    padding: 12px 16px;
                    border-bottom: 1px solid #e5e7eb;
                    vertical-align: top;
                }
                .cps-uid {
                    padding: 16px 24px;
                    font-size: 12px;
                    color: #6b7280;
                    border-top: 1px solid #e5e7eb;
                }
                
                /* Footer */
                .cps-footer {
                    display: flex;
                    gap: 12px;
                    padding: 16px 24px;
                    border-top: 1px solid #e5e7eb;
                    background: #fff;
                }
                .cps-footer-btn {
                    flex: 1;
                    padding: 14px 20px;
                    font-size: 14px;
                    font-weight: 600;
                    border: none;
                    border-radius: 0;
                    cursor: pointer;
                    transition: all 0.2s;
                }
                .cps-btn-save {
                    background: ${primaryColor};
                    color: white;
                }
                .cps-btn-save:hover {
                    background: ${accentColor};
                }
                .cps-btn-accept {
                    background: ${primaryColor};
                    color: white;
                }
                .cps-btn-accept:hover {
                    background: ${accentColor};
                }
                .cps-btn-reject {
                    background: #dc2626;
                    color: white;
                }
                .cps-btn-reject:hover {
                    background: #b91c1c;
                }
                
                /* Responsive */
                @media (max-width: 640px) {
                    .cps-modal {
                        width: 100%;
                        height: 100%;
                        max-height: 100%;
                        border-radius: 0;
                    }
                    .cps-tabs {
                        flex-wrap: wrap;
                    }
                    .cps-tab {
                        flex: 1 1 50%;
                    }
                    .cps-footer {
                        flex-direction: column;
                    }
                    .cps-header-links {
                        display: none;
                    }
                }
            `;
            document.head.appendChild(style);
        }
        
        renderSettingsHTML() {
            const { primaryColor } = this.config;
            return `
                <!-- Header -->
                <div class="cps-header">
                    <div class="cps-header-left">
                        <div class="cps-logo">C</div>
                        <h2 class="cps-title" id="complyo-settings-title">Datenschutz-Präferenz</h2>
                    </div>
                    <div class="cps-header-links">
                        <a href="/datenschutz" target="_blank">Datenschutzerklärung</a>
                        <a href="/impressum" target="_blank">Impressum</a>
                    </div>
                </div>
                
                <!-- Description -->
                <div class="cps-description">
                    ${this.config.texts?.description || 'Hier finden Sie eine Übersicht über alle verwendeten Cookies. Sie können Ihre Einwilligung für ganze Kategorien geben oder sich weitere Informationen anzeigen lassen und bestimmte Cookies auswählen.'}
                </div>
                
                <!-- Tabs -->
                <div class="cps-tabs">
                    <button class="cps-tab cps-active" data-tab="service-groups">Service-Gruppen</button>
                    <button class="cps-tab" data-tab="services">Services</button>
                    <button class="cps-tab" data-tab="providers">Provider</button>
                    <button class="cps-tab" data-tab="history">Einwilligung-Historie</button>
                </div>
                
                <!-- Tab Content -->
                <div class="cps-content">
                    <!-- Service Groups Tab -->
                    <div class="cps-tab-panel cps-active" data-panel="service-groups">
                        ${this.renderServiceGroupsTab()}
                    </div>
                    
                    <!-- Services Tab -->
                    <div class="cps-tab-panel" data-panel="services">
                        ${this.renderServicesTab()}
                    </div>
                    
                    <!-- Providers Tab -->
                    <div class="cps-tab-panel" data-panel="providers">
                        ${this.renderProvidersTab()}
                    </div>
                    
                    <!-- History Tab -->
                    <div class="cps-tab-panel" data-panel="history">
                        ${this.renderHistoryTab()}
                    </div>
                </div>
                
                <!-- Footer -->
                <div class="cps-footer">
                    <button class="cps-footer-btn cps-btn-save" id="cps-save">Speichern</button>
                    <button class="cps-footer-btn cps-btn-accept" id="cps-accept-all">Alle akzeptieren</button>
                    <button class="cps-footer-btn cps-btn-reject" id="cps-reject-all">Nur essenzielle Cookies akzeptieren</button>
                </div>
            `;
        }
        
        renderServiceGroupsTab() {
            const categories = [
                {
                    key: 'necessary',
                    name: this.config.texts.necessary || 'Essenziell',
                    desc: this.config.texts.necessaryDesc || 'Essenzielle Services ermöglichen grundlegende Funktionen und sind für das ordnungsgemäße Funktionieren der Website erforderlich.',
                    required: true
                },
                {
                    key: 'functional',
                    name: this.config.texts.functional || 'Funktional',
                    desc: this.config.texts.functionalDesc || 'Funktionale Cookies speichern Ihre Präferenzen wie Sprache und Region.'
                },
                {
                    key: 'analytics',
                    name: this.config.texts.analytics || 'Statistiken',
                    desc: this.config.texts.analyticsDesc || 'Statistik-Cookies helfen uns zu verstehen, wie Besucher mit der Website interagieren.'
                },
                {
                    key: 'marketing',
                    name: 'Externe Medien',
                    desc: 'Inhalte von Videoplattformen und Social-Media-Plattformen werden standardmäßig blockiert. Wenn externe Services akzeptiert werden, ist für den Zugriff auf diese Inhalte keine manuelle Einwilligung mehr erforderlich.'
                }
            ];
            
            let html = `
                <div class="cps-actions-bar">
                    <button class="cps-action-btn" id="cps-select-all">○ Alle auswählen</button>
                    <button class="cps-action-btn" id="cps-deselect-all">○ Alle abwählen</button>
                </div>
            `;
            
            categories.forEach(cat => {
                const services = this.serviceDetails[cat.key] || [];
                const isChecked = this.categorySelections[cat.key];
                
                html += `
                    <div class="cps-item" data-category="${cat.key}">
                        <div class="cps-item-header">
                            <div class="cps-item-checkbox">
                                <input type="checkbox" 
                                       id="cat-${cat.key}" 
                                       data-category="${cat.key}"
                                       ${isChecked ? 'checked' : ''} 
                                       ${cat.required ? 'checked disabled' : ''}>
                            </div>
                            <div class="cps-item-content">
                                <h3 class="cps-item-title">${cat.name}</h3>
                                <p class="cps-item-desc">${cat.desc}</p>
                            </div>
                            <div class="cps-item-actions">
                                <button class="cps-expand-btn" data-expand="cat-${cat.key}">
                                    Informationen anzeigen <span>▼</span>
                                </button>
                            </div>
                        </div>
                        <div class="cps-item-details" id="details-cat-${cat.key}">
                            ${services.length > 0 ? `
                                <div class="cps-details-section">
                                    <div class="cps-details-title">Zugehörige Services (${services.length})</div>
                                    ${services.map(s => `
                                        <div class="cps-details-row">
                                            <span class="cps-details-label">${s.name}</span>
                                            <span class="cps-details-value">${s.description || ''}</span>
                                        </div>
                                    `).join('')}
                                </div>
                            ` : '<p style="font-size: 12px; color: #9ca3af; padding: 8px 0;">Keine Services in dieser Kategorie.</p>'}
                        </div>
                    </div>
                `;
            });
            
            return html;
        }
        
        renderServicesTab() {
            // Flatten all services
            const allServices = [];
            Object.entries(this.serviceDetails).forEach(([category, services]) => {
                services.forEach(s => {
                    allServices.push({ ...s, category });
                });
            });
            
            let html = `
                <div class="cps-search-bar">
                    <input type="text" class="cps-search-input" id="cps-service-search" placeholder="Services suchen...">
                    <span class="cps-search-count">${allServices.length} Services</span>
                </div>
                <div id="cps-services-list">
            `;
            
            if (allServices.length === 0) {
                html += '<p style="padding: 24px; text-align: center; color: #9ca3af;">Keine Services konfiguriert.</p>';
            } else {
                allServices.forEach((service, idx) => {
                    const isEnabled = this.categorySelections[service.category] || false;
                    const isEssential = service.category === 'necessary';
                    
                    html += `
                        <div class="cps-item cps-service-item" data-service="${service.service_key || service.name}" data-category="${service.category}">
                            <div class="cps-item-header">
                                <div class="cps-item-content">
                                    <h3 class="cps-item-title">${service.name}</h3>
                                </div>
                                <div class="cps-item-actions">
                                    <button class="cps-expand-btn" data-expand="svc-${idx}">
                                        Informationen anzeigen <span>▼</span>
                                    </button>
                                    <label class="cps-toggle">
                                        <input type="checkbox" 
                                               data-service-toggle="${service.service_key || service.name}"
                                               data-category="${service.category}"
                                               ${isEnabled || isEssential ? 'checked' : ''} 
                                               ${isEssential ? 'disabled' : ''}>
                                        <span class="cps-toggle-slider"></span>
                                    </label>
                                </div>
                            </div>
                            <div class="cps-item-details" id="details-svc-${idx}">
                                <div class="cps-details-section">
                                    ${service.description ? `
                                        <div class="cps-details-row">
                                            <span class="cps-details-label">Beschreibung</span>
                                            <span class="cps-details-value">${service.description}</span>
                                        </div>
                                    ` : ''}
                                    <div class="cps-details-row">
                                        <span class="cps-details-label">Kategorie</span>
                                        <span class="cps-details-value">${this.getCategoryName(service.category)}</span>
                                    </div>
                                    ${service.provider ? `
                                        <div class="cps-details-row">
                                            <span class="cps-details-label">Anbieter</span>
                                            <span class="cps-details-value">${service.provider}</span>
                                        </div>
                                    ` : ''}
                                    ${service.cookies && service.cookies.length > 0 ? `
                                        <div class="cps-details-row">
                                            <span class="cps-details-label">Cookies</span>
                                            <span class="cps-details-value">${service.cookies.map(c => typeof c === 'string' ? c : c.name).join(', ')}</span>
                                        </div>
                                    ` : ''}
                                </div>
                            </div>
                        </div>
                    `;
                });
            }
            
            html += '</div>';
            return html;
        }
        
        renderProvidersTab() {
            // Group services by provider
            const providers = {};
            Object.entries(this.serviceDetails).forEach(([category, services]) => {
                services.forEach(s => {
                    const providerName = s.provider || 'Unbekannt';
                    if (!providers[providerName]) {
                        providers[providerName] = {
                            name: providerName,
                            description: s.provider_description || '',
                            address: s.provider_address || '',
                            privacy_url: s.provider_privacy_url || s.privacy_url || '',
                            cookie_url: s.provider_cookie_url || '',
                            services: []
                        };
                    }
                    providers[providerName].services.push(s);
                });
            });
            
            const providerList = Object.values(providers);
            
            let html = `
                <div class="cps-search-bar">
                    <input type="text" class="cps-search-input" id="cps-provider-search" placeholder="Provider suchen...">
                    <span class="cps-search-count">${providerList.length} Provider</span>
                </div>
                <div id="cps-providers-list">
            `;
            
            if (providerList.length === 0) {
                html += '<p style="padding: 24px; text-align: center; color: #9ca3af;">Keine Provider konfiguriert.</p>';
            } else {
                providerList.forEach((provider, idx) => {
                    html += `
                        <div class="cps-item cps-provider-item" data-provider="${provider.name}">
                            <div class="cps-item-header">
                                <div class="cps-item-content">
                                    <h3 class="cps-item-title">${provider.name}</h3>
                                    <p class="cps-item-desc">${provider.description || `Anbieter von ${provider.services.length} Service(s)`}</p>
                                </div>
                                <div class="cps-item-actions">
                                    <button class="cps-expand-btn" data-expand="prov-${idx}">
                                        Informationen anzeigen <span>▼</span>
                                    </button>
                                </div>
                            </div>
                            <div class="cps-item-details" id="details-prov-${idx}">
                                <div class="cps-details-section">
                                    <div class="cps-details-title">Provider-Informationen</div>
                                    ${provider.address ? `
                                        <div class="cps-details-row">
                                            <span class="cps-details-label">Adresse</span>
                                            <span class="cps-details-value">${provider.address}</span>
                                        </div>
                                    ` : ''}
                                    ${provider.privacy_url ? `
                                        <div class="cps-details-row">
                                            <span class="cps-details-label">URL der Datenschutzerklärung</span>
                                            <span class="cps-details-value"><a href="${provider.privacy_url}" target="_blank">${provider.privacy_url}</a></span>
                                        </div>
                                    ` : ''}
                                    ${provider.cookie_url ? `
                                        <div class="cps-details-row">
                                            <span class="cps-details-label">Cookie-URL</span>
                                            <span class="cps-details-value"><a href="${provider.cookie_url}" target="_blank">${provider.cookie_url}</a></span>
                                        </div>
                                    ` : ''}
                                    <div class="cps-details-row">
                                        <span class="cps-details-label">Services</span>
                                        <span class="cps-details-value">${provider.services.map(s => s.name).join(', ')}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                });
            }
            
            html += '</div>';
            return html;
        }
        
        renderHistoryTab() {
            // Load consent history from localStorage
            const consentHistory = this.loadConsentHistory();
            const currentConsent = this.consent;
            
            let html = `
                <table class="cps-history-table">
                    <thead>
                        <tr>
                            <th>Datum</th>
                            <th>Einwilligungen</th>
                            <th>Änderungen</th>
                            <th>Version</th>
                        </tr>
                    </thead>
                    <tbody>
            `;
            
            if (currentConsent && currentConsent.timestamp) {
                const services = this.formatConsentServices(currentConsent);
                html += `
                    <tr>
                        <td>${this.formatDate(currentConsent.timestamp)}</td>
                        <td>${services}</td>
                        <td></td>
                        <td>${currentConsent.version || 1}</td>
                    </tr>
                `;
            } else {
                html += `
                    <tr>
                        <td colspan="4" style="text-align: center; color: #9ca3af;">Keine Einwilligung erteilt</td>
                    </tr>
                `;
            }
            
            html += `
                    </tbody>
                </table>
                <div class="cps-uid">
                    UID: ${this.visitorId || 'Nicht verfügbar'}
                </div>
            `;
            
            return html;
        }
        
        getCategoryName(key) {
            const names = {
                necessary: 'Essenziell',
                functional: 'Funktional',
                analytics: 'Statistiken',
                marketing: 'Externe Medien'
            };
            return names[key] || key;
        }
        
        formatConsentServices(consent) {
            const parts = [];
            
            if (consent.necessary !== false) {
                const services = this.serviceDetails.necessary || [];
                if (services.length > 0) {
                    parts.push(`<strong>Essenziell:</strong> ${services.map(s => s.name).join(', ')}`);
                }
            }
            
            if (consent.functional) {
                const services = this.serviceDetails.functional || [];
                if (services.length > 0) {
                    parts.push(`<strong>Funktional:</strong> ${services.map(s => s.name).join(', ')}`);
                }
            }
            
            if (consent.analytics) {
                const services = this.serviceDetails.analytics || [];
                if (services.length > 0) {
                    parts.push(`<strong>Statistiken:</strong> ${services.map(s => s.name).join(', ')}`);
                }
            }
            
            if (consent.marketing) {
                const services = this.serviceDetails.marketing || [];
                if (services.length > 0) {
                    parts.push(`<strong>Externe Medien:</strong> ${services.map(s => s.name).join(', ')}`);
                }
            }
            
            return parts.join('<br>') || 'Nur essenzielle Cookies';
        }
        
        formatDate(dateStr) {
            try {
                const d = new Date(dateStr);
                return d.toLocaleString('de-DE', {
                    year: 'numeric',
                    month: '2-digit',
                    day: '2-digit',
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit'
                });
            } catch (e) {
                return dateStr;
            }
        }
        
        loadConsentHistory() {
            try {
                const history = localStorage.getItem('complyo_consent_history');
                return history ? JSON.parse(history) : [];
            } catch (e) {
                return [];
            }
        }
        
        bindSettingsEvents(modal, backdrop) {
            const { primaryColor, accentColor } = this.config;
            
            // Tab switching
            modal.querySelectorAll('.cps-tab').forEach(tab => {
                tab.addEventListener('click', () => {
                    const tabName = tab.dataset.tab;
                    
                    // Update tabs
                    modal.querySelectorAll('.cps-tab').forEach(t => t.classList.remove('cps-active'));
                    tab.classList.add('cps-active');
                    
                    // Update panels
                    modal.querySelectorAll('.cps-tab-panel').forEach(p => p.classList.remove('cps-active'));
                    modal.querySelector(`[data-panel="${tabName}"]`).classList.add('cps-active');
                });
            });
            
            // Expand/collapse
            modal.querySelectorAll('.cps-expand-btn').forEach(btn => {
                btn.addEventListener('click', () => {
                    const targetId = btn.dataset.expand;
                    const details = modal.querySelector(`#details-${targetId}`);
                    const arrow = btn.querySelector('span');
                    
                    if (details) {
                        details.classList.toggle('cps-expanded');
                        arrow.textContent = details.classList.contains('cps-expanded') ? '▲' : '▼';
                        btn.innerHTML = details.classList.contains('cps-expanded') 
                            ? 'Informationen ausblenden <span>▲</span>'
                            : 'Informationen anzeigen <span>▼</span>';
                    }
                });
            });
            
            // Category checkboxes
            modal.querySelectorAll('.cps-item-checkbox input[type="checkbox"]').forEach(checkbox => {
                checkbox.addEventListener('change', (e) => {
                    if (!e.target.disabled) {
                        const category = e.target.dataset.category;
                        this.categorySelections[category] = e.target.checked;
                        
                        // Update service toggles for this category
                        modal.querySelectorAll(`[data-service-toggle][data-category="${category}"]`).forEach(toggle => {
                            if (!toggle.disabled) {
                                toggle.checked = e.target.checked;
                            }
                        });
                    }
                });
            });
            
            // Service toggles
            modal.querySelectorAll('[data-service-toggle]').forEach(toggle => {
                toggle.addEventListener('change', (e) => {
                    const category = e.target.dataset.category;
                    // Check if all services in category are enabled
                    const categoryToggles = modal.querySelectorAll(`[data-service-toggle][data-category="${category}"]`);
                    const allEnabled = Array.from(categoryToggles).every(t => t.checked || t.disabled);
                    
                    const categoryCheckbox = modal.querySelector(`#cat-${category}`);
                    if (categoryCheckbox && !categoryCheckbox.disabled) {
                        categoryCheckbox.checked = allEnabled;
                        this.categorySelections[category] = allEnabled;
                    }
                });
            });
            
            // Select all / Deselect all
            const selectAllBtn = modal.querySelector('#cps-select-all');
            const deselectAllBtn = modal.querySelector('#cps-deselect-all');
            
            if (selectAllBtn) {
                selectAllBtn.addEventListener('click', () => {
                    modal.querySelectorAll('.cps-item-checkbox input[type="checkbox"]').forEach(cb => {
                        if (!cb.disabled) {
                            cb.checked = true;
                            const category = cb.dataset.category;
                            this.categorySelections[category] = true;
                        }
                    });
                    modal.querySelectorAll('[data-service-toggle]').forEach(toggle => {
                        if (!toggle.disabled) toggle.checked = true;
                    });
                });
            }
            
            if (deselectAllBtn) {
                deselectAllBtn.addEventListener('click', () => {
                    modal.querySelectorAll('.cps-item-checkbox input[type="checkbox"]').forEach(cb => {
                        if (!cb.disabled) {
                            cb.checked = false;
                            const category = cb.dataset.category;
                            this.categorySelections[category] = false;
                        }
                    });
                    modal.querySelectorAll('[data-service-toggle]').forEach(toggle => {
                        if (!toggle.disabled) toggle.checked = false;
                    });
                });
            }
            
            // Search functionality
            const serviceSearch = modal.querySelector('#cps-service-search');
            if (serviceSearch) {
                serviceSearch.addEventListener('input', (e) => {
                    const query = e.target.value.toLowerCase();
                    modal.querySelectorAll('.cps-service-item').forEach(item => {
                        const name = item.querySelector('.cps-item-title').textContent.toLowerCase();
                        item.style.display = name.includes(query) ? '' : 'none';
                    });
                });
            }
            
            const providerSearch = modal.querySelector('#cps-provider-search');
            if (providerSearch) {
                providerSearch.addEventListener('input', (e) => {
                    const query = e.target.value.toLowerCase();
                    modal.querySelectorAll('.cps-provider-item').forEach(item => {
                        const name = item.querySelector('.cps-item-title').textContent.toLowerCase();
                        item.style.display = name.includes(query) ? '' : 'none';
                    });
                });
            }
            
            // Footer buttons
            modal.querySelector('#cps-save').addEventListener('click', () => {
                this.saveCustom(this.categorySelections);
            });
            
            modal.querySelector('#cps-accept-all').addEventListener('click', () => {
                this.acceptAll();
            });
            
            modal.querySelector('#cps-reject-all').addEventListener('click', () => {
                this.rejectAll();
            });
            
            // Close on backdrop click
            backdrop.addEventListener('click', () => this.closeSettings());
        }
        
        // ====================================================================
        // Floating Settings Button (nach Consent)
        // ====================================================================
        
        renderFloatingButton() {
            // Entferne existierenden Button
            const existing = document.getElementById('complyo-cookie-settings-btn');
            if (existing) existing.remove();
            
            const primaryColor = this.config.primaryColor || '#7c3aed';
            
            const button = document.createElement('button');
            button.id = 'complyo-cookie-settings-btn';
            button.setAttribute('aria-label', 'Cookie-Einstellungen ändern');
            button.setAttribute('title', 'Cookie-Einstellungen ändern');
            
            // SVG Cookie Icon (passend zum Accessibility-Button-Style)
            button.innerHTML = `
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="12" cy="12" r="10"/>
                    <circle cx="8" cy="9" r="1" fill="currentColor"/>
                    <circle cx="15" cy="8" r="1" fill="currentColor"/>
                    <circle cx="10" cy="14" r="1" fill="currentColor"/>
                    <circle cx="15" cy="14" r="1" fill="currentColor"/>
                    <circle cx="12" cy="11" r="1" fill="currentColor"/>
                </svg>
            `;
            
            // Styles passend zum Accessibility-Button (rechts)
            Object.assign(button.style, {
                position: 'fixed',
                bottom: '20px',
                left: '20px',
                width: '48px',
                height: '48px',
                borderRadius: '12px',
                background: primaryColor,
                color: 'white',
                border: 'none',
                boxShadow: `0 4px 14px ${primaryColor}50`,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                zIndex: '999997',
                transition: 'all 0.2s ease',
                padding: '0'
            });
            
            // Hover-Effekt
            button.addEventListener('mouseenter', () => {
                button.style.transform = 'translateY(-2px)';
                button.style.boxShadow = `0 6px 20px ${primaryColor}60`;
            });
            button.addEventListener('mouseleave', () => {
                button.style.transform = 'translateY(0)';
                button.style.boxShadow = `0 4px 14px ${primaryColor}50`;
            });
            
            // Click öffnet Einstellungen
            button.addEventListener('click', () => {
                this.openSettings();
            });
            
            document.body.appendChild(button);
            console.log('[Complyo] Cookie-Settings-Button angezeigt');
        }
        
        hideFloatingButton() {
            const button = document.getElementById('complyo-cookie-settings-btn');
            if (button) button.remove();
        }
        
        // ====================================================================
        // Age Verification (Jugendschutz Art. 8 DSGVO)
        // ====================================================================
        
        /**
         * Laenderspezifische Altersgrenzen fuer digitale Einwilligung
         * Basierend auf Art. 8 DSGVO und nationalen Umsetzungen
         */
        getAgeThresholdByCountry() {
            return {
                'DE': 16, // Deutschland
                'AT': 14, // Oesterreich
                'BE': 13, // Belgien
                'BG': 14, // Bulgarien
                'CY': 14, // Zypern
                'CZ': 15, // Tschechien
                'DK': 13, // Daenemark
                'EE': 13, // Estland
                'ES': 14, // Spanien
                'FI': 13, // Finnland
                'FR': 15, // Frankreich
                'GR': 15, // Griechenland
                'HR': 16, // Kroatien
                'HU': 16, // Ungarn
                'IE': 16, // Irland
                'IT': 14, // Italien
                'LT': 14, // Litauen
                'LU': 16, // Luxemburg
                'LV': 13, // Lettland
                'MT': 13, // Malta
                'NL': 16, // Niederlande
                'PL': 16, // Polen
                'PT': 13, // Portugal
                'RO': 16, // Rumaenien
                'SE': 13, // Schweden
                'SI': 15, // Slowenien
                'SK': 16, // Slowakei
                'UK': 13, // Grossbritannien
                'CH': 16, // Schweiz
                'DEFAULT': 16
            };
        }
        
        checkAgeVerification() {
            const verified = localStorage.getItem('complyo_age_verified');
            if (verified) {
                try {
                    const data = JSON.parse(verified);
                    // Pruefe ob Verifikation noch gueltig ist (30 Tage)
                    const daysSince = (Date.now() - new Date(data.timestamp).getTime()) / (1000 * 60 * 60 * 24);
                    if (daysSince < 30 && data.verified === true) {
                        return true;
                    }
                } catch (e) {
                    console.warn('[Complyo] Age verification data invalid');
                }
            }
            return false;
        }
        
        saveAgeVerification(verified, birthYear = null) {
            const data = {
                verified: verified,
                birthYear: birthYear,
                timestamp: new Date().toISOString(),
                minAge: this.config.age_verification_min_age || 16
            };
            localStorage.setItem('complyo_age_verified', JSON.stringify(data));
        }
        
        renderAgeVerificationModal() {
            const { primaryColor, accentColor, bgColor, textColor } = this.config;
            const minAge = this.config.age_verification_min_age || 16;
            
            // Backdrop
            const backdrop = document.createElement('div');
            backdrop.id = 'complyo-age-backdrop';
            Object.assign(backdrop.style, {
                position: 'fixed',
                top: '0', left: '0', right: '0', bottom: '0',
                background: 'rgba(0, 0, 0, 0.7)',
                backdropFilter: 'blur(8px)',
                zIndex: '999999',
                opacity: '0',
                transition: 'opacity 0.3s ease'
            });
            
            // Modal
            const modal = document.createElement('div');
            modal.id = 'complyo-age-modal';
            Object.assign(modal.style, {
                position: 'fixed',
                top: '50%', left: '50%',
                transform: 'translate(-50%, -50%) scale(0.9)',
                background: bgColor || '#ffffff',
                borderRadius: '20px',
                padding: '40px',
                maxWidth: '420px',
                width: '90%',
                textAlign: 'center',
                boxShadow: '0 25px 80px rgba(0,0,0,0.3)',
                zIndex: '1000000',
                opacity: '0',
                transition: 'all 0.3s ease',
                fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
            });
            
            const currentYear = new Date().getFullYear();
            const maxYear = currentYear - minAge;
            
            modal.innerHTML = \`
                <div style="font-size: 48px; margin-bottom: 20px;">🔒</div>
                <h2 style="margin: 0 0 16px 0; font-size: 24px; font-weight: 700; color: \${textColor || '#1f2937'};">
                    Altersverifikation
                </h2>
                <p style="margin: 0 0 24px 0; font-size: 15px; color: \${textColor || '#6b7280'}; line-height: 1.6;">
                    Um fortzufahren, bestaetigen Sie bitte, dass Sie mindestens <strong>\${minAge} Jahre</strong> alt sind.
                    <br><small style="opacity: 0.7;">(Gemaess Art. 8 DSGVO)</small>
                </p>
                
                <div style="margin-bottom: 24px;">
                    <label style="display: block; font-size: 14px; font-weight: 500; color: \${textColor || '#374151'}; margin-bottom: 8px;">
                        Geburtsjahr eingeben:
                    </label>
                    <input 
                        type="number" 
                        id="complyo-birth-year" 
                        min="1920" 
                        max="\${currentYear}" 
                        placeholder="\${maxYear}"
                        style="width: 100%; padding: 14px; font-size: 18px; border: 2px solid #e5e7eb; border-radius: 12px; text-align: center; outline: none; transition: border-color 0.2s;"
                        onfocus="this.style.borderColor='\${primaryColor}'"
                        onblur="this.style.borderColor='#e5e7eb'"
                    >
                </div>
                
                <button 
                    id="complyo-age-confirm" 
                    style="width: 100%; padding: 16px; background: \${primaryColor}; color: white; border: none; border-radius: 12px; font-size: 16px; font-weight: 600; cursor: pointer; transition: all 0.2s; margin-bottom: 12px;"
                    onmouseover="this.style.background='\${accentColor}'; this.style.transform='translateY(-2px)';"
                    onmouseout="this.style.background='\${primaryColor}'; this.style.transform='translateY(0)';"
                >
                    Bestaetigen
                </button>
                
                <p style="margin: 0; font-size: 12px; color: #9ca3af;">
                    Diese Angabe wird lokal gespeichert und nicht an Server uebertragen.
                </p>
            \`;
            
            document.body.appendChild(backdrop);
            document.body.appendChild(modal);
            
            // Animate in
            requestAnimationFrame(() => {
                backdrop.style.opacity = '1';
                modal.style.opacity = '1';
                modal.style.transform = 'translate(-50%, -50%) scale(1)';
            });
            
            // Confirm button
            const confirmBtn = modal.querySelector('#complyo-age-confirm');
            const birthYearInput = modal.querySelector('#complyo-birth-year');
            
            confirmBtn.addEventListener('click', () => {
                const birthYear = parseInt(birthYearInput.value);
                const age = currentYear - birthYear;
                
                if (!birthYear || birthYear < 1920 || birthYear > currentYear) {
                    birthYearInput.style.borderColor = '#ef4444';
                    return;
                }
                
                if (age >= minAge) {
                    // Alter OK
                    this.saveAgeVerification(true, birthYear);
                    backdrop.style.opacity = '0';
                    modal.style.opacity = '0';
                    modal.style.transform = 'translate(-50%, -50%) scale(0.9)';
                    setTimeout(() => {
                        backdrop.remove();
                        modal.remove();
                        this.continueOnDOMReady();
                    }, 300);
                } else {
                    // Zu jung
                    modal.innerHTML = \`
                        <div style="font-size: 48px; margin-bottom: 20px;">⚠️</div>
                        <h2 style="margin: 0 0 16px 0; font-size: 22px; font-weight: 700; color: #ef4444;">
                            Zugriff nicht moeglich
                        </h2>
                        <p style="margin: 0; font-size: 15px; color: \${textColor || '#6b7280'}; line-height: 1.6;">
                            Diese Website erfordert ein Mindestalter von <strong>\${minAge} Jahren</strong>.
                            <br><br>
                            Bitte wende dich an einen Erziehungsberechtigten.
                        </p>
                    \`;
                    this.saveAgeVerification(false, birthYear);
                }
            });
            
            // Enter key
            birthYearInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') confirmBtn.click();
            });
        }
        
        // ====================================================================
        // Public API
        // ====================================================================
        
        getConsent() {
            return this.consent;
        }
        
        hasConsent(category) {
            return this.consent && this.consent[category] === true;
        }
        
        revokeConsent() {
            localStorage.removeItem(CONSENT_STORAGE_KEY);
            localStorage.removeItem(CONSENT_DATE_KEY);
            this.consent = null;
            this.hideFloatingButton();
            location.reload();
        }
        
        showBanner() {
            this.consent = null;
            localStorage.removeItem(CONSENT_STORAGE_KEY);
            this.hideFloatingButton();
            this.render();
        }
    }
    
    // ========================================================================
    // Auto-Initialize
    // ========================================================================
    
    // Auto-initialize if data-site-id is present
    const initBanner = () => {
        console.log('[Complyo] Initialisiere Cookie-Banner...');
        
        // ✅ DEBUG: Prüfe ob Script-Tag gefunden wurde
        const script = document.currentScript || 
                      document.querySelector('script[data-site-id]') ||
                      document.querySelector('script[src*="cookie-compliance.js"]');
        
        if (script) {
            const siteId = script.getAttribute('data-site-id') || 
                          script.getAttribute('data-complyo-site-id');
            console.log('[Complyo] Script-Tag gefunden, site-id:', siteId);
        } else {
            console.warn('[Complyo] Script-Tag nicht gefunden!');
        }
        
        if (!window.complyoCookieBanner) {
            console.log('[Complyo] Erstelle neue Banner-Instanz...');
            window.complyoCookieBanner = new ComplyoCookieBanner();
        } else {
            console.log('[Complyo] Banner-Instanz bereits vorhanden');
        }
        
        // Register global API (window.complyo)
        registerGlobalAPI(window.complyoCookieBanner);
        
        console.log('[Complyo] Banner-Initialisierung abgeschlossen');
    };
    
    // Register global window.complyo API
    const registerGlobalAPI = (bannerInstance) => {
        window.complyo = window.complyo || {};
        
        // Core API
        window.complyo.openPreferences = () => bannerInstance.openSettings();
        window.complyo.getConsent = () => bannerInstance.getConsent();
        window.complyo.hasConsent = (category) => bannerInstance.hasConsent(category);
        window.complyo.revokeConsent = () => bannerInstance.revokeConsent();
        window.complyo.showBanner = () => bannerInstance.showBanner();
        
        // Extended API
        window.complyo.acceptAll = () => bannerInstance.acceptAll();
        window.complyo.rejectAll = () => bannerInstance.rejectAll();
        window.complyo.saveCustom = (selections) => bannerInstance.saveCustom(selections);
        
        // Info
        window.complyo.version = VERSION;
        window.complyo.siteId = bannerInstance.siteId;
        
        // Event subscription
        window.complyo.onConsent = (callback) => {
            window.addEventListener('complyoConsent', (e) => callback(e.detail));
        };
        
        console.log('[Complyo] Global API registered: window.complyo');
    };
    
    // Wait for DOM or init immediately
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initBanner);
    } else {
        initBanner();
    }
    
    // Export for manual initialization
    window.ComplyoCookieBanner = ComplyoCookieBanner;
    
    console.log(`[Complyo] Cookie Banner v${VERSION} loaded`);
    
})();

