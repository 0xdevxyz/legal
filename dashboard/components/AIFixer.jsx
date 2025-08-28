import React, { useState } from 'react';
import { Zap, Download, CheckCircle, Clock, FileText, Code, Settings, AlertCircle } from 'lucide-react';

const AIFixer = ({ scanResult, onFixGenerated }) => {
  const [generating, setGenerating] = useState(false);
  const [fixResult, setFixResult] = useState(null);
  const [companyInfo, setCompanyInfo] = useState({
    company_name: '',
    address: '',
    postal_code: '',
    city: '',
    phone: '',
    email: '',
    vat_id: '',
    responsible_person: ''
  });
  const [selectedCategories, setSelectedCategories] = useState([]);

  const availableCategories = [
    'Impressum',
    'Datenschutz', 
    'Cookie-Compliance',
    'Barrierefreiheit',
    'Sicherheit',
    'Social Media'
  ];

  const generateFixes = async () => {
    try {
      setGenerating(true);
      
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'https://api.complyo.tech'}/api/ai-fix`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        },
        body: JSON.stringify({
          scan_id: scanResult.id,
          company_info: companyInfo,
          fix_categories: selectedCategories.length > 0 ? selectedCategories : undefined
        })
      });

      if (!response.ok) {
        throw new Error('AI fix generation failed');
      }

      const result = await response.json();
      setFixResult(result);
      
      if (onFixGenerated) {
        onFixGenerated(result);
      }
      
    } catch (error) {
      console.error('AI fix generation error:', error);
    } finally {
      setGenerating(false);
    }
  };

  const downloadFile = async (fixId, filename) => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'https://api.complyo.tech'}/api/download/${fixId}/${filename}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        }
      });
      
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        window.URL.revokeObjectURL(url);
      }
    } catch (error) {
      console.error('Download error:', error);
    }
  };

  const getFixTypeIcon = (fixType) => {
    switch (fixType) {
      case 'text_generation': return <FileText className="w-4 h-4" />;
      case 'code_modification': return <Code className="w-4 h-4" />;
      case 'banner_integration': return <Settings className="w-4 h-4" />;
      default: return <Zap className="w-4 h-4" />;
    }
  };

  const getConfidenceColor = (score) => {
    if (score >= 0.9) return 'text-green-600 bg-green-100';
    if (score >= 0.7) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <Zap className="w-5 h-5 text-blue-600" />
          KI-Automatisierung
        </h3>
        <button
          onClick={generateFixes}
          disabled={generating}
          className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
        >
          {generating ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
              Generierung...
            </>
          ) : (
            <>
              <Zap className="w-4 h-4" />
              Fixes generieren
            </>
          )}
        </button>
      </div>

      {/* Company Information Form */}
      <div className="mb-6">
        <h4 className="font-medium text-gray-900 mb-3">Unternehmensinformationen</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Firmenname *
            </label>
            <input
              type="text"
              value={companyInfo.company_name}
              onChange={(e) => setCompanyInfo({...companyInfo, company_name: e.target.value})}
              className="w-full border border-gray-300 rounded-md px-3 py-2"
              placeholder="Muster GmbH"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              E-Mail *
            </label>
            <input
              type="email"
              value={companyInfo.email}
              onChange={(e) => setCompanyInfo({...companyInfo, email: e.target.value})}
              className="w-full border border-gray-300 rounded-md px-3 py-2"
              placeholder="info@muster.de"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Adresse *
            </label>
            <input
              type="text"
              value={companyInfo.address}
              onChange={(e) => setCompanyInfo({...companyInfo, address: e.target.value})}
              className="w-full border border-gray-300 rounded-md px-3 py-2"
              placeholder="Musterstraße 123"
            />
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                PLZ *
              </label>
              <input
                type="text"
                value={companyInfo.postal_code}
                onChange={(e) => setCompanyInfo({...companyInfo, postal_code: e.target.value})}
                className="w-full border border-gray-300 rounded-md px-3 py-2"
                placeholder="12345"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Stadt *
              </label>
              <input
                type="text"
                value={companyInfo.city}
                onChange={(e) => setCompanyInfo({...companyInfo, city: e.target.value})}
                className="w-full border border-gray-300 rounded-md px-3 py-2"
                placeholder="Musterstadt"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Telefon
            </label>
            <input
              type="tel"
              value={companyInfo.phone}
              onChange={(e) => setCompanyInfo({...companyInfo, phone: e.target.value})}
              className="w-full border border-gray-300 rounded-md px-3 py-2"
              placeholder="+49 123 456789"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Verantwortliche Person
            </label>
            <input
              type="text"
              value={companyInfo.responsible_person}
              onChange={(e) => setCompanyInfo({...companyInfo, responsible_person: e.target.value})}
              className="w-full border border-gray-300 rounded-md px-3 py-2"
              placeholder="Max Mustermann"
            />
          </div>
        </div>
      </div>

      {/* Category Selection */}
      <div className="mb-6">
        <h4 className="font-medium text-gray-900 mb-3">Kategorien auswählen (optional)</h4>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
          {availableCategories.map(category => (
            <label key={category} className="flex items-center space-x-2 cursor-pointer">
              <input
                type="checkbox"
                checked={selectedCategories.includes(category)}
                onChange={(e) => {
                  if (e.target.checked) {
                    setSelectedCategories([...selectedCategories, category]);
                  } else {
                    setSelectedCategories(selectedCategories.filter(c => c !== category));
                  }
                }}
                className="rounded border-gray-300"
              />
              <span className="text-sm">{category}</span>
            </label>
          ))}
        </div>
        <p className="text-xs text-gray-500 mt-2">
          Leer lassen für alle Kategorien
        </p>
      </div>

      {/* Fix Results */}
      {fixResult && (
        <div className="border-t pt-6">
          <div className="flex items-center justify-between mb-4">
            <h4 className="font-medium text-gray-900">Generierte Lösungen</h4>
            <div className="text-sm text-gray-600">
              {fixResult.total_issues_fixed} von {scanResult.total_issues} Problemen behoben
            </div>
          </div>

          {/* Fix Summary */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="bg-green-50 p-4 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <CheckCircle className="w-5 h-5 text-green-600" />
                <span className="font-medium text-green-800">Erfolgsrate</span>
              </div>
              <div className="text-2xl font-bold text-green-600">
                {Math.round(fixResult.success_rate * 100)}%
              </div>
            </div>

            <div className="bg-blue-50 p-4 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <Clock className="w-5 h-5 text-blue-600" />
                <span className="font-medium text-blue-800">Geschätzte Zeit</span>
              </div>
              <div className="text-2xl font-bold text-blue-600">
                {fixResult.estimated_total_time} Min
              </div>
            </div>

            <div className="bg-purple-50 p-4 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <FileText className="w-5 h-5 text-purple-600" />
                <span className="font-medium text-purple-800">Dateien</span>
              </div>
              <div className="text-2xl font-bold text-purple-600">
                {Object.keys(fixResult.generated_files || {}).length}
              </div>
            </div>
          </div>

          {/* Generated Fixes */}
          <div className="space-y-4 mb-6">
            {fixResult.fixes_applied.map((fix, index) => (
              <div key={index} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    {getFixTypeIcon(fix.fix_type)}
                    <h5 className="font-medium">{fix.issue_category}</h5>
                    {fix.auto_applicable && (
                      <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full">
                        Auto-anwendbar
                      </span>
                    )}
                  </div>
                  <span className={`text-xs px-2 py-1 rounded-full ${getConfidenceColor(fix.confidence_score)}`}>
                    {Math.round(fix.confidence_score * 100)}% Konfidenz
                  </span>
                </div>
                
                <p className="text-gray-700 text-sm mb-2">{fix.description}</p>
                
                <div className="text-xs text-gray-600 bg-gray-50 p-2 rounded">
                  <strong>Implementierung:</strong> {fix.implementation_instructions}
                </div>
              </div>
            ))}
          </div>

          {/* Generated Files Download */}
          {fixResult.generated_files && Object.keys(fixResult.generated_files).length > 0 && (
            <div className="mb-6">
              <h5 className="font-medium text-gray-900 mb-3">Generierte Dateien</h5>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {Object.keys(fixResult.generated_files).map(filename => (
                  <button
                    key={filename}
                    onClick={() => downloadFile(fixResult.fix_id, filename)}
                    className="flex items-center gap-2 p-3 border border-gray-300 rounded-md hover:bg-gray-50"
                  >
                    <Download className="w-4 h-4 text-blue-600" />
                    <span className="text-sm">{filename}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Implementation Guide */}
          {fixResult.implementation_guide && (
            <div className="bg-blue-50 border-l-4 border-blue-400 p-4">
              <h5 className="font-medium text-blue-800 mb-2">Implementierungsanleitung</h5>
              <div className="text-sm text-blue-700 space-y-1">
                {fixResult.implementation_guide.slice(0, 5).map((step, index) => (
                  <div key={index}>{step}</div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default AIFixer;