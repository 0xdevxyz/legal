import React, { useState } from 'react';
import { AlertTriangle, Calculator, TrendingUp, TrendingDown, Shield, Zap } from 'lucide-react';

const RiskCalculator = ({ scanResult, onRiskCalculated }) => {
  const [calculating, setCalculating] = useState(false);
  const [riskAssessment, setRiskAssessment] = useState(null);
  const [companyProfile, setCompanyProfile] = useState({
    company_size: 'small',
    industry: 'general',
    data_sensitivity: 'basic',
    revenue: 'small'
  });

  const calculateRisk = async () => {
    try {
      setCalculating(true);
      
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'https://api.complyo.tech'}/api/risk-assessment`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        },
        body: JSON.stringify({
          scan_id: scanResult.id,
          company_profile: companyProfile
        })
      });

      if (!response.ok) {
        throw new Error('Risk calculation failed');
      }

      const result = await response.json();
      setRiskAssessment(result.risk_assessment);
      
      if (onRiskCalculated) {
        onRiskCalculated(result);
      }
      
    } catch (error) {
      console.error('Risk calculation error:', error);
    } finally {
      setCalculating(false);
    }
  };

  const getRiskLevelColor = (level) => {
    switch (level) {
      case 'critical': return 'text-red-600 bg-red-100';
      case 'high': return 'text-orange-600 bg-orange-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'low': return 'text-green-600 bg-green-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getRiskLevelIcon = (level) => {
    switch (level) {
      case 'critical': return <AlertTriangle className="w-5 h-5 text-red-600" />;
      case 'high': return <TrendingUp className="w-5 h-5 text-orange-600" />;
      case 'medium': return <TrendingUp className="w-5 h-5 text-yellow-600" />;
      case 'low': return <Shield className="w-5 h-5 text-green-600" />;
      default: return <Calculator className="w-5 h-5" />;
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <Calculator className="w-5 h-5" />
          Abmahn-Risiko-Kalkulator
        </h3>
        <button
          onClick={calculateRisk}
          disabled={calculating}
          className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
        >
          {calculating ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
              Berechnung...
            </>
          ) : (
            <>
              <Calculator className="w-4 h-4" />
              Risiko berechnen
            </>
          )}
        </button>
      </div>

      {/* Company Profile Form */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Unternehmensgröße
          </label>
          <select
            value={companyProfile.company_size}
            onChange={(e) => setCompanyProfile({...companyProfile, company_size: e.target.value})}
            className="w-full border border-gray-300 rounded-md px-3 py-2"
          >
            <option value="startup">Startup (< 10 MA)</option>
            <option value="small">Klein (< 50 MA)</option>
            <option value="medium">Mittel (50-250 MA)</option>
            <option value="large">Groß (250-1000 MA)</option>
            <option value="enterprise">Konzern (> 1000 MA)</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Branche
          </label>
          <select
            value={companyProfile.industry}
            onChange={(e) => setCompanyProfile({...companyProfile, industry: e.target.value})}
            className="w-full border border-gray-300 rounded-md px-3 py-2"
          >
            <option value="general">Allgemein</option>
            <option value="ecommerce">E-Commerce</option>
            <option value="healthcare">Gesundheitswesen</option>
            <option value="finance">Finanzdienstleistung</option>
            <option value="legal">Recht/Beratung</option>
            <option value="technology">Technologie</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Datensensitivität
          </label>
          <select
            value={companyProfile.data_sensitivity}
            onChange={(e) => setCompanyProfile({...companyProfile, data_sensitivity: e.target.value})}
            className="w-full border border-gray-300 rounded-md px-3 py-2"
          >
            <option value="basic">Standard (Kontaktdaten)</option>
            <option value="personal">Persönlich (Profile, etc.)</option>
            <option value="sensitive">Sensibel (Gesundheit, Finanzen)</option>
            <option value="special">Besonders (Biometrie, etc.)</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Umsatzgröße
          </label>
          <select
            value={companyProfile.revenue}
            onChange={(e) => setCompanyProfile({...companyProfile, revenue: e.target.value})}
            className="w-full border border-gray-300 rounded-md px-3 py-2"
          >
            <option value="micro">< 100k €</option>
            <option value="small">< 1M €</option>
            <option value="medium">< 10M €</option>
            <option value="large">< 100M €</option>
            <option value="enterprise">> 100M €</option>
          </select>
        </div>
      </div>

      {/* Risk Assessment Results */}
      {riskAssessment && (
        <div className="border-t pt-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900">
                {riskAssessment.base_risk_euro.toLocaleString()} €
              </div>
              <div className="text-sm text-gray-600">Basis-Risiko</div>
            </div>
            
            <div className="text-center">
              <div className="text-3xl font-bold text-red-600">
                {riskAssessment.adjusted_risk_euro.toLocaleString()} €
              </div>
              <div className="text-sm text-gray-600">Angepasstes Risiko</div>
            </div>
            
            <div className="text-center">
              <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium ${getRiskLevelColor(riskAssessment.risk_level)}`}>
                {getRiskLevelIcon(riskAssessment.risk_level)}
                {riskAssessment.risk_level.toUpperCase()}
              </div>
            </div>
          </div>

          {/* Risk Factors */}
          {riskAssessment.risk_factors && riskAssessment.risk_factors.length > 0 && (
            <div className="mb-6">
              <h4 className="font-medium text-gray-900 mb-3">Risikofaktoren</h4>
              <div className="space-y-2">
                {riskAssessment.risk_factors.map((factor, index) => (
                  <div key={index} className="flex items-center justify-between bg-gray-50 p-3 rounded-md">
                    <div>
                      <div className="font-medium text-sm">{factor.name}</div>
                      <div className="text-xs text-gray-600">{factor.description}</div>
                    </div>
                    <div className={`font-bold ${factor.multiplier > 1 ? 'text-red-600' : factor.multiplier < 1 ? 'text-green-600' : 'text-gray-600'}`}>
                      ×{factor.multiplier.toFixed(2)}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Recommendations */}
          {riskAssessment.recommendations && riskAssessment.recommendations.length > 0 && (
            <div>
              <h4 className="font-medium text-gray-900 mb-3">Empfehlungen</h4>
              <div className="bg-blue-50 border-l-4 border-blue-400 p-4">
                <ul className="space-y-2">
                  {riskAssessment.recommendations.map((rec, index) => (
                    <li key={index} className="text-sm text-blue-800">
                      {rec}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default RiskCalculator;