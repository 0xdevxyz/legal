'use client';

import React, { useState, useEffect, useRef } from 'react';
import { motion, useInView, useScroll, useTransform, AnimatePresence } from 'framer-motion';
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
  Sparkles,
  Crown,
  Star,
  Lock,
  AlertTriangle,
  TrendingUp,
  RefreshCw,
  Bell,
  BarChart3,
  Search,
  Check
} from 'lucide-react';
import { Logo } from './Logo';

function FadeInSection({ children, delay = 0, className = '' }: { children: React.ReactNode; delay?: number; className?: string }) {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-80px' });
  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 40 }}
      animate={isInView ? { opacity: 1, y: 0 } : {}}
      transition={{ duration: 0.7, delay, ease: [0.25, 0.46, 0.45, 0.94] }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

function SlideInSection({ children, from = 'left', delay = 0, className = '' }: { children: React.ReactNode; from?: 'left' | 'right'; delay?: number; className?: string }) {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-80px' });
  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, x: from === 'left' ? -60 : 60 }}
      animate={isInView ? { opacity: 1, x: 0 } : {}}
      transition={{ duration: 0.8, delay, ease: [0.25, 0.46, 0.45, 0.94] }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

function ComplianceScoreMockup() {
  const [score, setScore] = useState(42);
  const [animating, setAnimating] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => {
      setAnimating(true);
      let current = 42;
      const target = 97;
      const interval = setInterval(() => {
        current += 3;
        if (current >= target) {
          current = target;
          clearInterval(interval);
        }
        setScore(current);
      }, 40);
    }, 1200);
    return () => clearTimeout(timer);
  }, []);

  const getColor = (s: number) => s >= 80 ? '#22c55e' : s >= 60 ? '#f59e0b' : '#ef4444';

  return (
    <div className="bg-white rounded-3xl shadow-2xl border border-gray-100 p-8 w-full max-w-sm mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <p className="text-xs text-gray-400 uppercase tracking-widest font-medium">Compliance Score</p>
          <p className="text-sm text-gray-600 mt-0.5">complyo.tech</p>
        </div>
        <div className="w-8 h-8 bg-blue-50 rounded-lg flex items-center justify-center">
          <Shield className="w-4 h-4 text-blue-600" />
        </div>
      </div>

      <div className="flex items-center gap-6 mb-6">
        <div className="relative w-24 h-24">
          <svg viewBox="0 0 100 100" className="w-full h-full -rotate-90">
            <circle cx="50" cy="50" r="40" fill="none" stroke="#f3f4f6" strokeWidth="10" />
            <motion.circle
              cx="50" cy="50" r="40" fill="none"
              stroke={getColor(score)} strokeWidth="10"
              strokeLinecap="round"
              strokeDasharray={`${2 * Math.PI * 40}`}
              initial={{ strokeDashoffset: 2 * Math.PI * 40 }}
              animate={{ strokeDashoffset: 2 * Math.PI * 40 * (1 - score / 100) }}
              transition={{ duration: 1.5, ease: 'easeOut' }}
            />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <motion.span
              className="text-2xl font-black"
              style={{ color: getColor(score) }}
              key={score}
            >
              {score}
            </motion.span>
          </div>
        </div>
        <div className="flex-1 space-y-2">
          {[
            { label: 'DSGVO', val: score >= 90 ? 95 : 38, color: '#3b82f6' },
            { label: 'Barrierefr.', val: score >= 90 ? 99 : 51, color: '#8b5cf6' },
            { label: 'Cookies', val: score >= 90 ? 97 : 42, color: '#06b6d4' },
          ].map((item) => (
            <div key={item.label}>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-gray-500">{item.label}</span>
                <span className="font-semibold text-gray-700">{item.val}%</span>
              </div>
              <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                <motion.div
                  className="h-full rounded-full"
                  style={{ backgroundColor: item.color }}
                  initial={{ width: 0 }}
                  animate={{ width: `${item.val}%` }}
                  transition={{ duration: 1.2, delay: 0.3, ease: 'easeOut' }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-3 gap-2">
        {[
          { label: 'Issues', val: animating ? '0' : '23', color: 'text-red-500' },
          { label: 'Fixes', val: animating ? '23' : '0', color: 'text-green-500' },
          { label: 'Report', val: 'PDF', color: 'text-blue-500' },
        ].map((item) => (
          <div key={item.label} className="bg-gray-50 rounded-xl p-3 text-center">
            <p className={`text-lg font-black ${item.color}`}>{item.val}</p>
            <p className="text-xs text-gray-400 mt-0.5">{item.label}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

function FeatureCard({ icon, title, description, tag }: { icon: React.ReactNode; title: string; description: string; tag?: string }) {
  return (
    <div className="group relative bg-white rounded-2xl p-7 border border-gray-100 hover:border-blue-200 hover:shadow-xl transition-all duration-300 cursor-default">
      {tag && (
        <span className="absolute top-5 right-5 text-xs bg-blue-50 text-blue-600 font-semibold px-2.5 py-1 rounded-full border border-blue-100">
          {tag}
        </span>
      )}
      <div className="w-12 h-12 bg-gradient-to-br from-blue-50 to-purple-50 rounded-xl flex items-center justify-center text-blue-600 mb-5 group-hover:scale-110 transition-transform duration-300">
        {icon}
      </div>
      <h3 className="text-base font-bold text-gray-900 mb-2">{title}</h3>
      <p className="text-sm text-gray-500 leading-relaxed">{description}</p>
    </div>
  );
}

function ScanInputMockup() {
  const [scanning, setScanning] = useState(false);
  const [done, setDone] = useState(false);
  const [progress, setProgress] = useState(0);

  const startScan = () => {
    if (scanning || done) return;
    setScanning(true);
    let p = 0;
    const iv = setInterval(() => {
      p += Math.random() * 8 + 2;
      if (p >= 100) { p = 100; clearInterval(iv); setDone(true); setScanning(false); }
      setProgress(Math.min(p, 100));
    }, 120);
  };

  return (
    <div className="bg-white rounded-3xl shadow-2xl border border-gray-100 p-8 w-full max-w-md mx-auto">
      <p className="text-xs text-gray-400 uppercase tracking-widest font-medium mb-4">Live-Scanner</p>
      <div className="flex gap-2 mb-4">
        <div className="flex-1 flex items-center gap-2 bg-gray-50 border border-gray-200 rounded-xl px-4 py-3">
          <Search className="w-4 h-4 text-gray-400" />
          <span className="text-sm text-gray-500 font-mono">ihre-website.de</span>
        </div>
        <button
          onClick={startScan}
          className="px-5 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white text-sm font-bold rounded-xl hover:opacity-90 transition-opacity"
        >
          Scan
        </button>
      </div>

      {(scanning || done) && (
        <div className="space-y-3">
          <div className="flex justify-between text-xs mb-1">
            <span className="text-gray-500">{done ? 'Scan abgeschlossen' : 'Analysiere...'}</span>
            <span className="font-semibold text-gray-700">{Math.round(progress)}%</span>
          </div>
          <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
            <motion.div
              className="h-full bg-gradient-to-r from-blue-500 to-purple-500 rounded-full"
              animate={{ width: `${progress}%` }}
              transition={{ duration: 0.1 }}
            />
          </div>
          {done && (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="grid grid-cols-3 gap-2 pt-2">
              {[
                { label: '23 Issues', color: 'bg-red-50 text-red-600 border-red-100' },
                { label: '4 Kritisch', color: 'bg-orange-50 text-orange-600 border-orange-100' },
                { label: '97 Checks', color: 'bg-blue-50 text-blue-600 border-blue-100' },
              ].map((b) => (
                <div key={b.label} className={`${b.color} border rounded-lg px-2 py-1.5 text-center text-xs font-semibold`}>
                  {b.label}
                </div>
              ))}
            </motion.div>
          )}
        </div>
      )}

      {!scanning && !done && (
        <div className="flex gap-2 flex-wrap">
          {['DSGVO', 'BFSG', 'TCF 2.2', 'TTDSG'].map((tag) => (
            <span key={tag} className="text-xs bg-gray-50 border border-gray-200 text-gray-500 px-3 py-1 rounded-full">
              {tag}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

function AIFixMockup() {
  const [applied, setApplied] = useState(false);

  return (
    <div className="bg-white rounded-3xl shadow-2xl border border-gray-100 overflow-hidden w-full max-w-md mx-auto">
      <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-purple-500" />
          <span className="text-sm font-semibold text-gray-700">KI-Fix generiert</span>
        </div>
        <span className="text-xs bg-green-50 text-green-600 border border-green-100 rounded-full px-2.5 py-1 font-medium">Ready</span>
      </div>
      <div className="px-6 py-4">
        <div className="flex items-start gap-3 mb-4">
          <AlertTriangle className="w-4 h-4 text-orange-500 mt-0.5 flex-shrink-0" />
          <div>
            <p className="text-xs font-semibold text-gray-800">Fehlendes Cookie-Consent Banner</p>
            <p className="text-xs text-gray-400 mt-0.5">DSGVO Art. 6 · Kritisch</p>
          </div>
        </div>
        <div className="bg-gray-900 rounded-xl p-4 font-mono text-xs mb-4 overflow-hidden">
          <p className="text-gray-500 mb-1">{'// cookie-consent.js'}</p>
          <p className="text-blue-400">{'<script src='}<span className="text-green-400">'"https://cdn.complyo.tech/banner.js"'</span>{' />'}</p>
          <p className="text-gray-300">{'data-site-id='}<span className="text-yellow-300">'"abc-123"'</span></p>
        </div>
        <button
          onClick={() => setApplied(true)}
          className={`w-full py-3 rounded-xl text-sm font-bold transition-all ${applied
            ? 'bg-green-50 text-green-600 border border-green-200'
            : 'bg-gradient-to-r from-blue-600 to-purple-600 text-white hover:opacity-90'}`}
        >
          {applied ? <span className="flex items-center justify-center gap-2"><Check className="w-4 h-4" /> Angewendet</span> : 'Fix anwenden'}
        </button>
      </div>
    </div>
  );
}

export default function ComplyoViralLanding() {
  const [expandedFaq, setExpandedFaq] = useState<number | null>(null);
  const [isScrolled, setIsScrolled] = useState(false);
  const heroRef = useRef(null);
  const { scrollYProgress } = useScroll({ target: heroRef, offset: ['start start', 'end start'] });
  const heroY = useTransform(scrollYProgress, [0, 1], [0, 100]);
  const heroOpacity = useTransform(scrollYProgress, [0, 0.8], [1, 0]);

  useEffect(() => {
    const handleScroll = () => setIsScrolled(window.scrollY > 50);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const features = [
    'DSGVO-Prüfung', 'BFSG 2025', 'Cookie-Consent', 'Impressum-Check',
    'WCAG 2.1 AA', 'KI-Code-Fixes', 'TCF 2.2', 'PDF-Export', 'Risiko-Radar',
    'TTDSG', 'Alt-Text-KI', 'Live-Scanner', 'KI-Rechtstexte', 'Git-Integration',
  ];

  const faqs = [
    {
      q: 'Was ist der Unterschied zu Overlay-Lösungen wie Eye-Able®?',
      a: 'Im Gegensatz zu Overlay-Widgets bietet Complyo echte Code-Fixes. Nachhaltige Compliance ohne Drittanbieter-Abhängigkeit, bessere Performance und echte Barrierefreiheit statt kosmetischer Korrekturen.'
    },
    {
      q: 'Brauche ich technische Kenntnisse?',
      a: 'Nein. Alles wird Schritt-für-Schritt erklärt. Wenn Sie Copy-Paste können, können Sie Ihre Website compliant machen. Für den Expert-Plan übernehmen wir die Implementierung für Sie.'
    },
    {
      q: 'Wie schnell sehe ich Ergebnisse?',
      a: 'Die meisten Kunden haben ihre Website innerhalb von 24 Stunden compliant gemacht. Der Scan dauert 90 Sekunden, die Implementierung 1–3 Stunden.'
    },
    {
      q: 'Was ist, wenn ich bereits eine Abmahnung erhalten habe?',
      a: 'Unser Expert-Plan beinhaltet direkten Anwalts-Support für akute Fälle. Kontaktieren Sie uns sofort über das Kontaktformular.'
    },
    {
      q: 'Ist Complyo WCAG 2.1 AA konform?',
      a: 'Ja. Complyo prüft Ihre Website nach allen WCAG 2.1 Level AA Kriterien — über 127 Prüfpunkte mit konkreten Handlungsempfehlungen.'
    },
    {
      q: 'Wie funktioniert die Geld-zurück-Garantie?',
      a: 'Testen Sie 14 Tage risikofrei. Nicht zufrieden? Eine E-Mail an support@complyo.tech und wir erstatten Ihren Kaufpreis vollständig — keine Fragen.'
    },
  ];

  const appUrl = process.env.NODE_ENV === 'production' ? 'https://app.complyo.de' : 'http://localhost:3001';

  return (
    <div className="min-h-screen bg-white text-gray-900 overflow-x-hidden">

      {/* Nav */}
      <header>
        <nav
          role="navigation"
          aria-label="Hauptnavigation"
          className={`fixed top-0 left-0 right-0 z-50 transition-all duration-500 ${
            isScrolled ? 'bg-white/95 backdrop-blur-xl border-b border-gray-100 shadow-sm' : 'bg-transparent'
          }`}
        >
          <div className="max-w-7xl mx-auto px-6 lg:px-8">
            <div className="flex justify-between items-center h-18 py-4">
              <a href="/" className="flex items-center gap-3">
                <Logo size="lg" variant="light" />
              </a>
              <div className="hidden md:flex items-center gap-8">
                {[['#features', 'Features'], ['#how-it-works', 'So funktioniert\'s'], ['#pricing', 'Preise'], ['#faq', 'FAQ']].map(([href, label]) => (
                  <a key={href} href={href} className="text-sm text-gray-500 hover:text-gray-900 transition-colors font-medium">
                    {label}
                  </a>
                ))}
              </div>
              <div className="flex items-center gap-3">
                <a href={`${appUrl}/login`} className="hidden md:block text-sm text-gray-600 hover:text-gray-900 font-medium transition-colors px-4 py-2">
                  Anmelden
                </a>
                <a
                  href={appUrl}
                  className="inline-flex items-center gap-2 px-5 py-2.5 bg-gray-900 hover:bg-gray-700 text-white text-sm font-semibold rounded-xl transition-all"
                >
                  Kostenlos starten
                  <ArrowRight className="w-3.5 h-3.5" />
                </a>
              </div>
            </div>
          </div>
        </nav>
      </header>

      <main role="main">

        {/* Hero */}
        <section ref={heroRef} className="relative min-h-screen flex flex-col items-center justify-center pt-24 pb-16 px-6 overflow-hidden">
          {/* Subtle grid background */}
          <div className="absolute inset-0 bg-[linear-gradient(to_right,#f0f0f0_1px,transparent_1px),linear-gradient(to_bottom,#f0f0f0_1px,transparent_1px)] bg-[size:64px_64px] opacity-40 pointer-events-none" />
          {/* Radial gradient overlay */}
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_60%_at_50%_-10%,rgba(99,102,241,0.08),transparent)] pointer-events-none" />

          <motion.div style={{ y: heroY, opacity: heroOpacity }} className="relative z-10 max-w-5xl mx-auto text-center">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
              className="inline-flex items-center gap-2 bg-blue-50 border border-blue-100 rounded-full px-4 py-2 mb-8"
            >
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
              <span className="text-sm font-medium text-blue-700">Über 2.500 Websites geschützt</span>
            </motion.div>

            <motion.h1
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, delay: 0.1 }}
              className="text-6xl md:text-8xl font-black tracking-tight leading-[0.95] mb-6"
            >
              <span className="text-gray-900">Website</span>
              <br />
              <span className="bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 bg-clip-text text-transparent">
                Compliance
              </span>
              <br />
              <span className="text-gray-900">in Sekunden.</span>
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, delay: 0.2 }}
              className="text-xl md:text-2xl text-gray-500 mb-10 max-w-2xl mx-auto leading-relaxed font-light"
            >
              KI-gestützte Prüfung und Fixes für DSGVO, BFSG, TTDSG und Cookie-Consent — ohne technische Vorkenntnisse.
            </motion.p>

            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, delay: 0.3 }}
              className="flex flex-col sm:flex-row gap-3 justify-center mb-16"
            >
              <a
                href={appUrl}
                className="inline-flex items-center justify-center gap-2.5 px-8 py-4 bg-gray-900 hover:bg-gray-700 text-white font-semibold text-base rounded-2xl transition-all shadow-lg shadow-gray-900/20 hover:shadow-gray-900/30"
              >
                Jetzt kostenlos starten
                <ArrowRight className="w-4 h-4" />
              </a>
              <a
                href="#how-it-works"
                className="inline-flex items-center justify-center gap-2.5 px-8 py-4 bg-white border border-gray-200 hover:border-gray-300 hover:bg-gray-50 text-gray-700 font-semibold text-base rounded-2xl transition-all"
              >
                Wie es funktioniert
              </a>
            </motion.div>

            {/* Stats row */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.5 }}
              className="flex justify-center items-center gap-8 md:gap-16 mb-16"
            >
              {[
                { value: '2.500+', label: 'Websites' },
                { value: '90s', label: 'Scan-Zeit' },
                { value: '0', label: 'Abmahnungen' },
                { value: '127+', label: 'Prüfpunkte' },
              ].map((stat, i) => (
                <div key={i} className="text-center">
                  <p className="text-2xl md:text-3xl font-black text-gray-900">{stat.value}</p>
                  <p className="text-xs text-gray-400 uppercase tracking-widest mt-1">{stat.label}</p>
                </div>
              ))}
            </motion.div>

            {/* Hero mockup */}
            <motion.div
              initial={{ opacity: 0, y: 60, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              transition={{ duration: 0.9, delay: 0.4 }}
              className="flex justify-center"
            >
              <ComplianceScoreMockup />
            </motion.div>
          </motion.div>
        </section>

        {/* Scrolling Feature Banner */}
        <div className="border-y border-gray-100 py-4 overflow-hidden bg-gray-50/60">
          <div className="flex animate-scroll">
            {[...features, ...features].map((f, i) => (
              <div key={i} className="flex-shrink-0 mx-3 flex items-center gap-2 text-sm text-gray-500 font-medium whitespace-nowrap">
                <div className="w-1.5 h-1.5 rounded-full bg-blue-400" />
                {f}
              </div>
            ))}
          </div>
        </div>

        {/* Feature: Scanner */}
        <section className="py-32 px-6">
          <div className="max-w-6xl mx-auto">
            <div className="grid md:grid-cols-2 gap-16 items-center">
              <SlideInSection from="left">
                <p className="text-xs text-blue-600 font-bold uppercase tracking-widest mb-4">Schritt 1</p>
                <h2 className="text-4xl md:text-5xl font-black text-gray-900 leading-tight mb-6">
                  Website scannen — in 90 Sekunden.
                </h2>
                <p className="text-lg text-gray-500 leading-relaxed mb-8">
                  Geben Sie Ihre URL ein. Unsere KI analysiert DSGVO, BFSG, TTDSG, WCAG 2.1, Cookie-Consent und Impressum — vollautomatisch in unter 90 Sekunden.
                </p>
                <ul className="space-y-3">
                  {['Keine Installation nötig', 'Alle Seiten werden gecrawlt', 'Priorisierte Issue-Liste'].map((item) => (
                    <li key={item} className="flex items-center gap-3 text-gray-700">
                      <div className="w-5 h-5 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0">
                        <Check className="w-3 h-3 text-green-600" />
                      </div>
                      {item}
                    </li>
                  ))}
                </ul>
              </SlideInSection>
              <SlideInSection from="right" delay={0.1}>
                <ScanInputMockup />
              </SlideInSection>
            </div>
          </div>
        </section>

        {/* Feature: KI Fixes */}
        <section className="py-32 px-6 bg-gray-50">
          <div className="max-w-6xl mx-auto">
            <div className="grid md:grid-cols-2 gap-16 items-center">
              <SlideInSection from="left" delay={0.1} className="order-2 md:order-1">
                <AIFixMockup />
              </SlideInSection>
              <SlideInSection from="right" className="order-1 md:order-2">
                <p className="text-xs text-purple-600 font-bold uppercase tracking-widest mb-4">Schritt 2</p>
                <h2 className="text-4xl md:text-5xl font-black text-gray-900 leading-tight mb-6">
                  KI generiert fix&shy;fertige Code-Snippets.
                </h2>
                <p className="text-lg text-gray-500 leading-relaxed mb-8">
                  Für jedes gefundene Problem erstellt die KI sofort anwendbare Lösungen — kommentiert, erklärt, copy-paste-ready. Kein Rätselraten mehr.
                </p>
                <ul className="space-y-3">
                  {['Sofort einsatzbereiter Code', 'Schritt-für-Schritt Erklärung', 'KI-geprüfte Vorlage (juristisch prüfen lassen)'].map((item) => (
                    <li key={item} className="flex items-center gap-3 text-gray-700">
                      <div className="w-5 h-5 rounded-full bg-purple-100 flex items-center justify-center flex-shrink-0">
                        <Check className="w-3 h-3 text-purple-600" />
                      </div>
                      {item}
                    </li>
                  ))}
                </ul>
              </SlideInSection>
            </div>
          </div>
        </section>

        {/* Feature: Monitoring */}
        <section className="py-32 px-6">
          <div className="max-w-6xl mx-auto">
            <div className="grid md:grid-cols-2 gap-16 items-center">
              <SlideInSection from="left">
                <p className="text-xs text-green-600 font-bold uppercase tracking-widest mb-4">Schritt 3</p>
                <h2 className="text-4xl md:text-5xl font-black text-gray-900 leading-tight mb-6">
                  Dauerhaft compliant bleiben.
                </h2>
                <p className="text-lg text-gray-500 leading-relaxed mb-8">
                  Gesetze ändern sich. Complyo überwacht Ihre Website kontinuierlich und alarmiert Sie bei neuen Risiken — bevor es zur Abmahnung kommt.
                </p>
                <ul className="space-y-3">
                  {['Automatisches Monitoring', 'Sofort-Alerts bei Änderungen', 'Score-Verlauf & Reports'].map((item) => (
                    <li key={item} className="flex items-center gap-3 text-gray-700">
                      <div className="w-5 h-5 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0">
                        <Check className="w-3 h-3 text-green-600" />
                      </div>
                      {item}
                    </li>
                  ))}
                </ul>
              </SlideInSection>
              <SlideInSection from="right" delay={0.1}>
                {/* Monitoring mockup */}
                <div className="bg-white rounded-3xl shadow-2xl border border-gray-100 p-8 w-full max-w-sm mx-auto">
                  <div className="flex items-center justify-between mb-6">
                    <p className="text-xs text-gray-400 uppercase tracking-widest font-medium">Monitoring</p>
                    <div className="flex items-center gap-1.5">
                      <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                      <span className="text-xs text-green-600 font-medium">Live</span>
                    </div>
                  </div>
                  <div className="space-y-3 mb-6">
                    {[
                      { label: 'DSGVO-Status', status: 'Konform', color: 'text-green-600 bg-green-50 border-green-100' },
                      { label: 'WCAG 2.1 AA', status: 'Konform', color: 'text-green-600 bg-green-50 border-green-100' },
                      { label: 'Cookie-Banner', status: 'Aktiv', color: 'text-blue-600 bg-blue-50 border-blue-100' },
                      { label: 'Impressum', status: 'Aktuell', color: 'text-green-600 bg-green-50 border-green-100' },
                    ].map((row) => (
                      <div key={row.label} className="flex items-center justify-between">
                        <span className="text-sm text-gray-700">{row.label}</span>
                        <span className={`text-xs font-semibold border rounded-full px-2.5 py-1 ${row.color}`}>{row.status}</span>
                      </div>
                    ))}
                  </div>
                  <div className="bg-blue-50 border border-blue-100 rounded-xl p-4 flex items-start gap-3">
                    <Bell className="w-4 h-4 text-blue-500 mt-0.5 flex-shrink-0" />
                    <div>
                      <p className="text-xs font-semibold text-blue-800">Letzter Scan vor 2h</p>
                      <p className="text-xs text-blue-600 mt-0.5">Keine neuen Issues gefunden.</p>
                    </div>
                  </div>
                </div>
              </SlideInSection>
            </div>
          </div>
        </section>

        {/* Feature Grid */}
        <section id="features" className="py-32 px-6 bg-gray-50">
          <div className="max-w-6xl mx-auto">
            <FadeInSection className="text-center mb-16">
              <p className="text-xs text-blue-600 font-bold uppercase tracking-widest mb-4">Alles inklusive</p>
              <h2 className="text-4xl md:text-5xl font-black text-gray-900 mb-4">
                Was Sie bekommen
              </h2>
              <p className="text-lg text-gray-500 max-w-xl mx-auto">
                Eine Plattform für alle Compliance-Anforderungen Ihrer Website.
              </p>
            </FadeInSection>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
              {[
                { icon: <Zap className="w-5 h-5" />, title: '90-Sekunden-Scan', description: 'KI analysiert DSGVO, TTDSG, Impressumspflicht und BFSG-Barrierefreiheit — vollautomatisch.', tag: 'Schnell' },
                { icon: <Code className="w-5 h-5" />, title: 'KI-Code-Fixes', description: 'Sofort anwendbare Code-Snippets für jedes gefundene Problem — kommentiert, copy-paste-ready.' },
                { icon: <Shield className="w-5 h-5" />, title: 'KI-Rechtstexte', description: 'Interner Generator: Datenschutz-, Impressum- und AGB-Texte auf Basis aktueller Gesetzeslage — automatisch aktualisiert.' },
                { icon: <Eye className="w-5 h-5" />, title: 'BFSG & WCAG 2.1 AA', description: 'Vollständige Prüfung nach Barrierefreiheitsstärkungsgesetz (ab Juni 2025 Pflicht) und WCAG 2.1.', tag: 'Neu' },
                { icon: <Scale className="w-5 h-5" />, title: 'DSGVO & TTDSG', description: 'Automatische Prüfung aller datenschutzrelevanten Bereiche inkl. Telekommunikations-Datenschutz.' },
                { icon: <Lock className="w-5 h-5" />, title: 'TCF 2.2 Cookie-Consent', description: 'IAB TCF 2.2-konformes Cookie-Banner mit Blockliste, Opt-Out und vollständigem Vendor-Management.' },
                { icon: <Sparkles className="w-5 h-5" />, title: 'Alt-Text KI', description: 'KI generiert automatisch barrierefreie Alt-Texte für alle Bilder Ihrer Website.' },
                { icon: <RefreshCw className="w-5 h-5" />, title: 'Kontinuierliches Monitoring', description: 'Automatische Überwachung mit Sofort-Alerts bei Gesetzesänderungen oder neuen Risiken.' },
                { icon: <FileText className="w-5 h-5" />, title: 'PDF/Excel Reports', description: 'Professionelle Compliance-Berichte für interne Dokumentation, Audits und Nachweise.' },
              ].map((f, i) => (
                <FadeInSection key={i} delay={i * 0.05}>
                  <FeatureCard {...f} />
                </FadeInSection>
              ))}
            </div>
          </div>
        </section>

        {/* Pricing */}
        <section id="pricing" className="py-32 px-6">
          <div className="max-w-5xl mx-auto">
            <FadeInSection className="text-center mb-16">
              <div className="inline-flex items-center gap-2 bg-orange-50 border border-orange-100 rounded-full px-4 py-2 mb-6">
                <Sparkles className="w-4 h-4 text-orange-500" />
                <span className="text-sm font-bold text-orange-600">Launch-Special: 50% Rabatt</span>
              </div>
              <h2 className="text-4xl md:text-5xl font-black text-gray-900 mb-4">Transparente Preise</h2>
              <p className="text-lg text-gray-500 max-w-xl mx-auto">Wählen Sie den Plan, der zu Ihnen passt.</p>
            </FadeInSection>

            <div className="grid md:grid-cols-2 gap-6 max-w-4xl mx-auto">
              {/* DIY */}
              <FadeInSection delay={0.1}>
                <div className="bg-white rounded-3xl border-2 border-gray-200 hover:border-gray-300 p-8 h-full transition-all">
                  <div className="mb-8">
                    <div className="w-10 h-10 bg-blue-50 rounded-xl flex items-center justify-center mb-4">
                      <Sparkles className="w-5 h-5 text-blue-600" />
                    </div>
                    <h3 className="text-xl font-bold text-gray-900">DIY mit KI</h3>
                    <p className="text-sm text-gray-400 mt-1">Für Selbermacher & Entwickler</p>
                    <div className="mt-6">
                      <span className="text-5xl font-black text-gray-900">49€</span>
                      <span className="text-gray-400 text-sm ml-2">/Monat zzgl. MwSt.</span>
                    </div>
                  </div>
                  <ul className="space-y-3 mb-8">
                    {[
                      'Unbegrenzte Compliance-Analysen',
                      'KI-generierte Code-Fixes',
                      'Schritt-für-Schritt Anleitungen',
                      'Score-Verlauf & Reports',
                      'PDF/Excel Export',
                      'KI-Rechtstexte mit Auto-Update',
                      'E-Mail Support',
                    ].map((f) => (
                      <li key={f} className="flex items-center gap-3 text-sm text-gray-700">
                        <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0" />
                        {f}
                      </li>
                    ))}
                  </ul>
                  <a
                    href={`${appUrl}/register?plan=complete`}
                    className="block w-full text-center bg-gray-900 hover:bg-gray-700 text-white font-semibold py-3.5 rounded-xl transition-all text-sm"
                  >
                    Jetzt starten
                  </a>
                </div>
              </FadeInSection>

              {/* Expert */}
              <FadeInSection delay={0.2}>
                <div className="relative bg-gray-900 rounded-3xl p-8 h-full text-white">
                  <div className="absolute -top-3.5 left-1/2 -translate-x-1/2">
                    <span className="bg-gradient-to-r from-yellow-400 to-orange-400 text-gray-900 font-bold text-xs px-4 py-1.5 rounded-full">
                      Empfohlen
                    </span>
                  </div>
                  <div className="mb-8 mt-2">
                    <div className="w-10 h-10 bg-white/10 rounded-xl flex items-center justify-center mb-4">
                      <Crown className="w-5 h-5 text-yellow-400" />
                    </div>
                    <h3 className="text-xl font-bold">Expertenservice</h3>
                    <p className="text-sm text-white/50 mt-1">Vollständige Umsetzung für Sie</p>
                    <div className="mt-6 space-y-2">
                      <div className="bg-white/10 rounded-xl px-4 py-3">
                        <p className="text-xs text-white/50 mb-0.5">Einmalig</p>
                        <p className="text-3xl font-black">2.990€ <span className="text-sm font-normal text-white/50">netto</span></p>
                      </div>
                      <div className="bg-white/10 rounded-xl px-4 py-3">
                        <p className="text-xs text-white/50 mb-0.5">Danach monatlich</p>
                        <p className="text-2xl font-black">39€<span className="text-sm font-normal text-white/50">/Monat</span></p>
                      </div>
                    </div>
                  </div>
                  <ul className="space-y-3 mb-8">
                    {[
                      'Vollständige Website-Analyse',
                      'Professionelle Code-Umsetzung',
                      'WCAG 2.1 AA Zertifizierung',
                      'Cookie-Consent Implementation',
                      'Monatliche Compliance-Updates',
                      'Priority Support',
                      'Monitoring & Alerts',
                    ].map((f) => (
                      <li key={f} className="flex items-center gap-3 text-sm text-white/80">
                        <Star className="w-4 h-4 text-yellow-400 flex-shrink-0" />
                        {f}
                      </li>
                    ))}
                  </ul>
                  <a
                    href="/contact?service=expert"
                    className="block w-full text-center bg-white hover:bg-gray-100 text-gray-900 font-semibold py-3.5 rounded-xl transition-all text-sm"
                  >
                    Beratung vereinbaren
                  </a>
                </div>
              </FadeInSection>
            </div>

            {/* Guarantee */}
            <FadeInSection delay={0.3} className="mt-10 max-w-lg mx-auto">
              <div className="flex items-center gap-4 bg-green-50 border border-green-100 rounded-2xl px-6 py-5">
                <Shield className="w-8 h-8 text-green-600 flex-shrink-0" />
                <div>
                  <p className="text-sm font-bold text-gray-900">14-Tage Geld-zurück-Garantie</p>
                  <p className="text-xs text-gray-500 mt-0.5">Nicht zufrieden? Vollständige Rückerstattung — keine Fragen.</p>
                </div>
              </div>
            </FadeInSection>
          </div>
        </section>

        {/* FAQ */}
        <section id="faq" className="py-32 px-6 bg-gray-50">
          <div className="max-w-2xl mx-auto">
            <FadeInSection className="text-center mb-12">
              <h2 className="text-4xl md:text-5xl font-black text-gray-900">FAQ</h2>
            </FadeInSection>
            <div className="space-y-2">
              {faqs.map((faq, i) => (
                <FadeInSection key={i} delay={i * 0.05}>
                  <div className="bg-white rounded-2xl border border-gray-100 overflow-hidden">
                    <button
                      onClick={() => setExpandedFaq(expandedFaq === i ? null : i)}
                      className="w-full px-6 py-5 flex items-center justify-between text-left hover:bg-gray-50 transition-colors"
                    >
                      <span className="font-semibold text-gray-900 text-sm pr-4">{faq.q}</span>
                      <motion.div animate={{ rotate: expandedFaq === i ? 180 : 0 }} transition={{ duration: 0.25 }}>
                        <ChevronDown className="w-4 h-4 text-gray-400 flex-shrink-0" />
                      </motion.div>
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
                          <p className="px-6 pb-5 text-sm text-gray-500 leading-relaxed border-t border-gray-100 pt-4">
                            {faq.a}
                          </p>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                </FadeInSection>
              ))}
            </div>
          </div>
        </section>

        {/* Final CTA */}
        <section className="py-32 px-6">
          <div className="max-w-3xl mx-auto text-center">
            <FadeInSection>
              <h2 className="text-5xl md:text-7xl font-black text-gray-900 leading-tight mb-6">
                Bereit für echte
                <br />
                <span className="bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 bg-clip-text text-transparent">
                  Compliance?
                </span>
              </h2>
              <p className="text-lg text-gray-500 mb-10 max-w-xl mx-auto">
                Schließen Sie sich über 2.500 Unternehmen an, die ihre Websites mit Complyo schützen.
              </p>
              <a
                href={appUrl}
                className="inline-flex items-center gap-3 px-10 py-5 bg-gray-900 hover:bg-gray-700 text-white font-bold text-lg rounded-2xl transition-all shadow-xl shadow-gray-900/20"
              >
                Jetzt kostenlos starten
                <ArrowRight className="w-5 h-5" />
              </a>
              <p className="mt-6 text-sm text-gray-400">
                Keine Kreditkarte · 14-Tage Geld-zurück-Garantie
              </p>
            </FadeInSection>
          </div>
        </section>

      </main>

      {/* Footer */}
      <footer role="contentinfo" className="border-t border-gray-100 py-16 px-6 bg-white">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-4 gap-10 mb-12">
            <div className="md:col-span-1">
              <Logo size="lg" variant="light" />
              <p className="text-sm text-gray-400 mt-4 leading-relaxed">
                Echte Compliance mit KI. DSGVO, Barrierefreiheit und Cookie-Consent in einem Tool.
              </p>
            </div>
            <div>
              <p className="text-sm font-semibold text-gray-800 mb-4">Produkt</p>
              <ul className="space-y-2.5 text-sm">
                {[['#features', 'Features'], ['#pricing', 'Preise'], ['#faq', 'FAQ']].map(([href, label]) => (
                  <li key={href}><a href={href} className="text-gray-400 hover:text-gray-700 transition-colors">{label}</a></li>
                ))}
              </ul>
            </div>
            <div>
              <p className="text-sm font-semibold text-gray-800 mb-4">Rechtliches</p>
              <ul className="space-y-2.5 text-sm">
                {[['/impressum', 'Impressum'], ['/datenschutz', 'Datenschutz'], ['/agb', 'AGB']].map(([href, label]) => (
                  <li key={href}><Link href={href} className="text-gray-400 hover:text-gray-700 transition-colors">{label}</Link></li>
                ))}
              </ul>
            </div>
            <div>
              <p className="text-sm font-semibold text-gray-800 mb-4">Kontakt</p>
              <ul className="space-y-2.5 text-sm">
                <li><a href="mailto:support@complyo.tech" className="text-gray-400 hover:text-gray-700 transition-colors">support@complyo.tech</a></li>
                <li><a href="/contact" className="text-gray-400 hover:text-gray-700 transition-colors">Kontaktformular</a></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-100 pt-8 flex flex-col md:flex-row justify-between items-center gap-4">
            <p className="text-xs text-gray-400">© 2025 Complyo GmbH. Alle Rechte vorbehalten.</p>
            <div className="flex gap-5">
              <a href="#" className="text-gray-300 hover:text-gray-600 transition-colors">
                <span className="sr-only">LinkedIn</span>
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z" />
                </svg>
              </a>
              <a href="#" className="text-gray-300 hover:text-gray-600 transition-colors">
                <span className="sr-only">Twitter</span>
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M23.953 4.57a10 10 0 01-2.825.775 4.958 4.958 0 002.163-2.723c-.951.555-2.005.959-3.127 1.184a4.92 4.92 0 00-8.384 4.482C7.69 8.095 4.067 6.13 1.64 3.162a4.822 4.822 0 00-.666 2.475c0 1.71.87 3.213 2.188 4.096a4.904 4.904 0 01-2.228-.616v.06a4.923 4.923 0 003.946 4.827 4.996 4.996 0 01-2.212.085 4.936 4.936 0 004.604 3.417 9.867 9.867 0 01-6.102 2.105c-.39 0-.779-.023-1.17-.067a13.995 13.995 0 007.557 2.209c9.053 0 13.998-7.496 13.998-13.985 0-.21 0-.42-.015-.63A9.935 9.935 0 0024 4.59z" />
                </svg>
              </a>
            </div>
          </div>
        </div>
      </footer>

    </div>
  );
}
