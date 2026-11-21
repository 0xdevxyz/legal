'use client';

import React, { useState } from 'react';
import { Calculator } from 'lucide-react';
import { PREIS_EARLY, PREIS_REGULAER } from '@/components/kampagne/angebot';

/**
 * Was kostet es, nichts zu tun. Gerechnet mit den Zahlen des Besuchers.
 *
 * Die drei Eingaben sind sichtbar und änderbar, die Formel steht daneben. Das
 * ist die einzige Form, in der eine Kostenrechnung auf dieser Seite stehen
 * darf: keine Pauschale aus unserem Haus, keine Multiplikation von Befunden
 * mit Eurobeträgen (siehe WebsiteScanner.tsx, gelöscht am 03.09.2026).
 * Gerechnet wird der Eigenaufwand, nicht ein Bußgeld.
 *
 * Fällt die Rechnung gegen Complyo aus, sagt der Rechner das. Ein Rechner,
 * der immer dasselbe Ergebnis liefert, ist kein Rechner, sondern ein Werbe-
 * banner, und der Besucher merkt das an der ersten Eingabe.
 */
const PRO_MONAT_REGULAER = parseInt(PREIS_REGULAER, 10);
const PRO_MONAT_EARLY = parseInt(PREIS_EARLY, 10);

const euro = (n: number) =>
  n.toLocaleString('de-DE', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 });

