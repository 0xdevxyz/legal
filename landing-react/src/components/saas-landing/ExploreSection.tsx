'use client';
import React from 'react';
import { ShieldCheck, Cookie, Eye, FileText, Code2, Bell } from 'lucide-react';

const features = [
  {
    icon: ShieldCheck,
    color: 'blue',
    bg: 'bg-blue-50',
    iconColor: 'text-blue-600',
    title: 'DSGVO-Compliance Scan',
    description: 'Vollautomatische Prüfung aller datenschutzrechtlichen Anforderungen nach DSGVO – inklusive Datenschutzerklärung, Auftragsverarbeitung und Löschkonzepten.',
  },
  {
    icon: Cookie,
    color: 'orange',
    bg: 'bg-orange-50',
    iconColor: 'text-orange-600',
    title: 'Cookie Consent Manager',
    description: 'Rechtssicheres Cookie-Banner mit TCF 2.2 Unterstützung, automatischer Dienst-Erkennung und DSGVO-konformer Einwilligungsverwaltung.',
  },
  {
    icon: Eye,
    color: 'purple',
    bg: 'bg-purple-50',
    iconColor: 'text-purple-600',
    title: 'Barrierefreiheit WCAG 2.1',
    description: 'Umfassende Prüfung nach WCAG 2.1 Level AA. BFSG-konform ab 2025. KI-generierte Code-Fixes statt Overlay-Lösungen.',
  },
  {
    icon: FileText,
    color: 'green',
    bg: 'bg-green-50',
    iconColor: 'text-green-600',
    title: 'KI-generierte Rechtstexte',
    description: 'Individuelle Datenschutzerklärung, Impressum, AGB und Widerrufsbelehrung – automatisch erstellt und rechtlich stets aktuell.',
  },
  {
    icon: Code2,
    color: 'indigo',
    bg: 'bg-indigo-50',
    iconColor: 'text-indigo-600',
    title: 'Automatische Code-Fixes',
    description: 'KI analysiert Ihren Quellcode und liefert direkt einspielbare Fixes – keine manuellen Anpassungen, kein Agentur-Budget nötig.',
  },
  {
    icon: Bell,
    color: 'red',
    bg: 'bg-red-50',
    iconColor: 'text-red-600',
    title: 'Rechtliches Monitoring',
    description: 'Kontinuierliche Überwachung von Gesetzesänderungen. Automatische Benachrichtigungen bei neuen Anforderungen von BfDI, EDPB und LfDI.',
  },
];

export default function ExploreSection() {
  return (
    <section className="bg-gray-50 py-24" id="features">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-16">
          <p className="text-sm font-semibold text-blue-600 uppercase tracking-widest mb-3">Alle Möglichkeiten entdecken</p>
          <h2 className="font-heading text-3xl sm:text-4xl font-extrabold text-gray-900 mb-4">
            Explore the possibilities
          </h2>
          <p className="text-lg text-gray-500 max-w-2xl mx-auto">
            Complyo vereint alle rechtlichen Compliance-Anforderungen in einer Plattform – vollautomatisch, KI-gestützt und stets aktuell.
          </p>
        </div>

        {/* Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature, i) => (
            <div key={i} className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm hover:shadow-md transition-shadow group">
              <div className={`w-12 h-12 ${feature.bg} rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform`}>
                <feature.icon className={`w-6 h-6 ${feature.iconColor}`} />
              </div>
              <h3 className="font-heading text-base font-bold text-gray-900 mb-2">{feature.title}</h3>
              <p className="text-sm text-gray-500 leading-relaxed">{feature.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
