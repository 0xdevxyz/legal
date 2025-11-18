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
            apiUrl: 'https://api.complyo.tech',
            blockedScripts: [],
            blockedIframes: [],
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
            
            // Load configuration from API
            this.loadConfiguration();
            
            // Block scripts before they execute
            this.blockScriptsEarly();
            
            // Listen for DOM changes
            this.observeDOM();
            
            // Load existing consent
            this.loadConsent();
            
            this.state.initialized = true;
            console.log('[Complyo] ✅ Cookie Blocker initialized');
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
                }
                
                return element;
            };
            
            // Observer for dynamically added scripts
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', () => {
                    this.scanAndBlockScripts();
                });
            } else {
                this.scanAndBlockScripts();
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
    
    // Initialize immediately
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            ComplyoCookieBlocker.init();
        });
    } else {
        ComplyoCookieBlocker.init();
    }
    
    // Export to global scope
    window.ComplyoCookieBlocker = ComplyoCookieBlocker;
    
})();

