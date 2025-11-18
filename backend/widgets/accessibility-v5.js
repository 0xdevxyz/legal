/**
 * Complyo Accessibility Widget v5.0 - PROFESSIONAL EDITION
 * ==========================================================
 * Vollständiges Accessibility-Widget mit allen Features wie UserWay/AccessiBe
 * 
 * Features (25+):
 * ✅ Farben: Farbfilter, Helligkeit, Sättigung, Invertieren, Nachtmodus, Blaufilter
 * ✅ Text: Spacing, Dyslexie-Schrift, Bionic Reading, Ausrichtung
 * ✅ Audio: Text-to-Speech, Screen Reader Support
 * ✅ Content: Bilder ausblenden, Tooltips, Page Structure
 * ✅ Controls: Alles zurücksetzen, Widget verschieben, Tastatur-Guide
 * 
 * © 2025 Complyo.tech
 */

(function() {
  'use strict';
  
  const WIDGET_VERSION = '5.0.0';
  const API_BASE = window.location.hostname === 'localhost' ? 'http://localhost:8000' : 'https://api.complyo.tech';
  
  class ComplyoAccessibilityWidget {
    constructor(config = {}) {
      this.config = {
        siteId: config.siteId || this.getSiteIdFromScript(),
        showToolbar: config.showToolbar !== false,
        position: config.position || 'bottom-right',
        language: config.language || 'de'
      };
      
      // ALLE Features mit Defaults
      this.features = {
        // Text
        fontSize: 100,
        lineHeight: 150,
        letterSpacing: 0,
        wordSpacing: 0,
        textAlign: 'default',
        
        // Farben
        contrast: false,
        brightness: 100,
        saturation: 100,
        invertColors: false,
        nightMode: false,
        grayscale: false,
        colorFilter: 'none', // none, protanopia, deuteranopia, tritanopia
        
        // Features
        highlightLinks: false,
        readableFont: false,
        dyslexiaFont: false,
        bionicReading: false,
        hideImages: false,
        showTooltips: false,
        stopAnimations: false,
        bigCursor: false,
        readingGuide: false,
        
        // Audio
        textToSpeech: false,
        speechRate: 1.0,
        
        // Page Structure
        pageStructure: false
      };
      
      this.sessionId = this.generateSessionId();
      this.isOpen = false;
      this.isDragging = false;
      this.speechSynthesis = window.speechSynthesis;
      this.currentUtterance = null;
      
      this.init();
    }
    
    async init() {
      console.log(`🚀 Initializing Complyo Widget with site-id: ${this.config.siteId}`);
      
      // Load preferences
      this.loadPreferences();
      
      // Render toolbar
      this.renderToolbar();
      
      // Apply saved features
      this.applyAllFeatures();
      
      // Inject CSS
      this.injectCSS();
      
      // Load AI alt-texts
      await this.loadAndApplyAltTexts();
      
      // Setup keyboard shortcuts
      this.setupKeyboardShortcuts();
      
      console.log(`🎨 Complyo Accessibility Widget v${WIDGET_VERSION} initialized`);
    }
    
    getSiteIdFromScript() {
      const scripts = document.querySelectorAll('script[data-site-id]');
      if (scripts.length > 0) {
        return scripts[scripts.length - 1].getAttribute('data-site-id');
      }
      return 'demo';
    }
    
    generateSessionId() {
      return 'sess_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    renderToolbar() {
      const container = document.createElement('div');
      container.id = 'complyo-a11y-widget';
      container.className = `complyo-widget-${this.config.position}`;
      
      container.innerHTML = `
        <button class="complyo-toggle-btn" aria-label="Barrierefreiheit öffnen" aria-expanded="false" title="Barrierefreiheit (Alt+A)">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <!-- Universal Access Symbol: Person mit ausgestreckten Armen -->
            <circle cx="12" cy="12" r="10" />
            <circle cx="12" cy="6" r="2" fill="currentColor" />
            <path d="M12 9v6" />
            <path d="M9 11l-2 6" />
            <path d="M15 11l2 6" />
            <path d="M8 11h8" />
          </svg>
        </button>
        
        <div class="complyo-panel" hidden>
          <div class="complyo-panel-header">
            <h3>✨ Barrierefreiheit</h3>
            <button class="complyo-close-btn" aria-label="Schließen" title="Schließen (Esc)">✕</button>
          </div>
          
          <div class="complyo-panel-content">
            
            <!-- 📝 TEXT SEKTION -->
            <div class="complyo-section">
              <h4>📝 Text & Lesbarkeit</h4>
              
              <div class="complyo-control">
                <label>Schriftgröße: <span id="complyo-font-size-value">100%</span></label>
                <div class="complyo-slider-controls">
                  <button class="complyo-btn-small" data-action="decrease-font">-</button>
                  <input type="range" id="complyo-font-size" min="80" max="200" value="100" step="10">
                  <button class="complyo-btn-small" data-action="increase-font">+</button>
                </div>
              </div>
              
              <div class="complyo-control">
                <label>Zeilenhöhe: <span id="complyo-line-height-value">150%</span></label>
                <input type="range" id="complyo-line-height" min="100" max="250" value="150" step="10">
              </div>
              
              <div class="complyo-control">
                <label>Buchstabenabstand: <span id="complyo-letter-spacing-value">0px</span></label>
                <input type="range" id="complyo-letter-spacing" min="0" max="10" value="0" step="1">
              </div>
              
              <div class="complyo-control">
                <label>Wortabstand: <span id="complyo-word-spacing-value">0px</span></label>
                <input type="range" id="complyo-word-spacing" min="0" max="20" value="0" step="2">
              </div>
              
              <div class="complyo-control">
                <label>
                  <input type="checkbox" id="complyo-dyslexia-font">
                  <span>Dyslexie-freundliche Schrift</span>
                </label>
              </div>
              
              <div class="complyo-control">
                <label>
                  <input type="checkbox" id="complyo-readable-font">
                  <span>Leserliche Schrift</span>
                </label>
              </div>
              
              <div class="complyo-control">
                <label>
                  <input type="checkbox" id="complyo-bionic-reading">
                  <span>Bionic Reading (Wortanfänge fett)</span>
                </label>
              </div>
              
              <div class="complyo-control">
                <label>Text-Ausrichtung:</label>
                <div class="complyo-btn-group">
                  <button class="complyo-btn-icon" data-align="left" title="Links">
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                      <path d="M0 2h16v2H0V2zm0 4h10v2H0V6zm0 4h16v2H0v-2z"/>
                    </svg>
                  </button>
                  <button class="complyo-btn-icon" data-align="center" title="Zentriert">
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                      <path d="M3 2h10v2H3V2zm-1 4h12v2H2V6zm1 4h10v2H3v-2z"/>
                    </svg>
                  </button>
                  <button class="complyo-btn-icon" data-align="right" title="Rechts">
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                      <path d="M0 2h16v2H0V2zm6 4h10v2H6V6zm-6 4h16v2H0v-2z"/>
                    </svg>
                  </button>
                </div>
              </div>
            </div>
            
            <!-- 🎨 FARB-SEKTION -->
            <div class="complyo-section">
              <h4>🎨 Farben & Sehen</h4>
              
              <div class="complyo-control">
                <label>
                  <input type="checkbox" id="complyo-contrast">
                  <span>Hoher Kontrast</span>
                </label>
              </div>
              
              <div class="complyo-control">
                <label>Helligkeit: <span id="complyo-brightness-value">100%</span></label>
                <input type="range" id="complyo-brightness" min="50" max="150" value="100" step="5">
              </div>
              
              <div class="complyo-control">
                <label>Sättigung: <span id="complyo-saturation-value">100%</span></label>
                <input type="range" id="complyo-saturation" min="0" max="200" value="100" step="10">
              </div>
              
              <div class="complyo-control">
                <label>
                  <input type="checkbox" id="complyo-invert-colors">
                  <span>Farben invertieren</span>
                </label>
              </div>
              
              <div class="complyo-control">
                <label>
                  <input type="checkbox" id="complyo-night-mode">
                  <span>Nachtmodus (Dark Mode)</span>
                </label>
              </div>
              
              <div class="complyo-control">
                <label>
                  <input type="checkbox" id="complyo-grayscale">
                  <span>Graustufen</span>
                </label>
              </div>
              
              <div class="complyo-control">
                <label>Farbfilter für Farbschwäche:</label>
                <select id="complyo-color-filter" class="complyo-select">
                  <option value="none">Kein Filter</option>
                  <option value="protanopia">Rot-Grün (Protanopie)</option>
                  <option value="deuteranopia">Rot-Grün (Deuteranopie)</option>
                  <option value="tritanopia">Blau-Gelb (Tritanopie)</option>
                  <option value="achromatopsia">Farbenblind (Achromat.)</option>
                </select>
              </div>
            </div>
            
            <!-- 🖼️ CONTENT SEKTION -->
            <div class="complyo-section">
              <h4>🖼️ Inhalte & Navigation</h4>
              
              <div class="complyo-control">
                <label>
                  <input type="checkbox" id="complyo-highlight-links">
                  <span>Links hervorheben</span>
                </label>
              </div>
              
              <div class="complyo-control">
                <label>
                  <input type="checkbox" id="complyo-hide-images">
                  <span>Bilder ausblenden</span>
                </label>
              </div>
              
              <div class="complyo-control">
                <label>
                  <input type="checkbox" id="complyo-show-tooltips">
                  <span>Tooltips anzeigen</span>
                </label>
              </div>
              
              <div class="complyo-control">
                <label>
                  <input type="checkbox" id="complyo-stop-animations">
                  <span>Animationen stoppen</span>
                </label>
              </div>
              
              <div class="complyo-control">
                <label>
                  <input type="checkbox" id="complyo-reading-guide">
                  <span>Lese-Linie (Fokus-Guide)</span>
                </label>
              </div>
              
              <div class="complyo-control">
                <label>
                  <input type="checkbox" id="complyo-page-structure">
                  <span>Seitenstruktur anzeigen</span>
                </label>
              </div>
            </div>
            
            <!-- 🖱️ BEDIENUNG SEKTION -->
            <div class="complyo-section">
              <h4>🖱️ Bedienung & Cursor</h4>
              
              <div class="complyo-control">
                <label>
                  <input type="checkbox" id="complyo-big-cursor">
                  <span>Großer Mauszeiger</span>
                </label>
              </div>
              
              <div class="complyo-control">
                <button class="complyo-btn-full" id="complyo-keyboard-nav">
                  ⌨️ Tastatur-Navigation Guide
                </button>
              </div>
            </div>
            
            <!-- 🔊 AUDIO SEKTION -->
            <div class="complyo-section">
              <h4>🔊 Vorlesen & Audio</h4>
              
              <div class="complyo-control">
                <label>
                  <input type="checkbox" id="complyo-text-to-speech">
                  <span>Text vorlesen (Text-to-Speech)</span>
                </label>
              </div>
              
              <div class="complyo-control" id="complyo-tts-controls" hidden>
                <label>Sprech-Geschwindigkeit: <span id="complyo-speech-rate-value">1.0x</span></label>
                <input type="range" id="complyo-speech-rate" min="0.5" max="2.0" value="1.0" step="0.1">
                <div class="complyo-tts-buttons">
                  <button class="complyo-btn-small" id="complyo-tts-play">▶️ Start</button>
                  <button class="complyo-btn-small" id="complyo-tts-pause">⏸️ Pause</button>
                  <button class="complyo-btn-small" id="complyo-tts-stop">⏹️ Stop</button>
                </div>
                <small style="color: #6b7280;">Klicken Sie auf Text um ihn vorzulesen</small>
              </div>
            </div>
            
          </div>
          
          <div class="complyo-panel-footer">
            <button class="complyo-btn-reset" id="complyo-reset-all">
              🔄 Alles zurücksetzen
            </button>
            <small>Complyo Widget v${WIDGET_VERSION}</small>
          </div>
        </div>
        
        <!-- Reading Guide Overlay -->
        <div class="complyo-reading-guide" id="complyo-reading-guide-overlay" hidden></div>
        
        <!-- Page Structure Overlay -->
        <div class="complyo-page-structure-overlay" id="complyo-page-structure-overlay" hidden>
          <div class="complyo-structure-header">
            <h3>📑 Seitenstruktur</h3>
            <button class="complyo-structure-close">✕</button>
          </div>
          <div class="complyo-structure-content" id="complyo-structure-content"></div>
        </div>
        
        <!-- Keyboard Guide Modal -->
        <div class="complyo-keyboard-modal" id="complyo-keyboard-modal" hidden>
          <div class="complyo-modal-content">
            <div class="complyo-modal-header">
              <h3>⌨️ Tastatur-Shortcuts</h3>
              <button class="complyo-modal-close">✕</button>
            </div>
            <div class="complyo-modal-body">
              <div class="complyo-shortcut">
                <kbd>Alt</kbd> + <kbd>A</kbd>
                <span>Widget öffnen/schließen</span>
              </div>
              <div class="complyo-shortcut">
                <kbd>Alt</kbd> + <kbd>R</kbd>
                <span>Alle Einstellungen zurücksetzen</span>
              </div>
              <div class="complyo-shortcut">
                <kbd>Alt</kbd> + <kbd>+</kbd>
                <span>Schrift vergrößern</span>
              </div>
              <div class="complyo-shortcut">
                <kbd>Alt</kbd> + <kbd>-</kbd>
                <span>Schrift verkleinern</span>
              </div>
              <div class="complyo-shortcut">
                <kbd>Alt</kbd> + <kbd>C</kbd>
                <span>Kontrast umschalten</span>
              </div>
              <div class="complyo-shortcut">
                <kbd>Tab</kbd>
                <span>Durch Elemente navigieren</span>
              </div>
              <div class="complyo-shortcut">
                <kbd>Enter</kbd> / <kbd>Space</kbd>
                <span>Element aktivieren</span>
              </div>
              <div class="complyo-shortcut">
                <kbd>Esc</kbd>
                <span>Dialog/Widget schließen</span>
              </div>
            </div>
          </div>
        </div>
      `;
      
      document.body.appendChild(container);
      this.container = container;
      
      // Event Listeners
      this.setupEventListeners();
    }
    
    setupEventListeners() {
      const panel = this.container.querySelector('.complyo-panel');
      const toggleBtn = this.container.querySelector('.complyo-toggle-btn');
      const closeBtn = this.container.querySelector('.complyo-close-btn');
      
      // Toggle Widget
      toggleBtn.addEventListener('click', () => this.togglePanel());
      closeBtn.addEventListener('click', () => this.closePanel());
      
      // Text Controls
      this.container.querySelector('#complyo-font-size').addEventListener('input', (e) => {
        this.features.fontSize = parseInt(e.target.value);
        this.updateSliderValue('complyo-font-size-value', this.features.fontSize + '%');
        this.applyFeature('fontSize');
        this.savePreferences();
        this.trackAnalytics('fontSize', this.features.fontSize);
      });
      
      // Buttons für Font Size
      this.container.querySelector('[data-action="decrease-font"]').addEventListener('click', () => {
        const slider = this.container.querySelector('#complyo-font-size');
        slider.value = Math.max(80, parseInt(slider.value) - 10);
        slider.dispatchEvent(new Event('input'));
      });
      
      this.container.querySelector('[data-action="increase-font"]').addEventListener('click', () => {
        const slider = this.container.querySelector('#complyo-font-size');
        slider.value = Math.min(200, parseInt(slider.value) + 10);
        slider.dispatchEvent(new Event('input'));
      });
      
      this.container.querySelector('#complyo-line-height').addEventListener('input', (e) => {
        this.features.lineHeight = parseInt(e.target.value);
        this.updateSliderValue('complyo-line-height-value', this.features.lineHeight + '%');
        this.applyFeature('lineHeight');
        this.savePreferences();
      });
      
      this.container.querySelector('#complyo-letter-spacing').addEventListener('input', (e) => {
        this.features.letterSpacing = parseInt(e.target.value);
        this.updateSliderValue('complyo-letter-spacing-value', this.features.letterSpacing + 'px');
        this.applyFeature('letterSpacing');
        this.savePreferences();
      });
      
      this.container.querySelector('#complyo-word-spacing').addEventListener('input', (e) => {
        this.features.wordSpacing = parseInt(e.target.value);
        this.updateSliderValue('complyo-word-spacing-value', this.features.wordSpacing + 'px');
        this.applyFeature('wordSpacing');
        this.savePreferences();
      });
      
      // Color Controls
      this.container.querySelector('#complyo-brightness').addEventListener('input', (e) => {
        this.features.brightness = parseInt(e.target.value);
        this.updateSliderValue('complyo-brightness-value', this.features.brightness + '%');
        this.applyFeature('brightness');
        this.savePreferences();
      });
      
      this.container.querySelector('#complyo-saturation').addEventListener('input', (e) => {
        this.features.saturation = parseInt(e.target.value);
        this.updateSliderValue('complyo-saturation-value', this.features.saturation + '%');
        this.applyFeature('saturation');
        this.savePreferences();
      });
      
      this.container.querySelector('#complyo-color-filter').addEventListener('change', (e) => {
        this.features.colorFilter = e.target.value;
        this.applyFeature('colorFilter');
        this.savePreferences();
        this.trackAnalytics('colorFilter', this.features.colorFilter);
      });
      
      // Checkboxes
      const checkboxes = [
        'contrast', 'highlightLinks', 'readableFont', 'dyslexiaFont', 
        'bionicReading', 'stopAnimations', 'bigCursor', 'invertColors',
        'nightMode', 'grayscale', 'hideImages', 'showTooltips',
        'readingGuide', 'pageStructure', 'textToSpeech'
      ];
      
      checkboxes.forEach(feature => {
        const checkbox = this.container.querySelector(`#complyo-${feature.replace(/([A-Z])/g, '-$1').toLowerCase()}`);
        if (checkbox) {
          checkbox.addEventListener('change', (e) => {
            this.features[feature] = e.target.checked;
            this.applyFeature(feature);
            this.savePreferences();
            this.trackAnalytics(feature, e.target.checked);
            
            // Show/hide TTS controls
            if (feature === 'textToSpeech') {
              const ttsControls = this.container.querySelector('#complyo-tts-controls');
              ttsControls.hidden = !e.target.checked;
              if (!e.target.checked) {
                this.stopSpeech();
              }
            }
          });
        }
      });
      
      // Text Alignment
      this.container.querySelectorAll('[data-align]').forEach(btn => {
        btn.addEventListener('click', (e) => {
          this.features.textAlign = e.currentTarget.dataset.align;
          this.applyFeature('textAlign');
          this.savePreferences();
          
          // Update active state
          this.container.querySelectorAll('[data-align]').forEach(b => b.classList.remove('active'));
          e.currentTarget.classList.add('active');
        });
      });
      
      // TTS Controls
      this.container.querySelector('#complyo-speech-rate').addEventListener('input', (e) => {
        this.features.speechRate = parseFloat(e.target.value);
        this.updateSliderValue('complyo-speech-rate-value', this.features.speechRate.toFixed(1) + 'x');
        this.savePreferences();
      });
      
      this.container.querySelector('#complyo-tts-play').addEventListener('click', () => this.startSpeech());
      this.container.querySelector('#complyo-tts-pause').addEventListener('click', () => this.pauseSpeech());
      this.container.querySelector('#complyo-tts-stop').addEventListener('click', () => this.stopSpeech());
      
      // Reset Button
      this.container.querySelector('#complyo-reset-all').addEventListener('click', () => this.resetAll());
      
      // Keyboard Nav Button
      this.container.querySelector('#complyo-keyboard-nav').addEventListener('click', () => this.showKeyboardGuide());
      
      // Keyboard Guide Modal
      this.container.querySelector('.complyo-modal-close').addEventListener('click', () => this.hideKeyboardGuide());
      
      // Page Structure
      this.container.querySelector('.complyo-structure-close').addEventListener('click', () => {
        this.features.pageStructure = false;
        this.container.querySelector('#complyo-page-structure').checked = false;
        this.applyFeature('pageStructure');
      });
      
      // Make widget draggable
      this.makeDraggable();
    }
    
    updateSliderValue(id, value) {
      const elem = this.container.querySelector(`#${id}`);
      if (elem) elem.textContent = value;
    }
    
    applyFeature(feature) {
      const body = document.body;
      const html = document.documentElement;
      
      switch(feature) {
        case 'fontSize':
          // CSS-Variable für universelle Skalierung
          html.style.setProperty('--complyo-font-scale', this.features.fontSize / 100);
          
          // Auch body direkt setzen für Legacy-Support
          body.style.fontSize = `${this.features.fontSize}%`;
          
          // CSS-Klasse für spezifische Regeln
          if (this.features.fontSize !== 100) {
            body.classList.add('complyo-scaled-text');
            body.setAttribute('data-font-scale', this.features.fontSize);
          } else {
            body.classList.remove('complyo-scaled-text');
            body.removeAttribute('data-font-scale');
          }
          break;
          
        case 'lineHeight':
          body.style.lineHeight = `${this.features.lineHeight / 100}`;
          break;
          
        case 'letterSpacing':
          body.style.letterSpacing = `${this.features.letterSpacing}px`;
          break;
          
        case 'wordSpacing':
          body.style.wordSpacing = `${this.features.wordSpacing}px`;
          break;
          
        case 'textAlign':
          body.classList.remove('complyo-align-left', 'complyo-align-center', 'complyo-align-right');
          if (this.features.textAlign !== 'default') {
            body.classList.add(`complyo-align-${this.features.textAlign}`);
          }
          break;
          
        case 'contrast':
        case 'brightness':
        case 'saturation':
        case 'invertColors':
        case 'grayscale':
        case 'colorFilter':
          this.applyColorFilters();
          break;
          
        case 'nightMode':
          body.classList.toggle('complyo-night-mode', this.features.nightMode);
          break;
          
        case 'highlightLinks':
          body.classList.toggle('complyo-highlight-links', this.features.highlightLinks);
          break;
          
        case 'readableFont':
          body.classList.toggle('complyo-readable-font', this.features.readableFont);
          break;
          
        case 'dyslexiaFont':
          body.classList.toggle('complyo-dyslexia-font', this.features.dyslexiaFont);
          break;
          
        case 'bionicReading':
          body.classList.toggle('complyo-bionic-reading', this.features.bionicReading);
          if (this.features.bionicReading) {
            this.applyBionicReading();
          } else {
            this.removeBionicReading();
          }
          break;
          
        case 'hideImages':
          body.classList.toggle('complyo-hide-images', this.features.hideImages);
          break;
          
        case 'showTooltips':
          body.classList.toggle('complyo-show-tooltips', this.features.showTooltips);
          if (this.features.showTooltips) {
            this.addTooltips();
          } else {
            this.removeTooltips();
          }
          break;
          
        case 'stopAnimations':
          body.classList.toggle('complyo-stop-animations', this.features.stopAnimations);
          break;
          
        case 'bigCursor':
          body.classList.toggle('complyo-big-cursor', this.features.bigCursor);
          break;
          
        case 'readingGuide':
          const guide = document.getElementById('complyo-reading-guide-overlay');
          guide.hidden = !this.features.readingGuide;
          if (this.features.readingGuide) {
            this.setupReadingGuide();
          }
          break;
          
        case 'pageStructure':
          const structureOverlay = document.getElementById('complyo-page-structure-overlay');
          structureOverlay.hidden = !this.features.pageStructure;
          if (this.features.pageStructure) {
            this.showPageStructure();
          }
          break;
          
        case 'textToSpeech':
          // TTS is handled by separate controls
          break;
      }
    }
    
    applyColorFilters() {
      const body = document.body;
      let filters = [];
      
      // Kontrast: Setze auch CSS-Klasse für spezifische Widget-Styles
      if (this.features.contrast) {
        filters.push('contrast(1.5)');
        body.classList.add('complyo-high-contrast');
      } else {
        body.classList.remove('complyo-high-contrast');
      }
      
      // Nur wenn von Default-Werten abweichend
      if (this.features.brightness !== 100) {
        filters.push(`brightness(${this.features.brightness}%)`);
      }
      
      if (this.features.saturation !== 100) {
        filters.push(`saturate(${this.features.saturation}%)`);
      }
      
      if (this.features.invertColors) {
        filters.push('invert(1)');
      }
      
      if (this.features.grayscale) {
        filters.push('grayscale(1)');
      }
      
      // Farbfilter für Farbschwäche
      switch(this.features.colorFilter) {
        case 'protanopia':
          // Rot-Grün (Protanopie)
          filters.push('sepia(1) hue-rotate(20deg) saturate(0.8)');
          break;
        case 'deuteranopia':
          // Rot-Grün (Deuteranopie)
          filters.push('sepia(1) hue-rotate(30deg) saturate(0.7)');
          break;
        case 'tritanopia':
          // Blau-Gelb (Tritanopie)
          filters.push('sepia(1) hue-rotate(-30deg) saturate(0.9)');
          break;
        case 'achromatopsia':
          // Farbenblind
          filters.push('grayscale(1)');
          break;
      }
      
      // Nur Filter setzen wenn es welche gibt
      if (filters.length > 0) {
        body.style.filter = filters.join(' ');
        
        // Widget selbst ausnehmen - KRITISCH für Sichtbarkeit!
        const widget = document.getElementById('complyo-a11y-widget');
        if (widget) {
          widget.style.filter = 'none';
          widget.style.isolation = 'isolate';
        }
      } else {
        body.style.filter = 'none';
        
        // Widget-Isolation auch bei "none" beibehalten für Stabilität
        const widget = document.getElementById('complyo-a11y-widget');
        if (widget) {
          widget.style.filter = 'none';
          widget.style.isolation = 'isolate';
        }
      }
    }
    
    applyBionicReading() {
      // Bionic Reading: Erste Hälfte jedes Wortes fett
      const walker = document.createTreeWalker(
        document.body,
        NodeFilter.SHOW_TEXT,
        {
          acceptNode: (node) => {
            // Skip widget und scripts
            const parent = node.parentElement;
            if (!parent || parent.closest('#complyo-a11y-widget') || parent.closest('script') || parent.closest('style')) {
              return NodeFilter.FILTER_REJECT;
            }
            return NodeFilter.FILTER_ACCEPT;
          }
        }
      );
      
      const textNodes = [];
      let node;
      while (node = walker.nextNode()) {
        textNodes.push(node);
      }
      
      textNodes.forEach(textNode => {
        const text = textNode.textContent;
        if (text.trim().length === 0) return;
        
        const words = text.split(/(\s+)/);
        const fragment = document.createDocumentFragment();
        
        words.forEach(word => {
          if (word.match(/\s+/)) {
            fragment.appendChild(document.createTextNode(word));
          } else if (word.length > 2) {
            const half = Math.ceil(word.length / 2);
            const boldPart = document.createElement('strong');
            boldPart.className = 'complyo-bionic';
            boldPart.textContent = word.substring(0, half);
            fragment.appendChild(boldPart);
            fragment.appendChild(document.createTextNode(word.substring(half)));
          } else {
            fragment.appendChild(document.createTextNode(word));
          }
        });
        
        textNode.parentNode.replaceChild(fragment, textNode);
      });
    }
    
    removeBionicReading() {
      document.querySelectorAll('.complyo-bionic').forEach(el => {
        const text = el.textContent + (el.nextSibling ? el.nextSibling.textContent : '');
        const textNode = document.createTextNode(text);
        el.parentNode.replaceChild(textNode, el);
        if (el.nextSibling) el.nextSibling.remove();
      });
    }
    
    addTooltips() {
      // Fügt title-Tooltips für alle interaktiven Elemente ohne title hinzu
      document.querySelectorAll('a, button, input, select, textarea').forEach(el => {
        if (!el.title && !el.closest('#complyo-a11y-widget')) {
          const text = el.textContent.trim() || el.getAttribute('aria-label') || el.value;
          if (text && text.length < 100) {
            el.setAttribute('data-complyo-tooltip', 'true');
            el.title = text;
          }
        }
      });
    }
    
    removeTooltips() {
      document.querySelectorAll('[data-complyo-tooltip]').forEach(el => {
        el.removeAttribute('title');
        el.removeAttribute('data-complyo-tooltip');
      });
    }
    
    setupReadingGuide() {
      const guide = document.getElementById('complyo-reading-guide-overlay');
      
      document.addEventListener('mousemove', (e) => {
        if (this.features.readingGuide) {
          guide.style.top = e.clientY + 'px';
        }
      });
    }
    
    showPageStructure() {
      const content = document.getElementById('complyo-structure-content');
      content.innerHTML = '';
      
      // Sammle Headings
      const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
      const landmarks = document.querySelectorAll('[role="banner"], [role="navigation"], [role="main"], [role="contentinfo"], header, nav, main, footer');
      
      let html = '<div class="complyo-structure-section"><h4>📋 Überschriften</h4><ul>';
      headings.forEach((h, i) => {
        if (!h.closest('#complyo-a11y-widget')) {
          const level = h.tagName.toLowerCase();
          const text = h.textContent.trim().substring(0, 60);
          html += `<li class="complyo-structure-${level}" data-element-index="${i}">
            <span class="complyo-structure-tag">${level.toUpperCase()}</span>
            ${text}
          </li>`;
        }
      });
      html += '</ul></div>';
      
      html += '<div class="complyo-structure-section"><h4>🏛️ Landmarks</h4><ul>';
      landmarks.forEach((l, i) => {
        if (!l.closest('#complyo-a11y-widget')) {
          const role = l.getAttribute('role') || l.tagName.toLowerCase();
          html += `<li><span class="complyo-structure-tag">${role}</span></li>`;
        }
      });
      html += '</ul></div>';
      
      content.innerHTML = html;
      
      // Click Handler
      content.querySelectorAll('[data-element-index]').forEach(item => {
        item.addEventListener('click', (e) => {
          const index = parseInt(e.currentTarget.dataset.elementIndex);
          headings[index].scrollIntoView({ behavior: 'smooth', block: 'center' });
          headings[index].style.outline = '3px solid #7c3aed';
          setTimeout(() => {
            headings[index].style.outline = '';
          }, 2000);
        });
      });
    }
    
    // Text-to-Speech
    startSpeech() {
      if (!this.speechSynthesis) {
        alert('Text-to-Speech wird von Ihrem Browser nicht unterstützt.');
        return;
      }
      
      // Get all text content
      const textContent = document.body.innerText;
      
      this.currentUtterance = new SpeechSynthesisUtterance(textContent);
      this.currentUtterance.rate = this.features.speechRate;
      this.currentUtterance.lang = this.config.language;
      
      this.speechSynthesis.speak(this.currentUtterance);
      
      // Add click-to-read functionality
      document.addEventListener('click', this.handleTTSClick);
    }
    
    pauseSpeech() {
      if (this.speechSynthesis.speaking) {
        this.speechSynthesis.pause();
      }
    }
    
    stopSpeech() {
      this.speechSynthesis.cancel();
      document.removeEventListener('click', this.handleTTSClick);
    }
    
    handleTTSClick = (e) => {
      if (e.target.closest('#complyo-a11y-widget')) return;
      
      e.preventDefault();
      e.stopPropagation();
      
      const text = e.target.textContent.trim();
      if (text) {
        this.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = this.features.speechRate;
        utterance.lang = this.config.language;
        this.speechSynthesis.speak(utterance);
      }
    }
    
    showKeyboardGuide() {
      const modal = document.getElementById('complyo-keyboard-modal');
      modal.hidden = false;
    }
    
    hideKeyboardGuide() {
      const modal = document.getElementById('complyo-keyboard-modal');
      modal.hidden = true;
    }
    
    setupKeyboardShortcuts() {
      document.addEventListener('keydown', (e) => {
        // Alt+A: Toggle Widget
        if (e.altKey && e.key === 'a') {
          e.preventDefault();
          this.togglePanel();
        }
        
        // Alt+R: Reset All
        if (e.altKey && e.key === 'r') {
          e.preventDefault();
          this.resetAll();
        }
        
        // Alt++: Increase Font
        if (e.altKey && (e.key === '+' || e.key === '=')) {
          e.preventDefault();
          const slider = this.container.querySelector('#complyo-font-size');
          slider.value = Math.min(200, parseInt(slider.value) + 10);
          slider.dispatchEvent(new Event('input'));
        }
        
        // Alt+-: Decrease Font
        if (e.altKey && e.key === '-') {
          e.preventDefault();
          const slider = this.container.querySelector('#complyo-font-size');
          slider.value = Math.max(80, parseInt(slider.value) - 10);
          slider.dispatchEvent(new Event('input'));
        }
        
        // Alt+C: Toggle Contrast
        if (e.altKey && e.key === 'c') {
          e.preventDefault();
          const checkbox = this.container.querySelector('#complyo-contrast');
          checkbox.checked = !checkbox.checked;
          checkbox.dispatchEvent(new Event('change'));
        }
        
        // Esc: Close Widget/Modals
        if (e.key === 'Escape') {
          this.closePanel();
          this.hideKeyboardGuide();
        }
      });
    }
    
    makeDraggable() {
      const toggleBtn = this.container.querySelector('.complyo-toggle-btn');
      let isDragging = false;
      let startX, startY, startLeft, startTop;
      
      toggleBtn.addEventListener('mousedown', (e) => {
        if (e.target.closest('.complyo-toggle-btn')) {
          startX = e.clientX;
          startY = e.clientY;
          const rect = this.container.getBoundingClientRect();
          startLeft = rect.left;
          startTop = rect.top;
          
          const mouseMoveHandler = (e) => {
            const dx = e.clientX - startX;
            const dy = e.clientY - startY;
            
            if (Math.abs(dx) > 5 || Math.abs(dy) > 5) {
              isDragging = true;
              this.container.style.position = 'fixed';
              this.container.style.left = (startLeft + dx) + 'px';
              this.container.style.top = (startTop + dy) + 'px';
              this.container.style.right = 'auto';
              this.container.style.bottom = 'auto';
            }
          };
          
          const mouseUpHandler = (e) => {
            document.removeEventListener('mousemove', mouseMoveHandler);
            document.removeEventListener('mouseup', mouseUpHandler);
            
            setTimeout(() => {
              isDragging = false;
            }, 100);
          };
          
          document.addEventListener('mousemove', mouseMoveHandler);
          document.addEventListener('mouseup', mouseUpHandler);
        }
      });
      
      toggleBtn.addEventListener('click', (e) => {
        if (isDragging) {
          e.stopPropagation();
        }
      }, true);
    }
    
    resetAll() {
      if (!confirm('Alle Barrierefreiheits-Einstellungen zurücksetzen?')) return;
      
      // Reset all features
      this.features = {
        fontSize: 100,
        lineHeight: 150,
        letterSpacing: 0,
        wordSpacing: 0,
        textAlign: 'default',
        contrast: false,
        brightness: 100,
        saturation: 100,
        invertColors: false,
        nightMode: false,
        grayscale: false,
        colorFilter: 'none',
        highlightLinks: false,
        readableFont: false,
        dyslexiaFont: false,
        bionicReading: false,
        hideImages: false,
        showTooltips: false,
        stopAnimations: false,
        bigCursor: false,
        readingGuide: false,
        textToSpeech: false,
        speechRate: 1.0,
        pageStructure: false
      };
      
      // Remove all classes and styles
      document.body.className = document.body.className.split(' ').filter(c => !c.startsWith('complyo-')).join(' ');
      document.body.style.fontSize = '';
      document.body.style.lineHeight = '';
      document.body.style.letterSpacing = '';
      document.body.style.wordSpacing = '';
      document.body.style.filter = '';
      document.body.removeAttribute('data-font-scale');
      
      // Remove CSS-Variablen vom HTML-Element
      document.documentElement.style.removeProperty('--complyo-font-scale');
      
      // Stop speech
      this.stopSpeech();
      
      // Remove tooltips and bionic reading
      this.removeTooltips();
      this.removeBionicReading();
      
      // Update UI
      this.applyAllFeatures();
      this.updateAllControls();
      this.savePreferences();
      
      this.trackAnalytics('reset_all', true);
    }
    
    updateAllControls() {
      // Update all slider values
      this.container.querySelector('#complyo-font-size').value = this.features.fontSize;
      this.updateSliderValue('complyo-font-size-value', this.features.fontSize + '%');
      
      this.container.querySelector('#complyo-line-height').value = this.features.lineHeight;
      this.updateSliderValue('complyo-line-height-value', this.features.lineHeight + '%');
      
      this.container.querySelector('#complyo-letter-spacing').value = this.features.letterSpacing;
      this.updateSliderValue('complyo-letter-spacing-value', this.features.letterSpacing + 'px');
      
      this.container.querySelector('#complyo-word-spacing').value = this.features.wordSpacing;
      this.updateSliderValue('complyo-word-spacing-value', this.features.wordSpacing + 'px');
      
      this.container.querySelector('#complyo-brightness').value = this.features.brightness;
      this.updateSliderValue('complyo-brightness-value', this.features.brightness + '%');
      
      this.container.querySelector('#complyo-saturation').value = this.features.saturation;
      this.updateSliderValue('complyo-saturation-value', this.features.saturation + '%');
      
      this.container.querySelector('#complyo-speech-rate').value = this.features.speechRate;
      this.updateSliderValue('complyo-speech-rate-value', this.features.speechRate.toFixed(1) + 'x');
      
      // Update checkboxes
      Object.keys(this.features).forEach(feature => {
        if (typeof this.features[feature] === 'boolean') {
          const checkbox = this.container.querySelector(`#complyo-${feature.replace(/([A-Z])/g, '-$1').toLowerCase()}`);
          if (checkbox && checkbox.type === 'checkbox') {
            checkbox.checked = this.features[feature];
          }
        }
      });
      
      // Update select
      this.container.querySelector('#complyo-color-filter').value = this.features.colorFilter;
    }
    
    applyAllFeatures() {
      Object.keys(this.features).forEach(feature => {
        this.applyFeature(feature);
      });
    }
    
    togglePanel() {
      this.isOpen = !this.isOpen;
      const panel = this.container.querySelector('.complyo-panel');
      const toggleBtn = this.container.querySelector('.complyo-toggle-btn');
      
      panel.hidden = !this.isOpen;
      toggleBtn.setAttribute('aria-expanded', this.isOpen);
      
      if (this.isOpen) {
        this.trackAnalytics('widget_open', true);
      }
    }
    
    closePanel() {
      this.isOpen = false;
      const panel = this.container.querySelector('.complyo-panel');
      const toggleBtn = this.container.querySelector('.complyo-toggle-btn');
      
      panel.hidden = true;
      toggleBtn.setAttribute('aria-expanded', 'false');
    }
    
    loadPreferences() {
      try {
        const saved = localStorage.getItem('complyo_a11y_preferences');
        if (saved) {
          const prefs = JSON.parse(saved);
          this.features = { ...this.features, ...prefs };
        }
      } catch (e) {
        console.warn('Could not load preferences:', e);
      }
    }
    
    savePreferences() {
      try {
        localStorage.setItem('complyo_a11y_preferences', JSON.stringify(this.features));
      } catch (e) {
        console.warn('Could not save preferences:', e);
      }
    }
    
    async loadAndApplyAltTexts() {
      try {
        const response = await fetch(
          `${API_BASE}/api/accessibility/alt-text-fixes?site_id=${this.config.siteId}`
        );
        
        if (!response.ok) return;
        
        const data = await response.json();
        
        if (data.success && data.fixes && data.fixes.length > 0) {
          this.applyAltTextFixes(data.fixes);
          console.log(`✅ ${data.fixes.length} Alt-Texte angewendet (runtime)`);
        }
      } catch (e) {
        console.warn('Alt-Text-Fixes konnten nicht geladen werden:', e);
      }
    }
    
    applyAltTextFixes(fixes) {
      fixes.forEach(fix => {
        const selectors = [
          `img[src="${fix.image_src}"]`,
          `img[src*="${fix.image_filename}"]`,
          `img[data-src="${fix.image_src}"]`,
          `img[srcset*="${fix.image_filename}"]`
        ];
        
        for (const selector of selectors) {
          const images = document.querySelectorAll(selector);
          images.forEach(img => {
            if (!img.alt || img.alt.trim() === '') {
              img.setAttribute('alt', fix.suggested_alt);
              img.setAttribute('data-complyo-alt', 'runtime');
            }
          });
        }
      });
      
      // Observe for dynamically loaded images
      const observer = new MutationObserver(() => {
        this.applyAltTextFixes(fixes);
      });
      
      observer.observe(document.body, {
        childList: true,
        subtree: true
      });
    }
    
    trackAnalytics(feature, value) {
      try {
        fetch(`${API_BASE}/api/widgets/analytics`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            site_id: this.config.siteId,
            session_id: this.sessionId,
            feature: feature,
            value: value,
            timestamp: Date.now()
          })
        }).catch(e => console.warn('Analytics failed:', e));
      } catch (e) {
        // Silent fail
      }
    }
    
    injectCSS() {
      const style = document.createElement('style');
      style.id = 'complyo-a11y-styles';
      style.textContent = `
        /* Widget Container */
        #complyo-a11y-widget {
          position: fixed;
          z-index: 999999;
          font-family: system-ui, -apple-system, sans-serif;
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
          color: white;
          border: none;
          box-shadow: 0 4px 12px rgba(124, 58, 237, 0.3);
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: all 0.3s ease;
        }
        
        .complyo-toggle-btn:hover {
          transform: scale(1.1);
          box-shadow: 0 6px 16px rgba(124, 58, 237, 0.4);
        }
        
        /* Panel */
        .complyo-panel {
          position: absolute;
          bottom: 75px;
          right: 0;
          width: 380px;
          max-height: 80vh;
          background: white;
          border-radius: 16px;
          box-shadow: 0 10px 40px rgba(0,0,0,0.2);
          overflow: hidden;
          display: flex;
          flex-direction: column;
        }
        
        .complyo-panel-header {
          background: linear-gradient(135deg, #7c3aed 0%, #5b21b6 100%);
          color: white;
          padding: 16px 20px;
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
          background: rgba(255,255,255,0.2);
          border: none;
          color: white;
          width: 32px;
          height: 32px;
          border-radius: 50%;
          cursor: pointer;
          font-size: 18px;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: background 0.2s;
        }
        
        .complyo-close-btn:hover {
          background: rgba(255,255,255,0.3);
        }
        
        .complyo-panel-content {
          overflow-y: auto;
          padding: 20px;
          max-height: calc(80vh - 120px);
        }
        
        .complyo-section {
          margin-bottom: 24px;
          padding-bottom: 20px;
          border-bottom: 1px solid #e5e7eb;
        }
        
        .complyo-section:last-child {
          border-bottom: none;
          margin-bottom: 0;
        }
        
        .complyo-section h4 {
          margin: 0 0 16px 0;
          font-size: 15px;
          font-weight: 600;
          color: #1f2937;
        }
        
        .complyo-control {
          margin-bottom: 16px;
        }
        
        .complyo-control:last-child {
          margin-bottom: 0;
        }
        
        .complyo-control label {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 14px;
          color: #4b5563;
          cursor: pointer;
        }
        
        .complyo-control input[type="checkbox"] {
          width: 18px;
          height: 18px;
          cursor: pointer;
        }
        
        .complyo-control input[type="range"] {
          width: 100%;
          height: 6px;
          border-radius: 3px;
          background: #e5e7eb;
          outline: none;
          margin-top: 8px;
        }
        
        .complyo-control input[type="range"]::-webkit-slider-thumb {
          -webkit-appearance: none;
          appearance: none;
          width: 16px;
          height: 16px;
          border-radius: 50%;
          background: #7c3aed;
          cursor: pointer;
        }
        
        .complyo-control input[type="range"]::-moz-range-thumb {
          width: 16px;
          height: 16px;
          border-radius: 50%;
          background: #7c3aed;
          cursor: pointer;
          border: none;
        }
        
        .complyo-slider-controls {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-top: 8px;
        }
        
        .complyo-slider-controls input[type="range"] {
          flex: 1;
          margin-top: 0;
        }
        
        .complyo-btn-small {
          width: 32px;
          height: 32px;
          border-radius: 6px;
          background: #f3f4f6;
          border: 1px solid #d1d5db;
          color: #374151;
          cursor: pointer;
          font-size: 16px;
          font-weight: 600;
          transition: all 0.2s;
        }
        
        .complyo-btn-small:hover {
          background: #e5e7eb;
        }
        
        .complyo-select {
          width: 100%;
          padding: 8px 12px;
          border-radius: 6px;
          border: 1px solid #d1d5db;
          font-size: 14px;
          margin-top: 8px;
          cursor: pointer;
        }
        
        .complyo-btn-group {
          display: flex;
          gap: 8px;
          margin-top: 8px;
        }
        
        .complyo-btn-icon {
          flex: 1;
          padding: 10px;
          border-radius: 6px;
          background: #f3f4f6;
          border: 1px solid #d1d5db;
          cursor: pointer;
          transition: all 0.2s;
        }
        
        .complyo-btn-icon:hover,
        .complyo-btn-icon.active {
          background: #7c3aed;
          color: white;
          border-color: #7c3aed;
        }
        
        .complyo-btn-full {
          width: 100%;
          padding: 10px 16px;
          border-radius: 8px;
          background: #f3f4f6;
          border: 1px solid #d1d5db;
          font-size: 14px;
          cursor: pointer;
          transition: all 0.2s;
        }
        
        .complyo-btn-full:hover {
          background: #e5e7eb;
        }
        
        .complyo-tts-buttons {
          display: flex;
          gap: 8px;
          margin-top: 8px;
        }
        
        .complyo-panel-footer {
          padding: 16px 20px;
          border-top: 1px solid #e5e7eb;
          display: flex;
          justify-content: space-between;
          align-items: center;
          background: #f9fafb;
        }
        
        .complyo-panel-footer small {
          color: #6b7280;
          font-size: 12px;
        }
        
        .complyo-btn-reset {
          padding: 8px 16px;
          border-radius: 8px;
          background: #ef4444;
          color: white;
          border: none;
          font-size: 13px;
          font-weight: 500;
          cursor: pointer;
          transition: background 0.2s;
        }
        
        .complyo-btn-reset:hover {
          background: #dc2626;
        }
        
        /* WICHTIG: Hidden Elements verstecken */
        [hidden] {
          display: none !important;
        }
        
        /* Reading Guide */
        .complyo-reading-guide {
          position: fixed;
          left: 0;
          right: 0;
          height: 3px;
          background: rgba(124, 58, 237, 0.5);
          pointer-events: none;
          z-index: 999998;
          box-shadow: 0 0 20px rgba(124, 58, 237, 0.3);
        }
        
        /* Page Structure Overlay */
        .complyo-page-structure-overlay {
          position: fixed;
          top: 20px;
          right: 420px;
          width: 320px;
          max-height: 80vh;
          background: white;
          border-radius: 12px;
          box-shadow: 0 10px 40px rgba(0,0,0,0.2);
          overflow: hidden;
          z-index: 999998;
        }
        
        .complyo-structure-header {
          background: #7c3aed;
          color: white;
          padding: 16px;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        
        .complyo-structure-header h3 {
          margin: 0;
          font-size: 16px;
        }
        
        .complyo-structure-close {
          background: rgba(255,255,255,0.2);
          border: none;
          color: white;
          width: 28px;
          height: 28px;
          border-radius: 50%;
          cursor: pointer;
        }
        
        .complyo-structure-content {
          padding: 16px;
          overflow-y: auto;
          max-height: calc(80vh - 60px);
        }
        
        .complyo-structure-section h4 {
          margin: 0 0 12px 0;
          font-size: 14px;
          font-weight: 600;
          color: #1f2937;
        }
        
        .complyo-structure-section ul {
          list-style: none;
          padding: 0;
          margin: 0 0 20px 0;
        }
        
        .complyo-structure-section li {
          padding: 8px 12px;
          margin: 4px 0;
          border-radius: 6px;
          background: #f3f4f6;
          cursor: pointer;
          font-size: 13px;
          transition: background 0.2s;
        }
        
        .complyo-structure-section li:hover {
          background: #e5e7eb;
        }
        
        .complyo-structure-tag {
          display: inline-block;
          padding: 2px 6px;
          border-radius: 4px;
          background: #7c3aed;
          color: white;
          font-size: 10px;
          font-weight: 600;
          margin-right: 8px;
        }
        
        .complyo-structure-h1 { padding-left: 12px; }
        .complyo-structure-h2 { padding-left: 24px; }
        .complyo-structure-h3 { padding-left: 36px; }
        .complyo-structure-h4 { padding-left: 48px; }
        .complyo-structure-h5 { padding-left: 60px; }
        .complyo-structure-h6 { padding-left: 72px; }
        
        /* Keyboard Guide Modal */
        .complyo-keyboard-modal {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0,0,0,0.5);
          display: none; /* Standardmäßig versteckt */
          align-items: center;
          justify-content: center;
          z-index: 1000000;
        }
        
        /* Wenn nicht hidden, dann anzeigen */
        .complyo-keyboard-modal:not([hidden]) {
          display: flex;
        }
        
        .complyo-modal-content {
          background: white;
          border-radius: 16px;
          width: 90%;
          max-width: 500px;
          max-height: 80vh;
          overflow: hidden;
          box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        
        .complyo-modal-header {
          background: #7c3aed;
          color: white;
          padding: 20px;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        
        .complyo-modal-header h3 {
          margin: 0;
          font-size: 18px;
        }
        
        .complyo-modal-close {
          background: rgba(255,255,255,0.2);
          border: none;
          color: white;
          width: 32px;
          height: 32px;
          border-radius: 50%;
          cursor: pointer;
          font-size: 18px;
        }
        
        .complyo-modal-body {
          padding: 24px;
          overflow-y: auto;
          max-height: calc(80vh - 80px);
        }
        
        .complyo-shortcut {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 12px;
          margin: 8px 0;
          border-radius: 8px;
          background: #f3f4f6;
        }
        
        .complyo-shortcut kbd {
          padding: 4px 8px;
          border-radius: 4px;
          background: white;
          border: 1px solid #d1d5db;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1);
          font-family: monospace;
          font-size: 12px;
          margin: 0 2px;
        }
        
        .complyo-shortcut span {
          font-size: 13px;
          color: #4b5563;
        }
        
        /* Feature Styles */
        
        /* ✨ SCHRIFTGRÖSSE: Universelle Skalierung für ALLE Texte */
        body.complyo-scaled-text *:not(#complyo-a11y-widget):not(#complyo-a11y-widget *) {
          font-size: calc(1em * var(--complyo-font-scale, 1)) !important;
        }
        
        /* Spezifische Skalierung für Überschriften */
        body.complyo-scaled-text h1:not(#complyo-a11y-widget):not(#complyo-a11y-widget *) {
          font-size: calc(2.5em * var(--complyo-font-scale, 1)) !important;
        }
        
        body.complyo-scaled-text h2:not(#complyo-a11y-widget):not(#complyo-a11y-widget *) {
          font-size: calc(2em * var(--complyo-font-scale, 1)) !important;
        }
        
        body.complyo-scaled-text h3:not(#complyo-a11y-widget):not(#complyo-a11y-widget *) {
          font-size: calc(1.75em * var(--complyo-font-scale, 1)) !important;
        }
        
        body.complyo-scaled-text h4:not(#complyo-a11y-widget):not(#complyo-a11y-widget *) {
          font-size: calc(1.5em * var(--complyo-font-scale, 1)) !important;
        }
        
        body.complyo-scaled-text h5:not(#complyo-a11y-widget):not(#complyo-a11y-widget *) {
          font-size: calc(1.25em * var(--complyo-font-scale, 1)) !important;
        }
        
        body.complyo-scaled-text h6:not(#complyo-a11y-widget):not(#complyo-a11y-widget *) {
          font-size: calc(1em * var(--complyo-font-scale, 1)) !important;
        }
        
        /* Buttons und Inputs auch skalieren */
        body.complyo-scaled-text button:not(#complyo-a11y-widget):not(#complyo-a11y-widget *),
        body.complyo-scaled-text input:not(#complyo-a11y-widget):not(#complyo-a11y-widget *),
        body.complyo-scaled-text select:not(#complyo-a11y-widget):not(#complyo-a11y-widget *),
        body.complyo-scaled-text textarea:not(#complyo-a11y-widget):not(#complyo-a11y-widget *) {
          font-size: calc(1em * var(--complyo-font-scale, 1)) !important;
        }
        
        /* ⚠️ KRITISCH: Widget bei hohem Kontrast sichtbar halten */
        body.complyo-high-contrast #complyo-a11y-widget {
          filter: none !important;
          isolation: isolate;
        }
        
        /* Sicherstellen dass der Button immer sichtbar bleibt */
        body.complyo-high-contrast .complyo-toggle-btn {
          background: linear-gradient(135deg, #7c3aed 0%, #5b21b6 100%) !important;
          color: white !important;
          box-shadow: 0 4px 12px rgba(124, 58, 237, 0.4) !important;
          filter: none !important;
        }
        
        /* Panel auch normal darstellen */
        body.complyo-high-contrast .complyo-panel {
          filter: none !important;
          background: white !important;
          color: #1f2937 !important;
        }
        
        /* Night Mode */
        body.complyo-night-mode {
          filter: invert(1) hue-rotate(180deg);
        }
        
        body.complyo-night-mode #complyo-a11y-widget {
          filter: invert(1) hue-rotate(180deg);
        }
        
        body.complyo-highlight-links a {
          background-color: #fef3c7 !important;
          padding: 2px 4px !important;
          border-radius: 2px !important;
          text-decoration: underline !important;
        }
        
        body.complyo-readable-font {
          font-family: Arial, Helvetica, sans-serif !important;
        }
        
        body.complyo-dyslexia-font {
          font-family: 'Comic Sans MS', 'OpenDyslexic', Arial, sans-serif !important;
        }
        
        body.complyo-align-left * {
          text-align: left !important;
        }
        
        body.complyo-align-center * {
          text-align: center !important;
        }
        
        body.complyo-align-right * {
          text-align: right !important;
        }
        
        body.complyo-hide-images img {
          opacity: 0 !important;
          visibility: hidden !important;
        }
        
        body.complyo-show-tooltips [title]:hover::after {
          content: attr(title);
          position: absolute;
          background: #1f2937;
          color: white;
          padding: 8px 12px;
          border-radius: 6px;
          font-size: 12px;
          z-index: 999999;
          white-space: nowrap;
          pointer-events: none;
        }
        
        body.complyo-stop-animations * {
          animation: none !important;
          transition: none !important;
        }
        
        body.complyo-big-cursor,
        body.complyo-big-cursor * {
          cursor: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24"><path fill="white" stroke="black" stroke-width="1" d="M3 3l7.07 16.97 2.51-7.39 7.39-2.51L3 3z"/></svg>') 12 12, auto !important;
        }
        
        .complyo-bionic {
          font-weight: 700 !important;
        }
      `;
      
      document.head.appendChild(style);
    }
  }
  
  // Auto-Initialize
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      new ComplyoAccessibilityWidget();
    });
  } else {
    new ComplyoAccessibilityWidget();
  }
  
})();

