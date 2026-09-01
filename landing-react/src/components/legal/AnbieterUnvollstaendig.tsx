'use client';

import React from 'react';
import { AlertTriangle } from 'lucide-react';
import { ANBIETER_FEHLENDE_PFLICHTFELDER, ANBIETER_UNVOLLSTAENDIG } from '@/lib/anbieter';

/**
 * Sichtbarer Hinweis, solange Pflichtangaben des Anbieters fehlen.
 *
 * Steht auf Impressum, AGB und Datenschutzerklärung. Der Sinn ist, dass eine
 * unvollständige Rechtsseite als unvollständig erkennbar ist, statt still eine
 * erfundene Angabe zu behaupten. Sobald die Felder in `@/lib/anbieter` gefüllt
 * sind, verschwindet der Hinweis auf allen drei Seiten zugleich.
 */
export default function AnbieterUnvollstaendig({ seite }: { seite: string }) {
  if (!ANBIETER_UNVOLLSTAENDIG) return null;

  return (
    <div className="bg-red-50 border-2 border-red-400 rounded-xl p-6 mb-8">
      <div className="flex items-start gap-3">
        <AlertTriangle className="w-6 h-6 text-red-600 flex-shrink-0 mt-0.5" aria-hidden="true" />
        <div>
          <h2 className="text-lg font-bold text-red-900 mb-1">Diese Seite ist unvollständig</h2>
          <p className="text-sm text-red-800">
            {seite} nennt den Anbieter, und es fehlen Pflichtangaben. Die Seite darf in diesem
            Zustand nicht öffentlich erreichbar sein.
          </p>
          <ul className="list-disc list-outside ml-5 mt-2 text-sm text-red-800 space-y-1">
            {ANBIETER_FEHLENDE_PFLICHTFELDER.map((feld) => (
              <li key={feld}>{feld}</li>
            ))}
          </ul>
          <p className="text-sm text-red-800 mt-2">
            Die Werte stehen als leere Felder in
            <code className="mx-1 px-1.5 py-0.5 bg-red-100 rounded text-xs">
              src/lib/anbieter.ts
            </code>
            und wirken von dort auf Impressum, AGB und Datenschutzerklärung.
          </p>
        </div>
      </div>
    </div>
  );
}
