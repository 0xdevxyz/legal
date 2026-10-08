/**
 * Welcher Website gehoert ein Scan-Ergebnis?
 *
 * Das Dashboard haelt EIN Analyseergebnis (`analysisData` im Store) neben EINER
 * aktuellen Website (`currentWebsite`). Beides wurde bisher unabhaengig
 * voneinander geschrieben, und Leser setzten voraus, dass sie zusammenpassen.
 * Wechselt der Nutzer waehrend einer laufenden Analyse die Seite, tut es das
 * nicht mehr: Ueberschrift, Fortschrittsanzeige und die Issues, auf denen ein
 * KI-Fix oder ein PDF-Bericht aufsetzt, kommen dann von verschiedenen Seiten.
 *
 * Diese Funktionen sind rein (kein React, kein Store), damit sich die Regel
 * ohne Browser pruefen laesst:
 *     node --experimental-strip-types --test src/lib/scan-zuordnung.test.ts
 * (npm run test:zuordnung)
 */

/** Host ohne `www.` und Pfad ohne abschliessenden Schraegstrich. */
export interface Seitenschluessel {
  host: string;
  pfad: string;
}

/**
 * Reduziert eine Adresse auf die Seite, die sie meint. Akzeptiert auch eine
 * nackte Domain ("example.de"), wie sie das Eingabefeld liefert. Liefert null,
 * wenn nichts Auswertbares drinsteht.
 */
export function seitenSchluessel(url?: string | null): Seitenschluessel | null {
  if (typeof url !== 'string') return null;
  const roh = url.trim();
  if (!roh) return null;
  try {
    const u = new URL(/^[a-z][a-z0-9+.-]*:\/\//i.test(roh) ? roh : `https://${roh}`);
    const host = u.hostname.toLowerCase().replace(/^www\./, '');
    if (!host) return null;
    return { host, pfad: u.pathname.replace(/\/+$/, '').toLowerCase() };
  } catch {
    return null;
  }
}

/**
 * Meinen beide Adressen dieselbe Seite? Gleicher Host und gleicher Pfad; ein
 * leerer Pfad ist die ganze Domain und passt zu jedem Pfad auf ihr, weil das
 * Eingabefeld nur den Host weitergibt, getrackte Seiten aber auch mit Pfad
 * gespeichert sein koennen. Fehlt eine der Adressen, ist die Antwort nein.
 */
export function gleicheSeite(a?: string | null, b?: string | null): boolean {
  const ka = seitenSchluessel(a);
  const kb = seitenSchluessel(b);
  if (!ka || !kb) return false;
  if (ka.host !== kb.host) return false;
  return ka.pfad === kb.pfad || ka.pfad === '' || kb.pfad === '';
}

/** Alles, was wir von einem Ergebnis brauchen, um es einer Seite zuzuordnen. */
export interface Zuordenbar {
  url?: string | null;
}

/**
 * Darf dieses Ergebnis unter der Seite `seite` angezeigt werden?
 *
 * Ein Ergebnis ohne Adresse kann nicht widersprechen und wird durchgelassen
 * (aeltere gecachte Antworten), ebenso jedes, solange keine Seite gewaehlt ist.
 */
export function ergebnisPasstZurSeite(
  ergebnis: Zuordenbar | null | undefined,
  seite: string | null | undefined,
): boolean {
  if (!ergebnis) return false;
  if (!seitenSchluessel(seite)) return true;
  if (!seitenSchluessel(ergebnis.url)) return true;
  return gleicheSeite(ergebnis.url, seite);
}

/**
 * Das erste Ergebnis der Liste, das zur Seite passt. Die Reihenfolge ist die
 * Rangfolge der Quellen; ein Treffer der falschen Seite faellt durch, statt die
 * richtigen weiter hinten zu verdecken.
 */
export function ersteZurSeite<T extends Zuordenbar>(
  kandidaten: Array<T | null | undefined>,
  seite: string | null | undefined,
): T | null {
  for (const k of kandidaten) {
    if (k && ergebnisPasstZurSeite(k, seite)) return k;
  }
  return null;
}

/**
 * Darf ein fertiger Scan seiner Seite noch in den Vordergrund?
 *
 * `gescannt` ist die Seite, fuer die der Scan gestartet wurde, `aktuell` die,
 * die der Nutzer jetzt gewaehlt hat. Ist er weitergezogen, bleibt das Ergebnis
 * an seiner Seite (Zwischenspeicher, Verlauf) und ueberschreibt nicht die
 * Anzeige der neuen.
 */
export function darfScanUebernehmen(
  gescannt: string | null | undefined,
  aktuell: string | null | undefined,
): boolean {
  if (!seitenSchluessel(aktuell)) return true;
  return gleicheSeite(gescannt, aktuell);
}

/**
 * Wie `darfScanUebernehmen`, fuer die Startseite: dort wechselt die aktuelle
 * Seite durch den Scan selbst, von der Seite beim Start auf die gescannte. Das
 * ist gewollt. Nicht gewollt ist, dass ein Scan eine dritte Seite verdraengt, die
 * der Nutzer zwischendurch gewaehlt hat.
 */
export function darfStartseitenScanUebernehmen(
  beiStart: string | null | undefined,
  gescannt: string | null | undefined,
  aktuell: string | null | undefined,
): boolean {
  if (!seitenSchluessel(aktuell)) return true;
  return gleicheSeite(aktuell, gescannt) || gleicheSeite(aktuell, beiStart);
}
