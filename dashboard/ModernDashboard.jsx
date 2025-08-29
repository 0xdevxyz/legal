import React, { useState, useEffect } from 'react';
import { 
  Home, 
  Shield, 
  Search, 
  FileText, 
  Settings, 
  CreditCard,
  ChevronRight,
  AlertTriangle,
  CheckCircle,
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
  X
} from 'lucide-react';

// Design System CSS Variables (Import this at the top of your app)
const designSystemCSS = `
:root {
  /* Primary Colors */
  --complyo-blue-900: #0F172A;
  --complyo-blue-800: #1E293B;
  --complyo-blue-700: #334155;
  --complyo-blue-600: #475569;
  --complyo-blue-500: #64748B;
  
  /* Accent Colors */
  --complyo-accent-600: #2563EB;
  --complyo-accent-500: #3B82F6;
  --complyo-accent-400: #60A5FA;
  --complyo-accent-100: #DBEAFE;
  
  /* Status Colors */
  --complyo-success-600: #059669;
  --complyo-success-500: #10B981;
  --complyo-success-100: #D1FAE5;
  
  --complyo-warning-600: #D97706;
  --complyo-warning-500: #F59E0B;
  --complyo-warning-100: #FEF3C7;
  
  --complyo-error-600: #DC2626;
  --complyo-error-500: #EF4444;
  --complyo-error-100: #FEE2E2;
  
  /* Neutrals */
  --complyo-gray-900: #111827;
  --complyo-gray-800: #1F2937;
  --complyo-gray-700: #374151;
  --complyo-gray-600: #4B5563;
  --complyo-gray-500: #6B7280;
  --complyo-gray-400: #9CA3AF;
  --complyo-gray-300: #D1D5DB;
  --complyo-gray-200: #E5E7EB;
  --complyo-gray-100: #F3F4F6;
  --complyo-gray-50: #F9FAFB;
  --complyo-white: #FFFFFF;
  
  /* Typography */
  --font-primary: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  --font-display: 'Cal Sans', 'Inter', sans-serif;
  
  /* Spacing */
  --space-4: 1rem;
  --space-6: 1.5rem;
  --space-8: 2rem;
  --space-12: 3rem;
  --space-16: 4rem;
  
  /* Shadows */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.07);
  --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);
  
  /* Transitions */
  --transition-fast: 150ms ease;
  --transition-base: 200ms ease;
}

.btn-primary {
  background: var(--complyo-accent-600);
  color: var(--complyo-white);
  padding: 0.75rem 1.5rem;
  border-radius: 0.5rem;
  font-weight: 600;
  font-size: 1rem;
  transition: var(--transition-base);
  box-shadow: var(--shadow-sm);
  border: none;
  cursor: pointer;
  font-family: var(--font-primary);
}

.btn-primary:hover {
  background: var(--complyo-accent-700);
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}

.btn-secondary {
  background: transparent;
  color: var(--complyo-accent-600);
  border: 1px solid var(--complyo-accent-600);
  padding: 0.75rem 1.5rem;
  border-radius: 0.5rem;
  font-weight: 600;
  transition: var(--transition-base);
  cursor: pointer;
  font-family: var(--font-primary);
}

.btn-secondary:hover {
  background: var(--complyo-accent-50);
}

.card {
  background: var(--complyo-white);
  border-radius: 0.75rem;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--complyo-gray-200);
  padding: 1.5rem;
  transition: var(--transition-base);
}

.card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}

.form-input {
  width: 100%;
  padding: 0.75rem 1rem;
  border: 1px solid var(--complyo-gray-300);
  border-radius: 0.5rem;
  font-size: 1rem;
  transition: var(--transition-base);
  font-family: var(--font-primary);
}

.form-input:focus {
  border-color: var(--complyo-accent-500);
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
  outline: none;
}
`;

// API service
const API_URL = 'https://api.complyo.tech';

