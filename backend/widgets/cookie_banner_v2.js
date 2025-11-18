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
        
        // Services
        services: [],
        
        // Texts (default German) - synchronisiert mit Dashboard
        texts: {
            title: '🍪 Wir respektieren Ihre Privatsphäre',
            description: 'Wir verwenden Cookies und ähnliche Technologien, um Inhalte zu personalisieren und die Nutzung unserer Website zu analysieren. Einige davon sind essentiell, während andere uns helfen, die Website zu verbessern.',
            description2: '',
            ageNotice: '',
            acceptAll: 'Alle akzeptieren',
            continueWithout: 'Nur notwendige',
            settingsLink: 'Individuelle Einstellungen',
            acceptSelected: 'Auswahl speichern',
            settings: 'Einstellungen',
            privacyPolicy: 'Datenschutzerklärung',
            cookiePolicy: 'Über Cookies',
            imprint: 'Impressum',
            necessary: 'Notwendig',
            functional: 'Präferenzen',
            analytics: 'Statistiken',
            marketing: 'Marketing',
            necessaryDesc: 'Notwendige Cookies helfen dabei, eine Webseite nutzbar zu machen, indem sie Grundfunktionen wie Seitennavigation und Zugriff auf sichere Bereiche der Webseite ermöglichen. Die Webseite kann ohne diese Cookies nicht richtig funktionieren.',
            functionalDesc: 'Präferenz-Cookies ermöglichen einer Webseite sich an Informationen zu erinnern, die die Art beeinflussen, wie sich eine Webseite verhält oder aussieht, wie z.B. Ihre bevorzugte Sprache oder die Region in der Sie sich befinden.',
            analyticsDesc: 'Statistik-Cookies helfen Webseiten-Besitzern zu verstehen, wie Besucher mit Webseiten interagieren, indem Informationen anonym gesammelt und gemeldet werden.',
            marketingDesc: 'Marketing-Cookies werden verwendet, um Besuchern auf Webseiten zu folgen. Die Absicht ist, Anzeigen zu zeigen, die relevant und ansprechend für den einzelnen Benutzer sind und daher wertvoller für Publisher und werbetreibende Drittparteien sind.',
            serviceCount: 'Service',
            learnMore: 'Erfahren Sie mehr über diesen Anbieter',
            expand: 'Details anzeigen',
            collapse: 'Details ausblenden'
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
        
        async init() {
            // Check Do Not Track
            if (this.config.respectDNT && this.isDNTEnabled()) {
                console.log('[Complyo] Do Not Track detected. Banner not shown.');
                return;
            }
            
            // Load configuration from server if site_id exists
            if (this.siteId && this.siteId !== 'demo-site') {
                await this.loadServerConfig();
            }
            
            // Wait for DOM
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', () => this.onDOMReady());
            } else {
                this.onDOMReady();
            }
        }
        
        async loadServerConfig() {
            try {
                const response = await fetch(`${API_BASE}/api/cookie-compliance/config/${this.siteId}`);
                if (response.ok) {
                    const data = await response.json();
                    if (data.success && data.data) {
                        this.applyServerConfig(data.data);
                    }
                }
                
                // Load detailed service information
                await this.loadServiceDetails();
            } catch (error) {
                console.warn('[Complyo] Could not load server config:', error);
            }
        }
        
        async loadServiceDetails() {
            try {
                // Get all available services
                const servicesResponse = await fetch(`${API_BASE}/api/cookie-compliance/services`);
                if (servicesResponse.ok) {
                    const servicesData = await servicesResponse.json();
                    if (servicesData.success && servicesData.services) {
                        // Group services by category
                        servicesData.services.forEach(service => {
                            if (!this.serviceDetails[service.category]) {
                                this.serviceDetails[service.category] = [];
                            }
                            this.serviceDetails[service.category].push(service);
                        });
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
            
            // Merge texts (use browser language)
            const browserLang = navigator.language.split('-')[0];
            if (serverConfig.texts && serverConfig.texts[browserLang]) {
                this.config.texts = { ...this.config.texts, ...serverConfig.texts[browserLang] };
            } else if (serverConfig.texts && serverConfig.texts['de']) {
                this.config.texts = { ...this.config.texts, ...serverConfig.texts['de'] };
            }
        }
        
        isDNTEnabled() {
            return navigator.doNotTrack === '1' || 
                   window.doNotTrack === '1' || 
                   navigator.msDoNotTrack === '1';
        }
        
        onDOMReady() {
            if (this.consent) {
                // Consent already given - apply and trigger content unblocking
                console.log('[Complyo] Consent already given:', this.consent);
                this.applyConsent(this.consent);
                this.triggerConsentEvent(this.consent);
            } else {
                // Show banner
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
                        banner_shown: true
                    })
                });
            } catch (error) {
                console.warn('[Complyo] Error logging consent:', error);
            }
        }
        
        applyConsent(consent) {
            // Store consent in window for other scripts to access
            window.complyoConsent = consent;
            
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
                    services: consent.services || []
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
            
            this.saveConsent(consent);
            this.closeSettings();
            this.hideBanner();
        }
        
        hideBanner() {
            const banner = document.querySelector('.complyo-cookie-banner');
            if (banner) {
                banner.classList.remove('complyo-show');
                setTimeout(() => banner.remove(), 300);
            }
        }
        
        closeSettings() {
            const modal = document.querySelector('.complyo-settings-modal');
            const backdrop = document.querySelector('#complyo-settings-backdrop');
            
            if (modal) {
                modal.classList.remove('complyo-show');
                setTimeout(() => modal.remove(), 300);
            }
            
            if (backdrop) {
                backdrop.classList.remove('complyo-show');
                setTimeout(() => backdrop.remove(), 300);
            }
            
            this.settingsOpen = false;
        }
        
        renderSettingsModal() {
            // Create backdrop
            const backdrop = document.createElement('div');
            backdrop.className = 'complyo-backdrop';
            backdrop.id = 'complyo-settings-backdrop';
            document.body.appendChild(backdrop);
            
            // Create modal
            const modal = document.createElement('div');
            modal.className = 'complyo-settings-modal';
            modal.setAttribute('role', 'dialog');
            modal.setAttribute('aria-labelledby', 'complyo-settings-title');
            modal.setAttribute('aria-modal', 'true');
            
            // Build categories HTML with services
            let categoriesHTML = '';
            
            // Helper to build category section
            const buildCategory = (categoryKey, categoryName, description, disabled = false) => {
                const services = this.serviceDetails[categoryKey] || [];
                const serviceCount = services.length;
                
                // Filter services to only show those configured for this site
                const configuredServices = this.config.services || [];
                const visibleServices = services.filter(s => configuredServices.includes(s.service_key));
                
                return `
                    <div class="complyo-category" data-category="${categoryKey}">
                        <div class="complyo-category-header">
                            <div class="complyo-category-info">
                                <span class="complyo-category-name">${categoryName}</span>
                                ${serviceCount > 0 ? `<span class="complyo-service-count">${serviceCount}</span>` : ''}
                            </div>
                            <label class="complyo-toggle">
                                <input type="checkbox" 
                                       id="toggle-${categoryKey}" 
                                       ${disabled ? 'checked disabled' : ''}
                                       data-category="${categoryKey}">
                                <span class="complyo-toggle-slider"></span>
                            </label>
                        </div>
                        <p class="complyo-category-desc">${description}</p>
                        
                        ${visibleServices.length > 0 ? `
                            <div class="complyo-services-list">
                                ${visibleServices.map(service => `
                                    <div class="complyo-service-item">
                                        <div class="complyo-service-header">
                                            <div class="complyo-service-info">
                                                <span class="complyo-service-name">${service.name}</span>
                                                ${service.cookies && service.cookies.length > 0 ? 
                                                    `<span class="complyo-cookie-count">${service.cookies.length}</span>` : ''}
                                            </div>
                                            <label class="complyo-toggle complyo-toggle-small">
                                                <input type="checkbox" 
                                                       data-service="${service.service_key}"
                                                       data-category="${categoryKey}"
                                                       class="service-toggle">
                                                <span class="complyo-toggle-slider"></span>
                                            </label>
                                        </div>
                                        ${service.description ? `
                                            <p class="complyo-service-desc">${service.description}</p>
                                        ` : ''}
                                        ${service.privacy_policy_url ? `
                                            <a href="${service.privacy_policy_url}" 
                                               target="_blank" 
                                               rel="noopener" 
                                               class="complyo-service-link">
                                                ${this.config.texts.learnMore} ↗
                                            </a>
                                        ` : ''}
                                    </div>
                                `).join('')}
                            </div>
                        ` : ''}
                    </div>
                `;
            };
            
            // Build all categories
            categoriesHTML += buildCategory('necessary', this.config.texts.necessary, this.config.texts.necessaryDesc, true);
            categoriesHTML += buildCategory('functional', this.config.texts.functional, this.config.texts.functionalDesc);
            categoriesHTML += buildCategory('analytics', this.config.texts.analytics, this.config.texts.analyticsDesc);
            categoriesHTML += buildCategory('marketing', this.config.texts.marketing, this.config.texts.marketingDesc);
            
            modal.innerHTML = `
                <div class="complyo-settings-header">
                    <h3 id="complyo-settings-title" class="complyo-settings-title">${this.config.texts.settings}</h3>
                    <button class="complyo-close-btn" aria-label="Schließen">×</button>
                </div>
                
                <div class="complyo-categories">
                    ${categoriesHTML}
                </div>
                
                <div class="complyo-actions">
                    <button 
                        id="complyo-save-settings" 
                        class="complyo-btn complyo-btn-primary complyo-btn-${this.config.buttonStyle}"
                    >
                        ${this.config.texts.acceptSelected}
                    </button>
                </div>
            `;
            
            document.body.appendChild(modal);
            
            // Animate in
            requestAnimationFrame(() => {
                backdrop.classList.add('complyo-show');
                modal.classList.add('complyo-show');
            });
            
            // Bind events
            modal.querySelector('.complyo-close-btn').addEventListener('click', () => this.closeSettings());
            backdrop.addEventListener('click', () => this.closeSettings());
            
            // Category toggle - toggle all services in category
            modal.querySelectorAll('input[data-category]').forEach(toggle => {
                if (!toggle.disabled) {
                    toggle.addEventListener('change', (e) => {
                        const category = e.target.getAttribute('data-category');
                        const checked = e.target.checked;
                        
                        // Toggle all services in this category
                        modal.querySelectorAll(`input[data-service][data-category="${category}"]`).forEach(serviceToggle => {
                            serviceToggle.checked = checked;
                        });
                    });
                }
            });
            
            // Service toggle - update category toggle if all services are toggled
            modal.querySelectorAll('input[data-service]').forEach(toggle => {
                toggle.addEventListener('change', (e) => {
                    const category = e.target.getAttribute('data-category');
                    const categoryToggle = modal.querySelector(`#toggle-${category}`);
                    
                    if (categoryToggle) {
                        // Check if all services in category are checked
                        const allServices = modal.querySelectorAll(`input[data-service][data-category="${category}"]`);
                        const checkedServices = Array.from(allServices).filter(s => s.checked);
                        
                        categoryToggle.checked = checkedServices.length > 0;
                    }
                });
            });
            
            // Save settings
            modal.querySelector('#complyo-save-settings').addEventListener('click', () => {
                // Collect category selections
                const selections = {
                    functional: modal.querySelector('#toggle-functional')?.checked || false,
                    analytics: modal.querySelector('#toggle-analytics')?.checked || false,
                    marketing: modal.querySelector('#toggle-marketing')?.checked || false,
                    services: []
                };
                
                // Collect individual service selections
                modal.querySelectorAll('input[data-service]:checked').forEach(toggle => {
                    selections.services.push(toggle.getAttribute('data-service'));
                });
                
                this.saveCustom(selections);
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
            location.reload();
        }
        
        showBanner() {
            this.consent = null;
            localStorage.removeItem(CONSENT_STORAGE_KEY);
            this.render();
        }
    }
    
    // ========================================================================
    // Auto-Initialize
    // ========================================================================
    
    // Auto-initialize if data-site-id is present
    const initBanner = () => {
        if (!window.complyoCookieBanner) {
            window.complyoCookieBanner = new ComplyoCookieBanner();
        }
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

