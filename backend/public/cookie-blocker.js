/**
 * Complyo Cookie Blocker & Auto-Blocking System
 * Version: 2.1.0
 *
 * Automatically blocks scripts, iframes, and cookies until user consent
 * DSGVO/GDPR compliant cookie management
 *
 * 2.1.0 (10.11.2026): Kategorien statt flacher Musterliste (YouTube-API, Vimeo-API,
 * widgetapi), Haken auf Prototypen statt createElement, Einwilligung auch aus
 * localStorage (Banner-Schluessel), serverseitig neutralisierte Skripte/iframes
 * (Plugin) werden von hier freigegeben, auch fuer wiederkehrende Besucher.
 * Platzhalter fuer iframes baut allein der Content-Blocker des Widgets (Banner-
 * Gestaltung), hier gibt es keinen eigenen Platzhalter mehr.
 *
 * Grenze, die kein Browser-Skript loesen kann: Der Vorlade-Scanner des Browsers holt
 * statische <script src>/<link href> im HTML, bevor dieses Skript sie anfassen kann.
 * Das schliesst nur die Serverseite (WordPress-Plugin: Neutralisierung im Markup,
 * type="text/plain" + data-complyo-src). Dieses Skript gibt solche Elemente nach
 * der Einwilligung frei.
 */

