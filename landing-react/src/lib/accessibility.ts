export interface AccessibilityReport {
  score: number;
  issues: AccessibilityIssue[];
  passed: string[];
  wcagLevel: 'A' | 'AA' | 'AAA';
}

export interface AccessibilityIssue {
  type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  element?: string;
  recommendation: string;
}

export class ComplyoAccessibility {
  private announcer!: HTMLElement;
  private alertRegion!: HTMLElement;
  private previousFocus: Element | null = null;

  constructor(options: { autoFix?: boolean; announceChanges?: boolean } = {}) {
    this.init();
    
    if (options.autoFix) {
      this.runAutoFixes();
    }
  }

  private init() {
    this.setupScreenReaderSupport();
    this.setupKeyboardNavigation();
    this.setupModalHandling();
    this.setupLiveRegions();
    this.announce('Complyo Accessibility Framework aktiviert');
  }

  private setupScreenReaderSupport() {
    this.announcer = document.createElement('div');
    this.announcer.setAttribute('aria-live', 'polite');
    this.announcer.setAttribute('aria-atomic', 'true');
    this.announcer.className = 'sr-only';
    document.body.appendChild(this.announcer);

    this.alertRegion = document.createElement('div');
    this.alertRegion.setAttribute('aria-live', 'assertive');
    this.alertRegion.className = 'sr-only';
    document.body.appendChild(this.alertRegion);

    this.enhanceARIALabels();
  }

  private enhanceARIALabels() {
    document.querySelectorAll('button:not([aria-label]):not([aria-labelledby])').forEach(btn => {
      const text = (btn as HTMLElement).textContent?.trim();
      if (!text) {
        const icon = btn.querySelector('svg, i, [class*="icon"]');
        if (icon) {
          btn.setAttribute('aria-label', 'Button');
        }
      }
    });

    document.querySelectorAll('img:not([alt])').forEach(img => {
      const isDecorative = img.closest('[role="presentation"]') || 
                         img.getAttribute('role') === 'presentation';
      img.setAttribute('alt', isDecorative ? '' : 'Bild');
    });
  }

  private setupKeyboardNavigation() {
    document.addEventListener('keydown', (e) => {
      // Skip if the event is from an input, textarea, or contenteditable element
      const target = e.target as HTMLElement;
      if (target.matches('input, textarea, [contenteditable="true"]')) {
        return;
      }
      
      if (e.key === 'Escape') {
        this.handleEscape();
      }

      if (e.altKey && e.key === 'm') {
        const main = document.querySelector('main, #main, [role="main"]') as HTMLElement;
        if (main) {
          main.focus();
          this.announce('Zum Hauptinhalt gesprungen');
        }
      }

      if (e.altKey && e.key === 'n') {
        const nav = document.querySelector('nav, [role="navigation"]') as HTMLElement;
        if (nav) {
          nav.focus();
          this.announce('Zur Navigation gesprungen');
        }
      }
    });

    document.querySelectorAll('[role="dialog"]').forEach(modal => {
      this.setupTabTrapping(modal as HTMLElement);
    });
  }

  private setupTabTrapping(modal: HTMLElement) {
    const focusableElements = modal.querySelectorAll(
      'a, button, input, select, textarea, [tabindex]:not([tabindex="-1"])'
    ) as NodeListOf<HTMLElement>;
    
    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    modal.addEventListener('keydown', (e) => {
      if (e.key === 'Tab') {
        if (e.shiftKey && document.activeElement === firstElement) {
          e.preventDefault();
          lastElement?.focus();
        } else if (!e.shiftKey && document.activeElement === lastElement) {
          e.preventDefault();
          firstElement?.focus();
        }
      }
    });
  }

  private setupModalHandling() {
    document.addEventListener('click', (e) => {
      const target = e.target as HTMLElement;
      const modalTrigger = target.closest('[data-modal-trigger]') as HTMLElement;
      
      if (modalTrigger) {
        e.preventDefault();
        const modalId = modalTrigger.getAttribute('data-modal-trigger');
        if (modalId) {
          this.openModal(modalId);
        }
      }

      const closeBtn = target.closest('[data-modal-close]');
      if (closeBtn) {
        this.closeModal();
      }
    });
  }

  private openModal(modalId: string) {
    const modal = document.getElementById(modalId) as HTMLElement;
    if (!modal) return;

    this.previousFocus = document.activeElement as Element;
    modal.style.display = 'flex';
    modal.setAttribute('aria-hidden', 'false');
    
    // Only focus if the current active element is not an input field
    const currentElement = document.activeElement as HTMLElement;
    if (!currentElement.matches('input, textarea, [contenteditable="true"]')) {
      const focusable = modal.querySelector('button, input, select, textarea, a, [tabindex]') as HTMLElement;
      if (focusable) {
        focusable.focus();
      }
    }

    document.body.style.overflow = 'hidden';
    this.announce('Modal geöffnet');
  }

  private closeModal() {
    const modal = document.querySelector('[role="dialog"][style*="flex"]') as HTMLElement;
    if (!modal) return;

    modal.style.display = 'none';
    modal.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';

    if (this.previousFocus) {
      (this.previousFocus as HTMLElement).focus();
    }

    this.announce('Modal geschlossen');
  }

  private handleEscape() {
    this.closeModal();
    
    document.querySelectorAll('[aria-expanded="true"]').forEach(element => {
      element.setAttribute('aria-expanded', 'false');
    });
  }

  private setupLiveRegions() {
    const observer = new MutationObserver((mutations) => {
      mutations.forEach(mutation => {
        if (mutation.type === 'childList') {
          mutation.addedNodes.forEach(node => {
            if (node.nodeType === 1 && (node as Element).matches('[role="alert"]')) {
              this.announceAlert((node as Element).textContent || '');
            }
          });
        }
      });
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true
    });
  }

