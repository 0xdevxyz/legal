/**
 * ============================================================================
 * Complyo Opt-out Center v1.0
 * ============================================================================
 * Eigenstaendiges Cookie-Einstellungen Widget
 * 
 * Kann jederzeit ueber window.complyo.openPreferences() geoeffnet werden.
 * 
 * Features:
 * - Floating Button (optional)
 * - Vollstaendiges Einstellungs-Modal
 * - Service-Level Kontrolle
 * - Cookie-Details
 * - Consent-Widerruf
 * 
 * Integration:
 * <script src="https://api.complyo.tech/widgets/optout-center.js" data-site-id="YOUR_SITE_ID"></script>
 * 
 * API:
 * window.complyo.openPreferences()  - Oeffnet Einstellungen
 * window.complyo.getConsent()       - Gibt aktuellen Consent zurueck
 * window.complyo.revokeConsent()    - Widerruft Consent
 * window.complyo.hasConsent(cat)    - Prueft Consent fuer Kategorie
 * 
 * © 2025 Complyo - All rights reserved
 * ============================================================================
 */

(function() {
    'use strict';
    
    const VERSION = '1.0.0';
    const API_BASE = 'https://api.complyo.tech';
    const CONSENT_STORAGE_KEY = 'complyo_cookie_consent';
    
    // ========================================================================
    // Configuration
    // ========================================================================
    
    const DEFAULT_CONFIG = {
        showFloatingButton: true,
        floatingButtonPosition: 'bottom-left', // bottom-left, bottom-right, top-left, top-right
        floatingButtonText: '🍪',
        floatingButtonLabel: 'Cookie-Einstellungen',
        primaryColor: '#7c3aed',
        accentColor: '#9333ea',
        textColor: '#333333',
        bgColor: '#ffffff',
        buttonStyle: 'rounded',
        texts: {
            title: 'Cookie-Einstellungen',
            description: 'Hier koennen Sie Ihre Cookie-Praeferenzen anpassen oder Ihre Einwilligung widerrufen.',
            necessary: 'Notwendig',
            functional: 'Praefezenzen',
            analytics: 'Statistiken',
            marketing: 'Marketing',
            necessaryDesc: 'Notwendige Cookies ermöglichen Grundfunktionen und sind für den Betrieb der Website erforderlich.',
            functionalDesc: 'Praefezenzen-Cookies ermöglichen die Speicherung von Benutzereinstellungen.',
            analyticsDesc: 'Statistik-Cookies helfen uns zu verstehen, wie Besucher die Website nutzen.',
            marketingDesc: 'Marketing-Cookies werden verwendet, um Besuchern relevante Werbung zu zeigen.',
            save: 'Einstellungen speichern',
            revokeAll: 'Alle widerrufen',
            close: 'Schliessen',
            alwaysOn: 'Immer aktiv',
            lastUpdated: 'Zuletzt aktualisiert',
            privacyPolicy: 'Datenschutzerklaerung',
            cookiePolicy: 'Cookie-Richtlinie',
        }
    };
    
    // ========================================================================
    // ComplyoOptoutCenter Class
    // ========================================================================
    
    class ComplyoOptoutCenter {
        constructor(config = {}) {
            this.siteId = this.getSiteIdFromScript();
            this.config = { ...DEFAULT_CONFIG, ...config };
            this.consent = this.loadConsent();
            this.modalOpen = false;
            this.serviceDetails = {};
            
            this.init();
        }
        
        // ====================================================================
        // Initialization
        // ====================================================================
        
        getSiteIdFromScript() {
            const script = document.currentScript || 
                          document.querySelector('script[data-site-id]') ||
                          document.querySelector('script[src*="optout-center.js"]');
            
            if (script) {
                return script.getAttribute('data-site-id') || 
                       new URL(script.src).searchParams.get('site_id') ||
                       'demo-site';
            }
            return 'demo-site';
        }
        
        async init() {
            // Load configuration from server
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
                        // Merge colors from banner config
                        this.config.primaryColor = data.data.primary_color || this.config.primaryColor;
                        this.config.accentColor = data.data.accent_color || this.config.accentColor;
                        this.config.textColor = data.data.text_color || this.config.textColor;
                        this.config.bgColor = data.data.bg_color || this.config.bgColor;
                    }
                }
                
                // Load service details
                const servicesResponse = await fetch(`${API_BASE}/api/cookie-compliance/services`);
                if (servicesResponse.ok) {
                    const servicesData = await servicesResponse.json();
                    if (servicesData.success && servicesData.services) {
                        servicesData.services.forEach(service => {
                            if (!this.serviceDetails[service.category]) {
                                this.serviceDetails[service.category] = [];
                            }
                            this.serviceDetails[service.category].push(service);
                        });
                    }
                }
            } catch (error) {
                console.warn('[Complyo Optout Center] Could not load config:', error);
            }
        }
        
        onDOMReady() {
            // Inject styles
            this.injectStyles();
            
            // Render floating button if enabled
            if (this.config.showFloatingButton) {
                this.renderFloatingButton();
            }
            
            // Register global API
            this.registerGlobalAPI();
        }
        
        // ====================================================================
        // Consent Management
        // ====================================================================
        
        loadConsent() {
            try {
                const stored = localStorage.getItem(CONSENT_STORAGE_KEY);
                return stored ? JSON.parse(stored) : null;
            } catch (error) {
                return null;
            }
        }
        
        saveConsent(consent) {
            localStorage.setItem(CONSENT_STORAGE_KEY, JSON.stringify(consent));
            localStorage.setItem('complyo_consent_date', new Date().toISOString());
            this.consent = consent;
            
            // Log to server
            this.logConsentToServer(consent);
            
            // Trigger event
            this.triggerConsentEvent(consent);
        }
        
        async logConsentToServer(consent) {
            try {
                await fetch(`${API_BASE}/api/cookie-compliance/consent`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        site_id: this.siteId,
                        visitor_id: localStorage.getItem('complyo_visitor_id') || 'anonymous',
                        consent_categories: {
                            necessary: true,
                            functional: consent.functional || false,
                            analytics: consent.analytics || false,
                            marketing: consent.marketing || false
                        },
                        services_accepted: consent.services || [],
                        language: navigator.language.split('-')[0],
                        banner_shown: false // Updated via settings
                    })
                });
            } catch (error) {
                console.warn('[Complyo] Error logging consent:', error);
            }
        }
        
        triggerConsentEvent(consent) {
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
                    source: 'optout_center'
                }
            });
            window.dispatchEvent(event);
            document.dispatchEvent(event);
        }
        
        // ====================================================================
        // Rendering
        // ====================================================================
        
        injectStyles() {
            if (document.getElementById('complyo-optout-styles')) {
                return;
            }
            
            const style = document.createElement('style');
            style.id = 'complyo-optout-styles';
            style.textContent = this.getStyles();
            document.head.appendChild(style);
        }
        
        getStyles() {
            const { primaryColor, accentColor, textColor, bgColor } = this.config;
            const positions = {
                'bottom-left': 'bottom: 20px; left: 20px;',
                'bottom-right': 'bottom: 20px; right: 20px;',
                'top-left': 'top: 20px; left: 20px;',
                'top-right': 'top: 20px; right: 20px;',
            };
            const position = positions[this.config.floatingButtonPosition] || positions['bottom-left'];
            
            return `
                /* Complyo Optout Center Styles */
                
                /* Floating Button */
                .complyo-floating-btn {
                    position: fixed;
                    ${position}
                    z-index: 999990;
                    background: ${primaryColor};
                    color: white;
                    border: none;
                    border-radius: 50px;
                    padding: 12px 20px;
                    font-size: 14px;
                    font-weight: 600;
                    cursor: pointer;
                    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
                    transition: all 0.3s ease;
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                }
                
                .complyo-floating-btn:hover {
                    background: ${accentColor};
                    transform: translateY(-2px);
                    box-shadow: 0 6px 24px rgba(0, 0, 0, 0.2);
                }
                
                .complyo-floating-btn-icon {
                    font-size: 20px;
                }
                
                .complyo-floating-btn-text {
                    display: none;
                }
                
                .complyo-floating-btn:hover .complyo-floating-btn-text {
                    display: inline;
                }
                
                /* Modal Backdrop */
                .complyo-optout-backdrop {
                    position: fixed;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: rgba(0, 0, 0, 0.6);
                    backdrop-filter: blur(4px);
                    z-index: 999998;
                    opacity: 0;
                    transition: opacity 0.3s ease;
                }
                
                .complyo-optout-backdrop.complyo-show {
                    opacity: 1;
                }
                
                /* Modal */
                .complyo-optout-modal {
                    position: fixed;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%) scale(0.95);
                    background: ${bgColor};
                    color: ${textColor};
                    border-radius: 16px;
                    padding: 32px;
                    max-width: 600px;
                    width: 90%;
                    max-height: 85vh;
                    overflow-y: auto;
                    z-index: 999999;
                    opacity: 0;
                    transition: all 0.3s ease;
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.25);
                }
                
                .complyo-optout-modal.complyo-show {
                    opacity: 1;
                    transform: translate(-50%, -50%) scale(1);
                }
                
                .complyo-optout-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 20px;
                    padding-bottom: 16px;
                    border-bottom: 1px solid rgba(0, 0, 0, 0.1);
                }
                
                .complyo-optout-title {
                    font-size: 22px;
                    font-weight: 700;
                    margin: 0;
                }
                
                .complyo-optout-close {
                    background: none;
                    border: none;
                    font-size: 28px;
                    cursor: pointer;
                    color: ${textColor};
                    opacity: 0.6;
                    padding: 0;
                    line-height: 1;
                }
                
                .complyo-optout-close:hover {
                    opacity: 1;
                }
                
                .complyo-optout-description {
                    font-size: 14px;
                    color: ${textColor};
                    opacity: 0.8;
                    margin-bottom: 24px;
                    line-height: 1.6;
                }
                
                /* Consent Status */
                .complyo-consent-status {
                    background: linear-gradient(135deg, ${primaryColor}15 0%, ${accentColor}15 100%);
                    border-radius: 12px;
                    padding: 16px;
                    margin-bottom: 24px;
                }
                
                .complyo-consent-status-title {
                    font-weight: 600;
                    margin-bottom: 8px;
                }
                
                .complyo-consent-status-date {
                    font-size: 13px;
                    opacity: 0.7;
                }
                
                /* Categories */
                .complyo-optout-category {
                    background: rgba(0, 0, 0, 0.02);
                    border: 1px solid rgba(0, 0, 0, 0.06);
                    border-radius: 12px;
                    padding: 16px;
                    margin-bottom: 12px;
                }
                
                .complyo-optout-category-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 8px;
                }
                
                .complyo-optout-category-name {
                    font-weight: 600;
                    font-size: 15px;
                }
                
                .complyo-optout-category-desc {
                    font-size: 13px;
                    opacity: 0.7;
                    line-height: 1.5;
                }
                
                .complyo-optout-always-on {
                    font-size: 12px;
                    color: ${primaryColor};
                    font-weight: 500;
                }
                
                /* Toggle */
                .complyo-optout-toggle {
                    position: relative;
                    display: inline-block;
                    width: 48px;
                    height: 24px;
                }
                
                .complyo-optout-toggle input {
                    opacity: 0;
                    width: 0;
                    height: 0;
                }
                
                .complyo-optout-toggle-slider {
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
                
                .complyo-optout-toggle-slider:before {
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
                
                .complyo-optout-toggle input:checked + .complyo-optout-toggle-slider {
                    background-color: ${primaryColor};
                }
                
                .complyo-optout-toggle input:checked + .complyo-optout-toggle-slider:before {
                    transform: translateX(24px);
                }
                
                .complyo-optout-toggle input:disabled + .complyo-optout-toggle-slider {
                    opacity: 0.5;
                    cursor: not-allowed;
                }
                
                /* Actions */
                .complyo-optout-actions {
                    display: flex;
                    gap: 12px;
                    margin-top: 24px;
                    padding-top: 20px;
                    border-top: 1px solid rgba(0, 0, 0, 0.08);
                }
                
                .complyo-optout-btn {
                    flex: 1;
                    padding: 14px 20px;
                    border: none;
                    font-size: 14px;
                    font-weight: 600;
                    cursor: pointer;
                    border-radius: 10px;
                    transition: all 0.2s ease;
                }
                
                .complyo-optout-btn-primary {
                    background: ${primaryColor};
                    color: white;
                }
                
                .complyo-optout-btn-primary:hover {
                    background: ${accentColor};
                    transform: translateY(-1px);
                }
                
                .complyo-optout-btn-secondary {
                    background: transparent;
                    color: ${textColor};
                    border: 1px solid rgba(0, 0, 0, 0.15);
                }
                
                .complyo-optout-btn-secondary:hover {
                    background: rgba(0, 0, 0, 0.05);
                }
                
                .complyo-optout-btn-danger {
                    background: #ef4444;
                    color: white;
                }
                
                .complyo-optout-btn-danger:hover {
                    background: #dc2626;
                }
                
                /* Footer */
                .complyo-optout-footer {
                    margin-top: 20px;
                    text-align: center;
                    font-size: 12px;
                    opacity: 0.6;
                }
                
                .complyo-optout-footer a {
                    color: ${primaryColor};
                    text-decoration: none;
                    margin: 0 8px;
                }
                
                .complyo-optout-footer a:hover {
                    text-decoration: underline;
                }
                
                /* Responsive */
                @media (max-width: 600px) {
                    .complyo-optout-modal {
                        width: 95%;
                        padding: 24px;
                    }
                    
                    .complyo-optout-actions {
                        flex-direction: column;
                    }
                    
                    .complyo-floating-btn {
                        padding: 12px;
                    }
                    
                    .complyo-floating-btn-text {
                        display: none !important;
                    }
                }
            `;
        }
        
        renderFloatingButton() {
            if (document.getElementById('complyo-floating-btn')) {
                return;
            }
            
            const btn = document.createElement('button');
            btn.id = 'complyo-floating-btn';
            btn.className = 'complyo-floating-btn';
            btn.setAttribute('aria-label', this.config.floatingButtonLabel);
            btn.innerHTML = `
                <span class="complyo-floating-btn-icon">${this.config.floatingButtonText}</span>
                <span class="complyo-floating-btn-text">${this.config.floatingButtonLabel}</span>
            `;
            
            btn.addEventListener('click', () => this.openPreferences());
            
            document.body.appendChild(btn);
        }
        
        openPreferences() {
            if (this.modalOpen) return;
            this.modalOpen = true;
            
            // Create backdrop
            const backdrop = document.createElement('div');
            backdrop.id = 'complyo-optout-backdrop';
            backdrop.className = 'complyo-optout-backdrop';
            document.body.appendChild(backdrop);
            
            // Create modal
            const modal = document.createElement('div');
            modal.id = 'complyo-optout-modal';
            modal.className = 'complyo-optout-modal';
            modal.setAttribute('role', 'dialog');
            modal.setAttribute('aria-modal', 'true');
            modal.setAttribute('aria-labelledby', 'complyo-optout-title');
            
            // Current consent state
            const consent = this.consent || {};
            const consentDate = localStorage.getItem('complyo_consent_date');
            
            modal.innerHTML = `
                <div class="complyo-optout-header">
                    <h2 id="complyo-optout-title" class="complyo-optout-title">${this.config.texts.title}</h2>
                    <button class="complyo-optout-close" aria-label="${this.config.texts.close}">&times;</button>
                </div>
                
                <p class="complyo-optout-description">${this.config.texts.description}</p>
                
                ${consentDate ? `
                    <div class="complyo-consent-status">
                        <div class="complyo-consent-status-title">Aktuelle Einstellungen</div>
                        <div class="complyo-consent-status-date">
                            ${this.config.texts.lastUpdated}: ${new Date(consentDate).toLocaleDateString('de-DE', { 
                                day: '2-digit', 
                                month: '2-digit', 
                                year: 'numeric',
                                hour: '2-digit',
                                minute: '2-digit'
                            })}
                        </div>
                    </div>
                ` : ''}
                
                <div class="complyo-optout-categories">
                    <!-- Necessary -->
                    <div class="complyo-optout-category">
                        <div class="complyo-optout-category-header">
                            <span class="complyo-optout-category-name">${this.config.texts.necessary}</span>
                            <span class="complyo-optout-always-on">${this.config.texts.alwaysOn}</span>
                        </div>
                        <p class="complyo-optout-category-desc">${this.config.texts.necessaryDesc}</p>
                    </div>
                    
                    <!-- Functional -->
                    <div class="complyo-optout-category">
                        <div class="complyo-optout-category-header">
                            <span class="complyo-optout-category-name">${this.config.texts.functional}</span>
                            <label class="complyo-optout-toggle">
                                <input type="checkbox" id="toggle-functional" ${consent.functional ? 'checked' : ''}>
                                <span class="complyo-optout-toggle-slider"></span>
                            </label>
                        </div>
                        <p class="complyo-optout-category-desc">${this.config.texts.functionalDesc}</p>
                    </div>
                    
                    <!-- Analytics -->
                    <div class="complyo-optout-category">
                        <div class="complyo-optout-category-header">
                            <span class="complyo-optout-category-name">${this.config.texts.analytics}</span>
                            <label class="complyo-optout-toggle">
                                <input type="checkbox" id="toggle-analytics" ${consent.analytics ? 'checked' : ''}>
                                <span class="complyo-optout-toggle-slider"></span>
                            </label>
                        </div>
                        <p class="complyo-optout-category-desc">${this.config.texts.analyticsDesc}</p>
                    </div>
                    
                    <!-- Marketing -->
                    <div class="complyo-optout-category">
                        <div class="complyo-optout-category-header">
                            <span class="complyo-optout-category-name">${this.config.texts.marketing}</span>
                            <label class="complyo-optout-toggle">
                                <input type="checkbox" id="toggle-marketing" ${consent.marketing ? 'checked' : ''}>
                                <span class="complyo-optout-toggle-slider"></span>
                            </label>
                        </div>
                        <p class="complyo-optout-category-desc">${this.config.texts.marketingDesc}</p>
                    </div>
                </div>
                
                <div class="complyo-optout-actions">
                    <button id="complyo-save-btn" class="complyo-optout-btn complyo-optout-btn-primary">
                        ${this.config.texts.save}
                    </button>
                    <button id="complyo-revoke-btn" class="complyo-optout-btn complyo-optout-btn-danger">
                        ${this.config.texts.revokeAll}
                    </button>
                </div>
                
                <div class="complyo-optout-footer">
                    <a href="/datenschutz" target="_blank">${this.config.texts.privacyPolicy}</a>
                    <span>•</span>
                    <a href="/cookie-richtlinie" target="_blank">${this.config.texts.cookiePolicy}</a>
                </div>
            `;
            
            document.body.appendChild(modal);
            
            // Animate in
            requestAnimationFrame(() => {
                backdrop.classList.add('complyo-show');
                modal.classList.add('complyo-show');
            });
            
            // Bind events
            modal.querySelector('.complyo-optout-close').addEventListener('click', () => this.closePreferences());
            backdrop.addEventListener('click', () => this.closePreferences());
            
            modal.querySelector('#complyo-save-btn').addEventListener('click', () => {
                const newConsent = {
                    necessary: true,
                    functional: modal.querySelector('#toggle-functional').checked,
                    analytics: modal.querySelector('#toggle-analytics').checked,
                    marketing: modal.querySelector('#toggle-marketing').checked,
                    services: [],
                    timestamp: new Date().toISOString()
                };
                this.saveConsent(newConsent);
                this.closePreferences();
            });
            
            modal.querySelector('#complyo-revoke-btn').addEventListener('click', () => {
                this.revokeConsent();
            });
            
            // Focus trap
            modal.querySelector('.complyo-optout-close').focus();
        }
        
        closePreferences() {
            const modal = document.getElementById('complyo-optout-modal');
            const backdrop = document.getElementById('complyo-optout-backdrop');
            
            if (modal) {
                modal.classList.remove('complyo-show');
                setTimeout(() => modal.remove(), 300);
            }
            
            if (backdrop) {
                backdrop.classList.remove('complyo-show');
                setTimeout(() => backdrop.remove(), 300);
            }
            
            this.modalOpen = false;
        }
        
        // ====================================================================
        // Public API
        // ====================================================================
        
        getConsent() {
            return this.consent;
        }
        
        hasConsent(category) {
            if (category === 'necessary') return true;
            return this.consent && this.consent[category] === true;
        }
        
        revokeConsent() {
            localStorage.removeItem(CONSENT_STORAGE_KEY);
            localStorage.removeItem('complyo_consent_date');
            this.consent = null;
            this.closePreferences();
            
            // Trigger revoke event
            const event = new CustomEvent('complyoConsentRevoked', { detail: {} });
            window.dispatchEvent(event);
            
            // Reload to re-show banner
            location.reload();
        }
        
        registerGlobalAPI() {
            // Register global window.complyo API
            window.complyo = window.complyo || {};
            
            window.complyo.openPreferences = () => this.openPreferences();
            window.complyo.closePreferences = () => this.closePreferences();
            window.complyo.getConsent = () => this.getConsent();
            window.complyo.hasConsent = (category) => this.hasConsent(category);
            window.complyo.revokeConsent = () => this.revokeConsent();
            window.complyo.version = VERSION;
            
            console.log('[Complyo] Global API registered: window.complyo');
        }
    }
    
    // ========================================================================
    // Auto-Initialize
    // ========================================================================
    
    const initOptoutCenter = () => {
        if (!window.complyoOptoutCenter) {
            window.complyoOptoutCenter = new ComplyoOptoutCenter();
        }
    };
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initOptoutCenter);
    } else {
        initOptoutCenter();
    }
    
    window.ComplyoOptoutCenter = ComplyoOptoutCenter;
    
    console.log(`[Complyo] Optout Center v${VERSION} loaded`);
    
})();

