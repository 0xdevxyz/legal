import React, { useState, useEffect } from 'react';
import { Search, Shield, AlertTriangle, CheckCircle, FileText, PieChart, Globe, BarChart2, Clock, Download, Plus } from 'lucide-react';

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

export default function Dashboard() {
  const [loading, setLoading] = useState(true);
  const [scanResults, setScanResults] = useState([]);
  const [reports, setReports] = useState([]);
  const [statistics, setStatistics] = useState({
    totalScans: 0,
    averageScore: 0,
    issuesByCategory: {}
  });
  const [newScanUrl, setNewScanUrl] = useState('');
  const [isScanning, setIsScanning] = useState(false);
  const [user, setUser] = useState(null);
  const [activeTab, setActiveTab] = useState('dashboard');

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        
        // Fetch user profile
        const userProfile = await fetchWithAuth(`${API_URL}/api/users/me`);
        setUser(userProfile);
        
        // Fetch scan results
        const results = await fetchWithAuth(`${API_URL}/api/scans/list`);
        setScanResults(results);
        
        // Fetch reports
        const reportsList = await fetchWithAuth(`${API_URL}/api/reports/list`);
        setReports(reportsList);
        
        // Calculate statistics
        if (results.length > 0) {
          const totalScans = results.length;
          const totalScore = results.reduce((sum, scan) => sum + scan.overall_score, 0);
          const averageScore = Math.round(totalScore / totalScans);
          
          // Count issues by category
          const issuesByCategory = {};
          results.forEach(scan => {
            if (typeof scan.results === 'string') {
              scan.results = JSON.parse(scan.results);
            }
            
            scan.results.forEach(result => {
              const category = result.category;
              if (!issuesByCategory[category]) {
                issuesByCategory[category] = { fail: 0, warning: 0, pass: 0 };
              }
              issuesByCategory[category][result.status]++;
            });
          });
          
          setStatistics({
            totalScans,
            averageScore,
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
      if (!newScanUrl.startsWith('http://') && !newScanUrl.startsWith('https://')) {
        setNewScanUrl(`https://${newScanUrl}`);
      }
      
      // Perform scan
      const scanResult = await fetchWithAuth(`${API_URL}/api/analyze`, {
        method: 'POST',
        body: JSON.stringify({ url: newScanUrl })
      });
      
      // Update scan results
      setScanResults([scanResult, ...scanResults]);
      
      // Update statistics
      setStatistics(prev => ({
        totalScans: prev.totalScans + 1,
        averageScore: Math.round((prev.averageScore * prev.totalScans + scanResult.overall_score) / (prev.totalScans + 1)),
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
      console.error('Error generating report:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-900">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-indigo-500 mx-auto"></div>
          <p className="mt-4 text-gray-300">Lade Dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <nav className="bg-gray-800 border-b border-gray-700">
        <div className="mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <span className="text-2xl font-bold bg-gradient-to-r from-indigo-500 to-purple-600 text-transparent bg-clip-text">Complyo</span>
              </div>
              <div className="hidden md:block ml-10">
                <div className="flex items-baseline space-x-4">
                  <button 
                    onClick={() => setActiveTab('dashboard')}
                    className={`px-3 py-2 rounded-md text-sm font-medium ${activeTab === 'dashboard' ? 'bg-gray-700 text-white' : 'text-gray-300 hover:bg-gray-700 hover:text-white'}`}
                  >
                    Dashboard
                  </button>
                  <button 
                    onClick={() => setActiveTab('scans')}
                    className={`px-3 py-2 rounded-md text-sm font-medium ${activeTab === 'scans' ? 'bg-gray-700 text-white' : 'text-gray-300 hover:bg-gray-700 hover:text-white'}`}
                  >
                    Scans
                  </button>
                  <button 
                    onClick={() => setActiveTab('reports')}
                    className={`px-3 py-2 rounded-md text-sm font-medium ${activeTab === 'reports' ? 'bg-gray-700 text-white' : 'text-gray-300 hover:bg-gray-700 hover:text-white'}`}
                  >
                    Berichte
                  </button>
                  <button 
                    onClick={() => setActiveTab('settings')}
                    className={`px-3 py-2 rounded-md text-sm font-medium ${activeTab === 'settings' ? 'bg-gray-700 text-white' : 'text-gray-300 hover:bg-gray-700 hover:text-white'}`}
                  >
                    Einstellungen
                  </button>
                </div>
              </div>
            </div>
            <div className="hidden md:block">
              <div className="flex items-center">
                <span className="text-sm text-gray-300 mr-3">
                  {user?.subscription_tier === 'free' ? 'Kostenlose Nutzung' : 
                   user?.subscription_tier === 'basic' ? 'KI-Automatisierung' : 'Experten-Service'}
                </span>
                <span className="bg-indigo-800 py-1 px-3 rounded-full text-xs">
                  {user?.full_name || user?.email}
                </span>
              </div>
            </div>
          </div>
        </div>
      </nav>

      <main className="py-6">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          
          {/* New Scan Form */}
          <div className="mb-8 bg-gray-800 p-4 rounded-lg shadow">
            <form onSubmit={handleScanSubmit} className="flex">
              <div className="relative flex-grow">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                  <Globe className="h-5 w-5 text-gray-400" />
                </div>
                <input
                  type="text"
                  value={newScanUrl}
                  onChange={(e) => setNewScanUrl(e.target.value)}
                  placeholder="Website URL eingeben (z.B. example.com)"
                  className="bg-gray-700 text-white w-full pl-10 pr-4 py-2 rounded-l-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  disabled={isScanning}
                />
              </div>
              <button
                type="submit"
                className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white px-4 py-2 rounded-r-md hover:from-indigo-700 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 flex items-center"
                disabled={isScanning}
              >
                {isScanning ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-white mr-2"></div>
                    Analysiere...
                  </>
                ) : (
                  <>
                    <Search className="h-5 w-5 mr-2" />
                    Website prüfen
                  </>
                )}
              </button>
            </form>
            {user?.subscription_tier === 'free' && (
              <p className="mt-2 text-xs text-gray-400">
                Kostenlose Nutzung: {scanResults.length}/1 Scans. Für unbegrenzte Scans und automatische Fixes, upgraden Sie auf KI-Automatisierung.
              </p>
            )}
          </div>

          {activeTab === 'dashboard' && (
            <>
              {/* Stats Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <div className="bg-gray-800 rounded-lg shadow p-6">
                  <div className="flex items-center">
                    <div className="p-3 rounded-full bg-indigo-500 bg-opacity-10">
                      <PieChart className="h-6 w-6 text-indigo-400" />
                    </div>
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-400">Durchschnittlicher Score</p>
                      <p className="text-2xl font-semibold text-white">{statistics.averageScore}%</p>
                    </div>
                  </div>
                  <div className="w-full bg-gray-700 rounded-full h-2.5 mt-4">
                    <div 
                      className={`h-2.5 rounded-full ${
                        statistics.averageScore > 80 ? 'bg-green-500' : 
                        statistics.averageScore > 50 ? 'bg-yellow-500' : 'bg-red-500'
                      }`} 
                      style={{width: `${statistics.averageScore}%`}}
                    ></div>
                  </div>
                </div>
                
                <div className="bg-gray-800 rounded-lg shadow p-6">
                  <div className="flex items-center">
                    <div className="p-3 rounded-full bg-purple-500 bg-opacity-10">
                      <BarChart2 className="h-6 w-6 text-purple-400" />
                    </div>
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-400">Durchgeführte Scans</p>
                      <p className="text-2xl font-semibold text-white">{statistics.totalScans}</p>
                    </div>
                  </div>
                  <p className="text-sm text-gray-400 mt-4">
                    {statistics.totalScans === 0 ? 
                      "Führen Sie Ihren ersten Scan durch" : 
                      `Letzter Scan: ${new Date(scanResults[0]?.scan_timestamp).toLocaleDateString()}`}
                  </p>
                </div>
                
                <div className="bg-gray-800 rounded-lg shadow p-6">
                  <div className="flex items-center">
                    <div className="p-3 rounded-full bg-pink-500 bg-opacity-10">
                      <Shield className="h-6 w-6 text-pink-400" />
                    </div>
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-400">Abmahn-Risiko</p>
                      <p className="text-2xl font-semibold text-white">
                        {scanResults.length > 0 ? 
                          scanResults[0].overall_score > 80 ? "Niedrig" : 
                          scanResults[0].overall_score > 50 ? "Mittel" : "Hoch"
                          : "-"}
                      </p>
                    </div>
                  </div>
                  <p className="text-sm text-gray-400 mt-4">
                    {scanResults.length > 0 ? 
                      (scanResults[0].overall_score < 50 ? 
                        "Kritische Probleme gefunden" : 
                        scanResults[0].overall_score < 80 ? 
                          "Verbesserungspotential vorhanden" : 
                          "Gute Compliance") : 
                      "Noch keine Daten verfügbar"}
                  </p>
                </div>
              </div>
              
              {/* Recent Scans */}
              <div className="bg-gray-800 rounded-lg shadow mb-8">
                <div className="px-6 py-4 border-b border-gray-700">
                  <h2 className="text-lg font-medium">Letzte Scans</h2>
                </div>
                <div className="overflow-x-auto">
                  {scanResults.length === 0 ? (
                    <div className="p-6 text-center text-gray-400">
                      <Globe className="h-12 w-12 mx-auto mb-4 text-gray-500" />
                      <p>Noch keine Website-Scans durchgeführt</p>
                      <p className="text-sm mt-2">Geben Sie eine URL ein, um Ihre erste Compliance-Analyse zu starten</p>
                    </div>
                  
                </div>
{scanResults.length > 0 && (
  <div className="px-6 py-3 border-t border-gray-700 text-right">
    <button 
      onClick={() => setActiveTab('scans')}
      className="text-sm text-indigo-400 hover:text-indigo-300"
    >
      Alle Scans anzeigen →
    </button>
  </div>
)}
</div>

{/* Category Analysis */}
{scanResults.length > 0 && (
<div className="bg-gray-800 rounded-lg shadow">
  <div className="px-6 py-4 border-b border-gray-700">
    <h2 className="text-lg font-medium">Compliance-Analyse</h2>
  </div>
  <div className="grid grid-cols-1 md:grid-cols-2 gap-6 p-6">
    
    {/* Impressum */}
    <div className="bg-gray-750 rounded-lg p-4">
      <div className="flex items-center mb-3">
        <div className={`p-2 rounded-md ${
          scanResults[0].results.find(r => r.category === 'Impressum')?.status === 'pass' ? 
            'bg-green-900 text-green-300' : 
            scanResults[0].results.find(r => r.category === 'Impressum')?.status === 'warning' ? 
              'bg-yellow-900 text-yellow-300' : 
              'bg-red-900 text-red-300'
        }`}>
          <FileText className="h-5 w-5" />
        </div>
        <h3 className="ml-3 text-md font-medium">Impressum</h3>
      </div>
      <p className="text-sm text-gray-400 mb-3">
        {scanResults[0].results.find(r => r.category === 'Impressum')?.message || 
         'Keine Informationen verfügbar'}
      </p>
      <div className="flex justify-between items-center">
        <div className={`text-sm font-medium px-2 py-0.5 rounded ${
          scanResults[0].results.find(r => r.category === 'Impressum')?.status === 'pass' ? 
            'bg-green-900 text-green-300' : 
            scanResults[0].results.find(r => r.category === 'Impressum')?.status === 'warning' ? 
              'bg-yellow-900 text-yellow-300' : 
              'bg-red-900 text-red-300'
        }`}>
          {scanResults[0].results.find(r => r.category === 'Impressum')?.status === 'pass' ? 
            'Bestanden' : 
            scanResults[0].results.find(r => r.category === 'Impressum')?.status === 'warning' ? 
              'Warnung' : 
              'Nicht bestanden'}
        </div>
        {user?.subscription_tier !== 'free' && 
         scanResults[0].results.find(r => r.category === 'Impressum')?.status !== 'pass' && (
          <button className="text-sm text-indigo-400 hover:text-indigo-300">
            Automatisch beheben
          </button>
        )}
      </div>
    </div>
    
    {/* Datenschutzerklärung */}
    <div className="bg-gray-750 rounded-lg p-4">
      <div className="flex items-center mb-3">
        <div className={`p-2 rounded-md ${
          scanResults[0].results.find(r => r.category === 'Datenschutzerklärung')?.status === 'pass' ? 
            'bg-green-900 text-green-300' : 
            scanResults[0].results.find(r => r.category === 'Datenschutzerklärung')?.status === 'warning' ? 
              'bg-yellow-900 text-yellow-300' : 
              'bg-red-900 text-red-300'
        }`}>
          <Shield className="h-5 w-5" />
        </div>
        <h3 className="ml-3 text-md font-medium">Datenschutzerklärung</h3>
      </div>
      <p className="text-sm text-gray-400 mb-3">
        {scanResults[0].results.find(r => r.category === 'Datenschutzerklärung')?.message || 
         'Keine Informationen verfügbar'}
      </p>
      <div className="flex justify-between items-center">
        <div className={`text-sm font-medium px-2 py-0.5 rounded ${
          scanResults[0].results.find(r => r.category === 'Datenschutzerklärung')?.status === 'pass' ? 
            'bg-green-900 text-green-300' : 
            scanResults[0].results.find(r => r.category === 'Datenschutzerklärung')?.status === 'warning' ? 
              'bg-yellow-900 text-yellow-300' : 
              'bg-red-900 text-red-300'
        }`}>
          {scanResults[0].results.find(r => r.category === 'Datenschutzerklärung')?.status === 'pass' ? 
            'Bestanden' : 
            scanResults[0].results.find(r => r.category === 'Datenschutzerklärung')?.status === 'warning' ? 
              'Warnung' : 
              'Nicht bestanden'}
        </div>
        {user?.subscription_tier !== 'free' && 
         scanResults[0].results.find(r => r.category === 'Datenschutzerklärung')?.status !== 'pass' && (
          <button className="text-sm text-indigo-400 hover:text-indigo-300">
            Automatisch beheben
          </button>
        )}
      </div>
    </div>
    
    {/* Cookie-Compliance */}
    <div className="bg-gray-750 rounded-lg p-4">
      <div className="flex items-center mb-3">
        <div className={`p-2 rounded-md ${
          scanResults[0].results.find(r => r.category === 'Cookie-Compliance')?.status === 'pass' ? 
            'bg-green-900 text-green-300' : 
            scanResults[0].results.find(r => r.category === 'Cookie-Compliance')?.status === 'warning' ? 
              'bg-yellow-900 text-yellow-300' : 
              'bg-red-900 text-red-300'
        }`}>
          <AlertTriangle className="h-5 w-5" />
        </div>
        <h3 className="ml-3 text-md font-medium">Cookie-Compliance</h3>
      </div>
      <p className="text-sm text-gray-400 mb-3">
        {scanResults[0].results.find(r => r.category === 'Cookie-Compliance')?.message || 
         'Keine Informationen verfügbar'}
      </p>
      <div className="flex justify-between items-center">
        <div className={`text-sm font-medium px-2 py-0.5 rounded ${
          scanResults[0].results.find(r => r.category === 'Cookie-Compliance')?.status === 'pass' ? 
            'bg-green-900 text-green-300' : 
            scanResults[0].results.find(r => r.category === 'Cookie-Compliance')?.status === 'warning' ? 
              'bg-yellow-900 text-yellow-300' : 
              'bg-red-900 text-red-300'
        }`}>
          {scanResults[0].results.find(r => r.category === 'Cookie-Compliance')?.status === 'pass' ? 
            'Bestanden' : 
            scanResults[0].results.find(r => r.category === 'Cookie-Compliance')?.status === 'warning' ? 
              'Warnung' : 
              'Nicht bestanden'}
        </div>
        {user?.subscription_tier !== 'free' && 
         scanResults[0].results.find(r => r.category === 'Cookie-Compliance')?.status !== 'pass' && (
          <button className="text-sm text-indigo-400 hover:text-indigo-300">
            Automatisch beheben
          </button>
        )}
      </div>
    </div>
    
    {/* Barrierefreiheit */}
    <div className="bg-gray-750 rounded-lg p-4">
      <div className="flex items-center mb-3">
        <div className={`p-2 rounded-md ${
          scanResults[0].results.find(r => r.category === 'Basis-Barrierefreiheit')?.status === 'pass' ? 
            'bg-green-900 text-green-300' : 
            scanResults[0].results.find(r => r.category === 'Basis-Barrierefreiheit')?.status === 'warning' ? 
              'bg-yellow-900 text-yellow-300' : 
              'bg-red-900 text-red-300'
        }`}>
          <CheckCircle className="h-5 w-5" />
        </div>
        <h3 className="ml-3 text-md font-medium">Barrierefreiheit</h3>
      </div>
      <p className="text-sm text-gray-400 mb-3">
        {scanResults[0].results.find(r => r.category === 'Basis-Barrierefreiheit')?.message || 
         'Keine Informationen verfügbar'}
      </p>
      <div className="flex justify-between items-center">
        <div className={`text-sm font-medium px-2 py-0.5 rounded ${
          scanResults[0].results.find(r => r.category === 'Basis-Barrierefreiheit')?.status === 'pass' ? 
            'bg-green-900 text-green-300' : 
            scanResults[0].results.find(r => r.category === 'Basis-Barrierefreiheit')?.status === 'warning' ? 
              'bg-yellow-900 text-yellow-300' : 
              'bg-red-900 text-red-300'
        }`}>
          {scanResults[0].results.find(r => r.category === 'Basis-Barrierefreiheit')?.status === 'pass' ? 
            'Bestanden' : 
            scanResults[0].results.find(r => r.category === 'Basis-Barrierefreiheit')?.status === 'warning' ? 
              'Warnung' : 
              'Nicht bestanden'}
        </div>
        {user?.subscription_tier !== 'free' && 
         scanResults[0].results.find(r => r.category === 'Basis-Barrierefreiheit')?.status !== 'pass' && (
          <button className="text-sm text-indigo-400 hover:text-indigo-300">
            Automatisch beheben
          </button>
        )}
      </div>
    </div>
  </div>
</div>
)}
</>
)}

{activeTab === 'scans' && (
<div className="bg-gray-800 rounded-lg shadow">
<div className="px-6 py-4 border-b border-gray-700">
<h2 className="text-lg font-medium">Alle Website-Scans</h2>
</div>
<div className="overflow-x-auto">
{scanResults.length === 0 ? (
  <div className="p-6 text-center text-gray-400">
    <Globe className="h-12 w-12 mx-auto mb-4 text-gray-500" />
    <p>Noch keine Website-Scans durchgeführt</p>
    <p className="text-sm mt-2">Geben Sie eine URL ein, um Ihre erste Compliance-Analyse zu starten</p>
  </div>
) : (
  <table className="min-w-full divide-y divide-gray-700">
    <thead className="bg-gray-700">
      <tr>
        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
          Website
        </th>
        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
          Score
        </th>
        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
          Probleme
        </th>
        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
          Datum
        </th>
        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
          Dauer
        </th>
        <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
          Aktionen
        </th>
      </tr>
    </thead>
    <tbody className="bg-gray-800 divide-y divide-gray-700">
      {scanResults.map((scan, index) => (
        <tr key={index} className="hover:bg-gray-750">
          <td className="px-6 py-4 whitespace-nowrap">
            <div className="flex items-center">
              <div className="h-8 w-8 rounded-full bg-gray-700 flex items-center justify-center">
                <Globe className="h-4 w-4 text-gray-400" />
              </div>
              <div className="ml-3">
                <div className="text-sm font-medium text-white truncate max-w-xs">
                  {scan.url}
                </div>
              </div>
            </div>
          </td>
          <td className="px-6 py-4 whitespace-nowrap">
            <div className={`text-sm font-semibold rounded-full px-2.5 py-0.5 text-center w-12 ${
              scan.overall_score > 80 ? 'bg-green-900 text-green-200' : 
              scan.overall_score > 50 ? 'bg-yellow-900 text-yellow-200' : 
              'bg-red-900 text-red-200'
            }`}>
              {scan.overall_score}%
            </div>
          </td>
          <td className="px-6 py-4 whitespace-nowrap">
            <div className="flex items-center">
              <div className="flex -space-x-1">
                <div className="z-10 h-5 w-5 rounded-full bg-red-500 flex items-center justify-center">
                  <span className="text-xs text-white font-bold">
                    {Array.isArray(scan.results) ? 
                      scan.results.filter(r => r.status === 'fail').length : 
                      '?'
                    }
                  </span>
                </div>
                <div className="z-0 h-5 w-5 rounded-full bg-yellow-500 flex items-center justify-center">
                  <span className="text-xs text-white font-bold">
                    {Array.isArray(scan.results) ? 
                      scan.results.filter(r => r.status === 'warning').length : 
                      '?'
                    }
                  </span>
                </div>
              </div>
              <span className="ml-2 text-sm text-gray-400">
                {scan.total_issues} Probleme gefunden
              </span>
            </div>
          </td>
          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
            {new Date(scan.scan_timestamp).toLocaleDateString()} um{' '}
            {new Date(scan.scan_timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
          </td>
          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
            <div className="flex items-center">
              <Clock className="h-4 w-4 mr-1 text-gray-500" />
              {(scan.scan_duration_ms / 1000).toFixed(2)}s
            </div>
          </td>
          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
            <div className="flex space-x-3">
              <button 
                onClick={() => generateReport(scan.id)}
                className="text-indigo-400 hover:text-indigo-300 flex items-center"
              >
                <FileText className="h-4 w-4 mr-1" />
                PDF
              </button>
              {user?.subscription_tier !== 'free' && (
                <button className="text-green-400 hover:text-green-300 flex items-center">
                  <CheckCircle className="h-4 w-4 mr-1" />
                  Fix
                </button>
              )}
            </div>
          </td>
        </tr>
      ))}
    </tbody>
  </table>
)}
</div>
</div>
)}

{activeTab === 'reports' && (
<div className="bg-gray-800 rounded-lg shadow">
<div className="px-6 py-4 border-b border-gray-700 flex justify-between items-center">
<h2 className="text-lg font-medium">Compliance-Berichte</h2>
{reports.length > 0 && (
  <span className="text-sm text-gray-400">
    {reports.length} {reports.length === 1 ? 'Bericht' : 'Berichte'} generiert
  </span>
)}
</div>
<div>
{reports.length === 0 ? (
  <div className="p-6 text-center text-gray-400">
    <FileText className="h-12 w-12 mx-auto mb-4 text-gray-500" />
    <p>Noch keine Berichte generiert</p>
    <p className="text-sm mt-2">Führen Sie einen Scan durch und erstellen Sie dann einen PDF-Bericht</p>
  </div>
) : (
  <ul className="divide-y divide-gray-700">
    {reports.map((report, index) => (
      <li key={index} className="p-4 hover:bg-gray-750">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <div className="p-2 rounded-md bg-indigo-900 text-indigo-300">
              <FileText className="h-5 w-5" />
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-white">
                {report.url?.split('/').pop() || `Bericht #${index + 1}`}
              </p>
              <p className="text-xs text-gray-400">
                Erstellt am {new Date(report.created_at).toLocaleDateString()} um{' '}
                {new Date(report.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
              </p>
            </div>
          </div>
          <a
            href={report.url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center text-sm text-indigo-400 hover:text-indigo-300"
          >
            <Download className="h-4 w-4 mr-1" />
            Download
          </a>
        </div>
      </li>
    ))}
  </ul>
)}
</div>
</div>
)}

{activeTab === 'settings' && (
<div className="bg-gray-800 rounded-lg shadow">
<div className="px-6 py-4 border-b border-gray-700">
<h2 className="text-lg font-medium">Konto & Abonnement</h2>
</div>
<div className="p-6">
<div className="mb-8">
  <h3 className="text-md font-medium mb-4">Aktuelles Abonnement</h3>
  <div className="bg-gray-750 rounded-lg p-4">
    <div className="flex items-center">
      <div className={`p-3 rounded-full ${
        user?.subscription_tier === 'free' ? 'bg-gray-700 text-gray-300' :
        user?.subscription_tier === 'basic' ? 'bg-indigo-900 text-indigo-300' :
        'bg-purple-900 text-purple-300'
      }`}>
        <Shield className="h-6 w-6" />
      </div>
      <div className="ml-4">
        <p className="text-md font-medium text-white">
          {user?.subscription_tier === 'free' ? 'Kostenlose Nutzung' :
           user?.subscription_tier === 'basic' ? 'KI-Automatisierung' :
           'Experten-Service'}
        </p>
        <p className="text-sm text-gray-400">
          {user?.subscription_tier === 'free' ? 'Limitierte Funktionen' :
           user?.subscription_tier === 'basic' ? '39€/Monat' :
           '39€/Monat + Experten-Setup'}
        </p>
      </div>
    </div>
    
    {user?.subscription_tier === 'free' && (
      <div className="mt-4 p-3 bg-gray-800 rounded border border-gray-700">
        <h4 className="text-sm font-medium mb-2">Upgrade auf KI-Automatisierung</h4>
        <ul className="text-xs text-gray-400 mb-3 space-y-1">
          <li className="flex items-center">
            <CheckCircle className="h-3 w-3 text-green-500 mr-1" />
            Unbegrenzte Compliance-Scans
          </li>
          <li className="flex items-center">
            <CheckCircle className="h-3 w-3 text-green-500 mr-1" />
            KI-gestützte Rechtstext-Generierung
          </li>
          <li className="flex items-center">
            <CheckCircle className="h-3 w-3 text-green-500 mr-1" />
            Automatisches Cookie-Banner
          </li>
          <li className="flex items-center">
            <CheckCircle className="h-3 w-3 text-green-500 mr-1" />
            Monatliche Re-Scans
          </li>
        </ul>
        <button className="w-full bg-gradient-to-r from-indigo-600 to-purple-600 text-white px-4 py-2 rounded-md hover:from-indigo-700 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focusimport React, { useState, useEffect } from 'react';
import { Search, Shield, AlertTriangle, CheckCircle, FileText, PieChart, Globe, BarChart2, Clock, Download, Plus } from 'lucide-react';

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

export default function Dashboard() {
const [loading, setLoading] = useState(true);
const [scanResults, setScanResults] = useState([]);
const [reports, setReports] = useState([]);
const [statistics, setStatistics] = useState({
totalScans: 0,
averageScore: 0,
issuesByCategory: {}
});
const [newScanUrl, setNewScanUrl] = useState('');
const [isScanning, setIsScanning] = useState(false);
const [user, setUser] = useState(null);
const [activeTab, setActiveTab] = useState('dashboard');

useEffect(() => {
const fetchData = async () => {
try {
setLoading(true);

// Fetch user profile
const userProfile = await fetchWithAuth(`${API_URL}/api/users/me`);
setUser(userProfile);

// Fetch scan results
const results = await fetchWithAuth(`${API_URL}/api/scans/list`);
setScanResults(results);

// Fetch reports
const reportsList = await fetchWithAuth(`${API_URL}/api/reports/list`);
setReports(reportsList);

// Calculate statistics
if (results.length > 0) {
const totalScans = results.length;
const totalScore = results.reduce((sum, scan) => sum + scan.overall_score, 0);
const averageScore = Math.round(totalScore / totalScans);

// Count issues by category
const issuesByCategory = {};
results.forEach(scan => {
if (typeof scan.results === 'string') {
scan.results = JSON.parse(scan.results);
}

scan.results.forEach(result => {
const category = result.category;
if (!issuesByCategory[category]) {
issuesByCategory[category] = { fail: 0, warning: 0, pass: 0 };
}
issuesByCategory[category][result.status]++;
});
});

setStatistics({
totalScans,
averageScore,
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
if (!newScanUrl.startsWith('http://') && !newScanUrl.startsWith('https://')) {
setNewScanUrl(`https://${newScanUrl}`);
}

// Perform scan
const scanResult = await fetchWithAuth(`${API_URL}/api/analyze`, {
method: 'POST',
body: JSON.stringify({ url: newScanUrl })
});

// Update scan results
setScanResults([scanResult, ...scanResults]);

// Update statistics
setStatistics(prev => ({
totalScans: prev.totalScans + 1,
averageScore: Math.round((prev.averageScore * prev.totalScans + scanResult.overall_score) / (prev.totalScans + 1)),
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
console.error('Error generating report:', error);
}
};

if (loading) {
return (
<div className="flex items-center justify-center min-h-screen bg-gray-900">
<div className="text-center">
<div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-indigo-500 mx-auto"></div>
<p className="mt-4 text-gray-300">Lade Dashboard...</p>
</div>
</div>
);
}

return (
<div className="min-h-screen bg-gray-900 text-white">
<nav className="bg-gray-800 border-b border-gray-700">
<div className="mx-auto px-4 sm:px-6 lg:px-8">
<div className="flex items-center justify-between h-16">
<div className="flex items-center">
<div className="flex-shrink-0">
<span className="text-2xl font-bold bg-gradient-to-r from-indigo-500 to-purple-600 text-transparent bg-clip-text">Complyo</span>
</div>
<div className="hidden md:block ml-10">
<div className="flex items-baseline space-x-4">
  <button 
    onClick={() => setActiveTab('dashboard')}
    className={`px-3 py-2 rounded-md text-sm font-medium ${activeTab === 'dashboard' ? 'bg-gray-700 text-white' : 'text-gray-300 hover:bg-gray-700 hover:text-white'}`}
  >
    Dashboard
  </button>
  <button 
    onClick={() => setActiveTab('scans')}
    className={`px-3 py-2 rounded-md text-sm font-medium ${activeTab === 'scans' ? 'bg-gray-700 text-white' : 'text-gray-300 hover:bg-gray-700 hover:text-white'}`}
  >
    Scans
  </button>
  <button 
    onClick={() => setActiveTab('reports')}
    className={`px-3 py-2 rounded-md text-sm font-medium ${activeTab === 'reports' ? 'bg-gray-700 text-white' : 'text-gray-300 hover:bg-gray-700 hover:text-white'}`}
  >
    Berichte
  </button>
  <button 
    onClick={() => setActiveTab('settings')}
    className={`px-3 py-2 rounded-md text-sm font-medium ${activeTab === 'settings' ? 'bg-gray-700 text-white' : 'text-gray-300 hover:bg-gray-700 hover:text-white'}`}
  >
    Einstellungen
  </button>
</div>
</div>
</div>
<div className="hidden md:block">
<div className="flex items-center">
<span className="text-sm text-gray-300 mr-3">
  {user?.subscription_tier === 'free' ? 'Kostenlose Nutzung' : 
   user?.subscription_tier === 'basic' ? 'KI-Automatisierung' : 'Experten-Service'}
</span>
<span className="bg-indigo-800 py-1 px-3 rounded-full text-xs">
  {user?.full_name || user?.email}
</span>
</div>
</div>
</div>
</div>
</nav>

<main className="py-6">
<div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">

{/* New Scan Form */}
<div className="mb-8 bg-gray-800 p-4 rounded-lg shadow">
<form onSubmit={handleScanSubmit} className="flex">
<div className="relative flex-grow">
<div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
  <Globe className="h-5 w-5 text-gray-400" />
</div>
<input
  type="text"
  value={newScanUrl}
  onChange={(e) => setNewScanUrl(e.target.value)}
  placeholder="Website URL eingeben (z.B. example.com)"
  className="bg-gray-700 text-white w-full pl-10 pr-4 py-2 rounded-l-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
  disabled={isScanning}
/>
</div>
<button
type="submit"
className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white px-4 py-2 rounded-r-md hover:from-indigo-700 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 flex items-center"
disabled={isScanning}
>
{isScanning ? (
  <>
    <div className="animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-white mr-2"></div>
    Analysiere...
  </>
) : (
  <>
    <Search className="h-5 w-5 mr-2" />
    Website prüfen
  </>
)}
</button>
</form>
{user?.subscription_tier === 'free' && (
<p className="mt-2 text-xs text-gray-400">
Kostenlose Nutzung: {scanResults.length}/1 Scans. Für unbegrenzte Scans und automatische Fixes, upgraden Sie auf KI-Automatisierung.
</p>
)}
</div>

{activeTab === 'dashboard' && (
<>
{/* Stats Cards */}
<div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
<div className="bg-gray-800 rounded-lg shadow p-6">
  <div className="flex items-center">
    <div className="p-3 rounded-full bg-indigo-500 bg-opacity-10">
      <PieChart className="h-6 w-6 text-indigo-400" />
    </div>
    <div className="ml-4">
      <p className="text-sm font-medium text-gray-400">Durchschnittlicher Score</p>
      <p className="text-2xl font-semibold text-white">{statistics.averageScore}%</p>
    </div>
  </div>
  <div className="w-full bg-gray-700 rounded-full h-2.5 mt-4">
    <div 
      className={`h-2.5 rounded-full ${
        statistics.averageScore > 80 ? 'bg-green-500' : 
        statistics.averageScore > 50 ? 'bg-yellow-500' : 'bg-red-500'
      }`} 
      style={{width: `${statistics.averageScore}%`}}
    ></div>
  </div>
</div>

<div className="bg-gray-800 rounded-lg shadow p-6">
  <div className="flex items-center">
    <div className="p-3 rounded-full bg-purple-500 bg-opacity-10">
      <BarChart2 className="h-6 w-6 text-purple-400" />
    </div>
    <div className="ml-4">
      <p className="text-sm font-medium text-gray-400">Durchgeführte Scans</p>
      <p className="text-2xl font-semibold text-white">{statistics.totalScans}</p>
    </div>
  </div>
  <p className="text-sm text-gray-400 mt-4">
    {statistics.totalScans === 0 ? 
      "Führen Sie Ihren ersten Scan durch" : 
      `Letzter Scan: ${new Date(scanResults[0]?.scan_timestamp).toLocaleDateString()}`}
  </p>
</div>

<div className="bg-gray-800 rounded-lg shadow p-6">
  <div className="flex items-center">
    <div className="p-3 rounded-full bg-pink-500 bg-opacity-10">
      <Shield className="h-6 w-6 text-pink-400" />
    </div>
    <div className="ml-4">
      <p className="text-sm font-medium text-gray-400">Abmahn-Risiko</p>
      <p className="text-2xl font-semibold text-white">
        {scanResults.length > 0 ? 
          scanResults[0].overall_score > 80 ? "Niedrig" : 
          scanResults[0].overall_score > 50 ? "Mittel" : "Hoch"
          : "-"}
      </p>
    </div>
  </div>
  <p className="text-sm text-gray-400 mt-4">
    {scanResults.length > 0 ? 
      (scanResults[0].overall_score < 50 ? 
        "Kritische Probleme gefunden" : 
        scanResults[0].overall_score < 80 ? 
          "Verbesserungspotential vorhanden" : 
          "Gute Compliance") : 
      "Noch keine Daten verfügbar"}
  </p>
</div>
</div>

{/* Recent Scans */}
<div className="bg-gray-800 rounded-lg shadow mb-8">
<div className="px-6 py-4 border-b border-gray-700">
  <h2 className="text-lg font-medium">Letzte Scans</h2>
</div>
<div className="overflow-x-auto">
  {scanResults.length === 0 ? (
    <div className="p-6 text-center text-gray-400">
      <Globe className="h-12 w-12 mx-auto mb-4 text-gray-500" />
      <p>Noch keine Website-Scans durchgeführt</p>
      <p className="text-sm mt-2">Geben Sie eine URL ein, um Ihre erste Compliance-Analyse zu starten</p>
    </div>
  ) : (
    <table className="min-w-full divide-y divide-gray-700">
      <thead className="bg-gray-700">
        <tr>
          <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
            Website
          </th>
          <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
            Score
          </th>
          <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
            Probleme
          </th>
          <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
            Datum
          </th>
          <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
            Aktionen
          </th>
        </tr>
      </thead>
      <tbody className="bg-gray-800 divide-y divide-gray-700">
        {scanResults.slice(0, 5).map((scan, index) => (
          <tr key={index} className="hover:bg-gray-750">
            <td className="px-6 py-4 whitespace-nowrap">
              <div className="flex items-center">
                <div className="h-8 w-8 rounded-full bg-gray-700 flex items-center justify-center">
                  <Globe className="h-4 w-4 text-gray-400" />
                </div>
                <div className="ml-3">
                  <div className="text-sm font-medium text-white truncate max-w-xs">
                    {scan.url}
                  </div>
                </div>
              </div>
            </td>
            <td className="px-6 py-4 whitespace-nowrap">
              <div className={`text-sm font-semibold rounded-full px-2.5 py-0.5 text-center w-12 ${
                scan.overall_score > 80 ? 'bg-green-900 text-green-200' : 
                scan.overall_score > 50 ? 'bg-yellow-900 text-yellow-200' : 
                'bg-red-900 text-red-200'
              }`}>
                {scan.overall_score}%
              </div>
            </td>
            <td className="px-6 py-4 whitespace-nowrap">
              <div className="flex items-center">
                <div className="flex -space-x-1">
                  <div className="z-10 h-5 w-5 rounded-full bg-red-500 flex items-center justify-center">
                    <span className="text-xs text-white font-bold">
                      {Array.isArray(scan.results) ? 
                        scan.results.filter(r => r.status === 'fail').length : 
                        '?'
                      }
                    </span>
                  </div>
                  <div className="z-0 h-5 w-5 rounded-full bg-yellow-500 flex items-center justify-center">
                    <span className="text-xs text-white font-bold">
                      {Array.isArray(scan.results) ? 
                        scan.results.filter(r => r.status === 'warning').length : 
                        '?'
                      }
                    </span>
                  </div>
                </div>
                <span className="ml-2 text-sm text-gray-400">
                  {scan.total_issues} Probleme gefunden
                </span>
              </div>
            </td>
            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-300">
              {new Date(scan.scan_timestamp).toLocaleDateString()} um{' '}
              {new Date(scan.scan_timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
            </td>
            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
              <button 
                onClick={() => generateReport(scan.id)}
                className="text-indigo-400 hover:text-indigo-300 flex items-center"
              >
                <FileText className="h-4 w-4 mr-1" />
                PDF Report
              </button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )}
  