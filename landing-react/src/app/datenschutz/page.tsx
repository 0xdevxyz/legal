'use client';

import React from 'react';
import { motion } from 'framer-motion';
import Link from 'next/link';
import { ArrowLeft, Shield, Mail } from 'lucide-react';

export default function DatenschutzPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-blue-50">
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

          <div className="bg-white rounded-xl shadow-lg p-8 mb-8">
            <div className="flex items-center gap-3 mb-4">
              <Shield className="w-8 h-8 text-blue-600" />
              <h1 className="text-4xl font-bold text-gray-900">Datenschutzerklärung</h1>
            </div>
            <p className="text-gray-600">Stand: {new Date().toLocaleDateString('de-DE', { year: 'numeric', month: 'long', day: 'numeric' })}</p>
          </div>

          <div className="bg-white rounded-xl shadow-lg p-8 space-y-8">
            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">1. Datenschutz auf einen Blick</h2>
              <div className="space-y-4 text-gray-700 text-sm leading-relaxed">
                <div>
                  <h3 className="font-semibold mb-2">Allgemeine Hinweise</h3>
                  <p>
                    Die folgenden Hinweise geben einen einfachen Überblick darüber, was mit Ihren personenbezogenen Daten passiert, wenn Sie diese Website besuchen. Personenbezogene Daten sind alle Daten, mit denen Sie persönlich identifiziert werden können.
                  </p>
                </div>
                <div>
                  <h3 className="font-semibold mb-2">Datenerfassung auf dieser Website</h3>
                  <p className="font-semibold mb-2">Wer ist verantwortlich für die Datenerfassung auf dieser Website?</p>
                  <p>
                    Die Datenverarbeitung auf dieser Website erfolgt durch den Websitebetreiber. Dessen Kontaktdaten können Sie dem Abschnitt „Hinweis zur Verantwortlichen Stelle" in dieser Datenschutzerklärung entnehmen.
                  </p>
                </div>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">2. Hinweis zur verantwortlichen Stelle</h2>
              <div className="space-y-3 text-gray-700 text-sm leading-relaxed">
                <p className="font-semibold">Die verantwortliche Stelle für die Datenverarbeitung auf dieser Website ist:</p>
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="font-semibold">Complyo GmbH</p>
                  <p>Musterstraße 123</p>
                  <p>10115 Berlin</p>
                  <p>Deutschland</p>
                  <p className="mt-3">
                    Telefon: <a href="tel:+49301234567" className="text-blue-600 hover:underline">+49 (0) 30 1234567</a>
                  </p>
                  <p>
                    E-Mail: <a href="mailto:datenschutz@complyo.tech" className="text-blue-600 hover:underline">datenschutz@complyo.tech</a>
                  </p>
                </div>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">3. Datenerfassung auf dieser Website</h2>
              <div className="space-y-6 text-gray-700 text-sm leading-relaxed">
                <div>
                  <h3 className="font-semibold mb-2">Cookies</h3>
                  <p>
                    Unsere Internetseiten verwenden so genannte „Cookies". Cookies sind kleine Textdateien und richten auf Ihrem Endgerät keinen Schaden an. Sie werden entweder vorübergehend für die Dauer einer Sitzung (Session-Cookies) oder dauerhaft (dauerhafte Cookies) auf Ihrem Endgerät gespeichert.
                  </p>
                </div>
                <div>
                  <h3 className="font-semibold mb-2">Server-Log-Dateien</h3>
                  <p>
                    Der Provider der Seiten erhebt und speichert automatisch Informationen in so genannten Server-Log-Dateien, die Ihr Browser automatisch an uns übermittelt. Dies sind Browsertyp, Betriebssystem, Referrer URL, Hostname, Uhrzeit der Serveranfrage und IP-Adresse.
                  </p>
                </div>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">4. Ihre Rechte</h2>
              <div className="space-y-4 text-gray-700 text-sm leading-relaxed">
                <p>Sie haben folgende Rechte:</p>
                <ul className="list-disc list-inside space-y-2 ml-4">
                  <li><strong>Recht auf Auskunft (Art. 15 DSGVO)</strong></li>
                  <li><strong>Recht auf Berichtigung (Art. 16 DSGVO)</strong></li>
                  <li><strong>Recht auf Löschung (Art. 17 DSGVO)</strong></li>
                  <li><strong>Recht auf Einschränkung der Verarbeitung (Art. 18 DSGVO)</strong></li>
                  <li><strong>Recht auf Datenübertragbarkeit (Art. 20 DSGVO)</strong></li>
                  <li><strong>Widerspruchsrecht (Art. 21 DSGVO)</strong></li>
                  <li><strong>Widerruf Ihrer Einwilligung (Art. 7 Abs. 3 DSGVO)</strong></li>
                </ul>
                <div className="bg-blue-50 p-4 rounded-lg mt-4">
                  <p>
                    <strong>E-Mail:</strong>{' '}
                    <a href="mailto:datenschutz@complyo.tech" className="text-blue-600 hover:underline">
                      datenschutz@complyo.tech
                    </a>
                  </p>
                </div>
              </div>
            </section>
          </div>

          <div className="mt-8 bg-blue-50 rounded-xl p-6 text-center">
            <p className="text-gray-700 text-sm mb-3">
              Möchten Sie Ihre Daten verwalten oder löschen?
            </p>
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
              <Link href="/agb" className="hover:text-blue-600 transition-colors">
                AGB
              </Link>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
