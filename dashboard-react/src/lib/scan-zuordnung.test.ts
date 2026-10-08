/**
 * Laeuft ohne Testrahmen, mit Bordmitteln von Node:
 *     node --experimental-strip-types --test src/lib/scan-zuordnung.test.ts
 * (npm run test:zuordnung)
 */
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import {
  darfScanUebernehmen,
  darfStartseitenScanUebernehmen,
  ergebnisPasstZurSeite,
  ersteZurSeite,
  gleicheSeite,
  seitenSchluessel,
} from './scan-zuordnung.ts';

test('Schluessel: Schema, www, Gross-/Kleinschreibung und Schraegstrich fallen weg', () => {
  assert.deepEqual(seitenSchluessel('https://WWW.Beispiel.de/'), { host: 'beispiel.de', pfad: '' });
  assert.deepEqual(seitenSchluessel('beispiel.de'), { host: 'beispiel.de', pfad: '' });
  assert.deepEqual(seitenSchluessel('http://beispiel.de/shop/'), { host: 'beispiel.de', pfad: '/shop' });
});

test('Schluessel: Unbrauchbares ergibt null statt einer Ausnahme', () => {
  assert.equal(seitenSchluessel(''), null);
  assert.equal(seitenSchluessel('   '), null);
  assert.equal(seitenSchluessel(null), null);
  assert.equal(seitenSchluessel(undefined), null);
});

test('dieselbe Seite wird in jeder Schreibweise erkannt', () => {
  assert.ok(gleicheSeite('https://www.beispiel.de/', 'beispiel.de'));
  assert.ok(gleicheSeite('https://beispiel.de', 'http://WWW.BEISPIEL.DE/'));
});

test('zwei verschiedene Seiten sind nie dieselbe, auch nicht mit Namensanfang', () => {
  assert.equal(gleicheSeite('https://beispiel.de', 'https://anders.de'), false);
  assert.equal(gleicheSeite('https://beispiel.de', 'https://beispiel.de.evil.com'), false);
  assert.equal(gleicheSeite('https://shop.beispiel.de', 'https://beispiel.de'), false);
  // Der alte Vergleich im Dashboard war `url.includes(andere)`: damit galt
  // "a.de" als Teil von "banana.de". Das darf hier nicht wiederkehren.
  assert.equal(gleicheSeite('https://a.de', 'https://banana.de'), false);
});

test('Pfad: leere Wurzel passt zu allem auf der Domain, zwei Pfade nur bei Gleichheit', () => {
  assert.ok(gleicheSeite('https://beispiel.de', 'https://beispiel.de/shop'));
  assert.equal(gleicheSeite('https://beispiel.de/shop', 'https://beispiel.de/blog'), false);
});

test('fehlt eine Adresse, ist die Antwort nein', () => {
  assert.equal(gleicheSeite(null, 'https://beispiel.de'), false);
  assert.equal(gleicheSeite('https://beispiel.de', undefined), false);
});

// ---------------------------------------------------------------------------
// Der gemeldete Fehler: Seite A wird analysiert, der Nutzer wechselt auf B.
// ---------------------------------------------------------------------------

const ERGEBNIS_A = { url: 'https://seite-a.de', scan_id: 'scan_1_a' };
const ERGEBNIS_B = { url: 'https://seite-b.de', scan_id: 'scan_1_b' };

test('Ergebnis von A wird unter B nicht angezeigt', () => {
  assert.equal(ergebnisPasstZurSeite(ERGEBNIS_A, 'https://seite-b.de'), false);
  assert.equal(ergebnisPasstZurSeite(ERGEBNIS_A, 'https://seite-a.de'), true);
});

test('der Rueckfall auf einen Zwischenstand nimmt nur Ergebnisse der gewaehlten Seite', () => {
  // Reihenfolge wie im Dashboard: zuletzt gespeicherter Scan, frisch geholt, Store.
  // Der zuletzt gespeicherte Scan gehoert A. Gewaehlt ist B, B hat nichts Frisches,
  // im Store liegt aber der Stand von B.
  assert.equal(ersteZurSeite([ERGEBNIS_A, undefined, ERGEBNIS_B], 'https://seite-b.de'), ERGEBNIS_B);
});

test('liegt nur das Ergebnis der anderen Seite vor, wird nichts angezeigt statt des falschen', () => {
  assert.equal(ersteZurSeite([ERGEBNIS_A, null, undefined], 'https://seite-b.de'), null);
});

test('ohne gewaehlte Seite bleibt das Verhalten wie zuvor', () => {
  assert.equal(ersteZurSeite([ERGEBNIS_A], null), ERGEBNIS_A);
  assert.equal(ergebnisPasstZurSeite({ url: undefined }, 'https://seite-b.de'), true);
});

test('Rescan von A ist fertig, der Nutzer steht inzwischen auf B: nicht uebernehmen', () => {
  assert.equal(darfScanUebernehmen('https://seite-a.de', 'https://seite-b.de'), false);
});

