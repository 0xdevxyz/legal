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
  ChevronRight
} from 'lucide-react';

// Modern Travel/Fintech Inspired Design System
const modernCSS = `
:root {
  /* Soft Color Palette - Travel Inspired */
  --complyo-primary: #4A90E2;
  --complyo-primary-light: #6BA3F0;
  --complyo-primary-dark: #357ABD;
  
  /* Accent Colors - Fintech Status */
  --complyo-success: #2ECC71;
  --complyo-success-light: #58D68D;
  --complyo-warning: #F39C12;
  --complyo-warning-light: #F8C471;
  --complyo-error: #E74C3C;
  --complyo-error-light: #EC7063;
  
  /* Soft Neutrals */
  --complyo-gray-900: #2C3E50;
  --complyo-gray-800: #34495E;
  --complyo-gray-700: #5D6D7E;
  --complyo-gray-600: #85929E;
  --complyo-gray-500: #AEB6BF;
  --complyo-gray-400: #D5DBDB;
  --complyo-gray-300: #EAEDED;
  --complyo-gray-200: #F4F6F6;
  --complyo-gray-100: #F8F9FA;
  --complyo-white: #FFFFFF;
  
  /* Mint/Teal Accents */
  --complyo-mint: #1ABC9C;
  --complyo-mint-light: #48C9B0;
  --complyo-mint-bg: #D5F4E6;
  
  /* Typography */
  --font-primary: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  --font-display: 'Poppins', sans-serif;
  
  /* Spacing - Generous */
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
  --space-20: 5rem;
  
  /* Modern Shadows */
  --shadow-soft: 0 2px 8px rgba(0, 0, 0, 0.04);
  --shadow-medium: 0 4px 16px rgba(0, 0, 0, 0.08);
  --shadow-strong: 0 8px 32px rgba(0, 0, 0, 0.12);
  --shadow-glow: 0 0 24px rgba(74, 144, 226, 0.15);
  
  /* Border Radius - Rounded */
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --radius-xl: 24px;
  --radius-full: 50%;
  
  /* Gradients */
  --gradient-primary: linear-gradient(135deg, #4A90E2 0%, #6BA3F0 100%);
  --gradient-success: linear-gradient(135deg, #2ECC71 0%, #58D68D 100%);
  --gradient-mint: linear-gradient(135deg, #1ABC9C 0%, #48C9B0 100%);
  --gradient-background: linear-gradient(135deg, #F8F9FA 0%, #EAEDED 100%);
}

.modern-dashboard {
  font-family: var(--font-primary);
  background: var(--gradient-background);
  min-height: 100vh;
  color: var(--complyo-gray-900);
}

/* Modern Card Styles */
.modern-card {
  background: var(--complyo-white);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-soft);
  border: 1px solid rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(20px);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}

.modern-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-strong);
}

.modern-card.featured {
  background: var(--gradient-primary);
  color: var(--complyo-white);
}

.modern-card.success {
  background: var(--gradient-success);
  color: var(--complyo-white);
}

.modern-card.mint {
  background: var(--gradient-mint);
  color: var(--complyo-white);
}

/* Hero Header */
.hero-header {
  background: var(--gradient-primary);
  color: var(--complyo-white);
  padding: var(--space-12) var(--space-6);
  border-radius: 0 0 var(--radius-xl) var(--radius-xl);
  position: relative;
  overflow: hidden;
}

.hero-header::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="20" r="2" fill="rgba(255,255,255,0.1)"/><circle cx="20" cy="60" r="1" fill="rgba(255,255,255,0.1)"/><circle cx="80" cy="70" r="1.5" fill="rgba(255,255,255,0.1)"/></svg>');
  opacity: 0.6;
}

/* Navigation */
.modern-nav {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid var(--complyo-gray-200);
  padding: var(--space-4) var(--space-6);
  position: sticky;
  top: 0;
  z-index: 100;
}

/* Compliance Score Widget - Speedometer Style */
.compliance-speedometer {
  position: relative;
  width: 200px;
  height: 120px;
  margin: 0 auto var(--space-6);
}

.speedometer-bg {
  width: 100%;
  height: 100%;
}

.score-display {
  position: absolute;
  bottom: var(--space-4);
  left: 50%;
  transform: translateX(-50%);
  text-align: center;
}

.score-number {
  font-size: 3rem;
  font-weight: 800;
  margin-bottom: var(--space-1);
}

.score-label {
  font-size: 0.875rem;
  opacity: 0.8;
}

/* Action Cards */
.action-card {
  padding: var(--space-6);
  border-radius: var(--radius-lg);
  background: var(--complyo-white);
  box-shadow: var(--shadow-soft);
  transition: all 0.3s ease;
  cursor: pointer;
  position: relative;
  overflow: hidden;
}

.action-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-medium);
}

.action-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
  background: var(--gradient-primary);
}

.action-card.mint::before {
  background: var(--gradient-mint);
}

.action-card.success::before {
  background: var(--gradient-success);
}

/* Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: var(--space-6);
  margin-bottom: var(--space-8);
}

.stat-card {
  background: var(--complyo-white);
  padding: var(--space-6);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-soft);
  text-align: center;
  transition: transform 0.3s ease;
}

.stat-card:hover {
  transform: scale(1.02);
}

.stat-icon {
  width: 48px;
  height: 48px;
  margin: 0 auto var(--space-4);
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
}

.stat-number {
  font-size: 2.5rem;
  font-weight: 800;
  margin-bottom: var(--space-1);
}

.stat-label {
  color: var(--complyo-gray-600);
  font-size: 0.875rem;
}

/* Journey Progress */
.journey-progress {
  background: var(--complyo-white);
  padding: var(--space-8);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-soft);
  position: relative;
}

.progress-visual {
  display: flex;
  align-items: center;
  margin-bottom: var(--space-6);
}

.progress-steps {
  display: flex;
  align-items: center;
  flex: 1;
  gap: var(--space-2);
}

.progress-step {
  width: 12px;
  height: 12px;
  border-radius: var(--radius-full);
  background: var(--complyo-gray-300);
  transition: all 0.3s ease;
}

.progress-step.completed {
  background: var(--complyo-success);
  transform: scale(1.2);
}

.progress-step.current {
  background: var(--complyo-primary);
  transform: scale(1.4);
  box-shadow: 0 0 12px rgba(74, 144, 226, 0.4);
}

/* Modern Buttons */
.btn-modern {
  background: var(--gradient-primary);
  color: var(--complyo-white);
  border: none;
  padding: var(--space-3) var(--space-6);
  border-radius: var(--radius-md);
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  cursor: pointer;
  transition: all 0.3s ease;
  font-family: var(--font-primary);
}

.btn-modern:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow-glow);
}

.btn-modern.mint {
  background: var(--gradient-mint);
}

.btn-modern.success {
  background: var(--gradient-success);
}

/* Activity Timeline */
.activity-timeline {
  background: var(--complyo-white);
  padding: var(--space-6);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-soft);
}

.timeline-item {
  display: flex;
  align-items: flex-start;
  gap: var(--space-4);
  padding: var(--space-4) 0;
  border-bottom: 1px solid var(--complyo-gray-200);
  position: relative;
}

.timeline-item:last-child {
  border-bottom: none;
}

.timeline-icon {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.timeline-icon.success {
  background: var(--complyo-mint-bg);
  color: var(--complyo-success);
}

.timeline-icon.warning {
  background: var(--complyo-warning-light);
  color: var(--complyo-warning);
}

/* Responsive Design */
@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .hero-header {
    padding: var(--space-8) var(--space-4);
  }
  
  .compliance-speedometer {
    width: 160px;
    height: 100px;
  }
  
  .score-number {
    font-size: 2rem;
  }
}
`;

