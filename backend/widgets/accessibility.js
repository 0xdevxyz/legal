/**
 * Complyo Accessibility Widget v3.0
 * REVOLUTIONÄR: Wechselt zwischen ECHTEN CODE-TEMPLATES
 * KEIN Overlay! ECHTE Code-Lösungen die man einbauen kann!
 * 
 * Das macht Complyo einzigartig: Keine Runtime-Magic,
 * sondern echte Code-Vorlagen die permanent integriert werden können.
 */

(function() {
  'use strict';
  
  const WIDGET_VERSION = '3.0.0';
  const API_BASE = 'https://api.complyo.tech';
  
  class ComplyoAccessibilityWidget {
    constructor(config = {}) {
      this.config = {
        siteId: config.siteId || this.getSiteIdFromScript(),
        autoLoad: config.autoLoad !== false,
        showToolbar: config.showToolbar !== false,
        defaultTemplate: config.defaultTemplate || 'standard',
        ...config
      };
      
      this.templates = null;
      this.activeTemplate = null;
      this.injectedElements = {
        css: null,
        html: [],
        js: null
      };
      
      this.init();
    }
    
    getSiteIdFromScript() {
      const script = document.currentScript || 
                     document.querySelector('script[src*="accessibility.js"]');
      return script ? script.getAttribute('data-site-id') : null;
    }
    
    async init() {
      console.log(`[Complyo v${WIDGET_VERSION}] Initialisiere Code-Template-Widget...`);
      
      try {
        await this.loadTemplates();
        
        if (this.config.showToolbar) {
          this.renderToolbar();
        }
        
        // Auto-load gespeichertes oder Default-Template
        const savedTemplate = localStorage.getItem('complyo_active_template');
        const templateToLoad = savedTemplate || this.config.defaultTemplate;
        
        if (this.config.autoLoad && templateToLoad) {
          await this.applyTemplate(templateToLoad);
        }
        
        console.log('[Complyo] Widget bereit ✓');
      } catch (error) {
        console.error('[Complyo] Fehler beim Laden:', error);
      }
    }
    
    async loadTemplates() {
      try {
        const response = await fetch(`${API_BASE}/api/widgets/accessibility-templates`);
        const data = await response.json();
        
        if (data.success) {
          this.templates = data.templates;
          console.log(`[Complyo] ${Object.keys(this.templates).length} Templates geladen`);
        }
      } catch (error) {
        console.error('[Complyo] Fehler beim Laden der Templates:', error);
        throw error;
      }
    }
    
    async applyTemplate(templateId) {
      if (!this.templates || !this.templates[templateId]) {
        console.error(`[Complyo] Template "${templateId}" nicht gefunden`);
        return;
      }
      
      const template = this.templates[templateId];
      console.log(`[Complyo] Aktiviere Template: ${template.name}`);
      
      // 1. Entferne altes Template
      this.removeCurrentTemplate();
      
      // 2. Injiziere CSS
      if (template.css) {
        const style = document.createElement('style');
        style.id = 'complyo-template-css';
        style.textContent = template.css;
        document.head.appendChild(style);
        this.injectedElements.css = style;
      }
      
      // 3. Führe JavaScript aus
      if (template.js) {
        try {
          // Wrap in IIFE to avoid global scope pollution
          const scriptFunc = new Function(template.js);
          scriptFunc();
          console.log('[Complyo] JavaScript ausgeführt');
        } catch (error) {
          console.error('[Complyo] Fehler beim Ausführen von JavaScript:', error);
        }
      }
      
      // 4. Speichere aktives Template
      this.activeTemplate = templateId;
      localStorage.setItem('complyo_active_template', templateId);
      
      // 5. Update Toolbar UI
      this.updateToolbarUI();
      
      console.log(`[Complyo] Template "${template.name}" aktiviert ✓`);
    }
    
    removeCurrentTemplate() {
      // Entferne CSS
      if (this.injectedElements.css) {
        this.injectedElements.css.remove();
        this.injectedElements.css = null;
      }
      
      // Entferne HTML-Elemente (z.B. Skip-Links)
      this.injectedElements.html.forEach(el => {
        if (el && el.parentNode) {
          el.remove();
        }
      });
      this.injectedElements.html = [];
      
      // Remove Complyo-specific attributes and classes
      document.querySelectorAll('[data-complyo-alt-generated]').forEach(el => {
        el.removeAttribute('data-complyo-alt-generated');
      });
      
      document.querySelectorAll('[data-complyo-aria-generated]').forEach(el => {
        el.removeAttribute('data-complyo-aria-generated');
      });
      
      // Remove skip links
      document.querySelectorAll('.complyo-skip-link, .complyo-skip-links').forEach(el => el.remove());
    }
    
    renderToolbar() {
      const toolbar = document.createElement('div');
      toolbar.id = 'complyo-a11y-widget';
      toolbar.innerHTML = `
        <style>
          #complyo-a11y-widget {
            position: fixed;
            top: 20px;
            right: 20px;
            background: white;
            border-radius: 16px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.2);
            z-index: 2147483647;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            max-width: 420px;
            transition: all 0.3s ease;
          }
          
          #complyo-a11y-widget.minimized {
            max-width: 60px;
          }
          
          .complyo-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 16px;
            background: linear-gradient(135deg, #7c3aed 0%, #a855f7 100%);
            color: white;
            border-radius: 16px 16px 0 0;
            cursor: pointer;
          }
          
          .complyo-title {
            font-size: 16px;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 8px;
          }
          
          #complyo-a11y-widget.minimized .complyo-title span {
            display: none;
          }
          
          .complyo-toggle {
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
          
          .complyo-toggle:hover {
            background: rgba(255,255,255,0.3);
            transform: scale(1.1);
          }
          
          #complyo-a11y-widget.minimized .complyo-toggle {
            display: none;
          }
          
          .complyo-content {
            padding: 20px;
            max-height: 70vh;
            overflow-y: auto;
          }
          
          #complyo-a11y-widget.minimized .complyo-content {
            display: none;
          }
          
          .complyo-section {
            margin-bottom: 20px;
          }
          
          .complyo-section-title {
            font-size: 14px;
            font-weight: 600;
            color: #374151;
            margin-bottom: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
          }
          
          .complyo-template-card {
            border: 2px solid #e5e7eb;
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 12px;
            cursor: pointer;
            transition: all 0.2s;
            background: white;
          }
          
          .complyo-template-card:hover {
            border-color: #7c3aed;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(124, 58, 237, 0.15);
          }
          
          .complyo-template-card.active {
            border-color: #7c3aed;
            background: linear-gradient(135deg, rgba(124, 58, 237, 0.05) 0%, rgba(168, 85, 247, 0.05) 100%);
          }
          
          .complyo-template-name {
            font-size: 15px;
            font-weight: 600;
            color: #1f2937;
            margin-bottom: 4px;
            display: flex;
            align-items: center;
            justify-content: space-between;
          }
          
          .complyo-template-level {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 700;
            background: #7c3aed;
            color: white;
          }
          
          .complyo-template-desc {
            font-size: 13px;
            color: #6b7280;
            margin-bottom: 8px;
          }
          
          .complyo-template-features {
            font-size: 12px;
            color: #9ca3af;
          }
          
          .complyo-active-badge {
            background: #10b981;
            color: white;
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 600;
          }
          
          .complyo-code-section {
            background: #f9fafb;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 12px;
            margin-top: 12px;
          }
          
          .complyo-code-title {
            font-size: 12px;
            font-weight: 600;
            color: #6b7280;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            justify-content: space-between;
          }
          
          .complyo-code-content {
            font-family: 'Courier New', monospace;
            font-size: 11px;
            color: #374151;
            background: white;
            padding: 10px;
            border-radius: 4px;
            max-height: 200px;
            overflow-y: auto;
            white-space: pre-wrap;
            word-break: break-all;
          }
          
          .complyo-btn {
            padding: 8px 16px;
            border: none;
            border-radius: 6px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
          }
          
          .complyo-btn-primary {
            background: #7c3aed;
            color: white;
          }
          
          .complyo-btn-primary:hover {
            background: #6d28d9;
          }
          
          .complyo-btn-secondary {
            background: #e5e7eb;
            color: #374151;
          }
          
          .complyo-btn-secondary:hover {
            background: #d1d5db;
          }
          
          .complyo-branding {
            text-align: center;
            padding: 12px;
            font-size: 11px;
            color: #9ca3af;
            border-top: 1px solid #e5e7eb;
          }
          
          .complyo-branding a {
            color: #7c3aed;
            text-decoration: none;
            font-weight: 600;
          }
        </style>
        
        <div class="complyo-header" onclick="document.getElementById('complyo-a11y-widget').classList.toggle('minimized')">
          <div class="complyo-title">
            <span>♿</span>
            <span>Barrierefreiheit</span>
          </div>
          <button class="complyo-toggle" aria-label="Minimieren">−</button>
        </div>
        
        <div class="complyo-content">
          <div class="complyo-section">
            <div class="complyo-section-title">📋 WCAG Code-Templates</div>
            <div id="template-list">Lade Templates...</div>
          </div>
          
          <div class="complyo-section" id="active-template-code" style="display: none;">
            <div class="complyo-section-title">💻 Aktiver Code</div>
            <div class="complyo-code-section">
              <div class="complyo-code-title">
                <span>CSS</span>
                <button class="complyo-btn complyo-btn-secondary" onclick="window.complyoWidget.copyCode('css')">Kopieren</button>
              </div>
              <div class="complyo-code-content" id="code-css"></div>
            </div>
            
            <div class="complyo-code-section">
              <div class="complyo-code-title">
                <span>HTML</span>
                <button class="complyo-btn complyo-btn-secondary" onclick="window.complyoWidget.copyCode('html')">Kopieren</button>
              </div>
              <div class="complyo-code-content" id="code-html"></div>
            </div>
            
            <div class="complyo-code-section">
              <div class="complyo-code-title">
                <span>JavaScript</span>
                <button class="complyo-btn complyo-btn-secondary" onclick="window.complyoWidget.copyCode('js')">Kopieren</button>
              </div>
              <div class="complyo-code-content" id="code-js"></div>
            </div>
          </div>
        </div>
        
        <div class="complyo-branding">
          Powered by <a href="https://complyo.tech" target="_blank">Complyo</a> v${WIDGET_VERSION}
        </div>
      `;
      
      document.body.appendChild(toolbar);
      this.toolbarElement = toolbar;
      
      // Render template list
      this.renderTemplateList();
    }
    
    renderTemplateList() {
      if (!this.templates) return;
      
      const list = document.getElementById('template-list');
      if (!list) return;
      
      list.innerHTML = '';
      
      Object.entries(this.templates).forEach(([id, template]) => {
        const card = document.createElement('div');
        card.className = 'complyo-template-card';
        if (this.activeTemplate === id) {
          card.classList.add('active');
        }
        
        card.innerHTML = `
          <div class="complyo-template-name">
            <span>${template.name}</span>
            ${this.activeTemplate === id ? '<span class="complyo-active-badge">AKTIV</span>' : `<span class="complyo-template-level">${template.level}</span>`}
          </div>
          <div class="complyo-template-desc">${template.description}</div>
          <div class="complyo-template-features">
            ${template.features.length} Features • ~${template.estimated_time}
          </div>
        `;
        
        card.addEventListener('click', () => {
          this.applyTemplate(id);
        });
        
        list.appendChild(card);
      });
    }
    
    updateToolbarUI() {
      this.renderTemplateList();
      
      // Show code section
      const codeSection = document.getElementById('active-template-code');
      if (codeSection && this.activeTemplate) {
        codeSection.style.display = 'block';
        
        const template = this.templates[this.activeTemplate];
        document.getElementById('code-css').textContent = template.css || '// Kein CSS';
        document.getElementById('code-html').textContent = template.html || '<!-- Kein HTML -->';
        document.getElementById('code-js').textContent = template.js || '// Kein JavaScript';
      }
    }
    
    async copyCode(type) {
      if (!this.activeTemplate) return;
      
      const template = this.templates[this.activeTemplate];
      let code = '';
      
      switch(type) {
        case 'css':
          code = template.css || '';
          break;
        case 'html':
          code = template.html || '';
          break;
        case 'js':
          code = template.js || '';
          break;
      }
      
      try {
        await navigator.clipboard.writeText(code);
        alert(`${type.toUpperCase()}-Code kopiert! Sie können ihn jetzt in Ihre Website einfügen.`);
      } catch (err) {
        console.error('[Complyo] Fehler beim Kopieren:', err);
        // Fallback: Show code in prompt
        prompt(`${type.toUpperCase()}-Code (Strg+C zum Kopieren):`, code);
      }
    }
    
    downloadTemplate() {
      if (!this.activeTemplate) return;
      
      const template = this.templates[this.activeTemplate];
      
      // Create a comprehensive integration file
      const content = `
# Complyo Accessibility Template: ${template.name}
# WCAG ${template.level} Compliance
# Generiert am: ${new Date().toLocaleDateString('de-DE')}

## CSS (Fügen Sie dies in Ihre style.css ein)
${template.css}

## HTML (Fügen Sie dies in Ihre HTML-Dateien ein)
${template.html}

## JavaScript (Fügen Sie dies vor </body> ein)
<script>
${template.js}
</script>

## Features
${template.features.map(f => `- ${f}`).join('\n')}

## WCAG Kriterien
${template.wcag_criteria.map(c => `- ${c}`).join('\n')}

## Integration
Geschätzte Zeit: ${template.estimated_time}

1. Kopieren Sie den CSS-Code in Ihre Haupt-CSS-Datei
2. Fügen Sie den HTML-Code in Ihre Templates ein
3. Fügen Sie den JavaScript-Code vor dem </body>-Tag ein
4. Testen Sie mit Tab-Taste und Screen-Reader

---
Powered by Complyo • https://complyo.tech
`;
      
      const blob = new Blob([content], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `complyo-accessibility-${this.activeTemplate}.txt`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }
  }
  
  // Auto-initialize
  if (document.currentScript && document.currentScript.getAttribute('data-site-id')) {
    const script = document.currentScript;
    const config = {
      siteId: script.getAttribute('data-site-id'),
      autoLoad: script.getAttribute('data-auto-load') !== 'false',
      showToolbar: script.getAttribute('data-show-toolbar') !== 'false',
      defaultTemplate: script.getAttribute('data-default-template') || 'standard'
    };
    
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => {
        window.complyoWidget = new ComplyoAccessibilityWidget(config);
      });
    } else {
      window.complyoWidget = new ComplyoAccessibilityWidget(config);
    }
  }
  
  // Export for manual initialization
  window.ComplyoAccessibilityWidget = ComplyoAccessibilityWidget;
  
  console.log(`[Complyo] Widget v${WIDGET_VERSION} geladen - ECHTE Code-Templates, KEIN Overlay!`);
})();