test('Rescan fertig und der Nutzer ist auf der Seite geblieben: uebernehmen', () => {
  assert.equal(darfScanUebernehmen('https://seite-a.de', 'https://www.seite-a.de/'), true);
});

test('Startseite: der Scan selbst darf die aktuelle Seite von der alten auf die gescannte setzen', () => {
  // Beim Start war X gewaehlt, gescannt wurde A, am Ende steht noch X da.
  assert.equal(
    darfStartseitenScanUebernehmen('https://x.de', 'seite-a.de', 'https://x.de'),
    true,
  );
});

test('Startseite: eine zwischendurch gewaehlte dritte Seite wird nicht verdraengt', () => {
  assert.equal(
    darfStartseitenScanUebernehmen('https://x.de', 'seite-a.de', 'https://seite-b.de'),
    false,
  );
});

test('Startseite: ohne aktuelle Seite (erster Scan) wird uebernommen', () => {
  assert.equal(darfStartseitenScanUebernehmen(null, 'seite-a.de', null), true);
});

// ---------------------------------------------------------------------------
// Nahtstellen: die Regel nuetzt nichts, wenn die Stellen sie nicht benutzen.
// Wie bei test_fortschritt_kennung.py im Backend: geprueft wird die Verdrahtung,
// nicht die beiden Seiten einzeln.
// ---------------------------------------------------------------------------

const quelle = (pfad: string) => readFileSync(new URL(pfad, import.meta.url), 'utf8');

/** Rumpf einer Aktion im Store, von ihrem Kopf bis zur naechsten Aktion. */
function aktion(src: string, kopf: string): string {
  const start = src.indexOf(kopf);
  assert.ok(start >= 0, `${kopf} nicht gefunden`);
  const rest = src.slice(start + kopf.length);
  const ende = rest.search(/\n    [a-zA-Z]+: \(/);
  return src.slice(start, start + kopf.length + (ende < 0 ? rest.length : ende));
}

test('Store: Ergebnis wird nur abgelegt, wenn es zur gewaehlten Seite passt', () => {
  const s = quelle('../stores/dashboard.ts');
  assert.match(aktion(s, 'setAnalysisData: (data) =>'), /ergebnisPasstZurSeite\(/);
});

test('Store: Seitenwechsel raeumt das Ergebnis der alten Seite ab', () => {
  const s = quelle('../stores/dashboard.ts');
  const rumpf = aktion(s, 'setCurrentWebsite: (website) =>');
  assert.match(rumpf, /ergebnisPasstZurSeite\(/);
  assert.match(rumpf, /analysisData:\s*null/);
});

test('Analyse: jede Quelle laeuft durch die Seitenpruefung', () => {
  const s = quelle('../components/dashboard/WebsiteAnalysis.tsx');
  assert.match(s, /ersteZurSeite\(\[latestScanData, fetchedAnalysisData, storedAnalysisData\]/);
  assert.match(s, /ersteZurSeite\(\[fetchedAnalysisData, storedAnalysisData\]/);
  // Der alte Vergleich per Teilstring, der "a.de" in "banana.de" fand, kehrt nicht zurueck.
  assert.doesNotMatch(s, /latestScanData \|\| fetchedAnalysisData \|\| storedAnalysisData/);
});

test('Rescan: Ergebnis kommt aus dem Zwischenspeicher der gescannten Seite, nicht aus refetch()', () => {
  const s = quelle('../components/dashboard/WebsiteAnalysis.tsx');
  const start = s.indexOf('const handleRescan = async () =>');
  const rumpf = s.slice(start, s.indexOf('const handleAIFix', start));
  // refetch() liefert den Stand der Abfrage, die der Hook JETZT beobachtet,
  // also nach einem Seitenwechsel die der neuen Seite.
  assert.doesNotMatch(rumpf, /=\s*await refetch\(\)/);
  assert.match(rumpf, /getQueryState/);
  assert.match(rumpf, /darfScanUebernehmen\(/);
  // Die Seite wird beim Start festgehalten und nie aus dem Closure nachgelesen.
  assert.match(rumpf, /const gescannteUrl = currentWebsite\.url/);
});

test('Fortschrittspanel: gehoert zur Seite, fuer die der Lauf gestartet wurde', () => {
  const s = quelle('../components/dashboard/WebsiteAnalysis.tsx');
  assert.match(s, /<ScanProgressPanel url=\{scanLauf!\.url\}/);
  assert.doesNotMatch(s, /<ScanProgressPanel url=\{currentWebsite\.url\}/);
});

test('Startseite: ein Scan verdraengt keine zwischendurch gewaehlte Seite', () => {
  const s = quelle('../components/dashboard/DomainHeroSection.tsx');
  assert.match(s, /darfStartseitenScanUebernehmen\(/);
});

test('Hook: die Kennung kommt mit der Seite, fuer die der Abruf lief', () => {
  const s = quelle('../hooks/useCompliance.ts');
  assert.match(s, /onKennung\(kennung, trimmedUrl\)/);
});
