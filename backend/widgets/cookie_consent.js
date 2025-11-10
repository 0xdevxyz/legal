/**
 * Complyo Cookie Consent Widget
 * DSGVO-konformes Cookie-Consent-Management
 * White-Label-Version (versteckt eRecht24 CCM19 im Hintergrund)
 */

(function() {
  'use strict';
  
  // Configuration
  const COMPLYO_API = 'https://api.complyo.tech';
  const WIDGET_VERSION = '1.0.0';
  
  class ComplyoCookieConsent {
    constructor(config = {}) {
      this.config = {
        siteId: config.siteId || this.getSiteIdFromScript(),
        position: config.position || 'bottom',
        primaryColor: config.primaryColor || '#6366f1',
        accentColor: config.accentColor || '#8b5cf6',
        language: config.language || 'de',
        ...config
      };
      
      this.consentGiven = this.loadConsent();
      this.init();
    }
    
    getSiteIdFromScript() {
      const script = document.currentScript || 
                     document.querySelector('script[data-site-id]');
      return script ? script.getAttribute('data-site-id') : null;
    }
    
    init() {
      if (this.consentGiven) {
        console.log('[Complyo] Cookie consent already given');
        return;
      }
      
      // Wait for DOM ready
      if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => this.render());
      } else {
        this.render();
      }
    }
    
    render() {
      const banner = this.createBanner();
      document.body.appendChild(banner);
      
      // Add animations
      setTimeout(() => banner.classList.add('complyo-show'), 100);
    }
    
    createBanner() {
      const banner = document.createElement('div');
      banner.id = 'complyo-cookie-banner';
      banner.className = `complyo-banner complyo-${this.config.position}`;
      
      banner.innerHTML = `
        <style>
          #complyo-cookie-banner {
            position: fixed;
            left: 0;
            right: 0;
            background: white;
            box-shadow: 0 -4px 20px rgba(0,0,0,0.15);
            padding: 20px;
            z-index: 999999;
            transform: translateY(100%);
            transition: transform 0.3s ease-out;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
          }
          #complyo-cookie-banner.complyo-bottom {
            bottom: 0;
          }
          #complyo-cookie-banner.complyo-top {
            top: 0;
            transform: translateY(-100%);
          }
          #complyo-cookie-banner.complyo-show {
            transform: translateY(0);
          }
          .complyo-content {
            max-width: 1200px;
            margin: 0 auto;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 20px;
            flex-wrap: wrap;
          }
          .complyo-text {
            flex: 1;
            min-width: 300px;
            color: #333;
            font-size: 14px;
            line-height: 1.6;
          }
          .complyo-text h3 {
            margin: 0 0 8px 0;
            font-size: 18px;
            font-weight: 600;
          }
          .complyo-text p {
            margin: 0;
          }
          .complyo-text a {
            color: ${this.config.primaryColor};
            text-decoration: underline;
          }
          .complyo-actions {
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
          }
          .complyo-btn {
            padding: 10px 24px;
            border: none;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
          }
          .complyo-btn-accept {
            background: ${this.config.primaryColor};
            color: white;
          }
          .complyo-btn-accept:hover {
            background: ${this.config.accentColor};
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
          }
          .complyo-btn-reject {
            background: #e5e7eb;
            color: #374151;
          }
          .complyo-btn-reject:hover {
            background: #d1d5db;
          }
          .complyo-btn-settings {
            background: transparent;
            color: #6b7280;
            border: 1px solid #d1d5db;
          }
          .complyo-btn-settings:hover {
            background: #f9fafb;
            border-color: #9ca3af;
          }
          
          @media (max-width: 768px) {
            .complyo-content {
              flex-direction: column;
              align-items: stretch;
            }
            .complyo-actions {
              width: 100%;
            }
            .complyo-btn {
              flex: 1;
            }
          }
        </style>
        
        <div class="complyo-content">
          <div class="complyo-text">
            <h3>🍪 Wir respektieren Ihre Privatsphäre</h3>
            <p>
              Wir verwenden Cookies, um Ihre Erfahrung zu verbessern. 
              Weitere Informationen finden Sie in unserer 
              <a href="/datenschutz" target="_blank">Datenschutzerklärung</a>.
            </p>
          </div>
          <div class="complyo-actions">
            <button class="complyo-btn complyo-btn-accept" id="complyo-accept">
              Alle akzeptieren
            </button>
            <button class="complyo-btn complyo-btn-reject" id="complyo-reject">
              Ablehnen
            </button>
            <button class="complyo-btn complyo-btn-settings" id="complyo-settings">
              Einstellungen
            </button>
          </div>
        </div>
      `;
      
      // Event listeners
      banner.querySelector('#complyo-accept').addEventListener('click', () => this.acceptAll());
      banner.querySelector('#complyo-reject').addEventListener('click', () => this.rejectAll());
      banner.querySelector('#complyo-settings').addEventListener('click', () => this.openSettings());
      
      return banner;
    }
    
    acceptAll() {
      this.saveConsent('all');
      this.hideBanner();
      this.enableCookies(['necessary', 'analytics', 'marketing']);
      this.trackEvent('consent_accepted');
    }
    
    rejectAll() {
      this.saveConsent('necessary');
      this.hideBanner();
      this.enableCookies(['necessary']);
      this.trackEvent('consent_rejected');
    }
    
    openSettings() {
      // TODO: Open detailed cookie settings modal
      alert('Cookie-Einstellungen werden in Kürze verfügbar sein.');
    }
    
    hideBanner() {
      const banner = document.getElementById('complyo-cookie-banner');
      if (banner) {
        banner.classList.remove('complyo-show');
        setTimeout(() => banner.remove(), 300);
      }
    }
    
    saveConsent(level) {
      localStorage.setItem('complyo_consent', level);
      localStorage.setItem('complyo_consent_date', new Date().toISOString());
    }
    
    loadConsent() {
      return localStorage.getItem('complyo_consent');
    }
    
    enableCookies(categories) {
      // Trigger event for analytics/marketing scripts
      window.dispatchEvent(new CustomEvent('complyoConsent', {
        detail: { categories }
      }));
      
      console.log('[Complyo] Enabled cookies:', categories);
    }
    
    trackEvent(eventName) {
      if (!this.config.siteId) return;
      
      // Send to Complyo API
      fetch(`${COMPLYO_API}/api/widgets/track`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          siteId: this.config.siteId,
          event: eventName,
          timestamp: new Date().toISOString()
        })
      }).catch(err => console.warn('[Complyo] Tracking failed:', err));
    }
  }
  
  // Auto-initialize if data-site-id is present
  if (document.currentScript && document.currentScript.getAttribute('data-site-id')) {
    new ComplyoCookieConsent();
  }
  
  // Export for manual initialization
  window.ComplyoCookieConsent = ComplyoCookieConsent;
  
  console.log(`[Complyo] Cookie Consent Widget v${WIDGET_VERSION} loaded`);
})();

