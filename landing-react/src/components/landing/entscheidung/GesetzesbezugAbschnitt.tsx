'use client';

import React from 'react';
import { Scale, AlertTriangle } from 'lucide-react';
import { GESETZESBEZUG, PILLAR_ZU_BEREICH } from './gesetzesbezug';

interface PillarDaten {
  issues: number;
  critical: number;
  label?: string;
}

/**
 * Zu jedem Bereich mit Befunden: welche Norm die Pflicht trägt, wer sie
 * durchsetzt, was das Gesetz als Rahmen nennt, was in der Praxis passiert.
 *
 * Der Abschnitt zeigt nur Bereiche, in denen der Scan etwas gefunden hat.
 * Ein sauberer Bereich bekommt keinen Gesetzestext, sonst liest sich die Seite
 * wie ein Drohbrief und nicht wie ein Befund. Kritische Bereiche stehen vorn.
 */
export default function GesetzesbezugAbschnitt({ pillars }: { pillars: Record<string, PillarDaten> }) {
  const betroffen = Object.entries(pillars)
    .filter(([, p]) => (p.issues ?? 0) > 0)
    .map(([key, p]) => ({ key, p, bezug: GESETZESBEZUG[PILLAR_ZU_BEREICH[key] ?? key] }))
    .filter((e) => e.bezug)
    .sort((a, b) => (b.p.critical ?? 0) - (a.p.critical ?? 0) || (b.p.issues ?? 0) - (a.p.issues ?? 0));

  if (betroffen.length === 0) return null;

  return (
    <section aria-labelledby="gesetzesbezug-titel" className="bg-white rounded-2xl border-2 border-gray-200 p-6 sm:p-8">
      <div className="inline-flex items-center gap-2 bg-gray-100 rounded-full px-3 py-1 mb-4">
        <Scale className="w-4 h-4 text-gray-700" aria-hidden="true" />
        <span className="text-xs font-semibold text-gray-700 uppercase tracking-wide">
          Was das Gesetz dazu sagt
        </span>
      </div>
      <h3 id="gesetzesbezug-titel" className="font-heading text-2xl sm:text-3xl font-extrabold text-gray-900 mb-3">
        {betroffen.length === 1
          ? 'Ein Bereich mit Befunden. Das steht dahinter.'
          : `${betroffen.length} Bereiche mit Befunden. Das steht dahinter.`}
      </h3>
      <p className="text-gray-600 leading-relaxed mb-8 max-w-3xl">
        Der Scan misst, was von außen messbar ist. Was er nicht sehen kann: Größe Ihres
        Unternehmens, Zielgruppe, ob eine Pflicht für Sie überhaupt gilt. Deshalb steht hier
        der Rahmen aus dem Gesetz, mit Fundstelle, und keine Prognose für Ihre Website.
      </p>

      <ol className="space-y-6">
        {betroffen.map(({ key, p, bezug }) => {
          const kritisch = (p.critical ?? 0) > 0;
          return (
            <li key={key} className={`rounded-xl border-2 p-5 sm:p-6 ${kritisch ? 'border-red-200 bg-red-50/40' : 'border-gray-200 bg-gray-50'}`}>
              <div className="flex flex-wrap items-center gap-x-3 gap-y-2 mb-3">
                <h4 className="font-bold text-gray-900 text-lg">{p.label ?? key}</h4>
                <span className={`inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-1 rounded-full ${kritisch ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800'}`}>
                  {kritisch && <AlertTriangle className="w-3.5 h-3.5" aria-hidden="true" />}
                  {kritisch
                    ? `${p.critical} von ${p.issues} ${p.issues === 1 ? 'Befund' : 'Befunden'} betreffen eine Pflicht`
                    : `${p.issues} ${p.issues === 1 ? 'Befund' : 'Befunde'}, keine fehlende Pflichtangabe`}
                </span>
              </div>

              <dl className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-4 text-sm">
                <div>
                  <dt className="font-semibold text-gray-900 mb-1">Norm</dt>
                  <dd className="text-gray-700 leading-relaxed">{bezug.norm}</dd>
                </div>
                <div>
                  <dt className="font-semibold text-gray-900 mb-1">Pflicht</dt>
                  <dd className="text-gray-700 leading-relaxed">{bezug.pflicht}</dd>
                </div>
                <div>
                  <dt className="font-semibold text-gray-900 mb-1">Wer sie durchsetzt</dt>
                  <dd className="text-gray-700 leading-relaxed">{bezug.durchsetzung}</dd>
                </div>
                <div>
                  <dt className="font-semibold text-gray-900 mb-1">Rahmen laut Gesetz</dt>
                  <dd className="text-gray-700 leading-relaxed">
                    {bezug.rahmen}{' '}
                    <span className="text-gray-500">Das ist die Obergrenze im Gesetz, keine Aussage über Ihren Fall.</span>
                  </dd>
                </div>
                <div className="md:col-span-2">
                  <dt className="font-semibold text-gray-900 mb-1">Was in der Praxis zuerst kommt</dt>
                  <dd className="text-gray-700 leading-relaxed">{bezug.praxis}</dd>
                </div>
                {bezug.entscheidung && (
                  <div className="md:col-span-2">
                    <dt className="font-semibold text-gray-900 mb-1">Entscheidungen</dt>
                    <dd className="text-gray-500 leading-relaxed">{bezug.entscheidung}</dd>
                  </div>
                )}
              </dl>
            </li>
          );
        })}
      </ol>

      <p className="text-xs text-gray-500 mt-6 leading-relaxed">
        Keine Rechtsberatung. Ob und wie eine Pflicht Ihr Unternehmen trifft, klärt ein Anwalt.
        Complyo misst, behebt und dokumentiert den technisch prüfbaren Teil.
      </p>
    </section>
  );
}
