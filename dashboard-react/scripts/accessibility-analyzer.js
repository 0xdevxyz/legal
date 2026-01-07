#!/usr/bin/env node

/**
 * Accessibility Analyzer
 * 
 * Scannt alle .tsx Dateien im src/app Verzeichnis und prüft auf:
 * - Vorhandensein von <main> Elementen
 * - Vorhandensein von H1-Überschriften
 * - Verwendung von semantischen HTML-Elementen (header, nav, section, article, aside, footer)
 * - Generiert einen detaillierten Bericht mit Zeilennummern
 */

const fs = require('fs');
const path = require('path');

// Konfiguration
const SRC_DIR = path.join(__dirname, '..', 'src', 'app');
const OUTPUT_FILE = path.join(__dirname, '..', 'ACCESSIBILITY_REPORT.md');

// Farben für Console Output
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m',
};

// Statistiken
const stats = {
  totalFiles: 0,
  filesWithMain: 0,
  filesWithH1: 0,
  filesWithHeader: 0,
  filesWithNav: 0,
  filesWithSection: 0,
  filesWithArticle: 0,
  filesWithAside: 0,
  filesWithFooter: 0,
  issues: [],
};

/**
 * Findet alle .tsx Dateien rekursiv
 */
function findTsxFiles(dir, fileList = []) {
  const files = fs.readdirSync(dir);

  files.forEach(file => {
    const filePath = path.join(dir, file);
    const stat = fs.statSync(filePath);

    if (stat.isDirectory()) {
      // Ignoriere node_modules und .next
      if (!file.startsWith('.') && file !== 'node_modules') {
        findTsxFiles(filePath, fileList);
      }
    } else if (file.endsWith('.tsx')) {
      fileList.push(filePath);
    }
  });

  return fileList;
}

/**
 * Analysiert eine einzelne Datei
 */
function analyzeFile(filePath) {
  const content = fs.readFileSync(filePath, 'utf-8');
  const lines = content.split('\n');
  const relativePath = path.relative(path.join(__dirname, '..'), filePath);

  const analysis = {
    file: relativePath,
    hasMain: false,
    hasH1: false,
    hasHeader: false,
    hasNav: false,
    hasSection: false,
    hasArticle: false,
    hasAside: false,
    hasFooter: false,
    mainLine: null,
    h1Line: null,
    semanticElements: [],
    issues: [],
  };

  // Suche nach Elementen
  lines.forEach((line, index) => {
    const lineNum = index + 1;
    const trimmedLine = line.trim();

    // Main Element
    if (/<main[\s>]/.test(trimmedLine)) {
      analysis.hasMain = true;
      analysis.mainLine = lineNum;
      analysis.semanticElements.push({ element: 'main', line: lineNum });
    }

    // H1 Element
    if (/<h1[\s>]/.test(trimmedLine)) {
      analysis.hasH1 = true;
      analysis.h1Line = lineNum;
    }

    // Header Element
    if (/<header[\s>]/.test(trimmedLine)) {
      analysis.hasHeader = true;
      analysis.semanticElements.push({ element: 'header', line: lineNum });
    }

    // Nav Element
    if (/<nav[\s>]/.test(trimmedLine)) {
      analysis.hasNav = true;
      analysis.semanticElements.push({ element: 'nav', line: lineNum });
    }

    // Section Element
    if (/<section[\s>]/.test(trimmedLine)) {
      analysis.hasSection = true;
      analysis.semanticElements.push({ element: 'section', line: lineNum });
    }

    // Article Element
    if (/<article[\s>]/.test(trimmedLine)) {
      analysis.hasArticle = true;
      analysis.semanticElements.push({ element: 'article', line: lineNum });
    }

    // Aside Element
    if (/<aside[\s>]/.test(trimmedLine)) {
      analysis.hasAside = true;
      analysis.semanticElements.push({ element: 'aside', line: lineNum });
    }

    // Footer Element
    if (/<footer[\s>]/.test(trimmedLine)) {
      analysis.hasFooter = true;
      analysis.semanticElements.push({ element: 'footer', line: lineNum });
    }
  });

  // Erstelle Issues
  if (!analysis.hasMain) {
    analysis.issues.push({
      severity: 'error',
      message: 'Fehlendes <main> Element',
      suggestion: 'Fügen Sie ein <main> Element hinzu, um den Hauptinhalt der Seite zu kennzeichnen.',
    });
  }

  if (!analysis.hasH1) {
    analysis.issues.push({
      severity: 'error',
      message: 'Fehlende <h1> Überschrift',
      suggestion: 'Fügen Sie eine <h1> Überschrift hinzu, die das Hauptthema der Seite beschreibt.',
    });
  }

  if (!analysis.hasHeader && !analysis.hasNav && !analysis.hasSection) {
    analysis.issues.push({
      severity: 'warning',
      message: 'Keine semantischen Strukturelemente gefunden',
      suggestion: 'Verwenden Sie semantische HTML5-Elemente wie <header>, <nav>, <section>, <article> für bessere Barrierefreiheit.',
    });
  }

  return analysis;
}

