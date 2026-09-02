'use client';
import React, { useEffect, useState } from 'react';
import {
  ShieldCheck, Eye, Cookie, FileText, Gauge, CheckCircle2, ArrowDown,
} from 'lucide-react';
import WartelistenFormular from './WartelistenFormular';
import PlatzZaehler from './PlatzZaehler';

// Kennung dieser Kampagne. Landet je Anmeldung in waitlist_leads.campaign und
// ist der Schluessel, an dem sich spaeter ablesen laesst, was die Anzeigen
// gebracht haben. Eine zweite Seite bekommt eine eigene Kennung, nie diese.
const KAMPAGNE = 'ea100-bfsg';
const PLAETZE = 100;
const PREIS_EARLY = '35 €';
const PREIS_REGULAER = '49 €';

const SAEULEN = [
  {
    icon: Eye,
    titel: 'Barrierefreiheit',
    text: 'Kontraste, Alt-Texte, Tastaturbedienung und Formularbeschriftungen nach WCAG 2.1 AA.',
  },
  {
    icon: Cookie,
    titel: 'Cookies und Einwilligung',
    text: 'Welche Dienste vor der Einwilligung laden, und ob der Banner das abbildet.',
  },
  {
    icon: ShieldCheck,
    titel: 'Datenschutz',
    text: 'Eingebundene Drittdienste, Datenabflüsse und was die Erklärung davon abdeckt.',
  },
  {
    icon: FileText,
    titel: 'Rechtstexte',
    text: 'Impressum, Datenschutzerklärung und Widerruf auf Vollständigkeit geprüft.',
  },
];

const FAQ = [
  {
    q: `Warum ${PREIS_EARLY} statt ${PREIS_REGULAER}?`,
    a: `Complyo ist fertig genug, um zu arbeiten, aber jung genug, dass die ersten Nutzer die rauen Kanten finden werden. Dafür gibt es den Nachlass: ${PREIS_EARLY} statt ${PREIS_REGULAER} pro Monat, zwölf Monate ab deinem Start. Danach gilt der reguläre Preis, und du kannst monatlich kündigen.`,
  },
  {
    q: 'Wann geht es los?',
    a: 'Ein festes Datum steht noch nicht. Sobald die Plätze freigeschaltet werden, bekommst du eine Mail – vor allen anderen. Bis dahin entsteht dir keinerlei Verpflichtung: der Eintrag ist keine Bestellung.',
  },
  {
    q: 'Ist mein Platz sicher?',
    a: `Der Platz zählt ab dem Klick im Bestätigungslink, nicht ab dem Ausfüllen. Die ersten ${PLAETZE} bestätigten Anmeldungen bekommen den Preis; der Zähler oben zeigt den echten Stand. Wer später kommt, bleibt auf der Liste, aber ohne den Nachlass.`,
  },
  {
    q: 'Was passiert mit meiner E-Mail-Adresse?',
    a: 'Sie wird gespeichert, um dich zum Start zu benachrichtigen – sonst nichts. Kein Newsletter, keine Weitergabe an Dritte. Jede Mail enthält einen Abmeldelink, der die Adresse löscht.',
  },
  {
    q: 'Ersetzt complyo eine Rechtsberatung?',
    a: 'Nein. Complyo prüft technisch messbare Anforderungen, behebt sie und dokumentiert, was gemessen wurde. Ob dein Unternehmen im Einzelfall unter eine bestimmte Pflicht fällt, ist eine Rechtsfrage und bleibt bei deinem Anwalt.',
  },
];

