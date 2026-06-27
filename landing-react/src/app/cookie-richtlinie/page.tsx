'use client';

import React from 'react';
import { motion } from 'framer-motion';
import Link from 'next/link';
import { ArrowLeft, Cookie, Mail, Settings } from 'lucide-react';

export default function CookieRichtliniePage() {
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
              <Cookie className="w-8 h-8 text-yellow-500" />
              <h1 className="text-4xl font-bold text-gray-900">Cookie-Richtlinie</h1>
            </div>
            <p className="text-gray-600">
              Stand: {new Date().toLocaleDateString('de-DE', { year: 'numeric', month: 'long', day: 'numeric' })}
            </p>
          </div>

          <div className="bg-white rounded-xl shadow-lg p-8 space-y-8">
            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">1. Was sind Cookies?</h2>
              <div className="space-y-4 text-gray-700 text-sm leading-relaxed">
                <p>
                  Cookies sind kleine Textdateien, die beim Besuch einer Website auf Ihrem Endgerät gespeichert
                  und beim erneuten Aufruf wieder ausgelesen werden können. Sie dienen unterschiedlichen Zwecken,
                  etwa der Aufrechterhaltung grundlegender Funktionen, der Speicherung Ihrer Einstellungen oder
                  der Erhebung statistischer Daten.
                </p>
                <p>
                  Neben klassischen HTTP-Cookies setzen wir auch ähnliche Technologien wie den lokalen Speicher
                  (Local Storage) Ihres Browsers ein. Im Folgenden fassen wir alle diese Technologien unter dem
                  Begriff „Cookies" zusammen.
                </p>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">2. Rechtsgrundlage</h2>
              <div className="space-y-4 text-gray-700 text-sm leading-relaxed">
                <p>
                  Das Speichern und Auslesen von Cookies ist nach § 25 TDDDG nur mit Ihrer Einwilligung zulässig,
                  es sei denn, der Zugriff ist unbedingt erforderlich, um einen von Ihnen ausdrücklich gewünschten
                  Dienst bereitzustellen. Für technisch notwendige Cookies ist daher keine Einwilligung erforderlich
                  (Art. 6 Abs. 1 lit. f DSGVO – berechtigtes Interesse).
                </p>
                <p>
                  Alle übrigen Cookies (Analyse- und Marketing-Cookies) setzen wir ausschließlich auf Grundlage
                  Ihrer Einwilligung (Art. 6 Abs. 1 lit. a DSGVO) ein, die Sie über unser Cookie-Banner erteilen
                  und jederzeit widerrufen können.
                </p>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">3. Welche Arten von Cookies gibt es?</h2>
              <div className="space-y-3 text-gray-700 text-sm leading-relaxed">
                <p>
                  <strong>Technisch notwendige Cookies</strong> ermöglichen grundlegende Funktionen der Website,
                  etwa das Speichern Ihrer Cookie-Einwilligung. Ohne sie funktioniert die Website nicht
                  ordnungsgemäß.
                </p>
                <p>
                  <strong>Analyse-/Statistik-Cookies</strong> helfen uns zu verstehen, wie Besucher unsere Website
                  nutzen, damit wir Inhalte und Nutzererfahrung verbessern können.
                </p>
                <p>
                  <strong>Marketing-Cookies</strong> werden eingesetzt, um Nutzerverhalten website-übergreifend
                  nachzuvollziehen und personalisierte Werbung auszuspielen.
                </p>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">4. Welche Cookies verwenden wir?</h2>
              <p className="text-gray-700 text-sm leading-relaxed mb-4">
                Die folgende Übersicht zeigt die auf dieser Website eingesetzten Cookies. Analyse- und
                Marketing-Cookies werden ausschließlich nach Ihrer Einwilligung gesetzt.
              </p>

              <h3 className="font-semibold text-gray-900 mb-2">Technisch notwendig</h3>
              <div className="overflow-x-auto mb-6">
                <table className="w-full text-xs text-left text-gray-700 border border-gray-200 rounded-lg">
                  <thead className="bg-gray-50 text-gray-900">
                    <tr>
                      <th className="px-3 py-2 font-semibold">Name</th>
                      <th className="px-3 py-2 font-semibold">Typ</th>
                      <th className="px-3 py-2 font-semibold">Speicherdauer</th>
                      <th className="px-3 py-2 font-semibold">Zweck</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    <tr>
                      <td className="px-3 py-2 font-mono">cookie-consent</td>
                      <td className="px-3 py-2">Local Storage</td>
                      <td className="px-3 py-2">unbefristet (bis zur Löschung)</td>
                      <td className="px-3 py-2">Speichert Ihre Auswahl im Cookie-Banner (welche Kategorien Sie zugelassen haben).</td>
                    </tr>
                    <tr>
                      <td className="px-3 py-2 font-mono">cookie-consent-date</td>
                      <td className="px-3 py-2">Local Storage</td>
                      <td className="px-3 py-2">unbefristet (bis zur Löschung)</td>
                      <td className="px-3 py-2">Speichert den Zeitpunkt Ihrer Einwilligung als Nachweis.</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <h3 className="font-semibold text-gray-900 mb-2">Analyse / Statistik (nur mit Einwilligung)</h3>
              <div className="overflow-x-auto mb-6">
                <table className="w-full text-xs text-left text-gray-700 border border-gray-200 rounded-lg">
                  <thead className="bg-gray-50 text-gray-900">
                    <tr>
                      <th className="px-3 py-2 font-semibold">Anbieter</th>
                      <th className="px-3 py-2 font-semibold">Zweck</th>
                      <th className="px-3 py-2 font-semibold">Rechtsgrundlage</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    <tr>
                      <td className="px-3 py-2">Reichweiten- und Nutzungsanalyse</td>
                      <td className="px-3 py-2">Statistische Auswertung der Website-Nutzung zur Optimierung unseres Angebots.</td>
                      <td className="px-3 py-2">Art. 6 Abs. 1 lit. a DSGVO (Einwilligung)</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <h3 className="font-semibold text-gray-900 mb-2">Marketing (nur mit Einwilligung)</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left text-gray-700 border border-gray-200 rounded-lg">
                  <thead className="bg-gray-50 text-gray-900">
                    <tr>
                      <th className="px-3 py-2 font-semibold">Anbieter</th>
                      <th className="px-3 py-2 font-semibold">Zweck</th>
                      <th className="px-3 py-2 font-semibold">Rechtsgrundlage</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    <tr>
                      <td className="px-3 py-2">Marketing- und Retargeting-Dienste</td>
                      <td className="px-3 py-2">Ausspielung personalisierter Werbung und Messung von Werbeerfolg.</td>
                      <td className="px-3 py-2">Art. 6 Abs. 1 lit. a DSGVO (Einwilligung)</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">5. Einwilligung verwalten und widerrufen</h2>
              <div className="space-y-4 text-gray-700 text-sm leading-relaxed">
                <p>
                  Sie können Ihre Cookie-Einstellungen jederzeit ändern oder Ihre Einwilligung widerrufen. Löschen
                  Sie dazu die gespeicherte Einwilligung (z. B. durch Leeren der Website-Daten in Ihrem Browser);
                  beim nächsten Besuch erscheint das Cookie-Banner erneut und Sie können Ihre Auswahl anpassen.
                </p>
                <div className="bg-blue-50 p-4 rounded-lg flex items-start gap-3">
                  <Settings className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
                  <p>
                    Zusätzlich können Sie in den Einstellungen Ihres Browsers das Speichern von Cookies generell
                    einschränken oder blockieren. Bitte beachten Sie, dass dann möglicherweise nicht alle Funktionen
                    dieser Website vollständig nutzbar sind.
                  </p>
                </div>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">6. Ihre Rechte</h2>
              <div className="space-y-4 text-gray-700 text-sm leading-relaxed">
                <p>
                  Ihnen stehen die Rechte aus der DSGVO zu, insbesondere auf Auskunft (Art. 15), Berichtigung
                  (Art. 16), Löschung (Art. 17), Einschränkung der Verarbeitung (Art. 18), Datenübertragbarkeit
                  (Art. 20) sowie das Widerspruchsrecht (Art. 21) und der Widerruf einer erteilten Einwilligung
                  (Art. 7 Abs. 3). Weitere Informationen finden Sie in unserer{' '}
                  <Link href="/datenschutz" className="text-blue-600 hover:underline">Datenschutzerklärung</Link>.
                </p>
                <div className="bg-blue-50 p-4 rounded-lg flex items-center gap-3">
                  <Mail className="w-5 h-5 text-blue-600 flex-shrink-0" />
                  <p>
                    <strong>Kontakt:</strong>{' '}
                    <a href="mailto:datenschutz@complyo.de" className="text-blue-600 hover:underline">
                      datenschutz@complyo.de
                    </a>
                  </p>
                </div>
              </div>
            </section>
          </div>

          <div className="mt-8 text-center text-sm text-gray-600">
            <div className="flex justify-center gap-6">
              <Link href="/datenschutz" className="hover:text-blue-600 transition-colors">
                Datenschutz
              </Link>
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
