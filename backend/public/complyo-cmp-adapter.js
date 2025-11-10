/**
 * Complyo CMP Adapter
 * Cookie-Consent-Management ohne nerviges Overlay
 * 
 * Features:
 * - Blockiert Tracking-Scripts bis zur Einwilligung
 * - Google Consent Mode v2 kompatibel
 * - Minimal-invasiv, kein UI-Overlay
 * - TTDSG §25 konform
 * 
 * @version 1.0.0
 * @license MIT
 */

(function () {
  'use strict';

  console.log('🍪 Complyo CMP Adapter v1.0.0 loading...');

  // Registry bekannter Tracking-Dienste
  const cookieRegistry = [
    { id: 'ga4', test: /googletagmanager\.com|gtag\/js/, category: 'analytics' },
    { id: 'google-ads', test: /doubleclick\.net|googleads/, category: 'ads' },
    { id: 'facebook-pixel', test: /facebook\.com\/tr|connect\.facebook\.net/, category: 'marketing' },
    { id: 'tiktok-pixel', test: /tiktok\.com\/i18n\/pixel/, category: 'marketing' },
    { id: 'linkedin-insights', test: /snap\.licdn\.com/, category: 'marketing' },
    { id: 'hotjar', test: /static\.hotjar\.com/, category: 'analytics' },
    { id: 'matomo', test: /matomo\.js|piwik\.js/, category: 'analytics' },
    { id: 'hubspot', test: /js\.hs-scripts\.com/, category: 'marketing' }
  ];

  // Script-Blocker: Intercepte createElement für <script>-Tags
  const originalCreateElement = document.createElement.bind(document);
  
  document.createElement = function (tagName) {
    const element = originalCreateElement(tagName);
    
    if (tagName.toLowerCase() === 'script') {
      const originalSetAttribute = element.setAttribute.bind(element);
      
      element.setAttribute = function (attrName, attrValue) {
        if (attrName === 'src') {
          const match = cookieRegistry.find(service => 
            service.test.test(String(attrValue))
          );
          
          if (match && !window.__complyoConsentGranted?.[match.category]) {
            // Script blockieren
            (window.__complyoBlockedScripts ||= []).push({
              element: element,
              attr: [attrName, attrValue],
              service: match
            });
            
            console.log(`🛑 Blocked: ${match.id} (${match.category}) - waiting for consent`);
            return; // Verhindere das Setzen des src-Attributs
          }
        }
        
        return originalSetAttribute(attrName, attrValue);
      };
    }
    
    return element;
  };

  // Google Consent Mode v2 initialisieren
  window.dataLayer = window.dataLayer || [];
  function gtag() {
    dataLayer.push(arguments);
  }
  
  // Default: Alles abgelehnt
  gtag('consent', 'default', {
    ad_user_data: 'denied',
    ad_personalization: 'denied',
    ad_storage: 'denied',
    analytics_storage: 'denied',
    functionality_storage: 'denied',
    personalization_storage: 'denied',
    security_storage: 'granted' // Sicherheit immer erlaubt
  });

  /**
   * Public API: Consent anwenden
   * 
   * @param {Object} grants - Consent-Entscheidungen
   * @param {boolean} grants.analytics - Google Analytics, Matomo etc.
   * @param {boolean} grants.ads - Google Ads, Doubleclick
   * @param {boolean} grants.marketing - Facebook, TikTok, LinkedIn
   * @param {boolean} grants.functional - Funktionale Cookies (z.B. Warenkorb)
   * 
   * @example
   * window.complyoApplyConsent({
   *   analytics: true,
   *   ads: false,
   *   marketing: false,
   *   functional: true
   * });
   */
  window.complyoApplyConsent = function (grants) {
    if (!grants || typeof grants !== 'object') {
      console.error('❌ complyoApplyConsent: Invalid grants object');
      return;
    }

    window.__complyoConsentGranted = grants;

    // Google Consent Mode v2 aktualisieren
    gtag('consent', 'update', {
      analytics_storage: grants.analytics ? 'granted' : 'denied',
      ad_storage: grants.ads ? 'granted' : 'denied',
      ad_personalization: grants.marketing ? 'granted' : 'denied',
      ad_user_data: grants.marketing ? 'granted' : 'denied',
      functionality_storage: grants.functional ? 'granted' : 'denied',
      personalization_storage: grants.marketing ? 'granted' : 'denied'
    });

    // Blockierte Scripts nachladen
    const blockedScripts = window.__complyoBlockedScripts || [];
    let loadedCount = 0;

    blockedScripts.forEach(({ element, attr, service }) => {
      if (grants[service.category]) {
        element.setAttribute(attr[0], attr[1]);
        document.head.appendChild(element);
        loadedCount++;
        console.log(`✅ Loaded: ${service.id} (${service.category})`);
      }
    });

    // Liste leeren
    window.__complyoBlockedScripts = [];

    console.log(`✅ Consent applied: ${loadedCount} scripts loaded`, grants);

    // Event dispatchen für eigene Listeners
    window.dispatchEvent(new CustomEvent('complyoConsentApplied', {
      detail: { grants, scriptsLoaded: loadedCount }
    }));
  };

  /**
   * Helper: Consent aus LocalStorage laden
   * 
   * @returns {Object|null} Gespeicherter Consent oder null
   */
  window.complyoLoadConsent = function () {
    try {
      const stored = localStorage.getItem('complyo_consent');
      return stored ? JSON.parse(stored) : null;
    } catch (e) {
      console.error('❌ Error loading consent from localStorage:', e);
      return null;
    }
  };

  /**
   * Helper: Consent in LocalStorage speichern
   * 
   * @param {Object} grants - Consent-Entscheidungen
   */
  window.complyoSaveConsent = function (grants) {
    try {
      localStorage.setItem('complyo_consent', JSON.stringify(grants));
      localStorage.setItem('complyo_consent_timestamp', Date.now().toString());
    } catch (e) {
      console.error('❌ Error saving consent to localStorage:', e);
    }
  };

  /**
   * Helper: Consent zurücksetzen
   */
  window.complyoResetConsent = function () {
    localStorage.removeItem('complyo_consent');
    localStorage.removeItem('complyo_consent_timestamp');
    location.reload();
  };

  // Auto-Load gespeicherter Consent (optional)
  const savedConsent = window.complyoLoadConsent();
  if (savedConsent) {
    console.log('ℹ️ Auto-loading saved consent...');
    window.complyoApplyConsent(savedConsent);
  }

  console.log('✅ Complyo CMP Adapter loaded successfully');
  console.log('📚 Usage: window.complyoApplyConsent({ analytics: true, ads: false, ... })');
})();