// Compliance Score Speedometer Component
const ComplianceSpeedometer = ({ score = 85 }) => {
  const getScoreColor = (score) => {
    if (score >= 85) return '#2ECC71';
    if (score >= 70) return '#F39C12';
    return '#E74C3C';
  };

  const getScoreGradient = (score) => {
    if (score >= 85) return 'var(--gradient-success)';
    if (score >= 70) return 'linear-gradient(135deg, #F39C12 0%, #F8C471 100%)';
    return 'linear-gradient(135deg, #E74C3C 0%, #EC7063 100%)';
  };

  return (
    <div className="compliance-speedometer">
      <svg viewBox="0 0 200 120" className="speedometer-bg">
        {/* Background Arc */}
        <path
          d="M 20 100 A 80 80 0 0 1 180 100"
          fill="none"
          stroke="var(--complyo-gray-300)"
          strokeWidth="8"
          strokeLinecap="round"
        />
        
        {/* Progress Arc */}
        <path
          d="M 20 100 A 80 80 0 0 1 180 100"
          fill="none"
          stroke="url(#scoreGradient)"
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={`${(score / 100) * 251.3} 251.3`}
          style={{ transition: 'stroke-dasharray 1s ease' }}
        />
        
        {/* Gradient Definition */}
        <defs>
          <linearGradient id="scoreGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor={getScoreColor(score)} />
            <stop offset="100%" stopColor={getScoreColor(score)} stopOpacity="0.7" />
          </linearGradient>
        </defs>
        
        {/* Score Indicator */}
        <circle
          cx={20 + (160 * score / 100)}
          cy={100 - Math.sin(Math.PI * score / 100) * 80}
          r="6"
          fill={getScoreColor(score)}
          className="score-indicator"
        />
      </svg>
      
      <div className="score-display">
        <div className="score-number" style={{ color: getScoreColor(score) }}>
          {score}%
        </div>
        <div className="score-label">Compliance Score</div>
      </div>
    </div>
  );
};

