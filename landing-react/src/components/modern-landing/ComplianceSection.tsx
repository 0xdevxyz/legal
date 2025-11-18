'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { Shield, CheckCircle2, FileCheck, Globe } from 'lucide-react';

/**
 * ComplianceSection - Compliance & Standards hervorheben
 */
export default function ComplianceSection() {
  const standards = [
    {
      icon: Shield,
      title: 'WCAG 2.1 AA',
      description: 'Vollständig konform mit den Web Content Accessibility Guidelines',
      color: 'from-blue-500 to-cyan-500',
    },
    {
      icon: FileCheck,
      title: 'ADA Compliant',
      description: 'Erfüllt die Americans with Disabilities Act Standards',
      color: 'from-purple-500 to-pink-500',
    },
    {
      icon: Globe,
      title: 'EN 301-549',
      description: 'Europäischer Standard für digitale Barrierefreiheit',
      color: 'from-green-500 to-emerald-500',
    },
    {
      icon: CheckCircle2,
      title: 'Section 508',
      description: 'US-Standard für Regierungswebsites und -dienste',
      color: 'from-orange-500 to-red-500',
    },
  ];

  return (
    <section className="bg-gradient-to-b from-gray-50 to-white py-24">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <h2 className="text-4xl sm:text-5xl font-bold text-gray-900 mb-4">
            Compliance{' '}
            <span className="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              Standards
            </span>
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Erfüllen Sie alle wichtigen internationalen Standards für Web-Barrierefreiheit.
          </p>
        </motion.div>

        {/* Standards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {standards.map((standard, idx) => {
            const Icon = standard.icon;
            return (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: idx * 0.1 }}
                whileHover={{ y: -5 }}
                className="bg-white rounded-2xl p-8 shadow-lg border border-gray-100 hover:shadow-xl transition-all text-center"
              >
                <div
                  className={`w-16 h-16 mx-auto rounded-2xl bg-gradient-to-r ${standard.color} flex items-center justify-center mb-5 shadow-lg`}
                >
                  <Icon className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-xl font-bold text-gray-900 mb-3">
                  {standard.title}
                </h3>
                <p className="text-gray-600 text-sm leading-relaxed">
                  {standard.description}
                </p>
              </motion.div>
            );
          })}
        </div>

        {/* Privacy Statement */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="mt-16 bg-gradient-to-r from-blue-50 via-purple-50 to-pink-50 border border-blue-200 rounded-2xl p-12 text-center max-w-4xl mx-auto"
        >
          <div className="w-16 h-16 mx-auto mb-6 bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl flex items-center justify-center shadow-xl">
            <Shield className="w-8 h-8 text-white" />
          </div>
          <h3 className="text-3xl font-bold text-gray-900 mb-4">
            Privacy by Design
          </h3>
          <p className="text-lg text-gray-700 max-w-2xl mx-auto leading-relaxed">
            ISO 27001 zertifiziert. Wir sammeln oder speichern keine Benutzerdaten oder PII. 
            Die Accessibility-Lösung unterstützt die strikte Einhaltung von GDPR, COPPA und HIPAA.
          </p>
        </motion.div>
      </div>
    </section>
  );
}

