'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { ArrowRight, Sparkles, CheckCircle2, PlayCircle } from 'lucide-react';

/**
 * ModernHero - Hauptbereich der Landing Page
 * Features:
 * - Glassmorphism
 * - Gradienten (Blau/Lila/Rosa)
 * - Animations mit Framer Motion
 * - Accessibility Widget Preview
 * - Conversion-optimiert mit Schmerzpunkt-Fokus
 */
export default function ModernHero() {
  return (
    <section className="relative min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-purple-50 overflow-hidden">
      {/* Animated Background Blobs */}
      <div className="absolute inset-0 overflow-hidden">
        <motion.div
          className="absolute -top-40 -right-40 w-96 h-96 bg-gradient-to-br from-blue-400 to-purple-600 rounded-full opacity-20 blur-3xl"
          animate={{
            scale: [1, 1.2, 1],
            rotate: [0, 90, 0],
          }}
          transition={{
            duration: 20,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        />
        <motion.div
          className="absolute -bottom-40 -left-40 w-96 h-96 bg-gradient-to-br from-purple-400 to-pink-600 rounded-full opacity-20 blur-3xl"
          animate={{
            scale: [1, 1.3, 1],
            rotate: [0, -90, 0],
          }}
          transition={{
            duration: 15,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        />
      </div>

      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-16 lg:pt-32 lg:pb-24">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          {/* Left: Content */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-center lg:text-left"
          >
            {/* Badge */}
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.2 }}
              className="inline-flex items-center gap-2 bg-red-100 border border-red-300 rounded-full px-4 py-2 mb-6 shadow-lg"
            >
              <span className="text-sm font-bold text-red-600">
                ⚠️ Abmahnwelle 2025: Bis zu 50.000€ Bußgeld drohen
              </span>
            </motion.div>

            {/* Headline */}
            <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold leading-tight mb-6">
              <span className="text-gray-900">Schützen Sie sich vor</span>{' '}
              <span className="bg-gradient-to-r from-red-600 via-orange-600 to-red-600 bg-clip-text text-transparent">
                Abmahnungen
              </span>
              <br />
              <span className="text-gray-900">& Bußgeldern</span>
            </h1>

            {/* Subline */}
            <p className="text-xl text-gray-600 mb-8 leading-relaxed max-w-2xl">
              Ihre Website ist <strong>nicht barrierefrei?</strong> Das kann teuer werden! 
              Complyo macht Ihre Website rechtssicher – <strong>ohne Programmierkenntnisse.</strong>
            </p>

            {/* USPs */}
            <div className="flex flex-col gap-3 mb-8">
              <div className="flex items-center gap-3 text-gray-700">
                <CheckCircle2 className="w-5 h-5 text-green-500 flex-shrink-0" />
                <span className="text-base"><strong>Keine Programmierung nötig</strong> – in 5 Minuten startklar</span>
              </div>
              <div className="flex items-center gap-3 text-gray-700">
                <CheckCircle2 className="w-5 h-5 text-green-500 flex-shrink-0" />
                <span className="text-base"><strong>Rechtssicher:</strong> DSGVO + WCAG 2.1 konform</span>
              </div>
              <div className="flex items-center gap-3 text-gray-700">
                <CheckCircle2 className="w-5 h-5 text-green-500 flex-shrink-0" />
                <span className="text-base"><strong>Abmahn-Schutz:</strong> Vermeiden Sie teure Strafen</span>
              </div>
            </div>

            {/* CTAs */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center lg:justify-start">
              <motion.a
                href={process.env.NODE_ENV === 'production' ? 'https://app.complyo.tech' : 'http://localhost:3001'}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="inline-flex items-center justify-center gap-2 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-semibold px-8 py-4 rounded-full transition-all shadow-xl hover:shadow-2xl"
              >
                Kostenlos starten
                <ArrowRight className="w-5 h-5" />
              </motion.a>
              
              <motion.a
                href="#demo"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="inline-flex items-center justify-center gap-2 bg-white/80 backdrop-blur-sm hover:bg-white border border-gray-200 text-gray-900 font-semibold px-8 py-4 rounded-full transition-all shadow-lg hover:shadow-xl"
              >
                <PlayCircle className="w-5 h-5" />
                Demo ansehen
              </motion.a>
            </div>

            {/* Trust Line */}
            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.8 }}
              className="mt-8 text-sm text-gray-500"
            >
              ✅ Über 2.500 deutsche Unternehmen vertrauen auf Complyo<br />
              💰 Durchschnittlich 50.000€ Bußgeld vermieden
            </motion.p>
          </motion.div>

          {/* Right: Visual */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8, delay: 0.3 }}
            className="relative"
          >
            {/* Main Card - Accessibility Widget Preview */}
            <div className="relative">
              {/* Glow Effect */}
              <div className="absolute inset-0 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 blur-3xl opacity-30 rounded-3xl"></div>
              
              {/* Card */}
              <motion.div
                className="relative bg-white/80 backdrop-blur-xl border border-white/20 rounded-3xl shadow-2xl p-8 overflow-hidden"
                whileHover={{ y: -5 }}
                transition={{ duration: 0.3 }}
              >
                {/* Header */}
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <h3 className="text-2xl font-bold text-gray-900 mb-1">
                      Accessibility Menü
                    </h3>
                    <p className="text-sm text-gray-600">
                      Aktiviert für alle Nutzer
                    </p>
                  </div>
                  <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center shadow-lg">
                    <Sparkles className="w-6 h-6 text-white" />
                  </div>
                </div>

                {/* Features Grid */}
                <div className="grid grid-cols-2 gap-3 mb-6">
                  {[
                    { icon: '🔊', label: 'Screen Reader' },
                    { icon: '🔍', label: 'Text Spacing' },
                    { icon: '🎨', label: 'Kontrast' },
                    { icon: '📖', label: 'Dyslexia Font' },
                    { icon: '🖱️', label: 'Big Cursor' },
                    { icon: '🔗', label: 'Link Highlight' },
                  ].map((feature, idx) => (
                    <motion.div
                      key={idx}
                      initial={{ opacity: 0, scale: 0.8 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: 0.5 + idx * 0.1 }}
                      whileHover={{ scale: 1.05 }}
                      className="bg-gradient-to-br from-gray-50 to-blue-50 border border-gray-200 rounded-xl p-4 cursor-pointer hover:shadow-md transition-all"
                    >
                      <div className="text-2xl mb-2">{feature.icon}</div>
                      <div className="text-xs font-semibold text-gray-700">
                        {feature.label}
                      </div>
                    </motion.div>
                  ))}
                </div>

                {/* Stats */}
                <div className="bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-xl p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="text-sm text-gray-600 mb-1">
                        Compliance Score
                      </div>
                      <div className="text-3xl font-bold bg-gradient-to-r from-green-600 to-emerald-600 bg-clip-text text-transparent">
                        92%
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm text-gray-600 mb-1">
                        WCAG Level
                      </div>
                      <div className="text-2xl font-bold text-gray-900">
                        AA
                      </div>
                    </div>
                  </div>
                </div>
              </motion.div>

              {/* Floating Badge */}
              <motion.div
                className="absolute -bottom-4 -right-4 bg-gradient-to-r from-blue-600 to-purple-600 text-white px-6 py-3 rounded-2xl shadow-xl"
                animate={{
                  y: [0, -10, 0],
                }}
                transition={{
                  duration: 3,
                  repeat: Infinity,
                  ease: "easeInOut"
                }}
              >
                <div className="text-lg font-bold">100%</div>
                <div className="text-xs opacity-90">Konform</div>
              </motion.div>
            </div>
          </motion.div>
        </div>
      </div>

      {/* Wave Divider */}
      <div className="absolute bottom-0 left-0 right-0 pointer-events-none">
        <svg
          viewBox="0 0 1440 120"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="w-full h-auto"
        >
          <path
            d="M0 120L60 110C120 100 240 80 360 70C480 60 600 60 720 65C840 70 960 80 1080 85C1200 90 1320 90 1380 90L1440 90V120H1380C1320 120 1200 120 1080 120C960 120 840 120 720 120C600 120 480 120 360 120C240 120 120 120 60 120H0V120Z"
            fill="white"
          />
        </svg>
      </div>
    </section>
  );
}