export default function NichtstunRechner() {
  const [stundensatz, setStundensatz] = useState(65);
  const [stundenMonat, setStundenMonat] = useState(3);
  const [websites, setWebsites] = useState(1);

  const eigenaufwandJahr = Math.max(0, stundensatz) * Math.max(0, stundenMonat) * 12 * Math.max(1, websites);
  const complyoJahr = PRO_MONAT_REGULAER * 12 * Math.max(1, websites);
  const complyoEarlyJahr = PRO_MONAT_EARLY * 12 * Math.max(1, websites);
  const differenz = eigenaufwandJahr - complyoJahr;

  const feld = (
    id: string, label: string, hinweis: string, wert: number,
    setzen: (n: number) => void, min: number, max: number, einheit: string,
  ) => (
    <div>
      <label htmlFor={id} className="block text-sm font-semibold text-gray-900 mb-1">{label}</label>
      <div className="flex items-center gap-2">
        <input
          id={id}
          type="number"
          inputMode="numeric"
          min={min}
          max={max}
          value={wert}
          onChange={(e) => setzen(Number(e.target.value) || 0)}
          className="w-28 px-3 py-2 rounded-lg border-2 border-gray-200 bg-white text-gray-900 focus:border-akzent-600 focus:ring-4 focus:ring-akzent-100 outline-none"
        />
        <span className="text-sm text-gray-600">{einheit}</span>
      </div>
      <p className="text-xs text-gray-500 mt-1">{hinweis}</p>
    </div>
  );

  return (
    <section aria-labelledby="nichtstun-titel" className="bg-white rounded-2xl border-2 border-gray-200 p-6 sm:p-8">
      <div className="inline-flex items-center gap-2 bg-gray-100 rounded-full px-3 py-1 mb-4">
        <Calculator className="w-4 h-4 text-gray-700" aria-hidden="true" />
        <span className="text-xs font-semibold text-gray-700 uppercase tracking-wide">
          Ihre Zahlen, Ihre Rechnung
        </span>
      </div>
      <h3 id="nichtstun-titel" className="font-heading text-2xl sm:text-3xl font-extrabold text-gray-900 mb-3">
        Was kostet es, das selbst nachzuhalten?
      </h3>
      <p className="text-gray-600 leading-relaxed mb-8 max-w-3xl">
        Nichtstun ist selten gratis. Meist heißt es: jemand im Haus liest Urteile, prüft
        Cookie-Banner nach jedem Plugin-Update und pflegt Rechtstexte nach. Tragen Sie ein,
        was das bei Ihnen kostet. Wir rechnen nur mit dem, was Sie eingeben.
      </p>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
        <div className="lg:col-span-2 space-y-5">
          {feld('rechner-stundensatz', 'Stundensatz', 'Was eine Stunde von Ihnen oder Ihrer Agentur kostet.', stundensatz, setStundensatz, 0, 1000, '€ je Stunde')}
          {feld('rechner-stunden', 'Aufwand je Monat', 'Prüfen, nachlesen, nachpflegen. Pro Website.', stundenMonat, setStundenMonat, 0, 200, 'Stunden')}
          {feld('rechner-websites', 'Websites', 'Jede Domain zählt einzeln.', websites, setWebsites, 1, 500, websites === 1 ? 'Website' : 'Websites')}
        </div>

        <div className="lg:col-span-3">
          <div className="rounded-xl bg-gray-50 border border-gray-200 p-5 sm:p-6">
            <dl className="divide-y divide-gray-200">
              <div className="flex items-baseline justify-between gap-4 py-3">
                <dt className="text-sm text-gray-700">
                  Eigenaufwand im Jahr
                  <span className="block text-xs text-gray-500">
                    {euro(stundensatz)} × {stundenMonat} h × 12 Monate{websites > 1 ? ` × ${websites} Websites` : ''}
                  </span>
                </dt>
                <dd className="text-2xl font-extrabold text-gray-900 whitespace-nowrap">{euro(eigenaufwandJahr)}</dd>
              </div>
              <div className="flex items-baseline justify-between gap-4 py-3">
                <dt className="text-sm text-gray-700">
                  Complyo Pro im Jahr
                  <span className="block text-xs text-gray-500">
                    {PREIS_REGULAER} × 12 Monate{websites > 1 ? ` × ${websites} Websites` : ''}, monatlich kündbar
                  </span>
                </dt>
                <dd className="text-2xl font-extrabold text-gray-900 whitespace-nowrap">{euro(complyoJahr)}</dd>
              </div>
              <div className="flex items-baseline justify-between gap-4 py-3">
                <dt className="text-sm font-semibold text-gray-900">Unterschied im Jahr</dt>
                <dd className={`text-2xl font-extrabold whitespace-nowrap ${differenz >= 0 ? 'text-green-700' : 'text-gray-900'}`}>
                  {differenz >= 0 ? '+' : ''}{euro(differenz)}
                </dd>
              </div>
            </dl>

            <p className="text-sm leading-relaxed mt-4 text-gray-700">
              {differenz > 0 && (
                <>
                  Mit Ihren Zahlen kostet das Selbermachen {euro(differenz)} mehr im Jahr als Complyo Pro,
                  und die Befunde oben wären bis dahin behoben und dokumentiert.
                  Mit Early-Access-Platz sind es {euro(complyoEarlyJahr)} statt {euro(complyoJahr)} im ersten Jahr.
                </>
              )}
              {differenz === 0 && (
                <>Mit Ihren Zahlen kostet beides gleich viel. Dann entscheidet, ob Sie den Nachweis selbst führen wollen.</>
              )}
              {differenz < 0 && (
                <>
                  Mit Ihren Zahlen ist das Selbermachen {euro(-differenz)} im Jahr günstiger. Dann rechnet sich Complyo
                  für Sie über den Preis nicht. Was bleibt, ist der Nachweis: ein Protokoll je Änderung, nachgemessen im Browser.
                  Ob Ihnen das den Unterschied wert ist, entscheiden Sie.
                </>
              )}
            </p>
          </div>

          <p className="text-xs text-gray-500 mt-3 leading-relaxed">
            Nicht enthalten: Bußgelder, Abmahnungen, Schadensersatz. Die lassen sich für eine einzelne Website nicht
            seriös vorhersagen, und wir tun es deshalb nicht. Alle Preise netto.
          </p>
        </div>
      </div>
    </section>
  );
}
