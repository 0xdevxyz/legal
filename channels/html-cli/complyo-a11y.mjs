#!/usr/bin/env node
/**
 * Complyo Accessibility – HTML Build-/Source-Patcher (Channel #2)
 * ===============================================================
 * Konsumiert das vereinheitlichte FIX-MANIFEST vom Complyo-Backend und schreibt
 * die freigegebenen Fixes in statische .html-Dateien AN DER QUELLE:
 *   - alt_texts:  <img> ohne (nicht-leeres) alt → passender Alt-Text (Dateiname-Match)
 *   - html-lang:  <html> ohne lang → lang="…"                         (WCAG 3.1.1)
 *   - skip-link:  "Zum Inhalt springen" direkt nach <body>            (WCAG 2.4.1)
 *   - css-rule:   z.B. sichtbarer Fokus-Indikator via <style>         (WCAG 2.4.7)
 *
 * Echte Remediation (eingecheckt im Quellcode), kein Runtime-Overlay. Alle Fixes
 * sind guarded: Vorhandenes (alt, lang, Skip-Link) wird nie überschrieben.
 *
 * Nutzung:
 *   node complyo-a11y.mjs --site-id <id> --dir <pfad> [--api <url>] [--dry-run] [--ext html,htm]
 *   node complyo-a11y.mjs --manifest ./manifest.json --dir ./public --dry-run   (offline/CI)
 *
 * Quelle der Fixes (kanonisch, nur Status "approved"):
 *   GET {api}/api/accessibility/fix-manifest/{site_id}
 */

import fs from 'node:fs/promises';
import path from 'node:path';

const DEFAULT_API = 'https://api.complyo.de';

function parseArgs(argv) {
  const args = { api: DEFAULT_API, dryRun: false, ext: ['html', 'htm'] };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--dry-run') args.dryRun = true;
    else if (a === '--site-id') args.siteId = argv[++i];
    else if (a === '--dir') args.dir = argv[++i];
    else if (a === '--api') args.api = argv[++i];
    else if (a === '--manifest') args.manifest = argv[++i];
    else if (a === '--ext') args.ext = String(argv[++i]).split(',').map(s => s.trim().toLowerCase()).filter(Boolean);
    else if (a === '-h' || a === '--help') args.help = true;
  }
  return args;
}

function usage() {
  console.log(`Complyo Accessibility – HTML Source-Patcher

  --site-id <id>   Complyo Site-ID (Pflicht, außer --manifest)
  --dir <pfad>     Zu patchendes Verzeichnis (Pflicht, rekursiv)
  --api <url>      Backend-Basis-URL (Default: ${DEFAULT_API})
  --manifest <f>   Manifest aus lokaler JSON-Datei laden statt vom Backend (offline/CI/Test)
  --ext <liste>    Dateiendungen (Default: html,htm)
  --dry-run        Nichts schreiben, nur anzeigen was passieren würde
  -h, --help       Diese Hilfe`);
}

