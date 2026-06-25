#!/usr/bin/env node
/**
 * Complyo Accessibility – HTML Build-/Source-Patcher (Channel #2)
 * ===============================================================
 * Holt freigegebene KI-Alt-Texte vom Complyo-Backend und schreibt sie in
 * statische .html-Dateien AN DER QUELLE: bei jedem <img> ohne (nicht-leeres)
 * alt wird der passende Alt-Text per Dateinamen-Matching eingefügt.
 *
 * Echte Remediation (eingecheckt im Quellcode), kein Runtime-Overlay.
 *
 * Nutzung:
 *   node complyo-a11y.mjs --site-id <id> --dir <pfad> [--api <url>] [--dry-run] [--ext html,htm]
 *
 * Beispiel:
 *   node complyo-a11y.mjs --site-id zua-zwickau-de --dir ./public --dry-run
 *
 * Quelle der Fixes (kanonisch, nur Status "approved"):
 *   GET {api}/api/accessibility/alt-text-fixes?site_id=…&approved_only=true
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

  --site-id <id>   Complyo Site-ID (Pflicht)
  --dir <pfad>     Zu patchendes Verzeichnis (Pflicht, rekursiv)
  --api <url>      Backend-Basis-URL (Default: ${DEFAULT_API})
  --manifest <f>   Fixes aus lokaler JSON-Datei laden statt vom Backend (offline/CI/Test)
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

function fixesToMap(fixes) {
  const map = new Map();
  for (const fix of (Array.isArray(fixes) ? fixes : [])) {
    const alt = (fix.suggested_alt || fix.alt_text || fix.generated_alt || '').trim();
    if (!alt) continue;
    for (const cand of [fix.image_filename, fix.image_src]) {
      const key = normalizeFilename(cand);
      if (key) map.set(key, alt);
    }
  }
  return map;
}

async function loadManifestFile(file) {
  const raw = await fs.readFile(file, 'utf8');
  const body = JSON.parse(raw);
  // Akzeptiere {fixes:[…]} ODER ein nacktes Array.
  return fixesToMap(Array.isArray(body) ? body : body?.fixes);
}

async function fetchManifest(api, siteId) {
  const url = `${api.replace(/\/+$/, '')}/api/accessibility/alt-text-fixes?site_id=${encodeURIComponent(siteId)}&approved_only=true`;
  const res = await fetch(url, { headers: { 'accept': 'application/json' } });
  if (!res.ok) throw new Error(`Manifest-Abruf fehlgeschlagen: HTTP ${res.status}`);
  const body = await res.json();
  return fixesToMap(body?.fixes);
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

// Pro <img>-Tag: hat es ein nicht-leeres alt? Wenn nein und src matcht → alt einfügen.
function patchHtml(html, map) {
  let injected = 0;
  const patched = html.replace(/<img\b[^>]*>/gi, (tag) => {
    const altMatch = tag.match(/\salt\s*=\s*("([^"]*)"|'([^']*)'|[^\s>]+)/i);
    const altVal = altMatch ? (altMatch[2] ?? altMatch[3] ?? altMatch[1] ?? '') : null;
    if (altMatch && altVal.trim() !== '') return tag; // vorhandenes alt nicht anfassen

    const srcMatch = tag.match(/\s(?:data-)?src\s*=\s*("([^"]*)"|'([^']*)'|[^\s>]+)/i);
    const src = srcMatch ? (srcMatch[2] ?? srcMatch[3] ?? srcMatch[1] ?? '') : '';
    const key = normalizeFilename(src);
    if (!key || !map.has(key)) return tag;

    const alt = escapeAttr(map.get(key));
    injected++;
    if (altMatch) {
      // leeres alt="" durch echten Text ersetzen
      return tag.replace(altMatch[0], ` alt="${alt}"`);
    }
    // kein alt vorhanden → direkt nach <img einfügen
    return tag.replace(/^<img\b/i, `<img alt="${alt}"`);
  });
  return { patched, injected };
}

async function main() {
  const args = parseArgs(process.argv);
  if (args.help || !args.dir || (!args.siteId && !args.manifest)) {
    usage();
    process.exit(args.help ? 0 : 1);
  }

  let map;
  if (args.manifest) {
    console.log(`[complyo-a11y] Lade Fixes aus lokaler Datei ${args.manifest} …`);
    map = await loadManifestFile(args.manifest);
  } else {
    console.log(`[complyo-a11y] Lade freigegebene Alt-Texte für site-id=${args.siteId} …`);
    map = await fetchManifest(args.api, args.siteId);
  }
  console.log(`[complyo-a11y] ${map.size} eindeutige Dateinamen im Manifest.`);
  if (map.size === 0) {
    console.log('[complyo-a11y] Nichts anzuwenden (keine freigegebenen Alt-Texte). Ende.');
    return;
  }

  const files = await walk(path.resolve(args.dir), args.ext);
  console.log(`[complyo-a11y] ${files.length} HTML-Dateien gefunden.`);

  let totalInjected = 0, filesChanged = 0;
  for (const file of files) {
    const html = await fs.readFile(file, 'utf8');
    const { patched, injected } = patchHtml(html, map);
    if (injected > 0) {
      totalInjected += injected;
      filesChanged++;
      console.log(`  ${args.dryRun ? '[dry-run] ' : ''}${file}: ${injected} Alt-Text(e)`);
      if (!args.dryRun) await fs.writeFile(file, patched, 'utf8');
    }
  }

  console.log(`\n[complyo-a11y] Fertig: ${totalInjected} Alt-Texte in ${filesChanged} Datei(en)${args.dryRun ? ' (dry-run, nichts geschrieben)' : ' geschrieben'}.`);
}

main().catch((err) => {
  console.error('[complyo-a11y] Fehler:', err.message);
  process.exit(1);
});
