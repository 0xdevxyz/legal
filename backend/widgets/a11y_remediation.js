/**
 * Complyo Accessibility – Runtime-Remediation (Channel #3)
 * =======================================================
 * Für React/Vue/Angular/SPAs, deren gerendertes DOM serverseitig nicht
 * erreichbar ist. Konsumiert das vereinheitlichte FIX-MANIFEST und wendet die
 * freigegebenen Fixes auf das LIVE-DOM an; ein MutationObserver re-appliziert
 * nach jedem Re-Render, sodass die Fixes Framework-Updates überleben.
 *
 * Angewendete Fix-Typen (alle guarded — nie etwas Vorhandenes überschreiben):
 *   - alt_texts:      KI-Alt-Texte je Bild (image_filename/src, normalisiert)
 *   - html-lang:      lang-Attribut auf <html>, falls leer        (WCAG 3.1.1)
 *   - skip-link:      "Zum Inhalt springen" vor den Inhalt          (WCAG 2.4.1)
 *   - css-rule:       z.B. sichtbarer Fokus-Indikator               (WCAG 2.4.7)
 *
 * Ehrliche Grenze: Runtime-Remediation (korrigiert echte Semantik, nicht nur
 * Kosmetik), aber nicht quellseitig. Für Quell-Korrektur in SPAs: ESLint-Plugin/
 * Codemod im Repo (Roadmap).
 *
 * Einbindung:
 *   <script src="https://api.complyo.de/api/widgets/a11y-fixes.js"
 *           data-site-id="DEINE-SITE-ID" defer></script>
 *
 * Quelle (kanonisch, nur Status "approved"):
 *   GET {api}/api/accessibility/fix-manifest/{site_id}
 */
