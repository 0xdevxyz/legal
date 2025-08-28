import React, { useState, useEffect, useRef } from 'react';
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
import { ComplyoAccessibility } from '../lib/accessibility';

interface ComplyoLandingProps {
  variant: 'original' | 'high-conversion';
  sessionId: string;
}


interface AnalysisResult {
  url: string;
  score: number;
  issues: string[];
  riskAmount: string;
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
      question: "Wie funktioniert die KI-Analyse?",
      answer: "Unsere KI (Claude Sonnet 4) analysiert Ihre Website automatisch auf über 100 Compliance-Kriterien. Sie prüft rechtliche Texte, Cookie-Implementation, DSGVO-Konformität und Barrierefreiheit. Anschließend generiert sie maßgeschneiderte Lösungen in deutscher Rechtssprache.",
      isOpen: false
    },
    {
      id: 2,
      question: "Sind die generierten Rechtstexte rechtssicher?",
      answer: "Ja, unsere KI ist speziell auf deutsche Rechtslage trainiert und arbeitet mit aktuellen Rechtsprechungen. Bei unserem Experten-Service werden alle Texte zusätzlich von qualifizierten Anwälten geprüft und freigegeben.",
      isOpen: false
    },
    {
      id: 3,
      question: "Was passiert bei Rechtsänderungen?",
      answer: "Unser System überwacht kontinuierlich Rechtsänderungen und benachrichtigt Sie automatisch. Bei kritischen Änderungen führen wir sofortige Updates durch, damit Ihre Website immer aktuell und rechtssicher bleibt.",
      isOpen: false
    },
    {
      id: 4,
      question: "Funktioniert Complyo mit allen CMS-Systemen?",
      answer: "Ja, Complyo arbeitet CMS-unabhängig. Wir unterstützen WordPress, Shopify, Typo3, Drupal, Joomla und individuelle Lösungen. Unsere KI generiert passenden Code für jedes System und führt Sie durch die Implementation.",
      isOpen: false
    }
  ]);

  // Refs
  const analyzerRef = useRef<HTMLElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Initialize Accessibility Framework
  useEffect(() => {
    // Initialize accessibility framework with settings that won't interfere with input focus
    const a11y = ComplyoAccessibility.init({
      autoFix: false, // Disable auto-fixing to prevent focus issues
      announceChanges: true
    });
    
    // Store globally for testing
    window.ComplyoA11y = a11y;
    
    // Set page title for screen readers
    document.title = 'Complyo - Website Compliance & Abmahnschutz';
    
    // Add a custom event listener to prevent the accessibility framework
    // from interfering with the website-url input field
    const handleFocusIn = (e: FocusEvent) => {
      const target = e.target as HTMLElement;
      if (target.id === 'website-url' && inputRef.current) {
        // Stop propagation to prevent accessibility framework from handling it
        e.stopPropagation();
      }
    };
    
    // Add a custom event listener to handle input field focus
    const handleInputFocus = () => {
      // Make sure the input field is properly focused
      if (inputRef.current) {
        inputRef.current.focus();
      }
    };
    
    document.addEventListener('focusin', handleFocusIn, true);
    
    // Add event listener for the input field
    if (inputRef.current) {
      inputRef.current.addEventListener('click', handleInputFocus);
    }
    
    return () => {
      // Clean up event listeners
      document.removeEventListener('focusin', handleFocusIn, true);
      if (inputRef.current) {
        inputRef.current.removeEventListener('click', handleInputFocus);
      }
    };
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

  // Analysis Functions
  const generateMockAnalysis = (url: string): AnalysisResult => {
    const issues = [
      'Kein DSGVO-konformes Impressum gefunden',
      'Cookie-Banner fehlt oder nicht TTDSG-konform',
      'Datenschutzerklärung unvollständig oder veraltet',
      'Google Analytics ohne Consent-Management',
      'Fehlende Alt-Texte für Barrierefreiheit',
      'Social Media Plugins ohne Zwei-Klick-Lösung',
      'Kontaktformular ohne Datenschutzhinweis',
      'Keine SSL-Verschlüsselung für Formulare'
    ];

    const selectedIssues = issues.slice(0, Math.floor(Math.random() * 5) + 3);
    const score = Math.max(0, 100 - (selectedIssues.length * 15));
    const riskMin = selectedIssues.length * 1000;
    const riskMax = selectedIssues.length * 2500;

    return {
      url,
      score,
      issues: selectedIssues,
      riskAmount: `${riskMin.toLocaleString()}€ - ${riskMax.toLocaleString()}€`
    };
  };

  const analyzeWebsite = async () => {
    if (isAnalyzing || !websiteUrl.trim()) {
      if (!websiteUrl.trim()) {
        alert('Bitte geben Sie eine gültige URL ein.');
      }
      return;
    }

    // Validate URL format
    try {
      new URL(websiteUrl);
    } catch (e) {
      alert('Bitte geben Sie eine gültige URL ein (z.B. https://ihre-website.de)');
      return;
    }

    setIsAnalyzing(true);
    setShowResults(false);

    try {
      // Simulate API call with realistic delay
      await new Promise(resolve => setTimeout(resolve, 3000));
      
      const mockResults = generateMockAnalysis(websiteUrl);
      setAnalysisResults(mockResults);
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
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-lg">C</span>
            </div>
            <span className="text-xl font-bold text-white">Complyo</span>
          </div>
          
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
        <h1 className="text-4xl md:text-6xl lg:text-7xl font-bold mb-6">
          Von{' '}
          <span className="bg-gradient-to-r from-blue-500 to-purple-600 bg-clip-text text-transparent">
            abmahngefährdet
          </span>
          <br />
          zu{' '}
          <span className="bg-gradient-to-r from-blue-500 to-purple-600 bg-clip-text text-transparent">
            rechtssicher
          </span>
          <br />
          in 24 Stunden
        </h1>
        
        <p className="text-xl md:text-2xl text-gray-300 mb-8 max-w-3xl mx-auto">
          KI-gestützte Website-Compliance für DSGVO, Cookies & Barrierefreiheit. 
          Automatisch oder durch Experten - mit echtem Abmahnschutz.
        </p>
        
        <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-12">
          <button 
            onClick={scrollToAnalyzer}
            className="bg-gradient-to-r from-blue-500 to-purple-600 px-8 py-4 rounded-lg text-lg font-semibold hover:scale-105 transition-transform shadow-2xl"
          >
            🚀 Kostenlose Website-Analyse
          </button>
          <button 
            onClick={() => openModal('demo-modal')}
            className="bg-white/10 backdrop-blur-md border border-white/20 px-8 py-4 rounded-lg text-lg font-semibold hover:bg-white/20 transition-colors"
          >
            📹 Live-Demo ansehen
          </button>
        </div>
        
        {/* Risk Calculator Teaser */}
        <div className="bg-white/10 backdrop-blur-md border border-white/20 p-6 rounded-2xl max-w-2xl mx-auto">
          <h3 className="text-xl font-semibold mb-4">💰 Ihr aktuelles Abmahnrisiko:</h3>
          <div className="text-3xl font-bold text-red-400 mb-2">4.000€ - 20.000€+</div>
          <p className="text-gray-300">Durchschnittliches Risiko für deutsche Websites ohne vollständige Compliance</p>
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
          <h2 className="text-4xl md:text-5xl font-bold mb-6">
            🔍 Kostenlose{' '}
            <span className="bg-gradient-to-r from-blue-500 to-purple-600 bg-clip-text text-transparent">
              Website-Analyse
            </span>
          </h2>
          <p className="text-xl text-gray-300">
            Erfahren Sie in 30 Sekunden, wo Ihre Website rechtliche Risiken hat
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
          
          {/* Analysis Results */}
          {showResults && analysisResults && (
            <div id="analysis-results" className="border-t border-gray-600 pt-6">
              <h3 className="text-xl font-semibold mb-4">📊 Analyse-Ergebnisse:</h3>
              
              <div className="grid md:grid-cols-2 gap-6 mb-6">
                <div className="bg-gray-900 p-4 rounded-lg">
                  <h4 className="font-semibold mb-3">📊 Compliance-Score</h4>
                  <div className="flex items-center">
                    <div className={`text-3xl font-bold ${
                      analysisResults.score >= 80 ? 'text-green-400' : 
                      analysisResults.score >= 60 ? 'text-yellow-400' : 'text-red-400'
                    }`}>
                      {analysisResults.score}/100
                    </div>
                    <div className="ml-4 flex-1">
                      <div className="w-full bg-gray-700 rounded-full h-3">
                        <div 
                          className={`h-3 rounded-full ${
                            analysisResults.score >= 80 ? 'bg-green-400' : 
                            analysisResults.score >= 60 ? 'bg-yellow-400' : 'bg-red-400'
                          }`}
                          style={{ width: `${analysisResults.score}%` }}
                        ></div>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div className="bg-gray-900 p-4 rounded-lg">
                  <h4 className="font-semibold mb-3">⚠️ Gefundene Probleme</h4>
                  <div className="text-2xl font-bold text-red-400">{analysisResults.issues.length}</div>
                  <p className="text-sm text-gray-300">Compliance-Verstöße gefunden</p>
                </div>
              </div>
              
              <div className="bg-gray-900 p-4 rounded-lg mb-6">
                <h4 className="font-semibold mb-3">🔍 Detaillierte Probleme:</h4>
                <ul className="space-y-2">
                  {analysisResults.issues.map((issue, index) => (
                    <li key={index} className="flex items-start">
                      <span className="text-red-400 mr-2">•</span>
                      <span className="text-gray-300">{issue}</span>
                    </li>
                  ))}
                </ul>
              </div>
              
              <div className="p-4 bg-red-900 bg-opacity-50 rounded-lg border border-red-500 mb-6">
                <h4 className="font-semibold text-red-300 mb-2">⚠️ Geschätztes Abmahnrisiko:</h4>
                <div className="text-2xl font-bold text-red-400">{analysisResults.riskAmount}</div>
                <p className="text-sm text-red-300 mt-2">Basierend auf gefundenen Compliance-Verstößen</p>
              </div>
              
              <div className="flex flex-col sm:flex-row gap-4 mb-6">
                <button 
                  onClick={generateReport}
                  className="flex-1 bg-green-600 hover:bg-green-700 px-6 py-3 rounded-lg font-semibold transition-colors"
                >
                  📄 Vollständigen Report erhalten
                </button>
                <button 
                  onClick={() => {
                    setSelectedPlan('ki');
                    openModal('pricing-modal');
                  }}
                  className="flex-1 bg-gradient-to-r from-blue-500 to-purple-600 px-6 py-3 rounded-lg font-semibold hover:scale-105 transition-transform"
                >
                  🛡️ Jetzt rechtssicher machen
                </button>
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
            ⚡ Die 4 Säulen der{' '}
            <span className="bg-gradient-to-r from-blue-500 to-purple-600 bg-clip-text text-transparent">
              Compliance
            </span>
          </h2>
          <p className="text-xl text-gray-300 max-w-3xl mx-auto">
            Unser KI-System macht Ihre Website in allen relevanten Bereichen rechtssicher
          </p>
        </div>
        
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
          {[
            {
              icon: <FileText className="w-8 h-8" />,
              title: "Rechtliche Texte",
              features: [
                "DSGVO-konformes Impressum",
                "Datenschutzerklärung",
                "AGB & Widerrufsbelehrung",
                "Automatische Updates"
              ]
            },
            {
              icon: <Cookie className="w-8 h-8" />,
              title: "Cookie-Compliance",
              features: [
                "TTDSG-konforme Banner",
                "Consent Management",
                "Script-Erfassung",
                "Cookie-Kategorisierung"
              ]
            },
            {
              icon: <Shield className="w-8 h-8" />,
              title: "DSGVO-Compliance",
              features: [
                "Datenverarbeitungs-Audit",
                "Privacy-by-Design",
                "Betroffenenrechte",
                "Dokumentation"
              ]
            },
            {
              icon: <Eye className="w-8 h-8" />,
              title: "Barrierefreiheit",
              features: [
                "WCAG 2.1 AA Standard",
                "BITV 2.0 konform",
                "Screen-Reader optimiert",
                "Keyboard-Navigation"
              ]
            }
          ].map((pillar, index) => (
            <div key={index} className="bg-white/10 backdrop-blur-md border border-white/20 p-8 rounded-2xl hover:scale-105 transition-transform">
              <div className="text-blue-400 mb-4">{pillar.icon}</div>
              <h3 className="text-xl font-bold mb-4">{pillar.title}</h3>
              <ul className="text-gray-300 space-y-2 text-sm">
                {pillar.features.map((feature, featureIndex) => (
                  <li key={featureIndex} className="flex items-center">
                    <Check className="w-4 h-4 text-green-400 mr-2" />
                    {feature}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>
    </section>
  );

  const PricingSection = () => (
    <section id="pricing" className="py-20">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold mb-6">
            💰 Transparente{' '}
            <span className="bg-gradient-to-r from-blue-500 to-purple-600 bg-clip-text text-transparent">
              Preise
            </span>
          </h2>
          <p className="text-xl text-gray-300">
            Wählen Sie die Lösung, die zu Ihrem Bedarf passt
          </p>
        </div>
        
        <div className="grid md:grid-cols-3 gap-8">
          {/* Free Tier */}
          <div className="bg-white/10 backdrop-blur-md border border-white/20 p-8 rounded-2xl">
            <div className="text-center mb-8">
              <h3 className="text-2xl font-bold mb-2">Kostenlose Analyse</h3>
              <div className="text-4xl font-bold mb-4">0€</div>
              <p className="text-gray-300">Für erste Einschätzung</p>
            </div>
            
            <ul className="space-y-3 mb-8">
              {[
                "Vollständiger Compliance-Scan",
                "Abmahnrisiko in Euro",
                "PDF-Report",
                "Handlungsempfehlungen"
              ].map((feature, index) => (
                <li key={index} className="flex items-center">
                  <Check className="w-5 h-5 text-green-400 mr-3" />
                  {feature}
                </li>
              ))}
            </ul>
            
            <button 
              onClick={scrollToAnalyzer}
              className="w-full bg-white/10 hover:bg-white/20 backdrop-blur-md border border-white/20 px-6 py-3 rounded-lg font-semibold transition-colors"
            >
              Jetzt kostenlos testen
            </button>
          </div>
          
          {/* KI Plan */}
          <div className="relative">
            <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
              <span className="bg-gradient-to-r from-blue-500 to-purple-600 px-4 py-2 rounded-full text-sm font-semibold">
                Beliebt
              </span>
            </div>
            <div className="bg-white/10 backdrop-blur-md border-2 border-blue-500 p-8 rounded-2xl">
              <div className="text-center mb-8">
                <h3 className="text-2xl font-bold mb-2">KI-Automatisierung</h3>
                <div className="text-4xl font-bold mb-4">
                  39€<span className="text-lg">/Monat</span>
                </div>
                <p className="text-gray-300">Der intelligente Weg</p>
              </div>
              
              <ul className="space-y-3 mb-8">
                {[
                  "Automatische Rechtstexte",
                  "24h-Umsetzungsgarantie",
                  "Monatliche Re-Scans",
                  "Live-Dashboard"
                ].map((feature, index) => (
                  <li key={index} className="flex items-center">
                    <Check className="w-5 h-5 text-green-400 mr-3" />
                    {feature}
                  </li>
                ))}
              </ul>
              
              <button 
                onClick={() => {
                  setSelectedPlan('ki');
                  openModal('pricing-modal');
                }}
                className="w-full bg-gradient-to-r from-blue-500 to-purple-600 px-6 py-3 rounded-lg font-semibold hover:scale-105 transition-transform"
              >
                Jetzt starten
              </button>
            </div>
          </div>
          
          {/* Expert Plan */}
          <div className="bg-white/10 backdrop-blur-md border border-white/20 p-8 rounded-2xl">
            <div className="text-center mb-8">
              <h3 className="text-2xl font-bold mb-2">Experten-Service</h3>
              <div className="text-3xl font-bold mb-2">
                2.000€ <span className="text-lg">Setup</span>
              </div>
              <div className="text-xl font-bold mb-4">
                + 39€<span className="text-lg">/Monat</span>
              </div>
              <p className="text-gray-300">Die Profi-Lösung</p>
            </div>
            
            <ul className="space-y-3 mb-8">
              {[
                "Persönliche Anwalts-Betreuung",
                "Branchenspezifische Compliance",
                "Custom-Integration",
                "Quartalsweise Reviews",
                "Direkte Experten-Hotline"
              ].map((feature, index) => (
                <li key={index} className="flex items-center">
                  <Check className="w-5 h-5 text-green-400 mr-3" />
                  {feature}
                </li>
              ))}
            </ul>
            
            <button 
              onClick={() => {
                setSelectedPlan('expert');
                openModal('pricing-modal');
              }}
              className="w-full bg-white/10 hover:bg-white/20 backdrop-blur-md border border-white/20 px-6 py-3 rounded-lg font-semibold transition-colors"
            >
              Beratung anfragen
            </button>
          </div>
        </div>
      </div>
    </section>
  );

  const SocialProofSection = () => (
    <section className="py-20 bg-gray-800">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold mb-6">
            🏆 Vertrauen Sie auf{' '}
            <span className="bg-gradient-to-r from-blue-500 to-purple-600 bg-clip-text text-transparent">
              Expertise
            </span>
          </h2>
        </div>
        
        <div className="grid md:grid-cols-3 gap-8 mb-16">
          <div className="text-center">
            <div className="text-4xl font-bold text-blue-400 mb-2">500+</div>
            <p className="text-gray-300">Websites rechtssicher gemacht</p>
          </div>
          <div className="text-center">
            <div className="text-4xl font-bold text-green-400 mb-2">99%</div>
            <p className="text-gray-300">Abmahnrisiko-Reduktion</p>
          </div>
          <div className="text-center">
            <div className="text-4xl font-bold text-purple-400 mb-2">24h</div>
            <p className="text-gray-300">Durchschnittliche Umsetzungszeit</p>
          </div>
        </div>
        
        {/* Testimonials */}
        <div className="grid md:grid-cols-2 gap-8">
          <div className="bg-white/10 backdrop-blur-md border border-white/20 p-6 rounded-2xl">
            <div className="flex items-center mb-4">
              <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center mr-4">
                <span className="text-white font-bold">MS</span>
              </div>
              <div>
                <h4 className="font-semibold">Marcus Schmidt</h4>
                <p className="text-gray-400 text-sm">E-Commerce Unternehmer</p>
              </div>
            </div>
            <p className="text-gray-300 mb-4">
              "Nach einer teuren Abmahnung wegen fehlender Cookie-Banner war Complyo meine Rettung. 
              Innerhalb von 24 Stunden war alles rechtssicher - automatisch und ohne Stress."
            </p>
            <div className="flex text-yellow-400">
              {[...Array(5)].map((_, i) => (
                <Star key={i} className="w-5 h-5 fill-current" />
              ))}
            </div>
          </div>
          
          <div className="bg-white/10 backdrop-blur-md border border-white/20 p-6 rounded-2xl">
            <div className="flex items-center mb-4">
              <div className="w-12 h-12 bg-gradient-to-r from-green-500 to-blue-500 rounded-full flex items-center justify-center mr-4">
                <span className="text-white font-bold">AK</span>
              </div>
              <div>
                <h4 className="font-semibold">Anna Krüger</h4>
                <p className="text-gray-400 text-sm">Digitalagentur-Inhaberin</p>
              </div>
            </div>
            <p className="text-gray-300 mb-4">
              "Für unsere Agentur ist Complyo ein Game-Changer. Wir können jetzt allen Kunden 
              sofort Compliance anbieten, ohne eigene Rechtsexperten zu beschäftigen."
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
    <section className="py-20 bg-gray-800">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <h2 className="text-4xl md:text-5xl font-bold mb-6">
          🚀 Bereit für{' '}
          <span className="bg-gradient-to-r from-blue-500 to-purple-600 bg-clip-text text-transparent">
            rechtssichere
          </span>{' '}
          Websites?
        </h2>
        <p className="text-xl text-gray-300 mb-8 max-w-2xl mx-auto">
          Starten Sie jetzt mit der kostenlosen Analyse und erfahren Sie, 
          wo Ihre Website rechtliche Risiken hat.
        </p>
        
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <button 
            onClick={scrollToAnalyzer}
            className="bg-gradient-to-r from-blue-500 to-purple-600 px-8 py-4 rounded-lg text-lg font-semibold hover:scale-105 transition-transform shadow-2xl"
          >
            🔍 Kostenlose Analyse starten
          </button>
          <button 
            onClick={() => openModal('demo-modal')}
            className="bg-white/10 backdrop-blur-md border border-white/20 px-8 py-4 rounded-lg text-lg font-semibold hover:bg-white/20 transition-colors"
          >
            📞 Demo-Termin buchen
          </button>
        </div>
      </div>
    </section>
  );

  const Footer = () => (
    <footer className="py-12 border-t border-gray-700">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid md:grid-cols-4 gap-8">
          <div className="md:col-span-2">
            <div className="flex items-center space-x-2 mb-4">
              <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-lg">C</span>
              </div>
              <span className="text-xl font-bold">Complyo</span>
            </div>
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
            <a href="#" className="text-gray-400 hover:text-white text-sm transition-colors">
              Impressum
            </a>
            <a href="#" className="text-gray-400 hover:text-white text-sm transition-colors">
              Datenschutz
            </a>
            <a href="#" className="text-gray-400 hover:text-white text-sm transition-colors">
              AGB
            </a>
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
            <h3 className="text-2xl font-bold mb-6">🤖 KI-Automatisierung</h3>
            <div className="text-center mb-6">
              <div className="text-4xl font-bold mb-2">39€<span className="text-lg">/Monat</span></div>
              <p className="text-gray-300">Der intelligente Weg zur Compliance</p>
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
                className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-white placeholder-gray-400"
              />
              <input 
                type="url" 
                name="website"
                placeholder="Ihre Website-URL" 
                required
                className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-white placeholder-gray-400"
              />
              <button 
                type="submit" 
                className="w-full bg-gradient-to-r from-blue-500 to-purple-600 px-6 py-3 rounded-lg font-semibold hover:opacity-90 transition-opacity"
              >
                Jetzt für 39€/Monat starten
              </button>
            </form>
            
            <p className="text-xs text-gray-400 mt-4 text-center">
              🔒 SSL-verschlüsselt • Jederzeit kündbar • 14 Tage Geld-zurück-Garantie
            </p>
          </>
        ) : (
          <>
            <h3 className="text-2xl font-bold mb-6">👨‍💼 Experten-Service</h3>
            <div className="text-center mb-6">
              <div className="text-3xl font-bold mb-2">2.000€ <span className="text-lg">Setup</span></div>
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
                className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-white placeholder-gray-400"
              />
              <input 
                type="email" 
                name="email"
                placeholder="Ihre E-Mail-Adresse" 
                required 
                className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-white placeholder-gray-400"
              />
              <input 
                type="tel" 
                name="phone"
                placeholder="Telefonnummer" 
                required
                className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-white placeholder-gray-400"
              />
              <textarea 
                name="requirements"
                placeholder="Beschreiben Sie Ihre Anforderungen..." 
                required
                rows={4}
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
      <Navigation />
      <HeroSection />
      <AnalyzerSection />
      <FeaturesSection />
      <SocialProofSection />
      <PricingSection />
      <FAQSection />
      <CTASection />
      <Footer />
      
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

export default ComplyoLandingPage;