// Modern Action Card Component
const ModernActionCard = ({ icon, title, description, color = 'primary', onClick }) => {
  return (
    <div className={`action-card ${color}`} onClick={onClick}>
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 'var(--space-4)' }}>
        <div className={`stat-icon`} style={{ 
          background: color === 'mint' ? 'var(--complyo-mint-bg)' : 
                      color === 'success' ? 'var(--complyo-success-light)' : 
                      'var(--complyo-primary-light)',
          color: color === 'mint' ? 'var(--complyo-mint)' : 
                 color === 'success' ? 'var(--complyo-success)' : 
                 'var(--complyo-primary)'
        }}>
          {icon}
        </div>
        <div style={{ flex: 1 }}>
          <h4 style={{ 
            margin: '0 0 var(--space-2) 0', 
            color: 'var(--complyo-gray-900)',
            fontWeight: '600'
          }}>
            {title}
          </h4>
          <p style={{ 
            margin: 0, 
            color: 'var(--complyo-gray-600)',
            fontSize: '0.875rem',
            lineHeight: '1.4'
          }}>
            {description}
          </p>
        </div>
        <ChevronRight 
          style={{ 
            width: '20px', 
            height: '20px', 
            color: 'var(--complyo-gray-400)',
            transition: 'transform 0.3s ease'
          }} 
        />
      </div>
    </div>
  );
};

