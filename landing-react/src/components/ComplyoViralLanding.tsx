'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Link from 'next/link';
import {
  Shield,
  CheckCircle,
  ArrowRight,
  ChevronDown,
  Zap,
  Code,
  FileText,
  Eye,
  Scale,
  Globe,
  Users,
  TrendingUp,
  Sparkles,
  Crown,
  Play,
  Star,
  Clock,
  Lock,
  Award
} from 'lucide-react';
import { Logo } from './Logo';

/**
 * ComplyoViralLanding - Ultra-moderne Landing Page (HELLES THEME)
 * Inspiriert von Pykaso.ai und Web3Universe Design
 * 
 * Features:
 * - Heller Hintergrund mit lila/blauem Gradient
 * - Animierte Scroll-Banner
 * - Feature-Cards mit Hover-Effekten
 * - Statistik-Badges
 * - FAQ-Accordion
 */
export default function ComplyoViralLanding() {
  const [expandedFaq, setExpandedFaq] = useState<number | null>(null);
  const [isScrolled, setIsScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 50);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const features = [
    'DSGVO-Prüfung',
    'Barrierefreiheit',
    'Cookie-Consent',
    'Impressum-Check',
    'WCAG 2.1 AA',
    'KI-Fixes',
    'Code-Snippets',
    'PDF-Export',
    'Rechtssicher',
    'Automatisch',
    'DSGVO-Prüfung',
    'Barrierefreiheit',
    'Cookie-Consent',
    'Impressum-Check',
  ];

  const stats = [
    { value: '2.500+', label: 'Geschützte Websites' },
    { value: '50+', label: 'Länder' },
    { value: '0', label: 'Abmahnungen bei Kunden' },
  ];

  const benefits = [
    {
      icon: <Zap className="w-8 h-8" />,
      title: 'Blitzschnelle Analyse',
      description: 'Ihre Website wird in unter 90 Sekunden vollständig gescannt und analysiert.'
    },
    {
      icon: <Code className="w-8 h-8" />,
      title: 'KI-generierte Fixes',
      description: 'Erhalten Sie sofort einsatzbereite Code-Snippets für jedes gefundene Problem.'
    },
    {
      icon: <Shield className="w-8 h-8" />,
      title: 'Rechtssicher',
      description: 'Alle Texte und Empfehlungen sind von eRecht24 geprüft und zertifiziert.'
    },
    {
      icon: <Eye className="w-8 h-8" />,
      title: 'WCAG 2.1 AA',
      description: 'Vollständige Prüfung nach internationalem Barrierefreiheits-Standard.'
    },
    {
      icon: <Scale className="w-8 h-8" />,
      title: 'DSGVO-konform',
      description: 'Automatische Prüfung aller datenschutzrelevanten Bereiche.'
    },
    {
      icon: <Globe className="w-8 h-8" />,
      title: 'Multi-Language',
      description: 'Unterstützung für deutsche, englische und weitere Sprachen.'
    },
  ];

  const steps = [
    {
      number: '01',
      title: 'Website scannen',
      description: 'Geben Sie Ihre URL ein und unsere KI analysiert alle Compliance-Bereiche in unter 90 Sekunden.',
      icon: <Globe className="w-12 h-12" />,
      color: 'from-pink-400 to-rose-500',
    },
    {
      number: '02',
      title: 'Probleme identifizieren',
      description: 'Erhalten Sie einen detaillierten Report mit allen gefundenen Issues, priorisiert nach Wichtigkeit.',
      icon: <FileText className="w-12 h-12" />,
      color: 'from-purple-400 to-violet-500',
    },
    {
      number: '03',
      title: 'KI-Fixes anwenden',
      description: 'Kopieren Sie die generierten Code-Snippets direkt in Ihre Website – fertig!',
      icon: <Code className="w-12 h-12" />,
      color: 'from-blue-400 to-indigo-500',
    },
  ];

  const faqs = [
    {
      q: 'Was ist der Unterschied zu Overlay-Lösungen wie Eye-Able®?',
      a: 'Im Gegensatz zu Overlay-Widgets bietet Complyo echte Code-Fixes. Das bedeutet nachhaltige Compliance ohne Abhängigkeit von Drittanbietern, bessere Performance und echte Barrierefreiheit statt kosmetischer Korrekturen.'
    },
    {
      q: 'Brauche ich technische Kenntnisse?',
      a: 'Nein! Alles wird Schritt-für-Schritt erklärt. Wenn Sie Copy-Paste können, können Sie Ihre Website compliant machen. Für den Expert-Plan übernehmen wir sogar die Implementierung für Sie.'
    },
    {
      q: 'Wie schnell sehe ich Ergebnisse?',
      a: 'Die meisten Kunden haben ihre Website innerhalb von 24 Stunden compliant gemacht. Der Scan dauert 90 Sekunden, die Implementierung der Fixes je nach Komplexität 1-3 Stunden.'
    },
    {
      q: 'Was ist, wenn ich bereits eine Abmahnung erhalten habe?',
      a: 'Kein Problem! Wir haben mit jedem erdenklichen Fall gearbeitet. Unser Expert-Plan beinhaltet sogar direkten Anwalts-Support für akute Fälle.'
    },
    {
      q: 'Ist Complyo WCAG 2.1 AA konform?',
      a: 'Ja, Complyo prüft Ihre Website nach allen Kriterien der WCAG 2.1 Level AA. Unser Scanner analysiert über 127 Prüfpunkte und gibt Ihnen konkrete Handlungsempfehlungen.'
    },
    {
      q: 'Wie funktioniert die Geld-zurück-Garantie?',
      a: 'Einfach: Probieren Sie es 14 Tage aus. Wenn Sie nicht begeistert sind, schicken Sie eine E-Mail an support@complyo.tech und wir erstatten Ihren kompletten Kaufpreis zurück – keine Fragen.'
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/30 to-purple-50/40 text-gray-900 overflow-x-hidden">
      {/* Subtle Background Elements */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute -top-40 -right-40 w-96 h-96 bg-gradient-to-br from-blue-200/40 to-purple-200/40 rounded-full blur-3xl" />
        <div className="absolute top-1/3 -left-40 w-80 h-80 bg-gradient-to-br from-pink-200/30 to-rose-200/30 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 right-1/4 w-72 h-72 bg-gradient-to-br from-indigo-200/30 to-blue-200/30 rounded-full blur-3xl" />
        {/* Large watermark text like Web3Universe */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-[20vw] font-black text-blue-100/20 whitespace-nowrap select-none">
          Complyo
        </div>
      </div>

      {/* Header with Navigation */}
      <header>
        <nav role="navigation" aria-label="Hauptnavigation" className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        isScrolled ? 'bg-white/90 backdrop-blur-xl shadow-sm border-b border-gray-100' : 'bg-transparent'
      }`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-20">
            <a href="/" className="flex items-center gap-3">
              <Logo size="lg" variant="light" />
            </a>
            
            <div className="hidden md:flex items-center gap-8">
              <a href="#features" className="text-gray-600 hover:text-blue-600 transition-colors text-sm font-medium">Features</a>
              <a href="#how-it-works" className="text-gray-600 hover:text-blue-600 transition-colors text-sm font-medium">So funktioniert&apos;s</a>
              <a href="#pricing" className="text-gray-600 hover:text-blue-600 transition-colors text-sm font-medium">Preise</a>
              <a href="#faq" className="text-gray-600 hover:text-blue-600 transition-colors text-sm font-medium">FAQ</a>
            </div>

            <div className="flex items-center gap-4">
              <a 
                href={process.env.NODE_ENV === 'production' ? 'https://app.complyo.tech' : 'http://localhost:3001'}
                className="hidden md:inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-bold rounded-xl transition-all transform hover:scale-105 shadow-lg shadow-blue-500/25"
              >
                <Sparkles className="w-4 h-4" />
                Jetzt starten
              </a>
            </div>
          </div>
        </div>
        </nav>
      </header>

      {/* Main Content */}
      <main role="main">
        {/* Hero Section */}
        <section className="relative pt-32 pb-20 px-4">
        <div className="max-w-6xl mx-auto text-center relative z-10">
          {/* Badge */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="inline-flex items-center gap-2 bg-blue-100 border border-blue-200 rounded-full px-6 py-2 mb-8"
          >
            <CheckCircle className="w-5 h-5 text-blue-600" />
            <span className="text-sm font-medium text-blue-700">Über 2.500 Websites geschützt</span>
          </motion.div>

          {/* Main Headline */}
          <motion.h1
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="text-5xl md:text-7xl font-black leading-tight mb-6"
          >
            <span className="text-gray-900">
              Ultra-schnelle
            </span>
            <br />
            <span className="bg-gradient-to-r from-blue-600 via-purple-600 to-pink-500 bg-clip-text text-transparent">
              Compliance-Tools
            </span>
          </motion.h1>

          {/* Subheadline */}
          <motion.p
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="text-xl md:text-2xl text-gray-600 mb-8 max-w-3xl mx-auto leading-relaxed"
          >
            Scannen Sie Ihre Website und erhalten Sie KI-generierte Fixes für 
            <span className="text-gray-900 font-semibold"> DSGVO</span>, 
            <span className="text-gray-900 font-semibold"> Barrierefreiheit</span> und 
            <span className="text-gray-900 font-semibold"> Cookie-Consent</span> in Sekunden.
          </motion.p>

          {/* CTA Buttons */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="flex flex-col sm:flex-row gap-4 justify-center mb-12"
          >
            <a
              href={process.env.NODE_ENV === 'production' ? 'https://app.complyo.tech' : 'http://localhost:3001'}
              className="inline-flex items-center justify-center gap-3 px-8 py-4 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-bold text-lg rounded-2xl transition-all transform hover:scale-105 shadow-xl shadow-blue-500/25"
            >
              Kostenlos starten
              <ArrowRight className="w-5 h-5" />
            </a>
            <a
              href="#demo"
              className="inline-flex items-center justify-center gap-3 px-8 py-4 bg-white border-2 border-gray-200 hover:border-blue-300 hover:bg-blue-50 text-gray-700 font-semibold text-lg rounded-2xl transition-all"
            >
              <Play className="w-5 h-5 text-blue-600" />
              Demo ansehen
            </a>
          </motion.div>

          {/* Scrolling Feature Banner */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4 }}
            className="relative overflow-hidden py-4 mb-12"
          >
            <div className="flex animate-scroll">
              {[...features, ...features].map((feature, i) => (
                <div
                  key={i}
                  className="flex-shrink-0 mx-3 px-5 py-2.5 bg-white/80 border border-gray-200 rounded-full text-sm font-medium text-gray-700 hover:text-blue-600 hover:border-blue-300 hover:bg-blue-50 transition-colors cursor-pointer shadow-sm"
                >
                  {feature}
                </div>
              ))}
            </div>
          </motion.div>

          {/* Stats with laurel decorations */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
            className="flex justify-center items-center gap-8 md:gap-16"
          >
            {stats.map((stat, i) => (
              <div key={i} className="text-center flex items-center gap-2">
                <span className="text-2xl">🌿</span>
                <div>
                  <div className="text-3xl md:text-4xl font-black bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                    {stat.value}
                  </div>
                  <div className="text-xs text-gray-500 uppercase tracking-wider font-medium">
                    {stat.label}
                  </div>
                </div>
                <span className="text-2xl">🌿</span>
              </div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* Features Grid */}
      <section id="features" className="relative py-24 px-4">
        <div className="max-w-7xl mx-auto relative z-10">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-black mb-4 text-gray-900">
              Alles was Sie brauchen
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Erreichen Sie maximale Compliance mit den KI-Tools, die Sie brauchen, um rechtssicher zu werden.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {benefits.map((benefit, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1 }}
                viewport={{ once: true }}
                className="group relative bg-white rounded-2xl p-8 border border-gray-100 hover:border-blue-200 transition-all duration-300 shadow-sm hover:shadow-xl"
              >
                <div className="absolute inset-0 bg-gradient-to-br from-blue-50 to-purple-50 opacity-0 group-hover:opacity-100 transition-opacity rounded-2xl" />
                <div className="relative">
                  <div className="w-14 h-14 bg-gradient-to-br from-blue-100 to-purple-100 rounded-xl flex items-center justify-center text-blue-600 mb-6 group-hover:scale-110 transition-transform">
                    {benefit.icon}
                  </div>
                  <h3 className="text-xl font-bold text-gray-900 mb-3">{benefit.title}</h3>
                  <p className="text-gray-600 leading-relaxed">{benefit.description}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works - with colored cards like Web3Universe */}
      <section id="how-it-works" className="relative py-24 px-4">
        <div className="max-w-6xl mx-auto relative z-10">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-black mb-4 text-gray-900">
              So einfach funktioniert&apos;s
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              In nur 3 Schritten zur vollständigen Compliance
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {steps.map((step, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.2 }}
                viewport={{ once: true }}
                className="relative group"
              >
                {/* Colored Card Background */}
                <div className={`bg-gradient-to-br ${step.color} rounded-3xl p-8 text-white h-full shadow-xl hover:shadow-2xl transition-all hover:scale-105`}>
                  <div className="text-6xl font-black opacity-30 mb-4">
                    {step.number}
                  </div>
                  <div className="w-16 h-16 bg-white/20 backdrop-blur-sm rounded-2xl flex items-center justify-center mb-6">
                    {step.icon}
                  </div>
                  <h3 className="text-2xl font-bold mb-4">{step.title}</h3>
                  <p className="text-white/90 leading-relaxed">{step.description}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="relative py-24 px-4">
        <div className="max-w-6xl mx-auto relative z-10">
          <div className="text-center mb-16">
            <div className="inline-flex items-center gap-2 bg-gradient-to-r from-orange-100 to-pink-100 border border-orange-200 rounded-full px-6 py-2 mb-6">
              <Sparkles className="w-5 h-5 text-orange-500" />
              <span className="text-sm font-bold text-orange-600">LAUNCH-SPECIAL: 50% RABATT</span>
            </div>
            <h2 className="text-4xl md:text-5xl font-black mb-4 text-gray-900">
              Transparente Preise
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Wählen Sie den Plan, der zu Ihnen passt
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
            {/* DIY Plan */}
            <motion.div
              initial={{ opacity: 0, x: -30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              className="relative bg-white rounded-3xl p-8 border-2 border-gray-200 hover:border-blue-300 transition-all shadow-lg"
            >
              <div className="flex items-center gap-3 mb-6">
                <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-500 rounded-xl flex items-center justify-center">
                  <Sparkles className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h3 className="text-2xl font-bold text-gray-900">DIY mit KI</h3>
                  <p className="text-sm text-gray-500">Für Selbermacher & Entwickler</p>
                </div>
              </div>

              <div className="mb-8">
                <div className="flex items-baseline gap-2">
                  <span className="text-5xl font-black text-gray-900">49€</span>
                  <span className="text-gray-500">/Monat</span>
                </div>
                <p className="text-sm text-gray-400 mt-2">zzgl. MwSt. • Alle 4 Säulen</p>
              </div>

              <ul className="space-y-4 mb-8">
                {[
                  'Unbegrenzte Compliance-Analysen',
                  'KI-generierte Code-Fixes',
                  'Schritt-für-Schritt Anleitungen',
                  'Score-Verlauf & Reports',
                  'PDF/Excel Export',
                  'eRecht24 Integration',
                  'E-Mail Support'
                ].map((feature, i) => (
                  <li key={i} className="flex items-center gap-3">
                    <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0" />
                    <span className="text-gray-700">{feature}</span>
                  </li>
                ))}
              </ul>

              <a
                href={process.env.NODE_ENV === 'production' ? 'https://app.complyo.tech/register?plan=complete' : 'http://localhost:3001/register?plan=complete'}
                className="block w-full text-center bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-bold py-4 rounded-xl transition-all shadow-lg"
              >
                Jetzt starten
              </a>
            </motion.div>

            {/* Expert Plan */}
            <motion.div
              initial={{ opacity: 0, x: 30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              className="relative bg-gradient-to-br from-blue-600 via-purple-600 to-pink-500 rounded-3xl p-8 text-white shadow-2xl"
            >
              {/* Popular Badge */}
              <div className="absolute -top-4 left-1/2 -translate-x-1/2">
                <div className="bg-gradient-to-r from-yellow-400 to-orange-400 text-gray-900 font-bold px-6 py-2 rounded-full text-sm shadow-lg">
                  ⭐ EMPFOHLEN
                </div>
              </div>

              <div className="flex items-center gap-3 mb-6 mt-4">
                <div className="w-12 h-12 bg-white/20 backdrop-blur-sm rounded-xl flex items-center justify-center">
                  <Crown className="w-6 h-6 text-yellow-300" />
                </div>
                <div>
                  <h3 className="text-2xl font-bold">Expertenservice</h3>
                  <p className="text-sm text-white/70">Vollständige Umsetzung für Sie</p>
                </div>
              </div>

              <div className="mb-8">
                <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4 mb-3">
                  <div className="text-sm text-white/70 mb-1">Einmalig</div>
                  <div className="flex items-baseline gap-2">
                    <span className="text-4xl font-black">2.990€</span>
                    <span className="text-white/70">netto</span>
                  </div>
                </div>
                <div className="bg-white/10 backdrop-blur-sm rounded-xl p-4">
                  <div className="text-sm text-white/70 mb-1">Danach laufend</div>
                  <div className="flex items-baseline gap-2">
                    <span className="text-3xl font-bold">39€</span>
                    <span className="text-white/70">/Monat</span>
                  </div>
                </div>
              </div>

              <div className="mb-6">
                <h4 className="font-semibold mb-3 text-yellow-300 text-sm uppercase tracking-wider">Einmalige Umsetzung:</h4>
                <ul className="space-y-3">
                  {[
                    'Vollständige Website-Analyse',
                    'Professionelle Code-Umsetzung',
                    'WCAG 2.1 AA Zertifizierung',
                    'Cookie-Consent Implementation'
                  ].map((feature, i) => (
                    <li key={i} className="flex items-center gap-3">
                      <Star className="w-5 h-5 text-yellow-300 flex-shrink-0" />
                      <span className="text-white/90">{feature}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="mb-8">
                <h4 className="font-semibold mb-3 text-blue-200 text-sm uppercase tracking-wider">Laufende Updates:</h4>
                <ul className="space-y-3">
                  {[
                    'Monatliche Compliance-Updates',
                    'Priority Support',
                    'Monitoring & Alerts'
                  ].map((feature, i) => (
                    <li key={i} className="flex items-center gap-3">
                      <Star className="w-5 h-5 text-blue-200 flex-shrink-0" />
                      <span className="text-white/90">{feature}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <a
                href="/contact?service=expert"
                className="block w-full text-center bg-white hover:bg-gray-100 text-gray-900 font-bold py-4 rounded-xl transition-all shadow-lg"
              >
                Beratung vereinbaren
                <ArrowRight className="inline-block w-5 h-5 ml-2" />
              </a>
            </motion.div>
          </div>

          {/* Guarantee */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="mt-12 max-w-2xl mx-auto bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-2xl p-8 text-center"
          >
            <Shield className="w-12 h-12 text-green-600 mx-auto mb-4" />
            <h3 className="text-xl font-bold text-gray-900 mb-2">14-Tage Geld-zurück-Garantie</h3>
            <p className="text-gray-600">
              Testen Sie Complyo risikofrei. Wenn Sie nicht zufrieden sind, erstatten wir Ihren kompletten Kaufpreis zurück – keine Fragen.
            </p>
          </motion.div>
        </div>
      </section>

      {/* FAQ Section */}
      <section id="faq" className="relative py-24 px-4">
        <div className="max-w-4xl mx-auto relative z-10">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-black mb-4 text-gray-900">
              Häufig gestellte Fragen
            </h2>
          </div>

          <div className="space-y-4">
            {faqs.map((faq, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1 }}
                viewport={{ once: true }}
                className="bg-white rounded-2xl border border-gray-200 overflow-hidden shadow-sm"
              >
                <button
                  onClick={() => setExpandedFaq(expandedFaq === i ? null : i)}
                  className="w-full px-6 py-5 flex items-center justify-between text-left hover:bg-gray-50 transition-colors"
                >
                  <span className="font-semibold text-gray-900 pr-4">{faq.q}</span>
                  <ChevronDown 
                    className={`w-5 h-5 text-gray-400 flex-shrink-0 transition-transform ${
                      expandedFaq === i ? 'rotate-180' : ''
                    }`}
                  />
                </button>
                <AnimatePresence>
                  {expandedFaq === i && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.3 }}
                      className="overflow-hidden"
                    >
                      <div className="px-6 pb-5 text-gray-600 leading-relaxed border-t border-gray-100 pt-4">
                        {faq.a}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="relative py-24 px-4">
        <div className="max-w-4xl mx-auto text-center relative z-10">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            <h2 className="text-4xl md:text-6xl font-black mb-6 text-gray-900">
              Bereit für echte
              <span className="bg-gradient-to-r from-blue-600 via-purple-600 to-pink-500 bg-clip-text text-transparent"> Compliance?</span>
            </h2>
            <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
              Schließen Sie sich über 2.500 Unternehmen an, die ihre Websites mit Complyo schützen.
            </p>
            <a
              href={process.env.NODE_ENV === 'production' ? 'https://app.complyo.tech' : 'http://localhost:3001'}
              className="inline-flex items-center gap-3 px-10 py-5 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-bold text-xl rounded-2xl transition-all transform hover:scale-105 shadow-xl shadow-blue-500/25"
            >
              Jetzt kostenlos starten
              <ArrowRight className="w-6 h-6" />
            </a>
            <p className="mt-6 text-gray-500 text-sm">
              ✓ Keine Kreditkarte erforderlich • ✓ 14-Tage Geld-zurück-Garantie
            </p>
          </motion.div>
        </div>
      </section>
      </main>

      {/* Footer */}
      <footer role="contentinfo" className="border-t border-gray-200 py-12 px-4 bg-white/50 relative z-10">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-4 gap-8 mb-12">
            {/* Logo & Description */}
            <div className="md:col-span-1">
              <Logo size="lg" variant="light" />
              <p className="text-gray-500 mt-4 text-sm leading-relaxed">
                Echte Compliance mit KI-Unterstützung. 
                DSGVO, Barrierefreiheit und Cookie-Consent in einem Tool.
              </p>
            </div>

            {/* Product */}
            <div>
              <h4 className="font-bold text-gray-900 mb-4">Produkt</h4>
              <ul className="space-y-2 text-sm">
                <li><a href="#features" className="text-gray-600 hover:text-blue-600 transition-colors">Features</a></li>
                <li><a href="#pricing" className="text-gray-600 hover:text-blue-600 transition-colors">Preise</a></li>
                <li><a href="#faq" className="text-gray-600 hover:text-blue-600 transition-colors">FAQ</a></li>
              </ul>
            </div>

            {/* Legal */}
            <div>
              <h4 className="font-bold text-gray-900 mb-4">Rechtliches</h4>
              <ul className="space-y-2 text-sm">
                <li><Link href="/impressum" className="text-gray-600 hover:text-blue-600 transition-colors">Impressum</Link></li>
                <li><Link href="/datenschutz" className="text-gray-600 hover:text-blue-600 transition-colors">Datenschutz</Link></li>
                <li><Link href="/agb" className="text-gray-600 hover:text-blue-600 transition-colors">AGB</Link></li>
              </ul>
            </div>

            {/* Contact */}
            <div>
              <h4 className="font-bold text-gray-900 mb-4">Kontakt</h4>
              <ul className="space-y-2 text-sm">
                <li><a href="mailto:support@complyo.tech" className="text-gray-600 hover:text-blue-600 transition-colors">support@complyo.tech</a></li>
                <li><a href="/contact" className="text-gray-600 hover:text-blue-600 transition-colors">Kontaktformular</a></li>
              </ul>
            </div>
          </div>

          {/* Bottom */}
          <div className="border-t border-gray-200 pt-8 flex flex-col md:flex-row justify-between items-center">
            <p className="text-gray-500 text-sm">
              © 2025 Complyo GmbH. Alle Rechte vorbehalten.
            </p>
            <div className="flex gap-6 mt-4 md:mt-0">
              <a href="#" className="text-gray-400 hover:text-blue-600 transition-colors">
                <span className="sr-only">LinkedIn</span>
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"/>
                </svg>
              </a>
              <a href="#" className="text-gray-400 hover:text-blue-600 transition-colors">
                <span className="sr-only">Twitter</span>
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M23.953 4.57a10 10 0 01-2.825.775 4.958 4.958 0 002.163-2.723c-.951.555-2.005.959-3.127 1.184a4.92 4.92 0 00-8.384 4.482C7.69 8.095 4.067 6.13 1.64 3.162a4.822 4.822 0 00-.666 2.475c0 1.71.87 3.213 2.188 4.096a4.904 4.904 0 01-2.228-.616v.06a4.923 4.923 0 003.946 4.827 4.996 4.996 0 01-2.212.085 4.936 4.936 0 004.604 3.417 9.867 9.867 0 01-6.102 2.105c-.39 0-.779-.023-1.17-.067a13.995 13.995 0 007.557 2.209c9.053 0 13.998-7.496 13.998-13.985 0-.21 0-.42-.015-.63A9.935 9.935 0 0024 4.59z"/>
                </svg>
              </a>
            </div>
          </div>
        </div>
      </footer>

      {/* CSS for scroll animation */}
      <style jsx>{`
        @keyframes scroll {
          0% {
            transform: translateX(0);
          }
          100% {
            transform: translateX(-50%);
          }
        }
        .animate-scroll {
          animation: scroll 30s linear infinite;
        }
        .animate-scroll:hover {
          animation-play-state: paused;
        }
      `}</style>
    </div>
  );
}
