import React, { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import { 
  Check, 
  X, 
  Play, 
  ChevronDown, 
  Menu, 
  ExternalLink,
  Shield,
  FileText,
  Cookie,
  Eye,
  Zap,
  Users,
  Star,
  Mail,
  Phone,
  Globe
} from 'lucide-react';
import { Logo } from './Logo';

interface ComplyoLandingProps {
  variant: 'original' | 'high-conversion';
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
  // Legacy fields für Backward-Kompatibilität
  issues?: string[];
  riskAmount?: string;
}

interface FAQ {
  id: number;
  question: string;
  answer: string;
  isOpen: boolean;
}

type PlanType = 'ki' | 'expert';

interface FormData {
  email?: string;
  website?: string;
  company?: string;

  phone?: string;
  requirements?: string;
}

const ComplyoLandingPage: React.FC<ComplyoLandingProps> = ({ variant, sessionId }) => {
  // State Management
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [websiteUrl, setWebsiteUrl] = useState('');
  const [analysisResults, setAnalysisResults] = useState<AnalysisResult | null>(null);
  const [showResults, setShowResults] = useState(false);
  const [activeModal, setActiveModal] = useState<string | null>(null);
  const [selectedPlan, setSelectedPlan] = useState<PlanType | null>(null);
  
  // Lead generation form state
  const [showLeadForm, setShowLeadForm] = useState(false);
  const [isGeneratingReport, setIsGeneratingReport] = useState(false);
  const [leadFormData, setLeadFormData] = useState({
    email: '',
    name: '',
    company: ''
  });
  
  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'https://api.complyo.tech';
  const [faqs, setFaqs] = useState<FAQ[]>([
    {
      id: 1,
      question: "Bin ich wirklich in Gefahr, eine Abmahnung zu bekommen?",
      answer: "Ja, leider. Über 70% aller deutschen Websites haben rechtliche Mängel. Abmahnungen sind ein lukratives Geschäft für spezialisierte Anwälte geworden. Die häufigsten Gründe: Fehlende/veraltete Datenschutzerklärung, falsche Cookie-Banner, fehlendes Impressum. Eine Abmahnung kann jederzeit und ohne Vorwarnung kommen - und kostet Sie durchschnittlich 4.000€ - 20.000€.",
      isOpen: false
    },
    {
      id: 2,
      question: "Ich verstehe nichts von Technik - kann ich Complyo trotzdem nutzen?",
      answer: "Absolut! Genau dafür ist Complyo gemacht. Sie müssen NICHTS von Technik verstehen. Wir erklären alles in einfacher Sprache ohne Fachchinesisch. Sie bekommen fertige Texte zum Kopieren und klare Schritt-für-Schritt-Anleitungen. Und wenn Sie möchten, machen unsere Experten einfach alles für Sie - Sie lehnen sich zurück und sind geschützt.",
      isOpen: false
    },
    {
      id: 3,
      question: "Was genau macht Complyo für mich?",
      answer: "Complyo prüft Ihre Website auf alle wichtigen rechtlichen Anforderungen und erstellt automatisch alle Texte, die Sie brauchen: Impressum, Datenschutzerklärung, Cookie-Banner, AGB. Danach überwacht Complyo Ihre Website jeden Monat und warnt Sie, wenn sich Gesetze ändern oder neue Probleme auftauchen. Sie sind durchgehend geschützt - ohne dass Sie sich darum kümmern müssen.",
      isOpen: false
    },
    {
      id: 4,
      question: "Funktioniert das auch mit meinem Website-System? (WordPress, Wix, etc.)",
      answer: "Ja, Complyo funktioniert mit ALLEN Website-Systemen: WordPress, Wix, Jimdo, Shopify, Squarespace, TYPO3, Joomla und auch mit individuell programmierten Websites. Egal welches System Sie nutzen - Complyo gibt Ihnen die passenden Lösungen dafür. Und wenn Sie nicht wissen, welches System Sie haben: Kein Problem, das finden wir gemeinsam heraus.",
      isOpen: false
    },
    {
      id: 5,
      question: "Wie schnell bin ich geschützt?",
      answer: "Mit dem KI-Plan sind Sie innerhalb von 24 Stunden geschützt. Sie führen die kostenlose Analyse durch (30 Sekunden), melden sich an, und Complyo erstellt alle notwendigen Texte und Lösungen für Sie. Mit unserer Anleitung können Sie alles innerhalb weniger Stunden umsetzen. Beim Expert-Plan machen wir alles für Sie - meist innerhalb von 3-5 Werktagen.",
      isOpen: false
    },
    {
      id: 6,
      question: "Was passiert, wenn sich Gesetze ändern?",
      answer: "Das ist einer der größten Vorteile von Complyo: Wir beobachten alle relevanten Gesetzesänderungen für Sie. Wenn sich etwas ändert, bekommen Sie sofort eine E-Mail und sehen im Dashboard, was Sie anpassen müssen. Oft können wir Texte automatisch aktualisieren. Sie müssen sich nie Sorgen machen, etwas zu verpassen.",
      isOpen: false
    },
    {
      id: 7,
      question: "Kostet die erste Analyse wirklich nichts?",
      answer: "Ja, die Analyse ist 100% kostenlos und unverbindlich. Keine Kreditkarte nötig, keine versteckten Kosten. Sie geben einfach Ihre Website-Adresse ein und sehen innerhalb von 30 Sekunden, welche Probleme Ihre Website hat und wie viel Abmahnrisiko besteht. Erst wenn Sie sich für einen Plan entscheiden, zahlen Sie etwas. Die kostenlose Analyse können Sie beliebig oft wiederholen.",
      isOpen: false
    },
    {
      id: 8,
      question: "Kann ich wirklich jederzeit kündigen?",
      answer: "Ja, absolut. Es gibt keine Mindestlaufzeit und keine Kündigungsfrist. Sie können den KI-Plan jederzeit mit einem Klick kündigen. Wir glauben, dass Sie bei uns bleiben, weil Complyo gut ist - nicht weil Sie in einem Vertrag feststecken. Und: In den ersten 14 Tagen bekommen Sie Ihr Geld zurück, wenn Sie nicht zufrieden sind (solange Sie die Fehlerkorrektur noch nicht genutzt haben).",
      isOpen: false
    }
  ]);

  // Refs
  const analyzerRef = useRef<HTMLElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Initialize Page
  useEffect(() => {
    // Set page title for screen readers
    document.title = 'Complyo - Website Compliance & Abmahnschutz';
  }, []);

  // Utility Functions
  const scrollToAnalyzer = () => {
    analyzerRef.current?.scrollIntoView({ behavior: 'smooth' });
    setMobileMenuOpen(false);
  };

  const scrollToSection = (sectionId: string) => {
    const element = document.getElementById(sectionId);
    element?.scrollIntoView({ behavior: 'smooth' });
    setMobileMenuOpen(false);
  };

  const openModal = (modalId: string) => {
    setActiveModal(modalId);
    document.body.style.overflow = 'hidden';
  };

  const closeModal = () => {
    setActiveModal(null);
    document.body.style.overflow = '';
  };

  const toggleFAQ = (id: number) => {
    setFaqs(prev => prev.map(faq => 
      faq.id === id ? { ...faq, isOpen: !faq.isOpen } : faq
    ));
  };

  // Lead generation functions
  const generateReport = () => {
    if (!analysisResults) {
      alert('Bitte führen Sie zuerst eine Analyse durch');
      return;
    }
    setShowLeadForm(true);
  };

  const handleLeadFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!leadFormData.email.trim() || !leadFormData.name.trim()) {
      alert('Bitte füllen Sie alle Pflichtfelder aus');
      return;
    }

    setIsGeneratingReport(true);
    
    try {
      // Send lead data to backend
      const leadData = {
        name: leadFormData.name.trim(),
        email: leadFormData.email.trim(),
        company: leadFormData.company.trim() || null,
        url: websiteUrl,
        analysis_data: analysisResults,
        session_id: sessionId
      };
      
      const response = await fetch(`${API_BASE}/api/leads/collect`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(leadData)
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const result = await response.json();
      
      // Close form and show appropriate success message
      setShowLeadForm(false);
      
      if (result.verified) {
        alert(`✅ Report wird sofort an ${leadFormData.email} gesendet!`);
      } else {
        alert(`📧 Bestätigungs-E-Mail wurde an ${leadFormData.email} gesendet!\n\nBitte prüfen Sie Ihr Postfach und klicken Sie auf den Bestätigungslink, um den Report zu erhalten.`);
      }
      
      // Reset form
      setLeadFormData({ email: '', name: '', company: '' });
      
      console.log('Lead successfully submitted:', result);
      
    } catch (error) {
      console.error('Error submitting lead:', error);
      alert('Fehler beim Senden der Daten. Bitte versuchen Sie es erneut.');
    } finally {
      setIsGeneratingReport(false);
    }
  };

  const closeLeadForm = () => {
    setShowLeadForm(false);
    setLeadFormData({ email: '', name: '', company: '' });
  };

  // Analysis Functions (Legacy Mock - nicht mehr verwendet)
  // Wird durch echten API-Call ersetzt

  const analyzeWebsite = async () => {
    if (isAnalyzing || !websiteUrl.trim()) {
      if (!websiteUrl.trim()) {
        alert('Bitte geben Sie eine gültige URL ein.');
      }
      return;
    }

    // FIXED: Verbesserte URL-Normalisierung für Konsistenz
    let normalizedUrl = websiteUrl.trim().toLowerCase();
    if (!normalizedUrl.startsWith('http://') && !normalizedUrl.startsWith('https://')) {
      normalizedUrl = 'https://' + normalizedUrl;
    }

    try {
      const urlObj = new URL(normalizedUrl);
      // Normalisiere auf hostname + optional pathname (ohne trailing slash)
      // FIXED: Entferne www. Präfix für konsistente Hashes
      let hostname = urlObj.hostname;
      if (hostname.startsWith('www.')) {
        hostname = hostname.substring(4);
      }
      
      normalizedUrl = `${urlObj.protocol}//${hostname}`;
      if (urlObj.port && urlObj.port !== '80' && urlObj.port !== '443') {
        normalizedUrl += `:${urlObj.port}`;
      }
      if (urlObj.pathname && urlObj.pathname !== '/' && urlObj.pathname !== '') {
        normalizedUrl += urlObj.pathname.replace(/\/+$/, '');
      }
      console.log('✅ Normalisierte URL:', normalizedUrl);
    } catch (e) {
      alert('Bitte geben Sie eine gültige URL ein (z.B. example.com oder https://example.com)');
      return;
    }

    setIsAnalyzing(true);
    setShowResults(false);

    try {
      // Call REAL Preview-Endpoint
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
      
      // Transform API response to match AnalysisResult interface
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

      // Scroll to results
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

  // Form Handlers
  const handlePurchase = async (event: React.FormEvent<HTMLFormElement>, plan: PlanType) => {
    event.preventDefault();
    
    const formData = new FormData(event.currentTarget);
    const data: FormData = {};
    
    const entries = Array.from(formData.entries());
    for (const [key, value] of entries) {
      data[key as keyof FormData] = value as string;
    }

    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      console.log('Form submission:', { plan, data });
      
      closeModal();
      openModal('success-modal');
      
    } catch (error) {
      console.error('Submission error:', error);
      alert('Fehler beim Senden. Bitte versuchen Sie es erneut.');
    }
  };

  // Event Handlers
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Skip if the event is from an input, textarea, or contenteditable element
      const target = e.target as HTMLElement;
      if (target.matches('input, textarea, [contenteditable="true"]')) {
        return;
      }
      
      if (e.key === 'Escape') {
        closeModal();
      }
    };

    const handleClickOutside = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      if (target.classList.contains('modal-backdrop')) {
        closeModal();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    document.addEventListener('click', handleClickOutside);

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.removeEventListener('click', handleClickOutside);
    };
  }, []);

  // Components
  const Navigation = () => (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-gray-900/80 backdrop-blur-md border-b border-gray-700">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <Logo size="lg" />
          
          <div className="hidden md:flex items-center space-x-8">
            <button 
              onClick={() => scrollToSection('features')}
              className="text-gray-300 hover:text-white transition-colors"
            >
              Features
            </button>
            <button 
              onClick={() => scrollToSection('pricing')}
              className="text-gray-300 hover:text-white transition-colors"
            >
              Preise
            </button>
            <button 
              onClick={() => scrollToSection('demo')}
              className="text-gray-300 hover:text-white transition-colors"
            >
              Demo
            </button>
            <button 
              onClick={scrollToAnalyzer}
              className="bg-gradient-to-r from-blue-500 to-purple-600 px-4 py-2 rounded-lg font-medium hover:opacity-90 transition-opacity"
            >
              Kostenlos testen
            </button>
          </div>
          
          <button 
            className="md:hidden p-2"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            <Menu className="w-6 h-6" />
          </button>
        </div>
      </div>
      
      {mobileMenuOpen && (
        <div className="md:hidden bg-gray-800/95 backdrop-blur-md border-t border-gray-700">
          <div className="px-4 py-4 space-y-4">
            <button 
              onClick={() => scrollToSection('features')}
              className="block text-gray-300 hover:text-white"
            >
              Features
            </button>
            <button 
              onClick={() => scrollToSection('pricing')}
              className="block text-gray-300 hover:text-white"
            >
              Preise
            </button>
            <button 
              onClick={() => scrollToSection('demo')}
              className="block text-gray-300 hover:text-white"
            >
              Demo
            </button>
            <button 
              onClick={scrollToAnalyzer}
              className="w-full bg-gradient-to-r from-blue-500 to-purple-600 px-4 py-2 rounded-lg font-medium"
            >
              Kostenlos testen
            </button>
          </div>
        </div>
      )}
    </nav>
  );

  const HeroSection = () => (
    <section className="min-h-screen flex items-center justify-center relative overflow-hidden pt-16">
      {/* Background Elements */}
      <div className="absolute inset-0">
        <div className="absolute top-20 left-10 w-64 h-64 bg-blue-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-pulse"></div>
        <div className="absolute top-40 right-10 w-64 h-64 bg-purple-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-pulse" style={{animationDelay: '-3s'}}></div>
        <div className="absolute bottom-20 left-1/2 w-64 h-64 bg-indigo-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-pulse" style={{animationDelay: '-1.5s'}}></div>
      </div>
      
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative z-10">
        {/* Alarming Badge */}
        <div className="inline-block mb-6 px-6 py-3 bg-red-500/20 border-2 border-red-500 rounded-full animate-pulse">
          <span className="text-red-300 font-semibold text-sm md:text-base">
            ⚠️ Über 70% aller deutschen Websites sind abmahngefährdet
          </span>
        </div>
        
        <h1 className="text-4xl md:text-6xl lg:text-7xl font-bold mb-6 leading-tight">
          Schützen Sie sich vor{' '}
          <span className="bg-gradient-to-r from-red-500 to-orange-500 bg-clip-text text-transparent">
            teuren Abmahnungen
          </span>
          <br />
          <span className="text-3xl md:text-4xl lg:text-5xl text-gray-300">
            und machen Sie Ihre Website
          </span>
          <br />
          <span className="bg-gradient-to-r from-blue-500 to-purple-600 bg-clip-text text-transparent">
            rechtssicher
          </span>
        </h1>
        
        <p className="text-xl md:text-2xl text-gray-300 mb-8 max-w-3xl mx-auto leading-relaxed">
          Abmahnungen können Sie tausende Euro kosten - und kommen oft ohne Vorwarnung. 
          <br/>
          <strong className="text-white">Complyo schützt Ihre Website automatisch</strong> vor rechtlichen Problemen.
        </p>
        
        <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-12">
          <button 
            onClick={scrollToAnalyzer}
            className="bg-gradient-to-r from-blue-500 to-purple-600 px-8 py-4 rounded-lg text-lg font-semibold hover:scale-105 transition-transform shadow-2xl"
          >
            ✅ Jetzt kostenlos prüfen lassen
          </button>
          <button 
            onClick={() => openModal('demo-modal')}
            className="bg-white/10 backdrop-blur-md border border-white/20 px-8 py-4 rounded-lg text-lg font-semibold hover:bg-white/20 transition-colors"
          >
            📹 So funktioniert's
          </button>
        </div>
        
        {/* Real Risk Examples */}
        <div className="grid md:grid-cols-2 gap-6 max-w-5xl mx-auto mb-8">
          {/* Warning Box 1 */}
          <div className="bg-red-900/30 backdrop-blur-md border-2 border-red-500 p-6 rounded-2xl text-left">
            <div className="flex items-start mb-3">
              <div className="text-3xl mr-3">⚠️</div>
              <div>
                <h3 className="text-xl font-bold text-red-300 mb-2">Fehlende Datenschutzerklärung</h3>
                <p className="text-gray-300 mb-3">
                  "Mir ist eine Abmahnung über <strong className="text-white">8.500€</strong> ins Haus geflattert, 
                  nur weil meine Datenschutzerklärung nicht aktuell war."
                </p>
                <p className="text-sm text-gray-400 italic">- Michael S., Online-Shop Betreiber</p>
              </div>
            </div>
          </div>
          
          {/* Warning Box 2 */}
          <div className="bg-red-900/30 backdrop-blur-md border-2 border-red-500 p-6 rounded-2xl text-left">
            <div className="flex items-start mb-3">
              <div className="text-3xl mr-3">🍪</div>
              <div>
                <h3 className="text-xl font-bold text-red-300 mb-2">Cookie-Banner Fehler</h3>
                <p className="text-gray-300 mb-3">
                  "Wegen eines falschen Cookie-Banners musste ich <strong className="text-white">12.000€</strong> zahlen. 
                  Das hätte verhindert werden können."
                </p>
                <p className="text-sm text-gray-400 italic">- Sandra K., Agentur-Inhaberin</p>
              </div>
            </div>
          </div>
        </div>
        
        {/* Risk Calculator Teaser - Enhanced */}
        <div className="bg-gradient-to-br from-red-900/50 to-orange-900/50 backdrop-blur-md border-2 border-red-500 p-8 rounded-2xl max-w-2xl mx-auto shadow-2xl">
          <h3 className="text-2xl font-semibold mb-4 text-red-200">
            💰 Was kostet eine Abmahnung wirklich?
          </h3>
          <div className="text-5xl font-bold text-red-400 mb-4">4.000€ - 20.000€+</div>
          <p className="text-lg text-gray-300 mb-4">
            <strong>Pro Verstoß!</strong> Und oft kommen mehrere Verstöße zusammen...
          </p>
          <div className="bg-black/30 p-4 rounded-lg text-left">
            <p className="text-sm text-gray-300 mb-2">Typische Kosten:</p>
            <ul className="text-sm text-gray-300 space-y-1">
              <li>• Anwaltskosten der Gegenseite: <strong>2.000€ - 5.000€</strong></li>
              <li>• Eigene Anwaltskosten: <strong>1.500€ - 3.000€</strong></li>
              <li>• Vertragsstrafe: <strong>500€ - 10.000€</strong></li>
              <li>• Weitere Kosten: <strong>Zeit, Nerven, Reputation</strong></li>
            </ul>
          </div>
        </div>
      </div>
    </section>
  );

  const AnalyzerSection = () => (
    <section 
      id="analyzer" 
      ref={analyzerRef}
      className="py-20 bg-gray-800"
    >
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <div className="inline-block bg-green-500/20 border-2 border-green-500 px-6 py-3 rounded-full mb-6">
            <span className="text-green-300 font-semibold">
              ✅ 100% Kostenlos • Keine Anmeldung • Sofort Ergebnisse
            </span>
          </div>
          
          <h2 className="text-4xl md:text-5xl font-bold mb-6">
            🔍 Finden Sie heraus:{' '}
            <span className="bg-gradient-to-r from-blue-500 to-purple-600 bg-clip-text text-transparent">
              Wie gefährdet ist Ihre Website?
            </span>
          </h2>
          <p className="text-2xl text-gray-300 mb-4">
            In nur 30 Sekunden sehen Sie, ob Ihre Website sicher ist
          </p>
          <p className="text-lg text-red-300 font-semibold">
            ⚠️ Die meisten Websites haben 3-7 kritische Probleme, von denen die Betreiber nichts wissen
          </p>
        </div>
        
        <div className="bg-white/10 backdrop-blur-md border border-white/20 p-8 rounded-2xl">
          <div className="mb-6">
            <label htmlFor="website-url" className="block text-sm font-medium mb-2">
              Website-URL eingeben:
            </label>
            <div className="flex gap-4">
              <input
                ref={inputRef}
                type="text"
                id="website-url"
                value={websiteUrl}
                onChange={(e) => setWebsiteUrl(e.target.value)}
                onFocus={(e) => {
                  // Simple focus handling
                  e.stopPropagation();
                }}
                onClick={(e) => {
                  // Simple click handling
                  e.stopPropagation();
                }}
                onBlur={(e) => {
                  // Simple blur handling - no focus forcing
                  e.stopPropagation();
                }}
                onKeyDown={(e) => {
                  // Simple key handling
                  e.stopPropagation();
                }}
                placeholder="https://ihre-website.de"
                className="flex-1 px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-white placeholder-gray-400"
                autoComplete="url"
              />
              <button 
                onClick={analyzeWebsite}
                disabled={isAnalyzing}
                className="bg-gradient-to-r from-blue-500 to-purple-600 px-8 py-3 rounded-lg font-semibold hover:opacity-90 transition-opacity whitespace-nowrap disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isAnalyzing ? (
                  <div className="flex items-center space-x-2">
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    <span>Analysiert...</span>
                  </div>
                ) : (
                  'Analysieren'
                )}
              </button>
            </div>
          </div>
          
          {/* Loading State */}
          {isAnalyzing && (
            <div className="text-center py-8">
              <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
              <p className="text-gray-300">Website wird analysiert...</p>
            </div>
          )}
          
          {/* Analysis Results - Preview mit Paywall */}
          {showResults && analysisResults && (
            <div id="analysis-results" className="border-t border-gray-600 pt-6">
              <h3 className="text-2xl font-bold mb-6 text-center">📊 Ihre Compliance-Analyse</h3>
              
              {/* Score Display */}
              <div className="bg-gradient-to-r from-gray-900 to-gray-800 p-8 rounded-lg mb-6 text-center">
                <h4 className="text-lg text-gray-300 mb-4">Ihr Compliance-Score</h4>
                <div className={`text-6xl font-bold mb-4 ${
                  analysisResults.score >= 80 ? 'text-green-400' : 
                  analysisResults.score >= 60 ? 'text-yellow-400' : 'text-red-400'
                }`}>
                  {analysisResults.score}<span className="text-3xl text-gray-400">/100</span>
                </div>
                <div className="w-full max-w-md mx-auto bg-gray-700 rounded-full h-4 mb-2">
                  <div 
                    className={`h-4 rounded-full transition-all ${
                      analysisResults.score >= 80 ? 'bg-green-400' : 
                      analysisResults.score >= 60 ? 'bg-yellow-400' : 'bg-red-400'
                    }`}
                    style={{ width: `${analysisResults.score}%` }}
                  ></div>
                </div>
                <p className="text-sm text-gray-400">
                  {analysisResults.score >= 80 ? 'Gute Basis, aber Optimierungspotential vorhanden' : 
                   analysisResults.score >= 60 ? 'Dringende Handlung empfohlen' : 
                   'Kritische Compliance-Lücken entdeckt'}
                </p>
              </div>

              {/* Risk Categories Preview */}
              <div className="mb-6">
                <h4 className="text-xl font-semibold mb-4">🔍 Gefundene Risiko-Kategorien</h4>
                <div className="grid md:grid-cols-2 gap-4">
                  {analysisResults.risk_categories.map((category) => (
                    <div 
                      key={category.id}
                      className={`p-4 rounded-lg border-2 ${
                        category.detected 
                          ? 'bg-red-900 bg-opacity-30 border-red-500' 
                          : 'bg-green-900 bg-opacity-20 border-green-500'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <span className="text-2xl">{category.icon}</span>
                          <h5 className="font-semibold">{category.label}</h5>
                        </div>
                        {category.detected ? (
                          <span className="text-red-400 font-bold">⚠️</span>
                        ) : (
                          <span className="text-green-400 font-bold">✓</span>
                        )}
                      </div>
                      {category.detected && category.risk_range && (
                        <div className="mt-2 text-red-300 font-semibold text-sm">
                          Abmahnrisiko: {category.risk_range}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Total Risk */}
              <div className="p-6 bg-red-900 bg-opacity-50 rounded-lg border-2 border-red-500 mb-6">
                <h4 className="font-semibold text-red-300 mb-2 text-center text-lg">⚠️ Geschätztes Gesamt-Abmahnrisiko</h4>
                <div className="text-4xl font-bold text-red-400 text-center">{analysisResults.total_risk_range}</div>
                <p className="text-center text-sm text-gray-300 mt-2">
                  {analysisResults.critical_count} kritische Probleme gefunden
                </p>
                <p className="text-sm text-red-300 mt-2">Basierend auf gefundenen Compliance-Verstößen</p>
              </div>
              
              {/* Paywall - CTA für detaillierte Analyse */}
              <div className="bg-gradient-to-r from-blue-900 to-purple-900 p-8 rounded-xl border-2 border-blue-500 mb-6">
                <h4 className="text-2xl font-bold text-center mb-4">
                  🔒 Detaillierte Analyse & KI-Fix verfügbar
                </h4>
                <p className="text-center text-gray-300 mb-6">
                  Sehen Sie exakt <strong>WO</strong> die Probleme liegen, <strong>WARUM</strong> sie kritisch sind 
                  und erhalten Sie <strong>KI-generierte Lösungen</strong> in Sekunden.
                </p>
                
                <div className="grid md:grid-cols-2 gap-4 mb-6">
                  <div className="bg-black bg-opacity-30 p-4 rounded-lg">
                    <h5 className="font-semibold mb-2 flex items-center gap-2">
                      <span className="text-green-400">✓</span> Komplett-Paket - 49€ netto/Monat
                    </h5>
                    <ul className="text-sm text-gray-300 space-y-1">
                      <li>• Alle 4 Säulen inklusive</li>
                      <li>• Code-Snippets mit Anleitungen</li>
                      <li>• Unbegrenzte Exports</li>
                      <li>• Compliance-Dashboard</li>
                    </ul>
                  </div>
                  
                  <div className="bg-gradient-to-br from-yellow-900 to-yellow-800 bg-opacity-50 p-4 rounded-lg border border-yellow-500">
                    <h5 className="font-semibold mb-2 flex items-center gap-2">
                      <span className="text-yellow-400">⭐</span> Expertenservice - 2.990€ + 39€/Monat
                    </h5>
                    <ul className="text-sm text-gray-300 space-y-1">
                      <li>• Vollständige Umsetzung durch Experten</li>
                      <li>• KI-generierte vollständige Dokumente</li>
                      <li>• Unbegrenzte Exports</li>
                      <li>• Persönlicher Compliance-Berater</li>
                    </ul>
                  </div>
                </div>
                
                <div className="flex flex-col sm:flex-row gap-4">
                  <button 
                    onClick={() => {
                      setSelectedPlan('ki');
                      openModal('pricing-modal');
                    }}
                    className="flex-1 bg-gradient-to-r from-blue-500 to-purple-600 px-8 py-4 rounded-lg font-bold text-lg hover:scale-105 transition-transform shadow-lg"
                  >
                    🚀 Jetzt starten (KI Plan)
                  </button>
                  <button 
                    onClick={() => {
                      setSelectedPlan('expert');
                      openModal('pricing-modal');
                    }}
                    className="flex-1 bg-gradient-to-r from-yellow-500 to-yellow-600 px-8 py-4 rounded-lg font-bold text-lg hover:scale-105 transition-transform shadow-lg"
                  >
                    ⭐ Expert Plan wählen
                  </button>
                </div>
                
                <p className="text-center text-sm text-gray-400 mt-4">
                  ✓ 14 Tage Geld-zurück-Garantie<br />
                  <span className="text-xs text-yellow-300">Hinweis: Garantie verfällt bei Nutzung der Fehlerkorrektur</span>
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  );

  const FeaturesSection = () => (
    <section id="features" className="py-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold mb-6">
            🛡️ So schützt Complyo{' '}
            <span className="bg-gradient-to-r from-blue-500 to-purple-600 bg-clip-text text-transparent">
              Ihre Website
            </span>
          </h2>
          <p className="text-xl text-gray-300 max-w-3xl mx-auto">
            Wir kümmern uns um alles, was rechtlich wichtig ist - automatisch und verständlich
          </p>
        </div>
        
        <div className="grid md:grid-cols-2 gap-8 mb-12">
          {[
            {
              icon: <FileText className="w-12 h-12" />,
              title: "Alle wichtigen Rechtstexte",
              subtitle: "Keine Abmahnung wegen fehlender Texte",
              description: "Impressum, Datenschutzerklärung, AGB - wir erstellen alle Texte, die Ihre Website braucht. Automatisch aktualisiert, sobald sich Gesetze ändern.",
              features: [
                "Impressum (Pflicht für jede Website)",
                "Datenschutzerklärung (DSGVO-konform)",
                "AGB & Widerrufsrecht (für Online-Shops)",
                "Automatische Updates bei Gesetzesänderungen"
              ],
              savings: "Spart Ihnen: 500€ - 3.000€ Anwaltskosten"
            },
            {
              icon: <Cookie className="w-12 h-12" />,
              title: "Cookie-Banner richtig gemacht",
              subtitle: "Der Klassiker unter den Abmahnungen",
              description: "Viele Cookie-Banner sind nicht korrekt eingebunden - das kann teuer werden. Wir machen es richtig und prüfen Ihre Website regelmäßig.",
              features: [
                "Rechtssicherer Cookie-Banner (häufigste Fehlerquelle!)",
                "Nur mit Zustimmung werden Cookies gesetzt",
                "Alle Tracking-Tools werden erfasst",
                "Einfache Ablehnung für Besucher möglich"
              ],
              savings: "Verhindert: 5.000€ - 15.000€ typische Abmahnkosten"
            },
            {
              icon: <Shield className="w-12 h-12" />,
              title: "Datenschutz nach DSGVO",
              subtitle: "Die Basics müssen stimmen",
              description: "DSGVO klingt kompliziert? Ist es auch. Aber Complyo macht es einfach und übersetzt alles in verständliche Sprache.",
              features: [
                "Prüfung: Welche Daten sammelt Ihre Website?",
                "Automatische Dokumentation (rechtlich wichtig)",
                "Besucher können ihre Daten löschen lassen",
                "Alles wird protokolliert (wichtig bei Prüfungen)"
              ],
              savings: "Bußgelder vermeiden: bis zu 20 Mio. € oder 4% Jahresumsatz"
            },
            {
              icon: <Eye className="w-12 h-12" />,
              title: "Barrierefreiheit für alle",
              subtitle: "Ab 2025 Pflicht für viele Websites",
              description: "Menschen mit Einschränkungen müssen Ihre Website nutzen können. Das ist nicht nur fair, sondern ab 2025 oft gesetzlich vorgeschrieben.",
              features: [
                "Website für Screenreader optimiert (für Blinde)",
                "Bedienung ohne Maus möglich (Tastatur-Navigation)",
                "Kontraste und Schriftgrößen anpassbar",
                "Erfüllt gesetzliche Anforderungen (WCAG 2.1)"
              ],
              savings: "Neue Pflicht ab 2025: Vermeiden Sie Strafen von Anfang an"
            }
          ].map((pillar, index) => (
            <div key={index} className="bg-white/10 backdrop-blur-md border border-white/20 p-8 rounded-2xl hover:shadow-2xl hover:border-blue-500 transition-all">
              <div className="flex items-start mb-4">
                <div className="text-blue-400 mr-4">{pillar.icon}</div>
                <div className="flex-1">
                  <h3 className="text-2xl font-bold mb-2">{pillar.title}</h3>
                  <p className="text-yellow-400 text-sm font-semibold mb-3">{pillar.subtitle}</p>
                </div>
              </div>
              
              <p className="text-gray-300 mb-4 leading-relaxed">
                {pillar.description}
              </p>
              
              <ul className="text-gray-300 space-y-2 mb-4">
                {pillar.features.map((feature, featureIndex) => (
                  <li key={featureIndex} className="flex items-start">
                    <Check className="w-5 h-5 text-green-400 mr-2 mt-0.5 flex-shrink-0" />
                    <span>{feature}</span>
                  </li>
                ))}
              </ul>
              
              <div className="bg-green-900/30 border border-green-500 rounded-lg p-3 mt-4">
                <p className="text-green-300 text-sm font-semibold">
                  💰 {pillar.savings}
                </p>
              </div>
            </div>
          ))}
        </div>
        
        {/* Value Proposition */}
        <div className="bg-gradient-to-r from-blue-900/50 to-purple-900/50 border-2 border-blue-500 p-8 rounded-2xl text-center">
          <h3 className="text-3xl font-bold mb-4">
            🎯 Das Beste: Sie müssen <u>nichts</u> technisch verstehen
          </h3>
          <p className="text-xl text-gray-300 mb-6 max-w-3xl mx-auto">
            Complyo erklärt alles in einfacher Sprache und macht die Umsetzung kinderleicht. 
            Kopieren, einfügen, fertig - oder lassen Sie es gleich von unseren Experten machen.
          </p>
          <div className="grid md:grid-cols-3 gap-6 text-left">
            <div className="bg-white/10 p-6 rounded-xl">
              <div className="text-4xl mb-3">1️⃣</div>
              <h4 className="font-bold text-lg mb-2">Website prüfen lassen</h4>
              <p className="text-gray-300 text-sm">30 Sekunden, kostenlos - Sie sehen sofort alle Probleme</p>
            </div>
            <div className="bg-white/10 p-6 rounded-xl">
              <div className="text-4xl mb-3">2️⃣</div>
              <h4 className="font-bold text-lg mb-2">Lösungen erhalten</h4>
              <p className="text-gray-300 text-sm">Fertige Texte und Code - einfach kopieren und einfügen</p>
            </div>
            <div className="bg-white/10 p-6 rounded-xl">
              <div className="text-4xl mb-3">3️⃣</div>
              <h4 className="font-bold text-lg mb-2">Geschützt sein</h4>
              <p className="text-gray-300 text-sm">Complyo überwacht Ihre Website und warnt Sie bei Änderungen</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );

  const PricingSection = () => (
    <section id="pricing" className="py-20 bg-gray-800">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h2 className="text-4xl md:text-5xl font-bold mb-6">
            💰 Was kostet mich{' '}
            <span className="bg-gradient-to-r from-blue-500 to-purple-600 bg-clip-text text-transparent">
              Sicherheit
            </span>
            ?
          </h2>
          <p className="text-xl text-gray-300 mb-4">
            Weniger als eine einzige Abmahnung - aber Sie sparen sich den ganzen Ärger
          </p>
          <div className="inline-block bg-red-900/30 border-2 border-red-500 px-6 py-3 rounded-lg">
            <p className="text-red-300 font-semibold">
              ⚠️ Eine Abmahnung kostet Sie durchschnittlich <strong className="text-white">8.000€</strong> - und kann jederzeit kommen
            </p>
          </div>
        </div>
        
        <div className="grid md:grid-cols-3 gap-8 mb-12">
          {/* Free Tier */}
          <div className="bg-white/10 backdrop-blur-md border border-white/20 p-8 rounded-2xl">
            <div className="text-center mb-8">
              <div className="text-5xl mb-4">🔍</div>
              <h3 className="text-2xl font-bold mb-2">Erst mal schauen</h3>
              <div className="text-5xl font-bold mb-4 text-green-400">0€</div>
              <p className="text-gray-300">Kostenlose Analyse</p>
            </div>
            
            <div className="mb-6 text-center">
              <p className="text-gray-300 text-sm mb-4">
                Perfekt, wenn Sie sich erst mal einen Überblick verschaffen wollen:
              </p>
            </div>
            
            <ul className="space-y-3 mb-8">
              {[
                "Kompletter Check Ihrer Website",
                "Alle Probleme werden aufgelistet",
                "Abmahnrisiko in Euro berechnet",
                "Konkrete Handlungsempfehlungen"
              ].map((feature, index) => (
                <li key={index} className="flex items-start">
                  <Check className="w-5 h-5 text-green-400 mr-3 mt-0.5 flex-shrink-0" />
                  <span className="text-sm">{feature}</span>
                </li>
              ))}
            </ul>
            
            <button 
              onClick={scrollToAnalyzer}
              className="w-full bg-white/10 hover:bg-white/20 backdrop-blur-md border border-white/20 px-6 py-3 rounded-lg font-semibold transition-colors"
            >
              ✅ Jetzt kostenlos prüfen
            </button>
            
            <p className="text-xs text-gray-400 mt-4 text-center">
              Keine Anmeldung erforderlich
            </p>
          </div>
          
          {/* KI Plan */}
          <div className="relative">
            <div className="absolute -top-4 left-1/2 transform -translate-x-1/2 z-10">
              <span className="bg-gradient-to-r from-blue-500 to-purple-600 px-6 py-2 rounded-full text-sm font-semibold shadow-lg">
                ⭐ Meist gewählt
              </span>
            </div>
            <div className="bg-white/10 backdrop-blur-md border-2 border-blue-500 p-8 rounded-2xl shadow-2xl transform hover:scale-105 transition-transform">
              <div className="text-center mb-8">
                <div className="text-5xl mb-4">🤖</div>
                <h3 className="text-2xl font-bold mb-2">Komplett-Paket</h3>
                <div className="text-5xl font-bold mb-2">
                  49€<span className="text-2xl">/Monat</span>
                </div>
                <p className="text-gray-400 line-through text-sm">statt 8.000€ Abmahnung</p>
                <p className="text-green-400 font-semibold mt-2">Alle 4 Säulen inklusive</p>
              </div>
              
              <div className="mb-6 text-center bg-blue-900/30 p-4 rounded-lg">
                <p className="text-gray-300 text-sm">
                  <strong className="text-white">Für 1 Website</strong> - perfekt für kleine Unternehmen, Selbstständige und Shops
                </p>
              </div>
              
              <ul className="space-y-3 mb-8">
                {[
                  "Alle Rechtstexte automatisch erstellt",
                  "In 24 Stunden ist alles fertig",
                  "Jeden Monat automatische Überprüfung",
                  "Sie werden gewarnt, wenn was nicht stimmt",
                  "Einfache Schritt-für-Schritt Anleitung",
                  "Live-Dashboard - immer den Überblick"
                ].map((feature, index) => (
                  <li key={index} className="flex items-start">
                    <Check className="w-5 h-5 text-green-400 mr-3 mt-0.5 flex-shrink-0" />
                    <span className="text-sm">{feature}</span>
                  </li>
                ))}
              </ul>
              
              <button 
                onClick={() => {
                  setSelectedPlan('ki');
                  openModal('pricing-modal');
                }}
                className="w-full bg-gradient-to-r from-blue-500 to-purple-600 px-6 py-4 rounded-lg font-bold text-lg hover:scale-105 transition-transform shadow-lg"
              >
                🚀 Jetzt schützen für 49€/Monat
              </button>
              
              <p className="text-xs text-gray-400 mt-4 text-center">
                ✓ Jederzeit kündbar • 14 Tage Geld-zurück-Garantie
              </p>
            </div>
          </div>
          
          {/* Expert Plan */}
          <div className="bg-white/10 backdrop-blur-md border border-white/20 p-8 rounded-2xl">
            <div className="text-center mb-8">
              <div className="text-5xl mb-4">👨‍💼</div>
              <h3 className="text-2xl font-bold mb-2">Persönliche Betreuung</h3>
              <div className="text-3xl font-bold mb-1">
                2.990€ <span className="text-base">einmalig</span>
              </div>
              <div className="text-2xl font-bold mb-4">
                + 39€<span className="text-base">/Monat</span>
              </div>
              <p className="text-gray-300 text-sm">Für große Websites & Shops</p>
            </div>
            
            <div className="mb-6 text-center bg-yellow-900/30 p-4 rounded-lg border border-yellow-600">
              <p className="text-gray-300 text-sm">
                <strong className="text-white">Unbegrenzt viele Websites</strong> - für Agenturen, große Unternehmen und komplexe Projekte
              </p>
            </div>
            
            <ul className="space-y-3 mb-8">
              {[
                "Echter Anwalt kümmert sich persönlich",
                "Alles wird für Sie umgesetzt",
                "Unbegrenzt viele Websites",
                "Spezielle Anpassungen für Ihre Branche",
                "Direkte Hotline zu Ihrem Berater",
                "Persönliche Check-ups alle 3 Monate"
              ].map((feature, index) => (
                <li key={index} className="flex items-start">
                  <Check className="w-5 h-5 text-green-400 mr-3 mt-0.5 flex-shrink-0" />
                  <span className="text-sm">{feature}</span>
                </li>
              ))}
            </ul>
            
            <button 
              onClick={() => {
                setSelectedPlan('expert');
                openModal('pricing-modal');
              }}
              className="w-full bg-gradient-to-r from-yellow-600 to-orange-600 px-6 py-3 rounded-lg font-semibold hover:scale-105 transition-transform"
            >
              💼 Kostenlose Beratung anfragen
            </button>
            
            <p className="text-xs text-gray-400 mt-4 text-center">
              Wir rufen Sie zurück • 100% unverbindlich
            </p>
          </div>
        </div>
        
        {/* Comparison */}
        <div className="bg-gradient-to-r from-red-900/50 to-orange-900/50 border-2 border-red-500 p-8 rounded-2xl text-center">
          <h3 className="text-3xl font-bold mb-6">
            🧮 Rechnen Sie selbst: Was ist günstiger?
          </h3>
          
          <div className="grid md:grid-cols-2 gap-6 max-w-4xl mx-auto">
            <div className="bg-black/30 p-6 rounded-xl">
              <div className="text-red-400 text-5xl font-bold mb-3">❌</div>
              <h4 className="text-2xl font-bold mb-4 text-red-300">OHNE Complyo</h4>
              <ul className="text-left space-y-2 text-gray-300">
                <li className="flex justify-between">
                  <span>1 Abmahnung (Durchschnitt):</span>
                  <strong className="text-white">8.000€</strong>
                </li>
                <li className="flex justify-between">
                  <span>Anwalt für Rechtstexte:</span>
                  <strong className="text-white">2.000€</strong>
                </li>
                <li className="flex justify-between">
                  <span>Barrierefreiheit-Check:</span>
                  <strong className="text-white">1.500€</strong>
                </li>
                <li className="flex justify-between">
                  <span>Cookie-Banner Setup:</span>
                  <strong className="text-white">500€</strong>
                </li>
                <li className="border-t border-red-500 pt-2 mt-2 flex justify-between text-xl">
                  <span className="font-bold">Gesamt:</span>
                  <strong className="text-red-400">12.000€+</strong>
                </li>
              </ul>
              <p className="text-red-300 text-sm mt-4 italic">
                + Zeit, Stress und Unsicherheit
              </p>
            </div>
            
            <div className="bg-gradient-to-br from-green-900/50 to-blue-900/50 border-2 border-green-500 p-6 rounded-xl">
              <div className="text-green-400 text-5xl font-bold mb-3">✅</div>
              <h4 className="text-2xl font-bold mb-4 text-green-300">MIT Complyo</h4>
              <ul className="text-left space-y-2 text-gray-300">
                <li className="flex justify-between">
                  <span>Complyo (1 Jahr):</span>
                  <strong className="text-white">468€</strong>
                </li>
                <li className="flex justify-between">
                  <span>Abmahnungen:</span>
                  <strong className="text-white">0€</strong>
                </li>
                <li className="flex justify-between">
                  <span>Anwaltskosten:</span>
                  <strong className="text-white">0€</strong>
                </li>
                <li className="flex justify-between">
                  <span>Zusatzkosten:</span>
                  <strong className="text-white">0€</strong>
                </li>
                <li className="border-t border-green-500 pt-2 mt-2 flex justify-between text-xl">
                  <span className="font-bold">Gesamt:</span>
                  <strong className="text-green-400">468€</strong>
                </li>
              </ul>
              <p className="text-green-300 text-sm mt-4 font-semibold">
                ✓ Volle Sicherheit + Seelenruhe
              </p>
            </div>
          </div>
          
          <div className="mt-8 bg-yellow-500/20 border border-yellow-500 p-6 rounded-lg">
            <p className="text-2xl font-bold text-yellow-300 mb-2">
              💡 Sie sparen über <span className="text-white">11.500€</span> im ersten Jahr!
            </p>
            <p className="text-gray-300">
              Und haben dabei null Stress. Complyo übernimmt alles für Sie.
            </p>
          </div>
        </div>
      </div>
    </section>
  );

  const SocialProofSection = () => (
    <section className="py-20">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold mb-6">
            ❤️ Das sagen unsere{' '}
            <span className="bg-gradient-to-r from-blue-500 to-purple-600 bg-clip-text text-transparent">
              zufriedenen Kunden
            </span>
          </h2>
          <p className="text-xl text-gray-300">
            Echte Menschen, echte Geschichten - alle haben sich vor Abmahnungen geschützt
          </p>
        </div>
        
        <div className="grid md:grid-cols-3 gap-8 mb-16">
          <div className="text-center bg-white/10 backdrop-blur-md border border-white/20 p-6 rounded-2xl">
            <div className="text-5xl font-bold text-blue-400 mb-2">500+</div>
            <p className="text-gray-300 font-semibold">Geschützte Websites</p>
            <p className="text-gray-400 text-sm mt-2">Von kleinen Blogs bis zu großen Online-Shops</p>
          </div>
          <div className="text-center bg-white/10 backdrop-blur-md border border-white/20 p-6 rounded-2xl">
            <div className="text-5xl font-bold text-green-400 mb-2">0</div>
            <p className="text-gray-300 font-semibold">Abmahnungen bei Kunden</p>
            <p className="text-gray-400 text-sm mt-2">Seit Start - dank kontinuierlicher Überwachung</p>
          </div>
          <div className="text-center bg-white/10 backdrop-blur-md border border-white/20 p-6 rounded-2xl">
            <div className="text-5xl font-bold text-purple-400 mb-2">4,9</div>
            <p className="text-gray-300 font-semibold">⭐ Durchschnittsbewertung</p>
            <p className="text-gray-400 text-sm mt-2">Aus über 200 Kundenbewertungen</p>
          </div>
        </div>
        
        {/* Testimonials - More Personal */}
        <div className="grid md:grid-cols-2 gap-8 mb-8">
          <div className="bg-gradient-to-br from-blue-900/30 to-purple-900/30 backdrop-blur-md border-2 border-blue-500 p-8 rounded-2xl">
            <div className="flex items-center mb-6">
              <div className="w-16 h-16 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center mr-4 text-2xl font-bold">
                MS
              </div>
              <div>
                <h4 className="font-bold text-lg">Marcus Schmidt</h4>
                <p className="text-gray-400 text-sm">Betreiber eines Fahrrad-Online-Shops</p>
                <div className="flex text-yellow-400 mt-1">
                  {[...Array(5)].map((_, i) => (
                    <Star key={i} className="w-4 h-4 fill-current" />
                  ))}
                </div>
              </div>
            </div>
            <div className="bg-red-900/30 border-l-4 border-red-500 p-4 mb-4 rounded">
              <p className="text-red-300 text-sm font-semibold mb-1">Das Problem:</p>
              <p className="text-gray-300 italic text-sm">
                "Ich habe eine Abmahnung über 8.500€ bekommen - wegen eines falschen Cookie-Banners. 
                Ich wusste nicht mal, dass meins falsch war!"
              </p>
            </div>
            <div className="bg-green-900/30 border-l-4 border-green-500 p-4 rounded">
              <p className="text-green-300 text-sm font-semibold mb-1">Mit Complyo:</p>
              <p className="text-gray-300 text-sm">
                "Complyo hat innerhalb von 24 Stunden alles für mich korrigiert. Jetzt schläft 
                ich ruhig, weil ich weiß, dass ich überwacht werde. Das hätte mir 8.500€ gespart!"
              </p>
            </div>
          </div>
          
          <div className="bg-gradient-to-br from-green-900/30 to-blue-900/30 backdrop-blur-md border-2 border-green-500 p-8 rounded-2xl">
            <div className="flex items-center mb-6">
              <div className="w-16 h-16 bg-gradient-to-r from-green-500 to-blue-500 rounded-full flex items-center justify-center mr-4 text-2xl font-bold">
                SK
              </div>
              <div>
                <h4 className="font-bold text-lg">Sandra Kowalski</h4>
                <p className="text-gray-400 text-sm">Inhaberin eines Friseursalons mit Website</p>
                <div className="flex text-yellow-400 mt-1">
                  {[...Array(5)].map((_, i) => (
                    <Star key={i} className="w-4 h-4 fill-current" />
                  ))}
                </div>
              </div>
            </div>
            <div className="bg-red-900/30 border-l-4 border-red-500 p-4 mb-4 rounded">
              <p className="text-red-300 text-sm font-semibold mb-1">Das Problem:</p>
              <p className="text-gray-300 italic text-sm">
                "Ich verstehe GAR NICHTS von Technik. Meine Website hat ein Bekannter gemacht, 
                aber der ist nicht mehr erreichbar. Ich hatte totale Panik wegen DSGVO."
              </p>
            </div>
            <div className="bg-green-900/30 border-l-4 border-green-500 p-4 rounded">
              <p className="text-green-300 text-sm font-semibold mb-1">Mit Complyo:</p>
              <p className="text-gray-300 text-sm">
                "Complyo hat mir ALLES erklärt - ohne Fachchinesisch. Ich habe die fertigen Texte 
                einfach kopiert, wo sie hingesagt haben. Hat 20 Minuten gedauert. Jetzt bin ich sicher!"
              </p>
            </div>
          </div>
        </div>
        
        <div className="grid md:grid-cols-2 gap-8">
          <div className="bg-white/10 backdrop-blur-md border border-white/20 p-6 rounded-2xl">
            <div className="flex items-center mb-4">
              <div className="w-12 h-12 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full flex items-center justify-center mr-4">
                <span className="text-white font-bold text-lg">TM</span>
              </div>
              <div>
                <h4 className="font-semibold">Thomas Müller</h4>
                <p className="text-gray-400 text-sm">Zahnarzt-Praxis mit Online-Terminbuchung</p>
              </div>
            </div>
            <p className="text-gray-300 mb-4 italic">
              "Als Zahnarzt habe ich keine Zeit, mich um Website-Rechtskram zu kümmern. 
              Complyo macht das einfach automatisch für mich. 49€ im Monat sind ein Witz im 
              Vergleich zu dem, was eine Abmahnung kosten würde. Top Service!"
            </p>
            <div className="flex text-yellow-400">
              {[...Array(5)].map((_, i) => (
                <Star key={i} className="w-5 h-5 fill-current" />
              ))}
            </div>
          </div>
          
          <div className="bg-white/10 backdrop-blur-md border border-white/20 p-6 rounded-2xl">
            <div className="flex items-center mb-4">
              <div className="w-12 h-12 bg-gradient-to-r from-orange-500 to-red-500 rounded-full flex items-center justify-center mr-4">
                <span className="text-white font-bold text-lg">LB</span>
              </div>
              <div>
                <h4 className="font-semibold">Lisa Bauer</h4>
                <p className="text-gray-400 text-sm">Yoga-Lehrerin & Workshop-Anbieterin</p>
              </div>
            </div>
            <p className="text-gray-300 mb-4 italic">
              "Ich hatte ständig Angst vor Abmahnungen, aber die Angebote von Anwälten waren 
              viel zu teuer für mich als Einzelunternehmerin. Complyo ist perfekt - bezahlbar 
              und ich verstehe endlich, was auf meiner Website sein muss. Danke!"
            </p>
            <div className="flex text-yellow-400">
              {[...Array(5)].map((_, i) => (
                <Star key={i} className="w-5 h-5 fill-current" />
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );

  const FAQSection = () => (
    <section className="py-20">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold mb-6">
            ❓ Häufige{' '}
            <span className="bg-gradient-to-r from-blue-500 to-purple-600 bg-clip-text text-transparent">
              Fragen
            </span>
          </h2>
        </div>
        
        <div className="space-y-6">
          {faqs.map((faq) => (
            <div key={faq.id} className="bg-white/10 backdrop-blur-md border border-white/20 rounded-2xl overflow-hidden">
              <button 
                onClick={() => toggleFAQ(faq.id)}
                className="w-full p-6 text-left hover:bg-white/10 transition-colors"
              >
                <div className="flex justify-between items-center">
                  <h3 className="font-semibold text-lg">{faq.question}</h3>
                  <ChevronDown 
                    className={`w-5 h-5 transform transition-transform ${
                      faq.isOpen ? 'rotate-180' : ''
                    }`}
                  />
                </div>
              </button>
              {faq.isOpen && (
                <div className="px-6 pb-6">
                  <p className="text-gray-300">{faq.answer}</p>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );

  const CTASection = () => (
    <section className="py-20 bg-gray-800 relative overflow-hidden">
      {/* Urgent Background */}
      <div className="absolute inset-0">
        <div className="absolute top-0 left-0 w-full h-2 bg-gradient-to-r from-red-500 via-orange-500 to-red-500 animate-pulse"></div>
      </div>
      
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        {/* Urgency Badge */}
        <div className="text-center mb-8">
          <div className="inline-block bg-red-500/20 border-2 border-red-500 px-8 py-4 rounded-full animate-pulse mb-6">
            <p className="text-red-300 font-bold text-lg">
              ⏰ Jede Minute ohne Schutz ist ein Risiko
            </p>
          </div>
          
          <h2 className="text-4xl md:text-6xl font-bold mb-6 leading-tight">
            Warten Sie nicht auf die{' '}
            <span className="bg-gradient-to-r from-red-500 to-orange-500 bg-clip-text text-transparent">
              erste Abmahnung
            </span>
          </h2>
          
          <p className="text-2xl text-gray-300 mb-4 max-w-3xl mx-auto font-semibold">
            Schützen Sie sich JETZT - in nur 30 Sekunden wissen Sie, wo Ihre Website unsicher ist
          </p>
          
          <p className="text-lg text-gray-400 mb-8 max-w-2xl mx-auto">
            Über 200 Website-Betreiber haben diese Woche ihre Seite bereits geprüft. 
            Die meisten hatten kritische Sicherheitslücken - und wussten nichts davon.
          </p>
        </div>
        
        {/* Warning Stats */}
        <div className="grid md:grid-cols-3 gap-4 mb-10 max-w-4xl mx-auto">
          <div className="bg-red-900/30 border-2 border-red-500 p-4 rounded-xl text-center">
            <div className="text-3xl font-bold text-red-400 mb-1">73%</div>
            <p className="text-gray-300 text-sm">der deutschen Websites haben rechtliche Mängel</p>
          </div>
          <div className="bg-red-900/30 border-2 border-red-500 p-4 rounded-xl text-center">
            <div className="text-3xl font-bold text-red-400 mb-1">8.000€</div>
            <p className="text-gray-300 text-sm">Durchschnittliche Kosten einer Abmahnung</p>
          </div>
          <div className="bg-red-900/30 border-2 border-red-500 p-4 rounded-xl text-center">
            <div className="text-3xl font-bold text-red-400 mb-1">Jederzeit</div>
            <p className="text-gray-300 text-sm">Eine Abmahnung kann ohne Vorwarnung kommen</p>
          </div>
        </div>
        
        <div className="text-center">
          <div className="flex flex-col sm:flex-row gap-6 justify-center mb-8">
            <button 
              onClick={scrollToAnalyzer}
              className="bg-gradient-to-r from-blue-500 to-purple-600 px-10 py-5 rounded-xl text-xl font-bold hover:scale-110 transition-transform shadow-2xl border-4 border-blue-400"
            >
              ✅ JETZT kostenlos prüfen (30 Sek.)
            </button>
            <button 
              onClick={() => {
                setSelectedPlan('ki');
                openModal('pricing-modal');
              }}
              className="bg-gradient-to-r from-green-600 to-emerald-600 px-10 py-5 rounded-xl text-xl font-bold hover:scale-110 transition-transform shadow-2xl border-4 border-green-400"
            >
              🛡️ Sofort schützen (49€/Monat)
            </button>
          </div>
          
          <div className="flex items-center justify-center gap-8 text-sm text-gray-400 mb-8">
            <div className="flex items-center gap-2">
              <Check className="w-5 h-5 text-green-400" />
              <span>100% kostenlose Analyse</span>
            </div>
            <div className="flex items-center gap-2">
              <Check className="w-5 h-5 text-green-400" />
              <span>Keine Kreditkarte nötig</span>
            </div>
            <div className="flex items-center gap-2">
              <Check className="w-5 h-5 text-green-400" />
              <span>Sofort Ergebnisse</span>
            </div>
          </div>
        </div>
        
        {/* Final Warning */}
        <div className="bg-gradient-to-r from-red-900/50 to-orange-900/50 border-2 border-red-500 p-8 rounded-2xl text-center max-w-3xl mx-auto">
          <h3 className="text-2xl font-bold mb-4 text-red-200">
            ⚠️ Denken Sie daran:
          </h3>
          <ul className="text-left space-y-3 text-gray-300 max-w-xl mx-auto">
            <li className="flex items-start">
              <span className="text-red-400 font-bold mr-3">•</span>
              <span>Abmahnungen kommen <strong className="text-white">ohne Vorwarnung</strong></span>
            </li>
            <li className="flex items-start">
              <span className="text-red-400 font-bold mr-3">•</span>
              <span>Sie müssen <strong className="text-white">sofort zahlen</strong> (meist innerhalb von Tagen)</span>
            </li>
            <li className="flex items-start">
              <span className="text-red-400 font-bold mr-3">•</span>
              <span>"Ich wusste es nicht" ist <strong className="text-white">keine Ausrede</strong> vor Gericht</span>
            </li>
            <li className="flex items-start">
              <span className="text-red-400 font-bold mr-3">•</span>
              <span>Jeder Tag ohne Schutz erhöht Ihr Risiko</span>
            </li>
          </ul>
          <div className="mt-6 pt-6 border-t border-red-500">
            <p className="text-xl font-bold text-white mb-2">
              Die Frage ist nicht OB, sondern WANN
            </p>
            <p className="text-gray-300">
              Schützen Sie sich jetzt - bevor es zu spät ist
            </p>
          </div>
        </div>
      </div>
    </section>
  );

  const Footer = () => (
    <footer className="py-12 border-t border-gray-700 relative z-10">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid md:grid-cols-4 gap-8">
          <div className="md:col-span-2">
            <Logo size="lg" className="mb-4" />
            <p className="text-gray-300 mb-4 max-w-md">
              Die erste All-in-One Compliance-Plattform für deutsche Websites. 
              Von abmahngefährdet zu rechtssicher in 24 Stunden.
            </p>
            <div className="flex space-x-4">
              <a href="#" className="text-gray-400 hover:text-white transition-colors">
                <Globe className="w-6 h-6" />
              </a>
              <a href="#" className="text-gray-400 hover:text-white transition-colors">
                <Mail className="w-6 h-6" />
              </a>
              <a href="#" className="text-gray-400 hover:text-white transition-colors">
                <Phone className="w-6 h-6" />
              </a>
            </div>
          </div>
          
          <div>
            <h3 className="font-semibold mb-4">Produkt</h3>
            <ul className="space-y-2 text-gray-300">
              <li>
                <button 
                  onClick={() => scrollToSection('features')}
                  className="hover:text-white transition-colors"
                >
                  Features
                </button>
              </li>
              <li>
                <button 
                  onClick={() => scrollToSection('pricing')}
                  className="hover:text-white transition-colors"
                >
                  Preise
                </button>
              </li>
              <li><a href="#" className="hover:text-white transition-colors">API</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Integrationen</a></li>
            </ul>
          </div>
          
          <div>
            <h3 className="font-semibold mb-4">Unternehmen</h3>
            <ul className="space-y-2 text-gray-300">
              <li><a href="#" className="hover:text-white transition-colors">Über uns</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Blog</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Karriere</a></li>
              <li><a href="#" className="hover:text-white transition-colors">Kontakt</a></li>
            </ul>
          </div>
        </div>
        
        <div className="border-t border-gray-700 mt-8 pt-8 flex flex-col md:flex-row justify-between items-center">
          <p className="text-gray-400 text-sm">
            © 2025 Complyo. Alle Rechte vorbehalten.
          </p>
          <div className="flex space-x-6 mt-4 md:mt-0">
            <Link href="/impressum" className="text-gray-400 hover:text-white text-sm transition-colors">
              Impressum
            </Link>
            <Link href="/datenschutz" className="text-gray-400 hover:text-white text-sm transition-colors">
              Datenschutz
            </Link>
            <Link href="/agb" className="text-gray-400 hover:text-white text-sm transition-colors">
              AGB
            </Link>
          </div>
        </div>
      </div>
    </footer>
  );

  // Modal Components
  const DemoModal = () => (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4 modal-backdrop">
      <div className="bg-white/10 backdrop-blur-md border border-white/20 max-w-2xl w-full rounded-2xl p-8 relative">
        <button 
          onClick={closeModal}
          className="absolute top-4 right-4 text-gray-400 hover:text-white"
        >
          <X className="w-6 h-6" />
        </button>
        
        <h3 className="text-2xl font-bold mb-6">🎥 Complyo Live-Demo</h3>
        
        <div className="bg-gray-900 rounded-lg p-6 mb-6">
          <div className="flex items-center justify-center h-40">
            <div className="text-center">
              <div className="w-16 h-16 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-4">
                <Play className="w-8 h-8 text-white" />
              </div>
              <p className="text-gray-300">Demo-Video wird geladen...</p>
            </div>
          </div>
        </div>
        
        <p className="text-gray-300 mb-6">
          Sehen Sie, wie Complyo in nur wenigen Minuten eine komplette Website-Analyse durchführt 
          und automatisch rechtssichere Lösungen generiert.
        </p>
        
        <div className="flex gap-4">
          <button 
            onClick={() => {
              scrollToAnalyzer();
              closeModal();
            }}
            className="bg-gradient-to-r from-blue-500 to-purple-600 px-6 py-3 rounded-lg font-semibold flex-1"
          >
            Eigene Website testen
          </button>
          <button 
            onClick={() => {
              setSelectedPlan('ki');
              setActiveModal('pricing-modal');
            }}
            className="bg-white/10 hover:bg-white/20 backdrop-blur-md border border-white/20 px-6 py-3 rounded-lg font-semibold"
          >
            Jetzt kaufen
          </button>
        </div>
      </div>
    </div>
  );

  const PricingModal = () => (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4 modal-backdrop">
      <div className="bg-white/10 backdrop-blur-md border border-white/20 max-w-md w-full rounded-2xl p-8 relative">
        <button 
          onClick={closeModal}
          className="absolute top-4 right-4 text-gray-400 hover:text-white"
        >
          <X className="w-6 h-6" />
        </button>
        
        {selectedPlan === 'ki' ? (
          <>
            <h3 className="text-2xl font-bold mb-6">🤖 Komplett-Paket</h3>
            <div className="text-center mb-6">
              <div className="text-4xl font-bold mb-2">49€<span className="text-lg">/Monat</span></div>
              <p className="text-gray-300">Alle 4 Säulen - Der intelligente Weg zur Compliance</p>
            </div>
            
            <div className="space-y-4 mb-6">
              {[
                "KI-gestützte Website-Überarbeitung",
                "24h-Umsetzungsgarantie",
                "Monatliche Re-Scans",
                "Live-Dashboard mit Analytics"
              ].map((feature, index) => (
                <div key={index} className="flex items-center">
                  <Check className="w-5 h-5 text-green-400 mr-3" />
                  {feature}
                </div>
              ))}
            </div>
            
            <form onSubmit={(e) => handlePurchase(e, 'ki')} className="space-y-4">
              <input 
                type="email" 
                name="email"
                placeholder="Ihre E-Mail-Adresse" 
                required 
                aria-label="E-Mail-Adresse für KI-Lösung"
                className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-white placeholder-gray-400"
              />
              <input 
                type="url" 
                name="website"
                placeholder="Ihre Website-URL" 
                required
                aria-label="Website-URL für KI-Lösung"
                className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-white placeholder-gray-400"
              />
              <button 
                type="submit" 
                className="w-full bg-gradient-to-r from-blue-500 to-purple-600 px-6 py-3 rounded-lg font-semibold hover:opacity-90 transition-opacity"
              >
                Jetzt für 49€/Monat starten
              </button>
            </form>
            
            <p className="text-xs text-gray-400 mt-4 text-center">
              🔒 SSL-verschlüsselt • Jederzeit kündbar • 14 Tage Geld-zurück-Garantie
            </p>
          </>
        ) : (
          <>
            <h3 className="text-2xl font-bold mb-6">👨‍💼 Expertenservice</h3>
            <div className="text-center mb-6">
              <div className="text-3xl font-bold mb-2">2.990€ <span className="text-lg">Setup</span></div>
              <div className="text-xl font-bold mb-2">+ 39€<span className="text-lg">/Monat</span></div>
              <p className="text-gray-300">Die Profi-Lösung für komplexe Fälle</p>
            </div>
            
            <div className="space-y-4 mb-6">
              {[
                "Persönliche Anwalts-Betreuung",
                "Branchenspezifische Compliance",
                "Custom-Integration in IT-Landschaft",
                "Direkte Experten-Hotline"
              ].map((feature, index) => (
                <div key={index} className="flex items-center">
                  <Check className="w-5 h-5 text-green-400 mr-3" />
                  {feature}
                </div>
              ))}
            </div>
            
            <form onSubmit={(e) => handlePurchase(e, 'expert')} className="space-y-4">
              <input 
                type="text" 
                name="company"
                placeholder="Firmenname" 
                required
                aria-label="Firmenname"
                className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-white placeholder-gray-400"
              />
              <input 
                type="email" 
                name="email"
                placeholder="Ihre E-Mail-Adresse" 
                required 
                aria-label="E-Mail-Adresse für Expertenservice"
                className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-white placeholder-gray-400"
              />
              <input 
                type="tel" 
                name="phone"
                placeholder="Telefonnummer" 
                required
                aria-label="Telefonnummer"
                className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-white placeholder-gray-400"
              />
              <textarea 
                name="requirements"
                placeholder="Beschreiben Sie Ihre Anforderungen..." 
                required
                rows={4}
                aria-label="Anforderungsbeschreibung"
                className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-white placeholder-gray-400 resize-none"
              />
              <button 
                type="submit" 
                className="w-full bg-gradient-to-r from-blue-500 to-purple-600 px-6 py-3 rounded-lg font-semibold hover:opacity-90 transition-opacity"
              >
                Kostenlose Beratung anfragen
              </button>
            </form>
            
            <p className="text-xs text-gray-400 mt-4 text-center">
              📞 Rückruf innerhalb von 24h • Kostenlose Erstberatung • Unverbindlich
            </p>
          </>
        )}
      </div>
    </div>
  );

  const SuccessModal = () => (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4 modal-backdrop">
      <div className="bg-white/10 backdrop-blur-md border border-white/20 max-w-md w-full rounded-2xl p-8 relative text-center">
        <button 
          onClick={closeModal}
          className="absolute top-4 right-4 text-gray-400 hover:text-white"
        >
          <X className="w-6 h-6" />
        </button>
        
        <div className="w-16 h-16 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-6">
          <Check className="w-8 h-8 text-white" />
        </div>
        
        <h3 className="text-2xl font-bold mb-4">🎉 Erfolgreich!</h3>
        <p className="text-gray-300 mb-6">
          Ihre Anfrage wurde erfolgreich übermittelt. 
          Wir melden uns innerhalb von 24 Stunden bei Ihnen.
        </p>
        
        <button 
          onClick={closeModal}
          className="bg-gradient-to-r from-blue-500 to-purple-600 px-6 py-3 rounded-lg font-semibold"
        >
          Verstanden
        </button>
      </div>
    </div>
  );

  // Main Return
  return (
    <div className="bg-gray-900 text-white overflow-x-hidden">
      {/* Header mit Navigation und Hero */}
      <header>
        <Navigation />
        <HeroSection />
      </header>
      
      {/* Hauptinhalt */}
      <main role="main">
        <AnalyzerSection />
        <FeaturesSection />
        <SocialProofSection />
        <PricingSection />
        <FAQSection />
        <CTASection />
      </main>
      
      {/* Footer */}
      <footer role="contentinfo">
        <Footer />
      </footer>
      
      {/* Modals */}
      {activeModal === 'demo-modal' && <DemoModal />}
      {activeModal === 'pricing-modal' && <PricingModal />}
      {activeModal === 'success-modal' && <SuccessModal />}
      
      {/* Lead Generation Modal */}
      {showLeadForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white/10 backdrop-blur-md border border-white/20 rounded-2xl p-8 max-w-md w-full">
            <div className="text-center mb-6">
              <h3 className="text-2xl font-bold mb-2">Compliance-Report erhalten</h3>
              <p className="text-gray-300">
                Geben Sie Ihre Daten ein, um den detaillierten Report zu erhalten.
              </p>
            </div>
            
            <form onSubmit={handleLeadFormSubmit} className="space-y-4">
              <div>
                <label htmlFor="lead-name" className="block text-sm font-medium mb-2">
                  Name *
                </label>
                <input
                  id="lead-name"
                  type="text"
                  required
                  value={leadFormData.name}
                  onChange={(e) => setLeadFormData(prev => ({ ...prev, name: e.target.value }))}
                  placeholder="Ihr vollständiger Name"
                  className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-white placeholder-gray-400"
                />
              </div>
              
              <div>
                <label htmlFor="lead-email" className="block text-sm font-medium mb-2">
                  E-Mail Adresse *
                </label>
                <input
                  id="lead-email"
                  type="email"
                  required
                  value={leadFormData.email}
                  onChange={(e) => setLeadFormData(prev => ({ ...prev, email: e.target.value }))}
                  placeholder="ihre@email.de"
                  className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-white placeholder-gray-400"
                />
              </div>
              
              <div>
                <label htmlFor="lead-company" className="block text-sm font-medium mb-2">
                  Unternehmen (optional)
                </label>
                <input
                  id="lead-company"
                  type="text"
                  value={leadFormData.company}
                  onChange={(e) => setLeadFormData(prev => ({ ...prev, company: e.target.value }))}
                  placeholder="Ihr Unternehmen"
                  className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-white placeholder-gray-400"
                />
              </div>
              
              <div className="text-xs text-gray-400 bg-gray-700 bg-opacity-50 p-4 rounded-lg">
                <h4 className="font-semibold text-gray-300 mb-2">🔒 DSGVO-konforme Datenverarbeitung</h4>
                <p className="mb-2">
                  Mit dem Absenden willigen Sie ein, dass wir Ihnen:
                </p>
                <ul className="list-disc list-inside space-y-1 text-xs">
                  <li>Den angeforderten Compliance-Report zusenden</li>
                  <li>Gelegentlich relevante Compliance-Informationen übermitteln</li>
                </ul>
                <p className="mt-2">
                  Sie erhalten zunächst eine <strong>Bestätigungs-E-Mail</strong>, um Ihre Adresse zu verifizieren. 
                  Erst nach der Bestätigung wird der Report gesendet.
                </p>
                <p className="mt-2">
                  <strong>Ihre Rechte:</strong> Widerruf und Löschung jederzeit möglich unter 
                  <a href="mailto:datenschutz@complyo.tech" className="text-blue-400 hover:underline"> datenschutz@complyo.tech</a>
                </p>
              </div>
              
              <div className="flex space-x-3 pt-4">
                <button
                  type="button"
                  onClick={closeLeadForm}
                  disabled={isGeneratingReport}
                  className="flex-1 px-4 py-3 border border-gray-600 text-gray-300 rounded-lg hover:bg-gray-700 transition-colors disabled:opacity-50"
                >
                  Abbrechen
                </button>
                <button
                  type="submit"
                  disabled={isGeneratingReport || !leadFormData.email.trim() || !leadFormData.name.trim()}
                  className="flex-1 px-4 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg hover:opacity-90 transition-opacity disabled:opacity-50 flex items-center justify-center"
                >
                  {isGeneratingReport ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      Sende...
                    </>
                  ) : (
                    <>📧 Verification senden</>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default ComplyoLandingPage as React.FC<ComplyoLandingProps>;