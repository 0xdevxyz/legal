import React, { useState, useRef } from 'react';
import { 
  Shield, 
  Zap, 
  TrendingUp, 
  CheckCircle, 
  AlertTriangle,
  ArrowRight,
  Euro,
  Clock,
  Lock,
  Star,
  Users,
  Building2,
  FileCheck,
  Sparkles,
  ChevronDown,
  Play,
  Menu,
  X,
  Mail,
  Phone,
  MapPin
} from 'lucide-react';
import AccessibilityWidget from './AccessibilityWidget';
import CookieBanner from './CookieBanner';
import VideoDemo from './landing/VideoDemo';

interface ComplyoViralLandingProps {
  variant: 'viral' | 'high-conversion';
  sessionId: string;
}

interface RiskCategory {
  id: string;
  label: string;
  icon: string;
  detected: boolean;
  severity: string;
  risk_min: number;
  risk_max: number;
  risk_range: string | null;
  issues_count: number;
}

interface AnalysisResult {
  url: string;
  score: number;
  risk_categories: RiskCategory[];
  total_risk_range: string;
  issues_count: number;
  critical_count: number;
}

const ComplyoViralLanding: React.FC<ComplyoViralLandingProps> = ({ variant, sessionId }) => {
  const [websiteUrl, setWebsiteUrl] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResults, setAnalysisResults] = useState<AnalysisResult | null>(null);
  const [showResults, setShowResults] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState<'ki' | 'expert' | null>(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'https://api.complyo.tech';

  // FIXED: URL Normalisierung - konsistent mit anderen Komponenten
  const normalizeUrl = (input: string): string => {
    if (!input || typeof input !== 'string') {
      throw new Error('Ungültige URL');
    }

    let cleaned = input.trim().toLowerCase(); // Konsistente Kleinschreibung
    
    if (!cleaned) {
      throw new Error('URL darf nicht leer sein');
    }

    // Protokoll hinzufügen wenn nötig
    if (!cleaned.startsWith('http://') && !cleaned.startsWith('https://')) {
      if (cleaned.startsWith('www.')) {
        cleaned = 'https://' + cleaned;
      } else {
        cleaned = 'https://' + cleaned;
      }
    }

    // URL-Objekt für saubere Normalisierung
    try {
      const urlObj = new URL(cleaned);
      
      // FIXED: Entferne www. Präfix für konsistente Hashes
      let hostname = urlObj.hostname;
      if (hostname.startsWith('www.')) {
        hostname = hostname.substring(4);
      }
      
      let normalized = `${urlObj.protocol}//${hostname}`;
      
      if (urlObj.port && urlObj.port !== '80' && urlObj.port !== '443') {
        normalized += `:${urlObj.port}`;
      }
      
      if (urlObj.pathname && urlObj.pathname !== '/' && urlObj.pathname !== '') {
        normalized += urlObj.pathname.replace(/\/+$/, '');
      }
      
      return normalized;
    } catch (e) {
      throw new Error('Ungültiges URL-Format');
    }
  };

  const analyzeWebsite = async () => {
    if (isAnalyzing || !websiteUrl.trim()) {
      if (!websiteUrl.trim()) {
        alert('Bitte geben Sie eine Website-URL ein.');
      }
      return;
    }

    // FIXED: Verbesserte URL-Validierung
    let normalizedUrl: string;
    try {
      normalizedUrl = normalizeUrl(websiteUrl);
      new URL(normalizedUrl); // Validierung
    } catch (e) {
      alert('Bitte geben Sie eine gültige URL ein (z.B. example.com)');
      return;
    }

    setIsAnalyzing(true);
    setShowResults(false);

    try {
      const response = await fetch(`${API_BASE}/api/analyze-preview`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ url: normalizedUrl })
      });

      if (!response.ok) {
        throw new Error(`API Error: ${response.status}`);
      }

      const data = await response.json();
      
      const results: AnalysisResult = {
        url: data.url,
        score: data.score,
        risk_categories: data.risk_categories,
        total_risk_range: data.total_risk_range,
        issues_count: data.issues_count,
        critical_count: data.critical_count
      };
      
      setAnalysisResults(results);
      setShowResults(true);

      setTimeout(() => {
        document.getElementById('analysis-results')?.scrollIntoView({ behavior: 'smooth' });
      }, 100);

    } catch (error) {
      console.error('Analysis error:', error);
      alert('Fehler bei der Analyse. Bitte versuchen Sie es erneut.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handlePlanSelect = (plan: 'ki' | 'expert') => {
    setSelectedPlan(plan);
    // Redirect to Stripe Checkout or Dashboard Registration
    window.location.href = `https://app.complyo.tech/register?plan=${plan}`;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900 text-white">
      {/* Hero Section - VIRAL DESIGN */}
      <div className="relative overflow-hidden">
        {/* Animated Background */}
        <div className="absolute inset-0 opacity-20">
          <div className="absolute top-20 left-10 w-72 h-72 bg-blue-500 rounded-full mix-blend-multiply filter blur-xl animate-blob"></div>
          <div className="absolute top-40 right-10 w-72 h-72 bg-purple-500 rounded-full mix-blend-multiply filter blur-xl animate-blob animation-delay-2000"></div>
          <div className="absolute bottom-20 left-20 w-72 h-72 bg-pink-500 rounded-full mix-blend-multiply filter blur-xl animate-blob animation-delay-4000"></div>
        </div>

        {/* Navigation - RESPONSIVE */}
        <nav className="relative z-10 container mx-auto px-6 py-6">
          <div className="flex justify-between items-center">
            {/* Logo */}
            <div className="flex items-center gap-2">
              <Shield className="w-8 h-8 text-blue-400" />
              <span className="text-2xl font-bold">Complyo</span>
            </div>

            {/* Desktop Navigation */}
            <div className="hidden md:flex items-center gap-8">
              <a href="#features" className="hover:text-blue-400 transition font-medium">Features</a>
              <a href="#pricing" className="hover:text-blue-400 transition font-medium">Preise</a>
              <a href="#faq" className="hover:text-blue-400 transition font-medium">FAQ</a>
              <a href="https://app.complyo.tech" className="px-6 py-2 bg-blue-600 rounded-lg hover:bg-blue-700 transition font-semibold shadow-lg hover:shadow-xl">
                Login
              </a>
            </div>

            {/* Mobile Menu Button */}
            <button 
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden p-2 hover:bg-white hover:bg-opacity-10 rounded-lg transition"
              aria-label="Toggle menu"
            >
              {mobileMenuOpen ? (
                <X className="w-6 h-6" />
              ) : (
                <Menu className="w-6 h-6" />
              )}
            </button>
          </div>

          {/* Mobile Navigation */}
          {mobileMenuOpen && (
            <div className="md:hidden mt-4 py-4 bg-gray-800 bg-opacity-95 backdrop-blur-lg rounded-lg border border-gray-700 shadow-xl">
              <div className="flex flex-col space-y-1 px-4">
                <a 
                  href="#features" 
                  onClick={() => setMobileMenuOpen(false)}
                  className="px-4 py-3 hover:bg-blue-600 hover:bg-opacity-20 rounded-lg transition font-medium"
                >
                  Features
                </a>
                <a 
                  href="#pricing" 
                  onClick={() => setMobileMenuOpen(false)}
                  className="px-4 py-3 hover:bg-blue-600 hover:bg-opacity-20 rounded-lg transition font-medium"
                >
                  Preise
                </a>
                <a 
                  href="#faq" 
                  onClick={() => setMobileMenuOpen(false)}
                  className="px-4 py-3 hover:bg-blue-600 hover:bg-opacity-20 rounded-lg transition font-medium"
                >
                  FAQ
                </a>
                <div className="pt-2 mt-2 border-t border-gray-700">
                  <a 
                    href="https://app.complyo.tech" 
                    className="block px-4 py-3 bg-blue-600 rounded-lg hover:bg-blue-700 transition font-semibold text-center"
                  >
                    Login
                  </a>
                </div>
              </div>
            </div>
          )}
        </nav>

        {/* Hero Content */}
        <div className="relative z-10 container mx-auto px-6 pt-20 pb-32">
          <div className="max-w-5xl mx-auto text-center">
            {/* Social Proof Badge - VERSTÄRKT */}
            <div className="inline-flex items-center gap-3 bg-green-500 bg-opacity-20 border border-green-500 rounded-full px-8 py-3 mb-6 animate-pulse">
              <CheckCircle className="w-6 h-6 text-green-400" />
              <span className="text-sm font-bold">12.847 Abmahnungen 2024 • Über 2.500 Websites geschützt</span>
            </div>

            {/* Main Headline - VERSTÄRKTER FEAR TRIGGER */}
            <h1 className="text-5xl md:text-7xl font-bold mb-6 leading-tight">
              <span className="text-red-400">8.500€ Abmahnung</span><br />
              für <span className="text-yellow-400">fehlendes Cookie-Banner?</span><br />
              <span className="text-white text-4xl md:text-5xl mt-4 block">Das muss nicht sein.</span>
            </h1>

            {/* Sub-Headline - KONKRETE LÖSUNG */}
            <p className="text-xl md:text-2xl mb-3 text-gray-300 font-light">
              <span className="text-white font-bold">87% aller Websites</span> sind nicht compliant.<br />
              Schützen Sie sich in <span className="text-green-400 font-semibold">unter 3 Minuten</span> mit KI.
            </p>
            
            <p className="text-base text-gray-400 mb-8 max-w-2xl mx-auto">
              ✓ DSGVO • ✓ Barrierefreiheit (BFSG) • ✓ Impressum • ✓ Cookie-Compliance
            </p>
            
            {/* Trust Badges */}
            <div className="flex items-center justify-center gap-6 mb-8 flex-wrap">
              <div className="flex items-center gap-2 text-sm text-gray-400">
                <Shield className="w-5 h-5 text-blue-400" />
                <span>TÜV-geprüft</span>
              </div>
              <div className="flex items-center gap-2 text-sm text-gray-400">
                <CheckCircle className="w-5 h-5 text-green-400" />
                <span>Anwalt-geprüft</span>
              </div>
              <div className="flex items-center gap-2 text-sm text-gray-400">
                <Lock className="w-5 h-5 text-purple-400" />
                <span>DSGVO-konform</span>
              </div>
              <div className="flex items-center gap-2 text-sm text-gray-400">
                <Star className="w-5 h-5 text-yellow-400" />
                <span>4.9/5 (847 Reviews)</span>
              </div>
            </div>

            {/* CTA - Website Analyzer */}
            <div className="bg-gradient-to-br from-gray-900/80 via-blue-900/60 to-purple-900/80 backdrop-blur-lg rounded-2xl p-8 max-w-3xl mx-auto border border-blue-500/30 shadow-2xl">
              <h2 className="text-2xl font-bold mb-4">
                ⚡ Kostenloser Compliance-Check
              </h2>
              <p className="text-gray-300 mb-6">
                Prüfen Sie jetzt Ihr Abmahnrisiko – in 90 Sekunden
              </p>
              
              {/* FIXED: Input Field mit verbesserter URL-Behandlung */}
              <div className="flex flex-col md:flex-row gap-4">
                <div className="flex-1">
                  <input
                    ref={inputRef}
                    type="text"
                    value={websiteUrl}
                    onChange={(e) => {
                      // FIXED: Direktes State-Update ohne Re-Render-Probleme
                      setWebsiteUrl(e.target.value);
                    }}
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') {
                        analyzeWebsite();
                      }
                    }}
                    placeholder="Ihre Website (z.B. example.com)"
                    className="w-full px-6 py-4 rounded-lg text-gray-900 text-lg focus:outline-none focus:ring-4 focus:ring-blue-500 transition"
                    disabled={isAnalyzing}
                  />
                  <p className="text-sm text-gray-400 mt-2 text-left">
                    ✓ Mit oder ohne https:// • ✓ Mit oder ohne www.
                  </p>
                </div>
                <button
                  onClick={analyzeWebsite}
                  disabled={isAnalyzing}
                  className="px-8 py-4 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg font-bold text-lg hover:scale-105 transition-transform disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 whitespace-nowrap"
                >
                  {isAnalyzing ? (
                    <>
                      <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                      Analysiere...
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-5 h-5" />
                      Jetzt prüfen
                    </>
                  )}
                </button>
              </div>

              {/* Trust Badges */}
              <div className="flex items-center justify-center gap-6 mt-8 text-sm text-gray-400">
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-green-400" />
                  <span>Keine Anmeldung nötig</span>
                </div>
                <div className="flex items-center gap-2">
                  <Lock className="w-4 h-4 text-green-400" />
                  <span>100% DSGVO-konform</span>
                </div>
                <div className="flex items-center gap-2">
                  <Zap className="w-4 h-4 text-green-400" />
                  <span>Ergebnis in 90 Sek.</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Video Demo Section - WHITE BACKGROUND */}
      <VideoDemo />

      {/* Problem Amplification - Konkrete Risiken */}
      {!showResults && (
        <div className="bg-gray-950 py-16">
          <div className="container mx-auto px-6">
            <div className="max-w-6xl mx-auto">
              <h2 className="text-4xl font-bold text-center mb-4 text-red-400">
                ⚠️ Diese Fehler kosten Sie Tausende Euro
              </h2>
              <p className="text-center text-gray-400 mb-12 text-lg">
                Echte Abmahnfälle aus 2024 – Das kann auch Ihnen passieren
              </p>
              
              <div className="grid md:grid-cols-3 gap-6">
                {/* Case 1: Cookie Banner */}
                <div className="bg-gradient-to-br from-red-900 to-red-800 p-6 rounded-xl border-2 border-red-500 hover:scale-105 transition-transform">
                  <div className="text-4xl mb-4">🍪</div>
                  <h3 className="text-xl font-bold mb-2">Cookie-Banner fehlt</h3>
                  <div className="text-3xl font-bold text-red-300 mb-3">8.500€</div>
                  <p className="text-sm text-gray-300 mb-4">
                    Online-Shop ohne Cookie-Consent. Abmahnung wegen Google Analytics & Facebook Pixel.
                  </p>
                  <div className="text-xs text-red-200 bg-red-950 bg-opacity-50 p-2 rounded">
                    ⚖️ OLG Köln, Az. 6 U 65/20 – Schadenersatz + Anwaltskosten
                  </div>
                </div>

                {/* Case 2: Barrierefreiheit */}
                <div className="bg-gradient-to-br from-orange-900 to-orange-800 p-6 rounded-xl border-2 border-orange-500 hover:scale-105 transition-transform">
                  <div className="text-4xl mb-4">♿</div>
                  <h3 className="text-xl font-bold mb-2">Keine Barrierefreiheit</h3>
                  <div className="text-3xl font-bold text-orange-300 mb-3">12.000€</div>
                  <p className="text-sm text-gray-300 mb-4">
                    Seit Juni 2025 Pflicht (BFSG). Fehlende Alt-Texte, schlechte Kontraste, keine Tastaturbedienung.
                  </p>
                  <div className="text-xs text-orange-200 bg-orange-950 bg-opacity-50 p-2 rounded">
                    ⚖️ Bußgeld bis 100.000€ möglich – Behörden prüfen aktiv
                  </div>
                </div>

                {/* Case 3: Impressum */}
                <div className="bg-gradient-to-br from-yellow-900 to-yellow-800 p-6 rounded-xl border-2 border-yellow-500 hover:scale-105 transition-transform">
                  <div className="text-4xl mb-4">📄</div>
                  <h3 className="text-xl font-bold mb-2">Fehlerhaftes Impressum</h3>
                  <div className="text-3xl font-bold text-yellow-300 mb-3">3.200€</div>
                  <p className="text-sm text-gray-300 mb-4">
                    Unvollständige Angaben im Impressum. Fehlende Handelsregister-Nr., falsche Umsatzsteuer-ID.
                  </p>
                  <div className="text-xs text-yellow-200 bg-yellow-950 bg-opacity-50 p-2 rounded">
                    ⚖️ §5 TMG – Häufigster Abmahngrund in Deutschland
                  </div>
                </div>
              </div>

              {/* Statistik-Banner */}
              <div className="mt-12 bg-gradient-to-r from-red-900 to-purple-900 p-8 rounded-2xl border border-red-500">
                <div className="grid md:grid-cols-4 gap-6 text-center">
                  <div>
                    <div className="text-4xl font-bold text-red-300 mb-2">12.847</div>
                    <div className="text-sm text-gray-300">Abmahnungen 2024</div>
                  </div>
                  <div>
                    <div className="text-4xl font-bold text-yellow-300 mb-2">87%</div>
                    <div className="text-sm text-gray-300">Websites nicht compliant</div>
                  </div>
                  <div>
                    <div className="text-4xl font-bold text-orange-300 mb-2">6.200€</div>
                    <div className="text-sm text-gray-300">Durchschn. Abmahnkosten</div>
                  </div>
                  <div>
                    <div className="text-4xl font-bold text-green-300 mb-2">3 Min</div>
                    <div className="text-sm text-gray-300">Bis zum Schutz mit Complyo</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Analysis Results - PAYWALL */}
      {showResults && analysisResults && (
        <div id="analysis-results" className="bg-gray-900 py-20">
          <div className="container mx-auto px-6 max-w-6xl">
            <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-2xl p-8 border border-gray-700 shadow-2xl">
              
              {/* Score Display */}
              <div className="text-center mb-12">
                <h3 className="text-3xl font-bold mb-6">📊 Ihre Compliance-Analyse</h3>
                
                <div className={`inline-flex items-center justify-center w-48 h-48 rounded-full mb-6 ${
                  analysisResults.score >= 80 ? 'bg-gradient-to-br from-green-500 to-green-700' : 
                  analysisResults.score >= 60 ? 'bg-gradient-to-br from-yellow-500 to-yellow-700' : 
                  'bg-gradient-to-br from-red-500 to-red-700'
                } shadow-2xl`}>
                  <div className="text-center">
                    <div className="text-6xl font-bold text-white">{analysisResults.score}</div>
                    <div className="text-xl text-white opacity-90">/100</div>
                  </div>
                </div>

                <p className="text-xl text-gray-300">
                  {analysisResults.score >= 80 ? '✅ Gute Basis, aber Optimierung möglich' : 
                   analysisResults.score >= 60 ? '⚠️ Dringende Handlung empfohlen' : 
                   '🚨 Kritische Compliance-Lücken entdeckt'}
                </p>
              </div>

              {/* Risk Categories */}
              <div className="mb-12">
                <h4 className="text-2xl font-semibold mb-6 text-center">🔍 Gefundene Risiko-Kategorien</h4>
                <div className="grid md:grid-cols-2 gap-6">
                  {analysisResults.risk_categories.map((category) => (
                    <div 
                      key={category.id}
                      className={`p-6 rounded-xl border-2 transition-all ${
                        category.detected 
                          ? 'bg-red-900 bg-opacity-30 border-red-500 shadow-lg shadow-red-900/50' 
                          : 'bg-green-900 bg-opacity-20 border-green-500 shadow-lg shadow-green-900/30'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-3">
                          <span className="text-4xl">{category.icon}</span>
                          <h5 className="font-bold text-lg">{category.label}</h5>
                        </div>
                        {category.detected ? (
                          <AlertTriangle className="w-8 h-8 text-red-400" />
                        ) : (
                          <CheckCircle className="w-8 h-8 text-green-400" />
                        )}
                      </div>
                      {category.detected && category.risk_range && (
                        <div className="mt-3 p-3 bg-red-950 bg-opacity-50 rounded-lg">
                          <p className="text-red-300 font-semibold">
                            💰 Abmahnrisiko: {category.risk_range}
                          </p>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Total Risk - FEAR TRIGGER */}
              <div className="p-8 bg-gradient-to-r from-red-900 to-red-800 rounded-xl border-2 border-red-500 mb-12 shadow-2xl">
                <div className="flex items-center justify-between mb-4">
                  <h4 className="text-2xl font-bold text-white flex items-center gap-3">
                    <AlertTriangle className="w-8 h-8" />
                    Geschätztes Gesamt-Abmahnrisiko
                  </h4>
                </div>
                <div className="text-5xl font-bold text-white mb-3">{analysisResults.total_risk_range}</div>
                <p className="text-red-200 text-lg">
                  {analysisResults.critical_count} kritische Probleme gefunden • {analysisResults.issues_count} Issues gesamt
                </p>
                <p className="text-sm text-red-300 mt-2">
                  ⚠️ Jedes dieser Probleme kann einzeln abgemahnt werden
                </p>
              </div>
              
              {/* Paywall - CONVERSION OPTIMIZED */}
              <div className="bg-gradient-to-br from-blue-900 to-purple-900 p-10 rounded-2xl border-2 border-blue-500 shadow-2xl">
                <div className="text-center mb-8">
                  <h4 className="text-3xl font-bold mb-4 flex items-center justify-center gap-3">
                    <Lock className="w-8 h-8 text-yellow-400" />
                    Detaillierte Analyse & KI-Fix verfügbar
                  </h4>
                  <p className="text-xl text-gray-300 mb-2">
                    Sehen Sie exakt <strong className="text-white">WO</strong> die Probleme liegen, <strong className="text-white">WARUM</strong> sie kritisch sind 
                    und erhalten Sie <strong className="text-white">KI-generierte Lösungen</strong> in Sekunden.
                  </p>
                  <p className="text-lg text-yellow-300 font-semibold">
                    ⚡ Sparen Sie bis zu 10.000€ Anwaltskosten
                  </p>
                </div>
                
                {/* Plan Comparison */}
                <div className="grid md:grid-cols-2 gap-6 mb-8">
                  {/* KI Plan */}
                  <div className="bg-gray-900 bg-opacity-50 p-6 rounded-xl border border-blue-500 hover:scale-105 transition-transform">
                    <div className="flex items-center justify-between mb-4">
                      <h5 className="text-2xl font-bold text-white">🚀 KI Plan</h5>
                      <div className="text-right">
                        <div className="text-3xl font-bold text-blue-400">39€</div>
                        <div className="text-sm text-gray-400">netto/Monat</div>
                      </div>
                    </div>
                    <ul className="space-y-3 mb-6">
                      <li className="flex items-start gap-2">
                        <CheckCircle className="w-5 h-5 text-green-400 mt-0.5 flex-shrink-0" />
                        <span>1 Website professionell compliant</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <CheckCircle className="w-5 h-5 text-green-400 mt-0.5 flex-shrink-0" />
                        <span>KI-generierte Code-Snippets mit Anleitungen</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <CheckCircle className="w-5 h-5 text-green-400 mt-0.5 flex-shrink-0" />
                        <span>10 Exports/Monat</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <CheckCircle className="w-5 h-5 text-green-400 mt-0.5 flex-shrink-0" />
                        <span>Compliance-Dashboard</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <CheckCircle className="w-5 h-5 text-green-400 mt-0.5 flex-shrink-0" />
                        <span>Automatische Rechtsänderungs-Updates</span>
                      </li>
                    </ul>
                    <button 
                      onClick={() => handlePlanSelect('ki')}
                      className="w-full bg-gradient-to-r from-blue-500 to-blue-600 px-6 py-4 rounded-lg font-bold text-lg hover:scale-105 transition-transform shadow-lg flex items-center justify-center gap-2"
                    >
                      Jetzt starten
                      <ArrowRight className="w-5 h-5" />
                    </button>
                  </div>
                  
                  {/* Expert Plan */}
                  <div className="bg-gradient-to-br from-yellow-900 to-yellow-800 p-6 rounded-xl border-2 border-yellow-500 hover:scale-105 transition-transform relative overflow-hidden">
                    <div className="absolute top-0 right-0 bg-yellow-500 text-black px-4 py-1 text-sm font-bold rounded-bl-lg">
                      BELIEBT
                    </div>
                    <div className="flex items-start justify-between mb-4">
                      <h5 className="text-2xl font-bold text-white flex items-center gap-2">
                        <Star className="w-6 h-6 text-yellow-400" />
                        Expert Plan
                      </h5>
                      <div className="text-right">
                        <div className="text-sm text-yellow-300 line-through">5.000€</div>
                        <div className="text-3xl font-bold text-yellow-400">2.000€</div>
                        <div className="text-sm text-gray-300">einmalig + 39€/Monat</div>
                      </div>
                    </div>
                    <ul className="space-y-3 mb-6">
                      <li className="flex items-start gap-2">
                        <Star className="w-5 h-5 text-yellow-400 mt-0.5 flex-shrink-0" />
                        <span className="font-semibold">Alles aus KI Plan</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <Star className="w-5 h-5 text-yellow-400 mt-0.5 flex-shrink-0" />
                        <span>1 Website vollumfänglich professionell</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <Star className="w-5 h-5 text-yellow-400 mt-0.5 flex-shrink-0" />
                        <span className="font-semibold">KI-generierte vollständige Rechtstexte (Impressum, Datenschutz)</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <Star className="w-5 h-5 text-yellow-400 mt-0.5 flex-shrink-0" />
                        <span>Unbegrenzte Exports</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <Star className="w-5 h-5 text-yellow-400 mt-0.5 flex-shrink-0" />
                        <span className="font-semibold">Persönlicher Compliance-Berater</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <Star className="w-5 h-5 text-yellow-400 mt-0.5 flex-shrink-0" />
                        <span>Prioritäts-Support</span>
                      </li>
                    </ul>
                    <button 
                      onClick={() => handlePlanSelect('expert')}
                      className="w-full bg-gradient-to-r from-yellow-500 to-yellow-600 px-6 py-4 rounded-lg font-bold text-lg hover:scale-105 transition-transform shadow-lg flex items-center justify-center gap-2 text-black"
                    >
                      Expert Plan wählen
                      <ArrowRight className="w-5 h-5" />
                    </button>
                  </div>
                </div>
                
                {/* Money Back Guarantee */}
                <div className="text-center text-sm text-gray-300 bg-gray-900 bg-opacity-50 rounded-lg p-4">
                  <p className="flex items-center justify-center gap-2 mb-1">
                    <CheckCircle className="w-5 h-5 text-green-400" />
                    <strong className="text-white">14 Tage Geld-zurück-Garantie</strong>
                  </p>
                  <p className="text-xs text-yellow-300">
                    Hinweis: Garantie verfällt bei Nutzung der Fehlerkorrektur
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Social Proof Section */}
      <div className="bg-gray-900 py-20">
        <div className="container mx-auto px-6">
          <h3 className="text-4xl font-bold text-center mb-12">
            Über 2.500 Unternehmen vertrauen Complyo
          </h3>
          
          <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
              <div className="flex items-center gap-1 text-yellow-400 mb-4">
                {[...Array(5)].map((_, i) => <Star key={i} className="w-5 h-5 fill-current" />)}
              </div>
              <p className="text-gray-300 mb-4">
                "Innerhalb von 2 Stunden war unsere Website compliant. Hätten wir das über einen Anwalt gemacht, wären 5.000€ fällig gewesen."
              </p>
              <p className="text-sm text-gray-400">— Thomas M., E-Commerce Gründer</p>
            </div>

            <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
              <div className="flex items-center gap-1 text-yellow-400 mb-4">
                {[...Array(5)].map((_, i) => <Star key={i} className="w-5 h-5 fill-current" />)}
              </div>
              <p className="text-gray-300 mb-4">
                "Wir haben 12 kritische Compliance-Fehler gefunden. Eine Abmahnung hätte uns 30.000€ gekostet. Complyo hat uns gerettet!"
              </p>
              <p className="text-sm text-gray-400">— Sarah K., Online-Shop Inhaberin</p>
            </div>

            <div className="bg-gray-800 p-6 rounded-xl border border-gray-700">
              <div className="flex items-center gap-1 text-yellow-400 mb-4">
                {[...Array(5)].map((_, i) => <Star key={i} className="w-5 h-5 fill-current" />)}
              </div>
              <p className="text-gray-300 mb-4">
                "Als WordPress-Agentur nutzen wir Complyo für alle Kundenprojekte. Spart uns Wochen an Arbeit und schützt unsere Kunden."
              </p>
              <p className="text-sm text-gray-400">— Michael R., Agentur-Inhaber</p>
            </div>
          </div>
        </div>
      </div>

      {/* Benefits Section - WHY COMPLYO */}
      <div id="features" className="bg-gradient-to-br from-blue-900 to-purple-900 py-20">
        <div className="container mx-auto px-6">
          <div className="text-center mb-16">
            <h3 className="text-5xl font-bold mb-6">
              Warum ohne Complyo nicht mehr geht
            </h3>
            <p className="text-xl text-gray-300 max-w-3xl mx-auto">
              Die rechtlichen Anforderungen ändern sich ständig. Eine einzige verpasste Änderung kann Sie 50.000€ kosten.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8 max-w-6xl mx-auto">
            <div className="bg-white bg-opacity-10 backdrop-blur-lg p-6 rounded-xl border border-white border-opacity-20">
              <div className="w-14 h-14 bg-red-500 rounded-full flex items-center justify-center mb-4">
                <AlertTriangle className="w-8 h-8" />
              </div>
              <h4 className="text-xl font-bold mb-3">Abmahnwelle 2025</h4>
              <p className="text-gray-300">
                Seit Juni 2025 gilt das BFSG (Barrierefreiheitsgesetz). Über 80% der Websites sind noch nicht compliant.
              </p>
            </div>

            <div className="bg-white bg-opacity-10 backdrop-blur-lg p-6 rounded-xl border border-white border-opacity-20">
              <div className="w-14 h-14 bg-yellow-500 rounded-full flex items-center justify-center mb-4">
                <Euro className="w-8 h-8" />
              </div>
              <h4 className="text-xl font-bold mb-3">Bis zu 100.000€ Bußgeld</h4>
              <p className="text-gray-300">
                Fehlende Barrierefreiheit kann von Behörden mit bis zu 100.000€ geahndet werden. Zusätzlich drohen Abmahnungen.
              </p>
            </div>

            <div className="bg-white bg-opacity-10 backdrop-blur-lg p-6 rounded-xl border border-white border-opacity-20">
              <div className="w-14 h-14 bg-green-500 rounded-full flex items-center justify-center mb-4">
                <Clock className="w-8 h-8" />
              </div>
              <h4 className="text-xl font-bold mb-3">90 Sekunden Setup</h4>
              <p className="text-gray-300">
                Keine wochenlangen Anwalts-Konsultationen. Complyo analysiert und behebt Probleme in Minuten.
              </p>
            </div>

            <div className="bg-white bg-opacity-10 backdrop-blur-lg p-6 rounded-xl border border-white border-opacity-20">
              <div className="w-14 h-14 bg-blue-500 rounded-full flex items-center justify-center mb-4">
                <Sparkles className="w-8 h-8" />
              </div>
              <h4 className="text-xl font-bold mb-3">KI-Powered</h4>
              <p className="text-gray-300">
                Claude Sonnet 4 analysiert über 100 Compliance-Kriterien und generiert maßgeschneiderte Lösungen.
              </p>
            </div>
          </div>

          {/* Big CTA */}
          <div className="text-center mt-16">
            <a href="#" onClick={(e) => { e.preventDefault(); window.scrollTo({ top: 0, behavior: 'smooth' }); }} className="inline-flex items-center gap-3 px-12 py-6 bg-gradient-to-r from-green-500 to-green-600 rounded-xl font-bold text-2xl hover:scale-105 transition-transform shadow-2xl">
              Jetzt kostenlos prüfen
              <ArrowRight className="w-8 h-8" />
            </a>
            <p className="text-gray-400 mt-4">Keine Anmeldung • Kein Risiko • 90 Sekunden</p>
          </div>
        </div>
      </div>

      {/* FAQ Section */}
      <div id="faq" className="bg-gray-900 py-20">
        <div className="container mx-auto px-6 max-w-4xl">
          <div className="text-center mb-12">
            <h3 className="text-4xl font-bold mb-4">Häufig gestellte Fragen</h3>
            <p className="text-xl text-gray-400">Alles, was Sie über Complyo wissen müssen</p>
          </div>

          <div className="space-y-4">
            {/* FAQ 1 */}
            <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
              <h4 className="text-xl font-bold mb-3 flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-green-400" />
                Wie funktioniert die KI-Analyse?
              </h4>
              <p className="text-gray-300 pl-7">
                Unsere KI (Claude Sonnet 4) analysiert Ihre Website automatisch auf über 100 Compliance-Kriterien. Sie prüft rechtliche Texte, Cookie-Implementation, DSGVO-Konformität und Barrierefreiheit. Anschließend generiert sie maßgeschneiderte Lösungen in deutscher Rechtssprache.
              </p>
            </div>

            {/* FAQ 2 */}
            <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
              <h4 className="text-xl font-bold mb-3 flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-green-400" />
                Sind die generierten Rechtstexte rechtssicher?
              </h4>
              <p className="text-gray-300 pl-7">
                Ja, unsere KI ist speziell auf deutsche Rechtslage trainiert und arbeitet mit aktuellen Rechtsprechungen. Bei unserem Expert-Service werden alle Texte zusätzlich von qualifizierten Anwälten geprüft und freigegeben.
              </p>
            </div>

            {/* FAQ 3 */}
            <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
              <h4 className="text-xl font-bold mb-3 flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-green-400" />
                Was passiert bei Rechtsänderungen?
              </h4>
              <p className="text-gray-300 pl-7">
                Unser System überwacht kontinuierlich Rechtsänderungen und benachrichtigt Sie automatisch. Bei kritischen Änderungen führen wir sofortige Updates durch, damit Ihre Website immer aktuell und rechtssicher bleibt.
              </p>
            </div>

            {/* FAQ 4 */}
            <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
              <h4 className="text-xl font-bold mb-3 flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-green-400" />
                Funktioniert Complyo mit allen CMS-Systemen?
              </h4>
              <p className="text-gray-300 pl-7">
                Ja, Complyo arbeitet CMS-unabhängig. Wir unterstützen WordPress, Shopify, Typo3, Drupal, Joomla und individuelle Lösungen. Unsere KI generiert passenden Code für jedes System und führt Sie durch die Implementation.
              </p>
            </div>

            {/* FAQ 5 */}
            <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
              <h4 className="text-xl font-bold mb-3 flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-green-400" />
                Was ist die 14-Tage Geld-zurück-Garantie?
              </h4>
              <p className="text-gray-300 pl-7">
                Sie können innerhalb von 14 Tagen nach Kauf ohne Angabe von Gründen eine vollständige Rückerstattung erhalten. Wichtig: Die Garantie verfällt, sobald Sie die Fehlerkorrektur-Funktion nutzen, da Sie dann bereits von unserer Leistung profitiert haben.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      {/* Footer - Compliance Showcase */}
      <footer id="pricing" className="bg-gray-950 border-t border-gray-800 py-12">
        <div className="container mx-auto px-6">
          <div className="grid md:grid-cols-4 gap-8 mb-8">
            {/* Company Info */}
            <div>
              <div className="flex items-center gap-2 mb-4">
                <Shield className="w-8 h-8 text-blue-400" aria-hidden="true" />
                <span className="text-2xl font-bold">Complyo</span>
              </div>
              <p className="text-gray-400 text-sm mb-4">
                Automatisierte Compliance-Prüfung für DSGVO, Barrierefreiheit und Rechtstexte.
              </p>
              <div className="flex items-center gap-2 text-sm text-green-400">
                <CheckCircle className="w-4 h-4" aria-hidden="true" />
                <span>TÜV & Anwalt geprüft</span>
              </div>
            </div>

            {/* Produkt */}
            <div>
              <h4 className="font-bold text-white mb-4">Produkt</h4>
              <ul className="space-y-2 text-sm text-gray-400">
                <li><a href="#features" className="hover:text-white transition">Features</a></li>
                <li><a href="#pricing" className="hover:text-white transition">Preise</a></li>
                <li><a href="/demo" className="hover:text-white transition">Demo</a></li>
                <li><a href="/changelog" className="hover:text-white transition">Changelog</a></li>
              </ul>
            </div>

            {/* Rechtliches - DSGVO Showcase */}
            <div>
              <h4 className="font-bold text-white mb-4">Rechtliches</h4>
              <ul className="space-y-2 text-sm text-gray-400">
                <li>
                  <a href="/impressum" className="hover:text-white transition flex items-center gap-1">
                    <FileCheck className="w-3 h-3 text-green-400" aria-hidden="true" />
                    Impressum (§5 TMG)
                  </a>
                </li>
                <li>
                  <a href="/datenschutz" className="hover:text-white transition flex items-center gap-1">
                    <Shield className="w-3 h-3 text-blue-400" aria-hidden="true" />
                    Datenschutz (DSGVO)
                  </a>
                </li>
                <li>
                  <a href="/agb" className="hover:text-white transition">
                    AGB
                  </a>
                </li>
                <li>
                  <a href="/widerruf" className="hover:text-white transition">
                    Widerrufsbelehrung
                  </a>
                </li>
                <li>
                  <a href="/cookie-richtlinie" className="hover:text-white transition">
                    Cookie-Richtlinie
                  </a>
                </li>
              </ul>
            </div>

            {/* Kontakt */}
            <div>
              <h4 className="font-bold text-white mb-4">Kontakt</h4>
              <ul className="space-y-3 text-sm text-gray-400">
                <li className="flex items-start gap-2">
                  <Mail className="w-4 h-4 mt-0.5 text-blue-400" aria-hidden="true" />
                  <a href="mailto:support@complyo.tech" className="hover:text-white transition">
                    support@complyo.tech
                  </a>
                </li>
                <li className="flex items-start gap-2">
                  <Phone className="w-4 h-4 mt-0.5 text-blue-400" aria-hidden="true" />
                  <a href="tel:+4930123456789" className="hover:text-white transition">
                    +49 (0) 30 123 456 789
                  </a>
                </li>
                <li className="flex items-start gap-2">
                  <MapPin className="w-4 h-4 mt-0.5 text-blue-400" aria-hidden="true" />
                  <span>
                    Complyo GmbH<br />
                    Musterstraße 123<br />
                    10115 Berlin
                  </span>
                </li>
              </ul>
            </div>
          </div>

          {/* Compliance Badges - Live Demo */}
          <div className="border-t border-gray-800 pt-8">
            <div className="flex flex-wrap items-center justify-center gap-6 mb-6">
              <div className="bg-green-900 bg-opacity-30 border border-green-500 rounded-lg px-4 py-2 flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-green-400" aria-hidden="true" />
                <span className="text-xs text-green-300">DSGVO-konform</span>
              </div>
              <div className="bg-blue-900 bg-opacity-30 border border-blue-500 rounded-lg px-4 py-2 flex items-center gap-2">
                <Shield className="w-4 h-4 text-blue-400" aria-hidden="true" />
                <span className="text-xs text-blue-300">BFSG-compliant</span>
              </div>
              <div className="bg-purple-900 bg-opacity-30 border border-purple-500 rounded-lg px-4 py-2 flex items-center gap-2">
                <Lock className="w-4 h-4 text-purple-400" aria-hidden="true" />
                <span className="text-xs text-purple-300">SSL-verschlüsselt</span>
              </div>
              <div className="bg-yellow-900 bg-opacity-30 border border-yellow-500 rounded-lg px-4 py-2 flex items-center gap-2">
                <Star className="w-4 h-4 text-yellow-400" aria-hidden="true" />
                <span className="text-xs text-yellow-300">WCAG 2.1 AA</span>
              </div>
            </div>

            {/* Copyright & Legal Notice */}
            <div className="text-center text-xs text-gray-500">
              <p className="mb-2">
                © {new Date().getFullYear()} Complyo GmbH. Alle Rechte vorbehalten.
              </p>
              <p>
                USt-IdNr.: DE123456789 | HRB 12345 B | Amtsgericht Berlin-Charlottenburg
              </p>
              <p className="mt-4 text-gray-600">
                Diese Website ist ein Live-Showcase für Complyo's Compliance-Features:<br />
                ♿ Barrierefreiheit • 🍪 Cookie-Management • 📄 Rechtstexte • 🔒 DSGVO
              </p>
            </div>
          </div>
        </div>
      </footer>

      {/* Accessibility Widget - BFSG Showcase */}
      <AccessibilityWidget />

      {/* Cookie Banner - DSGVO Showcase */}
      <CookieBanner />

      <style jsx>{`
        @keyframes blob {
          0% { transform: translate(0px, 0px) scale(1); }
          33% { transform: translate(30px, -50px) scale(1.1); }
          66% { transform: translate(-20px, 20px) scale(0.9); }
          100% { transform: translate(0px, 0px) scale(1); }
        }
        .animate-blob {
          animation: blob 7s infinite;
        }
        .animation-delay-2000 {
          animation-delay: 2s;
        }
        .animation-delay-4000 {
          animation-delay: 4s;
        }
      `}</style>
    </div>
  );
};

export default ComplyoViralLanding;

