'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { Check, Sparkles, ArrowRight } from 'lucide-react';

const getAppUrl = (path: string) => {
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      return `http://localhost:3000${path}`;
    }
  }
  return `https://app.complyo.tech${path}`;
};

/**
 * PricingModern - Moderne Pricing-Sektion
 * Conversion-optimiert mit klaren Preisen und Benefits
 */
export default function PricingModern() {
  const plans = [
    {
      name: 'Einzelmodul',
      pages: '1 Säule nach Wahl',
      period: 'pro Monat',
      price: '19',
      priceInfo: '/ Monat',
      features: [
        'Cookie & DSGVO ODER',
        'Barrierefreiheit ODER',
        'Rechtliche Texte ODER',
        'Monitoring & Scan',
        'KI-generierte Lösungen',
        'E-Mail Support',
      ],
      popular: false,
      cta: 'Modul wählen',
      href: getAppUrl('/register?plan=single'),
      gradient: 'from-blue-50 to-cyan-50',
      borderColor: 'border-blue-200',
    },
    {
      name: 'Komplett-Paket',
      pages: 'Alle 4 Säulen',
      period: 'pro Monat',
      price: '49',
      priceInfo: '/ Monat',
      features: [
        'Cookie & DSGVO',
        'Barrierefreiheit',
        'Rechtliche Texte',
        'Monitoring & Scan',
        'eRecht24 Integration',
        'Priority Support',
        'API-Zugriff',
        'Sie sparen 27€/Monat',
      ],
      popular: true,
      cta: 'Jetzt starten',
      href: getAppUrl('/register?plan=complete'),
      gradient: 'from-purple-50 to-pink-50',
      borderColor: 'border-purple-300',
      badge: 'Am beliebtesten',
    },
    {
      name: 'Expertenservice',
      pages: 'Wir setzen alles um',
      period: 'einmalig + laufend',
      price: '2.990',
      priceInfo: '+ 39€/Mo',
      features: [
        'Vollständige Umsetzung',
        'WCAG 2.1 AA Zertifizierung',
        'Persönlicher Ansprechpartner',
        'Laufende Updates',
        'SLA & Garantie',
        'Priority Support',
        'Telefon-Support',
      ],
      popular: false,
      cta: 'Beratung anfragen',
      href: getAppUrl('/register?plan=expert'),
      gradient: 'from-indigo-50 to-purple-50',
      borderColor: 'border-indigo-200',
    },
  ];

  return (
    <section className="bg-white py-24" id="pricing">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <div className="inline-flex items-center gap-2 bg-green-100 border border-green-300 rounded-full px-5 py-2 mb-6">
            <span className="text-green-700 font-semibold">💰 Günstiger als eine einzige Abmahnung</span>
          </div>
          <h2 className="text-4xl sm:text-5xl font-bold text-gray-900 mb-4">
            Transparente{' '}
            <span className="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              Preise
            </span>
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            <strong>Keine versteckten Kosten.</strong> Wählen Sie das Paket, das zu Ihrer Website passt.
          </p>
        </motion.div>

        {/* Pricing Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto mb-12">
          {plans.map((plan, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: idx * 0.1 }}
              whileHover={{ y: -8, scale: 1.02 }}
              className={`relative bg-gradient-to-br ${plan.gradient} rounded-3xl p-8 border-2 ${plan.borderColor} ${
                plan.popular ? 'shadow-2xl ring-4 ring-purple-100' : 'shadow-lg'
              } transition-all`}
            >
              {/* Popular Badge */}
              {plan.popular && (
                <div className="absolute -top-4 left-1/2 -translate-x-1/2">
                  <div className="bg-gradient-to-r from-purple-600 to-pink-600 text-white font-bold px-6 py-2 rounded-full text-sm shadow-lg flex items-center gap-2">
                    <Sparkles className="w-4 h-4" />
                    {plan.badge}
                  </div>
                </div>
              )}

              {/* Header */}
              <div className="text-center mb-6">
                <div className="text-3xl font-bold text-gray-900 mb-2">
                  {plan.name}
                </div>
                <div className="text-sm text-gray-600 mb-1">{plan.pages}</div>
                <div className="text-xs text-gray-500">{plan.period}</div>
              </div>

              {/* Price */}
              <div className="text-center mb-8">
                <div className="flex items-baseline justify-center gap-2">
                  <span className="text-5xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                    {plan.price}€
                  </span>
                  <span className="text-gray-600 text-lg">{plan.priceInfo}</span>
                </div>
                <p className="text-sm text-gray-500 mt-2">zzgl. MwSt.</p>
              </div>

              {/* Features */}
              <ul className="space-y-4 mb-8">
                {plan.features.map((feature, fidx) => (
                  <li key={fidx} className="flex items-start gap-3">
                    <Check className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
                    <span className="text-gray-700 text-sm">{feature}</span>
                  </li>
                ))}
              </ul>

              {/* CTA */}
              <motion.a
                href={plan.href}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className={`w-full py-4 rounded-xl font-semibold transition-all flex items-center justify-center gap-2 ${
                  plan.popular
                    ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg hover:shadow-xl'
                    : 'bg-white text-gray-900 border-2 border-gray-200 hover:border-gray-300 shadow-md hover:shadow-lg'
                }`}
              >
                {plan.cta}
                <ArrowRight className="w-5 h-5" />
              </motion.a>
            </motion.div>
          ))}
        </div>

        {/* Bottom CTA */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center bg-gradient-to-r from-orange-50 to-red-50 border border-orange-200 rounded-2xl p-8 max-w-4xl mx-auto"
        >
          <h3 className="text-2xl font-bold text-gray-900 mb-3">
            💼 Sie brauchen die Komplettlösung?
          </h3>
          <p className="text-gray-600 mb-6">
            Lassen Sie unsere Experten Ihre Website komplett barrierefrei machen. <br />
            <strong>Einmalig 2.990€</strong> + laufende Betreuung ab <strong>39€/Monat</strong>
          </p>
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="inline-flex items-center gap-2 bg-gradient-to-r from-orange-600 to-red-600 hover:from-orange-700 hover:to-red-700 text-white font-semibold px-8 py-4 rounded-xl shadow-lg hover:shadow-xl transition-all"
          >
            Beratung vereinbaren
            <ArrowRight className="w-5 h-5" />
          </motion.button>
        </motion.div>
      </div>
    </section>
  );
}

