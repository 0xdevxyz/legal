/**
 * Complyo Cookie Blocker & Auto-Blocking System
 * Version: 2.0.0
 * 
 * Automatically blocks scripts, iframes, and cookies until user consent
 * DSGVO/GDPR compliant cookie management
 */

(function() {
    'use strict';
    
    const ComplyoCookieBlocker = {
        // Configuration
        config: {
            siteId: 'SITE_ID_PLACEHOLDER',
            apiUrl: 'https://api.complyo.de',
            blockedScripts: [],
            blockedIframes: [],
            blockedStyles: [],
            cookiesToDelete: [],
            localStorageKeys: [],
            serviceConfig: {}
        },
        
        // State
        state: {
            consent: null,
            initialized: false,
            blockedElements: [],
            pendingScripts: []
        },
        
        /**
         * Initialize the blocker
         */
        init: function() {
            if (this.state.initialized) return;
            
            console.log('[Complyo] 🛡️ Cookie Blocker initializing...');
            
            // Statische Block-Patterns SOFORT bauen, damit der erste (synchrone)
            // Scan bereits greift — die API-Konfiguration verfeinert sie danach.
            this.buildBlockingPatterns([]);

            // Load configuration from API (async, verfeinert Patterns)
            this.loadConfiguration();

            // Block scripts before they execute
            this.blockScriptsEarly();
            
            // Listen for DOM changes
            this.observeDOM();
            
            // Load existing consent
            this.loadConsent();

            // Auf Consent aus dem Banner reagieren. Der Banner feuert
            // 'complyoConsent' (window + document), ruft aber NICHT direkt
            // updateConsent() auf. Ohne diesen Listener blieben die im <head>
            // synchron blockierten Font-/CSS-<link>s nach "Akzeptieren" mit
            // media="not all" hängen → die Schrift lud erst nach Seiten-Reload.
            const onConsent = (e) => this.applyConsentFromEvent(e);
            window.addEventListener('complyoConsent', onConsent);
            document.addEventListener('complyoConsent', onConsent);

            this.state.initialized = true;
            console.log('[Complyo] ✅ Cookie Blocker initialized');
        },

        /**
         * Consent-Event des Banners verarbeiten: Kategorien in das interne
         * Consent-Format überführen und blockierte Elemente (insb. Google-Fonts-
         * Stylesheets) SOFORT wieder freigeben – ohne Page-Reload.
         */
        applyConsentFromEvent: function(e) {
            const detail = (e && e.detail) || {};
            const cats   = detail.categories || {};

            const accepted = !!(cats.functional || cats.analytics || cats.marketing);
            const consent = {
                accepted: accepted,
                consent_categories: {
                    necessary:  true,
                    functional: cats.functional === true,
                    analytics:  cats.analytics  === true,
                    marketing:  cats.marketing  === true
                }
            };

            this.state.consent = consent;

            // Freigeben, was jetzt erlaubt ist (Fonts/CSS = funktional). Bei reiner
            // Ablehnung Tracking-Cookies entfernen.
            this.unblockElements();
            if (!accepted) {
                this.deleteCookies();
            }

            console.log('[Complyo] Consent via Banner-Event übernommen:', consent);
        },
        
        /**
         * Load configuration from API
         */
        loadConfiguration: async function() {
            try {
                const response = await fetch(`${this.config.apiUrl}/api/cookie-compliance/config/${this.config.siteId}`);
                if (response.ok) {
                    const data = await response.json();
                    if (data.success && data.config) {
                        this.config.serviceConfig = data.config;
                        this.buildBlockingPatterns(data.config.services || []);
                    }
                }
            } catch (error) {
                console.error('[Complyo] Failed to load configuration:', error);
            }
        },
        
        /**
         * Build blocking patterns from service configuration
         */
        buildBlockingPatterns: function(services) {
            // In production, this would fetch detailed service info from API
            // For now, we use common patterns
            
            this.config.blockedScripts = [
                // Analytics
                /googletagmanager\.com\/gtag/,
                /google-analytics\.com/,
                /googletagmanager\.com\/gtm/,
                /static\.hotjar\.com/,
                /matomo\.js/,
                /plausible\.io/,
                
                // Marketing
                /connect\.facebook\.net/,
                /facebook\.com\/tr/,
                /googleadservices\.com/,
                /doubleclick\.net/,
                /snap\.licdn\.com/,
                /analytics\.tiktok\.com/,
                /platform\.twitter\.com/,
                
                // Chat
                /widget\.intercom\.io/,
                /static\.zdassets\.com/,
                /embed\.tawk\.to/,
                /client\.crisp\.chat/
            ];
            
            this.config.blockedIframes = [
                /youtube\.com\/embed/,
                /player\.vimeo\.com/,
                /instagram\.com\/embed/,
                /google\.com\/maps\/embed/,
                /twitter\.com\/widgets/,
                /platform\.twitter\.com/
            ];

            // Externe Font-/CSS-Hosts: laden via <link rel="stylesheet">,
            // <link as="font">/Preload oder @import und uebertragen die IP des
            // Besuchers VOR Consent an Dritte (z.B. Google Fonts -> LG Muenchen
            // 3 O 17493/20). Werden bis zur Einwilligung neutralisiert; das
            // Layout faellt solange auf System-/Fallback-Fonts zurueck.
            this.config.blockedStyles = [
                /fonts\.googleapis\.com/,      // Google Fonts (CSS)
                /fonts\.gstatic\.com/,         // Google Fonts (Font-Dateien)
                /use\.typekit\.net/,           // Adobe Fonts
                /p\.typekit\.net/,
                /use\.fontawesome\.com/,       // Font Awesome CDN
                /kit\.fontawesome\.com/,
                /fast\.fonts\.(net|com)/,      // Monotype
                /cloud\.typography\.com/,      // Hoefler&Co
                /fonts\.bunny\.net/            // Bunny Fonts (extern)
            ];
            
            this.config.cookiesToDelete = [
                // Analytics
                '_ga', '_gid', '_gat', '_gat_gtag_', '_ga_',
                '_pk_id', '_pk_ses',
                '_hjid', '_hjSessionUser_', '_hjSession_',
                
                // Marketing  
                '_fbp', '_fbc', 'fr',
                '_gcl_au', '_gcl_aw', '_gcl_dc',
                'li_fat_id', 'lidc',
                '_ttp',
                'personalization_id',
                
                // Others
                'VISITOR_INFO1_LIVE', 'YSC'
            ];
        },
        
        /**
         * Block scripts early (before DOMContentLoaded)
         */
        blockScriptsEarly: function() {
            const self = this;
            
            // Intercept script creation
            const originalCreateElement = document.createElement;
            document.createElement = function(tagName) {
                const element = originalCreateElement.call(document, tagName);
                
                if (tagName.toLowerCase() === 'script') {
                    const originalSetAttribute = element.setAttribute;
                    element.setAttribute = function(name, value) {
                        if (name === 'src' && self.shouldBlockScript(value)) {
                            console.log('[Complyo] 🚫 Blocked script:', value);

                            // Change type to prevent execution
                            originalSetAttribute.call(this, 'type', 'text/plain');
                            originalSetAttribute.call(this, 'data-complyo-src', value);
                            originalSetAttribute.call(this, 'data-complyo-blocked', 'true');

                            self.state.blockedElements.push(this);
                            return;
                        }
                        originalSetAttribute.call(this, name, value);
                    };
                    // el.src = … (so injizieren GA/GTM/Meta real) ebenfalls abfangen
                    const srcDesc = Object.getOwnPropertyDescriptor(HTMLScriptElement.prototype, 'src');
                    if (srcDesc && srcDesc.set && srcDesc.get) {
                        Object.defineProperty(element, 'src', {
                            configurable: true,
                            enumerable: true,
                            get: function() { return srcDesc.get.call(this); },
                            set: function(value) {
                                if (self.shouldBlockScript(value)) {
                                    console.log('[Complyo] 🚫 Blocked script:', value);
                                    originalSetAttribute.call(this, 'type', 'text/plain');
                                    originalSetAttribute.call(this, 'data-complyo-src', value);
                                    originalSetAttribute.call(this, 'data-complyo-blocked', 'true');
                                    self.state.blockedElements.push(this);
                                    return;
                                }
                                srcDesc.set.call(this, value);
                            }
                        });
                    }
                }

                // Dynamisch erzeugte <link rel="stylesheet"> / <link as="font">:
                // href abfangen, bevor der Browser den Request startet.
                if (tagName.toLowerCase() === 'link') {
                    const originalSetAttribute = element.setAttribute;
                    element.setAttribute = function(name, value) {
                        if (name === 'href' && self.shouldBlockStylesheet(value)) {
                            console.log('[Complyo] 🚫 Blocked stylesheet/font:', value);
                            originalSetAttribute.call(this, 'data-complyo-href', value);
                            originalSetAttribute.call(this, 'data-complyo-blocked', 'true');
                            originalSetAttribute.call(this, 'media', 'not all');
                            self.state.blockedElements.push(this);
                            return;
                        }
                        originalSetAttribute.call(this, name, value);
                    };
                    const hrefDesc = Object.getOwnPropertyDescriptor(HTMLLinkElement.prototype, 'href');
                    if (hrefDesc && hrefDesc.set) {
                        Object.defineProperty(element, 'href', {
                            configurable: true,
                            get: function() { return hrefDesc.get.call(this); },
                            set: function(value) {
                                if (self.shouldBlockStylesheet(value)) {
                                    console.log('[Complyo] 🚫 Blocked stylesheet/font:', value);
                                    element.setAttribute('href', value); // laeuft in Hook oben
                                    return;
                                }
                                hrefDesc.set.call(this, value);
                            }
                        });
                    }
                }

                return element;
            };
            
            // Sofort vorhandene (bis hier geparste) Scripts & Styles neutralisieren …
            this.scanAndBlockScripts();
            this.scanAndBlockStyles();
            // … und erneut nach vollstaendigem Parsen des restlichen DOM.
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', () => {
                    this.scanAndBlockScripts();
                    this.scanAndBlockStyles();
                });
            }
        },
        
        /**
         * Scan and block existing scripts
         */
        scanAndBlockScripts: function() {
            const scripts = document.querySelectorAll('script[src]');
            
            scripts.forEach(script => {
                const src = script.getAttribute('src');
                if (src && this.shouldBlockScript(src)) {
                    if (script.getAttribute('data-complyo-blocked') !== 'true') {
                        console.log('[Complyo] 🚫 Blocking existing script:', src);
                        
                        script.type = 'text/plain';
                        script.setAttribute('data-complyo-src', src);
                        script.setAttribute('data-complyo-blocked', 'true');
                        script.removeAttribute('src');
                        
                        this.state.blockedElements.push(script);
                    }
                }
            });
        },
        
        /**
         * Check if script should be blocked
         */
        shouldBlockScript: function(src) {
            if (!src) return false;
            
            // Don't block if consent given
            if (this.state.consent && this.hasConsentForScript(src)) {
                return false;
            }
            
            // Check against patterns
            return this.config.blockedScripts.some(pattern => pattern.test(src));
        },
        
        /**
         * Check if script should be blocked based on iframe src
         */
        shouldBlockIframe: function(src) {
            if (!src) return false;
            
            // Don't block if consent given
            if (this.state.consent && this.hasConsentForIframe(src)) {
                return false;
            }
            
            return this.config.blockedIframes.some(pattern => pattern.test(src));
        },

        /**
         * Soll diese URL (Stylesheet/Font) blockiert werden?
         */
        shouldBlockStylesheet: function(href) {
            if (!href) return false;
            if (this.state.consent && this.hasConsentForStyle()) {
                return false;
            }
            return this.config.blockedStyles.some(pattern => pattern.test(href));
        },

        /**
         * Externe Fonts/CSS zaehlen als "funktional" — erst bei funktionaler
         * Einwilligung (oder "Alle akzeptieren") wieder freigeben.
         */
        hasConsentForStyle: function() {
            const c = this.state.consent;
            if (!c) return false;
            const cat = c.consent_categories || {};
            return cat.functional === true || cat.all === true;
        },

        /**
         * Vorhandene <link>/<style>-Elemente scannen und externe Font-/CSS-Hosts
         * neutralisieren: <link rel="stylesheet">, <link as="font">/Preload und
         * inline @import-Regeln.
         */
        scanAndBlockStyles: function() {
            // 1) <link>-Elemente (stylesheet, preload/as=font, prefetch, dns-prefetch)
            document.querySelectorAll('link[href]').forEach(link => {
                if (link.getAttribute('data-complyo-blocked') === 'true') return;
                const href = link.getAttribute('href');
                const rel  = (link.getAttribute('rel') || '').toLowerCase();
                const as   = (link.getAttribute('as')  || '').toLowerCase();
                const isStyleish = rel.includes('stylesheet') || as === 'font' ||
                                   rel === 'preload' || rel === 'prefetch' ||
                                   rel === 'preconnect' || rel === 'dns-prefetch';
                if (isStyleish && this.shouldBlockStylesheet(href)) {
                    console.log('[Complyo] 🚫 Blocking stylesheet/font link:', href);
                    // href entfernen stoppt den Request (sofern noch nicht fertig);
                    // media="not all" verhindert das Anwenden bereits geladener CSS.
                    link.setAttribute('data-complyo-href', href);
                    link.setAttribute('data-complyo-rel', link.getAttribute('rel') || '');
                    link.setAttribute('data-complyo-blocked', 'true');
                    link.setAttribute('media', 'not all');
                    link.removeAttribute('href');
                    this.state.blockedElements.push(link);
                }
            });

            // 2) Inline <style> mit @import auf externe Hosts
            document.querySelectorAll('style:not([data-complyo-blocked])').forEach(style => {
                const css = style.textContent || '';
                if (!/@import/i.test(css)) return;
                const importRe = /@import\s+(?:url\(\s*)?['"]?([^'")\s;]+)['"]?\s*\)?[^;]*;/gi;
                let touched = false;
                const newCss = css.replace(importRe, (full, url) => {
                    if (this.shouldBlockStylesheet(url)) {
                        touched = true;
                        return '/* complyo-blocked: ' + full.replace(/\*\//g, '* /') + ' */';
                    }
                    return full;
                });
                if (touched) {
                    console.log('[Complyo] 🚫 Neutralizing @import in <style>');
                    style.setAttribute('data-complyo-css', css);
                    style.setAttribute('data-complyo-blocked', 'true');
                    style.textContent = newCss;
                    this.state.blockedElements.push(style);
                }
            });
        },

        /**
         * Check if user has consent for this script
         */
        hasConsentForScript: function(src) {
            if (!this.state.consent) return false;
            
            const categories = this.state.consent.consent_categories;
            
            // Analytics
            if (categories.analytics && /google-analytics|googletagmanager|hotjar|matomo/.test(src)) {
                return true;
            }
            
            // Marketing
            if (categories.marketing && /facebook|doubleclick|linkedin|tiktok|twitter/.test(src)) {
                return true;
            }
            
            // Functional
            if (categories.functional && /intercom|zendesk|tawk|crisp/.test(src)) {
                return true;
            }
            
            return false;
        },
        
        /**
         * Check if user has consent for this iframe
         */
        hasConsentForIframe: function(src) {
            if (!this.state.consent) return false;
            
            const categories = this.state.consent.consent_categories;
            
            // Functional content
            if (categories.functional && /youtube|vimeo|maps\.google|openstreetmap/.test(src)) {
                return true;
            }
            
            // Marketing content
            if (categories.marketing && /instagram|twitter|facebook/.test(src)) {
                return true;
            }
            
            return false;
        },
        
        /**
         * Observe DOM for dynamically added elements
         */
        observeDOM: function() {
            const self = this;
            
            const observer = new MutationObserver(mutations => {
                mutations.forEach(mutation => {
                    mutation.addedNodes.forEach(node => {
                        if (node.nodeType === 1) { // Element node
                            // Check scripts
                            if (node.tagName === 'SCRIPT') {
                                const src = node.getAttribute('src');
                                if (src && self.shouldBlockScript(src)) {
                                    console.log('[Complyo] 🚫 Blocking dynamically added script:', src);
                                    node.type = 'text/plain';
                                    node.setAttribute('data-complyo-src', src);
                                    node.setAttribute('data-complyo-blocked', 'true');
                                    node.removeAttribute('src');
                                    self.state.blockedElements.push(node);
                                }
                            }
                            
                            // Check iframes
                            if (node.tagName === 'IFRAME') {
                                const src = node.getAttribute('src');
                                if (src && self.shouldBlockIframe(src)) {
                                    console.log('[Complyo] 🚫 Blocking iframe:', src);
                                    self.replaceIframeWithPlaceholder(node);
                                }
                            }

                            // Externe Font-/CSS-Links und @import-Styles
                            if (node.tagName === 'LINK' || node.tagName === 'STYLE') {
                                self.scanAndBlockStyles();
                            }

                            // Check child elements
                            if (node.querySelectorAll) {
                                node.querySelectorAll('script[src], iframe[src]').forEach(child => {
                                    const src = child.getAttribute('src');
                                    if (child.tagName === 'SCRIPT' && self.shouldBlockScript(src)) {
                                        child.type = 'text/plain';
                                        child.setAttribute('data-complyo-src', src);
                                        child.setAttribute('data-complyo-blocked', 'true');
                                        child.removeAttribute('src');
                                        self.state.blockedElements.push(child);
                                    } else if (child.tagName === 'IFRAME' && self.shouldBlockIframe(src)) {
                                        self.replaceIframeWithPlaceholder(child);
                                    }
                                });
                                if (node.querySelector('link[href], style')) {
                                    self.scanAndBlockStyles();
                                }
                            }
                        }
                    });
                });
            });
            
            observer.observe(document.documentElement, {
                childList: true,
                subtree: true
            });
        },
        
        /**
         * Replace iframe with consent placeholder
         */
        replaceIframeWithPlaceholder: function(iframe) {
            const src = iframe.getAttribute('src');
            const width = iframe.getAttribute('width') || '100%';
            const height = iframe.getAttribute('height') || '400px';
            
            const placeholder = document.createElement('div');
            placeholder.className = 'complyo-iframe-placeholder';
            placeholder.style.cssText = `
                width: ${width};
                height: ${height};
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                display: flex;
                align-items: center;
                justify-content: center;
                flex-direction: column;
                color: white;
                padding: 20px;
                text-align: center;
                border-radius: 8px;
                cursor: pointer;
            `;
            
            placeholder.innerHTML = `
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect>
                    <line x1="8" y1="21" x2="16" y2="21"></line>
                    <line x1="12" y1="17" x2="12" y2="21"></line>
                </svg>
                <h3 style="margin: 16px 0 8px 0; font-size: 18px; font-weight: 600;">Externe Inhalte blockiert</h3>
                <p style="margin: 0 0 16px 0; font-size: 14px; opacity: 0.9;">Zum Anzeigen dieser Inhalte benötigen wir Ihre Zustimmung.</p>
                <button style="
                    background: white;
                    color: #667eea;
                    border: none;
                    padding: 10px 24px;
                    border-radius: 6px;
                    font-weight: 600;
                    cursor: pointer;
                    font-size: 14px;
                ">Inhalte entsperren</button>
            `;
            
            placeholder.setAttribute('data-complyo-iframe-src', src);
            placeholder.setAttribute('data-complyo-blocked', 'true');
            
            placeholder.addEventListener('click', () => {
                window.ComplyoBanner?.showBanner();
            });
            
            iframe.parentNode.replaceChild(placeholder, iframe);
            this.state.blockedElements.push(placeholder);
        },
        
        /**
         * Unblock all blocked elements
         */
        unblockElements: function() {
            console.log('[Complyo] ✅ Unblocking elements...');
            
            this.state.blockedElements.forEach(element => {
                if (element.tagName === 'SCRIPT') {
                    const originalSrc = element.getAttribute('data-complyo-src');
                    if (originalSrc && this.hasConsentForScript(originalSrc)) {
                        console.log('[Complyo] ✅ Unblocking script:', originalSrc);
                        element.type = 'text/javascript';
                        element.src = originalSrc;
                        element.removeAttribute('data-complyo-blocked');
                    }
                } else if (element.className === 'complyo-iframe-placeholder') {
                    const originalSrc = element.getAttribute('data-complyo-iframe-src');
                    if (originalSrc && this.hasConsentForIframe(originalSrc)) {
                        console.log('[Complyo] ✅ Unblocking iframe:', originalSrc);
                        const iframe = document.createElement('iframe');
                        iframe.src = originalSrc;
                        iframe.width = element.style.width;
                        iframe.height = element.style.height;
                        element.parentNode.replaceChild(iframe, element);
                    }
                } else if (element.tagName === 'LINK') {
                    const originalHref = element.getAttribute('data-complyo-href');
                    if (originalHref && this.hasConsentForStyle()) {
                        console.log('[Complyo] ✅ Unblocking stylesheet/font:', originalHref);
                        const originalRel = element.getAttribute('data-complyo-rel');
                        element.removeAttribute('media');
                        if (originalRel) element.setAttribute('rel', originalRel);
                        element.setAttribute('href', originalHref);
                        element.removeAttribute('data-complyo-blocked');
                    }
                } else if (element.tagName === 'STYLE') {
                    const originalCss = element.getAttribute('data-complyo-css');
                    if (originalCss && this.hasConsentForStyle()) {
                        console.log('[Complyo] ✅ Unblocking @import styles');
                        element.textContent = originalCss;
                        element.removeAttribute('data-complyo-blocked');
                    }
                }
            });
        },
        
        /**
         * Delete cookies based on consent
         */
        deleteCookies: function() {
            console.log('[Complyo] 🗑️ Deleting cookies...');
            
            this.config.cookiesToDelete.forEach(cookieName => {
                // Delete cookie
                document.cookie = `${cookieName}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`;
                document.cookie = `${cookieName}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; domain=${window.location.hostname};`;
                
                // Also try with leading dot
                const domain = window.location.hostname.split('.').slice(-2).join('.');
                document.cookie = `${cookieName}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/; domain=.${domain};`;
            });
            
            // Delete localStorage items
            this.config.localStorageKeys.forEach(key => {
                try {
                    localStorage.removeItem(key);
                } catch (e) {}
            });
        },
        
        /**
         * Load existing consent
         */
        loadConsent: function() {
            try {
                const consentCookie = this.getCookie('complyo_consent');
                if (consentCookie) {
                    this.state.consent = JSON.parse(decodeURIComponent(consentCookie));
                    console.log('[Complyo] Loaded existing consent:', this.state.consent);
                    
                    // Unblock elements if consent given
                    if (this.state.consent.consent_categories) {
                        this.unblockElements();
                    }
                }
            } catch (error) {
                console.error('[Complyo] Failed to load consent:', error);
            }
        },
        
        /**
         * Update consent
         */
        updateConsent: function(consent) {
            this.state.consent = consent;
            
            // Store consent cookie
            const expires = new Date();
            expires.setFullYear(expires.getFullYear() + 1);
            document.cookie = `complyo_consent=${encodeURIComponent(JSON.stringify(consent))}; expires=${expires.toUTCString()}; path=/; SameSite=Lax`;
            
            // Unblock or delete based on consent
            if (consent.accepted) {
                this.unblockElements();
            } else {
                this.deleteCookies();
            }
            
            console.log('[Complyo] Consent updated:', consent);
        },
        
        /**
         * Get cookie value
         */
        getCookie: function(name) {
            const value = `; ${document.cookie}`;
            const parts = value.split(`; ${name}=`);
            if (parts.length === 2) return parts.pop().split(';').shift();
            return null;
        }
    };
    
    // SOFORT initialisieren (Script laeuft synchron im <head>): nur so stehen
    // createElement-Hook und MutationObserver, bevor der Parser nachfolgende
    // <link>/<script>-Tags erreicht. Ein Warten auf DOMContentLoaded waere zu
    // spaet — statische Font-/Tracking-Ressourcen waeren dann laengst geladen.
    // init() startet selbst einen erneuten Scan auf DOMContentLoaded.
    ComplyoCookieBlocker.init();
    
    // Export to global scope
    window.ComplyoCookieBlocker = ComplyoCookieBlocker;
    
})();

