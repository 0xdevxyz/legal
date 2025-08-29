import React, { useState, useEffect } from 'react';
import { 
  Shield, 
  Search, 
  FileText, 
  Settings, 
  CreditCard,
  TrendingUp,
  Activity,
  Globe,
  Users,
  BarChart3,
  Download,
  RefreshCw,
  Bell,
  User,
  Menu,
  X,
  CheckCircle,
  AlertTriangle,
  Clock,
  Zap,
  Target,
  Award,
  Eye,
  ArrowRight,
  Play,
  ChevronRight,
  Sun,
  Moon
} from 'lucide-react';

// Accurate Color System with Dark/Light Mode
const accurateDesignSystem = `
:root {
  /* Light Mode Colors */
  --primary: #4A90E2;
  --primary-light: #6BA3F0;
  --primary-dark: #357ABD;
  
  /* Accurate Score Colors - Credit Score Style */
  --score-excellent: #2ECC71;    /* 85-100% */
  --score-good: #27AE60;         /* 70-84% */
  --score-fair: #F39C12;         /* 55-69% */
  --score-poor: #E67E22;         /* 40-54% */
  --score-very-poor: #E74C3C;    /* 0-39% */
  
  /* Status Colors */
  --success: #2ECC71;
  --success-light: #58D68D;
  --success-bg: #D5F4E6;
  
  --warning: #F39C12;
  --warning-light: #F8C471;
  --warning-bg: #FEF9E7;
  
  --error: #E74C3C;
  --error-light: #EC7063;
  --error-bg: #FDEDEC;
  
  --info: #3498DB;
  --info-light: #5DADE2;
  --info-bg: #EBF5FB;
  
  /* Light Mode Neutrals */
  --bg-primary: #FFFFFF;
  --bg-secondary: #F8F9FA;
  --bg-tertiary: #F4F6F8;
  
  --text-primary: #2C3E50;
  --text-secondary: #5D6D7E;
  --text-tertiary: #85929E;
  --text-muted: #BDC3C7;
  
  --border-light: #E8ECEF;
  --border-medium: #D5DBDB;
  --border-dark: #AEB6BF;
  
  /* Mint Accent */
  --mint: #1ABC9C;
  --mint-light: #48C9B0;
  --mint-bg: #D5F4E6;
  
  /* Typography */
  --font-primary: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  --font-display: 'Poppins', sans-serif;
  
  /* Spacing */
  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-3: 0.75rem;
  --space-4: 1rem;
  --space-5: 1.25rem;
  --space-6: 1.5rem;
  --space-8: 2rem;
  --space-10: 2.5rem;
  --space-12: 3rem;
  --space-16: 4rem;
  
  /* Shadows */
  --shadow-soft: 0 2px 8px rgba(0, 0, 0, 0.06);
  --shadow-medium: 0 4px 16px rgba(0, 0, 0, 0.1);
  --shadow-strong: 0 8px 32px rgba(0, 0, 0, 0.15);
  
  /* Border Radius */
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --radius-xl: 24px;
  --radius-full: 50%;
  
  /* Gradients */
  --gradient-primary: linear-gradient(135deg, var(--primary) 0%, var(--primary-light) 100%);
  --gradient-success: linear-gradient(135deg, var(--success) 0%, var(--success-light) 100%);
  --gradient-mint: linear-gradient(135deg, var(--mint) 0%, var(--mint-light) 100%);
}

/* Dark Mode Colors */
[data-theme="dark"] {
  /* Dark Mode Backgrounds */
  --bg-primary: #1A1D29;
  --bg-secondary: #252A3A;
  --bg-tertiary: #2A2F42;
  
  /* Dark Mode Text */
  --text-primary: #FFFFFF;
  --text-secondary: #B8BCC8;
  --text-tertiary: #9CA3AF;
  --text-muted: #6B7280;
  
  /* Dark Mode Borders */
  --border-light: #374151;
  --border-medium: #4B5563;
  --border-dark: #6B7280;
  
  /* Adjusted Status Colors for Dark Mode */
  --success-bg: rgba(46, 204, 113, 0.15);
  --warning-bg: rgba(243, 156, 18, 0.15);
  --error-bg: rgba(231, 76, 60, 0.15);
  --info-bg: rgba(52, 152, 219, 0.15);
  --mint-bg: rgba(26, 188, 156, 0.15);
  
  /* Dark Mode Shadows */
  --shadow-soft: 0 2px 8px rgba(0, 0, 0, 0.3);
  --shadow-medium: 0 4px 16px rgba(0, 0, 0, 0.4);
  --shadow-strong: 0 8px 32px rgba(0, 0, 0, 0.5);
}

/* Base Styles */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: var(--font-primary);
  background: var(--bg-secondary);
  color: var(--text-primary);
  transition: background-color 0.3s ease, color 0.3s ease;
}

/* Accurate Dashboard Styles */
.accurate-dashboard {
  min-height: 100vh;
  background: var(--bg-secondary);
  transition: all 0.3s ease;
}

/* Navigation */
.accurate-nav {
  background: var(--bg-primary);
  border-bottom: 1px solid var(--border-light);
  padding: var(--space-4) var(--space-6);
  position: sticky;
  top: 0;
  z-index: 100;
  backdrop-filter: blur(20px);
}

.nav-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  max-width: 1400px;
  margin: 0 auto;
}

.nav-left {
  display: flex;
  align-items: center;
  gap: var(--space-8);
}

.logo {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.logo-text {
  font-size: 1.5rem;
  font-weight: 800;
  background: var(--gradient-primary);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-family: var(--font-display);
}

.nav-tabs {
  display: flex;
  gap: var(--space-6);
}

.nav-tab {
  background: none;
  border: none;
  padding: var(--space-2) var(--space-4);
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  gap: var(--space-2);
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-secondary);
}

.nav-tab.active {
  background: var(--primary);
  color: var(--bg-primary);
}

.nav-tab:hover:not(.active) {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

.nav-right {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

.theme-toggle {
  background: var(--bg-tertiary);
  border: 1px solid var(--border-medium);
  padding: var(--space-2);
  border-radius: var(--radius-md);
  cursor: pointer;
  color: var(--text-secondary);
  transition: all 0.3s ease;
}

.theme-toggle:hover {
  background: var(--bg-secondary);
  color: var(--text-primary);
}

/* Accurate Compliance Score Component */
.accurate-score-widget {
  background: var(--bg-primary);
  padding: var(--space-8);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-medium);
  text-align: center;
  position: relative;
}

.score-container {
  position: relative;
  width: 280px;
  height: 140px;
  margin: 0 auto var(--space-6);
}

.score-svg {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}

.score-display-center {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  margin-top: var(--space-4);
}

.score-number {
  font-size: 3.5rem;
  font-weight: 800;
  margin-bottom: var(--space-1);
  font-family: var(--font-display);
}

.score-label {
  font-size: 1rem;
  color: var(--text-secondary);
  font-weight: 500;
}

.score-details {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-4);
  margin-top: var(--space-6);
}

.score-item {
  text-align: center;
  padding: var(--space-3);
  border-radius: var(--radius-md);
  background: var(--bg-secondary);
}

.score-item-value {
  font-size: 1.125rem;
  font-weight: 700;
  margin-bottom: var(--space-1);
}

.score-item-label {
  font-size: 0.75rem;
  color: var(--text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* Stats Cards */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: var(--space-6);
  margin-bottom: var(--space-8);
}

.stat-card {
  background: var(--bg-primary);
  padding: var(--space-6);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-soft);
  display: flex;
  align-items: center;
  justify-content: space-between;
  transition: all 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-medium);
}

.stat-info h4 {
  font-size: 0.875rem;
  color: var(--text-secondary);
  margin-bottom: var(--space-2);
  font-weight: 500;
}

.stat-info .stat-number {
  font-size: 2rem;
  font-weight: 800;
  color: var(--text-primary);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Dark Mode Specific Adjustments */
[data-theme="dark"] .accurate-score-widget,
[data-theme="dark"] .stat-card {
  border: 1px solid var(--border-light);
}

[data-theme="dark"] .nav-tab.active {
  color: var(--text-primary);
}

/* Responsive Design */
@media (max-width: 768px) {
  .nav-tabs {
    display: none;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .score-container {
    width: 220px;
    height: 110px;
  }
  
  .score-number {
    font-size: 2.5rem;
  }
  
  .score-details {
    grid-template-columns: 1fr;
  }
}
`;

