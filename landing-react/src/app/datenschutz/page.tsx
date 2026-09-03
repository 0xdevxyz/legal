'use client';

import React from 'react';
import { motion } from 'framer-motion';
import Link from 'next/link';
import { ArrowLeft, Shield } from 'lucide-react';
import { ANBIETER, ANBIETER_ANSCHRIFT } from '@/lib/anbieter';
import AnbieterUnvollstaendig from '@/components/legal/AnbieterUnvollstaendig';

// Der Verantwortliche in Abschnitt 2 war bis zum 01.09.2026 frei erfunden:
// "Complyo GmbH, Musterstrasse 123, 10115 Berlin" samt einer Telefonnummer
// +49 (0) 30 1234567, die niemandem gehoert. Art. 13 Abs. 1 lit. a DSGVO
// verlangt Namen und Kontaktdaten des Verantwortlichen; ohne sie kann niemand
// seine Rechte nach Art. 15 ff. ausueben, und die Erklaerung schuetzt nichts.
// Die Angaben kommen jetzt aus @/lib/anbieter, gemeinsam mit Impressum und AGB.

// Jede Verarbeitung nennt Zweck, Rechtsgrundlage und Speicherdauer — das
// verlangt Art. 13 DSGVO, und genau das fehlte hier. Die Angaben beschreiben
// den tatsaechlichen Betrieb: Logrotate loescht die Server-Logs nach 14 Tagen,
// die Einwilligung liegt im Local Storage, Lead-Daten werden nach 730 Tagen
// automatisch geloescht (GDPR_RETENTION_DAYS).
const VERARBEITUNGEN = [
  {
    titel: 'Aufruf der Website (Server-Log-Dateien)',
    daten:
      'Browsertyp und -version, verwendetes Betriebssystem, Referrer-URL, Hostname des zugreifenden Rechners, Uhrzeit der Serveranfrage und IP-Adresse.',
    zweck:
      'Auslieferung der Website, Gewährleistung eines störungsfreien Betriebs sowie Erkennung und Abwehr von Angriffen.',
    rechtsgrundlage:
      'Art. 6 Abs. 1 lit. f DSGVO — unser berechtigtes Interesse am sicheren und stabilen Betrieb dieser Website.',
    dauer: 'Die Server-Protokolle werden spätestens nach 14 Tagen gelöscht.',
  },
  {
    titel: 'Cookies und Einwilligungsverwaltung',
    daten:
      'Ihre Auswahl im Cookie-Banner und der Zeitpunkt der Auswahl, gespeichert im Local Storage Ihres Browsers (cookie-consent, cookie-consent-date).',
    zweck:
      'Technisch notwendige Bereitstellung der Website, Berücksichtigung Ihrer Auswahl bei weiteren Besuchen und Nachweis der erteilten oder verweigerten Einwilligung.',
    rechtsgrundlage:
      'Für technisch notwendige Speicherungen § 25 Abs. 2 Nr. 2 TDDDG und Art. 6 Abs. 1 lit. c DSGVO (Nachweispflicht nach Art. 7 Abs. 1 DSGVO). Analyse- und Marketing-Cookies setzen wir ausschließlich nach Ihrer Einwilligung nach § 25 Abs. 1 TDDDG und Art. 6 Abs. 1 lit. a DSGVO.',
    dauer:
      'Ihre Einwilligungsentscheidung bleibt bis zum Widerruf gespeichert, längstens jedoch für die Dauer der gesetzlichen Nachweispflicht von drei Jahren.',
  },
  {
    titel: 'Kostenloser Website-Check',
    daten:
      'Die von Ihnen eingegebene Website-Adresse, das Prüfergebnis, den Zeitpunkt der Prüfung sowie Ihre IP-Adresse zur Begrenzung der Zugriffszahl.',
    zweck:
      'Durchführung der von Ihnen angeforderten Prüfung, Anzeige des Ergebnisses und Schutz des Dienstes vor missbräuchlicher Massennutzung.',
    rechtsgrundlage:
      'Art. 6 Abs. 1 lit. b DSGVO — Durchführung vorvertraglicher Maßnahmen auf Ihre Anfrage; hinsichtlich der Missbrauchsabwehr Art. 6 Abs. 1 lit. f DSGVO.',
    dauer:
      'Prüfergebnisse ohne Kundenkonto werden nach 30 Tagen gelöscht. Ergebnisse in einem Kundenkonto bleiben gespeichert, solange das Konto besteht, damit Sie Verläufe vergleichen können.',
  },
  {
    titel: 'Kundenkonto und Vertragsabwicklung',
    daten:
      'Bestands- und Vertragsdaten wie Name, Firma, E-Mail-Adresse, gebuchter Tarif, die von Ihnen hinterlegten Websites und die Abrechnungsdaten.',
    zweck:
      'Bereitstellung des Kundenkontos, Erbringung der gebuchten Leistungen, Abrechnung und Kundenbetreuung.',
    rechtsgrundlage:
      'Art. 6 Abs. 1 lit. b DSGVO — Erfüllung des Vertrags; für die Aufbewahrung von Rechnungsunterlagen Art. 6 Abs. 1 lit. c DSGVO.',
    dauer:
      'Für die Dauer des Vertragsverhältnisses. Nach dessen Ende werden die Daten gelöscht, soweit keine gesetzliche Aufbewahrungspflicht besteht; Rechnungs- und Buchungsbelege bewahren wir nach § 147 AO und § 257 HGB zehn Jahre auf.',
  },
  {
    titel: 'Kontaktaufnahme',
    daten:
      'Ihre Nachricht sowie die darin und in den Kopfzeilen enthaltenen Angaben, insbesondere Ihre E-Mail-Adresse.',
    zweck: 'Bearbeitung Ihrer Anfrage und Anschlussfragen dazu.',
    rechtsgrundlage:
      'Art. 6 Abs. 1 lit. b DSGVO, wenn Ihre Anfrage der Anbahnung oder Durchführung eines Vertrags dient, sonst Art. 6 Abs. 1 lit. f DSGVO — unser berechtigtes Interesse an der Beantwortung von Anfragen.',
    dauer:
      'Anfragen ohne anschließendes Vertragsverhältnis werden spätestens nach 24 Monaten gelöscht, sofern keine gesetzliche Aufbewahrungspflicht entgegensteht.',
  },
];