// Basis-Dateiname (klein) inkl. Entfernung der WP-Größensuffixe (-300x200).
function normalizeFilename(p) {
  if (!p || typeof p !== 'string') return '';
  let base = p.split(/[?#]/)[0];                  // Query/Fragment weg
  base = base.split('/').pop() || '';             // basename
  base = base.toLowerCase();
  base = base.replace(/-\d+x\d+(\.[a-z0-9]+)$/i, '$1'); // Größensuffix weg
  return base;
}

function escapeAttr(s) {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/"/g, '&quot;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

function escapeText(s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

// Normalisiert ein Manifest (Backend-Antwort ODER lokale Datei) auf eine
// einheitliche Struktur: { altMap, lang, skipLink, cssRules }.
function buildManifest(body) {
  // Rückwärtskompatibel: nacktes Array oder {fixes:[…]} == nur Alt-Texte.
  const altSource = Array.isArray(body)
    ? body
    : (body?.alt_texts || body?.fixes || []);

  const altMap = new Map();
  for (const fix of altSource) {
    const alt = (fix.suggested_alt || fix.alt_text || fix.generated_alt || fix.alt || '').trim();
    if (!alt) continue;
    for (const cand of [fix.image_filename, fix.image_src]) {
      const key = normalizeFilename(cand);
      if (key) altMap.set(key, alt);
    }
  }

  const docFixes = Array.isArray(body) ? [] : (body?.document_fixes || []);
  const pick = (type) => docFixes.find(f => f && f.fix_type === type)?.payload || null;

  const langPayload = pick('html-lang');
  const skipPayload = pick('skip-link');
  const cssRules = Array.isArray(body) ? [] : (body?.css_rules || []);

  return {
    altMap,
    lang: langPayload?.value || null,
    skipLink: skipPayload ? {
      label: skipPayload.label || 'Zum Inhalt springen',
      target: skipPayload.target || '#main',
    } : null,
    cssRules: Array.isArray(cssRules) ? cssRules : [],
  };
}

async function loadManifestFile(file) {
  return buildManifest(JSON.parse(await fs.readFile(file, 'utf8')));
}

async function fetchManifest(api, siteId) {
  const url = `${api.replace(/\/+$/, '')}/api/accessibility/fix-manifest/${encodeURIComponent(siteId)}`;
  const res = await fetch(url, { headers: { accept: 'application/json' } });
  if (!res.ok) throw new Error(`Manifest-Abruf fehlgeschlagen: HTTP ${res.status}`);
  return buildManifest(await res.json());
}

async function walk(dir, exts, out = []) {
  const entries = await fs.readdir(dir, { withFileTypes: true });
  for (const e of entries) {
    const full = path.join(dir, e.name);
    if (e.isDirectory()) {
      if (e.name === 'node_modules' || e.name === '.git') continue;
      await walk(full, exts, out);
    } else if (exts.includes(path.extname(e.name).slice(1).toLowerCase())) {
      out.push(full);
    }
  }
  return out;
}

// --- Einzel-Transformationen (alle guarded) ---------------------------------

function patchAltTexts(html, altMap, stats) {
  return html.replace(/<img\b[^>]*>/gi, (tag) => {
    const altMatch = tag.match(/\salt\s*=\s*("([^"]*)"|'([^']*)'|[^\s>]+)/i);
    const altVal = altMatch ? (altMatch[2] ?? altMatch[3] ?? altMatch[1] ?? '') : null;
    if (altMatch && altVal.trim() !== '') return tag; // vorhandenes alt nicht anfassen

    const srcMatch = tag.match(/\s(?:data-)?src\s*=\s*("([^"]*)"|'([^']*)'|[^\s>]+)/i);
    const src = srcMatch ? (srcMatch[2] ?? srcMatch[3] ?? srcMatch[1] ?? '') : '';
    const key = normalizeFilename(src);
    if (!key || !altMap.has(key)) return tag;

    const alt = escapeAttr(altMap.get(key));
    stats.alt++;
    if (altMatch) return tag.replace(altMatch[0], ` alt="${alt}"`); // leeres alt füllen
    return tag.replace(/^<img\b/i, `<img alt="${alt}"`);
  });
}

function patchHtmlLang(html, lang, stats) {
  if (!lang) return html;
  return html.replace(/<html\b([^>]*)>/i, (tag, attrs) => {
    if (/\blang\s*=/i.test(attrs)) return tag; // vorhandenes lang nie überschreiben
    stats.lang++;
    return `<html${attrs} lang="${escapeAttr(lang)}">`;
  });
}

// Skip-Link nach <body> einfügen; Ziel-Element bekommt nötigenfalls eine id.
function patchSkipLink(html, skip, stats) {
  if (!skip) return html;
  if (/data-complyo-skip-link/i.test(html)) return html; // schon vorhanden
  if (!/<body\b[^>]*>/i.test(html)) return html;         // ohne <body> kein Anker

  let targetId = null;
  // 1) bevorzugtes Ziel "#foo" → existiert ein Element mit dieser id?
  const wanted = (skip.target || '').replace(/^#/, '');
  if (wanted && new RegExp(`id\\s*=\\s*["']${wanted}["']`, 'i').test(html)) {
    targetId = wanted;
  }
  // 2) sonst <main> verankern (id ergänzen, falls nötig)
  if (!targetId) {
    const mainMatch = html.match(/<main\b([^>]*)>/i);
    if (mainMatch) {
      const idMatch = mainMatch[1].match(/id\s*=\s*("([^"]*)"|'([^']*)')/i);
      if (idMatch) {
        targetId = idMatch[2] ?? idMatch[3];
      } else {
        targetId = 'complyo-main';
        html = html.replace(mainMatch[0], `<main${mainMatch[1]} id="complyo-main">`);
      }
    }
  }
  if (!targetId) return html; // kein auflösbares Ziel → keinen Dangling-Link setzen

  const link = `<a href="#${targetId}" class="complyo-skip-link" data-complyo-skip-link="1">${escapeText(skip.label)}</a>`;
  stats.skip++;
  return html.replace(/(<body\b[^>]*>)/i, `$1\n${link}`);
}

function patchStyle(html, skip, cssRules, stats) {
  const hasSkip = stats.skip > 0 || /data-complyo-skip-link/i.test(html);
  const rules = (cssRules || []).filter(r => r && r.selector && r.declarations);
  if (!hasSkip && rules.length === 0) return html;
  if (/id=["']complyo-a11y-style["']/i.test(html)) return html;

  let css = '';
  if (hasSkip) {
    css += '.complyo-skip-link{position:absolute;left:-9999px;top:0;z-index:100000;'
      + 'background:#1a73e8;color:#fff;padding:8px 16px;border-radius:0 0 4px 0;'
      + 'text-decoration:none;font:14px/1.4 sans-serif;}'
      + '.complyo-skip-link:focus{left:0;}';
  }
  for (const r of rules) css += `${r.selector}{${r.declarations}}`;

  const style = `<style id="complyo-a11y-style">${css}</style>`;
  stats.style++;
  if (/<\/head>/i.test(html)) return html.replace(/<\/head>/i, `${style}\n</head>`);
  if (/<body\b[^>]*>/i.test(html)) return html.replace(/(<body\b[^>]*>)/i, `${style}\n$1`);
  return style + html;
}

function patchHtml(html, manifest) {
  const stats = { alt: 0, lang: 0, skip: 0, style: 0 };
  html = patchAltTexts(html, manifest.altMap, stats);
  html = patchHtmlLang(html, manifest.lang, stats);
  html = patchSkipLink(html, manifest.skipLink, stats);
  html = patchStyle(html, manifest.skipLink, manifest.cssRules, stats);
  const total = stats.alt + stats.lang + stats.skip + stats.style;
  return { patched: html, stats, total };
}

async function main() {
  const args = parseArgs(process.argv);
  if (args.help || !args.dir || (!args.siteId && !args.manifest)) {
    usage();
    process.exit(args.help ? 0 : 1);
  }

  let manifest;
  if (args.manifest) {
    console.log(`[complyo-a11y] Lade Manifest aus lokaler Datei ${args.manifest} …`);
    manifest = await loadManifestFile(args.manifest);
  } else {
    console.log(`[complyo-a11y] Lade Fix-Manifest für site-id=${args.siteId} …`);
    manifest = await fetchManifest(args.api, args.siteId);
  }

  const docCount = (manifest.lang ? 1 : 0) + (manifest.skipLink ? 1 : 0) + manifest.cssRules.length;
  console.log(`[complyo-a11y] Manifest: ${manifest.altMap.size} Alt-Texte, ${docCount} dokumentweite Fixes.`);
  if (manifest.altMap.size === 0 && docCount === 0) {
    console.log('[complyo-a11y] Nichts anzuwenden (Manifest leer). Ende.');
    return;
  }

  const files = await walk(path.resolve(args.dir), args.ext);
  console.log(`[complyo-a11y] ${files.length} HTML-Dateien gefunden.`);

  const totals = { alt: 0, lang: 0, skip: 0, style: 0 };
  let filesChanged = 0;
  for (const file of files) {
    const html = await fs.readFile(file, 'utf8');
    const { patched, stats, total } = patchHtml(html, manifest);
    if (total > 0) {
      totals.alt += stats.alt; totals.lang += stats.lang;
      totals.skip += stats.skip; totals.style += stats.style;
      filesChanged++;
      console.log(`  ${args.dryRun ? '[dry-run] ' : ''}${file}: `
        + `${stats.alt} alt, ${stats.lang} lang, ${stats.skip} skip-link, ${stats.style} style`);
      if (!args.dryRun) await fs.writeFile(file, patched, 'utf8');
    }
  }

  console.log(`\n[complyo-a11y] Fertig: ${totals.alt} Alt-Texte, ${totals.lang} lang, `
    + `${totals.skip} Skip-Links, ${totals.style} Style-Blöcke in ${filesChanged} Datei(en)`
    + `${args.dryRun ? ' (dry-run, nichts geschrieben)' : ' geschrieben'}.`);
}

// Export für Tests (E2E-Re-Scan): reine Funktionen ohne Seiteneffekte.
export { buildManifest, patchHtml, normalizeFilename };

// Nur ausführen, wenn direkt gestartet (nicht beim Import im Test).
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => {
    console.error('[complyo-a11y] Fehler:', err.message);
    process.exit(1);
  });
}