const fetchWithAuth = async (url, options = {}) => {
  const token = localStorage.getItem('auth_token');
  const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`,
    ...options.headers
  };
  
  const response = await fetch(url, {
    ...options,
    headers
  });
  
  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }
  
  return response.json();
};

// Compliance Score Component
const ComplianceScoreWidget = ({ score, breakdown }) => {
  const getScoreColor = (score) => {
    if (score >= 85) return 'text-green-600';
    if (score >= 70) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreRing = (score) => {
    const percentage = (score / 100) * 283;
    return `stroke-dasharray: ${percentage} 283; stroke-dashoffset: 0;`;
  };

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">🛡️ Compliance Score</h3>
        <Shield className="w-5 h-5 text-blue-600" />
      </div>
      
      <div className="flex items-center justify-center mb-6">
        <div className="relative w-32 h-32">
          <svg className="w-32 h-32 transform -rotate-90">
            <circle
              cx="64"
              cy="64"
              r="45"
              stroke="currentColor"
              strokeWidth="8"
              fill="transparent"
              className="text-gray-200"
            />
            <circle
              cx="64"
              cy="64"
              r="45"
              stroke="currentColor"
              strokeWidth="8"
              fill="transparent"
              className={getScoreColor(score)}
              style={{ strokeDasharray: `${(score / 100) * 283} 283` }}
            />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center">
              <div className={`text-3xl font-bold ${getScoreColor(score)}`}>{score}%</div>
              <div className="text-sm text-gray-500">Score</div>
            </div>
          </div>
        </div>
      </div>
      
      <div className="space-y-2">
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-600">✅ DSGVO</span>
          <span className="text-sm font-semibold text-green-600">Compliant</span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-600">⚠️ TTDSG</span>
          <span className="text-sm font-semibold text-yellow-600">3 Issues</span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-600">✅ Accessibility</span>
          <span className="text-sm font-semibold text-green-600">Good</span>
        </div>
      </div>
    </div>
  );
};

// Quick Actions Component
const QuickActionsPanel = ({ onStartScan, onViewReports, onStartJourney }) => {
  return (
    <div className="card">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
      <div className="space-y-3">
        <button 
          onClick={onStartScan}
          className="w-full flex items-center justify-between p-3 bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors group"
        >
          <div className="flex items-center space-x-3">
            <Search className="w-5 h-5 text-blue-600" />
            <span className="font-medium text-blue-700">Scan Website</span>
          </div>
          <ChevronRight className="w-4 h-4 text-blue-600 group-hover:translate-x-1 transition-transform" />
        </button>
        
        <button 
          onClick={onViewReports}
          className="w-full flex items-center justify-between p-3 bg-green-50 hover:bg-green-100 rounded-lg transition-colors group"
        >
          <div className="flex items-center space-x-3">
            <FileText className="w-5 h-5 text-green-600" />
            <span className="font-medium text-green-700">View Report</span>
          </div>
          <ChevronRight className="w-4 h-4 text-green-600 group-hover:translate-x-1 transition-transform" />
        </button>
        
        <button 
          onClick={onStartJourney}
          className="w-full flex items-center justify-between p-3 bg-purple-50 hover:bg-purple-100 rounded-lg transition-colors group"
        >
          <div className="flex items-center space-x-3">
            <Activity className="w-5 h-5 text-purple-600" />
            <span className="font-medium text-purple-700">Start Journey</span>
          </div>
          <ChevronRight className="w-4 h-4 text-purple-600 group-hover:translate-x-1 transition-transform" />
        </button>
        
        <button className="w-full flex items-center justify-between p-3 bg-orange-50 hover:bg-orange-100 rounded-lg transition-colors group">
          <div className="flex items-center space-x-3">
            <CreditCard className="w-5 h-5 text-orange-600" />
            <span className="font-medium text-orange-700">Upgrade Plan</span>
          </div>
          <ChevronRight className="w-4 h-4 text-orange-600 group-hover:translate-x-1 transition-transform" />
        </button>
      </div>
    </div>
  );
};

// Journey Progress Component
const JourneyProgress = ({ currentStep = 3, totalSteps = 13, stepName = "Website Setup", nextAction = "Configure Cookie Banner" }) => {
  const progressPercentage = (currentStep / totalSteps) * 100;
  
  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">📋 Current Journey</h3>
        <Activity className="w-5 h-5 text-blue-600" />
      </div>
      
      <div className="mb-4">
        <div className="flex justify-between text-sm text-gray-600 mb-2">
          <span>Step {currentStep} of {totalSteps}: {stepName}</span>
          <span>{Math.round(progressPercentage)}%</span>
        </div>
        
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div 
            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${progressPercentage}%` }}
          ></div>
        </div>
      </div>
      
      <div className="bg-blue-50 p-3 rounded-lg mb-4">
        <p className="text-sm text-blue-700 mb-2">Next: {nextAction}</p>
      </div>
      
      <button className="btn-primary w-full">
        Continue Journey →
      </button>
    </div>
  );
};

