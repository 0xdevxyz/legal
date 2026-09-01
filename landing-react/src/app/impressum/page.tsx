'use client';

import React from 'react';
import { motion } from 'framer-motion';
import Link from 'next/link';
import { ArrowLeft, Mail, MapPin, Phone, AlertTriangle, Receipt, User } from 'lucide-react';

/**
 * Angaben nach § 5 DDG.
 *
 * Hier standen bis zum 01.09.2026 Platzhalter: "Complyo GmbH", "Musterstraße 123",
 * "Max Mustermann", eine erfundene Handelsregisternummer und eine erfundene
 * USt-IdNr. Das war nicht nur ein Verstoß gegen § 5 DDG auf der Verkaufsseite
 * eines Compliance-Anbieters. Schwerer wog die Firmierung als GmbH: wer unter
 * einer nicht existierenden Kapitalgesellschaft auftritt, haftet nach den
 * Grundsätzen der Rechtsscheinhaftung persönlich, also genau umgekehrt zur
 * Absicht einer Haftungsbeschränkung.
 *
 * complyo wird als Einzelunternehmen betrieben. Damit ist der Vor- und Nachname
 * der natürlichen Person Pflichtangabe (§ 5 Abs. 1 Nr. 1 DDG); die
 * Geschäftsbezeichnung "Complyo" allein genügt nicht.
 *
 * NICHT VERÖFFENTLICHEN, solange unten Felder leer sind. Die Seite weist
 * absichtlich sichtbar darauf hin, statt still etwas Falsches zu behaupten.
 */
const ANBIETER = {
  // Vor- und Nachname der natürlichen Person. Pflichtangabe.
  name: '',
  geschaeftsbezeichnung: 'Complyo',
  strasse: 'Pappelallee 64',
  plz: '10437',
  ort: 'Berlin',
  land: 'Deutschland',
  email: 'info@complyo.de',
  // Zweiter Kommunikationsweg neben der E-Mail. Optional, aber üblich.
  telefon: '',
  // Pflichtangabe, sobald vorhanden (§ 5 Abs. 1 Nr. 6 DDG).
  ustIdNr: 'DE405368946',
};

const PFLICHTFELDER_FEHLEN = !ANBIETER.name || !ANBIETER.ustIdNr;

export default function ImpressumPage() {
  const anschrift = ANBIETER.plz + ' ' + ANBIETER.ort;

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

          {PFLICHTFELDER_FEHLEN && (
            <div className="bg-red-50 border-2 border-red-400 rounded-xl p-6 mb-8">
              <div className="flex items-start gap-3">
                <AlertTriangle className="w-6 h-6 text-red-600 flex-shrink-0 mt-0.5" />
                <div>
                  <h2 className="text-lg font-bold text-red-900 mb-1">Diese Seite ist unvollständig</h2>
                  <p className="text-sm text-red-800">
                    Es fehlen Pflichtangaben nach § 5 DDG. Die Seite darf in diesem Zustand nicht
                    öffentlich erreichbar sein. Die fehlenden Werte stehen als leere Felder in
                    <code className="mx-1 px-1.5 py-0.5 bg-red-100 rounded text-xs">ANBIETER</code>
                    am Anfang dieser Datei.
                  </p>
                </div>
              </div>
            </div>
          )}

          <div className="bg-white rounded-xl shadow-lg p-8 mb-8">
            <h1 className="text-4xl font-bold text-gray-900 mb-4">Impressum</h1>
            <p className="text-gray-600">Angaben gemäß § 5 DDG</p>
          </div>

          <div className="bg-white rounded-xl shadow-lg p-8 space-y-8">
            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">Anbieter</h2>
              <div className="flex items-start gap-3 text-gray-700">
                <MapPin className="w-5 h-5 text-blue-600 mt-1 flex-shrink-0" />
                <div>
                  <p className="font-semibold">{ANBIETER.name || 'Name fehlt'}</p>
                  <p className="text-gray-600">{ANBIETER.geschaeftsbezeichnung}</p>
                  <p className="mt-2">{ANBIETER.strasse}</p>
                  <p>{anschrift}</p>
                  <p>{ANBIETER.land}</p>
                </div>
              </div>
              <p className="text-sm text-gray-500 mt-4">
                Einzelunternehmen. Eine Eintragung im Handelsregister besteht nicht.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">Kontakt</h2>
              <div className="space-y-3 text-gray-700">
                <div className="flex items-center gap-3">
                  <Mail className="w-5 h-5 text-blue-600 flex-shrink-0" />
                  <a href={'mailto:' + ANBIETER.email} className="hover:text-blue-600 transition-colors">
                    {ANBIETER.email}
                  </a>
                </div>
                {ANBIETER.telefon && (
                  <div className="flex items-center gap-3">
                    <Phone className="w-5 h-5 text-blue-600 flex-shrink-0" />
                    <a href={'tel:' + ANBIETER.telefon.replace(/[^+0-9]/g, '')} className="hover:text-blue-600 transition-colors">
                      {ANBIETER.telefon}
                    </a>
                  </div>
                )}
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">Umsatzsteuer</h2>
              <div className="flex items-start gap-3 text-gray-700">
                <Receipt className="w-5 h-5 text-blue-600 mt-1 flex-shrink-0" />
                <p>
                  Umsatzsteuer-Identifikationsnummer gemäß § 27a UStG:{' '}
                  <span className="font-medium">{ANBIETER.ustIdNr || 'fehlt'}</span>
                </p>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">
                Verantwortlich für den Inhalt nach § 18 Abs. 2 MStV
              </h2>
              <div className="flex items-start gap-3 text-gray-700">
                <User className="w-5 h-5 text-blue-600 mt-1 flex-shrink-0" />
                <div>
                  <p>{ANBIETER.name || 'Name fehlt'}</p>
                  <p>{ANBIETER.strasse}</p>
                  <p>{anschrift}</p>
                </div>
              </div>
              <p className="text-sm text-gray-500 mt-4">
                Gilt für die redaktionellen Beiträge im{' '}
                <Link href="/ratgeber" className="text-blue-600 hover:underline">Ratgeber</Link>.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">Streitbeilegung</h2>
              <p className="text-gray-700 text-sm leading-relaxed">
                complyo schließt Verträge ausschließlich mit Unternehmern im Sinne des § 14 BGB.
                Verbraucherschlichtungsverfahren nach dem VSBG kommen daher nicht in Betracht.
                Zur Teilnahme an einem Streitbeilegungsverfahren vor einer Verbraucherschlichtungs&shy;stelle
                sind wir weder verpflichtet noch bereit.
              </p>
            </section>
          </div>

          <div className="mt-8 text-center text-sm text-gray-600">
            <div className="flex justify-center gap-6">
              <Link href="/agb" className="hover:text-blue-600 transition-colors">AGB</Link>
              <Link href="/datenschutz" className="hover:text-blue-600 transition-colors">Datenschutz</Link>
            </div>
          </div>
        </motion.div>
      </div>
    </main>
  );
}
