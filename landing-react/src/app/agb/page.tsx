'use client';

import React from 'react';
import { motion } from 'framer-motion';
import Link from 'next/link';
import { ArrowLeft, FileText } from 'lucide-react';

export default function AGBPage() {
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
              <FileText className="w-8 h-8 text-blue-600" />
              <h1 className="text-4xl font-bold text-gray-900">Allgemeine Geschäftsbedingungen</h1>
            </div>
            <p className="text-gray-600">Stand: {new Date().toLocaleDateString('de-DE', { year: 'numeric', month: 'long', day: 'numeric' })}</p>
          </div>

          <div className="bg-white rounded-xl shadow-lg p-8 space-y-8">
            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">1. Geltungsbereich</h2>
              <div className="space-y-3 text-gray-700 text-sm leading-relaxed">
                <p>
                  (1) Diese Allgemeinen Geschäftsbedingungen (nachfolgend "AGB") gelten für alle Verträge zwischen der Complyo GmbH, Musterstraße 123, 10115 Berlin (nachfolgend "Anbieter" oder "wir") und ihren Kunden (nachfolgend "Kunde" oder "Sie") über die Nutzung der von uns angebotenen Software-as-a-Service (SaaS) Leistungen zur Website-Compliance, Barrierefreiheit und Datenschutz.
                </p>
                <p>
                  (2) Abweichende, entgegenstehende oder ergänzende Allgemeine Geschäftsbedingungen des Kunden werden nicht Vertragsbestandteil, es sei denn, ihrer Geltung wird ausdrücklich schriftlich zugestimmt.
                </p>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">2. Vertragsgegenstand und Leistungen</h2>
              <div className="space-y-3 text-gray-700 text-sm leading-relaxed">
                <p>
                  (1) Der Anbieter stellt dem Kunden eine cloudbasierte Software-Plattform zur Verfügung, die folgende Leistungen umfasst:
                </p>
                <ul className="list-disc list-inside space-y-1 ml-4">
                  <li>Automatische Website-Scans zur Erkennung von Compliance-Problemen</li>
                  <li>KI-gestützte Analyse und Behebung von Barrierefreiheitsproblemen</li>
                  <li>Cookie-Compliance und DSGVO-Konformitätsprüfung</li>
                  <li>Automatische Fix-Generierung für erkannte Probleme</li>
                  <li>Monitoring und kontinuierliche Überwachung der Website-Compliance</li>
                </ul>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">3. Vertragsschluss</h2>
              <div className="space-y-3 text-gray-700 text-sm leading-relaxed">
                <p>
                  (1) Die Darstellung der Leistungen auf unserer Website stellt kein rechtlich bindendes Angebot dar, sondern eine unverbindliche Aufforderung zur Abgabe eines Angebots.
                </p>
                <p>
                  (2) Durch Anklicken des Buttons "Jetzt starten" gibt der Kunde ein verbindliches Angebot auf Abschluss eines Nutzungsvertrages ab.
                </p>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">4. Preise und Zahlungsbedingungen</h2>
              <div className="space-y-3 text-gray-700 text-sm leading-relaxed">
                <p>
                  (1) Die Preise für die Nutzung der Plattform richten sich nach der jeweils gültigen Preisliste auf unserer Website zum Zeitpunkt des Vertragsschlusses.
                </p>
                <p>
                  (2) Alle Preise verstehen sich in Euro und enthalten die gesetzliche Mehrwertsteuer.
                </p>
                <p>
                  (3) Die Zahlung erfolgt im Voraus für den jeweils gebuchten Abrechnungszeitraum (monatlich oder jährlich).
                </p>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">5. Nutzungsrechte und -pflichten</h2>
              <div className="space-y-3 text-gray-700 text-sm leading-relaxed">
                <p>
                  (1) Der Anbieter räumt dem Kunden das nicht-exklusive, nicht übertragbare, zeitlich auf die Vertragslaufzeit beschränkte Recht ein, die Plattform für die eigenen geschäftlichen Zwecke zu nutzen.
                </p>
                <p>
                  (2) Der Kunde verpflichtet sich, die Zugangsdaten geheim zu halten und Dritten keinen Zugang zu gewähren.
                </p>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">6. Datenschutz</h2>
              <div className="space-y-3 text-gray-700 text-sm leading-relaxed">
                <p>
                  (1) Der Anbieter verarbeitet personenbezogene Daten des Kunden im Rahmen der Vertragsdurchführung gemäß den Bestimmungen der Datenschutz-Grundverordnung (DSGVO).
                </p>
                <p>
                  (2) Die Datenerhebung und -verarbeitung erfolgt auf Grundlage von Art. 6 Abs. 1 lit. b DSGVO zur Erfüllung des Vertrages.
                </p>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">7. Kündigung</h2>
              <div className="space-y-3 text-gray-700 text-sm leading-relaxed">
                <p>
                  (1) Der Vertrag kann von beiden Seiten mit einer Frist von 30 Tagen zum Ende eines Abrechnungszeitraums gekündigt werden.
                </p>
                <p>
                  (2) Das Recht zur außerordentlichen Kündigung aus wichtigem Grund bleibt unberührt.
                </p>
              </div>
            </section>
          </div>

          <div className="mt-8 bg-blue-50 rounded-xl p-6">
            <h3 className="font-semibold text-gray-900 mb-3">Fragen zu den AGB?</h3>
            <p className="text-gray-700 text-sm">
              <strong>E-Mail:</strong>{' '}
              <a href="mailto:info@complyo.tech" className="text-blue-600 hover:underline">
                info@complyo.tech
              </a>
            </p>
          </div>

          <div className="mt-8 text-center text-sm text-gray-600">
            <div className="flex justify-center gap-6">
              <Link href="/impressum" className="hover:text-blue-600 transition-colors">
                Impressum
              </Link>
              <Link href="/datenschutz" className="hover:text-blue-600 transition-colors">
                Datenschutz
              </Link>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
