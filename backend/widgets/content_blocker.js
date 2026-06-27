/**
 * ============================================================================
 * Complyo Content Blocker v2.0
 * ============================================================================
 * Blockiert Scripts, Iframes, Images und andere Inhalte bis Cookie-Consent gegeben
 * 
 * Features:
 * - Script Blocking (type="text/plain" → type="text/javascript")
 * - Iframe Blocking (YouTube, Vimeo, Google Maps, etc.)
 * - Image Blocking (Tracking Pixels)
 * - Visuelle Placeholder mit Click-to-Load
 * - URL-basiertes Blocking
 * - Data-Attribute-basiert (data-complyo-consent="analytics")
 * - Lazy Loading nach Consent
 * 
 * © 2025 Complyo - All rights reserved
 * ============================================================================
 */

(function() {
    'use strict';
    
    // ========================================================================
    // Configuration
    // ========================================================================
    
    const VERSION = '2.0.0';
    const API_BASE = 'https://api.complyo.de';

    // Blocked domains by category.
    // Built-in fallback list; at runtime this is enriched with the domains of
    // ALL services from the Complyo service catalogue (see loadServiceDomains)
    // so that every configurable tracker is blocked before consent — not just
    // the hard-coded ones.
    const BLOCKED_DOMAINS = {
        analytics: [
            'google-analytics.com',
            'googletagmanager.com',
            'analytics.tiktok.com',
            'matomo.org',
            'matomo.js',
            'piwik.js',
            'hotjar.com',
            'clarity.ms',
            'bat.bing.com',
            'scorecardresearch.com',
            'quantserve.com',
            'statcounter.com',
            'mixpanel.com',
            'segment.io',
            'segment.com',
            'amplitude.com',
            'heap.io',
            'fullstory.com',
            'logrocket.com',
            'mouseflow.com',
            'smartlook.com'
        ],
        marketing: [
            'facebook.com',
            'facebook.net',
            'connect.facebook.net',
            'doubleclick.net',
            'googleadservices.com',
            'snap.licdn.com',
            'analytics.tiktok.com',
            'youtube.com',
            'youtube-nocookie.com',
            'vimeo.com',
            'instagram.com',
            'twitter.com',
            'x.com',
            'platform.twitter.com',
            'linkedin.com',
            'ads.linkedin.com',
            'pinterest.com',
            'ct.pinterest.com',
            'reddit.com',
            'redd.it',
            'criteo.com',
            'criteo.net',
            'adform.net',
            'appnexus.com',
            'outbrain.com',
            'taboola.com',
            'zemanta.com',
            'mediaplex.com',
            'tradedoubler.com',
            'awin1.com',
            'shareasale.com',
            'impact.com',
            'tiktok.com'
        ],
        functional: [
            'google.com/maps',
            'maps.googleapis.com',
            'intercom.io',
            'widget.intercom.io',
            'zdassets.com',
            'zendesk.com',
            'fonts.googleapis.com',
            'freshchat.com',
            'freshdesk.com',
            'tawk.to',
            'livechatinc.com',
            'crisp.chat',
            'drift.com',
            'hubspot.com',
            'hs-scripts.com',
            'hs-analytics.net'
        ]
    };

    // Domains von Services, die Daten in unsicheren Drittländern verarbeiten
    // (Art. 49 Abs. 1 lit. a DSGVO). Wird zur Laufzeit aus dem Service-Katalog
    // befüllt (requires_third_country_consent === true). Solche Services werden
    // NUR freigeschaltet, wenn zusätzlich zur Kategorie die gesonderte
    // Drittland-Einwilligung vorliegt.
    const THIRD_COUNTRY_DOMAINS = [];

    // Service-specific patterns for visual placeholders
    const VIDEO_SERVICES = {
        youtube: {
            pattern: /youtube\.com\/embed\/([a-zA-Z0-9_-]+)/,
            name: 'YouTube',
            category: 'marketing',
            icon: '▶️'
        },
        vimeo: {
            pattern: /player\.vimeo\.com\/video\/(\d+)/,
            name: 'Vimeo',
            category: 'marketing',
            icon: '▶️'
        }
    };
    
    const MAP_SERVICES = {
        google_maps: {
            pattern: /google\.com\/maps\/embed/,
            name: 'Google Maps',
            category: 'functional',
            icon: '🗺️'
        }
    };

    // Bekannte Tracking-Cookies, die bei Widerruf/Ablehnung gelöscht werden
    // (DSGVO Art. 7 Abs. 3 – Widerruf so einfach wie Erteilung). Präfix-Match.
    const COOKIES_TO_DELETE = [
        '_ga', '_gid', '_gat', '_gat_gtag_', '_ga_', '__utm',
        '_pk_id', '_pk_ses', '_dc_gtm_',
        '_hjid', '_hjSessionUser_', '_hjSession_', '_hjAbsoluteSessionInProgress',
        '_fbp', '_fbc', 'fr',
        '_gcl_au', '_gcl_aw', '_gcl_dc',
        'li_fat_id', 'lidc', 'bcookie', 'bscookie', 'UserMatchHistory',
        '_ttp', '_tt_enable_cookie',
        '_scid', '_sctr',
        'personalization_id', 'guest_id',
        'IDE', 'DSID', 'test_cookie', 'NID',
        '_clck', '_clsk',
        'VISITOR_INFO1_LIVE', 'YSC', 'PREF'
    ];
    
    // ========================================================================
    // ComplyoContentBlocker Class
    // ========================================================================
    
    class ComplyoContentBlocker {
        constructor() {
            this.blockedElements = new Map();
            this.consent = null;
            this.observer = null;
            
            this.init();
        }
        
        // ====================================================================
        // Initialization
        // ====================================================================
        
        init() {
            // Auf der Complyo-App SELBST nicht blockieren: das Dashboard lädt
            // Firebase/Stripe/Google u.a. sowie Next.js-Navigations-Chunks
            // dynamisch. Würde der createElement-Hook die blockieren, bricht die
            // App (Auth/Navigation) und springt zurück aufs Dashboard.
            const host = (location.hostname || '').toLowerCase();
            if (/^(app|dashboard)\.complyo\.(de|tech)$/.test(host)) {
                console.log('[Complyo Content Blocker] Complyo-App erkannt – Blocking deaktiviert.');
                return;
            }

            // Listen for consent events
            window.addEventListener('complyoConsent', (e) => {
                this.consent = e.detail.categories;
                console.log('[Complyo Content Blocker] Consent received:', this.consent);
                this.unblockContent();
            });

            // Consent früh laden, um unnötiges Block→Unblock zu vermeiden.
            this.consent = this.loadConsentFromStorage();

            if (!this.consent) {
                // SOFORT (noch vor DOMContentLoaded) Hooks setzen, beobachten und
                // eine erste Runde blockieren – damit früh im <head> stehende und
                // dynamisch injizierte Ressourcen erfasst werden, statt erst nach
                // DOMContentLoaded (wo der Browser sie längst geladen hätte).
                this.installEarlyHooks();
                this.observeDOM();
                this.blockAllContent();
            }

            // Listen for DOM loaded
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', () => this.onDOMReady());
            } else {
                this.onDOMReady();
            }
        }

        async onDOMReady() {
            if (this.consent) {
                // Consent already given - unblock immediately
                console.log('[Complyo Content Blocker] Consent found, unblocking...');
                this.unblockContent();
            } else {
                // Vollständig geparstes DOM erneut scannen …
                this.blockAllContent();

                // … dann die Blockliste um den kompletten Service-Katalog
                // anreichern und nochmals scannen (selten genutzte Tools).
                await this.loadServiceDomains();
                this.blockAllContent();
            }

            // 🔒 Lizenzprüfung: Ohne aktive Lizenz (Website im Dashboard entfernt)
            // darf NICHT blockiert werden – sonst bliebe z. B. Google Maps kaputt.
            this.enforceLicense();
        }

        /**
         * Frühe Interception dynamisch erzeugter <script>/<link>-Elemente.
         * Wird übersprungen, wenn der synchrone Head-Blocker (cookie-blocker.js)
         * bereits aktiv ist – der übernimmt das dann (keine Doppel-Hooks).
         */
        installEarlyHooks() {
            if (this._hooked || window.ComplyoCookieBlocker) return;
            this._hooked = true;
            const self = this;
            const orig = document.createElement.bind(document);

            document.createElement = function(tagName) {
                const el  = orig(tagName);
                const tag = String(tagName).toLowerCase();

                if (tag === 'script' || tag === 'link') {
                    const attr    = (tag === 'script') ? 'src' : 'href';
                    const proto   = (tag === 'script') ? HTMLScriptElement.prototype : HTMLLinkElement.prototype;
                    const origSet = el.setAttribute.bind(el);

                    // Markiert das Element als geblockt (ohne den Request zu starten).
                    const blockIfNeeded = function(value) {
                        const cat = self.getCategoryForURL(value);
                        if (!cat || self.hasConsent(cat)) return false;
                        if (tag === 'script') {
                            origSet('type', 'text/plain');
                            origSet('data-complyo-src', value);
                            self.blockedElements.set(el, { type: 'script', category: cat, originalSrc: value });
                        } else {
                            origSet('data-complyo-href', value);
                            origSet('media', 'not all');
                            self.blockedElements.set(el, { type: 'stylesheet', category: cat, originalHref: value });
                        }
                        origSet('data-complyo-consent', cat);
                        origSet('data-complyo-blocked', 'true');
                        return true;
                    };

                    // 1) setAttribute('src'|'href', …)
                    el.setAttribute = function(name, value) {
                        if (name === attr && blockIfNeeded(value)) return;
                        origSet(name, value);
                    };

                    // 2) el.src = … / el.href = …  (so injizieren GA/GTM/Meta real!)
                    const desc = Object.getOwnPropertyDescriptor(proto, attr);
                    if (desc && desc.set && desc.get) {
                        Object.defineProperty(el, attr, {
                            configurable: true,
                            enumerable: true,
                            get: function() { return desc.get.call(this); },
                            set: function(value) {
                                if (blockIfNeeded(value)) return; // Request schlucken
                                desc.set.call(this, value);
                            }
                        });
                    }
                }
                return el;
            };
        }

        // Loads the domain→category mapping for ALL services from the Complyo
        // catalogue and merges it into BLOCKED_DOMAINS. This closes the gap
        // where only ~68 hard-coded domains were blocked while 200+ services
        // are configurable. Fail-open: on error the built-in list stays in use.
        async loadServiceDomains() {
            try {
                const siteId = this.getSiteIdFromScript();
                const url = siteId
                    ? `${API_BASE}/api/cookie-compliance/services?site_id=${encodeURIComponent(siteId)}`
                    : `${API_BASE}/api/cookie-compliance/services`;
                const res = await fetch(url);
                if (!res.ok) return;
                const data = await res.json();
                const services = (data && data.services) || [];
                let added = 0;
                services.forEach(svc => {
                    let tpl = svc.template;
                    if (typeof tpl === 'string') {
                        try { tpl = JSON.parse(tpl); } catch (e) { tpl = null; }
                    }
                    const category = (tpl && tpl.category) || svc.category;
                    const domains = (tpl && tpl.domains) || [];
                    // 'necessary' services never need blocking.
                    if (!category || category === 'necessary') return;
                    if (!BLOCKED_DOMAINS[category]) BLOCKED_DOMAINS[category] = [];
                    domains.forEach(d => {
                        const dom = String(d).toLowerCase().trim();
                        if (dom && !BLOCKED_DOMAINS[category].includes(dom)) {
                            BLOCKED_DOMAINS[category].push(dom);
                            added++;
                        }
                        // Drittland-Service? Domain zusätzlich für das Art.49-Gating merken.
                        if (dom && svc.requires_third_country_consent && !THIRD_COUNTRY_DOMAINS.includes(dom)) {
                            THIRD_COUNTRY_DOMAINS.push(dom);
                        }
                    });
                });
                if (added > 0) {
                    console.log(`[Complyo Content Blocker] Block list enriched with ${added} service domain(s)`);
                }
            } catch (e) {
                // fail-open – keep built-in list
                console.warn('[Complyo Content Blocker] Could not load service domains:', e);
            }
        }

        getSiteIdFromScript() {
            const scripts = document.querySelectorAll('script[data-site-id]');
            if (scripts.length > 0) {
                return scripts[scripts.length - 1].getAttribute('data-site-id');
            }
            return null;
        }

        // Hebt die Blockierung vollständig auf, wenn keine aktive Lizenz besteht.
        // Fail-open: bei Fehlern/Demo bleibt das normale Verhalten erhalten.
        async enforceLicense() {
            try {
                const siteId = this.getSiteIdFromScript();
                if (!siteId || siteId === 'demo-site' || siteId === 'demo') return;
                const res = await fetch(`https://api.complyo.de/api/cookie-compliance/config/${siteId}`);
                if (!res.ok) return;
                const data = await res.json();
                const licenseInactive = data && data.data && data.data.license_active === false;
                if (licenseInactive) {
                    console.warn('[Complyo Content Blocker] Keine aktive Lizenz – Blockierung wird vollständig aufgehoben.');
                    // Volle Freigabe, damit alle eingebetteten Inhalte normal laden
                    this.consent = { necessary: true, functional: true, analytics: true, marketing: true };
                    this.unblockContent();
                }
            } catch (e) {
                // fail-open – im Zweifel normales Blockierverhalten beibehalten
            }
        }
        
        loadConsentFromStorage() {
            try {
                const stored = localStorage.getItem('complyo_cookie_consent');
                if (stored) {
                    const consent = JSON.parse(stored);
                    return {
                        necessary: true,
                        functional: consent.functional || false,
                        analytics: consent.analytics || false,
                        marketing: consent.marketing || false,
                        third_country: consent.third_country || false
                    };
                }
            } catch (error) {
                console.warn('[Complyo] Error loading consent:', error);
            }
            return null;
        }
        
        observeDOM() {
            // Watch for dynamically added elements
            this.observer = new MutationObserver((mutations) => {
                for (const mutation of mutations) {
                    for (const node of mutation.addedNodes) {
                        if (node.nodeType === Node.ELEMENT_NODE) {
                            this.blockElement(node);
                        }
                    }
                }
            });
            
            // documentElement statt body: existiert bereits beim frühen Init und
            // erfasst auch in den <head> injizierte Tracker/Stylesheets.
            this.observer.observe(document.documentElement || document, {
                childList: true,
                subtree: true
            });
        }
        
        // ====================================================================
        // Blocking Logic
        // ====================================================================
        
        blockAllContent() {
            // Block scripts
            this.blockScripts();

            // Server-seitig neutralisierte Inline-Scripts erfassen (für Unblock)
            this.blockInlineScripts();

            // Block iframes
            this.blockIframes();
            
            // Block images (tracking pixels)
            this.blockImages();
            
            // Block data-attribute elements
            this.blockDataAttributes();
            
            // Block external stylesheets / web fonts (<link rel=stylesheet>,
            // <link as=font>, Preload/Preconnect zu Tracking-/Font-Hosts)
            this.blockStylesheets();

            // Block inline fonts (Google Fonts in style tags)
            this.blockInlineFonts();

            // Block inline styles with external URLs
            this.blockInlineStyles();
            
            // Check for ad blockers and ensure visibility
            this.ensureBannerVisibility();
        }
        
        blockScripts() {
            const scripts = document.querySelectorAll('script[src]');
            
            scripts.forEach(script => {
                // Skip if already processed
                if (script.hasAttribute('data-complyo-processed')) {
                    return;
                }
                
                const src = script.src;
                const category = this.getCategoryForURL(src);
                
                if (category && !this.hasConsent(category)) {
                    // Block script
                    const placeholder = document.createElement('script');
                    placeholder.type = 'text/plain';
                    placeholder.setAttribute('data-complyo-consent', category);
                    placeholder.setAttribute('data-complyo-src', src);
                    placeholder.setAttribute('data-complyo-blocked', 'true');
                    
                    // Copy attributes
                    Array.from(script.attributes).forEach(attr => {
                        if (attr.name !== 'src' && attr.name !== 'type') {
                            placeholder.setAttribute(attr.name, attr.value);
                        }
                    });
                    
                    // Replace
                    script.parentNode.replaceChild(placeholder, script);
                    
                    this.blockedElements.set(placeholder, {
                        type: 'script',
                        category: category,
                        original: script
                    });
                    
                    console.log(`[Complyo] Blocked script: ${src} (${category})`);
                }
                
                script.setAttribute('data-complyo-processed', 'true');
            });
        }
        
        /**
         * Inline-Tracking-Scripts, die das WP-Plugin server-seitig auf
         * type="text/plain" + data-complyo-consent="<kategorie>" gesetzt hat,
         * für die spätere Freigabe registrieren. (Reine Client-Seite kann bereits
         * ausgeführte Inline-Scripts nicht zurücknehmen – daher die Neutralisierung
         * im Markup, hier nur Tracking + Unblock.)
         */
        blockInlineScripts() {
            const scripts = document.querySelectorAll('script[type="text/plain"][data-complyo-consent]');
            scripts.forEach(s => {
                if (s.hasAttribute('data-complyo-inline-processed')) return;
                // Externe (mit data-complyo-src) werden via unblockScript behandelt.
                if (!s.getAttribute('data-complyo-src')) {
                    const category = s.getAttribute('data-complyo-consent');
                    if (category && !this.hasConsent(category)) {
                        this.blockedElements.set(s, { type: 'inline-script', category: category });
                    }
                }
                s.setAttribute('data-complyo-inline-processed', 'true');
            });
        }

        blockIframes() {
            const iframes = document.querySelectorAll('iframe[src]');
            
            iframes.forEach(iframe => {
                // Skip if already processed
                if (iframe.hasAttribute('data-complyo-processed')) {
                    return;
                }
                
                const src = iframe.src;
                const category = this.getCategoryForURL(src);
                
                if (category && !this.hasConsent(category)) {
                    // Check if it's a video/map service
                    const service = this.detectService(src);
                    
                    if (service) {
                        // Create visual placeholder
                        const placeholder = this.createVisualPlaceholder(iframe, service, category);
                        iframe.parentNode.replaceChild(placeholder, iframe);
                        
                        this.blockedElements.set(placeholder, {
                            type: 'iframe',
                            category: category,
                            original: iframe,
                            service: service
                        });
                        
                        console.log(`[Complyo] Blocked ${service.name}: ${src}`);
                    } else if (iframe.parentNode) {
                        // Generic embed: show the same click-to-load placeholder
                        // as for known video/map services (Borlabs-style), with a
                        // friendly name derived from the host.
                        let host = src;
                        try { host = new URL(src).hostname.replace(/^www\./, ''); } catch (e) {}
                        const genericService = {
                            name: host || 'Externer Inhalt',
                            icon: '🔒',
                            generic: true
                        };
                        const placeholder = this.createVisualPlaceholder(iframe, genericService, category);
                        iframe.parentNode.replaceChild(placeholder, iframe);

                        this.blockedElements.set(placeholder, {
                            type: 'iframe',
                            category: category,
                            original: iframe,
                            service: genericService
                        });

                        console.log(`[Complyo] Blocked iframe (placeholder): ${src} (${category})`);
                    } else {
                        // Detached iframe – fall back to plain hiding.
                        iframe.removeAttribute('src');
                        iframe.setAttribute('data-complyo-consent', category);
                        iframe.setAttribute('data-complyo-src', src);
                        iframe.setAttribute('data-complyo-blocked', 'true');
                        iframe.style.display = 'none';

                        this.blockedElements.set(iframe, {
                            type: 'iframe',
                            category: category,
                            originalSrc: src
                        });

                        console.log(`[Complyo] Blocked iframe: ${src} (${category})`);
                    }
                }
                
                iframe.setAttribute('data-complyo-processed', 'true');
            });
        }
        
        blockImages() {
            const images = document.querySelectorAll('img[src]');
            
            images.forEach(img => {
                // Skip if already processed
                if (img.hasAttribute('data-complyo-processed')) {
                    return;
                }
                
                const src = img.src;
                const category = this.getCategoryForURL(src);

                // Bilder von Analytics-/Marketing-/Tracking-Hosts werden anhand
                // der DOMAIN blockiert – nicht anhand der gerenderten Größe. Die
                // alte 1×1-Heuristik versagte, weil width/naturalWidth vor dem
                // Laden 0 sind und größere Tracking-Beacons durchrutschten.
                if (category && !this.hasConsent(category)) {
                    img.setAttribute('data-complyo-consent', category);
                    img.setAttribute('data-complyo-src', src);
                    img.setAttribute('data-complyo-blocked', 'true');
                    // Transparentes 1×1, um Broken-Image-Icons zu vermeiden.
                    img.src = 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7';

                    this.blockedElements.set(img, {
                        type: 'image',
                        category: category,
                        originalSrc: src
                    });

                    console.log(`[Complyo] Blocked tracking image: ${src} (${category})`);
                }

                img.setAttribute('data-complyo-processed', 'true');
            });
        }
        
        blockDataAttributes() {
            // Block elements with data-complyo-consent attribute
            const elements = document.querySelectorAll('[data-complyo-consent]');
            
            elements.forEach(element => {
                // <script>-Elemente gehören blockScripts()/blockInlineScripts() –
                // hier NICHT als 'data-attribute' registrieren, sonst wird die
                // inline-script-Registrierung überschrieben und nie wieder
                // ausgeführt (kein Unblock-Handler für 'data-attribute').
                if (element.tagName === 'SCRIPT') return;

                const category = element.getAttribute('data-complyo-consent');

                if (!this.hasConsent(category)) {
                    // Already blocked via attribute
                    this.blockedElements.set(element, {
                        type: 'data-attribute',
                        category: category
                    });
                }
            });
        }
        
        blockElement(element) {
            // Helper to block a single element
            if (element.tagName === 'SCRIPT') {
                this.blockScripts();
            } else if (element.tagName === 'IFRAME') {
                this.blockIframes();
            } else if (element.tagName === 'IMG') {
                this.blockImages();
            } else if (element.tagName === 'LINK') {
                this.blockStylesheets();
            } else if (element.tagName === 'STYLE') {
                this.blockInlineFonts();
                this.blockInlineStyles();
            }
            // Verschachtelte relevante Kinder (z.B. bei eingefügten Fragmenten):
            // einzelne, idempotente Scanner – NICHT blockAllContent (das würde
            // den AdBlock-Test bei jeder Mutation neu auslösen).
            if (element.querySelector && element.querySelector('link[href], style, script[src], iframe[src], img[src]')) {
                this.blockScripts();
                this.blockIframes();
                this.blockImages();
                this.blockStylesheets();
                this.blockInlineFonts();
                this.blockInlineStyles();
            }
        }
        
        // ====================================================================
        // Unblocking Logic
        // ====================================================================
        
        unblockContent() {
            if (!this.consent) {
                return;
            }
            
            console.log('[Complyo] Unblocking content based on consent:', this.consent);
            
            // Stop observing (no need to block new elements)
            if (this.observer) {
                this.observer.disconnect();
            }
            
            // Unblock all elements
            this.blockedElements.forEach((data, element) => {
                const category = data.category;
                // URL aus allen Block-Varianten ableiten: direkte Quelle, oder
                // — bei Platzhaltern (Video/Map/Script) — vom Original-DOM-Node.
                const url = data.originalSrc || data.originalHref ||
                    (data.original && (data.original.src || data.original.href)) || '';

                // Freischalten nur, wenn die Kategorie eingewilligt ist UND —
                // falls der Service in einem unsicheren Drittland verarbeitet —
                // zusätzlich die gesonderte Art.49-Einwilligung vorliegt.
                if (this.hasConsent(category) && this.thirdCountryAllowed(url)) {
                    this.unblockElement(element, data);
                }
            });
            
            // Unblock inline fonts (Phase 3)
            this.unblockFonts();
            
            // Unblock inline styles (Phase 3)
            this.unblockInlineStyles();
        }
        
        unblockElement(element, data) {
            const { type, category } = data;
            
            console.log(`[Complyo] Unblocking ${type} (${category})`);
            
            if (type === 'script') {
                this.unblockScript(element, data);
            } else if (type === 'iframe') {
                this.unblockIframe(element, data);
            } else if (type === 'image') {
                this.unblockImage(element, data);
            } else if (type === 'stylesheet') {
                this.unblockStylesheet(element, data);
            } else if (type === 'inline-script') {
                this.unblockInlineScript(element, data);
            }

            // Remove from blocked list
            this.blockedElements.delete(element);
        }
        
        unblockScript(element, data) {
            const src = element.getAttribute('data-complyo-src') || (data && data.originalSrc);

            if (src && element.parentNode) {
                // Create new script element
                const script = document.createElement('script');
                script.type = 'text/javascript';
                script.src = src;

                // Copy attributes
                Array.from(element.attributes).forEach(attr => {
                    if (!attr.name.startsWith('data-complyo') && attr.name !== 'type') {
                        script.setAttribute(attr.name, attr.value);
                    }
                });

                // Replace
                element.parentNode.replaceChild(script, element);
            }
        }
        
        unblockIframe(element, data) {
            if (data.service) {
                // Replace visual placeholder with actual iframe
                const iframe = data.original;
                element.parentNode.replaceChild(iframe, element);
                
                // Auto-play videos
                if (data.service.name === 'YouTube' && iframe.src.indexOf('autoplay=1') === -1) {
                    iframe.src += (iframe.src.indexOf('?') > -1 ? '&' : '?') + 'autoplay=1';
                }
            } else {
                // Restore src
                const src = element.getAttribute('data-complyo-src');
                if (src) {
                    element.src = src;
                    element.removeAttribute('data-complyo-src');
                    element.removeAttribute('data-complyo-blocked');
                    element.style.display = '';
                }
            }
        }
        
        unblockImage(element, data) {
            const src = data.originalSrc || element.getAttribute('data-complyo-src');
            if (src) {
                element.src = src;
                element.removeAttribute('data-complyo-src');
                element.removeAttribute('data-complyo-blocked');
            }
        }

        unblockInlineScript(element, data) {
            if (!element.parentNode) return;
            const script = document.createElement('script');
            script.type = 'text/javascript';
            Array.from(element.attributes).forEach(attr => {
                if (!attr.name.startsWith('data-complyo') && attr.name !== 'type') {
                    script.setAttribute(attr.name, attr.value);
                }
            });
            // Inline-Code 1:1 übernehmen → wird beim Einfügen ausgeführt.
            script.text = element.textContent || '';
            element.parentNode.replaceChild(script, element);
        }

        unblockStylesheet(element, data) {
            const href = data.originalHref || element.getAttribute('data-complyo-href');
            if (href) {
                const rel = element.getAttribute('data-complyo-rel');
                element.removeAttribute('media');
                if (rel) element.setAttribute('rel', rel);
                element.setAttribute('href', href);
                element.removeAttribute('data-complyo-blocked');
                element.removeAttribute('data-complyo-href');
            }
        }
        
        // ====================================================================
        // Visual Placeholders
        // ====================================================================
        
        createVisualPlaceholder(iframe, service, category) {
            const placeholder = document.createElement('div');
            placeholder.className = 'complyo-content-placeholder';
            placeholder.setAttribute('data-complyo-consent', category);
            placeholder.setAttribute('data-complyo-service', service.name);
            placeholder.style.cssText = `
                position: relative;
                width: ${iframe.width || '100%'};
                height: ${iframe.height || '400px'};
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                display: flex;
                align-items: center;
                justify-content: center;
                flex-direction: column;
                color: white;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                border-radius: 8px;
                overflow: hidden;
                cursor: pointer;
                transition: transform 0.2s;
            `;
            
            placeholder.innerHTML = `
                <style>
                    .complyo-content-placeholder:hover {
                        transform: scale(1.02);
                    }
                    .complyo-placeholder-icon {
                        font-size: 48px;
                        margin-bottom: 16px;
                        opacity: 0.9;
                    }
                    .complyo-placeholder-title {
                        font-size: 20px;
                        font-weight: 600;
                        margin-bottom: 8px;
                    }
                    .complyo-placeholder-text {
                        font-size: 14px;
                        opacity: 0.9;
                        text-align: center;
                        padding: 0 20px;
                        max-width: 400px;
                    }
                    .complyo-placeholder-btn {
                        margin-top: 20px;
                        padding: 12px 24px;
                        background: white;
                        color: #667eea;
                        border: none;
                        border-radius: 6px;
                        font-weight: 600;
                        cursor: pointer;
                        transition: all 0.2s;
                    }
                    .complyo-placeholder-btn:hover {
                        transform: translateY(-2px);
                        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
                    }
                </style>
                <div class="complyo-placeholder-icon">${service.icon}</div>
                <div class="complyo-placeholder-title">${service.generic ? service.name : service.name + ' Video'}</div>
                <div class="complyo-placeholder-text">
                    Zum Laden dieses Inhalts ist Ihre Zustimmung erforderlich.
                </div>
                <button class="complyo-placeholder-btn">
                    Inhalt laden
                </button>
            `;
            
            // Click handler to load content
            placeholder.addEventListener('click', () => {
                // If no consent yet, show banner
                if (!this.hasConsent(category)) {
                    if (window.complyoCookieBanner) {
                        window.complyoCookieBanner.showBanner();
                    }
                } else {
                    // Consent given, load immediately
                    this.unblockElement(placeholder, {
                        type: 'iframe',
                        category: category,
                        original: iframe,
                        service: service
                    });
                }
            });
            
            return placeholder;
        }
        
        // ====================================================================
        // Helper Methods
        // ====================================================================
        
        getCategoryForURL(url) {
            if (!url) return null;

            const full = url.toLowerCase();
            let host = '';
            try { host = new URL(url, location.href).hostname.toLowerCase(); } catch (e) { host = ''; }

            // Erstanbieter-Ressourcen (same-origin) NIE blockieren – eigene
            // Scripts/Stylesheets/Navigations-Chunks der Seite. Tracker sind
            // per Definition Drittanbieter.
            if (host && host === (location.hostname || '').toLowerCase()) {
                return null;
            }

            // Priorität: marketing > analytics > functional. Domains, die in
            // mehreren Kategorien stehen (z.B. tiktok.com, youtube.com), werden
            // damit der STRENGSTEN Kategorie zugeordnet — eine reine
            // Analytics-Einwilligung gibt sie dann NICHT frei (Bugfix).
            const order = ['marketing', 'analytics', 'functional'];
            const cats = order.concat(Object.keys(BLOCKED_DOMAINS).filter(c => order.indexOf(c) === -1));

            for (const category of cats) {
                const domains = BLOCKED_DOMAINS[category] || [];
                for (const domain of domains) {
                    if (this.matchesDomain(host, full, domain)) {
                        return category;
                    }
                }
            }
            return null;
        }

        /**
         * Domain-Match mit Hostname-Grenzen statt naivem includes():
         * verhindert, dass z.B. 'x.com' auf 'box.com' oder 'maxcdn.com' matcht.
         */
        matchesDomain(host, fullUrl, domain) {
            if (!domain) return false;
            domain = String(domain).toLowerCase().trim();
            if (!domain) return false;
            // Pfad-Einträge (z.B. 'google.com/maps') oder Dateinamen ('matomo.js')
            // → Teilstring auf der vollen URL.
            if (domain.indexOf('/') !== -1 || domain.slice(-3) === '.js') {
                return fullUrl.indexOf(domain) !== -1;
            }
            if (!host) return fullUrl.indexOf(domain) !== -1;
            // exakter Host oder Subdomain-Suffix
            return host === domain || host.endsWith('.' + domain);
        }
        
        detectService(url) {
            // Check video services
            for (const [key, service] of Object.entries(VIDEO_SERVICES)) {
                if (service.pattern.test(url)) {
                    return service;
                }
            }
            
            // Check map services
            for (const [key, service] of Object.entries(MAP_SERVICES)) {
                if (service.pattern.test(url)) {
                    return service;
                }
            }
            
            return null;
        }
        
        hasConsent(category) {
            if (!this.consent) {
                return false;
            }
            
            // Necessary cookies are always allowed
            if (category === 'necessary') {
                return true;
            }

            return this.consent[category] === true;
        }

        /**
         * Verarbeitet die Ziel-URL Daten in einem unsicheren Drittland?
         * (Service mit requires_third_country_consent — Domain in THIRD_COUNTRY_DOMAINS.)
         */
        requiresThirdCountryConsent(url) {
            if (!url || THIRD_COUNTRY_DOMAINS.length === 0) return false;
            const full = String(url).toLowerCase();
            let host = '';
            try { host = new URL(url, location.href).hostname.toLowerCase(); } catch (e) { host = ''; }
            return THIRD_COUNTRY_DOMAINS.some(domain => this.matchesDomain(host, full, domain));
        }

        /**
         * Darf eine ggf. drittland-relevante URL geladen werden? True, wenn die
         * URL kein unsicheres Drittland berührt ODER die gesonderte
         * Art.49-Einwilligung erteilt wurde.
         */
        thirdCountryAllowed(url) {
            if (!this.requiresThirdCountryConsent(url)) return true;
            return !!(this.consent && this.consent.third_country === true);
        }
        
        // ====================================================================
        // Phase 3: Enhanced Blocking Features
        // ====================================================================
        
        /**
         * Externe Stylesheets / Web-Fonts blockieren:
         * <link rel="stylesheet">, <link as="font">/Preload sowie Preconnect/
         * DNS-Prefetch zu Tracking-/Font-Hosts. href wird entfernt (stoppt den
         * Request, sofern noch nicht fertig) und media="not all" gesetzt
         * (verhindert das Anwenden bereits geladener CSS). Wiederherstellung
         * bei Consent über unblockStylesheet().
         */
        blockStylesheets() {
            const links = document.querySelectorAll('link[href]');

            links.forEach(link => {
                if (link.hasAttribute('data-complyo-processed-link')) return;

                const href = link.href;
                const rel  = (link.getAttribute('rel') || '').toLowerCase();
                const as   = (link.getAttribute('as')  || '').toLowerCase();
                const relevant = rel.indexOf('stylesheet') !== -1 || as === 'font' ||
                                 rel === 'preload' || rel === 'prefetch' ||
                                 rel === 'preconnect' || rel === 'dns-prefetch';

                if (relevant) {
                    const category = this.getCategoryForURL(href);
                    if (category && !this.hasConsent(category)) {
                        link.setAttribute('data-complyo-consent', category);
                        link.setAttribute('data-complyo-href', href);
                        link.setAttribute('data-complyo-rel', link.getAttribute('rel') || '');
                        link.setAttribute('data-complyo-blocked', 'true');
                        link.setAttribute('media', 'not all');
                        link.removeAttribute('href');

                        this.blockedElements.set(link, {
                            type: 'stylesheet',
                            category: category,
                            originalHref: href
                        });

                        console.log(`[Complyo] Blocked stylesheet/font: ${href} (${category})`);
                    }
                }

                link.setAttribute('data-complyo-processed-link', 'true');
            });
        }

        /**
         * Block @font-face in inline styles (e.g., Google Fonts)
         */
        blockInlineFonts() {
            const styleElements = document.querySelectorAll('style');
            
            styleElements.forEach(style => {
                if (style.hasAttribute('data-complyo-font-processed')) return;
                
                const content = style.textContent || '';
                const fontFaceRegex = /@font-face\s*\{[^}]*src:\s*url\(['"]?(https?:\/\/fonts\.googleapis\.com[^'")\s]+)['"]?\)[^}]*\}/gi;
                
                if (fontFaceRegex.test(content)) {
                    if (!this.hasConsent('functional')) {
                        // Store original and replace with placeholder
                        style.setAttribute('data-complyo-original', content);
                        style.setAttribute('data-complyo-font-blocked', 'true');
                        
                        // Remove font-face rules but keep other styles
                        style.textContent = content.replace(fontFaceRegex, '/* [Complyo] Font blocked until consent */');
                        
                        this.blockedElements.set(style, {
                            type: 'font',
                            category: 'functional',
                            original: content
                        });
                        
                        console.log('[Complyo] Blocked inline Google Fonts');
                    }
                }
                
                style.setAttribute('data-complyo-font-processed', 'true');
            });
        }
        
        /**
         * Split inline styles to block external resources while keeping layout
         */
        blockInlineStyles() {
            const elementsWithStyle = document.querySelectorAll('[style*="url("]');
            
            elementsWithStyle.forEach(element => {
                if (element.hasAttribute('data-complyo-style-processed')) return;
                
                const style = element.getAttribute('style') || '';
                const urlRegex = /url\(['"]?(https?:\/\/[^'")\s]+)['"]?\)/gi;
                
                let match;
                while ((match = urlRegex.exec(style)) !== null) {
                    const url = match[1];
                    const category = this.getCategoryForURL(url);
                    
                    if (category && !this.hasConsent(category)) {
                        // Store original and replace URL
                        element.setAttribute('data-complyo-original-style', style);
                        element.setAttribute('data-complyo-style-blocked', 'true');
                        
                        // Replace blocked URLs with placeholder
                        const newStyle = style.replace(
                            new RegExp(url.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g'),
                            'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7'
                        );
                        element.setAttribute('style', newStyle);
                        
                        this.blockedElements.set(element, {
                            type: 'style',
                            category: category,
                            original: style
                        });
                        
                        console.log(`[Complyo] Blocked inline style URL: ${url}`);
                    }
                }
                
                element.setAttribute('data-complyo-style-processed', 'true');
            });
        }
        
        /**
         * Auto-play videos after consent is given
         */
        enableAutoplayAfterConsent(element, info) {
            if (info.type !== 'iframe' || !info.service) return;
            
            const iframe = info.original;
            if (!iframe) return;
            
            let src = iframe.getAttribute('data-complyo-src') || iframe.src;
            
            // Check if element requested autoplay
            if (element.hasAttribute('data-complyo-autoplay') || 
                iframe.hasAttribute('data-complyo-autoplay')) {
                
                // Add autoplay parameter based on service
                if (info.service.name === 'YouTube') {
                    src += (src.includes('?') ? '&' : '?') + 'autoplay=1&mute=1';
                } else if (info.service.name === 'Vimeo') {
                    src += (src.includes('?') ? '&' : '?') + 'autoplay=1&muted=1';
                }
                
                console.log(`[Complyo] Auto-playing ${info.service.name} video`);
            }
            
            return src;
        }
        
        /**
         * Restore blocked fonts after consent
         */
        unblockFonts() {
            document.querySelectorAll('[data-complyo-font-blocked="true"]').forEach(style => {
                const original = style.getAttribute('data-complyo-original');
                if (original && this.hasConsent('functional')) {
                    style.textContent = original;
                    style.removeAttribute('data-complyo-font-blocked');
                    console.log('[Complyo] Unblocked inline fonts');
                }
            });
        }
        
        /**
         * Restore blocked inline styles after consent
         */
        unblockInlineStyles() {
            document.querySelectorAll('[data-complyo-style-blocked="true"]').forEach(element => {
                const original = element.getAttribute('data-complyo-original-style');
                const category = this.blockedElements.get(element)?.category;
                
                if (original && category && this.hasConsent(category)) {
                    element.setAttribute('style', original);
                    element.removeAttribute('data-complyo-style-blocked');
                    console.log('[Complyo] Unblocked inline style');
                }
            });
        }
        
        // ====================================================================
        // Anti-AdBlocker Mechanism
        // ====================================================================
        
        /**
         * Check if the cookie banner might be blocked by ad blockers
         * Uses obfuscated detection to avoid filter lists
         */
        detectAdBlocker() {
            return new Promise((resolve) => {
                // Beim frühen Init (vor <body>) keinen AdBlock-Test fahren.
                if (!document.body) { resolve(false); return; }
                // Method 1: Check if common ad-block targeted elements are hidden
                const testAd = document.createElement('div');
                testAd.innerHTML = '&nbsp;';
                testAd.className = 'adsbox ad-banner pub_300x250';
                testAd.style.cssText = 'position:absolute;left:-9999px;';
                document.body.appendChild(testAd);
                
                setTimeout(() => {
                    const blocked = testAd.offsetHeight === 0;
                    document.body.removeChild(testAd);
                    resolve(blocked);
                }, 100);
            });
        }
        
        /**
         * Fallback rendering if ad blocker detected
         * Uses non-blocked class names and inline styles
         */
        async ensureBannerVisibility() {
            const isBlocked = await this.detectAdBlocker();
            
            if (isBlocked) {
                console.log('[Complyo] Ad blocker detected, using fallback rendering');
                
                // Remove common blocked class patterns
                const banner = document.querySelector('.complyo-cookie-banner');
                if (banner) {
                    // Use data attributes instead of classes
                    banner.setAttribute('data-cply-consent', 'true');
                    
                    // Apply critical styles inline to avoid CSS blocking
                    banner.style.cssText += `
                        display: block !important;
                        visibility: visible !important;
                        opacity: 1 !important;
                        pointer-events: auto !important;
                    `;
                }
            }
        }
        
        // ====================================================================
        // Public API
        // ====================================================================
        
        updateConsent(consent) {
            this.consent = consent;
            this.unblockContent();
        }
        
        blockAgain() {
            this.consent = null;
            // Bei Widerruf bereits gesetzte Tracking-Cookies entfernen, BEVOR neu
            // geladen wird – sonst blieben sie trotz Widerruf bestehen.
            this.deleteCookies();
            location.reload(); // Easiest way to re-block everything
        }

        /**
         * Löscht bekannte Tracking-Cookies (Präfix-Match) auf der aktuellen
         * Domain inkl. übergeordneter Domain (führender Punkt) und localStorage.
         */
        deleteCookies() {
            try {
                const host  = window.location.hostname;
                const parts = host.split('.');
                const base  = parts.length > 1 ? parts.slice(-2).join('.') : host;
                const domains = ['', host, '.' + host, '.' + base];
                const existing = document.cookie.split(';').map(c => c.split('=')[0].trim());

                existing.forEach(name => {
                    if (!name) return;
                    const match = COOKIES_TO_DELETE.some(prefix => name.indexOf(prefix) === 0);
                    if (!match) return;
                    domains.forEach(d => {
                        const dom = d ? '; domain=' + d : '';
                        document.cookie = name + '=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/' + dom + ';';
                    });
                });

                // Tracking-bezogene localStorage-Schlüssel best effort entfernen.
                Object.keys(window.localStorage || {}).forEach(key => {
                    if (/^(_ga|_gid|amplitude|mp_|mixpanel|hj|_hj|fbq|_fbp)/i.test(key)) {
                        try { localStorage.removeItem(key); } catch (e) {}
                    }
                });
            } catch (e) {
                console.warn('[Complyo] Cookie cleanup failed:', e);
            }
        }
    }
    
    // ========================================================================
    // Auto-Initialize
    // ========================================================================
    
    // Auto-initialize
    const initBlocker = () => {
        if (!window.complyoContentBlocker) {
            window.complyoContentBlocker = new ComplyoContentBlocker();
        }
    };
    
    // Init as early as possible (even before DOM ready)
    initBlocker();
    
    // Export
    window.ComplyoContentBlocker = ComplyoContentBlocker;
    
    console.log(`[Complyo] Content Blocker v${VERSION} loaded`);
    
})();

