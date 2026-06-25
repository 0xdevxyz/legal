/**
 * Complyo Accessibility – Runtime Alt-Text-Remediation (Channel #3)
 * =================================================================
 * Für React/Vue/Angular/SPAs, deren gerendertes DOM serverseitig nicht
 * erreichbar ist. Holt die freigegebenen KI-Alt-Texte und setzt sie in das
 * LIVE-DOM; ein MutationObserver re-appliziert nach jedem Re-Render, sodass
 * die Fixes Framework-Updates überleben.
 *
 * Ehrliche Grenze: das ist Runtime-Remediation (korrigiert echte Semantik –
 * alt-Attribute –, nicht nur Kosmetik), aber nicht quellseitig. Für echte
 * Quell-Korrektur in SPAs: ESLint-Plugin/Codemod im Repo (Roadmap).
 *
 * Einbindung:
 *   <script src="https://api.complyo.de/api/widgets/a11y-fixes.js"
 *           data-site-id="DEINE-SITE-ID" defer></script>
 *
 * Quelle (kanonisch, nur Status "approved"):
 *   GET {api}/api/accessibility/alt-text-fixes?site_id=…&approved_only=true
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

  var map = Object.create(null);
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

  function apply() {
    if (!ready) return;
    var imgs = document.images || document.getElementsByTagName('img');
    for (var i = 0; i < imgs.length; i++) {
      var img = imgs[i];
      // vorhandenes, nicht-leeres alt nie überschreiben
      var cur = img.getAttribute('alt');
      if (cur && cur.trim() !== '') continue;
      var alt = altFor(img);
      if (alt) img.setAttribute('alt', alt);
    }
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

  function load() {
    var url = apiBase.replace(/\/+$/, '') +
      '/api/accessibility/alt-text-fixes?site_id=' + encodeURIComponent(siteId) + '&approved_only=true';
    fetch(url, { headers: { accept: 'application/json' } })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (d) {
        var fixes = d && d.fixes ? d.fixes : [];
        for (var i = 0; i < fixes.length; i++) {
          var f = fixes[i];
          var alt = (f.suggested_alt || f.alt_text || f.generated_alt || '').trim();
          if (!alt) continue;
          var cands = [f.image_filename, f.image_src];
          for (var j = 0; j < cands.length; j++) {
            var k = norm(cands[j]);
            if (k) map[k] = alt;
          }
        }
        ready = true;
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
