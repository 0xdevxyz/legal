/**
 * E2E-Re-Scan-Test (offline, ohne Browser)
 * ========================================
 * Belegt den Kern-Nachweis des Remediation-Plans:
 *   "Patch anwenden → re-scannen → Issue ist weg."
 *
 * Ablauf:
 *   1. BEFORE-Fixture mit echten WCAG-Verstößen (img ohne alt, <html> ohne lang,
 *      kein Skip-Link).
 *   2. Fix-Manifest (wie es das Backend liefert) → buildManifest().
 *   3. patchHtml() wendet die Fixes an (Channel #2 Quell-Patch).
 *   4. heuristicScan() zählt Verstöße VORHER und NACHHER — der "Re-Scan".
 *   5. Assertions: gezielte Issues sind nach dem Patch verschwunden.
 *
 * Bewusst kein Playwright/axe — diese Stufe verifiziert deterministisch, dass der
 * Patcher genau die Verstöße entfernt, die das Manifest adressiert.
 */
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { buildManifest, patchHtml } from '../complyo-a11y.mjs';

// --- Mini-"Scanner": zählt die Verstöße, die unsere Channels adressieren -------
function heuristicScan(html) {
  const issues = [];

  // 3.1.1 — <html> ohne lang
  const htmlTag = html.match(/<html\b([^>]*)>/i);
  if (htmlTag && !/\blang\s*=\s*["']?\s*\S/i.test(htmlTag[1])) {
    issues.push({ wcag: '3.1.1', msg: 'html ohne lang' });
  }

  // 1.1.1 — <img> ohne (nicht-leeres) alt
  const imgs = html.match(/<img\b[^>]*>/gi) || [];
  for (const tag of imgs) {
    const m = tag.match(/\salt\s*=\s*("([^"]*)"|'([^']*)'|[^\s>]+)/i);
    const val = m ? (m[2] ?? m[3] ?? m[1] ?? '') : null;
    if (!m || val.trim() === '') issues.push({ wcag: '1.1.1', msg: 'img ohne alt' });
  }

  // 2.4.1 — kein Skip-Link
  if (!/data-complyo-skip-link|class=["'][^"']*skip-link/i.test(html)) {
    issues.push({ wcag: '2.4.1', msg: 'kein Skip-Link' });
  }

  // 2.4.4 — nichtssagende Links ohne aria-label/title
  const VAGUE = /^(hier|mehr|weiterlesen|mehr erfahren|read more|details|weiter)$/i;
  const anchors = html.match(/<a\b[^>]*>[\s\S]*?<\/a>/gi) || [];
  for (const tag of anchors) {
    const attrs = tag.match(/<a\b([^>]*)>/i)?.[1] || '';
    if (/\saria-label\s*=/i.test(attrs) || /\stitle\s*=/i.test(attrs)) continue;
    const text = tag.replace(/<[^>]*>/g, '').replace(/\s+/g, ' ').trim();
    if (VAGUE.test(text)) issues.push({ wcag: '2.4.4', msg: `vager Link: ${text}` });
  }

  return issues;
}

const BEFORE = `<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>Beispielseite</title></head>
<body>
  <header><img src="/wp-content/uploads/logo-300x200.png"></header>
  <main>
    <h1>Willkommen</h1>
    <p><img src="/assets/team.jpg" alt=""></p>
    <p><img src="/img/dekor.svg" alt="Dekoratives Muster"></p>
    <p>Unsere Datenschutzrichtlinie: <a href="/datenschutz">mehr</a></p>
    <p>Bereits beschriftet: <a href="/agb" aria-label="Zu den AGB">hier</a></p>
  </main>
</body>
</html>`;

// So liefert das Backend (GET /api/accessibility/fix-manifest/{site_id}).
const MANIFEST = {
  success: true,
  alt_texts: [
    { image_filename: 'logo.png', image_src: '/wp-content/uploads/logo.png', suggested_alt: 'Firmenlogo Beispiel GmbH' },
    { image_filename: 'team.jpg', image_src: '/assets/team.jpg', suggested_alt: 'Team-Foto der Mitarbeitenden' },
  ],
  document_fixes: [
    { fix_type: 'html-lang', payload: { value: 'de' }, wcag_criterion: '3.1.1' },
    { fix_type: 'skip-link', payload: { target: '#main', label: 'Zum Inhalt springen' }, wcag_criterion: '2.4.1' },
  ],
  link_fixes: [
    { link_href: '/datenschutz', link_text: 'mehr', suggested_label: 'Mehr über Unsere Datenschutzrichtlinie' },
  ],
  css_rules: [
    { selector: ':focus', declarations: 'outline:2px solid #1a73e8' },
  ],
};

test('Re-Scan: Manifest-Patch entfernt die adressierten Verstöße', () => {
  const before = heuristicScan(BEFORE);

  // Vorher: lang fehlt, 2 Bilder ohne alt (logo + leeres team-alt), kein Skip-Link,
  // 1 vager Link ("mehr"; der "hier"-Link hat bereits aria-label → nicht gezählt).
  assert.ok(before.some(i => i.wcag === '3.1.1'), 'BEFORE: lang-Verstoß erwartet');
  assert.equal(before.filter(i => i.wcag === '1.1.1').length, 2, 'BEFORE: 2 alt-Verstöße erwartet');
  assert.ok(before.some(i => i.wcag === '2.4.1'), 'BEFORE: Skip-Link-Verstoß erwartet');
  assert.equal(before.filter(i => i.wcag === '2.4.4').length, 1, 'BEFORE: 1 vager Link erwartet');

  const manifest = buildManifest(MANIFEST);
  const { patched, stats } = patchHtml(BEFORE, manifest);
  const after = heuristicScan(patched);

  // Patcher-Statistik plausibel.
  assert.equal(stats.alt, 2, 'beide Alt-Texte gesetzt (logo + leeres team-alt gefüllt)');
  assert.equal(stats.lang, 1, 'lang gesetzt');
  assert.equal(stats.skip, 1, 'Skip-Link injiziert');
  assert.equal(stats.link, 1, 'aria-label auf vagem Link gesetzt');

  // Re-Scan: adressierte Verstöße sind weg.
  assert.equal(after.filter(i => i.wcag === '3.1.1').length, 0, 'AFTER: kein lang-Verstoß mehr');
  assert.equal(after.filter(i => i.wcag === '1.1.1').length, 0, 'AFTER: kein img-ohne-alt mehr');
  assert.equal(after.filter(i => i.wcag === '2.4.1').length, 0, 'AFTER: Skip-Link vorhanden');
  assert.equal(after.filter(i => i.wcag === '2.4.4').length, 0, 'AFTER: vager Link beschriftet');
  assert.equal(after.length, 0, 'AFTER: keine adressierten Verstöße mehr');
});

test('Guard: vorhandene Werte werden nie überschrieben', () => {
  const html = `<!DOCTYPE html><html lang="en"><head><title>x</title></head>
<body data-complyo-skip-link-present>
<a href="#main" data-complyo-skip-link="1">Zum Inhalt springen</a>
<main id="main">
<img src="/assets/team.jpg" alt="Bereits gesetzt">
<a href="/datenschutz" aria-label="Schon beschriftet">mehr</a>
</main>
</body></html>`;
  const manifest = buildManifest(MANIFEST);
  const { patched, stats } = patchHtml(html, manifest);

  assert.equal(stats.lang, 0, 'vorhandenes lang="en" nicht überschrieben');
  assert.equal(stats.skip, 0, 'vorhandener Skip-Link nicht dupliziert');
  assert.equal(stats.alt, 0, 'vorhandenes alt nicht überschrieben');
  assert.equal(stats.link, 0, 'vorhandenes aria-label auf Link nicht überschrieben');
  assert.ok(patched.includes('lang="en"'), 'lang="en" bleibt erhalten');
  assert.ok(patched.includes('alt="Bereits gesetzt"'), 'alt bleibt erhalten');
  assert.ok(patched.includes('aria-label="Schon beschriftet"'), 'Link-aria bleibt erhalten');
});

test('buildManifest ist rückwärtskompatibel (nacktes Alt-Text-Array)', () => {
  const m = buildManifest([{ image_filename: 'logo.png', suggested_alt: 'Logo' }]);
  assert.equal(m.altMap.get('logo.png'), 'Logo');
  assert.equal(m.lang, null);
  assert.equal(m.skipLink, null);
});
