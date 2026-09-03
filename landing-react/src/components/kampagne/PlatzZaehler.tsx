'use client';
import React, { useEffect, useState } from 'react';
import { Users } from 'lucide-react';
import { leadsApi } from '@/lib/api';

/**
 * Zeigt, wie viele der Early-Access-Plaetze noch frei sind.
 *
 * Die Zahl kommt aus der Datenbank, nicht aus einer Konstante: "nur noch X von
 * 100" ist eine Werbeaussage und muss gedeckt sein. Antwortet der Zaehler
 * nicht, wird gar nichts angezeigt — eine erfundene Zahl waere schlimmer als
 * keine.
 */
export default function PlatzZaehler({ gesamt }: { gesamt: number }) {
  const [frei, setFrei] = useState<number | null>(null);

  useEffect(() => {
    let abgebrochen = false;
    leadsApi
      .waitlistPlaetze()
      .then((p) => { if (!abgebrochen) setFrei(p.frei); })
      .catch(() => { /* still: lieber keine Zahl als eine geratene */ });
    return () => { abgebrochen = true; };
  }, []);

  if (frei === null) return null;

  const vergriffen = frei === 0;
  // Am ersten Tag stehen alle Plaetze offen. "Noch 100 von 100 frei" liest sich
  // dann wie "es will niemand"; die Zahl bleibt dieselbe, nur die Ansage nicht.
  const unberuehrt = frei === gesamt;

  return (
    <div
      className={`inline-flex items-center gap-2 rounded-full px-4 py-1.5 border ${
        vergriffen
          ? 'bg-gray-50 border-gray-200 text-gray-600'
          : 'bg-orange-50 border-orange-100 text-orange-800'
      }`}
    >
      <Users className="w-4 h-4 flex-shrink-0" aria-hidden="true" />
      <span className="text-sm font-semibold">
        {vergriffen
          ? `Alle ${gesamt} Plätze vergeben – Eintrag zählt für die Nachrückerliste`
          : unberuehrt
            ? `${gesamt} Plätze zum Early-Access-Preis`
            : `Noch ${frei} von ${gesamt} Plätzen frei`}
      </span>
    </div>
  );
}
