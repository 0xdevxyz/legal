'use client';

import React from 'react';
import { motion } from 'framer-motion';
import Link from 'next/link';
import { ArrowLeft, Mail, MapPin, Phone, Globe } from 'lucide-react';

export default function ImpressumPage() {
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
            <h1 className="text-4xl font-bold text-gray-900 mb-4">Impressum</h1>
            <p className="text-gray-600">Angaben gemäß § 5 TMG</p>
          </div>

          <div className="bg-white rounded-xl shadow-lg p-8 space-y-8">
            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">Verantwortlich für den Inhalt</h2>
              <div className="space-y-3 text-gray-700">
                <div className="flex items-start gap-3">
                  <MapPin className="w-5 h-5 text-blue-600 mt-1 flex-shrink-0" />
                  <div>
                    <p className="font-semibold">Complyo GmbH</p>
                    <p>Musterstraße 123</p>
                    <p>10115 Berlin</p>
                    <p>Deutschland</p>
                  </div>
                </div>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">Kontakt</h2>
              <div className="space-y-3 text-gray-700">
                <div className="flex items-center gap-3">
                  <Phone className="w-5 h-5 text-blue-600 flex-shrink-0" />
                  <a href="tel:+49301234567" className="hover:text-blue-600 transition-colors">
                    +49 (0) 30 1234567
                  </a>
                </div>
                <div className="flex items-center gap-3">
                  <Mail className="w-5 h-5 text-blue-600 flex-shrink-0" />
                  <a href="mailto:info@complyo.tech" className="hover:text-blue-600 transition-colors">
                    info@complyo.tech
                  </a>
                </div>
                <div className="flex items-center gap-3">
                  <Globe className="w-5 h-5 text-blue-600 flex-shrink-0" />
                  <a href="https://complyo.tech" target="_blank" rel="noopener noreferrer" className="hover:text-blue-600 transition-colors">
                    www.complyo.tech
                  </a>
                </div>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">Rechtliche Angaben</h2>
              <div className="space-y-4 text-gray-700">
                <div>
                  <p className="font-semibold mb-2">Handelsregister:</p>
                  <p>HRB 123456 B</p>
                  <p className="text-sm text-gray-600">Registergericht: Amtsgericht Berlin-Charlottenburg</p>
                </div>
                <div>
                  <p className="font-semibold mb-2">Umsatzsteuer-ID:</p>
                  <p>DE123456789</p>
                  <p className="text-sm text-gray-600">gemäß § 27 a Umsatzsteuergesetz</p>
                </div>
                <div>
                  <p className="font-semibold mb-2">Geschäftsführer:</p>
                  <p>Max Mustermann</p>
                </div>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">Haftungsausschluss</h2>
              <div className="space-y-4 text-gray-700">
                <div>
                  <h3 className="font-semibold mb-2">Haftung für Inhalte</h3>
                  <p className="text-sm leading-relaxed">
                    Als Diensteanbieter sind wir gemäß § 7 Abs.1 TMG für eigene Inhalte auf diesen Seiten nach den allgemeinen Gesetzen verantwortlich. Nach §§ 8 bis 10 TMG sind wir als Diensteanbieter jedoch nicht verpflichtet, übermittelte oder gespeicherte fremde Informationen zu überwachen oder nach Umständen zu forschen, die auf eine rechtswidrige Tätigkeit hinweisen.
                  </p>
                </div>
                <div>
                  <h3 className="font-semibold mb-2">Haftung für Links</h3>
                  <p className="text-sm leading-relaxed">
                    Unser Angebot enthält Links zu externen Websites Dritter, auf deren Inhalte wir keinen Einfluss haben. Deshalb können wir für diese fremden Inhalte auch keine Gewähr übernehmen. Für die Inhalte der verlinkten Seiten ist stets der jeweilige Anbieter oder Betreiber der Seiten verantwortlich.
                  </p>
                </div>
                <div>
                  <h3 className="font-semibold mb-2">Urheberrecht</h3>
                  <p className="text-sm leading-relaxed">
                    Die durch die Seitenbetreiber erstellten Inhalte und Werke auf diesen Seiten unterliegen dem deutschen Urheberrecht. Die Vervielfältigung, Bearbeitung, Verbreitung und jede Art der Verwertung außerhalb der Grenzen des Urheberrechtes bedürfen der schriftlichen Zustimmung des jeweiligen Autors bzw. Erstellers.
                  </p>
                </div>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">EU-Streitschlichtung</h2>
              <p className="text-gray-700 text-sm leading-relaxed">
                Die Europäische Kommission stellt eine Plattform zur Online-Streitbeilegung (OS) bereit: 
                <a 
                  href="https://ec.europa.eu/consumers/odr/" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:underline ml-1"
                >
                  https://ec.europa.eu/consumers/odr/
                </a>
                <br />
                Unsere E-Mail-Adresse finden Sie oben im Impressum.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">Verbraucherstreitbeilegung / Universalschlichtungsstelle</h2>
              <p className="text-gray-700 text-sm leading-relaxed">
                Wir sind nicht bereit oder verpflichtet, an Streitbeilegungsverfahren vor einer Verbraucherschlichtungsstelle teilzunehmen.
              </p>
            </section>
          </div>

          <div className="mt-8 text-center text-sm text-gray-600">
            <div className="flex justify-center gap-6">
              <Link href="/datenschutz" className="hover:text-blue-600 transition-colors">
                Datenschutz
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