// Stats Grid Component
const StatsGrid = ({ stats }) => {
  const statCards = [
    {
      title: 'Total Websites',
      value: stats.totalWebsites || 0,
      icon: Globe,
      color: 'blue'
    },
    {
      title: 'Avg. Compliance Score',
      value: `${stats.averageScore || 0}%`,
      icon: TrendingUp,
      color: 'green'
    },
    {
      title: 'Issues Resolved',
      value: stats.issuesResolved || 0,
      icon: CheckCircle,
      color: 'green'
    },
    {
      title: 'Active Scans',
      value: stats.activeScans || 0,
      icon: Activity,
      color: 'purple'
    }
  ];
  
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      {statCards.map((stat, index) => (
        <div key={index} className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">{stat.title}</p>
              <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
            </div>
            <stat.icon className={`w-8 h-8 text-${stat.color}-600`} />
          </div>
        </div>
      ))}
    </div>
  );
};

// Recent Scans Component
const RecentScans = ({ scans, onGenerateReport }) => {
  const getStatusBadge = (score) => {
    if (score >= 85) return 'bg-green-100 text-green-800';
    if (score >= 70) return 'bg-yellow-100 text-yellow-800';
    return 'bg-red-100 text-red-800';
  };

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Recent Scans</h3>
        <button className="text-blue-600 hover:text-blue-800 text-sm font-medium">
          View All →
        </button>
      </div>
      
      <div className="space-y-4">
        {scans.slice(0, 5).map((scan, index) => (
          <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <div className="flex items-center space-x-3">
              <Globe className="w-5 h-5 text-gray-400" />
              <div>
                <p className="font-medium text-gray-900">{scan.url || 'example.com'}</p>
                <p className="text-sm text-gray-500">{scan.created_at ? new Date(scan.created_at).toLocaleDateString() : 'Today'}</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-2">
              <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusBadge(scan.overall_score || 75)}`}>
                {scan.overall_score || 75}%
              </span>
              <button 
                onClick={() => onGenerateReport(scan.id)}
                className="p-1 text-gray-400 hover:text-blue-600"
              >
                <Download className="w-4 h-4" />
              </button>
            </div>
          </div>
        ))}
      </div>
      
      <button className="w-full mt-4 btn-secondary">
        <Search className="w-4 h-4 mr-2" />
        Start New Scan
      </button>
    </div>
  );
};

// Main Dashboard Component
export default function ModernDashboard() {
  const [loading, setLoading] = useState(true);
  const [scanResults, setScanResults] = useState([]);
  const [reports, setReports] = useState([]);
  const [statistics, setStatistics] = useState({
    totalWebsites: 0,
    averageScore: 0,
    issuesResolved: 0,
    activeScans: 0,
    issuesByCategory: {}
  });
  const [user, setUser] = useState(null);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [newScanUrl, setNewScanUrl] = useState('');
  const [isScanning, setIsScanning] = useState(false);

  // Navigation items
  const navigation = [
    { name: 'Dashboard', icon: Home, key: 'dashboard' },
    { name: 'Website Scanner', icon: Search, key: 'scanner' },
    { name: 'Journey Progress', icon: Activity, key: 'journey' },
    { name: 'Reports & Certificates', icon: FileText, key: 'reports' },
    { name: 'Settings & Profile', icon: Settings, key: 'settings' },
    { name: 'Subscription & Billing', icon: CreditCard, key: 'billing' },
  ];

  useEffect(() => {
    // Inject design system CSS
    const styleElement = document.createElement('style');
    styleElement.textContent = designSystemCSS;
    document.head.appendChild(styleElement);
    
    const fetchData = async () => {
      try {
        setLoading(true);
        
        // Mock data for demo purposes
        setUser({ name: 'Max Mustermann', email: 'max@example.com', plan: 'Business' });
        
        const mockScans = [
          { id: 1, url: 'example.com', overall_score: 85, created_at: new Date().toISOString() },
          { id: 2, url: 'shop.example.com', overall_score: 72, created_at: new Date().toISOString() },
          { id: 3, url: 'blog.example.com', overall_score: 91, created_at: new Date().toISOString() }
        ];
        
        setScanResults(mockScans);
        
        setStatistics({
          totalWebsites: 3,
          averageScore: 83,
          issuesResolved: 27,
          activeScans: 1,
          issuesByCategory: {}
        });
        
        setLoading(false);
      } catch (error) {
        console.error('Error fetching data:', error);
        setLoading(false);
      }
    };
    
    fetchData();
    
    // Cleanup
    return () => {
      const styles = document.querySelectorAll('style');
      styles.forEach(style => {
        if (style.textContent.includes('--complyo-blue-900')) {
          style.remove();
        }
      });
    };
  }, []);

  const handleStartScan = () => {
    setActiveTab('scanner');
  };

  const handleViewReports = () => {
    setActiveTab('reports');
  };

  const handleStartJourney = () => {
    setActiveTab('journey');
  };

  const handleGenerateReport = async (scanId) => {
    try {
      console.log('Generating report for scan:', scanId);
      // Implement report generation logic
    } catch (error) {
      console.error('Error generating report:', error);
    }
  };

  const handleScanSubmit = async (e) => {
    e.preventDefault();
    if (!newScanUrl) return;
    
    setIsScanning(true);
    // Simulate scan
    setTimeout(() => {
      const newScan = {
        id: scanResults.length + 1,
        url: newScanUrl,
        overall_score: Math.floor(Math.random() * 40) + 60,
        created_at: new Date().toISOString()
      };
      setScanResults([newScan, ...scanResults]);
      setNewScanUrl('');
      setIsScanning(false);
    }, 2000);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen" style={{ backgroundColor: 'var(--complyo-gray-50)' }}>
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 mx-auto" style={{ borderColor: 'var(--complyo-accent-600)' }}></div>
          <p className="mt-4" style={{ color: 'var(--complyo-gray-600)' }}>Lade Dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen" style={{ backgroundColor: 'var(--complyo-gray-50)', fontFamily: 'var(--font-primary)' }}>
      {/* Header */}
      <nav className="border-b" style={{ backgroundColor: 'var(--complyo-white)', borderColor: 'var(--complyo-gray-200)' }}>
        <div className="mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <span className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 text-transparent bg-clip-text" style={{ fontFamily: 'var(--font-display)' }}>
                  Complyo
                </span>
              </div>
              
              {/* Desktop Navigation */}
              <div className="hidden md:block ml-10">
                <div className="flex items-baseline space-x-4">
                  {navigation.map((item) => (
                    <button
                      key={item.key}
                      onClick={() => setActiveTab(item.key)}
                      className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                        activeTab === item.key
                          ? 'text-blue-600 bg-blue-50'
                          : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                      }`}
                    >
                      <item.icon className="w-4 h-4 inline-block mr-2" />
                      {item.name}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* User Menu */}
            <div className="flex items-center space-x-4">
              <button className="p-2 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100">
                <Bell className="w-5 h-5" />
              </button>
              <div className="flex items-center space-x-2">
                <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                  <User className="w-4 h-4 text-white" />
                </div>
                <span className="text-sm font-medium text-gray-700">{user?.name || 'User'}</span>
              </div>
              
              {/* Mobile menu button */}
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="md:hidden p-2 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100"
              >
                {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="mx-auto px-4 sm:px-6 lg:px-8 py-8 max-w-7xl">
        {activeTab === 'dashboard' && (
          <>
            {/* Welcome Section */}
            <div className="mb-8">
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                Willkommen zurück, {user?.name?.split(' ')[0] || 'User'}! 👋
              </h1>
              <p className="text-gray-600">
                Hier ist Ihr Compliance-Overview. Aktueller Plan: <span className="font-semibold text-blue-600">{user?.plan || 'Business'}</span>
              </p>
            </div>

            {/* Stats Grid */}
            <StatsGrid stats={statistics} />

            {/* Main Dashboard Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              {/* Left Column */}
              <div className="lg:col-span-1 space-y-6">
                <ComplianceScoreWidget score={statistics.averageScore} />
                <QuickActionsPanel 
                  onStartScan={handleStartScan}
                  onViewReports={handleViewReports}
                  onStartJourney={handleStartJourney}
                />
              </div>

              {/* Middle Column */}
              <div className="lg:col-span-1 space-y-6">
                <JourneyProgress />
                <RecentScans scans={scanResults} onGenerateReport={handleGenerateReport} />
              </div>

              {/* Right Column */}
              <div className="lg:col-span-1 space-y-6">
                {/* Activity Feed */}
                <div className="card">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h3>
                  <div className="space-y-3">
                    <div className="flex items-center space-x-3">
                      <CheckCircle className="w-5 h-5 text-green-600" />
                      <div>
                        <p className="text-sm font-medium text-gray-900">DSGVO Scan completed</p>
                        <p className="text-xs text-gray-500">2 hours ago</p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-3">
                      <AlertTriangle className="w-5 h-5 text-yellow-600" />
                      <div>
                        <p className="text-sm font-medium text-gray-900">3 issues found in TTDSG</p>
                        <p className="text-xs text-gray-500">1 day ago</p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-3">
                      <FileText className="w-5 h-5 text-blue-600" />
                      <div>
                        <p className="text-sm font-medium text-gray-900">Compliance report generated</p>
                        <p className="text-xs text-gray-500">3 days ago</p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Next Steps */}
                <div className="card">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Recommended Actions</h3>
                  <div className="space-y-3">
                    <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                      <p className="text-sm font-medium text-yellow-800">Fix Cookie Banner</p>
                      <p className="text-xs text-yellow-600">Update your cookie consent mechanism</p>
                    </div>
                    <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                      <p className="text-sm font-medium text-blue-800">Schedule Regular Scans</p>
                      <p className="text-xs text-blue-600">Set up automated monthly compliance checks</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </>
        )}

        {activeTab === 'scanner' && (
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-8">Website Scanner</h1>
            
            {/* Scan Form */}
            <div className="card mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Neue Website scannen</h2>
              <form onSubmit={handleScanSubmit} className="flex gap-4">
                <input
                  type="url"
                  value={newScanUrl}
                  onChange={(e) => setNewScanUrl(e.target.value)}
                  placeholder="https://example.com"
                  className="form-input flex-1"
                  disabled={isScanning}
                />
                <button
                  type="submit"
                  disabled={isScanning || !newScanUrl}
                  className="btn-primary"
                >
                  {isScanning ? (
                    <>
                      <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                      Scanning...
                    </>
                  ) : (
                    <>
                      <Search className="w-4 h-4 mr-2" />
                      Scannen
                    </>
                  )}
                </button>
              </form>
            </div>

            {/* Scan Results */}
            <RecentScans scans={scanResults} onGenerateReport={handleGenerateReport} />
          </div>
        )}

        {/* Add other tab content as needed */}
        {activeTab !== 'dashboard' && activeTab !== 'scanner' && (
          <div className="text-center py-12">
            <h1 className="text-2xl font-bold text-gray-900 mb-4">
              {navigation.find(nav => nav.key === activeTab)?.name}
            </h1>
            <p className="text-gray-600">Dieser Bereich wird bald verfügbar sein.</p>
          </div>
        )}
      </main>
    </div>
  );
}