// Main Dashboard Component
export default function ModernComplexDashboard() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [user] = useState({ name: 'Max Mustermann', plan: 'Business' });
  const [complianceScore] = useState(85);

  // Inject modern CSS
  useEffect(() => {
    const styleElement = document.createElement('style');
    styleElement.textContent = modernCSS;
    document.head.appendChild(styleElement);
    
    return () => {
      const styles = document.querySelectorAll('style');
      styles.forEach(style => {
        if (style.textContent.includes('--complyo-primary: #4A90E2')) {
          style.remove();
        }
      });
    };
  }, []);

  return (
    <div className="modern-dashboard">
      {/* Modern Navigation */}
      <nav className="modern-nav">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', maxWidth: '1400px', margin: '0 auto' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-8)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
              <Shield style={{ width: '32px', height: '32px', color: 'var(--complyo-primary)' }} />
              <span style={{ 
                fontSize: '1.5rem', 
                fontWeight: '800', 
                background: 'var(--gradient-primary)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                fontFamily: 'var(--font-display)'
              }}>
                Complyo
              </span>
            </div>
            
            <div style={{ display: 'flex', gap: 'var(--space-6)' }}>
              {[
                { key: 'dashboard', label: 'Overview', icon: BarChart3 },
                { key: 'scanner', label: 'Scanner', icon: Search },
                { key: 'journey', label: 'Journey', icon: Target },
                { key: 'reports', label: 'Reports', icon: FileText },
                { key: 'settings', label: 'Settings', icon: Settings }
              ].map(({ key, label, icon: Icon }) => (
                <button
                  key={key}
                  onClick={() => setActiveTab(key)}
                  style={{
                    background: activeTab === key ? 'var(--complyo-primary)' : 'transparent',
                    color: activeTab === key ? 'var(--complyo-white)' : 'var(--complyo-gray-600)',
                    border: 'none',
                    padding: 'var(--space-2) var(--space-4)',
                    borderRadius: 'var(--radius-md)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 'var(--space-2)',
                    cursor: 'pointer',
                    transition: 'all 0.3s ease',
                    fontSize: '0.875rem',
                    fontWeight: '500'
                  }}
                >
                  <Icon style={{ width: '16px', height: '16px' }} />
                  {label}
                </button>
              ))}
            </div>
          </div>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-4)' }}>
            <button style={{
              background: 'none',
              border: 'none',
              padding: 'var(--space-2)',
              borderRadius: 'var(--radius-md)',
              cursor: 'pointer',
              color: 'var(--complyo-gray-600)'
            }}>
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
                <User style={{ width: '20px', height: '20px', color: 'var(--complyo-white)' }} />
              </div>
              <div>
                <div style={{ fontWeight: '600', fontSize: '0.875rem' }}>{user.name}</div>
                <div style={{ fontSize: '0.75rem', color: 'var(--complyo-gray-500)' }}>{user.plan} Plan</div>
              </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Header */}
      <div className="hero-header">
        <div style={{ maxWidth: '1400px', margin: '0 auto', position: 'relative', zIndex: 1 }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-12)', alignItems: 'center' }}>
            <div>
              <h1 style={{ 
                fontSize: '2.5rem', 
                fontWeight: '800', 
                marginBottom: 'var(--space-4)',
                fontFamily: 'var(--font-display)'
              }}>
                Willkommen zurück, Max! 👋
              </h1>
              <p style={{ fontSize: '1.125rem', opacity: '0.9', marginBottom: 'var(--space-6)' }}>
                Ihr Compliance-Status im Überblick. Aktueller Plan: <strong>{user.plan}</strong>
              </p>
              
              <div style={{ display: 'flex', gap: 'var(--space-4)', marginBottom: 'var(--space-6)' }}>
                <div style={{ 
                  background: 'rgba(255, 255, 255, 0.2)', 
                  backdropFilter: 'blur(10px)',
                  padding: 'var(--space-3) var(--space-4)',
                  borderRadius: 'var(--radius-md)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 'var(--space-2)'
                }}>
                  <Globe style={{ width: '16px', height: '16px' }} />
                  <span style={{ fontSize: '0.875rem' }}>3 Websites</span>
                </div>
                <div style={{ 
                  background: 'rgba(255, 255, 255, 0.2)', 
                  backdropFilter: 'blur(10px)',
                  padding: 'var(--space-3) var(--space-4)',
                  borderRadius: 'var(--radius-md)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 'var(--space-2)'
                }}>
                  <CheckCircle style={{ width: '16px', height: '16px' }} />
                  <span style={{ fontSize: '0.875rem' }}>27 Issues Fixed</span>
                </div>
              </div>
              
              <button className="btn-modern" style={{ fontSize: '1rem', padding: 'var(--space-4) var(--space-8)' }}>
                <Search style={{ width: '20px', height: '20px' }} />
                Neue Website scannen
              </button>
            </div>
            
            <div style={{ textAlign: 'center' }}>
              <ComplianceSpeedometer score={complianceScore} />
              <div style={{ marginTop: 'var(--space-4)' }}>
                <div style={{ display: 'flex', justifyContent: 'center', gap: 'var(--space-6)', fontSize: '0.875rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                    <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--complyo-success)' }}></div>
                    <span>DSGVO: Compliant</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                    <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--complyo-warning)' }}></div>
                    <span>TTDSG: 3 Issues</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                    <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--complyo-success)' }}></div>
                    <span>Accessibility: Good</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div style={{ maxWidth: '1400px', margin: '0 auto', padding: 'var(--space-8) var(--space-6)' }}>
        
        {/* Stats Grid */}
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-icon" style={{ background: 'var(--complyo-mint-bg)', color: 'var(--complyo-mint)' }}>
              <Globe />
            </div>
            <div className="stat-number" style={{ color: 'var(--complyo-mint)' }}>3</div>
            <div className="stat-label">Active Websites</div>
          </div>
          
          <div className="stat-card">
            <div className="stat-icon" style={{ background: 'var(--complyo-success-light)', color: 'var(--complyo-success)' }}>
              <TrendingUp />
            </div>
            <div className="stat-number" style={{ color: 'var(--complyo-success)' }}>85%</div>
            <div className="stat-label">Avg. Compliance</div>
          </div>
          
          <div className="stat-card">
            <div className="stat-icon" style={{ background: 'var(--complyo-warning-light)', color: 'var(--complyo-warning)' }}>
              <AlertTriangle />
            </div>
            <div className="stat-number" style={{ color: 'var(--complyo-warning)' }}>3</div>
            <div className="stat-label">Issues to Fix</div>
          </div>
          
          <div className="stat-card">
            <div className="stat-icon" style={{ background: 'var(--complyo-primary-light)', color: 'var(--complyo-primary)' }}>
              <Activity />
            </div>
            <div className="stat-number" style={{ color: 'var(--complyo-primary)' }}>1</div>
            <div className="stat-label">Active Scans</div>
          </div>
        </div>

        {/* Main Dashboard Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-8)', marginBottom: 'var(--space-8)' }}>
          
          {/* Quick Actions */}
          <div>
            <h3 style={{ marginBottom: 'var(--space-6)', fontWeight: '600', color: 'var(--complyo-gray-900)' }}>
              Quick Actions
            </h3>
            <div style={{ display: 'grid', gap: 'var(--space-4)' }}>
              <ModernActionCard
                icon={<Search />}
                title="Website Scanner"
                description="Scan your website for compliance issues in under 60 seconds"
                color="primary"
                onClick={() => setActiveTab('scanner')}
              />
              <ModernActionCard
                icon={<Target />}
                title="Continue Journey"
                description="Step 3 of 13: Configure Cookie Banner"
                color="mint"
                onClick={() => setActiveTab('journey')}
              />
              <ModernActionCard
                icon={<FileText />}
                title="Generate Report"
                description="Download compliance certificate and detailed report"
                color="success"
                onClick={() => setActiveTab('reports')}
              />
            </div>
          </div>

          {/* Recent Activity */}
          <div className="activity-timeline">
            <h3 style={{ marginBottom: 'var(--space-6)', fontWeight: '600', color: 'var(--complyo-gray-900)' }}>
              Recent Activity
            </h3>
            
            <div className="timeline-item">
              <div className="timeline-icon success">
                <CheckCircle style={{ width: '20px', height: '20px' }} />
              </div>
              <div>
                <h4 style={{ margin: '0 0 var(--space-1) 0', fontSize: '0.875rem', fontWeight: '600' }}>
                  DSGVO Scan Completed
                </h4>
                <p style={{ margin: 0, fontSize: '0.75rem', color: 'var(--complyo-gray-600)' }}>
                  example.com - Score: 85% • 2 hours ago
                </p>
              </div>
            </div>
            
            <div className="timeline-item">
              <div className="timeline-icon warning">
                <AlertTriangle style={{ width: '20px', height: '20px' }} />
              </div>
              <div>
                <h4 style={{ margin: '0 0 var(--space-1) 0', fontSize: '0.875rem', fontWeight: '600' }}>
                  Cookie Banner Issues Found
                </h4>
                <p style={{ margin: 0, fontSize: '0.75rem', color: 'var(--complyo-gray-600)' }}>
                  shop.example.com - 3 issues detected • 1 day ago
                </p>
              </div>
            </div>
            
            <div className="timeline-item">
              <div className="timeline-icon success">
                <Award style={{ width: '20px', height: '20px' }} />
              </div>
              <div>
                <h4 style={{ margin: '0 0 var(--space-1) 0', fontSize: '0.875rem', fontWeight: '600' }}>
                  Compliance Certificate Generated
                </h4>
                <p style={{ margin: 0, fontSize: '0.75rem', color: 'var(--complyo-gray-600)' }}>
                  blog.example.com - Ready for download • 3 days ago
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Journey Progress */}
        <div className="journey-progress">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-6)' }}>
            <h3 style={{ margin: 0, fontWeight: '600', color: 'var(--complyo-gray-900)' }}>
              Compliance Journey Progress
            </h3>
            <span style={{ fontSize: '0.875rem', color: 'var(--complyo-gray-600)' }}>
              Step 3 of 13 • 60% Complete
            </span>
          </div>
          
          <div className="progress-visual">
            <div className="progress-steps">
              {Array.from({ length: 13 }, (_, i) => (
                <div 
                  key={i}
                  className={`progress-step ${
                    i < 3 ? 'completed' : i === 3 ? 'current' : ''
                  }`}
                />
              ))}
            </div>
          </div>
          
          <div style={{ 
            background: 'var(--complyo-mint-bg)', 
            padding: 'var(--space-4)', 
            borderRadius: 'var(--radius-md)',
            marginBottom: 'var(--space-6)'
          }}>
            <h4 style={{ margin: '0 0 var(--space-2) 0', color: 'var(--complyo-mint)', fontWeight: '600' }}>
              Next Step: Configure Cookie Banner
            </h4>
            <p style={{ margin: 0, fontSize: '0.875rem', color: 'var(--complyo-gray-700)' }}>
              Set up TTDSG-compliant cookie consent for your website visitors
            </p>
          </div>
          
          <div style={{ display: 'flex', gap: 'var(--space-3)' }}>
            <button className="btn-modern mint">
              <Play style={{ width: '16px', height: '16px' }} />
              Continue Journey
            </button>
            <button className="btn-modern" style={{ background: 'var(--complyo-gray-200)', color: 'var(--complyo-gray-700)' }}>
              <Eye style={{ width: '16px', height: '16px' }} />
              View All Steps
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}