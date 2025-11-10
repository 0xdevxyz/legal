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
    
    // Blocked domains by category
    const BLOCKED_DOMAINS = {
        analytics: [
            'google-analytics.com',
            'googletagmanager.com',
            'analytics.tiktok.com',
            'matomo.org',
            'matomo.js',
            'piwik.js',
            'hotjar.com'
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
            'platform.twitter.com'
        ],
        functional: [
            'google.com/maps',
            'maps.googleapis.com',
            'intercom.io',
            'widget.intercom.io',
            'zdassets.com',
            'zendesk.com',
            'fonts.googleapis.com'
        ]
    };
    
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
            // Listen for consent events
            window.addEventListener('complyoConsent', (e) => {
                this.consent = e.detail.categories;
                console.log('[Complyo Content Blocker] Consent received:', this.consent);
                this.unblockContent();
            });
            
            // Listen for DOM loaded
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', () => this.onDOMReady());
            } else {
                this.onDOMReady();
            }
        }
        
        onDOMReady() {
            // Check if consent already exists
            this.consent = this.loadConsentFromStorage();
            
            if (this.consent) {
                // Consent already given - unblock immediately
                console.log('[Complyo Content Blocker] Consent found, unblocking...');
                this.unblockContent();
            } else {
                // No consent yet - block everything
                console.log('[Complyo Content Blocker] No consent, blocking content...');
                this.blockAllContent();
                
                // Watch for dynamically added content
                this.observeDOM();
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
                        marketing: consent.marketing || false
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
            
            this.observer.observe(document.body, {
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
            
            // Block iframes
            this.blockIframes();
            
            // Block images (tracking pixels)
            this.blockImages();
            
            // Block data-attribute elements
            this.blockDataAttributes();
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
                    } else {
                        // Generic blocking
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
                
                // Only block tracking pixels (small images from analytics/marketing domains)
                if (category && !this.hasConsent(category)) {
                    const width = img.width || img.naturalWidth;
                    const height = img.height || img.naturalHeight;
                    
                    // Likely a tracking pixel
                    if (width <= 1 && height <= 1) {
                        img.removeAttribute('src');
                        img.setAttribute('data-complyo-consent', category);
                        img.setAttribute('data-complyo-src', src);
                        img.setAttribute('data-complyo-blocked', 'true');
                        
                        this.blockedElements.set(img, {
                            type: 'image',
                            category: category,
                            originalSrc: src
                        });
                        
                        console.log(`[Complyo] Blocked tracking pixel: ${src} (${category})`);
                    }
                }
                
                img.setAttribute('data-complyo-processed', 'true');
            });
        }
        
        blockDataAttributes() {
            // Block elements with data-complyo-consent attribute
            const elements = document.querySelectorAll('[data-complyo-consent]');
            
            elements.forEach(element => {
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
                
                if (this.hasConsent(category)) {
                    this.unblockElement(element, data);
                }
            });
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
            }
            
            // Remove from blocked list
            this.blockedElements.delete(element);
        }
        
        unblockScript(element, data) {
            const src = element.getAttribute('data-complyo-src');
            
            if (src) {
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
                <div class="complyo-placeholder-title">${service.name} Video</div>
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
            
            const urlLower = url.toLowerCase();
            
            // Check each category
            for (const [category, domains] of Object.entries(BLOCKED_DOMAINS)) {
                for (const domain of domains) {
                    if (urlLower.includes(domain)) {
                        return category;
                    }
                }
            }
            
            return null;
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
        
        // ====================================================================
        // Public API
        // ====================================================================
        
        updateConsent(consent) {
            this.consent = consent;
            this.unblockContent();
        }
        
        blockAgain() {
            this.consent = null;
            location.reload(); // Easiest way to re-block everything
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

