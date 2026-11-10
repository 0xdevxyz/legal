'use client';

import React from 'react';
import GesetzesbezugAbschnitt from './GesetzesbezugAbschnitt';
import NichtstunRechner from './NichtstunRechner';
import WegeVergleich from './WegeVergleich';
import PreisUndRisikoumkehr from './PreisUndRisikoumkehr';

/**
 * Der Teil der Ergebnisseite nach den Befunden: vom Befund zur Entscheidung.
 *
 * Reihenfolge (seit 10.11.2026):
 *   1. Befunde (WebsiteScanner, oberhalb)
 *   2. Gesetzesbezug je betroffenem Bereich, mit Fundstelle, ohne Prognose
 *   3. Rechner "Was kostet Selbermachen", mit den Zahlen des Besuchers
 *   4. Vier Wege im Vergleich, als Kategorien, mit "gewinnt, wenn"
 *   5. Preis und Risikoumkehr, samt dem, was wir nicht versprechen
 *
 * Der Druck auf dieser Seite kommt aus den gemessenen Befunden und aus dem
 * Gesetz, nicht aus erfundenen Zahlen, Zählern oder Fristen. Was hier
 * NICHT hingehört, weil es § 4a UWG oder Anhang Nr. 7 zu § 3 Abs. 3 UWG
 * berührt: Countdown, "nur noch X Plätze" ohne Datenbank dahinter (der
 * PlatzZaehler liest seine Zahl aus der DB), Bußgeldbeträge je Website,
 * "alternativlos" als Behauptung.
 */
export default function Entscheidung({ scanResult }: { scanResult: any }) {
  const befunde: number = scanResult?.befundeGesamt ?? 0;
  return (
    <>
      <GesetzesbezugAbschnitt pillars={scanResult?.pillars ?? {}} />
      {befunde > 0 && <NichtstunRechner />}
      <WegeVergleich />
      <PreisUndRisikoumkehr befunde={befunde} />
    </>
  );
}
