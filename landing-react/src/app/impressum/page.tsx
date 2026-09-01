'use client';

import React from 'react';
import { motion } from 'framer-motion';
import Link from 'next/link';
import { ArrowLeft, Mail, MapPin, Phone, Receipt, User } from 'lucide-react';
import { ANBIETER } from '@/lib/anbieter';
import AnbieterUnvollstaendig from '@/components/legal/AnbieterUnvollstaendig';

/**
 * Angaben nach § 5 DDG.
 *
 * Die Anbieterdaten stehen seit dem 01.09.2026 in @/lib/anbieter und werden von
 * Impressum, AGB und Datenschutzerklaerung gemeinsam benutzt. Vorher trug jede
 * der drei Seiten ihren eigenen Satz Platzhalter, und nur diese hier wurde
 * gepflegt.
 */
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

          <AnbieterUnvollstaendig seite="Das Impressum" />

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
