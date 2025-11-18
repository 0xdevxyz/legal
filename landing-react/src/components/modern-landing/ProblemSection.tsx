'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { AlertTriangle, Euro, Scale, Users, TrendingDown, Shield } from 'lucide-react';

/**
 * ProblemSection - Zeigt die Risiken und Probleme auf (Pain Points)
 * Nutzt das Problem-Agitate-Solve Pattern für höhere Conversion
 */
export default function ProblemSection() {
  const risks = [
    {
      icon: Euro,
      title: 'Bis zu 50.000€ Bußgeld',
      description: 'Verstöße gegen die Barrierefreiheitspflicht können richtig teuer werden.',
      color: 'from-red-500 to-orange-500',
    },
    {
      icon: Scale,
      title: 'Abmahnungen & Klagen',
      description: 'Anwaltskanzleien prüfen gezielt Websites auf Verstöße.',
      color: 'from-orange-500 to-yellow-500',
    },
    {
      icon: TrendingDown,
      title: 'Umsatzverlust',
      description: '15% der Bevölkerung haben eine Behinderung – das sind verlorene Kunden.',
      color: 'from-purple-500 to-pink-500',
    },
    {
      icon: Users,
      title: 'Imageschaden',
      description: 'Mangelnde Barrierefreiheit schadet Ihrem Unternehmensimage.',
      color: 'from-blue-500 to-indigo-500',
    },
  ];

  const solutions = [
    {
      title: 'Automatische Problemerkennung',
      description: 'Complyo scannt Ihre Website und findet alle Barrieren – vollautomatisch.',
    },
    {
      title: 'KI-generierte Lösungen',
      description: 'Unsere KI erstellt sofort umsetzbare Fixes. Kein Tech-Wissen nötig.',
    },
    {
      title: 'Rechtssichere Dokumentation',
      description: 'Perfekt für Behörden und Audits. Zeigen Sie, dass Sie compliant sind.',
    },
  ];

  return (
    <>
      {/* Problem Section - Dunkel, dramatisch */}
      <section className="bg-gradient-to-br from-gray-900 via-red-900 to-gray-900 py-24 relative overflow-hidden">
        {/* Background Pattern */}
        <div className="absolute inset-0 opacity-10">
          <div
            className="absolute inset-0"
            style={{
              backgroundImage:
                'radial-gradient(circle at 2px 2px, white 1px, transparent 0)',
              backgroundSize: '40px 40px',
            }}
          />
        </div>

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <div className="inline-flex items-center gap-2 bg-red-500/20 border border-red-500 rounded-full px-5 py-2 mb-6">
              <AlertTriangle className="w-5 h-5 text-red-400" />
              <span className="text-red-400 font-semibold">Achtung: Diese Risiken drohen Ihnen</span>
            </div>

            <h2 className="text-4xl sm:text-5xl font-bold text-white mb-4">
              Ist Ihre Website{' '}
              <span className="bg-gradient-to-r from-red-400 to-orange-400 bg-clip-text text-transparent">
                nicht barrierefrei?
              </span>
            </h2>
            <p className="text-xl text-gray-300 max-w-3xl mx-auto">
              Seit 2025 gilt das Barrierefreiheitsstärkungsgesetz (BFSG) auch für{' '}
              <strong className="text-white">private Unternehmen.</strong> Das kann teuer werden!
            </p>
          </motion.div>

          {/* Risks Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {risks.map((risk, idx) => {
              const Icon = risk.icon;
              return (
                <motion.div
                  key={idx}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: idx * 0.1 }}
                  whileHover={{ y: -5 }}
                  className="bg-white/10 backdrop-blur-sm border border-white/20 rounded-2xl p-6 hover:bg-white/15 transition-all"
                >
                  <div
                    className={`w-14 h-14 rounded-xl bg-gradient-to-r ${risk.color} flex items-center justify-center mb-4 shadow-lg`}
                  >
                    <Icon className="w-7 h-7 text-white" />
                  </div>
                  <h3 className="text-xl font-bold text-white mb-2">{risk.title}</h3>
                  <p className="text-gray-300 text-sm leading-relaxed">
                    {risk.description}
                  </p>
                </motion.div>
              );
            })}
          </div>

          {/* Urgency Banner */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            className="mt-12 bg-gradient-to-r from-red-600 to-orange-600 rounded-2xl p-8 text-center shadow-2xl"
          >
            <p className="text-2xl font-bold text-white mb-2">
              ⏰ Handeln Sie JETZT – bevor es zu spät ist!
            </p>
            <p className="text-red-100">
              Die ersten Abmahnungen sind bereits unterwegs. Schützen Sie Ihr Unternehmen.
            </p>
          </motion.div>
        </div>
      </section>

      {/* Solution Section - Hell, positiv */}
      <section className="bg-gradient-to-br from-green-50 via-blue-50 to-purple-50 py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <div className="inline-flex items-center gap-2 bg-green-100 border border-green-300 rounded-full px-5 py-2 mb-6">
              <Shield className="w-5 h-5 text-green-600" />
              <span className="text-green-700 font-semibold">Die Lösung: Complyo</span>
            </div>

            <h2 className="text-4xl sm:text-5xl font-bold text-gray-900 mb-4">
              So einfach schützen Sie sich
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Complyo macht Barrierefreiheit{' '}
              <strong>kinderleicht – auch ohne technisches Wissen.</strong>
            </p>
          </motion.div>

          {/* Solutions Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-12">
            {solutions.map((solution, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: idx * 0.1 }}
                className="bg-white rounded-2xl p-8 shadow-lg border-2 border-green-200 hover:shadow-xl transition-all"
              >
                <div className="text-4xl mb-4">
                  {idx === 0 ? '🔍' : idx === 1 ? '🤖' : '📋'}
                </div>
                <h3 className="text-xl font-bold text-gray-900 mb-3">
                  {solution.title}
                </h3>
                <p className="text-gray-600 leading-relaxed">{solution.description}</p>
              </motion.div>
            ))}
          </div>

          {/* Process Steps */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="bg-white rounded-2xl p-12 shadow-xl border border-gray-200"
          >
            <h3 className="text-2xl font-bold text-center text-gray-900 mb-10">
              🚀 So funktioniert's – in 3 einfachen Schritten
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <div className="text-center">
                <div className="w-16 h-16 bg-gradient-to-r from-blue-600 to-purple-600 rounded-full flex items-center justify-center text-white text-2xl font-bold mx-auto mb-4 shadow-lg">
                  1
                </div>
                <h4 className="font-bold text-lg mb-2">Website scannen</h4>
                <p className="text-gray-600 text-sm">
                  Geben Sie Ihre URL ein. Complyo findet alle Probleme in Sekunden.
                </p>
              </div>

              <div className="text-center">
                <div className="w-16 h-16 bg-gradient-to-r from-purple-600 to-pink-600 rounded-full flex items-center justify-center text-white text-2xl font-bold mx-auto mb-4 shadow-lg">
                  2
                </div>
                <h4 className="font-bold text-lg mb-2">Lösungen erhalten</h4>
                <p className="text-gray-600 text-sm">
                  KI erstellt sofort Fixes. Entweder selbst umsetzen oder Experten machen lassen.
                </p>
              </div>

              <div className="text-center">
                <div className="w-16 h-16 bg-gradient-to-r from-pink-600 to-red-600 rounded-full flex items-center justify-center text-white text-2xl font-bold mx-auto mb-4 shadow-lg">
                  3
                </div>
                <h4 className="font-bold text-lg mb-2">Geschützt sein</h4>
                <p className="text-gray-600 text-sm">
                  Automatisches Monitoring warnt Sie vor neuen Problemen. Immer compliant!
                </p>
              </div>
            </div>
          </motion.div>
        </div>
      </section>
    </>
  );
}

