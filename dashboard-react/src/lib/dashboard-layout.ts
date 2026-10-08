/**
 * Reine Layout-Logik für die anordenbare Dashboard-Startseite.
 *
 * Das Dashboard besteht aus zwei Spalten (Hauptspalte 2/3, Seitenspalte 1/3)
 * und einer Liste ausgeblendeter Module. Jede Funktion hier ist frei von React
 * und Browser-APIs, damit sie mit Bordmitteln testbar bleibt:
 *     node --experimental-strip-types --test src/lib/dashboard-layout.test.ts
 *
 * Der Katalog der Module (welche es gibt, in welcher Spalte sie standardmäßig
 * stehen) kommt von außen als `ModulVorgabe[]`. Die Reihenfolge der Vorgaben
 * ist die Standardreihenfolge je Spalte.
 */

export type Spalte = 'haupt' | 'seite';

export interface ModulVorgabe {
  id: string;
  spalte: Spalte;
}

export interface DashboardLayout {
  version: typeof LAYOUT_VERSION;
  haupt: string[];
  seite: string[];
  ausgeblendet: string[];
}

export const LAYOUT_VERSION = 1 as const;

export const SPALTEN: readonly Spalte[] = ['haupt', 'seite'] as const;

export function standardLayout(vorgaben: ModulVorgabe[]): DashboardLayout {
  return {
    version: LAYOUT_VERSION,
    haupt: vorgaben.filter((v) => v.spalte === 'haupt').map((v) => v.id),
    seite: vorgaben.filter((v) => v.spalte === 'seite').map((v) => v.id),
    ausgeblendet: [],
  };
}

function alsIdListe(wert: unknown): string[] {
  if (!Array.isArray(wert)) return [];
  return wert.filter((x): x is string => typeof x === 'string');
}

/**
 * Gleicht ein gespeichertes Layout (beliebiger Herkunft, z. B. localStorage)
 * mit dem aktuellen Modulkatalog ab:
 *  - unbekannte Ids fliegen raus (Modul wurde entfernt oder umbenannt),
 *  - doppelte Ids werden auf das erste Vorkommen reduziert,
 *  - Module, die im Katalog neu sind, landen in ihrer Standardspalte am Ende,
 *    damit ein neues Modul nach einem Deploy nicht unsichtbar bleibt.
 * Unbrauchbare Eingaben liefern das Standardlayout.
 */
export function abgleichen(gespeichert: unknown, vorgaben: ModulVorgabe[]): DashboardLayout {
  if (!gespeichert || typeof gespeichert !== 'object') return standardLayout(vorgaben);
  const roh = gespeichert as Record<string, unknown>;
  if (roh.version !== LAYOUT_VERSION) return standardLayout(vorgaben);

  const bekannt = new Set(vorgaben.map((v) => v.id));
  const gesehen = new Set<string>();
  const bereinigt = (liste: unknown): string[] =>
    alsIdListe(liste).filter((id) => {
      if (!bekannt.has(id) || gesehen.has(id)) return false;
      gesehen.add(id);
      return true;
    });

  const layout: DashboardLayout = {
    version: LAYOUT_VERSION,
    haupt: bereinigt(roh.haupt),
    seite: bereinigt(roh.seite),
    ausgeblendet: bereinigt(roh.ausgeblendet),
  };

  for (const vorgabe of vorgaben) {
    if (!gesehen.has(vorgabe.id)) layout[vorgabe.spalte].push(vorgabe.id);
  }
  return layout;
}

export function spalteVon(layout: DashboardLayout, id: string): Spalte | null {
  if (layout.haupt.includes(id)) return 'haupt';
  if (layout.seite.includes(id)) return 'seite';
  return null;
}

/**
 * Setzt ein Modul an eine Zielposition, auch spaltenübergreifend. `index`
 * bezieht sich auf die Zielspalte nach dem Entfernen des Moduls aus seiner
 * alten Position. Werte außerhalb werden auf das Ende begrenzt.
 */
export function verschieben(
  layout: DashboardLayout,
  id: string,
  ziel: Spalte,
  index: number,
): DashboardLayout {
  const quelle = spalteVon(layout, id);
  if (!quelle) return layout;

  const haupt = layout.haupt.filter((x) => x !== id);
  const seite = layout.seite.filter((x) => x !== id);
  const zielListe = ziel === 'haupt' ? haupt : seite;
  const pos = Math.max(0, Math.min(index, zielListe.length));
  zielListe.splice(pos, 0, id);

  return { ...layout, haupt, seite };
}

/** Ein Schritt nach oben oder unten innerhalb der eigenen Spalte. */
export function schritt(layout: DashboardLayout, id: string, richtung: 'auf' | 'ab'): DashboardLayout {
  const spalte = spalteVon(layout, id);
  if (!spalte) return layout;
  const liste = layout[spalte];
  const von = liste.indexOf(id);
  const nach = richtung === 'auf' ? von - 1 : von + 1;
  if (nach < 0 || nach >= liste.length) return layout;
  return verschieben(layout, id, spalte, nach);
}

/** Wechselt die Spalte und behält die relative Höhe ungefähr bei. */
export function spalteWechseln(layout: DashboardLayout, id: string): DashboardLayout {
  const spalte = spalteVon(layout, id);
  if (!spalte) return layout;
  const ziel: Spalte = spalte === 'haupt' ? 'seite' : 'haupt';
  const anteil = layout[spalte].indexOf(id) / Math.max(1, layout[spalte].length - 1);
  const index = Math.round(anteil * layout[ziel].length);
  return verschieben(layout, id, ziel, Number.isFinite(index) ? index : layout[ziel].length);
}

export function ausblenden(layout: DashboardLayout, id: string): DashboardLayout {
  if (!spalteVon(layout, id)) return layout;
  return {
    ...layout,
    haupt: layout.haupt.filter((x) => x !== id),
    seite: layout.seite.filter((x) => x !== id),
    ausgeblendet: [...layout.ausgeblendet, id],
  };
}

/** Holt ein ausgeblendetes Modul zurück, ans Ende seiner Standardspalte. */
export function einblenden(layout: DashboardLayout, id: string, vorgaben: ModulVorgabe[]): DashboardLayout {
  if (!layout.ausgeblendet.includes(id)) return layout;
  const vorgabe = vorgaben.find((v) => v.id === id);
  if (!vorgabe) return { ...layout, ausgeblendet: layout.ausgeblendet.filter((x) => x !== id) };
  return {
    ...layout,
    [vorgabe.spalte]: [...layout[vorgabe.spalte], id],
    ausgeblendet: layout.ausgeblendet.filter((x) => x !== id),
  };
}

export function istStandard(layout: DashboardLayout, vorgaben: ModulVorgabe[]): boolean {
  const standard = standardLayout(vorgaben);
  const gleich = (a: string[], b: string[]) => a.length === b.length && a.every((x, i) => x === b[i]);
  return (
    gleich(layout.haupt, standard.haupt) &&
    gleich(layout.seite, standard.seite) &&
    layout.ausgeblendet.length === 0
  );
}