// Accurate Score Color Function
const getAccurateScoreColor = (score) => {
  if (score >= 85) return '#2ECC71';      // Excellent - Green
  if (score >= 70) return '#27AE60';      // Good - Dark Green  
  if (score >= 55) return '#F39C12';      // Fair - Orange
  if (score >= 40) return '#E67E22';      // Poor - Dark Orange
  return '#E74C3C';                       // Very Poor - Red
};

// Accurate Score Gradient Function
const getAccurateScoreGradient = (score) => {
  // Create smooth gradient based on score ranges
  if (score >= 85) {
    return `conic-gradient(from 0deg, #E74C3C 0deg, #E67E22 ${36 * 0.4}deg, #F39C12 ${36 * 0.55}deg, #27AE60 ${36 * 0.7}deg, #2ECC71 ${36 * score / 100 * 1.8}deg, #E5E7EB ${36 * score / 100 * 1.8}deg)`;
  } else if (score >= 70) {
    return `conic-gradient(from 0deg, #E74C3C 0deg, #E67E22 ${36 * 0.4}deg, #F39C12 ${36 * 0.55}deg, #27AE60 ${36 * score / 100 * 1.8}deg, #E5E7EB ${36 * score / 100 * 1.8}deg)`;
  } else if (score >= 55) {
    return `conic-gradient(from 0deg, #E74C3C 0deg, #E67E22 ${36 * 0.4}deg, #F39C12 ${36 * score / 100 * 1.8}deg, #E5E7EB ${36 * score / 100 * 1.8}deg)`;
  } else if (score >= 40) {
    return `conic-gradient(from 0deg, #E74C3C 0deg, #E67E22 ${36 * score / 100 * 1.8}deg, #E5E7EB ${36 * score / 100 * 1.8}deg)`;
  } else {
    return `conic-gradient(from 0deg, #E74C3C ${36 * score / 100 * 1.8}deg, #E5E7EB ${36 * score / 100 * 1.8}deg)`;
  }
};

