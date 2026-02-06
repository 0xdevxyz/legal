'use client';

import React from 'react';
import { motion } from 'framer-motion';
import {
  Sparkles,
  Search,
  Code2,
  Shield,
  Zap,
  Users,
  BarChart3,
  Globe,
  Wand2,
  FileCheck,
  Bell,
  Euro,
} from 'lucide-react';

/**
 * FeaturesShowcase - Hauptfunktionen präsentieren
 */
export default function FeaturesShowcase() {
  const features = [
    {
      icon: Shield,
      title: 'Abmahn-Schutz',
      description: 'Schützen Sie sich vor teuren Abmahnungen und Bußgeldern. Rechtssichere Compliance.',
      gradient: 'from-green-500 to-emerald-500',
    },
    {
      icon: Sparkles,
      title: 'Ohne Programmierung',
      description: 'Auch ohne technisches Wissen nutzbar. Die KI macht die Arbeit für Sie.',
      gradient: 'from-blue-500 to-cyan-500',
    },
    {
      icon: Zap,
      title: 'In 5 Minuten startklar',
      description: 'Website-URL eingeben, scannen, fertig. Schneller geht\'s nicht.',
      gradient: 'from-yellow-500 to-orange-500',
    },
    {
      icon: Users,
      title: 'Mehr Kunden erreichen',
      description: '15% der Bevölkerung haben eine Behinderung – erschließen Sie neue Zielgruppen.',
      gradient: 'from-purple-500 to-pink-500',
    },
    {
      icon: Search,
      title: 'Alles wird geprüft',
      description: 'Vollautomatischer Scan aller Seiten. Kein Problem bleibt unentdeckt.',
      gradient: 'from-indigo-500 to-purple-500',
    },
    {
      icon: Code2,
      title: 'Echte Fixes statt Overlay',
      description: 'Keine Quick-Fixes. Wir beheben Probleme dauerhaft im Code.',
      gradient: 'from-orange-500 to-red-500',
    },
    {
      icon: FileCheck,
      title: 'Audit-sichere Reports',
      description: 'PDF-Reports für Behörden und Audits. Dokumentieren Sie Ihre Compliance.',
      gradient: 'from-cyan-500 to-blue-500',
    },
    {
      icon: Euro,
      title: 'Günstiger als eine Abmahnung',
      description: 'Ab 19€/Monat pro Säule oder 49€/Monat für alle 4 Säulen.',
      gradient: 'from-teal-500 to-green-500',
    },
    {
      icon: Bell,
      title: 'Automatische Überwachung',
      description: 'Werden Sie gewarnt, wenn neue Probleme auftauchen. Immer auf der sicheren Seite.',
      gradient: 'from-red-500 to-orange-500',
    },
    {
      icon: Wand2,
      title: 'Sofort-Widget',
      description: 'Accessibility-Menü für Ihre Nutzer – Vorlese-Funktion, Kontrast, Schriftgröße und mehr.',
      gradient: 'from-violet-500 to-purple-500',
    },
    {
      icon: Globe,
      title: 'Für alle CMS-Systeme',
      description: 'WordPress, Shopify, Wix – egal welches System Sie nutzen.',
      gradient: 'from-pink-500 to-rose-500',
    },
    {
      icon: BarChart3,
      title: 'Erfolge messbar machen',
      description: 'Dashboard zeigt Ihren Fortschritt. Sehen Sie, wie Sie besser werden.',
      gradient: 'from-blue-500 to-indigo-500',
    },
  ];

  return (
    <section className="bg-gradient-to-b from-white to-gray-50 py-24">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <h2 className="text-4xl sm:text-5xl font-bold text-gray-900 mb-4">
            Warum über 2.500 Unternehmen{' '}
            <span className="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              Complyo
            </span>{' '}
            vertrauen
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Die einfachste Lösung für Barrierefreiheit – <strong>ohne Technik-Kenntnisse,</strong>{' '}
            mit voller Rechtssicherheit.
          </p>
        </motion.div>

        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature, idx) => {
            const Icon = feature.icon;
            return (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: idx * 0.05 }}
                whileHover={{ y: -5, scale: 1.02 }}
                className="bg-white rounded-2xl p-8 shadow-lg border border-gray-100 hover:shadow-xl transition-all cursor-pointer group"
              >
                {/* Icon */}
                <div
                  className={`w-14 h-14 rounded-xl bg-gradient-to-r ${feature.gradient} flex items-center justify-center mb-5 group-hover:scale-110 transition-transform`}
                >
                  <Icon className="w-7 h-7 text-white" />
                </div>

                {/* Content */}
                <h3 className="text-xl font-bold text-gray-900 mb-3">
                  {feature.title}
                </h3>
                <p className="text-gray-600 leading-relaxed">
                  {feature.description}
                </p>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