const RECHTE = [
  ['Recht auf Auskunft (Art. 15 DSGVO)', 'Sie können erfahren, welche Daten wir zu Ihnen verarbeiten.'],
  ['Recht auf Berichtigung (Art. 16 DSGVO)', 'Unrichtige Daten müssen wir korrigieren.'],
  ['Recht auf Löschung (Art. 17 DSGVO)', 'Sie können die Löschung Ihrer Daten verlangen.'],
  ['Recht auf Einschränkung der Verarbeitung (Art. 18 DSGVO)', 'Sie können die Verarbeitung vorübergehend sperren lassen.'],
  ['Recht auf Datenübertragbarkeit (Art. 20 DSGVO)', 'Sie erhalten Ihre Daten in einem gängigen Format.'],
  ['Widerspruchsrecht (Art. 21 DSGVO)', 'Sie können der Verarbeitung aus berechtigtem Interesse widersprechen.'],
  ['Widerruf Ihrer Einwilligung (Art. 7 Abs. 3 DSGVO)', 'Eine erteilte Einwilligung können Sie jederzeit für die Zukunft widerrufen.'],
];

export default function DatenschutzPage() {
  return (
    <main id="inhalt" tabIndex={-1} className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-blue-50">
      <div className="container mx-auto px-4 py-12 max-w-4xl">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-blue-600 hover:text-blue-700 mb-8 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Zurück zur Startseite
          </Link>

          <AnbieterUnvollstaendig seite="Der Verantwortliche in dieser Erklärung" />

          <div className="bg-white rounded-xl shadow-lg p-8 mb-8">
            <div className="flex items-center gap-3 mb-4">
              <Shield className="w-8 h-8 text-blue-600" />
              <h1 className="text-4xl font-bold text-gray-900">Datenschutzerklärung</h1>
            </div>
            <p className="text-gray-600">
              Stand:{' '}
              1. September 2026
            </p>
          </div>

          <div className="bg-white rounded-xl shadow-lg p-8 space-y-8">
            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">1. Datenschutz auf einen Blick</h2>
              <div className="space-y-4 text-gray-700 text-sm leading-relaxed">
                <p>
                  Die folgenden Hinweise geben einen Überblick darüber, was mit Ihren personenbezogenen Daten
                  geschieht, wenn Sie diese Website besuchen. Personenbezogene Daten sind alle Daten, mit denen Sie
                  persönlich identifiziert werden können. Zu jeder Verarbeitung finden Sie unten, wozu wir die Daten
                  nutzen, worauf wir uns dabei stützen und wie lange wir sie speichern.
                </p>
                <p>
                  Verantwortlich für die Datenverarbeitung auf dieser Website ist der Websitebetreiber. Seine
                  Kontaktdaten stehen im nächsten Abschnitt.
                </p>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">2. Verantwortliche Stelle</h2>
              <div className="space-y-3 text-gray-700 text-sm leading-relaxed">
                <p className="font-semibold">
                  Verantwortlicher im Sinne der Datenschutz-Grundverordnung ist:
                </p>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="font-semibold">{ANBIETER.name || 'Name fehlt'}</p>
                  <p>{ANBIETER.geschaeftsbezeichnung}</p>
                  <p className="mt-2">{ANBIETER.strasse}</p>
                  <p>{ANBIETER_ANSCHRIFT}</p>
                  <p>{ANBIETER.land}</p>
                  {ANBIETER.telefon && (
                    <p className="mt-3">
                      Telefon:{' '}
                      <a
                        href={'tel:' + ANBIETER.telefon.replace(/[^+0-9]/g, '')}
                        className="text-blue-600 underline"
                      >
                        {ANBIETER.telefon}
                      </a>
                    </p>
                  )}
                  <p className={ANBIETER.telefon ? '' : 'mt-3'}>
                    E-Mail:{' '}
                    <a href={'mailto:' + ANBIETER.datenschutzEmail} className="text-blue-600 underline">
                      {ANBIETER.datenschutzEmail}
                    </a>
                  </p>
                </div>
                <p>
                  Verantwortliche Stelle ist die natürliche oder juristische Person, die allein oder gemeinsam mit
                  anderen über die Zwecke und Mittel der Verarbeitung personenbezogener Daten entscheidet.
                </p>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">
                3. Verarbeitungen im Einzelnen: Zwecke, Rechtsgrundlagen und Speicherdauer
              </h2>
              <div className="space-y-6 text-gray-700 text-sm leading-relaxed">
                {VERARBEITUNGEN.map((v) => (
                  <div key={v.titel} className="border-l-4 border-blue-100 pl-4">
                    <h3 className="font-semibold text-gray-900 mb-2">{v.titel}</h3>
                    <dl className="space-y-1">
                      <div>
                        <dt className="inline font-semibold">Verarbeitete Daten: </dt>
                        <dd className="inline">{v.daten}</dd>
                      </div>
                      <div>
                        <dt className="inline font-semibold">Zweck: </dt>
                        <dd className="inline">{v.zweck}</dd>
                      </div>
                      <div>
                        <dt className="inline font-semibold">Rechtsgrundlage: </dt>
                        <dd className="inline">{v.rechtsgrundlage}</dd>
                      </div>
                      <div>
                        <dt className="inline font-semibold">Speicherdauer: </dt>
                        <dd className="inline">{v.dauer}</dd>
                      </div>
                    </dl>
                  </div>
                ))}
                <p>
                  Welche Cookies im Einzelnen gesetzt werden, steht in der{' '}
                  <Link href="/cookie-richtlinie" className="text-blue-600 underline">
                    Cookie-Richtlinie
                  </Link>
                  . Ihre Einwilligung können Sie dort jederzeit ändern oder widerrufen.
                </p>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">4. Empfänger Ihrer Daten</h2>
              <div className="space-y-3 text-gray-700 text-sm leading-relaxed">
                <p>
                  Ihre Daten werden auf Servern in Deutschland verarbeitet. Dienstleister, die uns beim Betrieb
                  unterstützen — insbesondere für Hosting und Zahlungsabwicklung — erhalten Zugriff nur, soweit das
                  für ihre Aufgabe erforderlich ist, und sind über Verträge zur Auftragsverarbeitung nach Art. 28
                  DSGVO gebunden.
                </p>
                <p>
                  Eine Übermittlung in Länder außerhalb der Europäischen Union findet nicht statt. Sollte sich das
                  ändern, nennen wir das Land, den Empfänger und die Grundlage der Übermittlung an dieser Stelle,
                  bevor die Übermittlung beginnt.
                </p>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">5. Ihre Rechte</h2>
              <div className="space-y-4 text-gray-700 text-sm leading-relaxed">
                <p>Ihnen stehen jederzeit die folgenden Rechte zu:</p>
                <ul className="list-disc list-outside space-y-2 ml-6">
                  {RECHTE.map(([recht, erklaerung]) => (
                    <li key={recht}>
                      <strong>{recht}</strong> — {erklaerung}
                    </li>
                  ))}
                </ul>
                <p>
                  Zur Ausübung genügt eine formlose Nachricht an{' '}
                  <a href={'mailto:' + ANBIETER.datenschutzEmail} className="text-blue-600 underline">
                    {ANBIETER.datenschutzEmail}
                  </a>
                  . Auskunft, Export und Löschung Ihrer Kontodaten können Sie außerdem selbst über die{' '}
                  <Link href="/gdpr" className="text-blue-600 underline">
                    DSGVO-Datenverwaltung
                  </Link>{' '}
                  auslösen.
                </p>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">
                6. Beschwerderecht bei der Aufsichtsbehörde
              </h2>
              <div className="space-y-3 text-gray-700 text-sm leading-relaxed">
                <p>
                  Sind Sie der Ansicht, dass die Verarbeitung Ihrer Daten gegen die Datenschutz-Grundverordnung
                  verstößt, können Sie sich nach Art. 77 DSGVO bei einer Aufsichtsbehörde beschweren — unabhängig
                  von anderen Rechtsbehelfen. Zuständig ist die Behörde Ihres gewöhnlichen Aufenthaltsorts, Ihres
                  Arbeitsplatzes oder des Orts des vermuteten Verstoßes.
                </p>
                <p>
                  Für uns als verantwortliche Stelle ist die Aufsichtsbehörde am Sitz des Unternehmens zuständig.
                  Eine Liste aller deutschen Aufsichtsbehörden mit Kontaktdaten führt die Datenschutzkonferenz unter{' '}
                  <a
                    href="https://www.datenschutzkonferenz-online.de/datenschutzaufsichtsbehoerden.html"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 underline"
                  >
                    datenschutzkonferenz-online.de
                  </a>
                  .
                </p>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">7. SSL- und TLS-Verschlüsselung</h2>
              <div className="space-y-3 text-gray-700 text-sm leading-relaxed">
                <p>
                  Diese Website nutzt aus Sicherheitsgründen durchgehend eine TLS-Verschlüsselung. Sie erkennen
                  eine verschlüsselte Verbindung daran, dass die Adresszeile Ihres Browsers mit „https://" beginnt.
                  Daten, die Sie an uns übermitteln, können bei aktiver Verschlüsselung nicht von Dritten
                  mitgelesen werden.
                </p>
              </div>
            </section>
          </div>

          <div className="mt-8 bg-blue-50 rounded-xl p-6 text-center">
            <p className="text-gray-700 text-sm mb-3">Möchten Sie Ihre Daten verwalten oder löschen?</p>
            <Link
              href="/gdpr"
              className="inline-flex items-center gap-2 text-blue-600 hover:text-blue-700 font-semibold transition-colors"
            >
              <Shield className="w-5 h-5" />
              Zur DSGVO-Datenverwaltung
            </Link>
          </div>

          <div className="mt-8 text-center text-sm text-gray-600">
            <div className="flex justify-center gap-6">
              <Link href="/impressum" className="hover:text-blue-600 transition-colors">
                Impressum
              </Link>
              <Link href="/cookie-richtlinie" className="hover:text-blue-600 transition-colors">
                Cookie-Richtlinie
              </Link>
              <Link href="/agb" className="hover:text-blue-600 transition-colors">
                AGB
              </Link>
            </div>
          </div>
        </motion.div>
      </div>
    </main>
  );
}