// Accurate Compliance Score Component
const AccurateComplianceScore = ({ score = 85, breakdown = { dsgvo: 90, ttdsg: 75, accessibility: 85 } }) => {
  const scoreColor = getAccurateScoreColor(score);
  
  // Accurate arc calculation for semicircle (180 degrees)
  const circumference = Math.PI * 90; // radius 45, semicircle
  const scorePercentage = Math.min(Math.max(score, 0), 100);
  const arcLength = (scorePercentage / 100) * circumference;
  
  return (
    <div className="accurate-score-widget">
      <h3 style={{ marginBottom: 'var(--space-6)', fontWeight: '600' }}>
        🛡️ Compliance Score
      </h3>
      
      <div className="score-container">
        <svg viewBox="0 0 200 120" className="score-svg">
          {/* Background Arc - Accurate semicircle */}
          <path
            d="M 20 100 A 80 80 0 0 1 180 100"
            fill="none"
            stroke="var(--border-medium)"
            strokeWidth="12"
            strokeLinecap="round"
          />
          
          {/* Score Arc - Accurate positioning */}
          <path
            d="M 20 100 A 80 80 0 0 1 180 100"
            fill="none"
            stroke={scoreColor}
            strokeWidth="12"
            strokeLinecap="round"
            strokeDasharray={`${arcLength} ${circumference}`}
            style={{ 
              transition: 'stroke-dasharray 1.5s cubic-bezier(0.4, 0, 0.2, 1)',
              filter: 'drop-shadow(0 0 8px rgba(74, 144, 226, 0.3))'
            }}
          />
          
          {/* Score Indicator Dot - Accurate position calculation */}
          <circle
            cx={100 + 80 * Math.cos(Math.PI - (scorePercentage / 100) * Math.PI)}
            cy={100 - 80 * Math.sin(Math.PI - (scorePercentage / 100) * Math.PI)}
            r="8"
            fill={scoreColor}
            style={{ 
              filter: 'drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2))',
              transition: 'all 1.5s cubic-bezier(0.4, 0, 0.2, 1)'
            }}
          />
        </svg>
        
        <div className="score-display-center">
          <div className="score-number" style={{ color: scoreColor }}>
            {score}%
          </div>
          <div className="score-label">Compliance Score</div>
        </div>
      </div>
      
      <div className="score-details">
        <div className="score-item">
          <div 
            className="score-item-value" 
            style={{ color: getAccurateScoreColor(breakdown.dsgvo) }}
          >
            {breakdown.dsgvo}%
          </div>
          <div className="score-item-label">DSGVO</div>
        </div>
        
        <div className="score-item">
          <div 
            className="score-item-value" 
            style={{ color: getAccurateScoreColor(breakdown.ttdsg) }}
          >
            {breakdown.ttdsg}%
          </div>
          <div className="score-item-label">TTDSG</div>
        </div>
        
        <div className="score-item">
          <div 
            className="score-item-value" 
            style={{ color: getAccurateScoreColor(breakdown.accessibility) }}
          >
            {breakdown.accessibility}%
          </div>
          <div className="score-item-label">Accessibility</div>
        </div>
      </div>
    </div>
  );
};

