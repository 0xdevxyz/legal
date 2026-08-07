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
  var strukturFixes = [];          // Attribut-Setzungen (role, tabindex, title …)
  var linkFixes = [];              // [{link_href, link_text, suggested_label}]
  var cssRules = [];               // [{selector, declarations}]
  var ready = false;

  // ---- Wirkungsbilanz --------------------------------------------------------
  //
  // Das Widget ist die einzige Stelle, die weiss, was auf einer ECHTEN Seite
  // gerade tatsaechlich angekommen ist. Der Scan misst die Startseite zu einem
  // Zeitpunkt; hier laeuft die Pruefung bei jedem Aufruf, auf jeder Unterseite,
  // im Browser eines echten Besuchers.
  //
  // Der wertvolle Teil ist nicht `angewendet`, sondern `verfehlt`: ein Fix, der
  // ausgeliefert wurde und dessen Ziel es nicht mehr gibt. Genau so sieht ein
  // Theme-Update aus, das eine Klasse umbenennt — und genau das faellt sonst
  // erst beim naechsten Scan auf, Wochen spaeter.
  var bilanz = {
    alt_texte: { angewendet: 0, verfehlt: 0 },
    link_labels: { angewendet: 0, verfehlt: 0 },
    struktur: { angewendet: 0, verfehlt: 0 },
    css_regeln: { angewendet: 0, verfehlt: 0 }
  };

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
      if (alt) { img.setAttribute('alt', alt); bilanz.alt_texte.angewendet++; }
    }
    // Verfehlt: ein freigegebener Alt-Text, dessen Bild auf dieser Seite nicht
    // (mehr) vorkommt. Auf Unterseiten ist das normal — deshalb wird es
    // gezaehlt und nicht gemeldet; erst die Auswertung ueber viele Aufrufe
    // zeigt, ob ein Bild ueberall verschwunden ist.
    var gesehen = {};
    for (var k = 0; k < imgs.length; k++) {
      var q = norm(imgs[k].getAttribute('src') || imgs[k].currentSrc || '');
      if (q) gesehen[q] = 1;
    }
    for (var schluessel in map) {
      if (Object.prototype.hasOwnProperty.call(map, schluessel) && !gesehen[schluessel]) {
        bilanz.alt_texte.verfehlt++;
      }
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
    // Gemessenes Ziel aus der Struktur-Reparatur schlaegt jede Rateliste.
    if (!el) {
      for (var i = 0; i < strukturFixes.length; i++) {
        if (strukturFixes[i] && strukturFixes[i].attribut === 'role' &&
            strukturFixes[i].wert === 'main') {
          try { el = document.querySelector(strukturFixes[i].selector); } catch (e) {}
          if (el) break;
        }
      }
    }
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

  // Attribut-Setzungen aus der Struktur-Reparatur.
  //
  // Der Unterschied zu applyLandmarkMain(): dort wird zur Laufzeit GERATEN
  // (feste Selektorliste). Hier kommt der Selektor aus der Messung — beim Scan
  // wurde `role="main"` gesetzt, axe erneut laufen gelassen und nur behalten,
  // was die region-Befunde wirklich abgeraeumt hat. Im echten Bestand heissen
  // die Container `.wrapper`, `#main`, `#Content`, `#Wrapper` — die geratene
  // Liste traf die wenigsten davon.
  function applyStrukturFixes() {
    if (!strukturFixes.length) return 0;
    var gesetzt = 0;
    for (var i = 0; i < strukturFixes.length; i++) {
      var f = strukturFixes[i];
      if (!f || !f.selector || !f.attribut) continue;
      var ziele;
      try { ziele = document.querySelectorAll(f.selector); }
      catch (e) { bilanz.struktur.verfehlt++; continue; }  // ungueltiger Selektor
      // Kein Treffer heisst: das Ziel gibt es auf dieser Seite nicht mehr. Das
      // ist die Regressionsmeldung, auf die es ankommt — genau so sieht ein
      // Theme-Update aus, das eine Klasse umbenannt hat.
      if (!ziele.length) { bilanz.struktur.verfehlt++; continue; }
      for (var j = 0; j < ziele.length; j++) {
        var el = ziele[j];
        // Das viewport-Meta ist der einzige Fall, in dem ueberschrieben wird:
        // dort steht die Zoom-Sperre, die weg soll. Alles andere guarded.
        if (f.attribut === 'content' && el.tagName === 'META') {
          el.setAttribute('content', f.wert); gesetzt++; bilanz.struktur.angewendet++;
        } else if (!el.getAttribute(f.attribut)) {
          el.setAttribute(f.attribut, f.wert); gesetzt++; bilanz.struktur.angewendet++;
        }
      }
    }
    return gesetzt;
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
      if (!r || !r.selector || !r.declarations) continue;
      css += r.selector + '{' + r.declarations + '}';
      // Trifft die Regel auf dieser Seite ueberhaupt etwas? Eine Kontrastregel
      // ohne Ziel ist entweder eine Unterseite ohne dieses Element — oder ein
      // Selektor, den ein Theme-Update zerlegt hat.
      var trifft = 0;
      try { trifft = document.querySelectorAll(r.selector).length; } catch (e) { trifft = -1; }
      if (trifft > 0) bilanz.css_regeln.angewendet++;
      else if (trifft < 0) bilanz.css_regeln.verfehlt++;
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
      if (label) { a.setAttribute('aria-label', label); bilanz.link_labels.angewendet++; }
    }
  }

  function apply() {
    if (!ready) return;
    applyAltTexts();
    applyHtmlLang();
    // Struktur VOR dem Sprunglink: sie setzt das gemessene role="main" (und
    // gibt dem Container notfalls eine id). Erst danach hat applySkipLink()
    // ein aufloesbares Ziel — vorher landete der Link ins Nirgendwo und wurde
    // deshalb gar nicht erst injiziert.
    applyStrukturFixes();
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
    strukturFixes = d.struktur_fixes || [];
    linkFixes = d.link_fixes || [];
    cssRules = d.css_rules || [];
  }

  // ---- Rueckmeldung an complyo ----------------------------------------------
  //
  // Was gemeldet wird: der Pfad (ohne Parameter und Anker) und Zaehler. Sonst
  // nichts. Keine Kennung, kein Verweis, kein Zeitstempel des Besuchers — die
  // Meldung sagt etwas ueber die SEITE aus, nicht ueber den Menschen davor.
  // Deshalb braucht sie auch keine Einwilligung: sie verarbeitet keine
  // personenbezogenen Daten.
  //
  // Einmal je Seite und Sitzung. Ein Besucher, der zehnmal blaettert, erzeugt
  // zehn Pfade, aber keine zehn Meldungen derselben Seite.
  function melde() {
    var pfad;
    try {
      pfad = location.pathname.slice(0, 200);
      var schluessel = 'complyo_wirkung_' + siteId + pfad;
      if (sessionStorage.getItem(schluessel)) return;
      sessionStorage.setItem(schluessel, '1');
    } catch (e) { return; }   // Speicher gesperrt: dann eben keine Meldung

    var daten = {
      pfad: pfad,
      alt_texte: bilanz.alt_texte,
      link_labels: bilanz.link_labels,
      struktur: bilanz.struktur,
      css_regeln: bilanz.css_regeln,
      erwartet: {
        alt_texte: Object.keys(map).length,
        link_labels: linkFixes.length,
        struktur: strukturFixes.length,
        css_regeln: cssRules.length
      }
    };

    var url = apiBase.replace(/\/+$/, '') +
      '/api/wirkung/' + encodeURIComponent(siteId);
    try {
      var koerper = JSON.stringify(daten);
      // sendBeacon haelt die Meldung am Leben, wenn der Besucher sofort
      // weiterklickt. Ohne Fallback waere die Aussage auf schnellen Seiten
      // systematisch verzerrt.
      // text/plain statt application/json — und das ist kein Schludern:
      // application/json ist kein CORS-sicherer Inhaltstyp und loest einen
      // Preflight aus. sendBeacon kann keinen Preflight; die Meldung wird dann
      // stillschweigend verworfen. Genau so ist es beim ersten Live-Test auf
      // zua-zwickau.de passiert. text/plain gehoert zu den safelisted types,
      // damit geht die Meldung ohne Vorabfrage raus. Der Server liest den
      // Koerper ohnehin selbst als JSON.
      if (navigator.sendBeacon) {
        navigator.sendBeacon(url, new Blob([koerper], { type: 'text/plain;charset=UTF-8' }));
      } else {
        fetch(url, { method: 'POST', body: koerper, keepalive: true, mode: 'cors',
                     headers: { 'content-type': 'text/plain;charset=UTF-8' } })
          .catch(function () {});
      }
    } catch (e) { /* fail-silent: eine Messung darf nie die Seite stoeren */ }
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
        // Erst melden, wenn auch spaete Renders versorgt sind — sonst zaehlt
        // die Bilanz einen halben Seitenaufbau.
        setTimeout(melde, 3500);
      })
      .catch(function () { /* fail-silent */ });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', load);
  } else {
    load();
  }
})();