export default function EarlyAccessKampagne() {
  const [bestaetigt, setBestaetigt] = useState<boolean | null>(null);
  const [platz, setPlatz] = useState<string | null>(null);

  // Rueckkehr aus der Bestaetigungsmail. Der Endpunkt leitet seit der
  // Kampagne auf DIESE Seite zurueck statt auf die Startseite — wer ueber eine
  // Anzeige kam, soll nach dem Klick nicht auf etwas Fremdem landen.
  useEffect(() => {
    const p = new URLSearchParams(window.location.search);
    const c = p.get('confirmed');
    if (c === '1') setBestaetigt(true);
    if (c === '0') setBestaetigt(false);
    setPlatz(p.get('platz'));
  }, []);

  return (
    <main id="inhalt" tabIndex={-1} className="font-sans antialiased bg-white">

      {/* ---------------------------------------------------------------- */}
      <section className="relative pt-16 pb-14 overflow-hidden">
        <div className="absolute top-0 right-0 w-[600px] h-[600px] bg-gradient-to-bl from-blue-50 via-indigo-50 to-transparent rounded-full blur-3xl opacity-70 pointer-events-none" />
        <div className="relative max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">

          {bestaetigt === true && (
            <div className="mb-8 bg-green-50 border border-green-200 rounded-2xl p-5 flex items-start gap-3" role="status">
              <CheckCircle2 className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" aria-hidden="true" />
              <div>
                <p className="font-semibold text-green-900">
                  {platz ? `Bestätigt – du hast Platz ${platz}.` : 'E-Mail bestätigt.'}
                </p>
                <p className="text-sm text-green-800 mt-0.5">
                  {platz
                    ? `Der Preis von ${PREIS_EARLY} im ersten Jahr ist für dich vorgemerkt. Wir melden uns, sobald es losgeht.`
                    : 'Du stehst auf der Liste. Die 100 vergünstigten Plätze waren zu diesem Zeitpunkt bereits vergeben – wir melden uns trotzdem zum Start.'}
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

          <div className="mb-6">
            <PlatzZaehler gesamt={PLAETZE} />
          </div>

          <h1 className="font-heading text-4xl sm:text-5xl font-extrabold text-gray-900 leading-[1.1] mb-5">
            Seit Juni 2025 gilt das BFSG.{' '}
            <span className="text-blue-600">Complyo findet die Lücken auf deiner Website – und schließt sie.</span>
          </h1>

          <p className="text-lg text-gray-600 leading-relaxed mb-3">
            Barrierefreiheit, Cookies, Datenschutz und Rechtstexte: ein Scan zeigt, was nicht
            stimmt. Die Reparatur passiert im Werkzeug, und jede Änderung wird danach im Browser
            nachgemessen – damit du belegen kannst, was du getan hast.
          </p>

          <p className="text-lg text-gray-900 font-semibold leading-relaxed mb-8">
            Die ersten {PLAETZE} zahlen {PREIS_EARLY} statt {PREIS_REGULAER} im Monat – das ganze erste Jahr.
          </p>

          <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6">
            <WartelistenFormular kampagne={KAMPAGNE} id="anmeldung" />
          </div>
        </div>
      </section>

      {/* ---------------------------------------------------------------- */}
      <section className="py-16 bg-gray-50">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="font-heading text-3xl font-extrabold text-gray-900 mb-3">
            Vier Bereiche, ein Scan
          </h2>
          <p className="text-gray-600 mb-10 max-w-2xl leading-relaxed">
            Die meisten Werkzeuge prüfen eines davon und liefern eine Liste. Complyo prüft alle
            vier und arbeitet die Befunde ab.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
            {SAEULEN.map(({ icon: Icon, titel, text }) => (
              <div key={titel} className="bg-white rounded-2xl border border-gray-200 p-6">
                <Icon className="w-6 h-6 text-blue-600 mb-3" aria-hidden="true" />
                <h3 className="font-bold text-gray-900 mb-1.5">{titel}</h3>
                <p className="text-sm text-gray-600 leading-relaxed">{text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ---------------------------------------------------------------- */}
      <section className="py-16">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="rounded-2xl border-2 border-blue-600 p-8">
            <div className="inline-flex items-center gap-2 bg-blue-50 rounded-full px-3 py-1 mb-4">
              <Gauge className="w-4 h-4 text-blue-600" aria-hidden="true" />
              <span className="text-xs font-semibold text-blue-700 uppercase tracking-wide">
                Nachgemessen, nicht behauptet
              </span>
            </div>

            <h2 className="font-heading text-2xl sm:text-3xl font-extrabold text-gray-900 mb-4">
              289 Pflicht-Verstöße gefunden. 32 blieben übrig.
            </h2>

            <p className="text-gray-600 leading-relaxed mb-4">
              Gemessen an 24 echten Kundenwebsites im August 2026, in einem Durchlauf: Complyo hat
              89 Prozent der automatisiert prüfbaren Pflicht-Verstöße nach WCAG 2.1 AA behoben.
              Nachgemessen wurde im Browser, nach der Reparatur.
            </p>

            <p className="text-sm text-gray-500 leading-relaxed">
              Was diese Zahl nicht sagt: Ein automatischer Test erfasst je nach Studie ein Drittel
              bis die Hälfte aller Barrieren. Ob eine Bildbeschreibung inhaltlich taugt oder sich
              eine Seite mit dem Screenreader gut bedienen lässt, beurteilt ein Mensch. Complyo
              nimmt dir den messbaren Teil ab und sagt dir, wo der Rest anfängt.
            </p>
          </div>
        </div>
      </section>

      {/* ---------------------------------------------------------------- */}
      <section className="py-16 bg-gray-50">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="font-heading text-3xl font-extrabold text-gray-900 mb-10">
            Häufige Fragen
          </h2>
          <dl className="space-y-8">
            {FAQ.map(({ q, a }) => (
              <div key={q}>
                <dt className="font-bold text-gray-900 mb-2">{q}</dt>
                <dd className="text-gray-600 leading-relaxed">{a}</dd>
              </div>
            ))}
          </dl>
        </div>
      </section>

      {/* ---------------------------------------------------------------- */}
      <section className="py-16">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <ArrowDown className="w-6 h-6 text-blue-600 mx-auto mb-4" aria-hidden="true" />
          <h2 className="font-heading text-3xl font-extrabold text-gray-900 mb-3">
            Platz sichern, {PREIS_EARLY} statt {PREIS_REGULAER}
          </h2>
          <p className="text-gray-600 mb-8 leading-relaxed">
            Eine E-Mail-Adresse, ein Bestätigungsklick. Keine Zahlungsdaten, keine Bestellung.
          </p>
          <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6 text-left">
            <WartelistenFormular kampagne={KAMPAGNE} id="anmeldung-unten" />
          </div>
          <p className="text-xs text-gray-500 mt-6">
            Alle Preise netto zzgl. gesetzlicher Umsatzsteuer.
          </p>
        </div>
      </section>
    </main>
  );
}