(function() {
    'use strict';

    // site_id ermitteln: Vorrang hat das data-site-id-Attribut des einbindenden
    // <script>-Tags — genau so binden die WP-/Joomla-Plugins diese Datei ein.
    // document.currentScript ist bei async/defer oder verzoegerter Ausfuehrung
    // null, dann Fallback: das eigene Script-Tag per src-Match suchen. Zuletzt
    // greift der server-seitig ersetzte Platzhalter (falls er ersetzt wurde).
    const SERVER_SITE_ID = 'SITE_ID_PLACEHOLDER';
    function detectSiteId() {
        let el = document.currentScript;
        if (!el || !el.dataset || !el.dataset.siteId) {
            el = null;
            const scripts = document.querySelectorAll('script[src]');
            for (let i = 0; i < scripts.length; i++) {
                const s = scripts[i];
                if (/cookie-blocker(\.min)?\.js/.test(s.src || '') && s.dataset && s.dataset.siteId) {
                    el = s;
                    break;
                }
            }
        }
        if (el && el.dataset && el.dataset.siteId) {
            return el.dataset.siteId;
        }
        // Nur verwenden, wenn der Platzhalter tatsaechlich ersetzt wurde
        if (SERVER_SITE_ID && SERVER_SITE_ID.indexOf('PLACEHOLDER') === -1) {
            return SERVER_SITE_ID;
        }
        return null;
    }

    // Originale Funktionen VOR dem Ueberschreiben sichern (die Haken rufen sie auf).
    const nativeSetAttribute = Element.prototype.setAttribute;
    const nativeGetAttribute = Element.prototype.getAttribute;
    const nativeRemoveAttribute = Element.prototype.removeAttribute;
    const scriptSrcDesc = Object.getOwnPropertyDescriptor(HTMLScriptElement.prototype, 'src');
    const linkHrefDesc = Object.getOwnPropertyDescriptor(HTMLLinkElement.prototype, 'href');
    const iframeSrcDesc = Object.getOwnPropertyDescriptor(HTMLIFrameElement.prototype, 'src');

    // Skripte je Kategorie. Eine Kategorie ist erst frei, wenn der Besucher sie
    // eingewilligt hat. YouTube/Vimeo-APIs zaehlen als marketing (wie ihre iframes).
    const SCRIPT_RULES = {
        analytics: [
            /googletagmanager\.com\/(gtag|gtm)/,
            /google-analytics\.com/,
            /static\.hotjar\.com/,
            /matomo\.js|piwik\.js/,
            /plausible\.io/,
            /clarity\.ms/
        ],
        marketing: [
            /connect\.facebook\.net/,
            /facebook\.com\/tr/,
            /googleadservices\.com/,
            /doubleclick\.net/,
            /snap\.licdn\.com/,
            /analytics\.tiktok\.com/,
            /platform\.twitter\.com/,
            // Video-APIs: werden von Slidern/Page-Buildern dynamisch nachgeladen
            /youtube(-nocookie)?\.com\/(iframe_api|player_api)/,
            /youtube\.com\/s\/player\//,
            /s\.ytimg\.com\/yts\//,
            /www-widgetapi\.js/,
            /player\.vimeo\.com\/api\//
        ],
        functional: [
            /widget\.intercom\.io/,
            /static\.zdassets\.com/,
            /embed\.tawk\.to/,
            /client\.crisp\.chat/
        ]
    };

    // Rahmen (iframes) je Kategorie.
    const IFRAME_RULES = {
        marketing: [
            /youtube(-nocookie)?\.com\/embed/,
            /player\.vimeo\.com/,
            /instagram\.com\/embed/,
            /twitter\.com\/widgets/,
            /platform\.twitter\.com/
        ],
        functional: [
            /google\.com\/maps\/embed/
        ]
    };

    // Anbieter, die Daten in die USA uebertragen (Art. 49 Abs. 1 lit. a DSGVO):
    // zusaetzlich zur Kategorie wird die gesonderte Drittland-Einwilligung verlangt,
    // wie sie der Banner mit "Alle akzeptieren" bzw. dem Drittland-Schalter erteilt.
    const US_HOSTS = /(^|[./])(google|googleapis|gstatic|googletagmanager|google-analytics|googleadservices|doubleclick|youtube|youtube-nocookie|ytimg|facebook|facebook\.net|instagram|twitter|linkedin|licdn|tiktok|vimeo)\./i;

    function absoluteUrl(u) {
        try { return new URL(String(u), document.baseURI).href; } catch (e) { return String(u || ''); }
    }

    const ComplyoCookieBlocker = {
        // Configuration
        config: {
            siteId: detectSiteId(),
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

            // Einwilligung VOR dem ersten Haken laden: wer schon zugestimmt hat,
            // soll nie blockiert werden (kein Block-Freigabe-Zickzack).
            this.loadConsent();

            // Load configuration from API (async, verfeinert Patterns)
            this.loadConfiguration();

            // Block scripts before they execute
            this.blockScriptsEarly();

            // Listen for DOM changes
            this.observeDOM();

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
         * Consent-Format überführen und blockierte Elemente SOFORT wieder
         * freigeben – ohne Page-Reload.
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
                    marketing:  cats.marketing  === true,
                    third_country: cats.third_country === true
                }
            };

            this.state.consent = consent;

            // Freigeben, was jetzt erlaubt ist. Bei reiner Ablehnung
            // Tracking-Cookies entfernen.
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
            if (!this.config.siteId) {
                console.warn('[Complyo] Keine site_id gefunden — bitte data-site-id am <script>-Tag setzen. Es gelten nur die statischen Block-Patterns.');
                return;
            }
            try {
                const response = await fetch(`${this.config.apiUrl}/api/cookie-compliance/config/${encodeURIComponent(this.config.siteId)}`);
                if (response.ok) {
                    const data = await response.json();
                    // Der Endpoint liefert {success, data} — nicht {success, config}
                    if (data.success && data.data) {
                        this.config.serviceConfig = data.data;
                        this.buildBlockingPatterns(data.data.services || []);
                    }
                }
            } catch (error) {
                console.error('[Complyo] Failed to load configuration:', error);
            }
        },

        /**
         * Build blocking patterns
         */
        buildBlockingPatterns: function(services) {
            // Flache Listen (Rueckwaertskompatibel); die Kategorie steht in SCRIPT_RULES.
            this.config.blockedScripts = [].concat(
                SCRIPT_RULES.analytics, SCRIPT_RULES.marketing, SCRIPT_RULES.functional);
            this.config.blockedIframes = [].concat(IFRAME_RULES.marketing, IFRAME_RULES.functional);

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
         * Kategorie einer Skript-URL (analytics | marketing | functional) oder null.
         */
        categoryForScript: function(src) {
            if (!src) return null;
            const u = String(src);
            const cats = ['analytics', 'marketing', 'functional'];
            for (let i = 0; i < cats.length; i++) {
                if (SCRIPT_RULES[cats[i]].some(re => re.test(u))) return cats[i];
            }
            return null;
        },

        categoryForIframe: function(src) {
            if (!src) return null;
            const u = String(src);
            const cats = ['marketing', 'functional'];
            for (let i = 0; i < cats.length; i++) {
                if (IFRAME_RULES[cats[i]].some(re => re.test(u))) return cats[i];
            }
            return null;
        },

        /**
         * Ist diese Kategorie fuer diese URL freigegeben? Beruecksichtigt die
         * gesonderte Drittland-Einwilligung fuer US-Anbieter.
         */
        isAllowed: function(category, url) {
            const c = this.state.consent;
            if (!c || !c.consent_categories) return false;
            const cat = c.consent_categories;
            if (cat[category] !== true) return false;
            if (url && US_HOSTS.test(this.hostOf(url)) && cat.third_country !== true) return false;
            return true;
        },

        hostOf: function(url) {
            try { return new URL(String(url), document.baseURI).hostname; } catch (e) { return ''; }
        },

        /**
         * Block scripts early (before DOMContentLoaded)
         */
        blockScriptsEarly: function() {
            const self = this;

            // Haken auf den PROTOTYPEN statt auf document.createElement: so greifen sie fuer jedes
            // Element, egal wie es entsteht (createElement, cloneNode, innerHTML-Fragmente,
            // Slider-Code, der createElement vorher gesichert hat).
            if (scriptSrcDesc && scriptSrcDesc.set && scriptSrcDesc.get) {
                Object.defineProperty(HTMLScriptElement.prototype, 'src', {
                    configurable: true,
                    enumerable: true,
                    get: function() { return scriptSrcDesc.get.call(this); },
                    set: function(value) {
                        if (self.shouldBlockScript(value)) {
                            self.neutralizeScript(this, value);
                            return;
                        }
                        scriptSrcDesc.set.call(this, value);
                    }
                });
            }
            if (linkHrefDesc && linkHrefDesc.set && linkHrefDesc.get) {
                Object.defineProperty(HTMLLinkElement.prototype, 'href', {
                    configurable: true,
                    enumerable: true,
                    get: function() { return linkHrefDesc.get.call(this); },
                    set: function(value) {
                        if (self.shouldBlockStylesheet(value)) {
                            self.neutralizeLink(this, value);
                            return;
                        }
                        linkHrefDesc.set.call(this, value);
                    }
                });
            }
            if (iframeSrcDesc && iframeSrcDesc.set && iframeSrcDesc.get) {
                Object.defineProperty(HTMLIFrameElement.prototype, 'src', {
                    configurable: true,
                    enumerable: true,
                    get: function() { return iframeSrcDesc.get.call(this); },
                    set: function(value) {
                        if (self.shouldBlockIframe(value)) {
                            self.neutralizeIframe(this, value);
                            return;
                        }
                        iframeSrcDesc.set.call(this, value);
                    }
                });
            }
            Element.prototype.setAttribute = function(name, value) {
                const n = String(name).toLowerCase();
                if (n === 'src' && this instanceof HTMLScriptElement && self.shouldBlockScript(value)) {
                    self.neutralizeScript(this, value);
                    return;
                }
                if (n === 'src' && this instanceof HTMLIFrameElement && self.shouldBlockIframe(value)) {
                    self.neutralizeIframe(this, value);
                    return;
                }
                if (n === 'href' && this instanceof HTMLLinkElement && self.shouldBlockStylesheet(value)) {
                    self.neutralizeLink(this, value);
                    return;
                }
                return nativeSetAttribute.call(this, name, value);
            };

            // Sofort vorhandene (bis hier geparste) Elemente neutralisieren …
            this.scanAndBlockScripts();
            this.scanAndBlockIframes();
            this.scanAndBlockStyles();
            // … und erneut nach vollstaendigem Parsen des restlichen DOM.
            const nachParsen = () => {
                this.scanAndBlockScripts();
                this.scanAndBlockIframes();
                this.scanAndBlockStyles();
                // Schon eingewilligt (wiederkehrender Besucher): server-seitig neutralisierte
                // Elemente jetzt freigeben, alle eingewilligten Kategorien.
                if (this.state.consent) this.unblockElements();
            };
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', nachParsen);
            } else {
                nachParsen();
            }
        },

        neutralizeScript: function(el, src) {
            console.log('[Complyo] 🚫 Blocked script:', src);
            const cat = this.categoryForScript(src) || 'marketing';
            nativeSetAttribute.call(el, 'type', 'text/plain');
            nativeSetAttribute.call(el, 'data-complyo-src', String(src));
            nativeSetAttribute.call(el, 'data-complyo-consent', cat);
            nativeSetAttribute.call(el, 'data-complyo-blocked', 'true');
            nativeRemoveAttribute.call(el, 'src');
            this.state.blockedElements.push(el);
        },

        neutralizeIframe: function(el, src) {
            console.log('[Complyo] 🚫 Blocked iframe:', src);
            const cat = this.categoryForIframe(src) || 'marketing';
            nativeSetAttribute.call(el, 'data-complyo-src', String(src));
            nativeSetAttribute.call(el, 'data-complyo-consent', cat);
            nativeSetAttribute.call(el, 'data-complyo-blocked', 'true');
            nativeRemoveAttribute.call(el, 'src');
            this.state.blockedElements.push(el);
        },

        neutralizeLink: function(el, href) {
            console.log('[Complyo] 🚫 Blocked stylesheet/font:', href);
            nativeSetAttribute.call(el, 'data-complyo-href', String(href));
            nativeSetAttribute.call(el, 'data-complyo-blocked', 'true');
            nativeSetAttribute.call(el, 'media', 'not all');
            nativeRemoveAttribute.call(el, 'href');
            this.state.blockedElements.push(el);
        },

        /**
         * Scan and block existing scripts
         */
        scanAndBlockScripts: function() {
            const scripts = document.querySelectorAll('script[src]');

            scripts.forEach(script => {
                const src = nativeGetAttribute.call(script, 'src');
                if (src && this.shouldBlockScript(src)) {
                    if (nativeGetAttribute.call(script, 'data-complyo-blocked') !== 'true') {
                        console.log('[Complyo] 🚫 Blocking existing script:', src);
                        this.neutralizeScript(script, src);
                    }
                }
            });
        },

        /**
         * Vorhandene iframes mit blockierten Zielen neutralisieren; den sichtbaren
         * Platzhalter (Banner-Gestaltung) baut der Content-Blocker des Widgets.
         */
        scanAndBlockIframes: function() {
            document.querySelectorAll('iframe[src]').forEach(frame => {
                const src = nativeGetAttribute.call(frame, 'src');
                if (src && nativeGetAttribute.call(frame, 'data-complyo-blocked') !== 'true' &&
                        this.shouldBlockIframe(src)) {
                    this.neutralizeIframe(frame, src);
                }
            });
        },

        /**
         * Check if script should be blocked
         */
        shouldBlockScript: function(src) {
            const cat = this.categoryForScript(src);
            if (!cat) return false;
            // Eingewilligte Kategorie (und ggf. Drittland) -> frei
            return !this.isAllowed(cat, src);
        },

        /**
         * Check if iframe should be blocked based on iframe src
         */
        shouldBlockIframe: function(src) {
            const cat = this.categoryForIframe(src);
            if (!cat) return false;
            return !this.isAllowed(cat, src);
        },

        /**
         * Soll diese URL (Stylesheet/Font) blockiert werden?
         */
        shouldBlockStylesheet: function(href) {
            if (!href) return false;
            if (!this.config.blockedStyles.some(pattern => pattern.test(href))) return false;
            return !this.isAllowed('functional', href);
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
                if (nativeGetAttribute.call(link, 'data-complyo-blocked') === 'true') return;
                const href = nativeGetAttribute.call(link, 'href');
                const rel  = (nativeGetAttribute.call(link, 'rel') || '').toLowerCase();
                const as   = (nativeGetAttribute.call(link, 'as')  || '').toLowerCase();
                const isStyleish = rel.includes('stylesheet') || as === 'font' ||
                                   rel === 'preload' || rel === 'prefetch' ||
                                   rel === 'preconnect' || rel === 'dns-prefetch';
                if (isStyleish && this.shouldBlockStylesheet(href)) {
                    console.log('[Complyo] 🚫 Blocking stylesheet/font link:', href);
                    nativeSetAttribute.call(link, 'data-complyo-rel', nativeGetAttribute.call(link, 'rel') || '');
                    this.neutralizeLink(link, href);
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
         * Alte Schnittstelle (Rueckwaertskompatibel): Einwilligung fuer ein Skript.
         */
        hasConsentForScript: function(src) {
            const cat = this.categoryForScript(src);
            return !!cat && this.isAllowed(cat, src);
        },

        /**
         * Alte Schnittstelle: Einwilligung fuer einen iframe.
         */
        hasConsentForIframe: function(src) {
            const cat = this.categoryForIframe(src);
            return !!cat && this.isAllowed(cat, src);
        },

        /**
         * Observe DOM for dynamically added elements
         */
        observeDOM: function() {
            const self = this;

            const pruefe = (node) => {
                if (node.nodeType !== 1) return;
                if (node.tagName === 'SCRIPT') {
                    const src = nativeGetAttribute.call(node, 'src');
                    if (src && self.shouldBlockScript(src) &&
                            nativeGetAttribute.call(node, 'data-complyo-blocked') !== 'true') {
                        console.log('[Complyo] 🚫 Blocking dynamically added script:', src);
                        self.neutralizeScript(node, src);
                    }
                } else if (node.tagName === 'IFRAME') {
                    const src = nativeGetAttribute.call(node, 'src');
                    if (src && self.shouldBlockIframe(src) &&
                            nativeGetAttribute.call(node, 'data-complyo-blocked') !== 'true') {
                        console.log('[Complyo] 🚫 Blocking iframe:', src);
                        self.neutralizeIframe(node, src);
                    }
                } else if (node.tagName === 'LINK' || node.tagName === 'STYLE') {
                    self.scanAndBlockStyles();
                }
                if (node.querySelectorAll) {
                    node.querySelectorAll('script[src], iframe[src]').forEach(pruefe);
                    if (node.querySelector('link[href], style')) {
                        self.scanAndBlockStyles();
                    }
                }
            };

            const observer = new MutationObserver(mutations => {
                mutations.forEach(mutation => mutation.addedNodes.forEach(pruefe));
            });

            observer.observe(document.documentElement, {
                childList: true,
                subtree: true
            });
        },

        /**
         * Unblock all blocked elements: sowohl die hier neutralisierten als auch die
         * serverseitig (WordPress-Plugin) vorab neutralisierten Skripte und iframes.
         */
        unblockElements: function() {
            console.log('[Complyo] ✅ Unblocking elements...');

            // Serverseitig neutralisierte Elemente einsammeln (nicht ueber den Haken entstanden).
            document.querySelectorAll(
                'script[type="text/plain"][data-complyo-consent], iframe[data-complyo-src][data-complyo-blocked="true"], ' +
                'link[data-complyo-href][data-complyo-blocked="true"]'
            ).forEach(el => {
                if (this.state.blockedElements.indexOf(el) === -1) this.state.blockedElements.push(el);
            });

            const rest = [];
            this.state.blockedElements.forEach(element => {
                if (!this.releaseElement(element)) rest.push(element);
            });
            this.state.blockedElements = rest;
        },

        /**
         * Gibt ein Element frei, wenn seine Kategorie eingewilligt ist.
         * true = erledigt (frei oder nicht mehr im Dokument), false = bleibt blockiert.
         */
        releaseElement: function(element) {
            // Platzhalter des Content-Blockers sind kein neutralisiertes Original.
            if (!element.isConnected) return true;

            if (element.tagName === 'SCRIPT') {
                const src = nativeGetAttribute.call(element, 'data-complyo-src');
                const cat = nativeGetAttribute.call(element, 'data-complyo-consent') ||
                    (src && this.categoryForScript(src));
                if (!cat || !this.isAllowed(cat, src || '')) return false;
                this.releaseScript(element, src);
                return true;
            }

            if (element.tagName === 'IFRAME') {
                const src = nativeGetAttribute.call(element, 'data-complyo-src');
                const cat = nativeGetAttribute.call(element, 'data-complyo-consent') ||
                    (src && this.categoryForIframe(src));
                if (!src || !cat || !this.isAllowed(cat, src)) return false;
                console.log('[Complyo] ✅ Unblocking iframe:', src);
                nativeRemoveAttribute.call(element, 'data-complyo-blocked');
                nativeRemoveAttribute.call(element, 'data-complyo-src');
                nativeRemoveAttribute.call(element, 'data-complyo-consent');
                element.style.display = '';
                iframeSrcDesc.set.call(element, src);
                return true;
            }

            if (element.tagName === 'LINK') {
                const originalHref = nativeGetAttribute.call(element, 'data-complyo-href');
                if (!originalHref || !this.isAllowed('functional', originalHref)) return false;
                console.log('[Complyo] ✅ Unblocking stylesheet/font:', originalHref);
                const originalRel = nativeGetAttribute.call(element, 'data-complyo-rel');
                nativeRemoveAttribute.call(element, 'media');
                if (originalRel) nativeSetAttribute.call(element, 'rel', originalRel);
                nativeRemoveAttribute.call(element, 'data-complyo-blocked');
                linkHrefDesc.set.call(element, originalHref);
                return true;
            }

            if (element.tagName === 'STYLE') {
                const originalCss = nativeGetAttribute.call(element, 'data-complyo-css');
                if (!originalCss || !this.hasConsentForStyle()) return false;
                console.log('[Complyo] ✅ Unblocking @import styles');
                element.textContent = originalCss;
                nativeRemoveAttribute.call(element, 'data-complyo-blocked');
                return true;
            }

            return true;
        },

        /**
         * Skript freigeben: IMMER durch ein neues Element ersetzen. Ein Skript, das der
         * Parser mit type="text/plain" angelegt hat, laeuft nicht, wenn man nachtraeglich
         * type/src setzt — nur ein frisch erzeugtes tut es. Inline-Code wird 1:1 uebernommen.
         */
        releaseScript: function(element, src) {
            if (!element.parentNode) return;
            const script = document.createElement('script');
            Array.prototype.forEach.call(element.attributes, attr => {
                if (attr.name.indexOf('data-complyo') !== 0 && attr.name !== 'type') {
                    nativeSetAttribute.call(script, attr.name, attr.value);
                }
            });
            if (src) {
                console.log('[Complyo] ✅ Unblocking script:', src);
                scriptSrcDesc.set.call(script, src);
            } else {
                script.text = element.textContent || '';
            }
            element.parentNode.replaceChild(script, element);
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
         * Load existing consent: erst der Schluessel des Banners (localStorage), dann das
         * aeltere Cookie. Reihenfolge, damit wiederkehrende Besucher mit Banner-Einwilligung
         * von der ersten Zeile an frei sind.
         */
        loadConsent: function() {
            try {
                let stored = null;
                try { stored = localStorage.getItem('complyo_cookie_consent'); } catch (e) {}
                if (stored) {
                    const c = JSON.parse(stored);
                    this.state.consent = {
                        accepted: !!(c.functional || c.analytics || c.marketing),
                        consent_categories: {
                            necessary: true,
                            functional: c.functional === true,
                            analytics: c.analytics === true,
                            marketing: c.marketing === true,
                            third_country: c.third_country === true
                        }
                    };
                    console.log('[Complyo] Loaded existing consent (Banner):', this.state.consent);
                    return;
                }
                const consentCookie = this.getCookie('complyo_consent');
                if (consentCookie) {
                    this.state.consent = JSON.parse(decodeURIComponent(consentCookie));
                    console.log('[Complyo] Loaded existing consent:', this.state.consent);
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
    // die Haken und der MutationObserver, bevor der Parser nachfolgende
    // <link>/<script>-Tags erreicht. Ein Warten auf DOMContentLoaded waere zu
    // spaet — statische Font-/Tracking-Ressourcen waeren dann laengst geladen.
    // init() startet selbst einen erneuten Scan auf DOMContentLoaded.
    ComplyoCookieBlocker.init();

    // Export to global scope
    window.ComplyoCookieBlocker = ComplyoCookieBlocker;

})();
