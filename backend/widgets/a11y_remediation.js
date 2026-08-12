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
  var unbekannteKennung = false;   // data-site-id kennt complyo nicht
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
  //
  // Die Zaehlung ist idempotent ueber Laeufe. apply() laeuft mehrfach (initial,
  // 1000ms, 3000ms, MutationObserver); die erste Fassung addierte `verfehlt`
  // bei jedem Lauf auf, waehrend `angewendet` guarded nur einmal zaehlte —
  // gemessen: verfehlt=63 bei erwartet=2, eine Zahl, der niemand glaubt.
  // Deshalb Mengen eindeutiger Fix-Kennungen statt nackter Zaehler:
  // `verfehlt`/`unnoetig` werden je Lauf FRISCH aufgebaut (beginneLauf),
  // `angewendet` bleibt ueber Laeufe bestehen — einmal angekommen bleibt
  // angekommen, auch wenn ein SPA-Rerender das Ziel wieder entfernt hat.
  // melde() friert den Stand des letzten Laufs ein.
  //
  // Drei Zustaende statt zwei. "unnoetig" ist kein Fehlschlag: dass eine Seite
  // laengst ein <main> hat und `landmark-main` deshalb nichts tut, ist der
  // Normalfall und darf keinen Regressionsalarm ausloesen. Wer beides in einen
  // Topf wirft, erzeugt Rauschen — und eine Warnung, der niemand glaubt, ist
  // schlechter als keine.
  var bilanz = {
    alt_texte: { angewendet: 0, verfehlt: 0 },
    link_labels: { angewendet: 0, verfehlt: 0 },
    struktur: { angewendet: 0, verfehlt: 0, unnoetig: 0 },
    css_regeln: { angewendet: 0, verfehlt: 0 },
    dokument_fixes: { angewendet: 0, verfehlt: 0, unnoetig: 0 }
  };

  var BILANZ_ARTEN = ['alt_texte', 'link_labels', 'struktur', 'css_regeln', 'dokument_fixes'];

  function leereMenge() { return Object.create(null); }

  function _merkeNeu(menge, id) {
    if (menge[id]) return false;
    menge[id] = 1;
    return true;
  }

  var angewendetIds = {};
  var verfehltIds = {};
  var unnoetigIds = {};
  (function () {
    for (var i = 0; i < BILANZ_ARTEN.length; i++) {
      angewendetIds[BILANZ_ARTEN[i]] = leereMenge();
      verfehltIds[BILANZ_ARTEN[i]] = leereMenge();
      unnoetigIds[BILANZ_ARTEN[i]] = leereMenge();
    }
  })();

  // Je Lauf frisch: `verfehlt`/`unnoetig` beschreiben den AKTUELLEN Zustand
  // der Seite, nicht die Summe aller bisherigen Laeufe.
  function beginneLauf() {
    for (var i = 0; i < BILANZ_ARTEN.length; i++) {
      var art = BILANZ_ARTEN[i];
      verfehltIds[art] = leereMenge();
      unnoetigIds[art] = leereMenge();
      bilanz[art].verfehlt = 0;
      if ('unnoetig' in bilanz[art]) bilanz[art].unnoetig = 0;
    }
  }

  // true genau beim ERSTEN Mal — der Aufrufer zaehlt dann den Zaehler hoch.
  // "angewendet" gewinnt dauerhaft: was einmal angekommen ist, faellt spaeter
  // weder auf "verfehlt" noch auf "unnoetig" zurueck.
  function zaehltAngewendet(art, id) { return _merkeNeu(angewendetIds[art], id); }
  function zaehltVerfehlt(art, id) {
    if (angewendetIds[art][id]) return false;
    return _merkeNeu(verfehltIds[art], id);
  }
  function zaehltUnnoetig(art, id) {
    if (angewendetIds[art][id]) return false;
    return _merkeNeu(unnoetigIds[art], id);
  }
  // ---- Ende Wirkungsbilanz ---------------------------------------------------

  // Basis-Dateiname (klein) inkl. Entfernung der WP-Größensuffixe (-300x200).
  function norm(p) {
    if (!p) return '';
    p = String(p).split(/[?#]/)[0];
    p = p.split('/').pop() || '';
    p = p.toLowerCase();
    p = p.replace(/-\d+x\d+(\.[a-z0-9]+)$/i, '$1');
    return p;
  }

  // ---- Alt-Texte (laufen bei jedem Re-Render) ------------------------------
  function applyAltTexts() {
    var imgs = document.images || document.getElementsByTagName('img');
    for (var i = 0; i < imgs.length; i++) {
      var img = imgs[i];
      var cur = img.getAttribute('alt');
      if (cur && cur.trim() !== '') continue; // vorhandenes alt nie überschreiben
      var key = norm(img.getAttribute('src') || img.getAttribute('data-src') || img.currentSrc || '');
      var alt = key && map[key] ? map[key] : null;
      if (alt) {
        img.setAttribute('alt', alt);
        // je Bild-Datei einmal — nicht je <img> und nicht je Lauf
        if (zaehltAngewendet('alt_texte', key)) bilanz.alt_texte.angewendet++;
      }
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
        if (zaehltVerfehlt('alt_texte', schluessel)) bilanz.alt_texte.verfehlt++;
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
    if (cur === '') {
      html.setAttribute('lang', p.value); // nur setzen, wenn leer
      if (zaehltAngewendet('dokument_fixes', 'html-lang')) bilanz.dokument_fixes.angewendet++;
    } else if (zaehltUnnoetig('dokument_fixes', 'html-lang')) {
      // Seite bringt ihr lang selbst mit — Normalfall, kein Fehlschlag.
      bilanz.dokument_fixes.unnoetig++;
    }
  }

  // Volatile ID-Klassen (Elementor-Post-ID u.ä.): seitenspezifisch — der
  // exakte Mess-Selektor der Startseite trifft damit auf Unterseiten nichts.
  var RANDBEREICH_RE = /(^|[-_ ])(header|footer|nav|navigation|topbar|menu|sidebar|widget|cookie|banner)([-_ ]|$)/i;

  function istRandbereich(el) {
    if (el.closest && el.closest('header,nav,footer,aside')) return true;
    return RANDBEREICH_RE.test(el.id || '') ||
           RANDBEREICH_RE.test((el.className || '').toString());
  }

  // Löst das Ziel eines Struktur-Fixes auf: exakter Selektor → bei der
  // Messung verifizierte Alternativen (Manifest-Feld `alternativen`) →
  // Ableitung aus dem exakten Selektor (volatile ID-Klassen gestrichen).
  // Alles außer dem exakten Treffer gilt nur bei GENAU einem Treffer
  // außerhalb der Randbereiche — lieber verfehlt melden als role="main"
  // auf den falschen Container setzen (Audit 11.08.: Unterseiten 0/63).
  // Rückgabe: NodeList/Array der Ziele, [] = verfehlt, 'unnoetig' = Seite
  // hat schon eine main-Landmark, null = ungültiger Selektor.
  function findeStrukturZiele(f) {
    var ziele;
    try { ziele = document.querySelectorAll(f.selector); } catch (e) { return null; }
    if (ziele.length) return ziele;

    var kandidaten = [];
    if (f.alternativen && f.alternativen.length) kandidaten = kandidaten.concat(f.alternativen);
    var abgeleitet = String(f.selector)
      .replace(/\.(elementor|postid|post|page-id|page)-\d+(?![\w-])/g, '');
    if (abgeleitet !== f.selector && abgeleitet.replace(/[\s>+~]/g, '')) {
      kandidaten.push(abgeleitet);
    }

    var sucheMain = f.attribut === 'role' && f.wert === 'main';
    for (var i = 0; i < kandidaten.length; i++) {
      var t;
      try { t = document.querySelectorAll(kandidaten[i]); } catch (e) { continue; }
      if (t.length !== 1 || istRandbereich(t[0])) continue;
      // Nie eine zweite main-Landmark erzeugen — das wäre ein neuer Fehler.
      if (sucheMain && document.querySelector('main, [role="main"]')) return 'unnoetig';
      return t;
    }
    if (sucheMain && document.querySelector('main, [role="main"]')) return 'unnoetig';
    return ziele;
  }

  function resolveMainTarget(preferred) {
    // bevorzugtes Ziel (z.B. "#main") sonst gängige Hauptinhalts-Container.
    var el = null;
    if (preferred) { try { el = document.querySelector(preferred); } catch (e) {} }
    // Gemessenes Ziel aus der Struktur-Reparatur schlaegt jede Rateliste —
    // inklusive der stabilen Alternativen für Unterseiten.
    if (!el) {
      for (var i = 0; i < strukturFixes.length; i++) {
        if (strukturFixes[i] && strukturFixes[i].attribut === 'role' &&
            strukturFixes[i].wert === 'main') {
          var ziele = findeStrukturZiele(strukturFixes[i]);
          if (ziele && ziele !== 'unnoetig' && ziele.length) { el = ziele[0]; break; }
        }
      }
    }
    if (!el) el = document.querySelector('main, [role="main"], #content, #content-main, #primary');
    return el;
  }

  function applySkipLink() {
    var p = fixPayload('skip-link');
    if (!p) return;
    if (document.querySelector('a[data-complyo-skip-link]')) {
      // Schon injiziert: aus einem frueheren Lauf (dann bleibt es beim
      // "angewendet" von damals) oder von einem zweiten Einbau daneben.
      if (zaehltUnnoetig('dokument_fixes', 'skip-link')) bilanz.dokument_fixes.unnoetig++;
      return;
    }

    var target = resolveMainTarget(p.target);
    if (!target) {
      // Ohne aufloesbares Ziel keinen ins Leere zeigenden Link injizieren —
      // ein "Zum Inhalt springen", das nirgends landet, ist fuer Tastatur-
      // nutzer schlechter als gar keins. Aber melden: das ist ein
      // ausgelieferter Fix, der nicht ankommt.
      if (zaehltVerfehlt('dokument_fixes', 'skip-link')) bilanz.dokument_fixes.verfehlt++;
      return;
    }
    if (!target.id) target.id = 'complyo-main';
    var href = '#' + target.id;

    var a = document.createElement('a');
    a.setAttribute('href', href);
    a.setAttribute('data-complyo-skip-link', '1');
    a.className = 'complyo-skip-link';
    a.textContent = p.label || 'Zum Inhalt springen';
    if (document.body && document.body.firstChild) {
      document.body.insertBefore(a, document.body.firstChild);
      if (zaehltAngewendet('dokument_fixes', 'skip-link')) bilanz.dokument_fixes.angewendet++;
    } else if (document.body) {
      document.body.appendChild(a);
      if (zaehltAngewendet('dokument_fixes', 'skip-link')) bilanz.dokument_fixes.angewendet++;
    } else {
      if (zaehltVerfehlt('dokument_fixes', 'skip-link')) bilanz.dokument_fixes.verfehlt++;
    }
  }

  function applyLandmarkMain() {
    if (!fixPayload('landmark-main')) return;
    if (document.querySelector('main, [role="main"]')) {
      // Die Seite bringt ihren Hauptbereich selbst mit. Kein Fehlschlag,
      // sondern der Normalfall — deshalb "unnoetig" und nicht "verfehlt".
      // (Haben WIR das role="main" in einem frueheren Lauf gesetzt, greift
      // der angewendet-Vorrang und hier wird nichts umgezaehlt.)
      if (zaehltUnnoetig('dokument_fixes', 'landmark-main')) bilanz.dokument_fixes.unnoetig++;
      return;
    }
    var el = resolveMainTarget(null);
    if (el && !el.getAttribute('role')) {
      el.setAttribute('role', 'main');
      if (zaehltAngewendet('dokument_fixes', 'landmark-main')) bilanz.dokument_fixes.angewendet++;
    } else {
      // Kein Container gefunden, dem sich der Hauptbereich zuordnen liesse.
      if (zaehltVerfehlt('dokument_fixes', 'landmark-main')) bilanz.dokument_fixes.verfehlt++;
    }
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
      var kennung = 'struktur:' + i;   // eindeutige Fix-Kennung: je Fix, nicht je Element
      var ziele = findeStrukturZiele(f);
      if (ziele === null) {  // ungueltiger Selektor
        if (zaehltVerfehlt('struktur', kennung)) bilanz.struktur.verfehlt++;
        continue;
      }
      if (ziele === 'unnoetig') {
        // Seite hat bereits eine main-Landmark — hier gibt es nichts zu
        // reparieren; das ist kein Fehlschlag (vgl. Selbstdiagnose-Prinzip).
        if (zaehltUnnoetig('struktur', kennung)) bilanz.struktur.unnoetig++;
        continue;
      }
      // Kein Treffer (auch nicht über die stabilen Alternativen) heisst: das
      // Ziel gibt es auf dieser Seite nicht. Das ist die Regressionsmeldung,
      // auf die es ankommt — genau so sieht ein Theme-Update aus, das eine
      // Klasse umbenannt hat.
      if (!ziele.length) {
        if (zaehltVerfehlt('struktur', kennung)) bilanz.struktur.verfehlt++;
        continue;
      }
      for (var j = 0; j < ziele.length; j++) {
        var el = ziele[j];
        // Das viewport-Meta ist der einzige Fall, in dem ueberschrieben wird:
        // dort steht die Zoom-Sperre, die weg soll. Alles andere guarded.
        if (f.attribut === 'content' && el.tagName === 'META') {
          el.setAttribute('content', f.wert); gesetzt++;
          if (zaehltAngewendet('struktur', kennung)) bilanz.struktur.angewendet++;
        } else if (!el.getAttribute(f.attribut)) {
          el.setAttribute(f.attribut, f.wert); gesetzt++;
          if (zaehltAngewendet('struktur', kennung)) bilanz.struktur.angewendet++;
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
    }
    var style = document.createElement('style');
    style.id = 'complyo-a11y-style';
    style.appendChild(document.createTextNode(css));
    (document.head || document.documentElement).appendChild(style);
  }

  // Trifft jede CSS-Regel auf dieser Seite ueberhaupt etwas? Laeuft je
  // apply()-Lauf mit (nicht nur beim Injizieren des Styles), denn SPA-Inhalte
  // erscheinen oft erst nach der Hydration.
  function pruefeCssRegeln() {
    for (var i = 0; i < cssRules.length; i++) {
      var r = cssRules[i];
      if (!r || !r.selector || !r.declarations) continue;
      var kennung = 'css:' + i;
      var trifft = 0;
      try { trifft = document.querySelectorAll(r.selector).length; } catch (e) { trifft = -1; }
      if (trifft > 0) {
        if (zaehltAngewendet('css_regeln', kennung)) bilanz.css_regeln.angewendet++;
      } else {
        // trifft==0 ist KEIN Niemandsland: eine Kontrastregel ohne Ziel ist
        // entweder eine Unterseite ohne dieses Element — oder ein Selektor,
        // den ein Theme-Update zerlegt hat. Beides gehoert in `verfehlt`;
        // erst die Auswertung ueber viele Aufrufe trennt die Faelle. Frueher
        // zaehlte trifft==0 GAR NICHT — die Regression war unsichtbar.
        if (zaehltVerfehlt('css_regeln', kennung)) bilanz.css_regeln.verfehlt++;
      }
    }
  }

  // ---- Link-Zweck (WCAG 2.4.4): aria-label auf nichtssagende Links -----------
  function normText(s) { return (s || '').replace(/\s+/g, ' ').trim().toLowerCase(); }

  function hrefMatch(a, b) {
    if (!a || !b) return false;
    if (a === b) return true;
    // tolerant ggü. absolut/relativ: Endungs-Vergleich der Pfade.
    return a.indexOf(b) !== -1 || b.indexOf(a) !== -1;
  }

  function linkFixIndex(txt, href) {
    var nt = normText(txt);
    for (var i = 0; i < linkFixes.length; i++) {
      var f = linkFixes[i];
      if (normText(f.link_text) === nt && hrefMatch(href, f.link_href)) {
        return f.suggested_label ? i : -1;
      }
    }
    return -1;
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
      var idx = linkFixIndex(txt, a.getAttribute('href') || '');
      if (idx >= 0) {
        a.setAttribute('aria-label', linkFixes[idx].suggested_label);
        // je Fix einmal — sechs gleichlautende Icon-Links sind EIN Fix
        if (zaehltAngewendet('link_labels', 'link:' + idx)) bilanz.link_labels.angewendet++;
      }
    }
  }

  function apply() {
    if (!ready) return;
    // Bilanz je Lauf NEU berechnen — sonst zaehlt derselbe fehlende Selektor
    // bei jedem Timer- und Observer-Lauf erneut als verfehlt.
    beginneLauf();
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
    pruefeCssRegeln();
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

    // Kennt complyo diese site_id? Ein leeres Manifest bedeutet zweierlei —
    // "nichts zu tun" oder "falsche Kennung eingebaut". Auf loqal.io stand im
    // Skript-Tag eine Scan-Kennung statt der Site-ID; die Seite haette nie
    // eine Reparatur bekommen, und nichts haette darauf hingewiesen.
    //
    // Ein Hinweis in der Konsole, damit es beim Hinsehen auffaellt, und eine
    // Meldung an complyo, damit es auch ohne Hinsehen auffaellt.
    if (d.bekannt === false) {
      unbekannteKennung = true;
      try {
        console.warn('[complyo] Die eingebaute data-site-id "' + siteId +
          '" ist unbekannt. Es werden keine Reparaturen ausgeliefert. ' +
          'Bitte die Kennung aus dem complyo-Dashboard uebernehmen.');
      } catch (e) {}
    }
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
  //
  // Soll fuer dokument_fixes: nur die Arten, die dieses Widget selbst unter
  // `dokument_fixes` anwendet. Ein 'struktur'-Eintrag steckt zwar in docFixes,
  // wird aber ueber struktur_fixes bilanziert — er hier mitzuzaehlen wuerde
  // das Soll erneut verzerren.
  var DOKUMENT_FIX_ARTEN = { 'html-lang': 1, 'skip-link': 1, 'landmark-main': 1 };
  function dokumentFixSoll() {
    var n = 0;
    for (var i = 0; i < docFixes.length; i++) {
      if (docFixes[i] && DOKUMENT_FIX_ARTEN[docFixes[i].fix_type] === 1) n++;
    }
    return n;
  }

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
      dokument_fixes: bilanz.dokument_fixes,
      unbekannte_kennung: unbekannteKennung,
      erwartet: {
        alt_texte: Object.keys(map).length,
        link_labels: linkFixes.length,
        struktur: strukturFixes.length,
        css_regeln: cssRules.length,
        // dokument_fixes fehlte hier: Skip-Link & Co. standen in der Bilanz,
        // aber nicht im Soll — jede Quote angewendet/erwartet war damit
        // strukturell falsch. Widget und wirkung_routes decken jetzt
        // dieselben fuenf Arten ab.
        dokument_fixes: dokumentFixSoll()
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
