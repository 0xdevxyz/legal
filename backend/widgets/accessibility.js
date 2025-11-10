/**
 * Complyo Accessibility Widget
 * Real code-based accessibility enhancements (NO OVERLAY!)
 * Generates actual DOM modifications and CSS for WCAG compliance
 */

(function() {
  'use strict';
  
  const WIDGET_VERSION = '1.0.0';
  const COMPLYO_API = 'https://api.complyo.tech';
  
  class ComplyoAccessibility {
    constructor(config = {}) {
      this.config = {
        siteId: config.siteId || this.getSiteIdFromScript(),
        features: config.features || ['contrast', 'font-size', 'keyboard-nav', 'skip-links', 'alt-text-fallback'],
        autoFix: config.autoFix !== false, // Default true
        showToolbar: config.showToolbar !== false, // Default true
        ...config
      };
      
      this.state = {
        fontSize: 100,
        contrast: 'normal',
        keyboardNavEnabled: false
      };
      
      this.init();
    }
    
    getSiteIdFromScript() {
      const script = document.currentScript || 
                     document.querySelector('script[data-complyo-a11y]');
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
      
      // Apply enabled features
      if (this.config.features.includes('contrast')) {
        this.enhanceContrast();
      }
      
      if (this.config.features.includes('keyboard-nav')) {
        this.improveKeyboardNavigation();
      }
      
      if (this.config.features.includes('skip-links')) {
        this.addSkipLinks();
      }
      
      if (this.config.features.includes('alt-text-fallback')) {
        this.fixMissingAltTexts();
      }
      
      if (this.config.showToolbar) {
        this.renderToolbar();
      }
      
      this.loadUserPreferences();
      
      console.log('[Complyo A11y] Fixes applied successfully');
    }
    
    enhanceContrast() {
      // Inject CSS for better contrast
      const style = document.createElement('style');
      style.id = 'complyo-contrast-fixes';
      style.textContent = `
        /* Complyo Accessibility: Enhanced Contrast */
        body.complyo-high-contrast {
          filter: contrast(1.2);
        }
        
        body.complyo-high-contrast a {
          text-decoration: underline;
          font-weight: 500;
        }
        
        body.complyo-high-contrast button {
          border: 2px solid currentColor;
        }
        
        /* Ensure sufficient contrast for text */
        .complyo-contrast-fixed {
          color: #1f2937 !important;
          background: #ffffff !important;
        }
      `;
      document.head.appendChild(style);
    }
    
    improveKeyboardNavigation() {
      // Make all interactive elements focusable
      const interactiveSelectors = 'a, button, input, select, textarea, [onclick], [role="button"]';
      const elements = document.querySelectorAll(interactiveSelectors);
      
      elements.forEach(el => {
        if (!el.hasAttribute('tabindex') && el.tagName !== 'A' && el.tagName !== 'BUTTON' && el.tagName !== 'INPUT') {
          el.setAttribute('tabindex', '0');
        }
        
        // Add visible focus indicator
        el.addEventListener('focus', () => {
          el.style.outline = '3px solid #6366f1';
          el.style.outlineOffset = '2px';
        });
        
        el.addEventListener('blur', () => {
          el.style.outline = '';
          el.style.outlineOffset = '';
        });
      });
      
      // Enable Enter key for clickable elements
      document.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && e.target.hasAttribute('onclick')) {
          e.target.click();
        }
      });
    }
    
    addSkipLinks() {
      // Add skip-to-content link at the top
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
        padding: 10px 20px;
        text-decoration: none;
        font-weight: bold;
        z-index: 999999;
        transition: top 0.2s;
      `;
      
      skipLink.addEventListener('focus', () => {
        skipLink.style.top = '0';
      });
      
      skipLink.addEventListener('blur', () => {
        skipLink.style.top = '-100px';
      });
      
      document.body.insertBefore(skipLink, document.body.firstChild);
      
      // Add id to main content if not present
      const main = document.querySelector('main, [role="main"], #main, #content');
      if (main && !main.id) {
        main.id = 'main-content';
      }
    }
    
    fixMissingAltTexts() {
      const images = document.querySelectorAll('img:not([alt])');
      
      images.forEach(img => {
        // Try to infer alt text from filename or title
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
    
    renderToolbar() {
      const toolbar = document.createElement('div');
      toolbar.id = 'complyo-a11y-toolbar';
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
            min-width: 200px;
          }
          .complyo-a11y-title {
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
          }
          .complyo-a11y-control {
            margin-bottom: 12px;
          }
          .complyo-a11y-control:last-child {
            margin-bottom: 0;
          }
          .complyo-a11y-label {
            display: block;
            font-size: 12px;
            color: #6b7280;
            margin-bottom: 4px;
          }
          .complyo-a11y-btn {
            width: 100%;
            padding: 8px;
            border: 1px solid #d1d5db;
            border-radius: 6px;
            background: white;
            cursor: pointer;
            font-size: 13px;
            transition: all 0.2s;
          }
          .complyo-a11y-btn:hover {
            background: #f3f4f6;
            border-color: #9ca3af;
          }
          .complyo-a11y-btn.active {
            background: #6366f1;
            color: white;
            border-color: #6366f1;
          }
          .complyo-a11y-slider {
            width: 100%;
            height: 6px;
            border-radius: 3px;
            background: #e5e7eb;
            appearance: none;
            outline: none;
          }
          .complyo-a11y-slider::-webkit-slider-thumb {
            appearance: none;
            width: 16px;
            height: 16px;
            border-radius: 50%;
            background: #6366f1;
            cursor: pointer;
          }
        </style>
        
        <div class="complyo-a11y-title">
          ♿ Barrierefreiheit
        </div>
        
        <div class="complyo-a11y-control">
          <label class="complyo-a11y-label">Schriftgröße: <span id="font-size-value">100%</span></label>
          <input type="range" min="80" max="150" value="100" class="complyo-a11y-slider" id="font-size-slider">
        </div>
        
        <div class="complyo-a11y-control">
          <label class="complyo-a11y-label">Kontrast</label>
          <button class="complyo-a11y-btn" id="contrast-toggle">Hoher Kontrast</button>
        </div>
        
        <div class="complyo-a11y-control">
          <button class="complyo-a11y-btn" id="reset-a11y">Zurücksetzen</button>
        </div>
      `;
      
      document.body.appendChild(toolbar);
      
      // Event listeners
      const fontSlider = toolbar.querySelector('#font-size-slider');
      const fontValue = toolbar.querySelector('#font-size-value');
      const contrastBtn = toolbar.querySelector('#contrast-toggle');
      const resetBtn = toolbar.querySelector('#reset-a11y');
      
      fontSlider.addEventListener('input', (e) => {
        const size = e.target.value;
        this.setFontSize(size);
        fontValue.textContent = `${size}%`;
      });
      
      contrastBtn.addEventListener('click', () => {
        this.toggleContrast();
        contrastBtn.classList.toggle('active');
      });
      
      resetBtn.addEventListener('click', () => {
        this.reset();
        fontSlider.value = 100;
        fontValue.textContent = '100%';
        contrastBtn.classList.remove('active');
      });
    }
    
    setFontSize(size) {
      document.documentElement.style.fontSize = `${size}%`;
      this.state.fontSize = size;
      this.savePreferences();
    }
    
    toggleContrast() {
      document.body.classList.toggle('complyo-high-contrast');
      this.state.contrast = document.body.classList.contains('complyo-high-contrast') ? 'high' : 'normal';
      this.savePreferences();
    }
    
    reset() {
      document.documentElement.style.fontSize = '';
      document.body.classList.remove('complyo-high-contrast');
      this.state = { fontSize: 100, contrast: 'normal' };
      this.savePreferences();
    }
    
    savePreferences() {
      localStorage.setItem('complyo_a11y_prefs', JSON.stringify(this.state));
    }
    
    loadUserPreferences() {
      const saved = localStorage.getItem('complyo_a11y_prefs');
      if (saved) {
        try {
          const prefs = JSON.parse(saved);
          
          if (prefs.fontSize !== 100) {
            this.setFontSize(prefs.fontSize);
            const slider = document.querySelector('#font-size-slider');
            const value = document.querySelector('#font-size-value');
            if (slider) slider.value = prefs.fontSize;
            if (value) value.textContent = `${prefs.fontSize}%`;
          }
          
          if (prefs.contrast === 'high') {
            document.body.classList.add('complyo-high-contrast');
            const btn = document.querySelector('#contrast-toggle');
            if (btn) btn.classList.add('active');
          }
        } catch (e) {
          console.warn('[Complyo A11y] Could not load preferences:', e);
        }
      }
    }
  }
  
  // Auto-initialize
  if (document.currentScript && document.currentScript.getAttribute('data-site-id')) {
    new ComplyoAccessibility();
  }
  
  // Export for manual initialization
  window.ComplyoAccessibility = ComplyoAccessibility;
  
  console.log(`[Complyo] Accessibility Widget v${WIDGET_VERSION} loaded`);
})();