/**
 * Generiert den Markdown-Report
 */
function generateReport(analyses) {
  let report = `# Barrierefreiheits-Analyse Report\n\n`;
  report += `**Generiert am:** ${new Date().toLocaleString('de-DE')}\n\n`;
  report += `---\n\n`;

  // Übersicht
  report += `## 📊 Übersicht\n\n`;
  report += `| Metrik | Wert |\n`;
  report += `|--------|------|\n`;
  report += `| Analysierte Dateien | ${stats.totalFiles} |\n`;
  report += `| Mit \`<main>\` Element | ${stats.filesWithMain} (${Math.round((stats.filesWithMain / stats.totalFiles) * 100)}%) |\n`;
  report += `| Mit \`<h1>\` Überschrift | ${stats.filesWithH1} (${Math.round((stats.filesWithH1 / stats.totalFiles) * 100)}%) |\n`;
  report += `| Mit \`<header>\` Element | ${stats.filesWithHeader} |\n`;
  report += `| Mit \`<nav>\` Element | ${stats.filesWithNav} |\n`;
  report += `| Mit \`<section>\` Element | ${stats.filesWithSection} |\n`;
  report += `| Mit \`<article>\` Element | ${stats.filesWithArticle} |\n`;
  report += `| Mit \`<aside>\` Element | ${stats.filesWithAside} |\n`;
  report += `| Mit \`<footer>\` Element | ${stats.filesWithFooter} |\n\n`;

  // Status Badge
  const mainCompliance = Math.round((stats.filesWithMain / stats.totalFiles) * 100);
  const h1Compliance = Math.round((stats.filesWithH1 / stats.totalFiles) * 100);
  const overallCompliance = Math.round((mainCompliance + h1Compliance) / 2);

  report += `### Compliance Status\n\n`;
  if (overallCompliance >= 90) {
    report += `✅ **Ausgezeichnet** - ${overallCompliance}% Compliance\n\n`;
  } else if (overallCompliance >= 70) {
    report += `⚠️ **Gut** - ${overallCompliance}% Compliance\n\n`;
  } else {
    report += `❌ **Verbesserungsbedarf** - ${overallCompliance}% Compliance\n\n`;
  }

  report += `---\n\n`;

  // Detaillierte Analyse pro Datei
  report += `## 📋 Detaillierte Analyse\n\n`;

  analyses.forEach(analysis => {
    const hasIssues = analysis.issues.length > 0;
    const icon = hasIssues ? '❌' : '✅';

    report += `### ${icon} \`${analysis.file}\`\n\n`;

    // Status
    if (!hasIssues) {
      report += `**Status:** ✅ Alle Barrierefreiheits-Checks bestanden\n\n`;
    } else {
      report += `**Status:** ⚠️ ${analysis.issues.length} Problem(e) gefunden\n\n`;
    }

    // Semantische Elemente
    if (analysis.semanticElements.length > 0) {
      report += `**Gefundene semantische Elemente:**\n\n`;
      analysis.semanticElements.forEach(({ element, line }) => {
        report += `- \`<${element}>\` in Zeile ${line}\n`;
      });
      report += `\n`;
    }

    // H1 Information
    if (analysis.hasH1) {
      report += `**H1-Überschrift:** ✅ Gefunden in Zeile ${analysis.h1Line}\n\n`;
    }

    // Issues
    if (analysis.issues.length > 0) {
      report += `**Probleme:**\n\n`;
      analysis.issues.forEach((issue, index) => {
        const severityIcon = issue.severity === 'error' ? '🔴' : '🟡';
        report += `${index + 1}. ${severityIcon} **${issue.message}**\n`;
        report += `   - ${issue.suggestion}\n\n`;
      });
    }

    report += `---\n\n`;
  });

  // Empfehlungen
  report += `## 💡 Empfehlungen\n\n`;
  report += `### Allgemeine Best Practices\n\n`;
  report += `1. **\`<main>\` Element:** Jede Seite sollte genau ein \`<main>\` Element haben, das den Hauptinhalt umschließt.\n\n`;
  report += `2. **H1-Überschrift:** Jede Seite sollte genau eine \`<h1>\` Überschrift haben, die das Hauptthema beschreibt.\n\n`;
  report += `3. **Semantische Struktur:**\n`;
  report += `   - \`<header>\`: Für Kopfbereiche mit Logo, Navigation\n`;
  report += `   - \`<nav>\`: Für Navigationsbereiche\n`;
  report += `   - \`<section>\`: Für thematische Gruppierungen\n`;
  report += `   - \`<article>\`: Für eigenständige, wiederverwendbare Inhalte\n`;
  report += `   - \`<aside>\`: Für ergänzende Inhalte (Sidebars)\n`;
  report += `   - \`<footer>\`: Für Fußbereiche\n\n`;
  report += `4. **ARIA-Attribute:** Verwenden Sie \`role\` und \`aria-label\` Attribute für zusätzliche Kontext-Informationen.\n\n`;

  // Code-Beispiel
  report += `### Beispiel-Struktur\n\n`;
  report += `\`\`\`tsx\n`;
  report += `export default function Page() {\n`;
  report += `  return (\n`;
  report += `    <main role="main" aria-label="Hauptinhalt">\n`;
  report += `      <header>\n`;
  report += `        <h1>Seitentitel</h1>\n`;
  report += `        <nav aria-label="Hauptnavigation">\n`;
  report += `          {/* Navigation Items */}\n`;
  report += `        </nav>\n`;
  report += `      </header>\n\n`;
  report += `      <section aria-label="Inhaltsbereich">\n`;
  report += `        <article>\n`;
  report += `          {/* Hauptinhalt */}\n`;
  report += `        </article>\n`;
  report += `      </section>\n\n`;
  report += `      <aside aria-label="Zusätzliche Informationen">\n`;
  report += `        {/* Sidebar */}\n`;
  report += `      </aside>\n\n`;
  report += `      <footer>\n`;
  report += `        {/* Footer Inhalt */}\n`;
  report += `      </footer>\n`;
  report += `    </main>\n`;
  report += `  );\n`;
  report += `}\n`;
  report += `\`\`\`\n\n`;

  report += `---\n\n`;
  report += `**Tool:** Accessibility Analyzer v1.0\n`;
  report += `**Projekt:** Complyo Dashboard\n`;

  return report;
}

