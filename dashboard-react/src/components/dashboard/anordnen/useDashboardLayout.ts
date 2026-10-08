'use client';

/**
 * Hält das Dashboard-Layout eines Nutzers und schreibt jede Änderung sofort
 * in den Browser (localStorage, je Nutzer-Id). Es gibt kein Backend-Feld für
 * Nutzereinstellungen; wenn eines kommt, ist dieser Hook die einzige Stelle,
 * die es anbinden muss.
 */

import { useCallback, useEffect, useMemo, useState } from 'react';
import { safeStorage } from '@/lib/storage';
import {
  abgleichen,
  ausblenden as ausblendenRein,
  einblenden as einblendenRein,
  istStandard,
  schritt as schrittRein,
  spalteWechseln as spalteWechselnRein,
  standardLayout,
  verschieben as verschiebenRein,
  type DashboardLayout,
  type ModulVorgabe,
  type Spalte,
} from '@/lib/dashboard-layout';
import { MODULKATALOG } from './modulkatalog';

const VORGABEN: ModulVorgabe[] = MODULKATALOG.map((m) => ({ id: m.id, spalte: m.spalte }));

export function layoutSchluessel(userId: number | string | null | undefined): string {
  return `complyo_dashboard_layout_v1_${userId ?? 'anonym'}`;
}

export function useDashboardLayout(userId: number | string | null | undefined) {
  const schluessel = layoutSchluessel(userId);

  // Erst der Standard (identisch auf Server und Client, kein Hydration-Sprung),
  // nach dem Mount der gespeicherte Stand.
  const [layout, setLayout] = useState<DashboardLayout>(() => standardLayout(VORGABEN));
  const [geladen, setGeladen] = useState(false);

  useEffect(() => {
    setLayout(abgleichen(safeStorage.getJSON<unknown>(schluessel, null), VORGABEN));
    setGeladen(true);
  }, [schluessel]);

  const aendern = useCallback(
    (fn: (l: DashboardLayout) => DashboardLayout) => {
      setLayout((alt) => {
        const neu = fn(alt);
        if (neu !== alt) safeStorage.setJSON(schluessel, neu);
        return neu;
      });
    },
    [schluessel],
  );

  const api = useMemo(
    () => ({
      verschieben: (id: string, ziel: Spalte, index: number) =>
        aendern((l) => verschiebenRein(l, id, ziel, index)),
      schritt: (id: string, richtung: 'auf' | 'ab') => aendern((l) => schrittRein(l, id, richtung)),
      spalteWechseln: (id: string) => aendern((l) => spalteWechselnRein(l, id)),
      ausblenden: (id: string) => aendern((l) => ausblendenRein(l, id)),
      einblenden: (id: string) => aendern((l) => einblendenRein(l, id, VORGABEN)),
      zuruecksetzen: () => {
        safeStorage.remove(schluessel);
        setLayout(standardLayout(VORGABEN));
      },
    }),
    [aendern, schluessel],
  );

  return {
    layout,
    geladen,
    istStandard: istStandard(layout, VORGABEN),
    ...api,
  };
}