  private runAutoFixes() {
    if (!document.querySelector('.a11y-skip-link')) {
      this.addSkipLinks();
    }

    this.fixImageAltTexts();
    this.fixFormLabels();
  }

  private addSkipLinks() {
    const main = document.querySelector('main, #main, [role="main"]') as HTMLElement;
    const nav = document.querySelector('nav, [role="navigation"]') as HTMLElement;

    if (main || nav) {
      const skipLinks = document.createElement('div');
      skipLinks.innerHTML = `
        ${main ? `<a href="#${main.id || 'main-content'}" class="a11y-skip-link">Zum Hauptinhalt springen</a>` : ''}
        ${nav ? `<a href="#${nav.id || 'navigation'}" class="a11y-skip-link">Zur Navigation springen</a>` : ''}
      `;
      document.body.insertBefore(skipLinks, document.body.firstChild);
    }
  }

  private fixImageAltTexts() {
    document.querySelectorAll('img:not([alt])').forEach(img => {
      const isDecorative = img.closest('[role="presentation"]');
      const src = (img as HTMLImageElement).src;
      const filename = src ? src.split('/').pop()?.split('.')[0] : '';
      img.setAttribute('alt', isDecorative ? '' : filename || 'Bild');
    });
  }

  private fixFormLabels() {
    document.querySelectorAll('input, select, textarea').forEach(field => {
      // Skip the website-url input to prevent any interference
      if ((field as HTMLElement).id === 'website-url') {
        return;
      }
      
      if (!field.getAttribute('aria-label') && !field.getAttribute('aria-labelledby')) {
        const label = field.closest('label') || 
                    document.querySelector(`label[for="${(field as HTMLElement).id}"]`);
        
        if (!label && (field as HTMLInputElement).placeholder) {
          field.setAttribute('aria-label', (field as HTMLInputElement).placeholder);
        }
      }
    });
  }

  public announce(message: string, priority: 'polite' | 'assertive' = 'polite') {
    const region = priority === 'assertive' ? this.alertRegion : this.announcer;
    region.textContent = message;
    
    setTimeout(() => {
      region.textContent = '';
    }, 1000);
  }

  public announceAlert(message: string) {
    this.announce(message, 'assertive');
  }

  public async runAccessibilityTest(): Promise<AccessibilityReport> {
    const results: AccessibilityReport = {
      score: 0,
      issues: [],
      passed: [],
      wcagLevel: 'AA'
    };

    const imagesWithoutAlt = document.querySelectorAll('img:not([alt])');
    if (imagesWithoutAlt.length === 0) {
      results.passed.push('Alle Bilder haben Alt-Texte');
      results.score += 20;
    } else {
      results.issues.push({
        type: 'images',
        severity: 'high',
        message: `${imagesWithoutAlt.length} Bilder ohne Alt-Text gefunden`,
        recommendation: 'Fügen Sie beschreibende Alt-Texte für alle Bilder hinzu'
      });
    }

    const inputsWithoutLabels = Array.from(document.querySelectorAll('input:not([aria-label]):not([aria-labelledby])')).filter(input => {
      return !document.querySelector(`label[for="${(input as HTMLElement).id}"]`) && !input.closest('label');
    });
    
    if (inputsWithoutLabels.length === 0) {
      results.passed.push('Alle Formulareingaben haben Labels');
      results.score += 20;
    } else {
      results.issues.push({
        type: 'forms',
        severity: 'critical',
        message: `${inputsWithoutLabels.length} Eingabefelder ohne Label`,
        recommendation: 'Stellen Sie sicher, dass alle Formularelemente beschriftetet sind'
      });
    }

    const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
    let hierarchyValid = true;
    let lastLevel = 0;

    headings.forEach(heading => {
      const level = parseInt(heading.tagName.charAt(1));
      if (level > lastLevel + 1 && lastLevel !== 0) {
        hierarchyValid = false;
      }
      lastLevel = level;
    });

    if (hierarchyValid) {
      results.passed.push('Heading-Hierarchie ist korrekt');
      results.score += 20;
    } else {
      results.issues.push({
        type: 'headings',
        severity: 'medium',
        message: 'Heading-Hierarchie hat Lücken',
        recommendation: 'Verwenden Sie Überschriften in der richtigen Reihenfolge (h1, h2, h3, ...)'
      });
    }

    const focusableElements = document.querySelectorAll('a, button, input, select, textarea, [tabindex]');
    let keyboardIssues = 0;

    focusableElements.forEach(element => {
      const tabIndex = element.getAttribute('tabindex');
      if (tabIndex && parseInt(tabIndex) > 0) {
        keyboardIssues++;
      }
    });

    if (keyboardIssues === 0) {
      results.passed.push('Keyboard Navigation ist korrekt konfiguriert');
      results.score += 20;
    } else {
      results.issues.push({
        type: 'keyboard',
        severity: 'medium',
        message: `${keyboardIssues} Elemente mit positiven tabindex-Werten`,
        recommendation: 'Vermeiden Sie positive tabindex-Werte, nutzen Sie die natürliche Tab-Reihenfolge'
      });
    }

    if (results.score >= 60) {
      results.passed.push('Grundlegendes Farbkontrast-Design befolgt');
      results.score += 20;
    }

    return results;
  }

  static init(options?: { autoFix?: boolean; announceChanges?: boolean }): ComplyoAccessibility {
    return new ComplyoAccessibility(options);
  }
}

declare global {
  interface Window {
    ComplyoA11y: ComplyoAccessibility;
  }
}