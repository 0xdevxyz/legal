'use client';

import React from 'react';
import { motion } from 'framer-motion';

/**
 * DSGVO-Betroffenenrechte — Wegweiser statt Formular.
 *
 * Das frühere Formular postete auf eine nicht existente Route (308→404),
 * und das Backend verlangt für Export/Löschung ohnehin ein Login (JWT,
 * Identitätsnachweis nach Art. 12 Abs. 6 DSGVO). Ein Formular, das nur
 * eine E-Mail-Adresse abfragt, wäre zudem ein IDOR-Einfallstor gewesen.
 * Deshalb: eingeloggte Kunden → Dashboard-Einstellungen; alle anderen →
 * E-Mail an datenschutz@complyo.de.
 */
export default function GDPRDataManagement() {
  const mailtoBetreff = encodeURIComponent('DSGVO-Anfrage (Auskunft / Löschung / Export)');
  const mailtoBody = encodeURIComponent(
    'Guten Tag,\n\n' +
    'ich möchte mein(e) Betroffenenrecht(e) nach DSGVO ausüben:\n' +
    '[ ] Auskunft (Art. 15)\n' +
    '[ ] Berichtigung (Art. 16)\n' +
    '[ ] Löschung (Art. 17)\n' +
    '[ ] Datenexport (Art. 20)\n\n' +
    'Die Anfrage bezieht sich auf folgende E-Mail-Adresse: \n\n' +
    'Mit freundlichen Grüßen'
  );

  return (
    <main id="inhalt" tabIndex={-1} className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <div className="container mx-auto px-4 py-12">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="max-w-4xl mx-auto"
        >
          {/* Header */}
          <div className="text-center mb-12">
            <h1 className="text-4xl font-bold text-gray-900 mb-4">
              🛡️ DSGVO Datenverwaltung
            </h1>
            <p className="text-xl text-gray-600">
              So üben Sie Ihre Rechte an Ihren personenbezogenen Daten aus
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-8">
            {/* Weg 1: Kunden mit Konto */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="bg-white rounded-xl shadow-lg p-8"
            >
              <div className="text-center mb-6">
                <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-2xl">🔐</span>
                </div>
                <h2 className="text-2xl font-semibold text-gray-900 mb-2">
                  Sie haben ein Complyo-Konto?
                </h2>
                <p className="text-gray-600">
                  Export und Löschantrag direkt im Dashboard
                </p>
              </div>

              <div className="space-y-4 mb-6">
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h3 className="font-semibold text-gray-900 mb-2">So geht&apos;s:</h3>
                  <ol className="text-sm text-gray-600 space-y-1 list-decimal list-inside">
                    <li>Im Dashboard anmelden</li>
                    <li>Einstellungen → Datenschutz öffnen</li>
                    <li>Daten als JSON exportieren (Art. 20) oder die Löschung Ihres Kontos beantragen (Art. 17)</li>
                  </ol>
                </div>

                <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
                  <p className="text-sm text-blue-800">
                    <strong>ℹ️ Hinweis:</strong> Löschanträge laufen zweistufig — nach
                    dem Antrag erhalten Sie eine Eingangs- und nach Ausführung eine
                    Löschbestätigung per E-Mail.
                  </p>
                </div>
              </div>

              <a
                href="https://app.complyo.de/settings"
                className="block w-full text-center bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-lg transition-colors duration-200"
              >
                🔐 Zu den Dashboard-Einstellungen
              </a>
            </motion.div>

            {/* Weg 2: Ohne Konto per E-Mail */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6, delay: 0.4 }}
              className="bg-white rounded-xl shadow-lg p-8"
            >
              <div className="text-center mb-6">
                <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-2xl">✉️</span>
                </div>
                <h3 className="text-2xl font-semibold text-gray-900 mb-2">
                  Kein Konto? Per E-Mail anfragen
                </h3>
                <p className="text-gray-600">
                  Für Interessenten, Report-Empfänger und alle anderen Anfragen
                </p>
              </div>

              <div className="space-y-4 mb-6">
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h4 className="font-semibold text-gray-900 mb-2">Was Sie anfragen können:</h4>
                  <ul className="text-sm text-gray-600 space-y-1">
                    <li>• Auskunft über gespeicherte Daten (Art. 15)</li>
                    <li>• Berichtigung unrichtiger Daten (Art. 16)</li>
                    <li>• Löschung Ihrer Daten (Art. 17)</li>
                    <li>• Export im JSON-Format (Art. 20)</li>
                  </ul>
                </div>

                <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-200">
                  <p className="text-sm text-yellow-800">
                    <strong>⚠️ Wichtig:</strong> Bitte schreiben Sie von der
                    E-Mail-Adresse, auf die sich Ihre Anfrage bezieht — so können
                    wir Ihre Identität prüfen (Art. 12 Abs. 6 DSGVO). Wir antworten
                    innerhalb von 30 Tagen.
                  </p>
                </div>
              </div>

              <a
                href={`mailto:datenschutz@complyo.de?subject=${mailtoBetreff}&body=${mailtoBody}`}
                className="block w-full text-center bg-green-700 hover:bg-green-800 text-white font-semibold py-3 px-6 rounded-lg transition-colors duration-200"
              >
                ✉️ E-Mail an datenschutz@complyo.de
              </a>
            </motion.div>
          </div>

          {/* GDPR Information Section */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.6 }}
            className="mt-12 bg-gray-50 rounded-xl p-8"
          >
            <h3 className="text-2xl font-semibold text-gray-900 mb-6 text-center">
              Ihre Rechte nach DSGVO
            </h3>

            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="text-center">
                <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-3">
                  <span className="text-xl">📋</span>
                </div>
                <h4 className="font-semibold text-gray-900 mb-2">Auskunft</h4>
                <p className="text-sm text-gray-600">Artikel 15 - Recht auf Auskunft</p>
              </div>

              <div className="text-center">
                <div className="w-12 h-12 bg-yellow-100 rounded-full flex items-center justify-center mx-auto mb-3">
                  <span className="text-xl">✏️</span>
                </div>
                <h4 className="font-semibold text-gray-900 mb-2">Berichtigung</h4>
                <p className="text-sm text-gray-600">Artikel 16 - Recht auf Berichtigung</p>
              </div>

              <div className="text-center">
                <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-3">
                  <span className="text-xl">🗑️</span>
                </div>
                <h4 className="font-semibold text-gray-900 mb-2">Löschung</h4>
                <p className="text-sm text-gray-600">Artikel 17 - Recht auf Löschung</p>
              </div>

              <div className="text-center">
                <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-3">
                  <span className="text-xl">📥</span>
                </div>
                <h4 className="font-semibold text-gray-900 mb-2">Portabilität</h4>
                <p className="text-sm text-gray-600">Artikel 20 - Datenübertragbarkeit</p>
              </div>
            </div>

            <div className="mt-8 text-center">
              <p className="text-gray-600">
                Aufbewahrungsfrist: 24 Monate ab Erhebung. Bei Fragen zu Ihren
                Datenschutzrechten wenden Sie sich an:
                <a href="mailto:datenschutz@complyo.de" className="text-blue-600 hover:underline ml-1">
                  datenschutz@complyo.de
                </a>
              </p>
            </div>
          </motion.div>
        </motion.div>
      </div>
    </main>
  );
}
