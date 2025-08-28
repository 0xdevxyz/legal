
import React, { useState, useEffect } from 'react';
import { Check, Shield, Lock, Eye, FileText, Cookie, Users, Zap } from 'lucide-react';
import { ComplyoAccessibility } from '../lib/accessibility';

interface ComplyoLandingProps {
  variant: 'original' | 'high-conversion';
  sessionId: string;
}


interface AnalysisResult {
  category: string;
  status: 'pass' | 'warning' | 'fail';
  score: number;
  message: string;
  details?: Record<string, any>;
}

interface AnalysisData {
  overall_score: number;
  total_issues: number;
  results: AnalysisResult[];
  scan_timestamp?: string;
  scan_duration_ms?: number;
}

type NotificationType = 'success' | 'error' | 'warning' | 'info';

interface Notification {
  id: string;
  message: string;

  type: NotificationType;
}

const ComplyoLandingPage: React.FC<ComplyoLandingProps> = ({ variant, sessionId }) => {
  const [url, setUrl] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResults, setAnalysisResults] = useState<AnalysisData | null>(null);
  const [showResults, setShowResults] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  
  // Lead generation form state
  const [showLeadForm, setShowLeadForm] = useState(false);
  const [isGeneratingReport, setIsGeneratingReport] = useState(false);
  const [leadFormData, setLeadFormData] = useState({
    email: '',
    name: '',
    company: ''
  });

  // Use relative URL to avoid CORS issues when deployed
  const API_BASE = process.env.NODE_ENV === 'production'
    ? '' // Empty string for production to use relative URLs
    : process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8002';

  // Initialize Accessibility Framework
  useEffect(() => {
    const a11y = ComplyoAccessibility.init({
      autoFix: true,
      announceChanges: true
    });
    
    // Store globally for testing
    window.ComplyoA11y = a11y;
    
    // Set page title for screen readers
    document.title = 'Complyo - Automatische Website-Compliance mit Abmahnschutz';
    
    return () => {
      // Cleanup if needed
    };
  }, []);

  // Notification system
  const addNotification = (message: string, type: NotificationType = 'info') => {
    const id = Date.now().toString();
    const newNotification: Notification = { id, message, type };
    setNotifications(prev => [...prev, newNotification]);

    // Announce to screen readers
    if (window.ComplyoA11y) {
      window.ComplyoA11y.announce(message, type === 'error' ? 'assertive' : 'polite');
    }

    // Auto remove after 5 seconds
    setTimeout(() => {
      setNotifications(prev => prev.filter(n => n.id !== id));
    }, 5000);
  };

  const removeNotification = (id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  };

  // API Health Check
  useEffect(() => {
    fetch(`${API_BASE ? `${API_BASE}/health` : '/api/health'}`)
      .then(response => response.json())
      .then(data => {
        console.log('API Health Check:', data);
      })
      .catch(error => {
        console.warn('API not available, using demo mode:', error);
      });
  }, []);

  // URL Normalization function
  const normalizeUrl = (input: string): string => {
    if (!input || typeof input !== 'string') {
      throw new Error('URL is required and must be a string');
    }

    let url = input.trim();
    
    if (!url) {
      throw new Error('URL cannot be empty');
    }

    // Remove common user input issues
    url = url.replace(/^www\./, ''); // Remove leading www
    url = url.replace(/\/$/, ''); // Remove trailing slash
    
    // Add https:// if no protocol is present
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
      url = 'https://' + url;
    }

    // Basic validation
    try {
      const urlObj = new URL(url);
      
      // Basic domain validation
      if (!urlObj.hostname || urlObj.hostname.length < 3) {
        throw new Error('Invalid domain');
      }
      
      if (!urlObj.hostname.includes('.')) {
        throw new Error('Domain must contain at least one dot');
      }
      
      return url;
    } catch (error) {
      throw new Error(`Invalid URL format: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  };

  // Website Analysis
  const analyzeWebsite = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!url.trim()) {
      addNotification('Bitte geben Sie eine URL ein (z.B. example.com)', 'error');
      return;
    }

    // Normalize and validate URL
    let normalizedUrl: string;
    try {
      normalizedUrl = normalizeUrl(url);
    } catch (error) {
      addNotification(`Ungültige URL: ${error instanceof Error ? error.message : 'Unbekannter Fehler'}`, 'error');
      return;
    }

    setIsAnalyzing(true);
    setShowResults(false);

    try {
      const response = await fetch(`${API_BASE ? `${API_BASE}/api/analyze` : '/api/analyze'}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'same-origin',
        body: JSON.stringify({ url: normalizedUrl })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const backendData = await response.json();
      
      // Transform backend data to frontend format
      const transformedData: AnalysisData = {
        overall_score: backendData.compliance_score || 0,
        total_issues: backendData.findings ? Object.keys(backendData.findings).filter(key => 
          backendData.findings[key].includes('nicht') || 
          backendData.findings[key].includes('fehlt') ||
          backendData.findings[key].includes('Kein')
        ).length : 0,
        results: backendData.findings ? Object.entries(backendData.findings).map(([key, value]) => {
          const score = getScoreFromText(String(value));
          return {
            category: getCategoryDisplayName(key),
            status: getStatusFromScore(score),
            score: score,
            message: String(value),
            details: { source: key }
          };
        }) : []
      };
      
      setAnalysisResults(transformedData);
      setShowResults(true);
      addNotification('Analyse erfolgreich abgeschlossen!', 'success');
      
    } catch (error) {
      console.error('Analysis error:', error);
      
      // Show demo data as fallback
      const demoData: AnalysisData = {
        overall_score: 65,
        total_issues: 4,
        results: [
          {
            category: "Impressum",
            status: "warning",
            score: 75,
            message: "Impressum gefunden, aber unvollständig",
            details: { found: true, complete: false }
          },
          {
            category: "Datenschutzerklärung",
            status: "pass",
            score: 90,
            message: "DSGVO-konforme Datenschutzerklärung gefunden",
            details: { found: true, gdpr_compliant: true }
          },
          {
            category: "Cookie-Compliance",
            status: "fail",
            score: 30,
            message: "Kein Cookie-Consent-Banner gefunden",
            details: { banner_found: false, consent_mechanism: false }
          },
          {
            category: "Barrierefreiheit",
            status: "warning",
            score: 65,
            message: "Grundlegende Barrierefreiheit vorhanden, Verbesserungen möglich",
            details: { alt_texts: "partial", contrast: "good", navigation: "needs_improvement" }
          }
        ]
      };
      
      setAnalysisResults(demoData);
      setShowResults(true);
      addNotification('Demo-Daten werden angezeigt (API nicht verfügbar)', 'warning');
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Helper functions for data transformation
  const getCategoryDisplayName = (key: string): string => {
    const categoryMap: Record<string, string> = {
      'impressum': 'Impressum',
      'datenschutzerklaerung': 'Datenschutzerklärung',
      'cookies': 'Cookie-Compliance',
      'accessibility': 'Barrierefreiheit'
    };
    return categoryMap[key] || key;
  };

  const getScoreFromText = (text: string): number => {
    // Simple scoring based on text analysis
    if (text.includes('nicht') || text.includes('Kein') || text.includes('fehlt')) {
      return 25; // fail
    } else if (text.includes('unvollständig') || text.includes('Verbesserungen') || text.includes('mehrere')) {
      return 65; // warning
    } else {
      return 90; // pass
    }
  };

  const getStatusFromScore = (score: number): 'pass' | 'warning' | 'fail' => {
    if (score >= 80) return 'pass';
    if (score >= 50) return 'warning';
    return 'fail';
  };

  const generateReport = () => {
    if (!analysisResults) {
      addNotification('Bitte führen Sie zuerst eine Analyse durch', 'error');
      return;
    }
    setShowLeadForm(true);
  };

  const handleLeadFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!leadFormData.email.trim() || !leadFormData.name.trim()) {
      addNotification('Bitte füllen Sie alle Pflichtfelder aus', 'error');
      return;
    }

    setIsGeneratingReport(true);
    
    try {
      // Send lead data to backend
      const leadData = {
        name: leadFormData.name.trim(),
        email: leadFormData.email.trim(),
        company: leadFormData.company.trim() || null,
        url: url,
        analysis_data: analysisResults,
        session_id: sessionId
      };
      
      const response = await fetch(`${API_BASE ? `${API_BASE}/api/leads/collect` : '/api/leads/collect'}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'same-origin',
        body: JSON.stringify(leadData)
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const result = await response.json();
      
      // Close form and show appropriate success message
      setShowLeadForm(false);
      
      if (result.verified) {
        addNotification(`✅ Report wird sofort an ${leadFormData.email} gesendet!`, 'success');
      } else {
        addNotification(`📧 Bestätigungs-E-Mail gesendet! Bitte prüfen Sie Ihr Postfach.`, 'success');
      }
      
      // Reset form
      setLeadFormData({ email: '', name: '', company: '' });
      
      console.log('Lead successfully submitted:', result);
      
    } catch (error) {
      console.error('Error submitting lead:', error);
      addNotification('Fehler beim Senden der Daten. Bitte versuchen Sie es erneut.', 'error');
    } finally {
      setIsGeneratingReport(false);
    }
  };

  const closeLeadForm = () => {
    setShowLeadForm(false);
    setLeadFormData({ email: '', name: '', company: '' });
  };

  const upgradeToPro = () => {
    addNotification('Weiterleitung zum Checkout...', 'info');
    setTimeout(() => {
      window.open('https://billing.complyo.tech/checkout/pro', '_blank');
    }, 1000);
  };

  const contactExpert = () => {
    addNotification('Weiterleitung zu Expertenberatung...', 'info');
    setTimeout(() => {
      window.open('https://calendly.com/complyo-experts', '_blank');
    }, 1000);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pass': return '✅';
      case 'warning': return '⚠️';
      case 'fail': return '❌';
      default: return '❓';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pass': return 'text-green-400';
      case 'warning': return 'text-yellow-400';
      case 'fail': return 'text-red-400';
      default: return 'text-gray-400';
    }
  };

  const scrollToSection = (sectionId: string) => {
    const element = document.getElementById(sectionId);
    element?.scrollIntoView({ behavior: 'smooth' });
    setMobileMenuOpen(false);
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100" role="document">
      {/* Skip Links for Accessibility */}
      <a 
        href="#main-content" 
        className="a11y-skip-link"
      >
        Zum Hauptinhalt springen
      </a>
      <a 
        href="#navigation" 
        className="a11y-skip-link"
      >
        Zur Navigation springen
      </a>

      {/* Notifications */}
      <div 
        className="fixed top-4 right-4 z-50 space-y-2"
        role="region"
        aria-label="Benachrichtigungen"
        aria-live="polite"
      >
        {notifications.map((notification) => (
          <div
            key={notification.id}
            className={`p-4 rounded-lg shadow-lg max-w-sm transform transition-all duration-300 ${
              notification.type === 'success' ? 'bg-green-600' :
              notification.type === 'error' ? 'bg-red-600' :
              notification.type === 'warning' ? 'bg-yellow-600' :
              'bg-blue-600'
            }`}
            role="alert"
            aria-atomic="true"
          >
            <div className="flex items-center space-x-3">
              <span className="flex-shrink-0">
                {notification.type === 'success' ? '✅' :
                 notification.type === 'error' ? '❌' :
                 notification.type === 'warning' ? '⚠️' : 'ℹ️'}
              </span>
              <p className="text-sm font-medium text-white">{notification.message}</p>
              <button
                onClick={() => removeNotification(notification.id)}
                className="ml-auto text-white hover:opacity-70 text-lg leading-none focus:outline-none focus:ring-2 focus:ring-white/50 rounded"
                aria-label="Benachrichtigung schließen"
              >
                ×
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Navigation */}
      <nav 
        id="navigation"
        className="fixed top-0 w-full z-40 bg-slate-900/80 backdrop-blur-md border-b border-slate-800"
        role="navigation"
        aria-label="Hauptnavigation"
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <Check className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                Complyo
              </span>
            </div>
            
            <div className="hidden md:flex items-center space-x-8">
              <button 
                onClick={() => scrollToSection('features')}
                className="text-slate-300 hover:text-white transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 rounded px-2 py-1"
                aria-describedby="features-nav-desc"
              >
                Features
              </button>
              <span id="features-nav-desc" className="sr-only">Zu den Funktionen springen</span>
              
              <button 
                onClick={() => scrollToSection('pricing')}
                className="text-slate-300 hover:text-white transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 rounded px-2 py-1"
                aria-describedby="pricing-nav-desc"
              >
                Preise
              </button>
              <span id="pricing-nav-desc" className="sr-only">Zu den Preisen springen</span>
              
              <button 
                onClick={() => scrollToSection('contact')}
                className="text-slate-300 hover:text-white transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 rounded px-2 py-1"
                aria-describedby="contact-nav-desc"
              >
                Kontakt
              </button>
              <span id="contact-nav-desc" className="sr-only">Zum Kontaktbereich springen</span>
              
              <button 
                onClick={() => scrollToSection('demo')}
                className="bg-gradient-to-r from-blue-500 to-purple-600 text-white px-4 py-2 rounded-lg hover:opacity-90 transition-opacity focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-slate-900"
                aria-describedby="demo-nav-desc"
              >
                Demo starten
              </button>
              <span id="demo-nav-desc" className="sr-only">Zur Demo-Sektion springen</span>
            </div>
            
            {/* Mobile menu button */}
            <div className="md:hidden">
              <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="text-slate-300 hover:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 rounded p-2"
                aria-expanded={mobileMenuOpen}
                aria-controls="mobile-menu"
                aria-label={mobileMenuOpen ? 'Navigationsmenü schließen' : 'Navigationsmenü öffnen'}
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              </button>
            </div>
          </div>
        </div>
        
        {/* Mobile menu */}
        {mobileMenuOpen && (
          <div 
            id="mobile-menu"
            className="md:hidden bg-slate-800/95 backdrop-blur-md"
            role="menu"
            aria-label="Mobile Navigation"
          >
            <div className="px-2 pt-2 pb-3 space-y-1">
              <button 
                onClick={() => scrollToSection('features')}
                className="block w-full text-left px-3 py-2 text-slate-300 hover:text-white transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 rounded"
                role="menuitem"
              >
                Features
              </button>
              <button 
                onClick={() => scrollToSection('pricing')}
                className="block w-full text-left px-3 py-2 text-slate-300 hover:text-white transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 rounded"
                role="menuitem"
              >
                Preise
              </button>
              <button 
                onClick={() => scrollToSection('contact')}
                className="block w-full text-left px-3 py-2 text-slate-300 hover:text-white transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 rounded"
                role="menuitem"
              >
                Kontakt
              </button>
              <button 
                onClick={() => scrollToSection('demo')}
                className="w-full text-left px-3 py-2 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                role="menuitem"
              >
                Demo starten
              </button>
            </div>
          </div>
        )}
      </nav>

      {/* Hero Section */}
      <main id="main-content" role="main">
        <section id="demo" className="pt-24 pb-16 px-4 sm:px-6 lg:px-8" aria-labelledby="hero-heading">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h1 id="hero-heading" className="text-4xl md:text-6xl font-bold mb-6">
              <span className="bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                KI-gestützte
              </span>
              <br />
              Website-Compliance
            </h1>
            <p className="text-xl text-slate-400 mb-8 max-w-3xl mx-auto">
              Schützen Sie sich vor Abmahnungen mit automatischer DSGVO-, Cookie- und Barrierefreiheits-Analyse. 
              Von abmahngefährdet zu rechtssicher in 24 Stunden.
            </p>
            
            {/* Website Analysis Form */}
            <div className="max-w-2xl mx-auto">
              <div className="bg-slate-800/50 backdrop-blur-md rounded-2xl p-8 border border-slate-700">
                <h3 className="text-2xl font-semibold mb-6">Kostenlose Website-Analyse</h3>
                <form 
                  onSubmit={analyzeWebsite} 
                  className="a11y-form space-y-4"
                  role="search"
                  aria-labelledby="hero-heading"
                >
                  <fieldset className="a11y-fieldset border-0 p-0">
                    <legend className="sr-only">Website-URL eingeben für Compliance-Analyse</legend>
                    <div className="flex flex-col sm:flex-row gap-4">
                      <div className="flex-1">
                        <label htmlFor="website-url" className="sr-only">
                          Website-URL für Analyse
                        </label>
                        <input 
                          id="website-url"
                          type="text" 
                          value={url}
                          onChange={(e) => setUrl(e.target.value)}
                          placeholder="beispiel.de oder https://ihre-website.de" 
                          required
                          className="a11y-input w-full px-4 py-3 rounded-lg bg-slate-700 border border-slate-600 text-white placeholder-slate-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                          disabled={isAnalyzing}
                          aria-describedby="url-help"
                          aria-required="true"
                          autoComplete="url"
                        />
                        <div id="url-help" className="a11y-help mt-2 text-slate-400 text-sm text-left">
                          Geben Sie Ihre Website-URL ein (mit oder ohne https://)
                        </div>
                      </div>
                      <button 
                        type="submit" 
                        disabled={isAnalyzing || !url.trim()}
                        className="a11y-btn px-8 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg hover:opacity-90 transition-opacity font-semibold disabled:opacity-50 disabled:cursor-not-allowed focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-slate-800"
                        aria-describedby="analyze-btn-desc"
                      >
                        {isAnalyzing ? 'Analysiere...' : 'Analysieren'}
                      </button>
                      <div id="analyze-btn-desc" className="sr-only">
                        Startet eine umfassende Compliance-Analyse Ihrer Website
                      </div>
                    </div>
                  </fieldset>
                </form>
                
                {/* Loading State */}
                {isAnalyzing && (
                  <div className="mt-8 flex items-center justify-center space-x-3">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                    <span className="text-slate-400">Website wird analysiert...</span>
                  </div>
                )}
                
                {/* Results Container */}
                {showResults && analysisResults && (
                  <div className="mt-8" role="region" aria-labelledby="results-heading">
                    <div className="bg-slate-700 rounded-lg p-6">
                      <div className="flex items-center justify-between mb-4">
                        <h4 id="results-heading" className="text-lg font-semibold">Analyse-Ergebnisse</h4>
                        <div 
                          className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent"
                          role="text"
                          aria-label={`Gesamt-Score: ${Math.round(analysisResults.overall_score)} Prozent`}
                        >
                          {Math.round(analysisResults.overall_score)}%
                        </div>
                      </div>
                      <div className="space-y-4" role="list" aria-label="Compliance-Ergebnisse">
                        {analysisResults.results && analysisResults.results.length > 0 ? (
                          analysisResults.results.map((result, index) => (
                            <div key={index} className="border border-slate-600 rounded-lg p-4" role="listitem">
                              <div className="flex items-center justify-between mb-2">
                                <div className="flex items-center space-x-3">
                                  <span 
                                    className="text-xl"
                                    role="img"
                                    aria-label={`Status: ${result.status === 'pass' ? 'Bestanden' : result.status === 'warning' ? 'Warnung' : 'Fehlgeschlagen'}`}
                                  >
                                    {getStatusIcon(result.status)}
                                  </span>
                                  <h5 className="font-semibold">{result.category}</h5>
                                </div>
                                <span 
                                  className={`text-sm font-medium ${getStatusColor(result.status)}`}
                                  aria-label={`Score: ${result.score} Prozent`}
                                >
                                  {result.score}%
                                </span>
                              </div>
                              <p className="text-slate-400 text-sm mb-2">{result.message}</p>
                              {result.details && (
                                <div className="mt-2 text-xs text-slate-500">
                                  {Object.entries(result.details).map(([key, value]) => (
                                    <span key={key} className="inline-block mr-3">
                                      {key}: {String(value)}
                                    </span>
                                  ))}
                                </div>
                              )}
                            </div>
                          ))
                        ) : (
                          <div className="text-center text-slate-400 py-4">
                            Keine Analyseergebnisse verfügbar
                          </div>
                        )}
                      </div>
                      <div className="mt-6 pt-4 border-t border-slate-600">
                        <button 
                          onClick={generateReport}
                          className="a11y-btn w-full py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors focus:ring-2 focus:ring-green-500 focus:ring-offset-2 focus:ring-offset-slate-700"
                          aria-describedby="report-btn-desc"
                        >
                          <span role="img" aria-label="Dokument-Symbol">📄</span>
                          <span className="ml-2">Vollständigen Report generieren</span>
                        </button>
                        <div id="report-btn-desc" className="sr-only">
                          Erstellt einen detaillierten PDF-Report mit allen Compliance-Ergebnissen
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4 bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
              Vollständiger Abmahnschutz
            </h2>
            <p className="text-xl text-slate-400 max-w-3xl mx-auto">
              Unsere KI-gestützte Plattform überprüft alle kritischen Compliance-Bereiche 
              und schützt Sie vor kostspieligen Abmahnungen.
            </p>
          </div>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {/* Legal Compliance */}
            <div className="bg-slate-800/50 backdrop-blur-md rounded-xl p-6 border border-slate-700 hover:scale-105 transition-transform">
              <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center mb-4">
                <FileText className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-xl font-semibold mb-3">Rechtliche Texte</h3>
              <p className="text-slate-400 mb-4">Impressum, Datenschutzerklärung, AGB - vollständig DSGVO-konform</p>
              <div className="text-sm text-red-400 font-medium">
                Risiko: 500-3.000€ pro Verstoß
              </div>
            </div>

            {/* Cookie Compliance */}
            <div className="bg-slate-800/50 backdrop-blur-md rounded-xl p-6 border border-slate-700 hover:scale-105 transition-transform">
              <div className="w-12 h-12 bg-gradient-to-r from-green-500 to-blue-600 rounded-lg flex items-center justify-center mb-4">
                <Cookie className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-xl font-semibold mb-3">Cookie-Compliance</h3>
              <p className="text-slate-400 mb-4">TTDSG-konforme Banner und Consent-Management</p>
              <div className="text-sm text-red-400 font-medium">
                Risiko: 1.000-5.000€ pro Fall
              </div>
            </div>

            {/* GDPR Compliance */}
            <div className="bg-slate-800/50 backdrop-blur-md rounded-xl p-6 border border-slate-700 hover:scale-105 transition-transform">
              <div className="w-12 h-12 bg-gradient-to-r from-purple-500 to-pink-600 rounded-lg flex items-center justify-center mb-4">
                <Shield className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-xl font-semibold mb-3">DSGVO-Compliance</h3>
              <p className="text-slate-400 mb-4">Vollständige Datenverarbeitungs-Analyse und Privacy-by-Design</p>
              <div className="text-sm text-red-400 font-medium">
                Risiko: 2.000-10.000€ + Bußgeld
              </div>
            </div>

            {/* Accessibility */}
            <div className="bg-slate-800/50 backdrop-blur-md rounded-xl p-6 border border-slate-700 hover:scale-105 transition-transform">
              <div className="w-12 h-12 bg-gradient-to-r from-orange-500 to-red-600 rounded-lg flex items-center justify-center mb-4">
                <Eye className="w-6 h-6 text-white" />
              </div>
              <h3 className="text-xl font-semibold mb-3">Barrierefreiheit</h3>
              <p className="text-slate-400 mb-4">WCAG 2.1 AA und BITV 2.0 Compliance für alle Nutzer</p>
              <div className="text-sm text-red-400 font-medium">
                Risiko: 500-2.000€ pro Mangel
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4 bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
              Transparent & Skalierbar
            </h2>
            <p className="text-xl text-slate-400">
              Wählen Sie die perfekte Lösung für Ihre Anforderungen
            </p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-8">
            {/* Free Analysis */}
            <div className="bg-slate-800/50 backdrop-blur-md rounded-xl p-8 border border-slate-700">
              <h3 className="text-2xl font-bold mb-4">Kostenlose Analyse</h3>
              <div className="text-4xl font-bold mb-6 bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                0€
              </div>
              <ul className="space-y-3 mb-8">
                <li className="flex items-center text-slate-300">
                  <Check className="w-5 h-5 text-green-500 mr-3" />
                  Vollständiger Compliance-Scan
                </li>
                <li className="flex items-center text-slate-300">
                  <Check className="w-5 h-5 text-green-500 mr-3" />
                  Abmahn-Risiko in €
                </li>
                <li className="flex items-center text-slate-300">
                  <Check className="w-5 h-5 text-green-500 mr-3" />
                  PDF-Report
                </li>
              </ul>
              <button 
                onClick={() => scrollToSection('demo')}
                className="w-full py-3 border border-slate-600 text-white rounded-lg hover:bg-slate-700 transition-colors"
              >
                Jetzt starten
              </button>
            </div>

            {/* AI Automation */}
            <div className="bg-slate-800/50 backdrop-blur-md rounded-xl p-8 border-2 border-blue-500 relative">
              <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                <span className="bg-blue-500 text-white px-4 py-1 rounded-full text-sm font-medium">
                  Empfohlen
                </span>
              </div>
              <h3 className="text-2xl font-bold mb-4">KI-Automatisierung</h3>
              <div className="text-4xl font-bold mb-2 bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                39€
              </div>
              <div className="text-slate-400 mb-6">pro Monat</div>
              <ul className="space-y-3 mb-8">
                <li className="flex items-center text-slate-300">
                  <Check className="w-5 h-5 text-green-500 mr-3" />
                  KI-gestützte Automatisierung
                </li>
                <li className="flex items-center text-slate-300">
                  <Check className="w-5 h-5 text-green-500 mr-3" />
                  Automatische Rechtstexte
                </li>
                <li className="flex items-center text-slate-300">
                  <Check className="w-5 h-5 text-green-500 mr-3" />
                  24h-Umsetzung
                </li>
                <li className="flex items-center text-slate-300">
                  <Check className="w-5 h-5 text-green-500 mr-3" />
                  Monatliche Re-Scans
                </li>
              </ul>
              <button 
                onClick={upgradeToPro}
                className="w-full py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg hover:opacity-90 transition-opacity"
              >
                Upgrade starten
              </button>
            </div>

            {/* Expert Service */}
            <div className="bg-slate-800/50 backdrop-blur-md rounded-xl p-8 border border-slate-700">
              <h3 className="text-2xl font-bold mb-4">Experten-Service</h3>
              <div className="text-4xl font-bold mb-2 bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                2.000€
              </div>
              <div className="text-slate-400 mb-6">einmalig + 39€/Monat</div>
              <ul className="space-y-3 mb-8">
                <li className="flex items-center text-slate-300">
                  <Check className="w-5 h-5 text-green-500 mr-3" />
                  Persönliche Experten-Betreuung
                </li>
                <li className="flex items-center text-slate-300">
                  <Check className="w-5 h-5 text-green-500 mr-3" />
                  Branchenspezifische Compliance
                </li>
                <li className="flex items-center text-slate-300">
                  <Check className="w-5 h-5 text-green-500 mr-3" />
                  Custom-Integration
                </li>
                <li className="flex items-center text-slate-300">
                  <Check className="w-5 h-5 text-green-500 mr-3" />
                  Direkte Experten-Hotline
                </li>
              </ul>
              <button 
                onClick={contactExpert}
                className="w-full py-3 border border-slate-600 text-white rounded-lg hover:bg-slate-700 transition-colors"
              >
                Experten kontaktieren
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto text-center">
          <div className="bg-gradient-to-r from-blue-500 to-purple-600 rounded-2xl p-8 text-white">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Schützen Sie sich noch heute vor Abmahnungen
            </h2>
            <p className="text-xl opacity-90 mb-8">
              Über 10.000 deutsche Websites vertrauen bereits auf Complyo. 
              Starten Sie jetzt Ihre kostenlose Analyse.
            </p>
            <button 
              onClick={() => scrollToSection('demo')}
              className="bg-white text-blue-600 px-8 py-4 rounded-lg font-semibold text-lg hover:bg-slate-100 transition-colors"
            >
              🚀 Kostenlose Analyse starten
            </button>
          </div>
        </div>
      </section>
      </main>

      {/* Footer */}
      <footer id="contact" className="bg-slate-800 py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-4 gap-8">
            <div className="col-span-2">
              <div className="flex items-center space-x-2 mb-4">
                <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                  <Check className="w-5 h-5 text-white" />
                </div>
                <span className="text-xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                  Complyo
                </span>
              </div>
              <p className="text-slate-400 mb-6 max-w-md">
                Die führende KI-gestützte Compliance-Plattform für deutsche Websites. 
                Automatischer Abmahnschutz und rechtssichere Umsetzung.
              </p>
            </div>
            
            <div>
              <h3 className="text-lg font-semibold mb-4">Produkt</h3>
              <ul className="space-y-2 text-slate-400">
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
                <li>
                  <a href="#" className="hover:text-white transition-colors">
                    API
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-white transition-colors">
                    Integrationen
                  </a>
                </li>
              </ul>
            </div>
            
            <div>
              <h3 className="text-lg font-semibold mb-4">Kontakt</h3>
              <ul className="space-y-2 text-slate-400">
                <li>
                  <a href="mailto:hello@complyo.tech" className="hover:text-white transition-colors">
                    hello@complyo.tech
                  </a>
                </li>
                <li>
                  <a href="tel:+4930123456789" className="hover:text-white transition-colors">
                    +49 30 123 456 789
                  </a>
                </li>
                <li>Berlin, Deutschland</li>
              </ul>
            </div>
          </div>
          
          <div className="border-t border-slate-700 mt-12 pt-8 flex flex-col md:flex-row justify-between items-center">
            <p className="text-slate-400 text-sm">
              © 2025 Complyo. Alle Rechte vorbehalten.
            </p>
            <div className="flex space-x-6 mt-4 md:mt-0">
              <a href="#" className="text-slate-400 hover:text-white text-sm transition-colors">
                Datenschutz
              </a>
              <a href="#" className="text-slate-400 hover:text-white text-sm transition-colors">
                Impressum
              </a>
              <a href="#" className="text-slate-400 hover:text-white text-sm transition-colors">
                AGB
              </a>
            </div>
          </div>
        </div>
      </footer>

      {/* Lead Generation Modal */}
      {showLeadForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-slate-800 rounded-2xl p-8 max-w-md w-full border border-slate-700">
            <div className="text-center mb-6">
              <h3 className="text-2xl font-bold mb-2">Vollständigen Report erhalten</h3>
              <p className="text-slate-400">
                Geben Sie Ihre Kontaktdaten ein, um den detaillierten Compliance-Report als PDF zu erhalten.
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
                  className="w-full px-4 py-3 rounded-lg bg-slate-700 border border-slate-600 text-white placeholder-slate-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
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
                  className="w-full px-4 py-3 rounded-lg bg-slate-700 border border-slate-600 text-white placeholder-slate-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
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
                  className="w-full px-4 py-3 rounded-lg bg-slate-700 border border-slate-600 text-white placeholder-slate-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              
              <div className="text-xs text-slate-400 bg-slate-700/50 p-3 rounded-lg">
                🔒 Ihre Daten werden vertraulich behandelt und nur für die Übersendung des Reports verwendet.
              </div>
              
              <div className="flex space-x-3 pt-4">
                <button
                  type="button"
                  onClick={closeLeadForm}
                  disabled={isGeneratingReport}
                  className="flex-1 px-4 py-3 border border-slate-600 text-slate-300 rounded-lg hover:bg-slate-700 transition-colors disabled:opacity-50"
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
                      Generiere...
                    </>
                  ) : (
                    '📧 Report senden'
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