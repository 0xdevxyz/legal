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
      this._renderSettingsModal();
    }

    _getCategoryState() {
      const consent = this.loadConsent();
      return {
        necessary: true,
        functional: consent === 'all' || consent === 'functional',
        analytics: consent === 'all' || consent === 'analytics',
        marketing: consent === 'all',
      };
    }

    _renderSettingsModal() {
      const existing = document.getElementById('complyo-settings-modal');
      if (existing) existing.remove();

      const state = this._getCategoryState();
      const p = this.config.primaryColor;

      const categories = [
        {
          id: 'necessary',
          label: 'Notwendig',
          desc: 'Diese Cookies sind für den Betrieb der Website erforderlich und können nicht deaktiviert werden.',
          locked: true,
        },
        {
          id: 'functional',
          label: 'Funktional',
          desc: 'Ermöglichen erweiterte Funktionen wie gespeicherte Einstellungen und Sprachpräferenzen.',
          locked: false,
        },
        {
          id: 'analytics',
          label: 'Analytik',
          desc: 'Helfen uns zu verstehen, wie Besucher die Website nutzen (z.B. Google Analytics).',
          locked: false,
        },
        {
          id: 'marketing',
          label: 'Marketing',
          desc: 'Werden verwendet, um Ihnen relevante Werbung zu zeigen.',
          locked: false,
        },
      ];

      const modal = document.createElement('div');
      modal.id = 'complyo-settings-modal';

      const rows = categories.map(cat => {
        const checked = state[cat.id] ? 'checked' : '';
        const disabled = cat.locked ? 'disabled' : '';
        return `
          <div class="complyo-cat-row">
            <div class="complyo-cat-info">
              <div class="complyo-cat-label">${cat.label}${cat.locked ? ' <span class="complyo-cat-badge">Immer aktiv</span>' : ''}</div>
              <div class="complyo-cat-desc">${cat.desc}</div>
            </div>
            <label class="complyo-toggle ${cat.locked ? 'complyo-toggle-locked' : ''}">
              <input type="checkbox" id="complyo-cat-${cat.id}" ${checked} ${disabled}>
              <span class="complyo-slider"></span>
            </label>
          </div>`;
      }).join('');

      modal.innerHTML = `
        <style>
          #complyo-settings-modal {
            position: fixed; inset: 0; z-index: 1000000;
            display: flex; align-items: center; justify-content: center;
            background: rgba(0,0,0,0.5);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            animation: complyo-fadein 0.2s ease;
          }
          @keyframes complyo-fadein { from { opacity:0 } to { opacity:1 } }
          .complyo-modal-box {
            background: white; border-radius: 12px;
            width: 100%; max-width: 520px; max-height: 90vh;
            overflow-y: auto; padding: 28px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            margin: 16px;
          }
          .complyo-modal-header {
            display: flex; align-items: center; justify-content: space-between;
            margin-bottom: 20px;
          }
          .complyo-modal-title {
            font-size: 20px; font-weight: 700; color: #111;
          }
          .complyo-modal-close {
            background: none; border: none; cursor: pointer;
            font-size: 22px; color: #9ca3af; line-height: 1;
          }
          .complyo-modal-close:hover { color: #374151; }
          .complyo-modal-intro {
            font-size: 14px; color: #6b7280; margin-bottom: 20px; line-height: 1.6;
          }
          .complyo-cat-row {
            display: flex; align-items: flex-start; justify-content: space-between;
            gap: 16px; padding: 16px 0; border-bottom: 1px solid #f3f4f6;
          }
          .complyo-cat-row:last-child { border-bottom: none; }
          .complyo-cat-info { flex: 1; }
          .complyo-cat-label {
            font-size: 15px; font-weight: 600; color: #111; margin-bottom: 4px;
          }
          .complyo-cat-badge {
            font-size: 11px; font-weight: 500; color: ${p};
            background: ${p}1a; padding: 2px 6px; border-radius: 4px; margin-left: 6px;
          }
          .complyo-cat-desc { font-size: 13px; color: #6b7280; line-height: 1.5; }
          .complyo-toggle { position: relative; display: inline-block; width: 44px; height: 24px; flex-shrink: 0; }
          .complyo-toggle input { opacity: 0; width: 0; height: 0; }
          .complyo-slider {
            position: absolute; inset: 0; cursor: pointer;
            background: #d1d5db; border-radius: 24px; transition: 0.2s;
          }
          .complyo-slider:before {
            content: ""; position: absolute;
            width: 18px; height: 18px; left: 3px; bottom: 3px;
            background: white; border-radius: 50%; transition: 0.2s;
          }
          .complyo-toggle input:checked + .complyo-slider { background: ${p}; }
          .complyo-toggle input:checked + .complyo-slider:before { transform: translateX(20px); }
          .complyo-toggle-locked .complyo-slider { cursor: not-allowed; opacity: 0.7; }
          .complyo-modal-actions {
            display: flex; gap: 10px; margin-top: 24px; flex-wrap: wrap;
          }
          .complyo-modal-btn {
            padding: 10px 20px; border: none; border-radius: 6px;
            font-size: 14px; font-weight: 600; cursor: pointer; transition: all 0.2s; flex: 1;
          }
          .complyo-modal-btn-save {
            background: ${p}; color: white;
          }
          .complyo-modal-btn-save:hover { filter: brightness(1.1); }
          .complyo-modal-btn-all {
            background: #f3f4f6; color: #374151;
          }
          .complyo-modal-btn-all:hover { background: #e5e7eb; }
        </style>
        <div class="complyo-modal-box">
          <div class="complyo-modal-header">
            <div class="complyo-modal-title">Cookie-Einstellungen</div>
            <button class="complyo-modal-close" id="complyo-modal-close" aria-label="Schließen">&times;</button>
          </div>
          <div class="complyo-modal-intro">
            Wählen Sie, welche Cookies Sie zulassen möchten. Notwendige Cookies sind immer aktiv.
          </div>
          <div class="complyo-categories">${rows}</div>
          <div class="complyo-modal-actions">
            <button class="complyo-modal-btn complyo-modal-btn-all" id="complyo-modal-accept-all">Alle akzeptieren</button>
            <button class="complyo-modal-btn complyo-modal-btn-save" id="complyo-modal-save">Auswahl speichern</button>
          </div>
        </div>
      `;

      document.body.appendChild(modal);

      modal.querySelector('#complyo-modal-close').addEventListener('click', () => modal.remove());
      modal.addEventListener('click', (e) => { if (e.target === modal) modal.remove(); });

      modal.querySelector('#complyo-modal-accept-all').addEventListener('click', () => {
        this.acceptAll();
        modal.remove();
      });

      modal.querySelector('#complyo-modal-save').addEventListener('click', () => {
        const active = ['necessary'];
        ['functional', 'analytics', 'marketing'].forEach(id => {
          if (modal.querySelector(`#complyo-cat-${id}`).checked) active.push(id);
        });
        const level = active.includes('marketing') ? 'all'
          : active.includes('analytics') ? 'analytics'
          : active.includes('functional') ? 'functional'
          : 'necessary';
        this.saveConsent(level);
        this.hideBanner();
        this.enableCookies(active);
        this.trackEvent('consent_settings_saved');
        modal.remove();
      });
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

