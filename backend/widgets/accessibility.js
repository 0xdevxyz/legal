/**
 * Complyo Accessibility Widget v4.0
 * Overlay-Lösung für sofortige Barrierefreiheit
 * 
 * Features:
 * - Toggle-Interface (wie AccessiBe/UserWay)
 * - Analytics-Tracking für Upsell-Insights
 * - LocalStorage für User-Präferenzen
 * - Keine Code-Anzeige (nur für Website-Besucher)
 * 
 * © 2025 Complyo.tech
 */

(function() {
  'use strict';
  
  const WIDGET_VERSION = '4.0.0';
  const API_BASE = window.location.hostname === 'localhost' ? 'http://localhost:8000' : 'https://api.complyo.tech';
  
  class ComplyoAccessibilityWidget {
    constructor(config = {}) {
      this.config = {
        siteId: config.siteId || this.getSiteIdFromScript(),
        showToolbar: config.showToolbar !== false,
        position: config.position || 'bottom-right'
      };
      
      this.features = {
        fontSize: 100,
        lineHeight: 1.5,
        contrast: false,
        highlightLinks: false,
        readableFont: false,
        stopAnimations: false,
        bigCursor: false
      };
      
      this.sessionId = this.generateSessionId();
      this.isOpen = false;
      
      this.init();
    }
    
    async init() {
      // Load preferences from localStorage
      this.loadPreferences();
      
      // Render toolbar
      this.renderToolbar();
      
      // Apply saved features
      this.applyAllFeatures();
      
      // Inject CSS
      this.injectCSS();
      
      // Load and apply AI-generated alt texts
      await this.loadAndApplyAltTexts();
      
      console.log(`🎨 Complyo Accessibility Widget v${WIDGET_VERSION} initialized`);
    }
    
    getSiteIdFromScript() {
      const script = document.currentScript || document.querySelector('script[data-site-id]');
      return script ? script.getAttribute('data-site-id') : 'demo';
    }
    
    generateSessionId() {
      return 'sess_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    renderToolbar() {
      // Create container
      const container = document.createElement('div');
      container.id = 'complyo-a11y-widget';
      container.className = `complyo-widget-${this.config.position}`;
      
      container.innerHTML = `
        <button class="complyo-toggle-btn" aria-label="Barrierefreiheitsoptionen öffnen" aria-expanded="false">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z"/>
          </svg>
        </button>
        
        <div class="complyo-panel" hidden aria-label="Barrierefreiheitsoptionen">
          <div class="complyo-panel-header">
            <h3>♿ Barrierefreiheit</h3>
            <button class="complyo-close-btn" aria-label="Schließen">✕</button>
          </div>
          
          <div class="complyo-panel-content">
            <!-- Text-Sektion -->
            <div class="complyo-section">
              <h4>📝 Text</h4>
              
              <div class="complyo-control">
                <label for="complyo-font-size">
                  Schriftgröße: <span id="complyo-font-size-value">100%</span>
                </label>
                <input 
                  type="range" 
                  id="complyo-font-size" 
                  min="80" 
                  max="200" 
                  step="10" 
                  value="100"
                  aria-label="Schriftgröße anpassen"
                >
              </div>
              
              <div class="complyo-control">
                <label for="complyo-line-height">
                  Zeilenabstand: <span id="complyo-line-height-value">1.5</span>
                </label>
                <input 
                  type="range" 
                  id="complyo-line-height" 
                  min="1.0" 
                  max="2.5" 
                  step="0.1" 
                  value="1.5"
                  aria-label="Zeilenabstand anpassen"
                >
              </div>
            </div>
            
            <!-- Anzeige-Sektion -->
            <div class="complyo-section">
              <h4>🎨 Anzeige</h4>
              
              <label class="complyo-checkbox">
                <input type="checkbox" id="complyo-contrast" aria-label="Hoher Kontrast aktivieren">
                <span>Hoher Kontrast</span>
              </label>
              
              <label class="complyo-checkbox">
                <input type="checkbox" id="complyo-highlight-links" aria-label="Links hervorheben">
                <span>Links hervorheben</span>
              </label>
              
              <label class="complyo-checkbox">
                <input type="checkbox" id="complyo-readable-font" aria-label="Lesbare Schriftart aktivieren">
                <span>Lesbare Schriftart</span>
              </label>
              
              <label class="complyo-checkbox">
                <input type="checkbox" id="complyo-stop-animations" aria-label="Animationen stoppen">
                <span>Animationen stoppen</span>
              </label>
            </div>
            
            <!-- Navigation-Sektion -->
            <div class="complyo-section">
              <h4>🖱️ Navigation</h4>
              
              <label class="complyo-checkbox">
                <input type="checkbox" id="complyo-big-cursor" aria-label="Großen Cursor aktivieren">
                <span>Großer Cursor</span>
              </label>
            </div>
            
            <!-- Reset-Button -->
            <div class="complyo-section">
              <button class="complyo-reset-btn">🔄 Zurücksetzen</button>
            </div>
          </div>
          
          <div class="complyo-panel-footer">
            <p>Powered by <a href="https://complyo.tech" target="_blank" rel="noopener">Complyo</a></p>
          </div>
        </div>
      `;
      
      document.body.appendChild(container);
      this.container = container;
      
      // Attach event listeners
      this.attachEventListeners();
      
      // Set initial values
      this.updateUIValues();
    }
    
    attachEventListeners() {
      const toggleBtn = this.container.querySelector('.complyo-toggle-btn');
      const closeBtn = this.container.querySelector('.complyo-close-btn');
      const panel = this.container.querySelector('.complyo-panel');
      const resetBtn = this.container.querySelector('.complyo-reset-btn');
      
      // Toggle panel
      toggleBtn.addEventListener('click', () => {
        this.isOpen = !this.isOpen;
        panel.hidden = !this.isOpen;
        toggleBtn.setAttribute('aria-expanded', this.isOpen.toString());
      });
      
      // Close panel
      closeBtn.addEventListener('click', () => {
        this.isOpen = false;
        panel.hidden = true;
        toggleBtn.setAttribute('aria-expanded', 'false');
      });
      
      // Font size
      const fontSizeInput = this.container.querySelector('#complyo-font-size');
      fontSizeInput.addEventListener('input', (e) => {
        this.features.fontSize = parseInt(e.target.value);
        this.updateUIValues();
        this.applyFeature('fontSize');
        this.savePreferences();
        this.trackFeatureUsage('fontSize', this.features.fontSize);
      });
      
      // Line height
      const lineHeightInput = this.container.querySelector('#complyo-line-height');
      lineHeightInput.addEventListener('input', (e) => {
        this.features.lineHeight = parseFloat(e.target.value);
        this.updateUIValues();
        this.applyFeature('lineHeight');
        this.savePreferences();
        this.trackFeatureUsage('lineHeight', this.features.lineHeight);
      });
      
      // Checkboxes
      const checkboxes = {
        'complyo-contrast': 'contrast',
        'complyo-highlight-links': 'highlightLinks',
        'complyo-readable-font': 'readableFont',
        'complyo-stop-animations': 'stopAnimations',
        'complyo-big-cursor': 'bigCursor'
      };
      
      Object.entries(checkboxes).forEach(([id, feature]) => {
        const checkbox = this.container.querySelector(`#${id}`);
        checkbox.addEventListener('change', (e) => {
          this.features[feature] = e.target.checked;
          this.applyFeature(feature);
          this.savePreferences();
          this.trackFeatureUsage(feature, this.features[feature]);
        });
      });
      
      // Reset button
      resetBtn.addEventListener('click', () => {
        this.resetAllFeatures();
      });
      
      // Close on Escape
      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && this.isOpen) {
          this.isOpen = false;
          panel.hidden = true;
          toggleBtn.setAttribute('aria-expanded', 'false');
          toggleBtn.focus();
        }
      });
    }
    
    updateUIValues() {
      // Update range displays
      const fontSizeValue = this.container.querySelector('#complyo-font-size-value');
      const lineHeightValue = this.container.querySelector('#complyo-line-height-value');
      
      fontSizeValue.textContent = `${this.features.fontSize}%`;
      lineHeightValue.textContent = this.features.lineHeight.toFixed(1);
      
      // Update range inputs
      this.container.querySelector('#complyo-font-size').value = this.features.fontSize;
      this.container.querySelector('#complyo-line-height').value = this.features.lineHeight;
      
      // Update checkboxes
      this.container.querySelector('#complyo-contrast').checked = this.features.contrast;
      this.container.querySelector('#complyo-highlight-links').checked = this.features.highlightLinks;
      this.container.querySelector('#complyo-readable-font').checked = this.features.readableFont;
      this.container.querySelector('#complyo-stop-animations').checked = this.features.stopAnimations;
      this.container.querySelector('#complyo-big-cursor').checked = this.features.bigCursor;
    }
    
    applyFeature(feature) {
      const body = document.body;
      
      switch(feature) {
        case 'fontSize':
          body.style.fontSize = `${this.features.fontSize}%`;
          break;
          
        case 'lineHeight':
          body.style.lineHeight = this.features.lineHeight;
          break;
          
        case 'contrast':
          body.classList.toggle('complyo-high-contrast', this.features.contrast);
          break;
          
        case 'highlightLinks':
          body.classList.toggle('complyo-highlight-links', this.features.highlightLinks);
          break;
          
        case 'readableFont':
          body.classList.toggle('complyo-readable-font', this.features.readableFont);
          break;
          
        case 'stopAnimations':
          body.classList.toggle('complyo-stop-animations', this.features.stopAnimations);
          break;
          
        case 'bigCursor':
          body.classList.toggle('complyo-big-cursor', this.features.bigCursor);
          break;
      }
    }
    
    applyAllFeatures() {
      Object.keys(this.features).forEach(feature => {
        this.applyFeature(feature);
      });
    }
    
    resetAllFeatures() {
      this.features = {
        fontSize: 100,
        lineHeight: 1.5,
        contrast: false,
        highlightLinks: false,
        readableFont: false,
        stopAnimations: false,
        bigCursor: false
      };
      
      this.applyAllFeatures();
      this.updateUIValues();
      this.savePreferences();
      this.trackFeatureUsage('reset', true);
    }
    
    savePreferences() {
      try {
        localStorage.setItem('complyo_a11y_prefs', JSON.stringify(this.features));
      } catch (e) {
        console.warn('Failed to save preferences:', e);
      }
    }
    
    loadPreferences() {
      try {
        const saved = localStorage.getItem('complyo_a11y_prefs');
        if (saved) {
          this.features = { ...this.features, ...JSON.parse(saved) };
        }
      } catch (e) {
        console.warn('Failed to load preferences:', e);
      }
    }
    
    trackFeatureUsage(feature, value) {
      // Sendet anonyme Nutzungsdaten für Upsell-Insights
      const data = {
        site_id: this.config.siteId,
        feature: feature,
        value: value,
        timestamp: Date.now(),
        session_id: this.sessionId
      };
      
      fetch(`${API_BASE}/api/widgets/analytics`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
      }).catch(() => {
        // Silent fail - analytics shouldn't break the widget
      });
    }
    
    async loadAndApplyAltTexts() {
      /**
       * Lädt AI-generierte Alt-Texte vom Backend und fügt sie runtime ins DOM ein
       * Dies ist der Hybrid-Ansatz: Widget funktioniert sofort, Alt-Texte werden nachgeladen
       */
      try {
        const response = await fetch(
          `${API_BASE}/api/accessibility/alt-text-fixes?site_id=${this.config.siteId}`
        );
        
        if (!response.ok) {
          console.warn('Alt-Text-Fixes konnten nicht geladen werden:', response.status);
          return;
        }
        
        const data = await response.json();
        
        if (data.success && data.fixes && data.fixes.length > 0) {
          this.applyAltTextFixes(data.fixes);
          console.log(`✅ ${data.fixes.length} Alt-Texte angewendet (runtime)`);
        }
      } catch (e) {
        console.warn('Fehler beim Laden der Alt-Text-Fixes:', e);
        // Silent fail - sollte Widget nicht blockieren
      }
    }
    
    applyAltTextFixes(fixes) {
      /**
       * Wendet Alt-Text-Fixes auf Bilder an
       * Unterstützt verschiedene Bild-Formate (normal, lazy-loading, responsive)
       */
      fixes.forEach(fix => {
        // Verschiedene Selektoren für verschiedene Bild-Implementierungen
        const selectors = [
          `img[src="${fix.image_src}"]`,  // Normales Bild
          `img[src*="${fix.image_filename}"]`,  // Dateiname im Pfad
          `img[data-src="${fix.image_src}"]`,  // Lazy loading
          `img[srcset*="${fix.image_filename}"]`  // Responsive images
        ];
        
        for (const selector of selectors) {
          try {
            const images = document.querySelectorAll(selector);
            images.forEach(img => {
              // Nur wenn noch kein Alt-Text vorhanden
              if (!img.alt || img.alt.trim() === '') {
                img.setAttribute('alt', fix.suggested_alt);
                img.setAttribute('data-complyo-alt', 'runtime');
                img.setAttribute('title', fix.suggested_alt); // Zusätzlich als Tooltip
              }
            });
          } catch (e) {
            console.warn(`Fehler bei Selector ${selector}:`, e);
          }
        }
      });
      
      // Beobachte dynamisch nachgeladene Bilder (für SPAs)
      this.observeNewImages(fixes);
    }
    
    observeNewImages(fixes) {
      /**
       * MutationObserver für dynamisch nachgeladene Bilder
       * Wichtig für Single-Page Applications und Lazy Loading
       */
      if (this.imageObserver) {
        return; // Observer läuft bereits
      }
      
      this.imageObserver = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
          mutation.addedNodes.forEach((node) => {
            // Prüfe ob es ein img-Element ist
            if (node.tagName === 'IMG') {
              this.applyAltTextFixes(fixes);
            }
            // Prüfe ob es ein Container mit Bildern ist
            else if (node.querySelectorAll) {
              const images = node.querySelectorAll('img');
              if (images.length > 0) {
                this.applyAltTextFixes(fixes);
              }
            }
          });
        });
      });
      
      this.imageObserver.observe(document.body, {
        childList: true,
        subtree: true
      });
    }
    
    injectCSS() {
      const style = document.createElement('style');
      style.textContent = `
        /* Complyo Accessibility Widget v4.0 Styles */
        
        #complyo-a11y-widget {
          position: fixed;
          z-index: 999999;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }
        
        .complyo-widget-bottom-right {
          bottom: 100px;
          right: 30px;
        }
        
        .complyo-toggle-btn {
          width: 60px;
          height: 60px;
          border-radius: 50%;
          background: linear-gradient(135deg, #7c3aed 0%, #5b21b6 100%);
          border: none;
          color: white;
          cursor: pointer;
          box-shadow: 0 4px 12px rgba(124, 58, 237, 0.4);
          transition: transform 0.2s, box-shadow 0.2s;
          display: flex;
          align-items: center;
          justify-content: center;
        }
        
        .complyo-toggle-btn:hover {
          transform: scale(1.05);
          box-shadow: 0 6px 16px rgba(124, 58, 237, 0.5);
        }
        
        .complyo-toggle-btn:focus {
          outline: 3px solid #7c3aed;
          outline-offset: 3px;
        }
        
        .complyo-panel {
          position: absolute;
          bottom: 75px;
          right: 0;
          width: 320px;
          max-height: 600px;
          background: white;
          border-radius: 12px;
          box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
          overflow: hidden;
          animation: slideUp 0.3s ease;
        }
        
        @keyframes slideUp {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        
        .complyo-panel-header {
          background: linear-gradient(135deg, #7c3aed 0%, #5b21b6 100%);
          color: white;
          padding: 16px;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        
        .complyo-panel-header h3 {
          margin: 0;
          font-size: 18px;
          font-weight: 600;
        }
        
        .complyo-close-btn {
          background: none;
          border: none;
          color: white;
          font-size: 24px;
          cursor: pointer;
          padding: 0;
          width: 32px;
          height: 32px;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: 4px;
          transition: background 0.2s;
        }
        
        .complyo-close-btn:hover {
          background: rgba(255, 255, 255, 0.2);
        }
        
        .complyo-panel-content {
          padding: 16px;
          max-height: 480px;
          overflow-y: auto;
        }
        
        .complyo-section {
          margin-bottom: 20px;
          padding-bottom: 20px;
          border-bottom: 1px solid #e5e7eb;
        }
        
        .complyo-section:last-child {
          border-bottom: none;
          margin-bottom: 0;
        }
        
        .complyo-section h4 {
          margin: 0 0 12px 0;
          font-size: 14px;
          font-weight: 600;
          color: #374151;
        }
        
        .complyo-control {
          margin-bottom: 16px;
        }
        
        .complyo-control label {
          display: flex;
          justify-content: space-between;
          margin-bottom: 8px;
          font-size: 14px;
          color: #4b5563;
        }
        
        .complyo-control input[type="range"] {
          width: 100%;
          height: 6px;
          border-radius: 3px;
          background: #e5e7eb;
          outline: none;
          -webkit-appearance: none;
        }
        
        .complyo-control input[type="range"]::-webkit-slider-thumb {
          -webkit-appearance: none;
          width: 18px;
          height: 18px;
          border-radius: 50%;
          background: #7c3aed;
          cursor: pointer;
          box-shadow: 0 2px 4px rgba(124, 58, 237, 0.3);
        }
        
        .complyo-control input[type="range"]::-moz-range-thumb {
          width: 18px;
          height: 18px;
          border-radius: 50%;
          background: #7c3aed;
          cursor: pointer;
          border: none;
          box-shadow: 0 2px 4px rgba(124, 58, 237, 0.3);
        }
        
        .complyo-checkbox {
          display: flex;
          align-items: center;
          margin-bottom: 12px;
          cursor: pointer;
          font-size: 14px;
          color: #4b5563;
        }
        
        .complyo-checkbox input[type="checkbox"] {
          width: 20px;
          height: 20px;
          margin-right: 10px;
          cursor: pointer;
          accent-color: #7c3aed;
        }
        
        .complyo-reset-btn {
          width: 100%;
          padding: 12px;
          background: #f3f4f6;
          border: 1px solid #d1d5db;
          border-radius: 8px;
          color: #374151;
          font-size: 14px;
          font-weight: 500;
          cursor: pointer;
          transition: background 0.2s, border-color 0.2s;
        }
        
        .complyo-reset-btn:hover {
          background: #e5e7eb;
          border-color: #9ca3af;
        }
        
        .complyo-panel-footer {
          padding: 12px 16px;
          background: #f9fafb;
          text-align: center;
          font-size: 12px;
          color: #6b7280;
        }
        
        .complyo-panel-footer a {
          color: #7c3aed;
          text-decoration: none;
        }
        
        .complyo-panel-footer a:hover {
          text-decoration: underline;
        }
        
        /* Feature Styles */
        body.complyo-high-contrast {
          filter: contrast(1.5) brightness(1.1);
        }
        
        /* ⚠️ WICHTIG: Widget selbst vom Kontrast-Filter ausnehmen */
        body.complyo-high-contrast #complyo-a11y-widget {
          filter: none !important;
          isolation: isolate;
        }
        
        /* Sicherstellen dass der Button immer sichtbar bleibt */
        body.complyo-high-contrast .complyo-toggle-btn {
          background: #7c3aed !important;
          color: white !important;
          box-shadow: 0 4px 12px rgba(124, 58, 237, 0.4) !important;
        }
        
        /* Panel auch normal darstellen */
        body.complyo-high-contrast .complyo-panel {
          filter: none !important;
          background: white !important;
          color: #1f2937 !important;
        }
        
        body.complyo-highlight-links a {
          background-color: #fef3c7 !important;
          padding: 2px 4px !important;
          border-radius: 2px !important;
        }
        
        body.complyo-readable-font,
        body.complyo-readable-font * {
          font-family: 'Arial', 'Helvetica', sans-serif !important;
        }
        
        body.complyo-stop-animations * {
          animation-duration: 0s !important;
          animation-delay: 0s !important;
          transition-duration: 0s !important;
        }
        
        body.complyo-big-cursor,
        body.complyo-big-cursor * {
          cursor: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32"><path fill="black" stroke="white" stroke-width="2" d="M2 2 L2 28 L12 20 L17 30 L22 28 L17 18 L28 18 Z"/></svg>') 0 0, auto !important;
        }
        
        /* Responsive */
        @media (max-width: 480px) {
          .complyo-panel {
            width: calc(100vw - 40px);
            right: 20px;
            left: 20px;
          }
        }
      `;
      
      document.head.appendChild(style);
    }
  }
  
  // Auto-initialize when script is loaded
  // ✅ FIX: Warte immer auf DOMContentLoaded für async/defer Scripts
  function initWidget() {
    // Suche nach Widget-Script mit data-site-id
    const script = document.currentScript || 
                   document.querySelector('script[src*="accessibility.js"][data-site-id]') ||
                   document.querySelector('script[data-site-id]');
    
    if (script && script.hasAttribute('data-site-id')) {
      console.log('🚀 Initializing Complyo Widget with site-id:', script.getAttribute('data-site-id'));
      new ComplyoAccessibilityWidget({
        siteId: script.getAttribute('data-site-id'),
        showToolbar: script.getAttribute('data-show-toolbar') !== 'false'
      });
    } else {
      console.warn('⚠️ Complyo Widget: No script tag with data-site-id found');
    }
  }
  
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initWidget);
  } else {
    // DOM already loaded - init immediately
    initWidget();
  }
})();
