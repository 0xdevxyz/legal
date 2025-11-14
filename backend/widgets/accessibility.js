/**
 * Complyo Accessibility Widget v2.0
 * Vollständige WCAG 2.1 AA/AAA konforme Barrierefreiheits-Lösung
 * Real code-based accessibility enhancements (NO OVERLAY!)
 */

(function() {
  'use strict';
  
  const WIDGET_VERSION = '2.0.0';
  const COMPLYO_API = 'https://api.complyo.tech';
  
  class ComplyoAccessibility {
    constructor(config = {}) {
      this.config = {
        siteId: config.siteId || this.getSiteIdFromScript(),
        features: config.features || ['all'],
        autoFix: config.autoFix !== false,
        showToolbar: config.showToolbar !== false,
        ...config
      };
      
      this.state = {
        fontSize: 100,
        lineHeight: 1.5,
        letterSpacing: 0,
        contrast: 'normal',
        highlightLinks: false,
        readableFont: false,
        stopAnimations: false,
        bigCursor: false,
        isMinimized: false
      };
      
      this.init();
    }
    
    getSiteIdFromScript() {
      const script = document.currentScript || 
                     document.querySelector('script[src*="accessibility.js"]');
      return script ? script.getAttribute('data-site-id') : null;
    }
    
    init() {
      if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => this.applyFixes());
      } else {
        this.applyFixes();
      }
    }
    
    applyFixes() {
      console.log('[Complyo A11y] Applying accessibility fixes...');
      
      // Apply base CSS fixes
      this.injectBaseStyles();
      
      // Apply enabled features
      if (this.config.autoFix) {
        this.improveKeyboardNavigation();
        this.addSkipLinks();
        this.fixMissingAltTexts();
        this.fixFormLabels();
        this.addAriaLabels();
      }
      
      if (this.config.showToolbar) {
        this.renderToolbar();
      }
      
      this.loadUserPreferences();
      
      console.log('[Complyo A11y] Fixes applied successfully');
    }
    
    injectBaseStyles() {
      const style = document.createElement('style');
      style.id = 'complyo-base-styles';
      style.textContent = `
        /* Complyo Accessibility: Base Styles */
        
        /* High Contrast Mode */
        body.complyo-high-contrast {
          filter: contrast(1.3);
        }
        
        body.complyo-high-contrast a {
          text-decoration: underline !important;
          font-weight: 500 !important;
        }
        
        body.complyo-high-contrast button {
          border: 2px solid currentColor !important;
        }
        
        /* Highlight Links */
        body.complyo-highlight-links a {
          background: #ffeb3b !important;
          color: #000 !important;
          padding: 2px 4px !important;
          text-decoration: underline !important;
          font-weight: 600 !important;
        }
        
        /* Readable Font */
        body.complyo-readable-font,
        body.complyo-readable-font * {
          font-family: Arial, Helvetica, sans-serif !important;
        }
        
        /* Stop Animations */
        body.complyo-stop-animations *,
        body.complyo-stop-animations *::before,
        body.complyo-stop-animations *::after {
          animation-duration: 0.01ms !important;
          animation-iteration-count: 1 !important;
          transition-duration: 0.01ms !important;
          scroll-behavior: auto !important;
        }
        
        /* Big Cursor */
        body.complyo-big-cursor,
        body.complyo-big-cursor * {
          cursor: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewport="0 0 40 40"><circle cx="20" cy="20" r="18" fill="black" opacity="0.8"/><circle cx="20" cy="20" r="15" fill="white"/></svg>') 20 20, auto !important;
        }
        
        /* Enhanced Focus Indicators */
        body.complyo-enhanced-focus *:focus {
          outline: 3px solid #6366f1 !important;
          outline-offset: 3px !important;
          box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2) !important;
        }
        
        /* Line Height Adjustment */
        body.complyo-line-height-15 * { line-height: 1.5 !important; }
        body.complyo-line-height-20 * { line-height: 2.0 !important; }
        body.complyo-line-height-25 * { line-height: 2.5 !important; }
        
        /* Letter Spacing */
        body.complyo-letter-spacing-1 * { letter-spacing: 0.1em !important; }
        body.complyo-letter-spacing-2 * { letter-spacing: 0.2em !important; }
      `;
      document.head.appendChild(style);
    }
    
    improveKeyboardNavigation() {
      const interactiveSelectors = 'a, button, input, select, textarea, [onclick], [role="button"]';
      const elements = document.querySelectorAll(interactiveSelectors);
      
      elements.forEach(el => {
        if (!el.hasAttribute('tabindex') && !['A', 'BUTTON', 'INPUT', 'SELECT', 'TEXTAREA'].includes(el.tagName)) {
          el.setAttribute('tabindex', '0');
        }
      });
      
      // Enable Enter key for clickable elements
      document.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && e.target.hasAttribute('onclick') && !e.target.closest('a, button')) {
          e.target.click();
        }
      });
      
      // Add enhanced focus
      document.body.classList.add('complyo-enhanced-focus');
    }
    
    addSkipLinks() {
      const skipLink = document.createElement('a');
      skipLink.href = '#main-content';
      skipLink.textContent = 'Zum Hauptinhalt springen';
      skipLink.id = 'complyo-skip-link';
      skipLink.style.cssText = `
        position: absolute;
        top: -100px;
        left: 0;
        background: #6366f1;
        color: white;
        padding: 12px 24px;
        text-decoration: none;
        font-weight: bold;
        font-size: 16px;
        z-index: 999999;
        transition: top 0.2s;
        border-radius: 0 0 8px 0;
      `;
      
      skipLink.addEventListener('focus', () => {
        skipLink.style.top = '0';
      });
      
      skipLink.addEventListener('blur', () => {
        skipLink.style.top = '-100px';
      });
      
      document.body.insertBefore(skipLink, document.body.firstChild);
      
      // Add id to main content if not present
      const main = document.querySelector('main, [role="main"], #main, #content, .main-content');
      if (main && !main.id) {
        main.id = 'main-content';
      }
    }
    
    fixMissingAltTexts() {
      const images = document.querySelectorAll('img:not([alt])');
      
      images.forEach(img => {
        const src = img.src || '';
        const filename = src.split('/').pop().split('.')[0];
        const altText = img.title || filename.replace(/[-_]/g, ' ') || 'Bild';
        
        img.setAttribute('alt', altText);
        img.setAttribute('data-complyo-alt-generated', 'true');
      });
      
      if (images.length > 0) {
        console.log(`[Complyo A11y] Fixed ${images.length} missing alt texts`);
      }
    }
    
    fixFormLabels() {
      const inputs = document.querySelectorAll('input:not([type="hidden"]), select, textarea');
      
      inputs.forEach(input => {
        if (!input.id) {
          input.id = `complyo-input-${Math.random().toString(36).substr(2, 9)}`;
        }
        
        const existingLabel = document.querySelector(`label[for="${input.id}"]`);
        if (!existingLabel && !input.getAttribute('aria-label')) {
          const placeholder = input.placeholder || input.name || 'Eingabefeld';
          input.setAttribute('aria-label', placeholder);
        }
      });
    }
    
    addAriaLabels() {
      // Add ARIA labels to common elements without accessible names
      const buttons = document.querySelectorAll('button:not([aria-label]):not(:has(text))');
      buttons.forEach(btn => {
        const title = btn.title || btn.getAttribute('data-title') || 'Button';
        btn.setAttribute('aria-label', title);
      });
      
      const links = document.querySelectorAll('a:not([aria-label]):empty');
      links.forEach(link => {
        const title = link.title || link.href || 'Link';
        link.setAttribute('aria-label', title);
      });
    }
    
    renderToolbar() {
      const toolbar = document.createElement('div');
      toolbar.id = 'complyo-a11y-toolbar';
      toolbar.innerHTML = `
        <style>
          #complyo-a11y-toolbar {
            position: fixed;
            top: 20px;
            right: 20px;
            background: white;
            border-radius: 16px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.2);
            z-index: 2147483647;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            max-width: 320px;
            transition: all 0.3s ease;
          }
          
          #complyo-a11y-toolbar.minimized {
            max-width: 60px;
          }
          
          .complyo-a11y-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 16px;
            border-bottom: 1px solid #e5e7eb;
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
            color: white;
            border-radius: 16px 16px 0 0;
            cursor: pointer;
          }
          
          .complyo-a11y-title {
            font-size: 16px;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 8px;
          }
          
          #complyo-a11y-toolbar.minimized .complyo-a11y-title span {
            display: none;
          }
          
          .complyo-a11y-toggle {
            background: rgba(255,255,255,0.2);
            border: none;
            color: white;
            width: 28px;
            height: 28px;
            border-radius: 50%;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
            transition: all 0.2s;
          }
          
          .complyo-a11y-toggle:hover {
            background: rgba(255,255,255,0.3);
            transform: scale(1.1);
          }
          
          #complyo-a11y-toolbar.minimized .complyo-a11y-toggle {
            display: none;
          }
          
          .complyo-a11y-content {
            padding: 16px;
            max-height: 70vh;
            overflow-y: auto;
            scrollbar-width: thin;
            scrollbar-color: #6366f1 #e5e7eb;
          }
          
          #complyo-a11y-toolbar.minimized .complyo-a11y-content {
            display: none;
          }
          
          .complyo-a11y-content::-webkit-scrollbar {
            width: 6px;
          }
          
          .complyo-a11y-content::-webkit-scrollbar-track {
            background: #f1f1f1;
          }
          
          .complyo-a11y-content::-webkit-scrollbar-thumb {
            background: #6366f1;
            border-radius: 3px;
          }
          
          .complyo-a11y-section {
            margin-bottom: 20px;
          }
          
          .complyo-a11y-section:last-child {
            margin-bottom: 0;
          }
          
          .complyo-a11y-section-title {
            font-size: 13px;
            font-weight: 600;
            color: #374151;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
          }
          
          .complyo-a11y-control {
            margin-bottom: 12px;
          }
          
          .complyo-a11y-control:last-child {
            margin-bottom: 0;
          }
          
          .complyo-a11y-label {
            display: block;
            font-size: 13px;
            color: #6b7280;
            margin-bottom: 6px;
            font-weight: 500;
          }
          
          .complyo-a11y-btn {
            width: 100%;
            padding: 10px 12px;
            border: 2px solid #e5e7eb;
            border-radius: 8px;
            background: white;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 8px;
          }
          
          .complyo-a11y-btn:hover {
            background: #f9fafb;
            border-color: #6366f1;
            transform: translateY(-1px);
          }
          
          .complyo-a11y-btn.active {
            background: #6366f1;
            color: white;
            border-color: #6366f1;
          }
          
          .complyo-a11y-btn.active::after {
            content: '✓';
            font-weight: bold;
          }
          
          .complyo-a11y-slider-container {
            display: flex;
            align-items: center;
            gap: 8px;
          }
          
          .complyo-a11y-slider {
            flex: 1;
            height: 8px;
            border-radius: 4px;
            background: #e5e7eb;
            appearance: none;
            outline: none;
            cursor: pointer;
          }
          
          .complyo-a11y-slider::-webkit-slider-thumb {
            appearance: none;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: #6366f1;
            cursor: pointer;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
          }
          
          .complyo-a11y-slider::-moz-range-thumb {
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: #6366f1;
            cursor: pointer;
            border: none;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
          }
          
          .complyo-a11y-value {
            min-width: 50px;
            text-align: right;
            font-size: 13px;
            font-weight: 600;
            color: #6366f1;
          }
          
          .complyo-a11y-reset {
            width: 100%;
            padding: 12px;
            background: #ef4444;
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            margin-top: 16px;
            transition: all 0.2s;
          }
          
          .complyo-a11y-reset:hover {
            background: #dc2626;
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(239, 68, 68, 0.3);
          }
          
          .complyo-a11y-branding {
            text-align: center;
            padding: 12px;
            font-size: 11px;
            color: #9ca3af;
            border-top: 1px solid #e5e7eb;
          }
          
          .complyo-a11y-branding a {
            color: #6366f1;
            text-decoration: none;
            font-weight: 600;
          }
        </style>
        
        <div class="complyo-a11y-header" onclick="document.getElementById('complyo-a11y-toolbar').classList.toggle('minimized')">
          <div class="complyo-a11y-title">
            <span>♿</span>
            <span>Barrierefreiheit</span>
          </div>
          <button class="complyo-a11y-toggle" aria-label="Minimieren">−</button>
        </div>
        
        <div class="complyo-a11y-content">
          <!-- Text Section -->
          <div class="complyo-a11y-section">
            <div class="complyo-a11y-section-title">📝 Text</div>
            
            <div class="complyo-a11y-control">
              <label class="complyo-a11y-label">Schriftgröße</label>
              <div class="complyo-a11y-slider-container">
                <input type="range" min="80" max="200" value="100" step="10" class="complyo-a11y-slider" id="font-size-slider">
                <span class="complyo-a11y-value" id="font-size-value">100%</span>
              </div>
            </div>
            
            <div class="complyo-a11y-control">
              <label class="complyo-a11y-label">Zeilenabstand</label>
              <div class="complyo-a11y-slider-container">
                <input type="range" min="1" max="2.5" value="1.5" step="0.5" class="complyo-a11y-slider" id="line-height-slider">
                <span class="complyo-a11y-value" id="line-height-value">1.5</span>
              </div>
            </div>
            
            <div class="complyo-a11y-control">
              <label class="complyo-a11y-label">Zeichenabstand</label>
              <div class="complyo-a11y-slider-container">
                <input type="range" min="0" max="0.2" value="0" step="0.05" class="complyo-a11y-slider" id="letter-spacing-slider">
                <span class="complyo-a11y-value" id="letter-spacing-value">0</span>
              </div>
            </div>
            
            <div class="complyo-a11y-control">
              <button class="complyo-a11y-btn" id="readable-font-toggle">
                <span>Lesbare Schriftart</span>
              </button>
            </div>
          </div>
          
          <!-- Display Section -->
          <div class="complyo-a11y-section">
            <div class="complyo-a11y-section-title">🎨 Anzeige</div>
            
            <div class="complyo-a11y-control">
              <button class="complyo-a11y-btn" id="contrast-toggle">
                <span>Hoher Kontrast</span>
              </button>
            </div>
            
            <div class="complyo-a11y-control">
              <button class="complyo-a11y-btn" id="highlight-links-toggle">
                <span>Links hervorheben</span>
              </button>
            </div>
            
            <div class="complyo-a11y-control">
              <button class="complyo-a11y-btn" id="stop-animations-toggle">
                <span>Animationen stoppen</span>
              </button>
            </div>
          </div>
          
          <!-- Navigation Section -->
          <div class="complyo-a11y-section">
            <div class="complyo-a11y-section-title">🖱️ Navigation</div>
            
            <div class="complyo-a11y-control">
              <button class="complyo-a11y-btn" id="big-cursor-toggle">
                <span>Großer Cursor</span>
              </button>
            </div>
          </div>
          
          <button class="complyo-a11y-reset" id="reset-a11y">Alle zurücksetzen</button>
        </div>
        
        <div class="complyo-a11y-branding">
          Powered by <a href="https://complyo.tech" target="_blank">Complyo</a>
        </div>
      `;
      
      document.body.appendChild(toolbar);
      this.attachEventListeners();
    }
    
    attachEventListeners() {
      // Font Size
      const fontSlider = document.getElementById('font-size-slider');
      const fontValue = document.getElementById('font-size-value');
      fontSlider?.addEventListener('input', (e) => {
        const size = e.target.value;
        this.setFontSize(size);
        fontValue.textContent = `${size}%`;
      });
      
      // Line Height
      const lineHeightSlider = document.getElementById('line-height-slider');
      const lineHeightValue = document.getElementById('line-height-value');
      lineHeightSlider?.addEventListener('input', (e) => {
        const height = e.target.value;
        this.setLineHeight(height);
        lineHeightValue.textContent = height;
      });
      
      // Letter Spacing
      const letterSpacingSlider = document.getElementById('letter-spacing-slider');
      const letterSpacingValue = document.getElementById('letter-spacing-value');
      letterSpacingSlider?.addEventListener('input', (e) => {
        const spacing = e.target.value;
        this.setLetterSpacing(spacing);
        letterSpacingValue.textContent = `${(spacing * 100).toFixed(0)}%`;
      });
      
      // Toggle Buttons
      document.getElementById('contrast-toggle')?.addEventListener('click', (e) => {
        this.toggleFeature('contrast', e.target.closest('button'));
      });
      
      document.getElementById('highlight-links-toggle')?.addEventListener('click', (e) => {
        this.toggleFeature('highlightLinks', e.target.closest('button'));
      });
      
      document.getElementById('readable-font-toggle')?.addEventListener('click', (e) => {
        this.toggleFeature('readableFont', e.target.closest('button'));
      });
      
      document.getElementById('stop-animations-toggle')?.addEventListener('click', (e) => {
        this.toggleFeature('stopAnimations', e.target.closest('button'));
      });
      
      document.getElementById('big-cursor-toggle')?.addEventListener('click', (e) => {
        this.toggleFeature('bigCursor', e.target.closest('button'));
      });
      
      // Reset Button
      document.getElementById('reset-a11y')?.addEventListener('click', () => {
        this.reset();
      });
    }
    
    setFontSize(size) {
      document.documentElement.style.fontSize = `${size}%`;
      this.state.fontSize = parseInt(size);
      this.savePreferences();
    }
    
    setLineHeight(height) {
      document.body.className = document.body.className.replace(/complyo-line-height-\d+/g, '');
      const heightClass = `complyo-line-height-${Math.round(height * 10)}`;
      document.body.classList.add(heightClass);
      this.state.lineHeight = parseFloat(height);
      this.savePreferences();
    }
    
    setLetterSpacing(spacing) {
      document.body.className = document.body.className.replace(/complyo-letter-spacing-\d+/g, '');
      if (spacing > 0) {
        const spacingClass = `complyo-letter-spacing-${Math.round(spacing * 10)}`;
        document.body.classList.add(spacingClass);
      }
      this.state.letterSpacing = parseFloat(spacing);
      this.savePreferences();
    }
    
    toggleFeature(feature, button) {
      const featureMap = {
        contrast: 'complyo-high-contrast',
        highlightLinks: 'complyo-highlight-links',
        readableFont: 'complyo-readable-font',
        stopAnimations: 'complyo-stop-animations',
        bigCursor: 'complyo-big-cursor'
      };
      
      const className = featureMap[feature];
      document.body.classList.toggle(className);
      button?.classList.toggle('active');
      
      this.state[feature] = !this.state[feature];
      this.savePreferences();
    }
    
    reset() {
      // Reset font size
      document.documentElement.style.fontSize = '';
      document.getElementById('font-size-slider').value = 100;
      document.getElementById('font-size-value').textContent = '100%';
      
      // Reset line height
      document.body.className = document.body.className.replace(/complyo-line-height-\d+/g, '');
      document.getElementById('line-height-slider').value = 1.5;
      document.getElementById('line-height-value').textContent = '1.5';
      
      // Reset letter spacing
      document.body.className = document.body.className.replace(/complyo-letter-spacing-\d+/g, '');
      document.getElementById('letter-spacing-slider').value = 0;
      document.getElementById('letter-spacing-value').textContent = '0';
      
      // Reset all features
      document.body.classList.remove(
        'complyo-high-contrast',
        'complyo-highlight-links',
        'complyo-readable-font',
        'complyo-stop-animations',
        'complyo-big-cursor'
      );
      
      // Remove active states from buttons
      document.querySelectorAll('.complyo-a11y-btn.active').forEach(btn => {
        btn.classList.remove('active');
      });
      
      // Reset state
      this.state = {
        fontSize: 100,
        lineHeight: 1.5,
        letterSpacing: 0,
        contrast: false,
        highlightLinks: false,
        readableFont: false,
        stopAnimations: false,
        bigCursor: false
      };
      
      this.savePreferences();
    }
    
    savePreferences() {
      try {
        localStorage.setItem('complyo_a11y_prefs', JSON.stringify(this.state));
      } catch (e) {
        console.warn('[Complyo A11y] Could not save preferences:', e);
      }
    }
    
    loadUserPreferences() {
      try {
        const saved = localStorage.getItem('complyo_a11y_prefs');
        if (!saved) return;
        
        const prefs = JSON.parse(saved);
        
        // Apply saved preferences
        if (prefs.fontSize && prefs.fontSize !== 100) {
          this.setFontSize(prefs.fontSize);
          const slider = document.getElementById('font-size-slider');
          const value = document.getElementById('font-size-value');
          if (slider) slider.value = prefs.fontSize;
          if (value) value.textContent = `${prefs.fontSize}%`;
        }
        
        if (prefs.lineHeight && prefs.lineHeight !== 1.5) {
          this.setLineHeight(prefs.lineHeight);
          const slider = document.getElementById('line-height-slider');
          const value = document.getElementById('line-height-value');
          if (slider) slider.value = prefs.lineHeight;
          if (value) value.textContent = prefs.lineHeight;
        }
        
        if (prefs.letterSpacing && prefs.letterSpacing !== 0) {
          this.setLetterSpacing(prefs.letterSpacing);
          const slider = document.getElementById('letter-spacing-slider');
          const value = document.getElementById('letter-spacing-value');
          if (slider) slider.value = prefs.letterSpacing;
          if (value) value.textContent = `${(prefs.letterSpacing * 100).toFixed(0)}%`;
        }
        
        // Apply boolean features
        const features = ['contrast', 'highlightLinks', 'readableFont', 'stopAnimations', 'bigCursor'];
        features.forEach(feature => {
          if (prefs[feature]) {
            const buttonMap = {
              contrast: 'contrast-toggle',
              highlightLinks: 'highlight-links-toggle',
              readableFont: 'readable-font-toggle',
              stopAnimations: 'stop-animations-toggle',
              bigCursor: 'big-cursor-toggle'
            };
            const button = document.getElementById(buttonMap[feature]);
            if (button) {
              this.toggleFeature(feature, button);
            }
          }
        });
        
        console.log('[Complyo A11y] Preferences loaded');
      } catch (e) {
        console.warn('[Complyo A11y] Could not load preferences:', e);
      }
    }
  }
  
  // Auto-initialize
  if (document.currentScript && document.currentScript.getAttribute('data-site-id')) {
    const script = document.currentScript;
    const config = {
      siteId: script.getAttribute('data-site-id'),
      autoFix: script.getAttribute('data-auto-fix') !== 'false',
      showToolbar: script.getAttribute('data-show-toolbar') !== 'false'
    };
    new ComplyoAccessibility(config);
  }
  
  // Export for manual initialization
  window.ComplyoAccessibility = ComplyoAccessibility;
  
  console.log(`[Complyo] Accessibility Widget v${WIDGET_VERSION} loaded`);
})();