(function () {
  'use strict';

  var scriptEl = document.currentScript || (function () {
    var s = document.querySelectorAll('script[data-site-id]');
    return s.length ? s[s.length - 1] : null;
  })();
  if (!scriptEl) return;

  var siteId = scriptEl.getAttribute('data-site-id');
  if (!siteId) return;

  var apiBase = scriptEl.getAttribute('data-api') ||
    (location.hostname === 'localhost' ? 'http://localhost:8002' : 'https://api.complyo.de');

  var map = Object.create(null);   // normalisierter Dateiname -> alt-text
  var docFixes = [];               // dokumentweite Fixes
  var linkFixes = [];              // [{link_href, link_text, suggested_label}]
  var cssRules = [];               // [{selector, declarations}]
  var ready = false;

  // Basis-Dateiname (klein) inkl. Entfernung der WP-Größensuffixe (-300x200).
  function norm(p) {
    if (!p) return '';
    p = String(p).split(/[?#]/)[0];
    p = p.split('/').pop() || '';
    p = p.toLowerCase();
    p = p.replace(/-\d+x\d+(\.[a-z0-9]+)$/i, '$1');
    return p;
  }

  function altFor(img) {
    var src = img.getAttribute('src') || img.getAttribute('data-src') || img.currentSrc || '';
    var key = norm(src);
    return key && map[key] ? map[key] : null;
  }

  // ---- Alt-Texte (laufen bei jedem Re-Render) ------------------------------
  function applyAltTexts() {
    var imgs = document.images || document.getElementsByTagName('img');
    for (var i = 0; i < imgs.length; i++) {
      var img = imgs[i];
      var cur = img.getAttribute('alt');
      if (cur && cur.trim() !== '') continue; // vorhandenes alt nie überschreiben
      var alt = altFor(img);
      if (alt) img.setAttribute('alt', alt);
    }
  }

  // ---- Dokumentweite Fixes (idempotent, einmal pro Render reicht) -----------
  function fixPayload(type) {
    for (var i = 0; i < docFixes.length; i++) {
      if (docFixes[i] && docFixes[i].fix_type === type) return docFixes[i].payload || {};
    }
    return null;
  }

  function applyHtmlLang() {
    var p = fixPayload('html-lang');
    if (!p || !p.value) return;
    var html = document.documentElement;
    var cur = (html.getAttribute('lang') || '').trim();
    if (cur === '') html.setAttribute('lang', p.value); // nur setzen, wenn leer
  }

  function resolveMainTarget(preferred) {
    // bevorzugtes Ziel (z.B. "#main") sonst gängige Hauptinhalts-Container.
    var el = null;
    if (preferred) { try { el = document.querySelector(preferred); } catch (e) {} }
    if (!el) el = document.querySelector('main, [role="main"], #content, #content-main, #primary');
    return el;
  }

  function applySkipLink() {
    var p = fixPayload('skip-link');
    if (!p) return;
    if (document.querySelector('a[data-complyo-skip-link]')) return; // schon injiziert

    var target = resolveMainTarget(p.target);
    if (!target) return; // ohne auflösbares Ziel keinen Dangling-Link injizieren
    if (!target.id) target.id = 'complyo-main';
    var href = '#' + target.id;

    var a = document.createElement('a');
    a.setAttribute('href', href);
    a.setAttribute('data-complyo-skip-link', '1');
    a.className = 'complyo-skip-link';
    a.textContent = p.label || 'Zum Inhalt springen';
    if (document.body && document.body.firstChild) {
      document.body.insertBefore(a, document.body.firstChild);
    } else if (document.body) {
      document.body.appendChild(a);
    }
  }

  function applyLandmarkMain() {
    if (!fixPayload('landmark-main')) return;
    if (document.querySelector('main, [role="main"]')) return; // bereits vorhanden
    var el = resolveMainTarget(null);
    if (el && !el.getAttribute('role')) el.setAttribute('role', 'main');
  }

  // CSS einmalig in den <head> injizieren (Fokus/Kontrast + Skip-Link-Styling).
  function injectStyleOnce() {
    if (document.getElementById('complyo-a11y-style')) return;
    var css = '.complyo-skip-link{position:absolute;left:-9999px;top:0;z-index:100000;' +
      'background:#1a73e8;color:#fff;padding:8px 16px;border-radius:0 0 4px 0;' +
      'text-decoration:none;font:14px/1.4 sans-serif;}' +
      '.complyo-skip-link:focus{left:0;}';
    for (var i = 0; i < cssRules.length; i++) {
      var r = cssRules[i];
      if (r && r.selector && r.declarations) css += r.selector + '{' + r.declarations + '}';
    }
    var style = document.createElement('style');
    style.id = 'complyo-a11y-style';
    style.appendChild(document.createTextNode(css));
    (document.head || document.documentElement).appendChild(style);
  }

  // ---- Link-Zweck (WCAG 2.4.4): aria-label auf nichtssagende Links -----------
  function normText(s) { return (s || '').replace(/\s+/g, ' ').trim().toLowerCase(); }

  function hrefMatch(a, b) {
    if (!a || !b) return false;
    if (a === b) return true;
    // tolerant ggü. absolut/relativ: Endungs-Vergleich der Pfade.
    return a.indexOf(b) !== -1 || b.indexOf(a) !== -1;
  }

  function labelForLink(txt, href) {
    var nt = normText(txt);
    for (var i = 0; i < linkFixes.length; i++) {
      var f = linkFixes[i];
      if (normText(f.link_text) === nt && hrefMatch(href, f.link_href)) {
        return f.suggested_label || null;
      }
    }
    return null;
  }

  function applyLinkLabels() {
    if (!linkFixes.length) return;
    var anchors = document.getElementsByTagName('a');
    for (var i = 0; i < anchors.length; i++) {
      var a = anchors[i];
      // vorhandenen zugänglichen Namen nie überschreiben
      if ((a.getAttribute('aria-label') || '').trim() !== '') continue;
      if ((a.getAttribute('title') || '').trim() !== '') continue;
      var txt = (a.textContent || '').trim();
      if (!txt) continue;
      var label = labelForLink(txt, a.getAttribute('href') || '');
      if (label) a.setAttribute('aria-label', label);
    }
  }

  function apply() {
    if (!ready) return;
    applyAltTexts();
    applyHtmlLang();
    applySkipLink();
    applyLandmarkMain();
    applyLinkLabels();
  }

  var scheduled = false;
  function schedule() {
    if (scheduled) return;
    scheduled = true;
    var run = function () { scheduled = false; apply(); };
    if (window.requestAnimationFrame) window.requestAnimationFrame(run);
    else setTimeout(run, 50);
  }

  function observe() {
    if (!window.MutationObserver) return;
    var mo = new MutationObserver(function (muts) {
      for (var i = 0; i < muts.length; i++) {
        var m = muts[i];
        if (m.type === 'childList' && m.addedNodes && m.addedNodes.length) { schedule(); return; }
        if (m.type === 'attributes' && m.target && m.target.tagName === 'IMG') { schedule(); return; }
      }
    });
    mo.observe(document.documentElement, {
      childList: true, subtree: true,
      attributes: true, attributeFilter: ['src', 'data-src', 'alt']
    });
  }

  function ingestManifest(d) {
    if (!d) return;
    var alts = d.alt_texts || d.fixes || [];
    for (var i = 0; i < alts.length; i++) {
      var f = alts[i];
      var alt = (f.suggested_alt || f.alt_text || f.generated_alt || f.alt || '').trim();
      if (!alt) continue;
      var cands = [f.image_filename, f.image_src];
      for (var j = 0; j < cands.length; j++) {
        var k = norm(cands[j]);
        if (k) map[k] = alt;
      }
    }
    docFixes = d.document_fixes || [];
    linkFixes = d.link_fixes || [];
    cssRules = d.css_rules || [];
  }

  function load() {
    var url = apiBase.replace(/\/+$/, '') +
      '/api/accessibility/fix-manifest/' + encodeURIComponent(siteId);
    fetch(url, { headers: { accept: 'application/json' } })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (d) {
        ingestManifest(d);
        ready = true;
        injectStyleOnce();
        apply();
        observe();
        // Nach-Hydration-Sicherheitsnetz für späte SPA-Renders:
        setTimeout(apply, 1000);
        setTimeout(apply, 3000);
      })
      .catch(function () { /* fail-silent */ });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', load);
  } else {
    load();
  }
})();
