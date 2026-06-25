/**
 * Complyo Accessibility Widget v6.0 - NEXT LEVEL EDITION
 * ========================================================
 * Modernes Grid-Layout wie UserWay mit Feature-Tiles
 * 
 * Features:
 * ✅ Grid-Layout (3 Spalten)
 * ✅ Große, klickbare Feature-Kacheln
 * ✅ Checkmarks bei aktivierten Features
 * ✅ Moderne Icons
 * ✅ Hover-Effekte
 * ✅ 30+ Features
 * 
 * © 2025 Complyo.tech
 */

(function() {
  'use strict';
  
  const WIDGET_VERSION = '6.0.0';
  const _currentScript = document.currentScript || (function() {
    const scripts = document.getElementsByTagName('script');
    return scripts[scripts.length - 1];
  })();
  const API_BASE = (window.location.hostname === 'localhost')
    ? 'http://localhost:8000'
    : (_currentScript && _currentScript.getAttribute('data-api-base')) || 'https://api.complyo.de';
  
  // Multi-Language Translations
  const TRANSLATIONS = {
    de: {
      title: 'Barrierefreiheit Menü (CTRL+U)',
      language: 'Deutsch (German)',
      accessibilityProfiles: 'Zugänglichkeitsprofile',
      fontSize: 'Schriftgröße',
      lineHeight: 'Zeilenhöhe',
      letterSpacing: 'Buchstabenabstand',
      wordSpacing: 'Wortabstand',
      textAlign: 'Textausrichtung',
      colorFilter: 'Farbfilter',
      brightness: 'Helligkeit',
      saturation: 'Sättigung',
      speechRate: 'Sprechgeschwindigkeit',
      resetAll: 'Alle zurücksetzen',
      keyboardShortcuts: 'Tastaturkürzel',
      close: 'Schließen',
      // Feature Names
      contrast: 'Kontrast +',
      highlightLinks: 'Mark. Sie Links',
      readableFont: 'Leseschrift',
      dyslexiaFont: 'Legasthenie-Schrift',
      bigCursor: 'Großer Cursor',
      hideImages: 'Bilder ausblenden',
      stopAnimations: 'Stoppen Sie Animationen',
      invertColors: 'Farben invertieren',
      nightMode: 'Nachtmodus',
      grayscale: 'Graustufen',
      readingGuide: 'Leseleitfaden',
      pageStructure: 'Seitenstruktur',
      textToSpeech: 'Text-zu-Sprache',
      showTooltips: 'Tooltips anzeigen',
      bionicReading: 'Bionisches Lesen',
      xlWidget: 'Übergroßes Widget',
      smartContrast: 'Intelligenter Kontrast',
      groserText: 'Großer Text',
      textabstand: 'Textabstand',
      bilderAusblenden: 'Bilder ausblenden',
      legasthenieFreundlich: 'Legasthenie-freundlich',
      zeiger: 'Zeiger',
      kurzinfos: 'Kurzinfos',
      seitenstruktur: 'Seitenstruktur',
      zeilenhohe: 'Zeilenhöhe',
      textausrichtung: 'Textausrichtung',
      vorlesen: 'Vorlesen',
      sprachnavigation: 'Sprachnavigation',
      // UI-Strings (Footer, Modals, Tabs)
      resetAllSettings: 'Alle Einstellungen zurücksetzen',
      resetTextSettings: 'Text-Einstellungen zurücksetzen',
      textSettings: 'Text-Einstellungen',
      tabHeadings: 'Überschriften',
      tabLandmarks: 'Bereiche',
      tabLinks: 'Links',
      alignDefault: 'Standard',
      alignLeft: 'Linksbündig',
      alignCenter: 'Zentriert',
      alignRight: 'Rechtsbündig'
    },
    en: {
      title: 'Accessibility Menu (CTRL+U)',
      language: 'English',
      accessibilityProfiles: 'Accessibility Profiles',
      fontSize: 'Font Size',
      lineHeight: 'Line Height',
      letterSpacing: 'Letter Spacing',
      wordSpacing: 'Word Spacing',
      textAlign: 'Text Alignment',
      colorFilter: 'Color Filter',
      brightness: 'Brightness',
      saturation: 'Saturation',
      speechRate: 'Speech Rate',
      resetAll: 'Reset All',
      keyboardShortcuts: 'Keyboard Shortcuts',
      close: 'Close',
      // Feature Names
      contrast: 'Contrast +',
      highlightLinks: 'Highlight Links',
      readableFont: 'Readable Font',
      dyslexiaFont: 'Dyslexia Font',
      bigCursor: 'Big Cursor',
      hideImages: 'Hide Images',
      stopAnimations: 'Stop Animations',
      invertColors: 'Invert Colors',
      nightMode: 'Night Mode',
      grayscale: 'Grayscale',
      readingGuide: 'Reading Guide',
      pageStructure: 'Page Structure',
      textToSpeech: 'Text-to-Speech',
      showTooltips: 'Show Tooltips',
      bionicReading: 'Bionic Reading',
      xlWidget: 'XL Widget',
      smartContrast: 'Smart Contrast',
      groserText: 'Large Text',
      textabstand: 'Text Spacing',
      bilderAusblenden: 'Hide Images',
      legasthenieFreundlich: 'Dyslexia Friendly',
      zeiger: 'Cursor',
      kurzinfos: 'Tooltips',
      seitenstruktur: 'Page Structure',
      zeilenhohe: 'Line Height',
      textausrichtung: 'Text Alignment',
      vorlesen: 'Read Aloud',
      sprachnavigation: 'Voice Navigation',
      // UI strings (footer, modals, tabs)
      resetAllSettings: 'Reset All Settings',
      resetTextSettings: 'Reset Text Settings',
      textSettings: 'Text Settings',
      tabHeadings: 'Headings',
      tabLandmarks: 'Landmarks',
      tabLinks: 'Links',
      alignDefault: 'Default',
      alignLeft: 'Left',
      alignCenter: 'Center',
      alignRight: 'Right'
    }
  };
  
  class ComplyoAccessibilityWidget {
    constructor(config = {}) {
      this.config = {
        siteId: config.siteId || this.getSiteIdFromScript(),
        showToolbar: config.showToolbar !== false,
        position: config.position || 'bottom-right',
        language: config.language || 'de'
      };
      
      // Simplified features for tile-based UI
      this.features = {
        // Toggle Features (Tiles)
        contrast: false,
        highlightLinks: false,
        readableFont: false,
        dyslexiaFont: false,
        bigCursor: false,
        hideImages: false,
        stopAnimations: false,
        invertColors: false,
        nightMode: false,
        grayscale: false,
        readingGuide: false,
        pageStructure: false,
        textToSpeech: false,
        showTooltips: false,
        bionicReading: false,
        
        // Adjustable Features (mit Sliders)
        fontSize: 100,
        lineHeight: 150,
        letterSpacing: 0,
        wordSpacing: 0,
        brightness: 100,
        saturation: 100,
        textAlign: 'default',
        colorFilter: 'none',
        speechRate: 1.0
      };
      
      this.sessionId = this.generateSessionId();
      this.isOpen = false;
      this.speechSynthesis = window.speechSynthesis;
      this.currentUtterance = null;
      
      this.init();
    }
    
    async init() {
      console.log(`🚀 Initializing Complyo Widget v${WIDGET_VERSION} with site-id: ${this.config.siteId}`);

      // 🔒 Lizenzprüfung: Wurde die Website im Complyo-Dashboard entfernt, ist die
      // Lizenz entzogen → das Widget wird nicht gerendert und funktioniert nicht.
      const licensed = await this.checkLicense();
      if (!licensed) {
        console.warn('[Complyo] Keine aktive Lizenz für diese Website – Barrierefreiheits-Widget deaktiviert.');
        return;
      }

      this.loadPreferences();
      this.injectCSS(); // CSS ZUERST injizieren!
      this.renderToolbar();
      this.applyAllFeatures();
      await this.loadAndApplyAltTexts();
      this.setupKeyboardShortcuts();
      this.startVisibilityWatcher(); // KRITISCH: Widget-Sichtbarkeit ständig überwachen
      this.startPositionWatcher(); // Theme-Scroll-to-Top-Button erkennen & links daneben ausweichen

      console.log(`🎨 Complyo Accessibility Widget v${WIDGET_VERSION} initialized`);
    }
    
    startVisibilityWatcher() {
      // Widget-Sichtbarkeit alle 500ms garantieren
      setInterval(() => {
        const widget = document.getElementById('complyo-a11y-widget');
        if (!widget) return;
        
        // Nur aktiv prüfen wenn Filter aktiv sind
        if (this.features.contrast || this.features.invertColors || this.features.grayscale || this.features.nightMode) {
          const filters = [];
          if (this.features.invertColors) filters.push('invert(1)');
          if (this.features.nightMode) {
            filters.push('invert(1)');
            filters.push('hue-rotate(180deg)');
          }
          this.ensureWidgetVisibility(filters);
        }
      }, 500);
    }

    // Erkennt einen fixierten Theme-Button unten rechts (z. B. Scroll-to-Top) und
    // setzt das Widget links daneben auf gleiche Höhe. Wird keiner gefunden, bleibt
    // das Widget am Standardplatz unten rechts (20/20).
    startPositionWatcher() {
      // Nur für die Standard-Ecke unten rechts relevant
      if ((this.config.position || 'bottom-right') !== 'bottom-right') return;

      const apply = () => this.positionWidget();
      // Initial + nach vollständigem Laden
      apply();
      window.addEventListener('load', apply, { once: true });
      // Theme-Top-Buttons erscheinen oft erst beim Scrollen → reagieren
      let raf = null;
      const onScrollResize = () => {
        if (raf) return;
        raf = requestAnimationFrame(() => { raf = null; apply(); });
      };
      window.addEventListener('scroll', onScrollResize, { passive: true });
      window.addEventListener('resize', onScrollResize, { passive: true });
      // Sicherheitsnetz: ein paar verzögerte Durchläufe für spät injizierte Buttons
      setTimeout(apply, 800);
      setTimeout(apply, 2500);
    }

    positionWidget() {
      const widget = this.container || document.getElementById('complyo-a11y-widget');
      if (!widget) return;
      // Während das Panel offen ist nicht verschieben
      if (this.isOpen) return;

      const GAP = 12;            // Abstand zum Theme-Button
      const vw = window.innerWidth;
      const vh = window.innerHeight;
      const topBtn = this.findCornerButton();

      // Sanftes Umpositionieren ab dem zweiten Durchlauf (kein Slide beim ersten Render)
      if (this._positioned) {
        widget.style.transition = 'right 0.2s ease, bottom 0.2s ease';
      }
      this._positioned = true;

      if (topBtn) {
        const r = topBtn.getBoundingClientRect();
        // Links neben den Button, Unterkanten bündig
        const right = Math.max(Math.round(vw - r.left + GAP), 20);
        const bottom = Math.max(Math.round(vh - r.bottom), 0);
        widget.style.right = right + 'px';
        widget.style.bottom = bottom + 'px';
        widget.dataset.complyoDodge = '1';
      } else {
        widget.style.right = '20px';
        widget.style.bottom = '20px';
        widget.dataset.complyoDodge = '0';
      }
    }

    // Sucht den fixierten "nach oben"-Button des Themes in der unteren rechten Ecke.
    findCornerButton() {
      const vw = window.innerWidth;
      const vh = window.innerHeight;

      const isOwn = (el) =>
        el.id === 'complyo-a11y-widget' || el.closest('#complyo-a11y-widget') ||
        el.id === 'complyo-cookie-settings-btn' || el.closest('#complyo-cookie-settings-btn');

      const inCorner = (el) => {
        if (!el || el.nodeType !== 1 || isOwn(el)) return false;
        let cs;
        try { cs = getComputedStyle(el); } catch (e) { return false; }
        if (cs.position !== 'fixed' && cs.position !== 'sticky') return false;
        if (cs.visibility === 'hidden' || cs.display === 'none' || parseFloat(cs.opacity || '1') === 0) return false;
        const r = el.getBoundingClientRect();
        if (r.width < 16 || r.height < 16 || r.width > 96 || r.height > 96) return false; // nur kleine Buttons
        const nearRight = (vw - r.right) <= 90 && r.right <= vw + 6;
        const nearBottom = (vh - r.bottom) <= 160 && r.bottom <= vh + 6;
        return nearRight && nearBottom;
      };

      // 1) Häufige Selektoren für Scroll-to-Top-Buttons
      const SELECTORS = [
        '[class*="scroll-top" i]', '[class*="scrolltop" i]', '[class*="scroll-to-top" i]',
        '[class*="back-to-top" i]', '[class*="backtotop" i]', '[class*="back_to_top" i]',
        '[id*="scroll-top" i]', '[id*="scrolltop" i]', '[id*="scrollup" i]',
        '[id*="back-to-top" i]', '[id*="backtotop" i]',
        '[aria-label*="nach oben" i]', '[aria-label*="scroll to top" i]', '[aria-label*="back to top" i]',
        '[title*="nach oben" i]', '[title*="scroll to top" i]', '[title*="back to top" i]',
        'a[href="#top"]', 'a[href="#"]'
      ];
      let candidates = [];
      try { candidates = Array.from(document.querySelectorAll(SELECTORS.join(','))); } catch (e) {}
      const hit = candidates.find(inCorner);
      if (hit) return hit;

      // 2) Generischer, begrenzter Scan über fixierte Elemente unten rechts
      const all = document.body ? document.body.querySelectorAll('*') : [];
      const max = Math.min(all.length, 4000); // Performance-Grenze
      for (let i = 0; i < max; i++) {
        if (inCorner(all[i])) return all[i];
      }
      return null;
    }

    getSiteIdFromScript() {
      const scripts = document.querySelectorAll('script[data-site-id]');
      if (scripts.length > 0) {
        return scripts[scripts.length - 1].getAttribute('data-site-id');
      }
      return 'demo';
    }

    // 🔒 Prüft, ob für diese Website noch eine aktive Lizenz besteht.
    // Fail-open: bei Fehlern/Demo wird das Widget normal angezeigt.
    async checkLicense() {
      try {
        const siteId = this.config.siteId;
        if (!siteId || siteId === 'demo') return true;
        const res = await fetch(`${API_BASE}/api/widgets/config/${siteId}`);
        if (!res.ok) return true;
        const data = await res.json();
        return data.license_active !== false;
      } catch (e) {
        return true;
      }
    }
    
    generateSessionId() {
      return 'sess_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    // Translation Helper
    t(key) {
      const lang = this.config.language || 'de';
      return TRANSLATIONS[lang]?.[key] || TRANSLATIONS['de'][key] || key;
    }
    
    changeLanguage(lang) {
      this.config.language = lang;
      this.savePreferences();
      
      // Einfach nur neu übersetzen, kein Re-Render!
      this.applyTranslations();
    }
    
    renderToolbar() {
      const container = document.createElement('div');
      container.id = 'complyo-a11y-widget';
      container.className = `complyo-widget-${this.config.position}`;
      
      container.innerHTML = `
        <button class="complyo-toggle-btn" aria-label="Barrierefreiheit öffnen" aria-expanded="false" title="Barrierefreiheit (CTRL+U)">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <!-- Universal Accessibility Symbol -->
            <circle cx="12" cy="12" r="10"/>
            <circle cx="12" cy="8" r="1.5" fill="currentColor"/>
            <path d="M12 10.5v5"/>
            <path d="M9 13l-1.5 3"/>
            <path d="M15 13l1.5 3"/>
            <path d="M8 13h8"/>
          </svg>
        </button>
        
        <div class="complyo-panel" hidden>
          <div class="complyo-panel-header">
            <h3 data-i18n="title">Accessibility Menu (CTRL+U)</h3>
            <button class="complyo-close-btn" aria-label="Schließen" title="Schließen">✕</button>
          </div>
          
          <!-- Language Switcher -->
          <div class="complyo-language-selector">
            <button class="complyo-lang-btn ${this.config.language === 'de' ? 'active' : ''}" data-lang="de">
              <span class="complyo-lang-flag">🇩🇪</span>
              <span>DE</span>
            </button>
            <button class="complyo-lang-btn ${this.config.language === 'en' ? 'active' : ''}" data-lang="en">
              <span class="complyo-lang-flag">🇬🇧</span>
              <span>EN</span>
            </button>
          </div>
          
          <div class="complyo-panel-content">
            <!-- Feature Grid -->
            <div class="complyo-feature-grid">
              
              <!-- Contrast -->
              <div class="complyo-feature-tile" data-feature="contrast">
                <div class="complyo-tile-icon">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"/>
                    <path d="M12 2 A10 10 0 0 1 12 22 Z" fill="currentColor"/>
                  </svg>
                </div>
                <div class="complyo-tile-label" data-i18n="smartContrast">Contrast +</div>
                <div class="complyo-tile-check" hidden>✓</div>
              </div>
              
              <!-- Highlight Links -->
              <div class="complyo-feature-tile" data-feature="highlightLinks">
                <div class="complyo-tile-icon">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
                    <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
                  </svg>
                </div>
                <div class="complyo-tile-label" data-i18n="highlightLinks">Highlight Links</div>
                <div class="complyo-tile-check" hidden>✓</div>
              </div>
              
              <!-- Bigger Text -->
              <div class="complyo-feature-tile" data-feature="fontSize">
                <div class="complyo-tile-icon">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="4 7 4 4 20 4 20 7"/>
                    <line x1="9" y1="20" x2="15" y2="20"/>
                    <line x1="12" y1="4" x2="12" y2="20"/>
                  </svg>
                </div>
                <div class="complyo-tile-label" data-i18n="groserText">Bigger Text</div>
                <div class="complyo-tile-check" hidden>✓</div>
              </div>
              
              <!-- Text Spacing -->
              <div class="complyo-feature-tile" data-feature="letterSpacing">
                <div class="complyo-tile-icon">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="3 7 3 4 21 4 21 7"/>
                    <line x1="8" y1="20" x2="16" y2="20"/>
                    <line x1="12" y1="4" x2="12" y2="20"/>
                    <line x1="3" y1="12" x2="8" y2="12"/>
                    <line x1="16" y1="12" x2="21" y2="12"/>
                  </svg>
                </div>
                <div class="complyo-tile-label" data-i18n="textabstand">Text Spacing</div>
                <div class="complyo-tile-check" hidden>✓</div>
              </div>
              
              <!-- Line Height -->
              <div class="complyo-feature-tile" data-feature="lineHeight">
                <div class="complyo-tile-icon">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="8" y1="6" x2="21" y2="6"/>
                    <line x1="8" y1="12" x2="21" y2="12"/>
                    <line x1="8" y1="18" x2="21" y2="18"/>
                    <line x1="3" y1="6" x2="3" y2="18"/>
                    <polyline points="3 18 5 16 3 14"/>
                    <polyline points="3 6 5 8 3 10"/>
                  </svg>
                </div>
                <div class="complyo-tile-label" data-i18n="zeilenhohe">Line Height</div>
                <div class="complyo-tile-check" hidden>✓</div>
              </div>
              
              <!-- Text Align -->
              <div class="complyo-feature-tile" data-feature="textAlign">
                <div class="complyo-tile-icon">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="21" y1="10" x2="3" y2="10"/>
                    <line x1="21" y1="6" x2="3" y2="6"/>
                    <line x1="21" y1="14" x2="3" y2="14"/>
                    <line x1="21" y1="18" x2="3" y2="18"/>
                  </svg>
                </div>
                <div class="complyo-tile-label" data-i18n="textausrichtung">Text Align</div>
                <div class="complyo-tile-check" hidden>✓</div>
              </div>
              
              <!-- Dyslexia Friendly -->
              <div class="complyo-feature-tile" data-feature="dyslexiaFont">
                <div class="complyo-tile-icon">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M4 7V4h16v3"/>
                    <path d="M9 20h6"/>
                    <path d="M12 4v16"/>
                    <text x="12" y="14" text-anchor="middle" fill="currentColor" font-size="8" font-weight="bold">Df</text>
                  </svg>
                </div>
                <div class="complyo-tile-label" data-i18n="legasthenieFreundlich">Dyslexia Friendly</div>
                <div class="complyo-tile-check" hidden>✓</div>
              </div>
              
              <!-- Hide Images -->
              <div class="complyo-feature-tile" data-feature="hideImages">
                <div class="complyo-tile-icon">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <rect x="3" y="3" width="18" height="18" rx="2"/>
                    <circle cx="8.5" cy="8.5" r="1.5"/>
                    <path d="M21 15l-5-5L5 21"/>
                    <line x1="3" y1="3" x2="21" y2="21"/>
                  </svg>
                </div>
                <div class="complyo-tile-label">Hide Images</div>
                <div class="complyo-tile-check" hidden>✓</div>
              </div>
              
              <!-- Readable Font -->
              <div class="complyo-feature-tile" data-feature="readableFont">
                <div class="complyo-tile-icon">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M4 7V4h16v3M9 20h6M12 4v16"/>
                  </svg>
                </div>
                <div class="complyo-tile-label">Readable Font</div>
                <div class="complyo-tile-check" hidden>✓</div>
              </div>
              
              <!-- Big Cursor -->
              <div class="complyo-feature-tile" data-feature="bigCursor">
                <div class="complyo-tile-icon">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M3 3l7.07 16.97 2.51-7.39 7.39-2.51L3 3z"/>
                  </svg>
                </div>
                <div class="complyo-tile-label">Big Cursor</div>
                <div class="complyo-tile-check" hidden>✓</div>
              </div>
              
              <!-- Reading Guide -->
              <div class="complyo-feature-tile" data-feature="readingGuide">
                <div class="complyo-tile-icon">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <line x1="3" y1="12" x2="21" y2="12"/>
                    <polyline points="8 6 2 12 8 18"/>
                    <polyline points="16 6 22 12 16 18"/>
                  </svg>
                </div>
                <div class="complyo-tile-label">Reading Guide</div>
                <div class="complyo-tile-check" hidden>✓</div>
              </div>
              
              <!-- Page Structure -->
              <div class="complyo-feature-tile" data-feature="pageStructure">
                <div class="complyo-tile-icon">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M3 3h7v7H3zM14 3h7v7h-7zM14 14h7v7h-7zM3 14h7v7H3z"/>
                  </svg>
                </div>
                <div class="complyo-tile-label">Page Structure</div>
                <div class="complyo-tile-check" hidden>✓</div>
              </div>
              
              <!-- Tooltips -->
              <div class="complyo-feature-tile" data-feature="showTooltips">
                <div class="complyo-tile-icon">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                    <line x1="9" y1="10" x2="15" y2="10"/>
                  </svg>
                </div>
                <div class="complyo-tile-label">Tooltips</div>
                <div class="complyo-tile-check" hidden>✓</div>
              </div>
              
              <!-- Stop Animations -->
              <div class="complyo-feature-tile" data-feature="stopAnimations">
                <div class="complyo-tile-icon">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"/>
                    <path d="M10 15l5-5"/>
                    <path d="M10 9l5 5"/>
                  </svg>
                </div>
                <div class="complyo-tile-label">Stop Animations</div>
                <div class="complyo-tile-check" hidden>✓</div>
              </div>
              
              <!-- Invert Colors -->
              <div class="complyo-feature-tile" data-feature="invertColors">
                <div class="complyo-tile-icon">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"/>
                    <path d="M12 2v20" stroke="none" fill="currentColor"/>
                  </svg>
                </div>
                <div class="complyo-tile-label">Invert Colors</div>
                <div class="complyo-tile-check" hidden>✓</div>
              </div>
              
              <!-- Night Mode -->
              <div class="complyo-feature-tile" data-feature="nightMode">
                <div class="complyo-tile-icon">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
                  </svg>
                </div>
                <div class="complyo-tile-label">Night Mode</div>
                <div class="complyo-tile-check" hidden>✓</div>
              </div>
              
              <!-- Grayscale -->
              <div class="complyo-feature-tile" data-feature="grayscale">
                <div class="complyo-tile-icon">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"/>
                    <path d="M2 12h20"/>
                  </svg>
                </div>
                <div class="complyo-tile-label">Grayscale</div>
                <div class="complyo-tile-check" hidden>✓</div>
              </div>
              
              <!-- Bionic Reading -->
              <div class="complyo-feature-tile" data-feature="bionicReading">
                <div class="complyo-tile-icon">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
                    <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
                    <text x="12" y="13" text-anchor="middle" fill="currentColor" font-size="6" font-weight="bold">B</text>
                  </svg>
                </div>
                <div class="complyo-tile-label">Bionic Reading</div>
                <div class="complyo-tile-check" hidden>✓</div>
              </div>
              
              <!-- Text to Speech -->
              <div class="complyo-feature-tile" data-feature="textToSpeech">
                <div class="complyo-tile-icon">
                  <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
                    <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"/>
                  </svg>
                </div>
                <div class="complyo-tile-label">Text to Speech</div>
                <div class="complyo-tile-check" hidden>✓</div>
              </div>
              
            </div>
          </div>
          
          <div class="complyo-panel-footer">
            <button class="complyo-btn-reset" id="complyo-reset-all" data-i18n="resetAllSettings">
              Reset All Settings
            </button>
            <div class="complyo-footer-info">
              <span class="complyo-version">Complyo Widget v${WIDGET_VERSION}</span>
            </div>
          </div>
        </div>
        
        <!-- Reading Guide Overlay -->
        <div class="complyo-reading-guide" id="complyo-reading-guide-overlay" hidden></div>
        
        <!-- Page Structure Overlay mit Tabs -->
        <div class="complyo-page-structure-overlay" id="complyo-page-structure-overlay" hidden>
          <div class="complyo-structure-header">
            <h3 data-i18n="pageStructure">Page Structure</h3>
            <button class="complyo-structure-close" aria-label="Schließen">✕</button>
          </div>

          <!-- Tabs für Page Structure -->
          <div class="complyo-structure-tabs">
            <button class="complyo-tab-btn active" data-tab="headings" data-i18n="tabHeadings">Headings</button>
            <button class="complyo-tab-btn" data-tab="landmarks" data-i18n="tabLandmarks">Landmarks</button>
            <button class="complyo-tab-btn" data-tab="links" data-i18n="tabLinks">Links</button>
          </div>
          
          <div class="complyo-structure-content" id="complyo-structure-content">
            <div class="complyo-tab-panel active" data-panel="headings"></div>
            <div class="complyo-tab-panel" data-panel="landmarks"></div>
            <div class="complyo-tab-panel" data-panel="links"></div>
          </div>
        </div>
        
        <!-- Backdrop für das Text-Modal (klick schließt) -->
        <div class="complyo-modal-backdrop" id="complyo-modal-backdrop" hidden></div>

        <!-- Text Settings Modal mit Schiebereglern -->
        <div class="complyo-settings-modal" id="complyo-text-settings-modal" role="dialog" aria-modal="true" hidden>
          <div class="complyo-modal-header">
            <h3 data-i18n="textSettings">Text Settings</h3>
            <button class="complyo-modal-close" data-modal="text-settings" aria-label="Schließen">✕</button>
          </div>
          
          <div class="complyo-modal-content">
            <!-- Font Size Slider -->
            <div class="complyo-slider-group">
              <label>
                <span data-i18n="fontSize">Font Size</span>
                <span class="complyo-slider-value" id="fontSize-value">100%</span>
              </label>
              <input type="range" class="complyo-slider" id="fontSize-slider" 
                     min="80" max="200" step="10" value="100" data-feature="fontSize">
              <div class="complyo-slider-labels">
                <span>80%</span>
                <span>200%</span>
              </div>
            </div>
            
            <!-- Line Height Slider -->
            <div class="complyo-slider-group">
              <label>
                <span data-i18n="lineHeight">Line Height</span>
                <span class="complyo-slider-value" id="lineHeight-value">150%</span>
              </label>
              <input type="range" class="complyo-slider" id="lineHeight-slider" 
                     min="100" max="250" step="10" value="150" data-feature="lineHeight">
              <div class="complyo-slider-labels">
                <span>100%</span>
                <span>250%</span>
              </div>
            </div>
            
            <!-- Letter Spacing Slider -->
            <div class="complyo-slider-group">
              <label>
                <span data-i18n="letterSpacing">Letter Spacing</span>
                <span class="complyo-slider-value" id="letterSpacing-value">0px</span>
              </label>
              <input type="range" class="complyo-slider" id="letterSpacing-slider" 
                     min="0" max="10" step="1" value="0" data-feature="letterSpacing">
              <div class="complyo-slider-labels">
                <span>0px</span>
                <span>10px</span>
              </div>
            </div>
            
            <!-- Word Spacing Slider -->
            <div class="complyo-slider-group">
              <label>
                <span data-i18n="wordSpacing">Word Spacing</span>
                <span class="complyo-slider-value" id="wordSpacing-value">0px</span>
              </label>
              <input type="range" class="complyo-slider" id="wordSpacing-slider" 
                     min="0" max="10" step="1" value="0" data-feature="wordSpacing">
              <div class="complyo-slider-labels">
                <span>0px</span>
                <span>10px</span>
              </div>
            </div>
            
            <!-- Text Align Buttons -->
            <div class="complyo-slider-group">
              <label data-i18n="textAlign">Text Alignment</label>
              <div class="complyo-button-group">
                <button class="complyo-align-btn active" data-align="default" data-i18n="alignDefault">Default</button>
                <button class="complyo-align-btn" data-align="left" data-i18n="alignLeft">Left</button>
                <button class="complyo-align-btn" data-align="center" data-i18n="alignCenter">Center</button>
                <button class="complyo-align-btn" data-align="right" data-i18n="alignRight">Right</button>
              </div>
            </div>

            <!-- Reset Button -->
            <button class="complyo-reset-btn" id="reset-text-settings" data-i18n="resetTextSettings">
              Reset Text Settings
            </button>
          </div>
        </div>
      `;
      
      // Widget an <html> anhängen statt <body>, damit body.style.filter das Widget nicht beeinflusst
      // (CSS filter auf parent erstellt neuen containing block für position:fixed)
      document.documentElement.appendChild(container);
      this.container = container;
      
      this.setupEventListeners();
    }
    
    setupEventListeners() {
      const panel = this.container.querySelector('.complyo-panel');
      const toggleBtn = this.container.querySelector('.complyo-toggle-btn');
      const closeBtn = this.container.querySelector('.complyo-close-btn');
      
      // Toggle Widget
      toggleBtn.addEventListener('click', () => this.togglePanel());
      closeBtn.addEventListener('click', () => this.closePanel());
      
      // Feature Tiles
      this.container.querySelectorAll('.complyo-feature-tile').forEach(tile => {
        tile.addEventListener('click', () => {
          const feature = tile.dataset.feature;
          this.toggleFeature(feature);
        });
      });
      
      // Reset Button
      this.container.querySelector('#complyo-reset-all').addEventListener('click', () => this.resetAll());

      // Page Structure Close
      const structureClose = this.container.querySelector('.complyo-structure-close');
      if (structureClose) {
        structureClose.addEventListener('click', () => {
          this.features.pageStructure = false;
          this.applyFeature('pageStructure');
          this.updateTileState('pageStructure');
        });
      }
      
      // Page Structure Tabs
      this.container.querySelectorAll('.complyo-tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
          const tab = btn.dataset.tab;
          this.switchTab(tab);
        });
      });
      
      // Text Settings Modal Close
      this.container.querySelectorAll('.complyo-modal-close').forEach(btn => {
        btn.addEventListener('click', () => {
          this.closeModal(btn.dataset.modal);
        });
      });

      // Backdrop-Klick schließt das Text-Modal
      const modalBackdrop = this.container.querySelector('#complyo-modal-backdrop');
      if (modalBackdrop) {
        modalBackdrop.addEventListener('click', () => this.closeModal('text-settings'));
      }
      
      // Slider Event Listeners (Live Preview)
      this.container.querySelectorAll('.complyo-slider').forEach(slider => {
        slider.addEventListener('input', (e) => {
          const feature = e.target.dataset.feature;
          const value = parseInt(e.target.value);
          this.updateSliderValue(feature, value);
          this.features[feature] = value;
          this.applyFeature(feature);
        });
        
        slider.addEventListener('change', () => {
          this.savePreferences();
        });
      });
      
      // Text Align Buttons
      this.container.querySelectorAll('.complyo-align-btn').forEach(btn => {
        btn.addEventListener('click', () => {
          const align = btn.dataset.align;
          this.setTextAlign(align);
        });
      });
      
      // Reset Text Settings
      const resetTextBtn = this.container.querySelector('#reset-text-settings');
      if (resetTextBtn) {
        resetTextBtn.addEventListener('click', () => this.resetTextSettings());
      }
      
      // Make widget draggable
      this.makeDraggable();
      
      // Language Switcher
      this.container.querySelectorAll('.complyo-lang-btn').forEach(btn => {
        btn.addEventListener('click', () => {
          const lang = btn.dataset.lang;
          this.changeLanguage(lang);
        });
      });
      
      // Apply translations
      this.applyTranslations();
    }
    
    applyTranslations() {
      // Translate all elements with data-i18n attribute
      this.container.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        el.textContent = this.t(key);
      });
      
      // Auto-translate all feature tiles based on their data-feature attribute
      this.container.querySelectorAll('.complyo-feature-tile').forEach(tile => {
        const feature = tile.dataset.feature;
        const label = tile.querySelector('.complyo-tile-label');
        if (label && feature && !label.hasAttribute('data-i18n')) {
          // Try to find translation for this feature
          const translationKey = this.getTranslationKeyForFeature(feature);
          if (translationKey) {
            label.textContent = this.t(translationKey);
          }
        }
      });
      
      // Update aria-labels
      const toggleBtn = this.container.querySelector('.complyo-toggle-btn');
      if (toggleBtn) {
        toggleBtn.setAttribute('aria-label', this.t('title'));
        toggleBtn.setAttribute('title', this.t('title'));
      }
      
      const closeBtn = this.container.querySelector('.complyo-close-btn');
      if (closeBtn) {
        closeBtn.setAttribute('aria-label', this.t('close'));
        closeBtn.setAttribute('title', this.t('close'));
      }
      
      // Update language button states
      this.container.querySelectorAll('.complyo-lang-btn').forEach(btn => {
        if (btn.dataset.lang === this.config.language) {
          btn.classList.add('active');
        } else {
          btn.classList.remove('active');
        }
      });
    }
    
    getTranslationKeyForFeature(feature) {
      // Map feature names to translation keys
      const mapping = {
        'contrast': 'smartContrast',
        'highlightLinks': 'highlightLinks',
        'readableFont': 'readableFont',
        'dyslexiaFont': 'legasthenieFreundlich',
        'bigCursor': 'bigCursor',
        'hideImages': 'hideImages',
        'stopAnimations': 'stopAnimations',
        'invertColors': 'invertColors',
        'nightMode': 'nightMode',
        'grayscale': 'grayscale',
        'readingGuide': 'readingGuide',
        'pageStructure': 'pageStructure',
        'textToSpeech': 'vorlesen',
        'showTooltips': 'showTooltips',
        'bionicReading': 'bionicReading',
        'fontSize': 'groserText',
        'letterSpacing': 'textabstand',
        'lineHeight': 'zeilenhohe',
        'textAlign': 'textausrichtung'
      };
      return mapping[feature] || feature;
    }
    
    toggleFeature(feature) {
      // Adjustable features öffnen Dialog/Slider
      if (['fontSize', 'letterSpacing', 'lineHeight', 'textAlign'].includes(feature)) {
        this.showAdjustmentDialog(feature);
        return;
      }
      
      // Toggle features
      this.features[feature] = !this.features[feature];
      this.applyFeature(feature);
      this.updateTileState(feature);
      this.savePreferences();
      this.trackAnalytics(feature, this.features[feature]);
    }
    
    showAdjustmentDialog(feature) {
      // Öffnet Text Settings Modal mit Schiebereglern
      this.openModal('text-settings');
      this.syncSlidersWithFeatures();
    }
    
    openModal(modalName) {
      const modal = document.getElementById(`complyo-${modalName}-modal`);
      const backdrop = document.getElementById('complyo-modal-backdrop');
      if (modal) {
        modal.hidden = false;
        if (backdrop) backdrop.hidden = false;
      }
    }

    closeModal(modalName) {
      const modal = document.getElementById(`complyo-${modalName}-modal`);
      const backdrop = document.getElementById('complyo-modal-backdrop');
      if (modal) {
        modal.hidden = true;
        if (backdrop) backdrop.hidden = true;
      }
    }
    
    syncSlidersWithFeatures() {
      // Sync aktuelle Feature-Werte mit Schiebereglern
      const sliders = {
        'fontSize': this.features.fontSize,
        'lineHeight': this.features.lineHeight,
        'letterSpacing': this.features.letterSpacing,
        'wordSpacing': this.features.wordSpacing
      };
      
      Object.entries(sliders).forEach(([feature, value]) => {
        const slider = this.container.querySelector(`#${feature}-slider`);
        if (slider) {
          slider.value = value;
          this.updateSliderValue(feature, value);
        }
      });
      
      // Sync Text Align Buttons
      const currentAlign = this.features.textAlign || 'default';
      this.container.querySelectorAll('.complyo-align-btn').forEach(btn => {
        if (btn.dataset.align === currentAlign) {
          btn.classList.add('active');
        } else {
          btn.classList.remove('active');
        }
      });
    }
    
    updateSliderValue(feature, value) {
      const valueDisplay = this.container.querySelector(`#${feature}-value`);
      if (valueDisplay) {
        const unit = (feature === 'fontSize' || feature === 'lineHeight') ? '%' : 'px';
        valueDisplay.textContent = `${value}${unit}`;
      }
    }
    
    setTextAlign(align) {
      this.features.textAlign = align;
      this.applyFeature('textAlign');
      this.updateTileState('textAlign');
      this.savePreferences();
      
      // Update Button States
      this.container.querySelectorAll('.complyo-align-btn').forEach(btn => {
        if (btn.dataset.align === align) {
          btn.classList.add('active');
        } else {
          btn.classList.remove('active');
        }
      });
    }
    
    resetTextSettings() {
      // Reset alle Text-Einstellungen auf Default
      this.features.fontSize = 100;
      this.features.lineHeight = 150;
      this.features.letterSpacing = 0;
      this.features.wordSpacing = 0;
      this.features.textAlign = 'default';
      
      // Apply reset
      this.applyFeature('fontSize');
      this.applyFeature('lineHeight');
      this.applyFeature('letterSpacing');
      this.applyFeature('wordSpacing');
      this.applyFeature('textAlign');
      
      // Sync UI
      this.syncSlidersWithFeatures();
      this.savePreferences();
      
      // Update Tiles
      this.updateTileState('fontSize');
      this.updateTileState('lineHeight');
      this.updateTileState('letterSpacing');
      this.updateTileState('textAlign');
    }
    
    updateTileState(feature) {
      const tile = this.container.querySelector(`[data-feature="${feature}"]`);
      if (!tile) return;
      
      const check = tile.querySelector('.complyo-tile-check');
      const isActive = this.features[feature] && this.features[feature] !== 100 && this.features[feature] !== 150 && this.features[feature] !== 0 && this.features[feature] !== 'default';
      
      if (isActive || this.features[feature] === true) {
        tile.classList.add('active');
        if (check) check.hidden = false;
      } else {
        tile.classList.remove('active');
        if (check) check.hidden = true;
      }
    }
    
    updateAllTiles() {
      Object.keys(this.features).forEach(feature => {
        this.updateTileState(feature);
      });
    }
    
    applyFeature(feature) {
      const body = document.body;
      const html = document.documentElement;
      
      // Aktuelle Scroll-Position merken
      const scrollY = window.scrollY;
      const scrollX = window.scrollX;
      
      switch(feature) {
        case 'fontSize':
          html.style.setProperty('--complyo-font-scale', this.features.fontSize / 100);
          body.style.fontSize = `${this.features.fontSize}%`;
          if (this.features.fontSize !== 100) {
            body.classList.add('complyo-scaled-text');
          } else {
            body.classList.remove('complyo-scaled-text');
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
        case 'invertColors':
        case 'grayscale':
          this.applyColorFilters();
          // Sicherstellen, dass Widget sichtbar bleibt nach kurzer Verzögerung
          requestAnimationFrame(() => {
            this.applyColorFilters(); // Nochmal aufrufen für Sicherheit
          });
          break;
          
        case 'nightMode':
          body.classList.toggle('complyo-night-mode', this.features.nightMode);
          // Night Mode nutzt auch Filter, also Widget-Sichtbarkeit garantieren
          if (this.features.nightMode) {
            requestAnimationFrame(() => {
              this.ensureWidgetVisibility(['invert(1)', 'hue-rotate(180deg)']);
            });
          } else {
            requestAnimationFrame(() => {
              // Widget-Filter basierend auf anderen aktiven Filter-Features
              const filters = [];
              if (this.features.invertColors) filters.push('invert(1)');
              this.ensureWidgetVisibility(filters);
            });
          }
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
          break;
          
        case 'stopAnimations':
          body.classList.toggle('complyo-stop-animations', this.features.stopAnimations);
          break;
          
        case 'bigCursor':
          body.classList.toggle('complyo-big-cursor', this.features.bigCursor);
          break;
          
        case 'readingGuide':
          const guide = document.getElementById('complyo-reading-guide-overlay');
          if (guide) {
            guide.hidden = !this.features.readingGuide;
            if (this.features.readingGuide) {
              this.setupReadingGuide();
            }
          }
          break;
          
        case 'pageStructure':
          const structureOverlay = document.getElementById('complyo-page-structure-overlay');
          if (structureOverlay) {
            structureOverlay.hidden = !this.features.pageStructure;
            if (this.features.pageStructure) {
              this.showPageStructure();
            }
          }
          break;
          
        case 'textToSpeech':
          if (this.features.textToSpeech) {
            this.startSpeech();
          } else {
            this.stopSpeech();
          }
          break;
      }
      
      // Scroll-Position wiederherstellen (verhindert Springen zum Ende der Seite)
      window.scrollTo(scrollX, scrollY);
    }
    
    applyColorFilters() {
      const body = document.body;
      const html = document.documentElement;
      
      // Kontrast-Klasse
      if (this.features.contrast) {
        body.classList.add('complyo-high-contrast');
      } else {
        body.classList.remove('complyo-high-contrast');
      }
      
      // Farben invertieren
      if (this.features.invertColors) {
        body.classList.add('complyo-invert-colors');
      } else {
        body.classList.remove('complyo-invert-colors');
      }
      
      // Graustufen
      if (this.features.grayscale) {
        body.classList.add('complyo-grayscale');
      } else {
        body.classList.remove('complyo-grayscale');
      }
      
      // WICHTIG: Filter NICHT auf body.style setzen!
      // Stattdessen CSS-Klassen nutzen die den Filter auf body > * anwenden
      // Das Widget hängt an <html>, nicht an <body>, also wird es nicht beeinflusst
      body.style.filter = '';
    }
    
    ensureWidgetVisibility(additionalFilters = []) {
      // Widget ist jetzt an <html> angehängt, braucht keine spezielle Behandlung mehr
      const widget = document.getElementById('complyo-a11y-widget');
      if (!widget) return;
      
      // Sicherstellen dass Widget keine Filter vom Body erbt
      widget.style.setProperty('filter', 'none', 'important');
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
        const parent = el.parentNode;
        if (!parent) return;
        
        // Sammle den kompletten Text des Wortes
        let fullText = el.textContent;
        const nextSibling = el.nextSibling;
        if (nextSibling && nextSibling.nodeType === Node.TEXT_NODE) {
          fullText += nextSibling.textContent;
        }
        
        // Ersetze durch normalen Text
        const textNode = document.createTextNode(fullText);
        parent.replaceChild(textNode, el);
        
        // Entferne das zweite Text-Fragment
        if (nextSibling && nextSibling.nodeType === Node.TEXT_NODE) {
          parent.removeChild(nextSibling);
        }
        
        // Normalize parent to merge text nodes
        parent.normalize();
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
    
    switchTab(tabName) {
      // Tab-Buttons aktualisieren
      this.container.querySelectorAll('.complyo-tab-btn').forEach(btn => {
        if (btn.dataset.tab === tabName) {
          btn.classList.add('active');
        } else {
          btn.classList.remove('active');
        }
      });
      
      // Tab-Panels aktualisieren
      this.container.querySelectorAll('.complyo-tab-panel').forEach(panel => {
        if (panel.dataset.panel === tabName) {
          panel.classList.add('active');
        } else {
          panel.classList.remove('active');
        }
      });
      
      // Content für aktuellen Tab laden
      this.loadTabContent(tabName);
    }
    
    loadTabContent(tabName) {
      const panel = this.container.querySelector(`[data-panel="${tabName}"]`);
      if (!panel) return;
      
      switch(tabName) {
        case 'headings':
          panel.innerHTML = this.getHeadingsHTML();
          break;
        case 'landmarks':
          panel.innerHTML = this.getLandmarksHTML();
          break;
        case 'links':
          panel.innerHTML = this.getLinksHTML();
          break;
      }
    }
    
    getHeadingsHTML() {
      const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
      let html = '<ul class="complyo-structure-list">';
      let count = 0;
      headings.forEach((h) => {
        if (!h.closest('#complyo-a11y-widget') && !h.closest('#complyo-page-structure-overlay')) {
          const level = h.tagName.toLowerCase();
          const text = h.textContent.trim().substring(0, 50);
          const indent = parseInt(level.charAt(1)) - 1;
          html += `<li class="complyo-heading-${level}" style="padding-left: ${indent * 15}px;">
            <span class="complyo-heading-badge">${level.toUpperCase()}</span>
            ${text}
          </li>`;
          count++;
        }
      });
      html += '</ul>';
      if (count === 0) html = '<p class="complyo-empty">No headings found on this page.</p>';
      return html;
    }
    
    getLandmarksHTML() {
      const landmarks = document.querySelectorAll('[role], header, nav, main, footer, aside, form');
      let html = '<ul class="complyo-structure-list">';
      let count = 0;
      landmarks.forEach((el) => {
        if (!el.closest('#complyo-a11y-widget') && !el.closest('#complyo-page-structure-overlay')) {
          const role = el.getAttribute('role') || el.tagName.toLowerCase();
          const label = el.getAttribute('aria-label') || el.getAttribute('aria-labelledby') || 'Unlabeled';
          html += `<li class="complyo-landmark-item">
            <span class="complyo-landmark-badge">${role}</span>
            ${label}
          </li>`;
          count++;
        }
      });
      html += '</ul>';
      if (count === 0) html = '<p class="complyo-empty">No ARIA landmarks found on this page.</p>';
      return html;
    }
    
    getLinksHTML() {
      const links = document.querySelectorAll('a[href]');
      let html = '<ul class="complyo-structure-list complyo-links-list">';
      let count = 0;
      links.forEach((link) => {
        if (!link.closest('#complyo-a11y-widget') && !link.closest('#complyo-page-structure-overlay')) {
          const text = link.textContent.trim().substring(0, 40) || link.href;
          const href = link.href;
          const isExternal = !href.startsWith(window.location.origin);
          html += `<li class="complyo-link-item">
            <a href="${href}" target="_blank" rel="noopener">
              ${isExternal ? '🔗 ' : ''}${text}
            </a>
          </li>`;
          count++;
          if (count >= 50) return; // Limit to 50 links
        }
      });
      html += '</ul>';
      if (count === 0) html = '<p class="complyo-empty">No links found on this page.</p>';
      return html;
    }
    
    showPageStructure() {
      // Initial mit Headings Tab laden
      this.loadTabContent('headings');
    }
    
    startSpeech() {
      console.log('Text-to-Speech aktiviert');
    }
    
    stopSpeech() {
      if (this.speechSynthesis) {
        this.speechSynthesis.cancel();
      }
    }
    
    setupKeyboardShortcuts() {
      document.addEventListener('keydown', (e) => {
        // CTRL+U: Toggle Widget
        if (e.ctrlKey && e.key === 'u') {
          e.preventDefault();
          this.togglePanel();
        }
        
        // ESC: Close Widget
        if (e.key === 'Escape') {
          this.closePanel();
        }
      });
    }
    
    makeDraggable() {
      // Simplified draggable
      console.log('Widget is draggable');
    }

    resetAll() {
      if (!confirm('Alle Barrierefreiheits-Einstellungen zurücksetzen?')) return;
      
      // Reset all features
      Object.keys(this.features).forEach(key => {
        if (typeof this.features[key] === 'boolean') {
          this.features[key] = false;
        } else if (key === 'fontSize') {
          this.features[key] = 100;
        } else if (key === 'lineHeight') {
          this.features[key] = 150;
        } else if (key === 'letterSpacing' || key === 'wordSpacing') {
          this.features[key] = 0;
        } else if (key === 'textAlign') {
          this.features[key] = 'default';
        }
      });
      
      // Remove all styles
      document.body.className = document.body.className.split(' ').filter(c => !c.startsWith('complyo-')).join(' ');
      document.body.style.fontSize = '';
      document.body.style.lineHeight = '';
      document.body.style.letterSpacing = '';
      document.body.style.wordSpacing = '';
      document.body.style.filter = '';
      document.documentElement.style.removeProperty('--complyo-font-scale');
      
      // Remove Bionic Reading markup
      this.removeBionicReading();
      
      // Stop speech if running
      this.stopSpeech();
      
      this.applyAllFeatures();
      this.updateAllTiles();
      this.savePreferences();
      this.trackAnalytics('reset_all', true);
    }
    
    applyAllFeatures() {
      Object.keys(this.features).forEach(feature => {
        this.applyFeature(feature);
      });
      this.updateAllTiles();
    }
    
    togglePanel() {
      this.isOpen = !this.isOpen;
      const panel = this.container.querySelector('.complyo-panel');
      const toggleBtn = this.container.querySelector('.complyo-toggle-btn');
      
      if (panel) {
        panel.hidden = !this.isOpen;
      }
      if (toggleBtn) {
        toggleBtn.setAttribute('aria-expanded', this.isOpen);
        toggleBtn.style.display = this.isOpen ? 'none' : 'flex';
      }
      
      if (this.isOpen) {
        this.trackAnalytics('widget_open', true);
      }
    }
    
    closePanel() {
      this.isOpen = false;
      const panel = this.container.querySelector('.complyo-panel');
      const toggleBtn = this.container.querySelector('.complyo-toggle-btn');

      if (panel) {
        panel.hidden = true;
      }
      if (toggleBtn) {
        toggleBtn.setAttribute('aria-expanded', 'false');
        toggleBtn.style.display = 'flex';
      }
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
        const response = await fetch(`${API_BASE}/api/accessibility/alt-text-fixes?site_id=${this.config.siteId}&approved_only=true`);
        if (!response.ok) return;
        const data = await response.json();
        if (data.success && data.fixes && data.fixes.length > 0) {
          let applied = 0;
          data.fixes.forEach(fix => {
            const img = document.querySelector(`img[src="${fix.image_url}"]`) || 
                        document.querySelector(`img[src*="${fix.image_url.split('/').pop()}"]`);
            if (img && !img.alt) {
              img.alt = fix.alt_text;
              img.setAttribute('data-complyo-alt', 'true');
              applied++;
            }
          });
          if (applied > 0) {
            console.log(`✅ Complyo: ${applied} Alt-Texte angewendet`);
          }
        }
      } catch (e) {
        console.warn('Alt-Text-Fixes konnten nicht geladen werden:', e);
      }
    }
    
    trackAnalytics(feature, value) {
      try {
        fetch(`${API_BASE}/api/widgets/analytics`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            site_id: this.config.siteId,
            session_id: this.sessionId,
            feature,
            value,
            timestamp: Date.now()
          })
        }).catch(() => {});
      } catch (e) {}
    }
    
    injectCSS() {
      const style = document.createElement('style');
      style.id = 'complyo-a11y-styles';
      style.textContent = `
        /* ===== COMPLYO WIDGET v6.0 - MODERN GRID LAYOUT ===== */
        
        #complyo-a11y-widget {
          position: fixed;
          z-index: 999999;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
          /* ===== Clean / neutral palette ===== */
          --c-accent: #2563eb;
          --c-accent-hover: #1d4ed8;
          --c-accent-tint: #eff6ff;
          --c-accent-border: #bfdbfe;
          --c-surface: #ffffff;
          --c-surface-2: #f9fafb;
          --c-border: #e5e7eb;
          --c-border-hover: #d1d5db;
          --c-text: #111827;
          --c-text-mid: #374151;
          --c-text-muted: #6b7280;
          --c-radius: 14px;
          --c-radius-sm: 10px;
          --c-shadow: 0 8px 28px rgba(17, 24, 39, 0.12);
        }
        
        .complyo-widget-bottom-right {
          bottom: 20px;
          right: 20px;
        }

        /* ===== TOGGLE BUTTON ===== */
        /* Maße/Form/Position passend zum Cookie-Settings-Button (links): 48x48, radius 12px, 20px Abstand */
        .complyo-toggle-btn {
          width: 48px;
          height: 48px;
          border-radius: 12px;
          background: var(--c-accent);
          color: white;
          border: none;
          box-shadow: 0 4px 12px rgba(37, 99, 235, 0.28);
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 0;
          transition: background 0.18s ease, transform 0.18s ease, box-shadow 0.18s ease;
        }

        .complyo-toggle-btn:hover {
          background: var(--c-accent-hover);
          transform: translateY(-2px);
          box-shadow: 0 6px 16px rgba(37, 99, 235, 0.32);
        }

        .complyo-toggle-btn:focus-visible {
          outline: 3px solid var(--c-accent-border);
          outline-offset: 2px;
        }
        
        /* ===== PANEL ===== */
        .complyo-panel {
          position: fixed !important;
          bottom: 20px !important;
          right: 20px !important;
          width: 460px;
          max-width: calc(100vw - 32px);
          max-height: calc(100vh - 40px);
          background: var(--c-surface);
          border: 1px solid var(--c-border);
          border-radius: var(--c-radius);
          box-shadow: var(--c-shadow);
          overflow: hidden;
          display: flex;
          flex-direction: column;
          transform-origin: bottom right;
          animation: scaleIn 0.2s ease-out;
          z-index: 2147483647 !important;
          font-size: 16px !important;
        }
        
        @keyframes scaleIn {
          from {
            opacity: 0;
            transform: scale(0.95) translateY(10px);
          }
          to {
            opacity: 1;
            transform: scale(1) translateY(0);
          }
        }
        
        .complyo-panel-header {
          background: var(--c-surface);
          color: var(--c-text);
          padding: 18px 20px;
          display: flex;
          justify-content: space-between;
          align-items: center;
          border-bottom: 1px solid var(--c-border);
        }

        .complyo-panel-header h3 {
          margin: 0;
          font-size: 16px;
          font-weight: 600;
          letter-spacing: 0;
          color: var(--c-text);
        }

        .complyo-close-btn {
          background: transparent;
          border: none;
          color: var(--c-text-muted);
          width: 32px;
          height: 32px;
          border-radius: 8px;
          cursor: pointer;
          font-size: 18px;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: background 0.18s, color 0.18s;
        }

        .complyo-close-btn:hover {
          background: var(--c-surface-2);
          color: var(--c-text);
        }
        
        /* ===== LANGUAGE SWITCHER ===== */
        .complyo-language-selector {
          display: flex;
          gap: 8px;
          padding: 12px 20px;
          background: var(--c-surface-2);
          border-bottom: 1px solid var(--c-border);
        }

        .complyo-lang-btn {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 7px 14px;
          background: var(--c-surface);
          border: 1px solid var(--c-border);
          border-radius: 8px;
          cursor: pointer;
          font-size: 14px;
          font-weight: 500;
          color: var(--c-text-mid);
          transition: border-color 0.18s, color 0.18s, background 0.18s;
        }

        .complyo-lang-btn:hover {
          border-color: var(--c-border-hover);
          color: var(--c-text);
        }

        .complyo-lang-btn.active {
          background: var(--c-accent-tint);
          border-color: var(--c-accent);
          color: var(--c-accent);
        }
        
        .complyo-lang-flag {
          font-size: 18px;
        }
        
        .complyo-panel-content {
          overflow-y: auto;
          padding: 20px;
          max-height: calc(85vh - 140px);
        }

        /* ===== FEATURE GRID ===== */
        .complyo-feature-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 10px;
        }

        /* ===== FEATURE TILE ===== */
        .complyo-feature-tile {
          position: relative;
          background: var(--c-surface);
          border: 1px solid var(--c-border);
          border-radius: var(--c-radius-sm);
          padding: 16px 10px;
          cursor: pointer;
          transition: border-color 0.18s, background 0.18s, box-shadow 0.18s;
          display: flex;
          flex-direction: column;
          align-items: center;
          text-align: center;
          min-height: 96px;
        }

        .complyo-feature-tile:hover {
          background: var(--c-surface-2);
          border-color: var(--c-border-hover);
          box-shadow: 0 2px 8px rgba(17, 24, 39, 0.06);
        }

        .complyo-feature-tile:focus-visible {
          outline: 3px solid var(--c-accent-border);
          outline-offset: 2px;
        }

        .complyo-feature-tile.active {
          background: var(--c-accent-tint);
          border-color: var(--c-accent);
        }

        .complyo-tile-icon {
          color: var(--c-text-muted);
          margin-bottom: 8px;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .complyo-feature-tile.active .complyo-tile-icon {
          color: var(--c-accent);
        }

        .complyo-tile-label {
          font-size: 12px;
          font-weight: 500;
          color: var(--c-text-mid);
          line-height: 1.3;
        }

        .complyo-feature-tile.active .complyo-tile-label {
          color: var(--c-accent);
          font-weight: 600;
        }

        .complyo-tile-check {
          position: absolute;
          top: 8px;
          right: 8px;
          width: 18px;
          height: 18px;
          background: var(--c-accent);
          color: white;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 11px;
          font-weight: bold;
        }
        
        /* ===== FOOTER ===== */
        .complyo-panel-footer {
          padding: 14px 20px;
          border-top: 1px solid var(--c-border);
          background: var(--c-surface-2);
          display: flex;
          flex-direction: column;
          gap: 10px;
        }

        .complyo-btn-reset {
          width: 100%;
          padding: 11px 20px;
          border-radius: var(--c-radius-sm);
          background: var(--c-surface);
          color: var(--c-text-mid);
          border: 1px solid var(--c-border);
          font-size: 13px;
          font-weight: 600;
          cursor: pointer;
          transition: background 0.18s, border-color 0.18s, color 0.18s;
        }

        .complyo-btn-reset:hover {
          background: #fef2f2;
          border-color: #fecaca;
          color: #b91c1c;
        }

        .complyo-footer-info {
          display: flex;
          justify-content: flex-end;
          align-items: center;
        }

        .complyo-version {
          font-size: 11px;
          color: var(--c-text-muted);
        }
        
        /* ===== OVERLAYS ===== */
        [hidden] {
          display: none !important;
        }
        
        .complyo-reading-guide {
          position: fixed;
          left: 0;
          right: 0;
          height: 3px;
          background: rgba(37, 99, 235, 0.4);
          pointer-events: none;
          z-index: 999998;
          box-shadow: 0 0 20px rgba(37, 99, 235, 0.28);
        }
        
        .complyo-page-structure-overlay {
          position: fixed;
          top: 20px;
          right: 496px;
          width: 320px;
          max-width: calc(100vw - 32px);
          max-height: 80vh;
          background: var(--c-surface);
          border: 1px solid var(--c-border);
          border-radius: var(--c-radius);
          box-shadow: var(--c-shadow);
          overflow: hidden;
          z-index: 999998;
        }
        
        .complyo-structure-header {
          background: var(--c-surface);
          color: var(--c-text);
          padding: 16px;
          display: flex;
          justify-content: space-between;
          align-items: center;
          border-bottom: 1px solid var(--c-border);
        }

        .complyo-structure-header h3 {
          margin: 0;
          font-size: 14px;
          color: var(--c-text);
        }

        .complyo-structure-close {
          background: transparent;
          border: none;
          color: var(--c-text-muted);
          width: 28px;
          height: 28px;
          border-radius: 8px;
          cursor: pointer;
          transition: background 0.18s, color 0.18s;
        }

        .complyo-structure-close:hover {
          background: var(--c-surface-2);
          color: var(--c-text);
        }
        
        .complyo-structure-content {
          padding: 0;
          overflow-y: auto;
          max-height: calc(80vh - 120px);
        }
        
        /* Tabs für Page Structure */
        .complyo-structure-tabs {
          display: flex;
          background: var(--c-surface-2);
          border-bottom: 2px solid var(--c-border);
          padding: 0 12px;
        }
        
        .complyo-tab-btn {
          flex: 1;
          padding: 12px 16px;
          border: none;
          background: transparent;
          color: var(--c-text-muted);
          font-size: 13px;
          font-weight: 500;
          cursor: pointer;
          border-bottom: 3px solid transparent;
          transition: all 0.2s;
          position: relative;
          top: 2px;
        }
        
        .complyo-tab-btn:hover {
          color: var(--c-accent);
          background: rgba(37, 99, 235, 0.06);
        }
        
        .complyo-tab-btn.active {
          color: var(--c-accent);
          border-bottom-color: var(--c-accent);
          background: white;
        }
        
        /* Tab Panels */
        .complyo-tab-panel {
          display: none;
          padding: 16px;
          animation: fadeIn 0.2s ease-in;
        }
        
        .complyo-tab-panel.active {
          display: block;
        }
        
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(-5px); }
          to { opacity: 1; transform: translateY(0); }
        }
        
        /* Structure Lists */
        .complyo-structure-list {
          list-style: none;
          padding: 0;
          margin: 0;
        }
        
        .complyo-structure-list li {
          padding: 10px 12px;
          margin: 6px 0;
          border-radius: 6px;
          background: var(--c-surface-2);
          font-size: 13px;
          line-height: 1.5;
          border-left: 3px solid transparent;
          transition: all 0.2s;
        }
        
        .complyo-structure-list li:hover {
          background: var(--c-border);
          border-left-color: var(--c-accent);
        }
        
        /* Heading Badges */
        .complyo-heading-badge {
          display: inline-block;
          padding: 2px 6px;
          background: var(--c-accent);
          color: white;
          border-radius: 4px;
          font-size: 10px;
          font-weight: 600;
          margin-right: 8px;
        }
        
        .complyo-heading-h1 .complyo-heading-badge { background: #e63946; }
        .complyo-heading-h2 .complyo-heading-badge { background: #f77f00; }
        .complyo-heading-h3 .complyo-heading-badge { background: #06a77d; }
        .complyo-heading-h4 .complyo-heading-badge { background: var(--c-accent); }
        .complyo-heading-h5 .complyo-heading-badge { background: #7209b7; }
        .complyo-heading-h6 .complyo-heading-badge { background: var(--c-text-muted); }
        
        /* Landmark Badges */
        .complyo-landmark-badge {
          display: inline-block;
          padding: 2px 8px;
          background: #06a77d;
          color: white;
          border-radius: 4px;
          font-size: 10px;
          font-weight: 600;
          margin-right: 8px;
          text-transform: uppercase;
        }
        
        /* Links List */
        .complyo-links-list a {
          color: var(--c-accent);
          text-decoration: none;
          display: block;
          font-size: 13px;
        }
        
        .complyo-links-list a:hover {
          text-decoration: underline;
        }
        
        .complyo-empty {
          text-align: center;
          color: var(--c-text-muted);
          padding: 24px;
          font-style: italic;
        }
        
        /* ===== TEXT SETTINGS MODAL ===== */
        .complyo-modal-backdrop {
          position: fixed;
          inset: 0;
          background: rgba(17, 24, 39, 0.45);
          /* Gleiche z-Ebene wie Panel/Modal; DOM-Reihenfolge (Panel → Backdrop → Modal)
             legt den Backdrop über das Panel und das Modal über den Backdrop. */
          z-index: 2147483647 !important;
          animation: fadeIn 0.2s ease-out;
        }

        .complyo-settings-modal {
          position: fixed;
          top: 50%;
          left: 50%;
          transform: translate(-50%, -50%);
          width: 480px;
          max-width: calc(100vw - 32px);
          max-height: 85vh;
          background: var(--c-surface);
          border: 1px solid var(--c-border);
          border-radius: var(--c-radius);
          box-shadow: var(--c-shadow);
          display: flex;
          flex-direction: column;
          overflow: hidden;
          z-index: 2147483647 !important;
          animation: modalIn 0.2s ease-out;
        }

        @keyframes modalIn {
          from { opacity: 0; transform: translate(-50%, -50%) scale(0.97); }
          to   { opacity: 1; transform: translate(-50%, -50%) scale(1); }
        }
        
        .complyo-modal-header {
          background: var(--c-surface);
          color: var(--c-text);
          padding: 18px 20px;
          display: flex;
          justify-content: space-between;
          align-items: center;
          border-bottom: 1px solid var(--c-border);
        }

        .complyo-modal-header h3 {
          margin: 0;
          font-size: 16px;
          font-weight: 600;
          color: var(--c-text);
        }

        .complyo-modal-close {
          background: transparent;
          border: none;
          color: var(--c-text-muted);
          width: 32px;
          height: 32px;
          border-radius: 8px;
          cursor: pointer;
          font-size: 18px;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: background 0.18s, color 0.18s;
        }

        .complyo-modal-close:hover {
          background: var(--c-surface-2);
          color: var(--c-text);
        }
        
        .complyo-modal-content {
          padding: 20px;
          overflow-y: auto;
          flex: 1 1 auto;
          min-height: 0;
        }

        /* Slider Groups */
        .complyo-slider-group {
          margin-bottom: 18px;
        }
        
        .complyo-slider-group label {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 12px;
          font-size: 14px;
          font-weight: 500;
          color: var(--c-text);
        }
        
        .complyo-slider-value {
          background: var(--c-border);
          padding: 4px 12px;
          border-radius: 6px;
          font-size: 13px;
          font-weight: 600;
          color: var(--c-accent);
          min-width: 55px;
          text-align: center;
        }
        
        /* Range Slider */
        .complyo-slider {
          width: 100%;
          height: 6px;
          border-radius: 3px;
          background: var(--c-border);
          outline: none;
          -webkit-appearance: none;
          appearance: none;
          cursor: pointer;
        }
        
        .complyo-slider::-webkit-slider-thumb {
          -webkit-appearance: none;
          appearance: none;
          width: 20px;
          height: 20px;
          border-radius: 50%;
          background: var(--c-accent);
          cursor: pointer;
          box-shadow: 0 2px 8px rgba(37, 99, 235, 0.28);
          transition: all 0.2s;
        }
        
        .complyo-slider::-webkit-slider-thumb:hover {
          transform: scale(1.2);
          box-shadow: 0 4px 12px rgba(37, 99, 235, 0.4);
        }
        
        .complyo-slider::-moz-range-thumb {
          width: 20px;
          height: 20px;
          border-radius: 50%;
          background: var(--c-accent);
          cursor: pointer;
          border: none;
          box-shadow: 0 2px 8px rgba(37, 99, 235, 0.28);
          transition: all 0.2s;
        }
        
        .complyo-slider::-moz-range-thumb:hover {
          transform: scale(1.2);
          box-shadow: 0 4px 12px rgba(37, 99, 235, 0.4);
        }
        
        .complyo-slider-labels {
          display: flex;
          justify-content: space-between;
          margin-top: 8px;
          font-size: 11px;
          color: var(--c-text-muted);
        }
        
        /* Button Group */
        .complyo-button-group {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
          margin-top: 8px;
        }

        .complyo-align-btn {
          flex: 1 1 auto;
          min-width: 0;
          padding: 10px 12px;
          border: 1px solid var(--c-border);
          background: var(--c-surface);
          border-radius: 8px;
          font-size: 13px;
          font-weight: 500;
          color: var(--c-text-mid);
          cursor: pointer;
          transition: border-color 0.18s, color 0.18s, background 0.18s;
          white-space: nowrap;
        }
        
        .complyo-align-btn:hover {
          border-color: var(--c-accent);
          color: var(--c-accent);
          background: rgba(37, 99, 235, 0.06);
        }
        
        .complyo-align-btn.active {
          background: var(--c-accent);
          border-color: var(--c-accent);
          color: white;
        }
        
        /* Reset Button */
        .complyo-reset-btn {
          width: 100%;
          padding: 12px 24px;
          margin-top: 20px;
          background: var(--c-surface);
          border: 1px solid var(--c-border);
          border-radius: var(--c-radius-sm);
          font-size: 14px;
          font-weight: 600;
          color: var(--c-text-mid);
          cursor: pointer;
          transition: background 0.18s, border-color 0.18s, color 0.18s;
        }

        .complyo-reset-btn:hover {
          background: var(--c-surface-2);
          border-color: var(--c-border-hover);
          color: var(--c-text);
        }
        
        /* ===== HIGH CONTRAST FIX - MAXIMUM PRIORITY ===== */
        body.complyo-high-contrast #complyo-a11y-widget,
        body.complyo-high-contrast #complyo-a11y-widget *,
        body.complyo-invert-colors #complyo-a11y-widget,
        body.complyo-invert-colors #complyo-a11y-widget *,
        body.complyo-grayscale #complyo-a11y-widget,
        body.complyo-grayscale #complyo-a11y-widget *,
        #complyo-a11y-widget {
          isolation: isolate !important;
        }
        
        body.complyo-high-contrast .complyo-toggle-btn,
        body.complyo-invert-colors .complyo-toggle-btn,
        body.complyo-grayscale .complyo-toggle-btn,
        body.complyo-night-mode .complyo-toggle-btn,
        .complyo-toggle-btn {
          background: var(--c-accent) !important;
          opacity: 1 !important;
          visibility: visible !important;
          pointer-events: auto !important;
          z-index: 999999 !important;
        }
        
        body.complyo-high-contrast .complyo-panel,
        body.complyo-invert-colors .complyo-panel,
        body.complyo-grayscale .complyo-panel,
        body.complyo-night-mode .complyo-panel,
        .complyo-panel {
          background: white !important;
          color: var(--c-text) !important;
          opacity: 1 !important;
          visibility: visible !important;
          pointer-events: auto !important;
        }
        
        /* Widget-Container hat höchste Priorität - IMMER SICHTBAR UND FIXED */
        body.complyo-high-contrast #complyo-a11y-widget,
        body.complyo-invert-colors #complyo-a11y-widget,
        body.complyo-grayscale #complyo-a11y-widget,
        body.complyo-night-mode #complyo-a11y-widget,
        #complyo-a11y-widget {
          position: fixed !important;
          isolation: isolate !important;
          opacity: 1 !important;
          visibility: visible !important;
          z-index: 2147483647 !important;
          pointer-events: auto !important;
          display: block !important;
          bottom: 20px !important;
          right: 20px !important;
          transform: none !important;
          will-change: auto !important;
        }
        
        /* Spezifische Filter-Behandlung */
        body:not(.complyo-invert-colors):not(.complyo-night-mode) #complyo-a11y-widget {
          filter: none !important;
          -webkit-filter: none !important;
        }
        
        /* ===== FEATURE STYLES ===== */
        
        /* Filter-Features via CSS-Klassen (nicht via style.filter) */
        /* Widget hängt an <html>, Body-Filter betreffen es nicht */
        body.complyo-high-contrast {
          filter: contrast(1.5);
        }
        
        body.complyo-invert-colors {
          filter: invert(1);
        }
        
        body.complyo-grayscale {
          filter: grayscale(1);
        }
        
        /* Kombinationen */
        body.complyo-high-contrast.complyo-invert-colors {
          filter: contrast(1.5) invert(1);
        }
        
        body.complyo-high-contrast.complyo-grayscale {
          filter: contrast(1.5) grayscale(1);
        }
        
        body.complyo-invert-colors.complyo-grayscale {
          filter: invert(1) grayscale(1);
        }
        
        body.complyo-high-contrast.complyo-invert-colors.complyo-grayscale {
          filter: contrast(1.5) invert(1) grayscale(1);
        }
        
        body.complyo-scaled-text *:not(#complyo-a11y-widget):not(#complyo-a11y-widget *) {
          font-size: calc(1em * var(--complyo-font-scale, 1)) !important;
        }
        
        /* Widget NIEMALS durch body-Styles beeinflussen */
        #complyo-a11y-widget,
        #complyo-a11y-widget *,
        .complyo-panel,
        .complyo-panel * {
          font-size: revert !important;
          line-height: normal !important;
          letter-spacing: normal !important;
          word-spacing: normal !important;
          text-align: left !important;
        }
        
        #complyo-a11y-widget .complyo-panel {
          font-size: 16px !important;
        }
        
        #complyo-a11y-widget .complyo-tile-label {
          font-size: 11px !important;
        }
        
        #complyo-a11y-widget .complyo-panel-header h3 {
          font-size: 16px !important;
        }
        
        body.complyo-night-mode {
          filter: invert(1) hue-rotate(180deg);
        }
        
        body.complyo-night-mode #complyo-a11y-widget {
          filter: invert(1) hue-rotate(180deg);
        }
        
        body.complyo-highlight-links a {
          background-color: #fff3cd !important;
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
        
        /* Bionic Reading: Erste Worthälfte fett */
        .complyo-bionic {
          font-weight: 700 !important;
        }
        
        body.complyo-hide-images img {
          opacity: 0 !important;
          visibility: hidden !important;
        }
        
        body.complyo-stop-animations * {
          animation: none !important;
          transition: none !important;
        }
        
        body.complyo-big-cursor,
        body.complyo-big-cursor * {
          cursor: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24"><path fill="white" stroke="black" stroke-width="1" d="M3 3l7.07 16.97 2.51-7.39 7.39-2.51L3 3z"/></svg>') 12 12, auto !important;
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

        /* ===== RESPONSIVE / MOBILE ===== */
        @media (max-width: 540px) {
          .complyo-panel {
            width: auto !important;
            left: 16px !important;
            right: 16px !important;
            bottom: 16px !important;
            max-width: none !important;
            max-height: calc(100vh - 32px);
            border-radius: var(--c-radius);
          }

          .complyo-panel-content {
            max-height: calc(100vh - 230px);
          }

          .complyo-feature-grid {
            grid-template-columns: repeat(2, 1fr);
          }

          /* Ausrichtungs-Buttons 2x2 statt abgeschnitten einreihig */
          .complyo-align-btn {
            flex: 1 1 calc(50% - 4px);
          }

          /* Page-Structure-Overlay vollflächig statt neben dem Panel */
          .complyo-page-structure-overlay {
            top: 16px;
            left: 16px;
            right: 16px;
            width: auto;
            max-width: none;
          }
        }

        /* Reduzierte Bewegung respektieren */
        @media (prefers-reduced-motion: reduce) {
          .complyo-panel,
          .complyo-tab-panel,
          .complyo-settings-modal {
            animation: none !important;
          }
          #complyo-a11y-widget * {
            transition: none !important;
          }
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