// Main Dashboard Component
export default function AccurateDashboard() {
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [complianceScore] = useState(85);
  const [complianceBreakdown] = useState({
    dsgvo: 90,
    ttdsg: 75,
    accessibility: 88
  });

  // Theme Management
  useEffect(() => {
    const savedTheme = localStorage.getItem('complyo-theme');
    if (savedTheme) {
      setIsDarkMode(savedTheme === 'dark');
    }
  }, []);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', isDarkMode ? 'dark' : 'light');
    localStorage.setItem('complyo-theme', isDarkMode ? 'dark' : 'light');
  }, [isDarkMode]);

  // Inject CSS
  useEffect(() => {
    const styleElement = document.createElement('style');
    styleElement.textContent = accurateDesignSystem;
    document.head.appendChild(styleElement);
    
    return () => {
      const styles = document.querySelectorAll('style');
      styles.forEach(style => {
        if (style.textContent.includes('--primary: #4A90E2')) {
          style.remove();
        }
      });
    };
  }, []);

  const toggleTheme = () => {
    setIsDarkMode(!isDarkMode);
  };

  const statsData = [
    {
      title: 'Gesamt-Score',
      value: complianceScore,
      suffix: '%',
      icon: TrendingUp,
      color: getAccurateScoreColor(complianceScore),
      trend: '+2.3% diese Woche'
    },
    {
      title: 'Websites',
      value: 3,
      suffix: '',
      icon: Globe,
      color: 'var(--primary)',
      trend: '3 aktive Scans'
    },
    {
      title: 'Kritische Issues',
      value: 2,
      suffix: '',
      icon: AlertTriangle,
      color: 'var(--warning)',
      trend: 'Sofortige Beachtung'
    },
    {
      title: 'Scans verfügbar',
      value: 47,
      suffix: '/100',
      icon: BarChart3,
      color: 'var(--info)',
      trend: '0% genutzt'
    }
  ];

  return (
    <div className="accurate-dashboard">
      {/* Navigation */}
      <nav className="accurate-nav">
        <div className="nav-content">
          <div className="nav-left">
            <div className="logo">
              <Shield style={{ width: '32px', height: '32px', color: 'var(--primary)' }} />
              <span className="logo-text">Complyo</span>
            </div>
            
            <div className="nav-tabs">
              {[
                { key: 'dashboard', label: 'Dashboard', icon: BarChart3 },
                { key: 'scanner', label: 'Website-Scanner', icon: Search },
                { key: 'journey', label: 'Journey', icon: Target },
                { key: 'reports', label: 'Berichte', icon: FileText },
                { key: 'settings', label: 'Einstellungen', icon: Settings }
              ].map(({ key, label, icon: Icon }) => (
                <button
                  key={key}
                  onClick={() => setActiveTab(key)}
                  className={`nav-tab ${activeTab === key ? 'active' : ''}`}
                >
                  <Icon style={{ width: '16px', height: '16px' }} />
                  {label}
                </button>
              ))}
            </div>
          </div>
          
          <div className="nav-right">
            <button className="theme-toggle" onClick={toggleTheme}>
              {isDarkMode ? <Sun style={{ width: '20px', height: '20px' }} /> : <Moon style={{ width: '20px', height: '20px' }} />}
            </button>
            
            <button style={{ background: 'none', border: 'none', padding: 'var(--space-2)', cursor: 'pointer', color: 'var(--text-secondary)' }}>
              <Bell style={{ width: '20px', height: '20px' }} />
            </button>
            
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
              <div style={{
                width: '36px',
                height: '36px',
                borderRadius: 'var(--radius-full)',
                background: 'var(--gradient-primary)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <User style={{ width: '20px', height: '20px', color: 'var(--bg-primary)' }} />
              </div>
              <div>
                <div style={{ fontWeight: '600', fontSize: '0.875rem' }}>Max Mustermann</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)' }}>Business Plan</div>
              </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div style={{ maxWidth: '1400px', margin: '0 auto', padding: 'var(--space-8) var(--space-6)' }}>
        
        {/* Stats Grid */}
        <div className="stats-grid">
          {statsData.map((stat, index) => (
            <div key={index} className="stat-card">
              <div className="stat-info">
                <h4>{stat.title}</h4>
                <div className="stat-number" style={{ color: stat.color }}>
                  {stat.value}{stat.suffix}
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-tertiary)', marginTop: 'var(--space-1)' }}>
                  {stat.trend}
                </div>
              </div>
              <div className="stat-icon" style={{ background: `${stat.color}20`, color: stat.color }}>
                <stat.icon />
              </div>
            </div>
          ))}
        </div>

        {/* Main Dashboard Content */}
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 3fr', gap: 'var(--space-8)', alignItems: 'start' }}>
          
          {/* Compliance Score Widget */}
          <AccurateComplianceScore 
            score={complianceScore} 
            breakdown={complianceBreakdown}
          />
          
          {/* Additional Content Area */}
          <div style={{ 
            background: 'var(--bg-primary)', 
            padding: 'var(--space-8)', 
            borderRadius: 'var(--radius-lg)', 
            boxShadow: 'var(--shadow-medium)',
            border: isDarkMode ? '1px solid var(--border-light)' : 'none'
          }}>
            <h3 style={{ marginBottom: 'var(--space-6)', fontWeight: '600' }}>
              Rechtliche Neuigkeiten
            </h3>
            
            {/* News Items */}
            {[
              {
                type: 'critical',
                title: 'TTDSG Änderung: Neue Cookie-Richtlinien',
                description: 'Seit 1. August 2025 gelten verschärfte Regeln für Cookie-Banner. Ihre Website ist betroffen.',
                timeAgo: 'vor etwa 2 Stunden',
                source: 'Quelle: BMJ'
              },
              {
                type: 'info',
                title: 'DSGVO: Neue Mustervorlagen verfügbar',
                description: 'Aktualisierte Datenschutzerklärung-Templates für 2025 sind verfügbar.',
                timeAgo: 'vor 1 Tag',
                source: 'Quelle: Datenschutzkonferenz'
              },
              {
                type: 'tip',
                title: 'Barrierefreiheit: WCAG 2.2 Update',
                description: 'Neue Accessibility Standards können Ihre Website-Bewertung verbessern.',
                timeAgo: 'vor 5 Tagen',
                source: 'Quelle: W3C'
              }
            ].map((news, index) => (
              <div key={index} style={{
                padding: 'var(--space-4)',
                borderRadius: 'var(--radius-md)',
                marginBottom: 'var(--space-4)',
                background: news.type === 'critical' ? 'var(--error-bg)' :
                           news.type === 'info' ? 'var(--info-bg)' : 'var(--success-bg)',
                borderLeft: `4px solid ${
                  news.type === 'critical' ? 'var(--error)' :
                  news.type === 'info' ? 'var(--info)' : 'var(--success)'
                }`
              }}>
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: 'var(--space-3)' }}>
                  <div style={{
                    padding: 'var(--space-2)',
                    borderRadius: 'var(--radius-md)',
                    background: news.type === 'critical' ? 'var(--error)' :
                               news.type === 'info' ? 'var(--info)' : 'var(--success)',
                    color: 'var(--bg-primary)'
                  }}>
                    {news.type === 'critical' ? '⚠️' : news.type === 'info' ? 'ℹ️' : '💡'}
                  </div>
                  <div style={{ flex: 1 }}>
                    <h4 style={{ 
                      margin: '0 0 var(--space-2) 0',
                      fontSize: '0.875rem',
                      fontWeight: '600',
                      color: news.type === 'critical' ? 'var(--error)' :
                             news.type === 'info' ? 'var(--info)' : 'var(--success)'
                    }}>
                      {news.title}
                    </h4>
                    <p style={{
                      margin: '0 0 var(--space-2) 0',
                      fontSize: '0.8rem',
                      color: 'var(--text-secondary)',
                      lineHeight: '1.4'
                    }}>
                      {news.description}
                    </p>
                    <div style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      fontSize: '0.75rem',
                      color: 'var(--text-tertiary)'
                    }}>
                      <span>{news.timeAgo}</span>
                      <span>{news.source}</span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}