/**
 * Hauptfunktion
 */
function main() {
  console.log(`${colors.bright}${colors.cyan}🔍 Barrierefreiheits-Analyse${colors.reset}\n`);
  console.log(`Durchsuche: ${SRC_DIR}\n`);

  // Finde alle .tsx Dateien
  const files = findTsxFiles(SRC_DIR);
  stats.totalFiles = files.length;

  console.log(`Gefunden: ${colors.bright}${files.length}${colors.reset} .tsx Dateien\n`);

  // Analysiere jede Datei
  const analyses = [];
  files.forEach(file => {
    const analysis = analyzeFile(file);
    analyses.push(analysis);

    // Update Statistiken
    if (analysis.hasMain) stats.filesWithMain++;
    if (analysis.hasH1) stats.filesWithH1++;
    if (analysis.hasHeader) stats.filesWithHeader++;
    if (analysis.hasNav) stats.filesWithNav++;
    if (analysis.hasSection) stats.filesWithSection++;
    if (analysis.hasArticle) stats.filesWithArticle++;
    if (analysis.hasAside) stats.filesWithAside++;
    if (analysis.hasFooter) stats.filesWithFooter++;

    // Console Output
    const relativePath = path.relative(path.join(__dirname, '..'), file);
    const hasIssues = analysis.issues.length > 0;
    const icon = hasIssues ? `${colors.red}❌${colors.reset}` : `${colors.green}✅${colors.reset}`;
    
    console.log(`${icon} ${relativePath}`);
    if (hasIssues) {
      analysis.issues.forEach(issue => {
        const severityColor = issue.severity === 'error' ? colors.red : colors.yellow;
        console.log(`   ${severityColor}└─ ${issue.message}${colors.reset}`);
      });
    }
  });

  console.log(`\n${colors.bright}${colors.cyan}📊 Statistiken${colors.reset}\n`);
  console.log(`<main> Elemente:     ${stats.filesWithMain}/${stats.totalFiles} (${Math.round((stats.filesWithMain / stats.totalFiles) * 100)}%)`);
  console.log(`<h1> Überschriften:  ${stats.filesWithH1}/${stats.totalFiles} (${Math.round((stats.filesWithH1 / stats.totalFiles) * 100)}%)`);
  console.log(`Semantische Elemente:`);
  console.log(`  - <header>:        ${stats.filesWithHeader}`);
  console.log(`  - <nav>:           ${stats.filesWithNav}`);
  console.log(`  - <section>:       ${stats.filesWithSection}`);
  console.log(`  - <article>:       ${stats.filesWithArticle}`);
  console.log(`  - <aside>:         ${stats.filesWithAside}`);
  console.log(`  - <footer>:        ${stats.filesWithFooter}`);

  // Generiere Report
  const report = generateReport(analyses);
  fs.writeFileSync(OUTPUT_FILE, report, 'utf-8');

  console.log(`\n${colors.green}✅ Report generiert: ${colors.bright}${path.relative(path.join(__dirname, '..'), OUTPUT_FILE)}${colors.reset}\n`);
}

// Starte Analyse
main();

