/**
 * Complyo Smart Accessibility Widget v2.0
 * 
 * Zwei-Ebenen-Ansatz:
 * 1. Enhancement-Layer: User-Präferenzen (legitim)
 * 2. Fix-Layer: Automatische Barrierefreiheits-Reparaturen (Code-Injection)
 * 
 * © 2025 Complyo.tech - WCAG 2.1 Level AA Compliance
 */

(function() {
  'use strict';
  
  const VERSION = '2.0.0';
  const API_BASE_URL = 'https://api.complyo.tech/v1';
  
  /**
   * Hauptklasse für Smart Accessibility
   */
  class ComplyoSmartAccessibility {
    constructor(config = {}) {
      this.config = {
        siteId: config.siteId || this.getSiteIdFromScript(),
        apiKey: config.apiKey || null,
        autoFix: config.autoFix !== false, // Default: true
        showToolbar: config.showToolbar !== false, // Default: true
        features: config.features || ['all'],
        debug: config.debug || false,
        ...config
      };
      
      this.fixes = {
        alt_text_fixes: [],
        aria_fixes: [],
        contrast_fixes: [],
        focus_fixes: [],
        keyboard_fixes: []
      };
      
      this.state = {
        initialized: false,
        fixesLoaded: false,
        fixesApplied: 0
      };
      
      this.init();
    }
    
    /**
     * Initialisierung
     */
    async init() {
      this.log('🚀 Initializing Complyo Smart Accessibility Widget v' + VERSION);
      
      if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => this.start());
      } else {
        this.start();
      }
    }
    
    /**
     * Startet Widget nach DOM-Ready
     */
    async start() {
      try {
        // 1. Lade Fix-Definitionen von API
        if (this.config.autoFix) {
          await this.loadFixes();
        }
        
        // 2. Wende Auto-Fixes an
        if (this.config.autoFix && this.state.fixesLoaded) {
          this.applyAutoFixes();
        }
        
        // 3. Render Enhancement-Toolbar
        if (this.config.showToolbar) {
          this.renderToolbar();
        }
        
        // 4. Lade User-Präferenzen
        this.loadUserPreferences();
        
        this.state.initialized = true;
        this.log('✅ Widget initialized successfully');
        
        // Trigger custom event
        window.dispatchEvent(new CustomEvent('complyo-initialized', {
          detail: { version: VERSION, fixesApplied: this.state.fixesApplied }
        }));
        
      } catch (error) {
        this.error('Initialization failed:', error);
      }
    }
    
    /**
     * Lädt Fix-Definitionen von Complyo API
     */
    async loadFixes() {
      if (!this.config.siteId) {
        this.warn('No site ID configured, skipping auto-fixes');
        return;
      }
      
      try {
        const url = `${API_BASE_URL}/sites/${this.config.siteId}/accessibility-fixes`;
        const headers = {};
        
        if (this.config.apiKey) {
          headers['Authorization'] = `Bearer ${this.config.apiKey}`;
        }
        
        this.log('📥 Loading fixes from API...');
        
        const response = await fetch(url, {
          method: 'GET',
          headers: headers,
          cache: 'default'
        });
        
        if (!response.ok) {
          throw new Error(`API returned ${response.status}`);
        }
        
        this.fixes = await response.json();
        this.state.fixesLoaded = true;
        
        this.log(`✅ Loaded ${this.countTotalFixes()} fixes from API`);
        
      } catch (error) {
        this.warn('Failed to load fixes from API:', error);
        // Continue without API fixes (toolbar still works)
      }
    }
    
    /**
     * Wendet alle Auto-Fixes an
     */
    applyAutoFixes() {
      this.log('🔧 Applying auto-fixes...');
      
      let count = 0;
      
      // 1. Alt-Text Fixes
      count += this.applyAltTextFixes();
      
      // 2. ARIA-Label Fixes
      count += this.applyAriaFixes();
      
      // 3. Kontrast-Fixes (CSS)
      count += this.applyContrastFixes();
      
      // 4. Focus-Indikatoren
      count += this.applyFocusFixes();
      
      // 5. Keyboard-Navigation
      count += this.applyKeyboardFixes();
      
      this.state.fixesApplied = count;
      this.log(`✅ Applied ${count} auto-fixes`);
    }
    
    /**
     * Wendet Alt-Text-Fixes an
     */
    applyAltTextFixes() {
      if (!this.fixes.alt_text_fixes || !Array.isArray(this.fixes.alt_text_fixes)) {
        return 0;
      }
      
      let count = 0;
      
      this.fixes.alt_text_fixes.forEach(fix => {
        try {
          const img = document.querySelector(fix.selector);
          if (img && !img.alt) {
            img.setAttribute('alt', fix.alt);
            img.setAttribute('data-complyo-fixed', 'alt-text');
            count++;
          }
        } catch (e) {
          this.warn('Alt-text fix failed for selector:', fix.selector, e);
        }
      });
      
      this.log(`Applied ${count} alt-text fixes`);
      return count;
    }
    
    /**
     * Wendet ARIA-Label-Fixes an
     */
    applyAriaFixes() {
      if (!this.fixes.aria_fixes || !Array.isArray(this.fixes.aria_fixes)) {
        return 0;
      }
      
      let count = 0;
      
      this.fixes.aria_fixes.forEach(fix => {
        try {
          const elements = document.querySelectorAll(fix.selector);
          elements.forEach(el => {
            if (!el.getAttribute('aria-label')) {
              el.setAttribute('aria-label', fix['aria-label']);
              el.setAttribute('data-complyo-fixed', 'aria-label');
              count++;
            }
          });
        } catch (e) {
          this.warn('ARIA fix failed for selector:', fix.selector, e);
        }
      });
      
      this.log(`Applied ${count} ARIA fixes`);
      return count;
    }
    
    /**
     * Wendet Kontrast-Fixes an (CSS-Injection)
     */
    applyContrastFixes() {
      if (!this.fixes.contrast_fixes || !Array.isArray(this.fixes.contrast_fixes)) {
        return 0;
      }
      
      if (this.fixes.contrast_fixes.length === 0) {
        return 0;
      }
      
      const style = document.createElement('style');
      style.id = 'complyo-contrast-fixes';
      style.setAttribute('data-complyo-version', VERSION);
      
      const cssRules = this.fixes.contrast_fixes
        .map(fix => `${fix.selector} { color: ${fix.color} !important; }`)
        .join('\n');
      
      style.textContent = `/* Complyo Auto-Fixes: Contrast */\n${cssRules}`;
      document.head.appendChild(style);
      
      this.log(`Applied ${this.fixes.contrast_fixes.length} contrast fixes`);
      return this.fixes.contrast_fixes.length;
    }
    
    /**
     * Wendet Focus-Indikator-Fixes an
     */
    applyFocusFixes() {
      const style = document.createElement('style');
      style.id = 'complyo-focus-fixes';
      style.setAttribute('data-complyo-version', VERSION);
      
      style.textContent = `
        /* Complyo Auto-Fixes: Focus Indicators */
        *:focus-visible {
          outline: 3px solid #3b82f6 !important;
          outline-offset: 2px !important;
        }
        
        /* Skip-Link */
        .complyo-skip-link {
          position: absolute;
          left: -9999px;
          z-index: 999999;
          padding: 1rem 1.5rem;
          background: #3b82f6;
          color: white;
          font-weight: bold;
          text-decoration: none;
          border-radius: 0 0 4px 4px;
        }
        
        .complyo-skip-link:focus {
          left: 50%;
          top: 0;
          transform: translateX(-50%);
        }
      `;
      
      document.head.appendChild(style);
      
      // Skip-Link hinzufügen
      const skipLink = document.createElement('a');
      skipLink.href = '#main';
      skipLink.textContent = 'Zum Hauptinhalt springen';
      skipLink.className = 'complyo-skip-link';
      skipLink.setAttribute('data-complyo-fixed', 'skip-link');
      document.body.insertBefore(skipLink, document.body.firstChild);
      
      // Versuche main-Element zu finden oder markieren
      let main = document.querySelector('main, [role="main"], #main, #content');
      if (main && !main.id) {
        main.id = 'main';
      }
      
      this.log('Applied focus fixes');
      return 2; // Style + Skip-Link
    }
    
    /**
     * Verbessert Keyboard-Navigation
     */
    applyKeyboardFixes() {
      let count = 0;
      
      // Alle klickbaren Elemente ohne tabindex
      const clickables = document.querySelectorAll('[onclick]:not([tabindex]), [data-click]:not([tabindex])');
      
      clickables.forEach(el => {
        if (!el.getAttribute('tabindex')) {
          el.setAttribute('tabindex', '0');
          el.setAttribute('data-complyo-fixed', 'keyboard-nav');
          
          if (!el.getAttribute('role')) {
            el.setAttribute('role', 'button');
          }
          
          // Enter/Space handler
          el.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              this.click();
            }
          });
          
          count++;
        }
      });
      
      this.log(`Applied keyboard fixes to ${count} elements`);
      return count;
    }
    
    /**
     * Rendert Enhancement-Toolbar
     */
    renderToolbar() {
      const toolbar = document.createElement('div');
      toolbar.id = 'complyo-a11y-toolbar';
      toolbar.setAttribute('data-complyo-version', VERSION);
      toolbar.setAttribute('role', 'region');
      toolbar.setAttribute('aria-label', 'Barrierefreiheits-Einstellungen');
      
      toolbar.innerHTML = `
        <style>
          #complyo-a11y-toolbar {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
            padding: 16px;
            z-index: 999998;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            min-width: 260px;
            max-width: 320px;
          }
          
          #complyo-a11y-toolbar.collapsed {
            min-width: auto;
            padding: 12px;
          }
          
          #complyo-a11y-toolbar.collapsed .toolbar-content {
            display: none;
          }
          
          .complyo-toolbar-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
          }
          
          .complyo-toolbar-title {
            font-size: 14px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
          }
          
          .complyo-toolbar-toggle {
            background: none;
            border: none;
            cursor: pointer;
            padding: 4px;
            color: #6b7280;
          }
          
          .complyo-control {
            margin-bottom: 12px;
          }
          
          .complyo-control:last-child {
            margin-bottom: 0;
          }
          
          .complyo-label {
            display: block;
            font-size: 12px;
            color: #6b7280;
            margin-bottom: 4px;
            font-weight: 500;
          }
          
          .complyo-btn {
            width: 100%;
            padding: 8px;
            border: 1px solid #d1d5db;
            border-radius: 6px;
            background: white;
            cursor: pointer;
            font-size: 13px;
            transition: all 0.2s;
            text-align: left;
          }
          
          .complyo-btn:hover {
            background: #f3f4f6;
            border-color: #9ca3af;
          }
          
          .complyo-btn.active {
            background: #3b82f6;
            color: white;
            border-color: #3b82f6;
          }
          
          .complyo-slider {
            width: 100%;
            height: 6px;
            border-radius: 3px;
            background: #e5e7eb;
            appearance: none;
            outline: none;
          }
          
          .complyo-slider::-webkit-slider-thumb {
            appearance: none;
            width: 16px;
            height: 16px;
            border-radius: 50%;
            background: #3b82f6;
            cursor: pointer;
          }
          
          .complyo-slider::-moz-range-thumb {
            width: 16px;
            height: 16px;
            border-radius: 50%;
            background: #3b82f6;
            cursor: pointer;
            border: none;
          }
          
          .complyo-badge {
            display: inline-block;
            background: #10b981;
            color: white;
            font-size: 10px;
            padding: 2px 6px;
            border-radius: 4px;
            font-weight: 600;
          }
        </style>
        
        <div class="complyo-toolbar-header">
          <div class="complyo-toolbar-title">
            ♿ Barrierefreiheit
            <span class="complyo-badge">BFSG</span>
          </div>
          <button class="complyo-toolbar-toggle" aria-label="Toolbar minimieren" onclick="document.getElementById('complyo-a11y-toolbar').classList.toggle('collapsed')">
            <svg width="20" height="20" fill="currentColor"><path d="M6 9l6 6 6-6"/></svg>
          </button>
        </div>
        
        <div class="toolbar-content">
          <div class="complyo-control">
            <label class="complyo-label">
              Schriftgröße: <span id="font-size-value">100%</span>
            </label>
            <input 
              type="range" 
              min="80" 
              max="150" 
              value="100" 
              class="complyo-slider" 
              id="font-size-slider"
              aria-label="Schriftgröße anpassen"
            >
          </div>
          
          <div class="complyo-control">
            <label class="complyo-label">Kontrast</label>
            <button class="complyo-btn" id="contrast-toggle" aria-pressed="false">
              ⚪ Normal
            </button>
          </div>
          
          <div class="complyo-control">
            <label class="complyo-label">Zeilenabstand</label>
            <button class="complyo-btn" id="line-height-toggle" aria-pressed="false">
              ≡ Normal
            </button>
          </div>
          
          <div class="complyo-control">
            <button class="complyo-btn" id="reset-a11y">
              Zurücksetzen
            </button>
          </div>
          
          <div style="text-align: center; margin-top: 12px;">
            <a href="https://complyo.tech" target="_blank" style="font-size: 11px; color: #9ca3af; text-decoration: none;">
              Powered by Complyo
            </a>
          </div>
        </div>
      `;
      
      document.body.appendChild(toolbar);
      this.attachToolbarEvents();
      
      this.log('Toolbar rendered');
    }
    
    /**
     * Bindet Toolbar-Events
     */
    attachToolbarEvents() {
      const fontSlider = document.getElementById('font-size-slider');
      const fontValue = document.getElementById('font-size-value');
      const contrastBtn = document.getElementById('contrast-toggle');
      const lineHeightBtn = document.getElementById('line-height-toggle');
      const resetBtn = document.getElementById('reset-a11y');
      
      if (fontSlider) {
        fontSlider.addEventListener('input', (e) => {
          const size = e.target.value;
          this.setFontSize(size);
          if (fontValue) fontValue.textContent = `${size}%`;
        });
      }
      
      if (contrastBtn) {
        contrastBtn.addEventListener('click', () => {
          this.toggleContrast();
          const active = document.body.classList.contains('complyo-high-contrast');
          contrastBtn.classList.toggle('active', active);
          contrastBtn.textContent = active ? '⚫ Hoher Kontrast' : '⚪ Normal';
          contrastBtn.setAttribute('aria-pressed', active);
        });
      }
      
      if (lineHeightBtn) {
        lineHeightBtn.addEventListener('click', () => {
          this.toggleLineHeight();
          const active = document.documentElement.classList.contains('complyo-large-line-height');
          lineHeightBtn.classList.toggle('active', active);
          lineHeightBtn.textContent = active ? '≡ Groß' : '≡ Normal';
          lineHeightBtn.setAttribute('aria-pressed', active);
        });
      }
      
      if (resetBtn) {
        resetBtn.addEventListener('click', () => {
          this.reset();
          if (fontSlider) fontSlider.value = 100;
          if (fontValue) fontValue.textContent = '100%';
          if (contrastBtn) {
            contrastBtn.classList.remove('active');
            contrastBtn.textContent = '⚪ Normal';
            contrastBtn.setAttribute('aria-pressed', 'false');
          }
          if (lineHeightBtn) {
            lineHeightBtn.classList.remove('active');
            lineHeightBtn.textContent = '≡ Normal';
            lineHeightBtn.setAttribute('aria-pressed', 'false');
          }
        });
      }
    }
    
    /**
     * Setzt Schriftgröße
     */
    setFontSize(size) {
      document.documentElement.style.fontSize = `${size}%`;
      this.savePreference('fontSize', size);
    }
    
    /**
     * Toggelt Kontrast-Modus
     */
    toggleContrast() {
      document.body.classList.toggle('complyo-high-contrast');
      const active = document.body.classList.contains('complyo-high-contrast');
      
      if (active && !document.getElementById('complyo-contrast-style')) {
        const style = document.createElement('style');
        style.id = 'complyo-contrast-style';
        style.textContent = `
          body.complyo-high-contrast {
            filter: contrast(1.2);
          }
          body.complyo-high-contrast a {
            text-decoration: underline !important;
            font-weight: 500;
          }
        `;
        document.head.appendChild(style);
      }
      
      this.savePreference('contrast', active ? 'high' : 'normal');
    }
    
    /**
     * Toggelt Zeilenabstand
     */
    toggleLineHeight() {
      document.documentElement.classList.toggle('complyo-large-line-height');
      const active = document.documentElement.classList.contains('complyo-large-line-height');
      
      if (active && !document.getElementById('complyo-line-height-style')) {
        const style = document.createElement('style');
        style.id = 'complyo-line-height-style';
        style.textContent = `
          html.complyo-large-line-height * {
            line-height: 1.8 !important;
          }
        `;
        document.head.appendChild(style);
      }
      
      this.savePreference('lineHeight', active ? 'large' : 'normal');
    }
    
    /**
     * Reset auf Standardwerte
     */
    reset() {
      document.documentElement.style.fontSize = '';
      document.body.classList.remove('complyo-high-contrast');
      document.documentElement.classList.remove('complyo-large-line-height');
      localStorage.removeItem('complyo_a11y_prefs');
    }
    
    /**
     * Speichert Präferenz in localStorage
     */
    savePreference(key, value) {
      try {
        const prefs = JSON.parse(localStorage.getItem('complyo_a11y_prefs') || '{}');
        prefs[key] = value;
        localStorage.setItem('complyo_a11y_prefs', JSON.stringify(prefs));
      } catch (e) {
        this.warn('Failed to save preference:', e);
      }
    }
    
    /**
     * Lädt gespeicherte Präferenzen
     */
    loadUserPreferences() {
      try {
        const prefs = JSON.parse(localStorage.getItem('complyo_a11y_prefs') || '{}');
        
        if (prefs.fontSize) {
          this.setFontSize(prefs.fontSize);
          const slider = document.getElementById('font-size-slider');
          const value = document.getElementById('font-size-value');
          if (slider) slider.value = prefs.fontSize;
          if (value) value.textContent = `${prefs.fontSize}%`;
        }
        
        if (prefs.contrast === 'high') {
          this.toggleContrast();
          const btn = document.getElementById('contrast-toggle');
          if (btn) {
            btn.classList.add('active');
            btn.textContent = '⚫ Hoher Kontrast';
            btn.setAttribute('aria-pressed', 'true');
          }
        }
        
        if (prefs.lineHeight === 'large') {
          this.toggleLineHeight();
          const btn = document.getElementById('line-height-toggle');
          if (btn) {
            btn.classList.add('active');
            btn.textContent = '≡ Groß';
            btn.setAttribute('aria-pressed', 'true');
          }
        }
        
      } catch (e) {
        this.warn('Failed to load preferences:', e);
      }
    }
    
    // Utility-Methoden
    
    getSiteIdFromScript() {
      const script = document.currentScript || 
                     document.querySelector('script[data-complyo-a11y], script[data-site-id]');
      return script ? script.getAttribute('data-site-id') : null;
    }
    
    countTotalFixes() {
      return (this.fixes.alt_text_fixes?.length || 0) +
             (this.fixes.aria_fixes?.length || 0) +
             (this.fixes.contrast_fixes?.length || 0);
    }
    
    log(...args) {
      if (this.config.debug) {
        console.log('[Complyo A11y]', ...args);
      }
    }
    
    warn(...args) {
      console.warn('[Complyo A11y]', ...args);
    }
    
    error(...args) {
      console.error('[Complyo A11y]', ...args);
    }
  }
  
  // Auto-Initialisierung wenn data-site-id vorhanden
  if (document.currentScript && document.currentScript.getAttribute('data-site-id')) {
    window.ComplyoAccessibility = new ComplyoSmartAccessibility({
      siteId: document.currentScript.getAttribute('data-site-id'),
      autoFix: document.currentScript.getAttribute('data-auto-fix') !== 'false',
      debug: document.currentScript.getAttribute('data-debug') === 'true'
    });
  }
  
  // Export für manuelle Initialisierung
  window.ComplyoSmartAccessibility = ComplyoSmartAccessibility;
  
  console.log(`[Complyo] Smart Accessibility Widget v${VERSION} loaded`);
  
})();

