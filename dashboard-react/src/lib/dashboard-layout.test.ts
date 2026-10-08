/**
 * Läuft ohne Testrahmen, mit Bordmitteln von Node:
 *     node --experimental-strip-types --test src/lib/dashboard-layout.test.ts
 * (npm run test:layout)
 */
import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  abgleichen,
  ausblenden,
  einblenden,
  istStandard,
  schritt,
  spalteWechseln,
  standardLayout,
  verschieben,
  type ModulVorgabe,
} from './dashboard-layout.ts';

const KATALOG: ModulVorgabe[] = [
  { id: 'hero', spalte: 'haupt' },
  { id: 'metriken', spalte: 'haupt' },
  { id: 'analyse', spalte: 'haupt' },
  { id: 'score', spalte: 'seite' },
  { id: 'ki', spalte: 'seite' },
];

test('Standardlayout folgt der Katalogreihenfolge je Spalte', () => {
  const l = standardLayout(KATALOG);
  assert.deepEqual(l.haupt, ['hero', 'metriken', 'analyse']);
  assert.deepEqual(l.seite, ['score', 'ki']);
  assert.deepEqual(l.ausgeblendet, []);
  assert.equal(istStandard(l, KATALOG), true);
});

test('Abgleich: Müll und falsche Version ergeben das Standardlayout', () => {
  assert.deepEqual(abgleichen(null, KATALOG), standardLayout(KATALOG));
  assert.deepEqual(abgleichen('kaputt', KATALOG), standardLayout(KATALOG));
  assert.deepEqual(abgleichen({ version: 99, haupt: ['hero'] }, KATALOG), standardLayout(KATALOG));
});

test('Abgleich: unbekannte Ids fliegen raus, neue Module landen am Ende ihrer Standardspalte', () => {
  const gespeichert = {
    version: 1,
    haupt: ['analyse', 'gibtsnicht', 'hero'],
    seite: ['ki'],
    ausgeblendet: ['metriken'],
  };
  const l = abgleichen(gespeichert, KATALOG);
  assert.deepEqual(l.haupt, ['analyse', 'hero']);
  // 'score' fehlte im gespeicherten Stand (z. B. nach einem Deploy): sichtbar, nicht verloren.
  assert.deepEqual(l.seite, ['ki', 'score']);
  assert.deepEqual(l.ausgeblendet, ['metriken']);
});

test('Abgleich: eine Id darf nur einmal vorkommen, das erste Vorkommen gewinnt', () => {
  const l = abgleichen(
    { version: 1, haupt: ['hero', 'hero'], seite: ['hero', 'score'], ausgeblendet: ['score'] },
    KATALOG,
  );
  assert.deepEqual(l.haupt, ['hero', 'metriken', 'analyse']);
  assert.deepEqual(l.seite, ['score', 'ki']);
  assert.deepEqual(l.ausgeblendet, []);
});

test('verschieben: innerhalb der Spalte und spaltenübergreifend, Index wird begrenzt', () => {
  const l = standardLayout(KATALOG);
  assert.deepEqual(verschieben(l, 'analyse', 'haupt', 0).haupt, ['analyse', 'hero', 'metriken']);
  const quer = verschieben(l, 'metriken', 'seite', 1);
  assert.deepEqual(quer.haupt, ['hero', 'analyse']);
  assert.deepEqual(quer.seite, ['score', 'metriken', 'ki']);
  assert.deepEqual(verschieben(l, 'hero', 'seite', 99).seite, ['score', 'ki', 'hero']);
  assert.equal(verschieben(l, 'unbekannt', 'seite', 0), l);
});

test('schritt: Ränder sind Grenzen, kein Umlauf', () => {
  const l = standardLayout(KATALOG);
  assert.equal(schritt(l, 'hero', 'auf'), l);
  assert.deepEqual(schritt(l, 'hero', 'ab').haupt, ['metriken', 'hero', 'analyse']);
  assert.equal(schritt(l, 'analyse', 'ab'), l);
});

test('spalteWechseln: landet in der anderen Spalte auf ähnlicher Höhe', () => {
  const l = standardLayout(KATALOG);
  const oben = spalteWechseln(l, 'hero');
  assert.deepEqual(oben.seite, ['hero', 'score', 'ki']);
  const unten = spalteWechseln(l, 'analyse');
  assert.deepEqual(unten.seite, ['score', 'ki', 'analyse']);
  assert.deepEqual(unten.haupt, ['hero', 'metriken']);
});

test('ausblenden und einblenden: zurück ans Ende der Standardspalte', () => {
  const l = standardLayout(KATALOG);
  const weg = ausblenden(l, 'score');
  assert.deepEqual(weg.seite, ['ki']);
  assert.deepEqual(weg.ausgeblendet, ['score']);
  assert.equal(istStandard(weg, KATALOG), false);
  const zurueck = einblenden(weg, 'score', KATALOG);
  assert.deepEqual(zurueck.seite, ['ki', 'score']);
  assert.deepEqual(zurueck.ausgeblendet, []);
  assert.equal(ausblenden(l, 'gibtsnicht'), l);
  assert.equal(einblenden(l, 'hero', KATALOG), l);
});
