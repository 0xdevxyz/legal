import React, { useState, useEffect } from 'react';
import { Search, Shield, AlertTriangle, CheckCircle, FileText, PieChart, Globe, BarChart2, Clock, Download, Plus, Calculator, Zap, Euro } from 'lucide-react';
import RiskCalculator from './components/RiskCalculator';
import AIFixer from './components/AIFixer';

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

export default function EnhancedDashboard() {
  const [loading, setLoading] = useState(true);
  const [scanResults, setScanResults] = useState([]);
  const [reports, setReports] = useState([]);
  const [statistics, setStatistics] = useState({
    totalScans: 0,
    averageScore: 0,
    totalRiskEuro: 0,
    issuesByCategory: {}
  });
  const [newScanUrl, setNewScanUrl] = useState('');
  const [isScanning, setIsScanning] = useState(false);
  const [user, setUser] = useState(null);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [selectedScan, setSelectedScan] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        
        // Fetch user profile
        const userProfile = await fetchWithAuth(`${API_URL}/api/users/me`);
        setUser(userProfile);
        
        // Fetch scan results
        const results = await fetchWithAuth(`${API_URL}/api/scans`);
        setScanResults(results);
        
        // Calculate enhanced statistics
        if (results.length > 0) {
          const totalScans = results.length;
          const totalScore = results.reduce((sum, scan) => sum + scan.overall_score, 0);
          const averageScore = Math.round(totalScore / totalScans);
          const totalRiskEuro = results.reduce((sum, scan) => sum + (scan.total_risk_euro || 0), 0);
          
          // Count issues by category
          const issuesByCategory = {};
          results.forEach(scan => {
            if (typeof scan.results === 'string') {
              scan.results = JSON.parse(scan.results);
            }
            
            scan.results.forEach(result => {
              const category = result.category;
              if (!issuesByCategory[category]) {
                issuesByCategory[category] = { fail: 0, warning: 0, pass: 0, totalRisk: 0 };
              }
              issuesByCategory[category][result.status]++;
              issuesByCategory[category].totalRisk += result.risk_euro || 0;
            });
          });
          
          setStatistics({
            totalScans,
            averageScore,
            totalRiskEuro,
            issuesByCategory
          });
        }
        
        setLoading(false);
      } catch (error) {
        console.error('Error fetching data:', error);
        setLoading(false);
      }
    };
    
    fetchData();
  }, []);
  
  const handleScanSubmit = async (e) => {
    e.preventDefault();
    
    if (!newScanUrl) return;
    
    try {
      setIsScanning(true);
      
      // Validate URL
      let url = newScanUrl;
      if (!url.startsWith('http://') && !url.startsWith('https://')) {
        url = `https://${url}`;
      }
      
      // Perform scan
      const scanResult = await fetchWithAuth(`${API_URL}/api/analyze`, {
        method: 'POST',
        body: JSON.stringify({ url })
      });
      
      // Update scan results
      setScanResults([scanResult, ...scanResults]);
      
      // Update statistics
      setStatistics(prev => ({
        totalScans: prev.totalScans + 1,
        averageScore: Math.round((prev.averageScore * prev.totalScans + scanResult.overall_score) / (prev.totalScans + 1)),
        totalRiskEuro: prev.totalRiskEuro + (scanResult.total_risk_euro || 0),
        issuesByCategory: { ...prev.issuesByCategory }
      }));
      
      setNewScanUrl('');
      setIsScanning(false);
      
    } catch (error) {
      console.error('Scan error:', error);
      setIsScanning(false);
    }
  };
  
  const generateReport = async (scanId) => {
    try {
      const report = await fetchWithAuth(`${API_URL}/api/reports/generate`, {
        method: 'POST',
        body: JSON.stringify({ scan_id: scanId, include_details: true })
      });
      
      // Add to reports list
      setReports([report, ...reports]);
      
      // Open report in new tab
      if (report.url) {
        window.open(report.url, '_blank');
      }
      
    } catch (error) {
      console.error('Report generation error:', error);
    }
  };

  const getRiskLevelColor = (riskEuro) => {
    if (riskEuro >= 10000) return 'text-red-600';
    if (riskEuro >= 5000) return 'text-orange-600';
    if (riskEuro >= 2000) return 'text-yellow-600';
    return 'text-green-600';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-indigo-500"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <div className="bg-gray-800 shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <Shield className="h-8 w-8 text-indigo-500" />
              <h1 className="ml-3 text-xl font-bold">Complyo Dashboard</h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-300">
                {user?.subscription_tier === 'expert' ? '👨‍💼 Expert' : 
                 user?.subscription_tier === 'basic' ? '🤖 KI-Automation' : '🆓 Free'}
              </span>
              <span className="text-sm font-medium">{user?.email}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex space-x-8">
            {['dashboard', 'scans', 'risk-calculator', 'ai-fixer', 'reports'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab
                    ? 'border-indigo-500 text-indigo-400'
                    : 'border-transparent text-gray-300 hover:text-white hover:border-gray-300'
                }`}
              >
                {tab === 'dashboard' && 'Übersicht'}
                {tab === 'scans' && 'Website Scans'}
                {tab === 'risk-calculator' && 'Risiko-Rechner'}
                {tab === 'ai-fixer' && 'KI-Automation'}
                {tab === 'reports' && 'Reports'}
              </button>
            ))}
          </nav>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Dashboard Overview */}
        {activeTab === 'dashboard' && (
          <>
            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
              <div className="bg-gray-800 rounded-lg p-6">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <BarChart2 className="h-8 w-8 text-indigo-500" />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-300 truncate">
                        Durchschnittlicher Score
                      </dt>
                      <dd className="text-lg font-semibold text-white">
                        {statistics.averageScore}%
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>

              <div className="bg-gray-800 rounded-lg p-6">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <Globe className="h-8 w-8 text-green-500" />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-300 truncate">
                        Websites gescannt
                      </dt>
                      <dd className="text-lg font-semibold text-white">
                        {statistics.totalScans}
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>

              <div className="bg-gray-800 rounded-lg p-6">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <Euro className={`h-8 w-8 ${getRiskLevelColor(statistics.totalRiskEuro)}`} />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-300 truncate">
                        Gesamtrisiko
                      </dt>
                      <dd className={`text-lg font-semibold ${getRiskLevelColor(statistics.totalRiskEuro)}`}>
                        {statistics.totalRiskEuro.toLocaleString()} €
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>

              <div className="bg-gray-800 rounded-lg p-6">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <FileText className="h-8 w-8 text-purple-500" />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-300 truncate">
                        Reports erstellt
                      </dt>
                      <dd className="text-lg font-semibold text-white">
                        {reports.length}
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>

            {/* New Scan Form */}
            <div className="bg-gray-800 rounded-lg p-6 mb-8">
              <h3 className="text-lg font-medium mb-4">Neue Website scannen</h3>
              <form onSubmit={handleScanSubmit} className="flex gap-4">
                <input
                  type="url"
                  placeholder="https://example.com"
                  value={newScanUrl}
                  onChange={(e) => setNewScanUrl(e.target.value)}
                  className="flex-1 bg-gray-700 border border-gray-600 rounded-md px-3 py-2 text-white placeholder-gray-400"
                />
                <button
                  type="submit"
                  disabled={isScanning || !newScanUrl}
                  className="bg-indigo-600 text-white px-6 py-2 rounded-md hover:bg-indigo-700 disabled:opacity-50 flex items-center gap-2"
                >
                  {isScanning ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
                      Scannen...
                    </>
                  ) : (
                    <>
                      <Search className="w-4 h-4" />
                      Compliance scannen
                    </>
                  )}
                </button>
              </form>
            </div>

            {/* Recent Scans */}
            <div className="bg-gray-800 rounded-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium">Letzte Scans</h3>
                <button
                  onClick={() => setActiveTab('scans')}
                  className="text-indigo-400 hover:text-indigo-300 text-sm"
                >
                  Alle anzeigen →
                </button>
              </div>
              {scanResults.length === 0 ? (
                <div className="text-center py-8 text-gray-400">
                  <Globe className="h-12 w-12 mx-auto mb-4 text-gray-600" />
                  <p>Noch keine Scans durchgeführt</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {scanResults.slice(0, 3).map((scan) => (
                    <div key={scan.id} className="flex items-center justify-between bg-gray-700 p-4 rounded-lg">
                      <div className="flex items-center gap-4">
                        <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
                          scan.overall_score > 80 ? 'bg-green-600' : 
                          scan.overall_score > 50 ? 'bg-yellow-600' : 'bg-red-600'
                        }`}>
                          <span className="font-bold">{scan.overall_score}%</span>
                        </div>
                        <div>
                          <div className="font-medium">{scan.url}</div>
                          <div className="text-sm text-gray-400">
                            {scan.total_issues} Probleme • 
                            {scan.total_risk_euro ? ` ${scan.total_risk_euro.toLocaleString()} € Risiko` : ''} •
                            {new Date(scan.scan_timestamp).toLocaleDateString()}
                          </div>
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <button
                          onClick={() => {
                            setSelectedScan(scan);
                            setActiveTab('risk-calculator');
                          }}
                          className="text-yellow-400 hover:text-yellow-300 text-sm"
                        >
                          <Calculator className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => {
                            setSelectedScan(scan);
                            setActiveTab('ai-fixer');
                          }}
                          className="text-blue-400 hover:text-blue-300 text-sm"
                        >
                          <Zap className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </>
        )}

        {/* Scans Tab */}
        {activeTab === 'scans' && (
          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-lg font-medium mb-4">Alle Website-Scans</h3>
            {scanResults.length === 0 ? (
              <div className="text-center py-8 text-gray-400">
                <Globe className="h-12 w-12 mx-auto mb-4 text-gray-600" />
                <p>Keine Scans vorhanden</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-700">
                  <thead>
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase">Website</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase">Score</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase">Risiko</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase">Probleme</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase">Datum</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase">Aktionen</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-700">
                    {scanResults.map((scan) => (
                      <tr key={scan.id} className="hover:bg-gray-700">
                        <td className="px-6 py-4">
                          <div className="text-sm font-medium text-white truncate max-w-xs">
                            {scan.url}
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <div className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                            scan.overall_score > 80 ? 'bg-green-600 text-green-100' : 
                            scan.overall_score > 50 ? 'bg-yellow-600 text-yellow-100' : 'bg-red-600 text-red-100'
                          }`}>
                            {scan.overall_score}%
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <div className={`text-sm font-medium ${getRiskLevelColor(scan.total_risk_euro || 0)}`}>
                            {scan.total_risk_euro ? `${scan.total_risk_euro.toLocaleString()} €` : '-'}
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-2">
                            <span className="text-red-400">{scan.critical_issues || 0} kritisch</span>
                            <span className="text-yellow-400">{scan.warning_issues || 0} Warnungen</span>
                          </div>
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-300">
                          {new Date(scan.scan_timestamp).toLocaleDateString()}
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex gap-2">
                            <button
                              onClick={() => {
                                setSelectedScan(scan);
                                setActiveTab('risk-calculator');
                              }}
                              className="text-yellow-400 hover:text-yellow-300"
                            >
                              <Calculator className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => {
                                setSelectedScan(scan);
                                setActiveTab('ai-fixer');
                              }}
                              className="text-blue-400 hover:text-blue-300"
                            >
                              <Zap className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => generateReport(scan.id)}
                              className="text-purple-400 hover:text-purple-300"
                            >
                              <FileText className="w-4 h-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Risk Calculator Tab */}
        {activeTab === 'risk-calculator' && (
          <div>
            <div className="mb-6">
              <h2 className="text-2xl font-bold text-white mb-2">Abmahn-Risiko-Kalkulator</h2>
              <p className="text-gray-400">
                Berechnen Sie das konkrete Abmahnrisiko Ihrer Website in Euro
              </p>
            </div>
            {selectedScan ? (
              <RiskCalculator 
                scanResult={selectedScan}
                onRiskCalculated={(result) => console.log('Risk calculated:', result)}
              />
            ) : (
              <div className="bg-gray-800 rounded-lg p-6">
                <div className="text-center py-8 text-gray-400">
                  <Calculator className="h-12 w-12 mx-auto mb-4 text-gray-600" />
                  <p>Wählen Sie einen Scan aus, um das Risiko zu berechnen</p>
                  <button
                    onClick={() => setActiveTab('scans')}
                    className="mt-4 text-indigo-400 hover:text-indigo-300"
                  >
                    Zu den Scans →
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* AI Fixer Tab */}
        {activeTab === 'ai-fixer' && (
          <div>
            <div className="mb-6">
              <h2 className="text-2xl font-bold text-white mb-2">KI-Automatisierung</h2>
              <p className="text-gray-400">
                Automatische Generierung von Compliance-Lösungen mit KI
              </p>
            </div>
            {selectedScan ? (
              <AIFixer 
                scanResult={selectedScan}
                onFixGenerated={(result) => console.log('Fix generated:', result)}
              />
            ) : (
              <div className="bg-gray-800 rounded-lg p-6">
                <div className="text-center py-8 text-gray-400">
                  <Zap className="h-12 w-12 mx-auto mb-4 text-gray-600" />
                  <p>Wählen Sie einen Scan aus, um Fixes zu generieren</p>
                  <button
                    onClick={() => setActiveTab('scans')}
                    className="mt-4 text-indigo-400 hover:text-indigo-300"
                  >
                    Zu den Scans →
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Reports Tab */}
        {activeTab === 'reports' && (
          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-lg font-medium mb-4">Compliance Reports</h3>
            {reports.length === 0 ? (
              <div className="text-center py-8 text-gray-400">
                <FileText className="h-12 w-12 mx-auto mb-4 text-gray-600" />
                <p>Keine Reports vorhanden</p>
              </div>
            ) : (
              <div className="space-y-4">
                {reports.map((report) => (
                  <div key={report.id} className="flex items-center justify-between bg-gray-700 p-4 rounded-lg">
                    <div>
                      <div className="font-medium">{report.title}</div>
                      <div className="text-sm text-gray-400">
                        {new Date(report.created_at).toLocaleDateString()}
                      </div>
                    </div>
                    <button
                      onClick={() => window.open(report.url, '_blank')}
                      className="text-indigo-400 hover:text-indigo-300 flex items-center gap-2"
                    >
                      <Download className="w-4 h-4" />
                      Download
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}