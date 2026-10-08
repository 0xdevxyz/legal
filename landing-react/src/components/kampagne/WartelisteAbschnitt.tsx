'use client';
import React, { useEffect, useRef, useState } from 'react';
import { CheckCircle2 } from 'lucide-react';
import WartelistenFormular from './WartelistenFormular';
import PlatzZaehler from './PlatzZaehler';
import { PLAETZE, PREIS_EARLY, PREIS_REGULAER } from './angebot';

/**
 * Die Warteliste als zweiter Weg unter der Preistabelle der Startseite.
 *
 * Seit dem Rueckbau (Launch Woche 40/41, 2026) verkauft "/" wieder. Die
 * Warteliste bleibt trotzdem stehen, aus zwei Gruenden:
 *
 * 1. Sie ist die Messbasis des laufenden Tests. Faellt sie weg, verliert die
 *    Auswertung nach Woche 45 ihren Vergleich (Launchplan complyo §7).
 * 2. Der Early-Access-Preis haengt an einem bestaetigten Platz
 *    (waitlist_leads.platz_nr), nicht an der Registrierung. Wer ihn will,
 *    braucht den Platz VOR dem Kauf; der Checkout prueft das selbst.
 *
 * Die Bestaetigungsmail fuehrt auf die Seite zurueck, von der die Anmeldung
 * kam (landing_path), also hierher mit ?confirmed=1&platz=N. Die Rueckmeldung
 * steht deshalb in diesem Abschnitt und nicht oben im Hero: wer bestaetigt
 * hat, soll direkt neben dem Hinweis landen, wie er den Preis einloest.
 */
export default function WartelisteAbschnitt({ kampagne }: { kampagne: string }) {
  const [bestaetigt, setBestaetigt] = useState<boolean | null>(null);
  const [platz, setPlatz] = useState<string | null>(null);
  const abschnitt = useRef<HTMLElement>(null);

  useEffect(() => {
    const p = new URLSearchParams(window.location.search);
    const c = p.get('confirmed');
    if (c === '1') setBestaetigt(true);
    if (c === '0') setBestaetigt(false);
    setPlatz(p.get('platz'));
    if (c === '1' || c === '0') {
      // Erst nach dem Laden und ohne Animation springen. Gemessen 28.09.2026:
      // Die Seite hat scroll-behavior: smooth, und ein animierter Sprung kurz
      // nach der Hydrierung wurde von nachladendem Video und Scanner
      // abgebrochen, scrollY blieb 0. 'instant' uebersteuert das CSS.
      let t = 0;
      const springen = () => {
        t = window.setTimeout(() => {
          abschnitt.current?.scrollIntoView({ block: 'start', behavior: 'instant' as ScrollBehavior });
        }, 150);
      };
      if (document.readyState === 'complete') springen();
      else window.addEventListener('load', springen, { once: true });
      return () => {
        window.removeEventListener('load', springen);
        window.clearTimeout(t);
      };
    }
  }, []);

  return (
    <section
      ref={abschnitt}
      id="anmeldung"
      aria-labelledby="warteliste-titel"
      className="py-20 scroll-mt-16"
    >
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        {bestaetigt === true && (
          <div className="mb-8 bg-green-50 border border-green-200 rounded-2xl p-5 flex items-start gap-3" role="status">
            <CheckCircle2 className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" aria-hidden="true" />
            <div>
              <p className="font-semibold text-green-900">
                {platz ? `Bestätigt, du hast Platz ${platz}.` : 'E-Mail bestätigt.'}
              </p>
              <p className="text-sm text-green-800 mt-0.5">
                {platz
                  ? `Buche Pro mit derselben E-Mail-Adresse, dann gilt ${PREIS_EARLY} statt ${PREIS_REGULAER} für zwölf Monate. Der Nachlass wird im Checkout automatisch abgezogen.`
                  : `Du stehst auf der Liste. Die ${PLAETZE} vergünstigten Plätze waren zu diesem Zeitpunkt bereits vergeben.`}
              </p>
            </div>
          </div>
        )}
        {bestaetigt === false && (
          <div className="mb-8 bg-amber-50 border border-amber-200 rounded-2xl p-5" role="alert">
            <p className="font-semibold text-amber-900">Dieser Bestätigungslink gilt nicht mehr.</p>
            <p className="text-sm text-amber-800 mt-0.5">
              Links laufen nach sieben Tagen ab. Trag dich unten einfach noch einmal ein.
            </p>
          </div>
        )}

        <div className="rounded-2xl border-2 border-akzent-600 p-8">
          <div className="mb-5">
            <PlatzZaehler gesamt={PLAETZE} />
          </div>
          <h2 id="warteliste-titel" className="font-heading text-2xl sm:text-3xl font-extrabold text-gray-900 mb-3">
            <span className="text-gray-500">Noch nicht buchen?</span>{' '}
            Sichere dir den Early-Access-Preis.
          </h2>
          <p className="text-gray-600 leading-relaxed mb-6">
            Die ersten {PLAETZE} bestätigten Plätze zahlen für Pro {PREIS_EARLY} statt {PREIS_REGULAER} im
            Monat, zwölf Monate lang. Der Platz zählt ab dem Klick in der Bestätigungsmail.
            Eine E-Mail-Adresse genügt, keine Zahlungsdaten, keine Bestellung.
          </p>
          <WartelistenFormular kampagne={kampagne} id="anmeldung-formular" />
        </div>
      </div>
    </section>
  );
}
