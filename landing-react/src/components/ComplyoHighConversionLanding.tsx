'use client';

import React, { useState, useRef } from 'react';
import { 
  Shield, 
  CheckCircle, 
  AlertTriangle,
  ArrowRight,
  Star,
  Clock,
  Zap,
  TrendingUp,
  Users,
  ChevronDown,
  Play
} from 'lucide-react';
import WebsiteScanner from './landing/WebsiteScanner';
import { Logo } from './Logo';

interface ComplyoLandingProps {
  variant: 'original' | 'high-conversion';
  sessionId: string;
}

/**
 * High-Conversion Landing Page im MovesMethod-Stil
 * Fokus auf Social Proof, Scarcity, Money-Back Guarantee
 * 
 * ✅ Barrierefreiheit: Semantisches HTML5 (header, nav, main, footer)
 */
export default function ComplyoHighConversionLanding({ variant, sessionId }: ComplyoLandingProps) {
  const [websiteUrl, setWebsiteUrl] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [expandedFaq, setExpandedFaq] = useState<number | null>(null);

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'https://api.complyo.tech';

  const handleAnalyze = async () => {
    if (!websiteUrl) return;
    
    setIsAnalyzing(true);
    // Redirect to full analysis
    window.location.href = `#analysis?url=${encodeURIComponent(websiteUrl)}`;
  };

  const handlePlanSelect = (plan: 'ki' | 'expert') => {
    window.location.href = `https://app.complyo.tech/register?plan=${plan}`;
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header mit Top Banner und Hero */}
      <header>
        {/* Navigation */}
        <nav className="bg-gray-950 border-b border-gray-800" role="navigation" aria-label="Hauptnavigation">
          <div className="container mx-auto px-6">
            <div className="flex justify-between items-center h-16">
              <a href="/" aria-label="Zur Startseite">
                <Logo size="lg" />
              </a>
              <div className="hidden md:flex items-center space-x-8">
                <a href="#pricing" className="text-gray-300 hover:text-white transition-colors">Preise</a>
                <a href="#faq" className="text-gray-300 hover:text-white transition-colors">FAQ</a>
                <a 
                  href={process.env.NODE_ENV === 'production' ? 'https://app.complyo.tech' : 'http://localhost:3001'}
                  className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
                >
                  Login
                </a>
              </div>
            </div>
          </div>
        </nav>
        
        {/* Top Banner - Scarcity */}
        <div className="bg-gradient-to-r from-red-600 to-orange-600 py-3 text-center font-bold text-sm md:text-base animate-pulse">
          🔥 HERBST-SALE! JETZT 70% SPAREN - NUR FÜR KURZE ZEIT 🔥
        </div>

        {/* Hero Section */}
        <div className="container mx-auto px-6 py-12 max-w-5xl text-center">
        <div className="inline-flex items-center gap-2 bg-green-500 bg-opacity-20 border border-green-500 rounded-full px-6 py-2 mb-6">
          <CheckCircle className="w-5 h-5 text-green-400" />
          <span className="text-sm font-bold">Über 2.500 Websites geschützt</span>
        </div>

        {/* Main Headline - MovesMethod Style */}
        <h1 className="text-4xl md:text-6xl font-black mb-6 leading-tight">
          WARUM 2.500+ UNTERNEHMEN DIESE EINFACHE TÄGLICHE ROUTINE NUTZEN,<br />
          <span className="text-yellow-400">UM ABMAHNUNGEN ZU VERMEIDEN</span><br />
          OHNE ANWALT & OHNE STRESS
        </h1>

        <p className="text-xl md:text-2xl text-gray-300 mb-4">
          Auch wenn Sie keine Ahnung von DSGVO haben, wenig Zeit haben, und "nicht technisch veranlagt" sind
        </p>

        <p className="text-lg text-gray-400 mb-8">
          Nur 15 Minuten Setup, einmal, für jede Branche oder Website-Typ
        </p>

        {/* Video Placeholder */}
        <div className="bg-gradient-to-br from-blue-900 to-purple-900 rounded-2xl p-8 mb-8 border-2 border-blue-500">
          <div className="aspect-video bg-gray-800 rounded-xl flex items-center justify-center mb-4">
            <Play className="w-20 h-20 text-blue-400" />
          </div>
          <p className="text-lg font-bold">
            🔊 Klicken Sie auf das Video, um mehr zu erfahren 👇
          </p>
        </div>

        {/* Primary CTA */}
        <button
          onClick={() => document.getElementById('pricing')?.scrollIntoView({ behavior: 'smooth' })}
          className="bg-green-600 hover:bg-green-700 text-white text-xl font-black py-6 px-12 rounded-xl shadow-2xl hover:scale-105 transition-all mb-3 w-full md:w-auto"
        >
          JA, ICH WILL JETZT LOSLEGEN
        </button>
        <p className="text-sm text-gray-400">
          Einmalige Zahlung - Lebenslanger Zugang
        </p>
        <p className="text-sm text-green-400 font-bold mt-2">
          ✓ 14-Tage Geld-zurück-Garantie - Keine Fragen
        </p>
      </div>
      </header>

      {/* Hauptinhalt */}
      <main role="main">
        {/* Social Proof Stats */}
        <div className="bg-gray-950 py-12">
        <div className="container mx-auto px-6">
          <div className="grid md:grid-cols-3 gap-8 text-center max-w-4xl mx-auto">
            <div>
              <div className="text-5xl md:text-6xl font-black text-blue-400 mb-2">2.500+</div>
              <div className="text-gray-400 uppercase text-sm font-bold">Geschützte Websites</div>
            </div>
            <div>
              <div className="text-5xl md:text-6xl font-black text-yellow-400 mb-2">50+</div>
              <div className="text-gray-400 uppercase text-sm font-bold">Länder</div>
            </div>
            <div>
              <div className="text-5xl md:text-6xl font-black text-green-400 mb-2">0</div>
              <div className="text-gray-400 uppercase text-sm font-bold">Abmahnungen bei Kunden</div>
            </div>
          </div>
        </div>
      </div>

      {/* Website Scanner */}
      <div className="bg-gradient-to-b from-gray-950 to-gray-900">
        <WebsiteScanner />
      </div>

      {/* Problem Section - MovesMethod "Breaking News" Style */}
      <div className="bg-gradient-to-br from-gray-900 to-gray-800 py-16">
        <div className="container mx-auto px-6 max-w-4xl">
          <div className="bg-red-600 text-white inline-block px-4 py-2 rounded-full text-sm font-black mb-6">
            🚨 ACHTUNG 🚨
          </div>
          
          <h2 className="text-4xl md:text-5xl font-black mb-8 leading-tight">
            DIE MEHRHEIT DER UNTERNEHMEN MACHT IHRE COMPLIANCE KOMPLETT FALSCH
          </h2>

          <p className="text-xl text-gray-300 mb-6">
            Wir kennen das nur zu gut. Es ist frustrierend, wenn Sie...
          </p>

          <div className="space-y-4 mb-8">
            {[
              'Ständig Angst vor einer Abmahnung haben, die 8.500€ oder mehr kostet',
              'Sich verwirrt und unsicher fühlen, welche Gesetze Sie einhalten müssen',
              'Jeden YouTube-"Hack" ausprobieren, nur um festzustellen, dass nichts funktioniert',
              'Tausende Euro für Anwälte ausgeben, die Ihnen nicht wirklich helfen',
              'Ihre Website aus Angst vor Strafen gar nicht erst online stellen'
            ].map((problem, i) => (
              <div key={i} className="flex items-start gap-3 bg-gray-800 p-4 rounded-lg">
                <AlertTriangle className="w-6 h-6 text-red-400 flex-shrink-0 mt-1" />
                <span className="text-gray-200">{problem}</span>
              </div>
            ))}
          </div>

          <div className="bg-yellow-500 bg-opacity-20 border-2 border-yellow-500 rounded-xl p-6 text-center">
            <p className="text-2xl font-bold mb-2">Aber keine Sorge…</p>
            <p className="text-lg text-gray-300">
              Es gibt eine <span className="text-yellow-400 font-bold">schnellere & einfachere Lösung</span>,<br />
              als alles, was Ihnen bisher erzählt wurde.
            </p>
          </div>
        </div>
      </div>

      {/* Solution Section */}
      <div className="bg-gray-950 py-16">
        <div className="container mx-auto px-6 max-w-4xl">
          <div className="bg-green-600 text-white inline-block px-4 py-2 rounded-full text-sm font-black mb-6">
            🚨 BREAKING NEWS 🚨
          </div>

          <h2 className="text-4xl md:text-5xl font-black mb-8 leading-tight">
            ES GIBT EINEN SCHNELLEREN & EINFACHEREN WEG<br />
            ZUR COMPLIANCE
          </h2>

          <p className="text-xl text-gray-300 mb-6">
            Sie haben wahrscheinlich schon durch das endlose Hamsterrad gedreht:
          </p>

          <div className="grid md:grid-cols-2 gap-4 mb-8">
            {[
              'Anwälte (500€+ pro Stunde)',
              'Datenschutzbeauftragte (3.000€/Jahr)',
              'Compliance-Berater (Tausende Euro)',
              'Online-Kurse (die nichts bewirken)',
              'Template-Downloads (veraltet)',
              'YouTube-Tutorials (widersprüchlich)'
            ].map((method, i) => (
              <div key={i} className="bg-red-900 bg-opacity-30 border border-red-500 p-4 rounded-lg flex items-center gap-3">
                <span className="text-2xl">❌</span>
                <span className="text-gray-200 line-through">{method}</span>
              </div>
            ))}
          </div>

          <div className="bg-gradient-to-r from-blue-900 to-purple-900 rounded-2xl p-8 border-2 border-blue-500">
            <h3 className="text-3xl font-black mb-6">Das Problem?</h3>
            <p className="text-xl text-gray-200 mb-4">
              All diese Lösungen sind nur <span className="text-red-400 font-bold">oberflächliche Pflaster</span>.
            </p>
            <p className="text-lg text-gray-300 mb-6">
              Sie werden vielleicht kurzfristig beruhigt…<br />
              …aber sie werden <span className="text-red-400 font-bold">NIEMALS</span> Ihre Website wirklich schützen.
            </p>

            <div className="bg-green-600 rounded-xl p-6">
              <p className="text-2xl font-black mb-3">Die Lösung:</p>
              <ul className="space-y-3 text-lg">
                <li className="flex items-start gap-3">
                  <CheckCircle className="w-6 h-6 text-green-200 flex-shrink-0 mt-1" />
                  <span>KI-gestützte automatische Prüfung</span>
                </li>
                <li className="flex items-start gap-3">
                  <CheckCircle className="w-6 h-6 text-green-200 flex-shrink-0 mt-1" />
                  <span>Schritt-für-Schritt Implementierung</span>
                </li>
                <li className="flex items-start gap-3">
                  <CheckCircle className="w-6 h-6 text-green-200 flex-shrink-0 mt-1" />
                  <span>Anwalt-geprüfte Rechtstexte</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* 3-Step System */}
      <div className="bg-gradient-to-br from-gray-900 to-gray-800 py-16">
        <div className="container mx-auto px-6 max-w-5xl">
          <h2 className="text-4xl md:text-5xl font-black text-center mb-4">
            DAS 3-SCHRITT COMPLYO-SYSTEM
          </h2>
          <p className="text-xl text-gray-400 text-center mb-12">
            Das alles verändert…
          </p>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                step: '1',
                title: 'Scannen',
                icon: <Zap className="w-12 h-12" />,
                description: 'KI analysiert Ihre Website in 90 Sekunden auf alle 4 Compliance-Säulen'
              },
              {
                step: '2',
                title: 'Fix-Code erhalten',
                icon: <Shield className="w-12 h-12" />,
                description: 'Sofort einsatzbereite Code-Snippets oder vollständige Rechtstexte'
              },
              {
                step: '3',
                title: 'Geschützt sein',
                icon: <CheckCircle className="w-12 h-12" />,
                description: 'Nie wieder Angst vor Abmahnungen - 14 Tage Geld-zurück-Garantie'
              }
            ].map((item, i) => (
              <div key={i} className="bg-gray-800 rounded-2xl p-8 border-2 border-blue-500 hover:scale-105 transition-transform">
                <div className="text-6xl font-black text-blue-400 mb-4">
                  {item.step}
                </div>
                <div className="text-blue-400 mb-4">{item.icon}</div>
                <h3 className="text-2xl font-bold mb-3">{item.title}</h3>
                <p className="text-gray-300">{item.description}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Pricing Section - Flash Sale */}
      <div id="pricing" className="bg-gray-950 py-16">
        <div className="container mx-auto px-6 max-w-4xl">
          <div className="text-center mb-12">
            <div className="bg-red-600 text-white inline-block px-6 py-3 rounded-full text-lg font-black mb-6 animate-pulse">
              🔥 HERBST-SALE! 70% RABATT - NUR FÜR KURZE ZEIT 🔥
            </div>
            
            <h2 className="text-4xl md:text-5xl font-black mb-4">
              Normalerweise Kosten:<br />
              <span className="line-through text-gray-500">147€ / Monat</span>
            </h2>

            <div className="text-6xl md:text-7xl font-black text-green-400 mb-6">
              NUR 39€
              <span className="text-2xl text-gray-400">/Monat</span>
            </div>

            <p className="text-xl text-gray-400 mb-8">
              Einmalige Zahlung - Lebenslanger Zugang zum KI-Plan
            </p>
          </div>

          {/* Plan Comparison */}
          <div className="grid md:grid-cols-2 gap-6 mb-12">
            {/* KI Plan */}
            <div className="bg-gradient-to-br from-blue-900 to-blue-800 rounded-2xl p-8 border-4 border-green-500 relative">
              <div className="absolute -top-4 left-1/2 transform -translate-x-1/2 bg-green-500 text-white px-6 py-2 rounded-full text-sm font-black">
                ⭐ BELIEBTESTER PLAN
              </div>
              
              <h3 className="text-3xl font-black mb-4 mt-6">KI Plan</h3>
              <div className="text-5xl font-black mb-6">
                39€
                <span className="text-lg text-gray-400">/Monat</span>
              </div>

              <ul className="space-y-3 mb-8">
                {[
                  '1 Website',
                  'KI-gestützte Prüfung',
                  'Code-Snippets & Fixes',
                  '10 PDF-Exporte / Monat',
                  'DSGVO + Barrierefreiheit',
                  'Email-Support'
                ].map((feature, i) => (
                  <li key={i} className="flex items-center gap-3">
                    <CheckCircle className="w-5 h-5 text-green-400 flex-shrink-0" />
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>

              <button
                onClick={() => handlePlanSelect('ki')}
                className="w-full bg-green-600 hover:bg-green-700 text-white font-black py-4 rounded-xl transition"
              >
                JETZT STARTEN →
              </button>
            </div>

            {/* Expert Plan */}
            <div className="bg-gradient-to-br from-purple-900 to-purple-800 rounded-2xl p-8 border-2 border-purple-500">
              <div className="bg-yellow-500 text-black px-4 py-2 rounded-full text-sm font-black mb-6 inline-block">
                💎 PREMIUM
              </div>
              
              <h3 className="text-3xl font-black mb-4">Expert Plan</h3>
              <div className="text-4xl font-black mb-2">
                2.000€
                <span className="text-lg text-gray-400"> einmalig</span>
              </div>
              <div className="text-2xl font-bold text-gray-400 mb-6">
                + 39€/Monat
              </div>

              <ul className="space-y-3 mb-8">
                {[
                  '1 Website (professionell)',
                  'Persönlicher Experten-Support',
                  'Vollständige Rechtstexte',
                  'Unbegrenzte Exporte',
                  'WordPress-Integration',
                  '24/7 Prioritäts-Support',
                  'Anwalt-Review (optional)'
                ].map((feature, i) => (
                  <li key={i} className="flex items-center gap-3">
                    <Star className="w-5 h-5 text-yellow-400 flex-shrink-0" />
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>

              <button
                onClick={() => handlePlanSelect('expert')}
                className="w-full bg-purple-600 hover:bg-purple-700 text-white font-black py-4 rounded-xl transition"
              >
                EXPERT WERDEN →
              </button>
            </div>
          </div>

          {/* Money-Back Guarantee */}
          <div className="bg-gradient-to-r from-green-900 to-blue-900 rounded-2xl p-8 border-2 border-green-500 text-center">
            <Shield className="w-16 h-16 text-green-400 mx-auto mb-4" />
            <h3 className="text-2xl font-black mb-3">
              14-TAGE GELD-ZURÜCK-GARANTIE
            </h3>
            <p className="text-lg text-gray-200">
              Einfach "Vielleicht" sagen und uns 14 Tage testen.<br />
              Wenn Sie nicht begeistert sind, gibt's Ihr Geld zurück - keine Fragen.
            </p>
            <p className="text-sm text-gray-400 mt-4">
              (Ja, so überzeugt sind wir)
            </p>
          </div>
        </div>
      </div>

      {/* FAQ Section */}
      <div className="bg-gray-900 py-16">
        <div className="container mx-auto px-6 max-w-4xl">
          <h2 className="text-4xl md:text-5xl font-black text-center mb-12">
            SIE HABEN FRAGEN, WIR HABEN ANTWORTEN
          </h2>

          <div className="space-y-4">
            {[
              {
                q: 'Kann ich das nicht alles kostenlos online finden?',
                a: 'Es gibt überall kostenlose Inhalte, aber was Sie hier bekommen, ist ein bewährtes System, das über 2.500 Unternehmen geholfen hat. Kein Zusammensetzen von zufälligen YouTube-Videos mehr. Wir haben Jahre und über 100.000€ investiert, um diesen Ansatz zu perfektionieren.'
              },
              {
                q: 'Ich habe keine Ahnung von DSGVO. Funktioniert das trotzdem?',
                a: '100%! Viele unserer besten Erfolgsgeschichten stammen von Leuten, die dachten, sie seien "nicht technisch". Dieses System funktioniert unabhängig von Ihrem Startpunkt, weil es nicht um Fachwissen geht - es geht um das Befolgen eines bewährten Prozesses.'
              },
              {
                q: 'Was ist, wenn ich bereits eine Abmahnung erhalten habe?',
                a: 'Kein Problem! Wir haben mit jedem erdenklichen Fall gearbeitet - von drohenden Abmahnungen bis hin zu laufenden Verfahren. Unser Expert-Plan beinhaltet sogar direkten Anwalts-Support für akute Fälle.'
              },
              {
                q: 'Funktioniert das wirklich?',
                a: 'Kurze Antwort: Ja, für über 2.500 Unternehmen bisher. Aber nehmen Sie nicht unser Wort dafür - deshalb bieten wir eine 14-Tage Geld-zurück-Garantie. Probieren Sie es selbst mit null Risiko aus.'
              },
              {
                q: 'Wie schnell sehe ich Ergebnisse?',
                a: 'Die meisten Kunden haben ihre Website innerhalb von 24 Stunden compliant gemacht. Der Scan dauert 90 Sekunden, die Implementierung der Fixes je nach Komplexität 1-3 Stunden.'
              },
              {
                q: 'Brauche ich technische Kenntnisse?',
                a: 'Nein! Alles wird Schritt-für-Schritt erklärt. Wenn Sie copy-paste können, können Sie Ihre Website compliant machen. Für den Expert-Plan übernehmen wir sogar die Implementierung für Sie.'
              },
              {
                q: 'Was ist der Unterschied zum Anwalt?',
                a: 'Ein Anwalt kostet 500€+/Stunde und erstellt Ihnen Dokumente. Wir prüfen, was wirklich nicht compliant ist, geben Ihnen sofort einsatzbare Lösungen UND überwachen kontinuierlich. Und das für einen Bruchteil der Kosten.'
              },
              {
                q: 'Wie funktioniert die Rückerstattung?',
                a: 'Einfach: Probieren Sie es 14 Tage aus. Wenn Sie nicht begeistert sind, schicken Sie eine Email an support@complyo.tech und wir erstatten Ihren kompletten Kaufpreis zurück - keine Fragen.'
              }
            ].map((faq, i) => (
              <div key={i} className="bg-gray-800 rounded-xl overflow-hidden border border-gray-700">
                <button
                  onClick={() => setExpandedFaq(expandedFaq === i ? null : i)}
                  className="w-full px-6 py-4 flex items-center justify-between text-left hover:bg-gray-750 transition"
                >
                  <span className="font-bold text-lg">{faq.q}</span>
                  <ChevronDown 
                    className={`w-6 h-6 transition-transform ${expandedFaq === i ? 'rotate-180' : ''}`}
                  />
                </button>
                {expandedFaq === i && (
                  <div className="px-6 pb-4 text-gray-300">
                    {faq.a}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Final CTA */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 py-16">
        <div className="container mx-auto px-6 max-w-4xl text-center">
          <h2 className="text-4xl md:text-5xl font-black mb-6">
            BEREIT, IHRE WEBSITE ZU SCHÜTZEN?
          </h2>
          <p className="text-xl mb-8">
            Schließen Sie sich 2.500+ geschützten Websites an
          </p>
          
          <button
            onClick={() => handlePlanSelect('ki')}
            className="bg-green-600 hover:bg-green-700 text-white text-2xl font-black py-6 px-12 rounded-xl shadow-2xl hover:scale-105 transition-all mb-4"
          >
            JETZT STARTEN - 70% RABATT
          </button>
          
          <p className="text-sm">
            ✓ 14-Tage Geld-zurück-Garantie<br />
            ✓ Keine versteckten Kosten<br />
            ✓ Sofortiger Zugang
          </p>
        </div>
      </div>
      </main>

      {/* Footer */}
      <footer role="contentinfo">
        <div className="bg-gray-950 py-8 text-center text-gray-500 text-sm">
          <p>© 2025 Complyo GmbH - Alle Rechte vorbehalten</p>
          <div className="flex justify-center gap-6 mt-4">
            <a href="/impressum" className="hover:text-white">Impressum</a>
            <a href="/datenschutz" className="hover:text-white">Datenschutz</a>
            <a href="/agb" className="hover:text-white">AGB</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
