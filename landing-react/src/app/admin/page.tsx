'use client';

import React, { useState, useEffect } from 'react';
import { TrendingUp, Users, Target, AlertCircle, RefreshCw } from 'lucide-react';

interface AnalyticsData {
  visitors: { professional: number; original: number; highConversion: number };
  conversions: { professional: number; original: number; highConversion: number };
}

export default function AdminDashboard() {
  const [analytics, setAnalytics] = useState<AnalyticsData>({
    visitors: { professional: 0, original: 0, highConversion: 0 },
    conversions: { professional: 0, original: 0, highConversion: 0 }
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'https://api.complyo.tech';

  const loadAnalytics = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Versuche echte Daten vom Backend zu laden
      const response = await fetch(`${API_BASE}/api/analytics/ab-test-summary`);
      
      if (response.ok) {
        const data = await response.json();
        setAnalytics(data);
      } else {
        throw new Error('Backend nicht verfügbar');
      }
    } catch (err) {
      console.error('Failed to load analytics:', err);
      setError('Backend-Daten nicht verfügbar. Zeige lokale Browser-Daten.');
      
      // Fallback: Zeige Daten aus localStorage (lokale Tracking-Daten)
      const storedVariant = localStorage.getItem('complyo_ab_variant');
      const mockData = {
        visitors: { 
          professional: storedVariant === 'professional' ? 1 : 0,
          original: storedVariant === 'original' ? 1 : 0, 
          highConversion: storedVariant === 'high-conversion' ? 1 : 0 
        },
        conversions: { professional: 0, original: 0, highConversion: 0 }
      };
      setAnalytics(mockData);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAnalytics();
    // Auto-refresh alle 30 Sekunden
    const interval = setInterval(loadAnalytics, 30000);
    return () => clearInterval(interval);
  }, []);

  const totalVisitors = analytics.visitors.professional + analytics.visitors.original + analytics.visitors.highConversion;
  const totalConversions = analytics.conversions.professional + analytics.conversions.original + analytics.conversions.highConversion;
  
  const conversionRateProfessional = analytics.visitors.professional > 0 
    ? (analytics.conversions.professional / analytics.visitors.professional * 100) 
    : 0;
  const conversionRateOriginal = analytics.visitors.original > 0
    ? (analytics.conversions.original / analytics.visitors.original * 100)
    : 0;
  const conversionRateHighConversion = analytics.visitors.highConversion > 0
    ? (analytics.conversions.highConversion / analytics.visitors.highConversion * 100)
    : 0;
  
  const bestRate = Math.max(conversionRateProfessional, conversionRateOriginal, conversionRateHighConversion);
  const improvement = bestRate > 0 ? bestRate - Math.min(conversionRateProfessional || 100, conversionRateOriginal || 100, conversionRateHighConversion || 100) : 0;

  if (loading && totalVisitors === 0) {
    return (
      <div className="min-h-screen bg-gray-900 text-white flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="w-12 h-12 text-blue-400 animate-spin mx-auto mb-4" />
          <p className="text-gray-400">Lade Analytics-Daten...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <div className="bg-gray-800 border-b border-gray-700">
        <div className="container mx-auto px-6 py-6 flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold">Complyo A/B Test Dashboard (3 Varianten)</h1>
            <p className="text-gray-400 mt-1">
              Live Performance Analytics 
              {error && <span className="text-orange-400"> · {error}</span>}
            </p>
          </div>
          <button
            onClick={loadAnalytics}
            disabled={loading}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Aktualisieren
          </button>
        </div>
      </div>

      <div className="container mx-auto px-6 py-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Total Visitors</p>
                <p className="text-3xl font-bold">{totalVisitors}</p>
              </div>
              <Users className="h-8 w-8 text-blue-400" />
            </div>
          </div>

          <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Total Conversions</p>
                <p className="text-3xl font-bold">{totalConversions}</p>
              </div>
              <Target className="h-8 w-8 text-green-400" />
            </div>
          </div>

          <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Best Rate</p>
                <p className="text-3xl font-bold">{bestRate.toFixed(1)}%</p>
              </div>
              <TrendingUp className="h-8 w-8 text-purple-400" />
            </div>
          </div>

          <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Improvement</p>
                <p className={`text-3xl font-bold ${improvement > 0 ? 'text-green-400' : 'text-gray-400'}`}>
                  {improvement > 0 ? '+' : ''}{improvement.toFixed(1)}%
                </p>
              </div>
              <AlertCircle className={`h-8 w-8 ${improvement > 0 ? 'text-green-400' : 'text-gray-400'}`} />
            </div>
          </div>
        </div>

        {bestRate > 0 && (
          <div className="mb-8 p-6 rounded-xl border-2 bg-green-900/20 border-green-500">
            <div className="text-center">
              <h2 className="text-2xl font-bold mb-2">
                🏆 {conversionRateProfessional === bestRate ? 'PROFESSIONAL' : conversionRateHighConversion === bestRate ? 'HIGH-CONVERSION' : 'ORIGINAL'} VARIANT GEWINNT!
              </h2>
              <p className="text-lg">
                {improvement > 0 && `${improvement.toFixed(1)}% bessere Performance als die schlechteste Variante`}
              </p>
            </div>
          </div>
        )}

        <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
          <h3 className="text-xl font-bold mb-6">Performance Comparison</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="border-b border-gray-700">
                  <th className="py-3 px-4 text-gray-400">Variant</th>
                  <th className="py-3 px-4 text-gray-400">Weight</th>
                  <th className="py-3 px-4 text-gray-400">Visitors</th>
                  <th className="py-3 px-4 text-gray-400">Conversions</th>
                  <th className="py-3 px-4 text-gray-400">Rate</th>
                  <th className="py-3 px-4 text-gray-400">Status</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b border-gray-700">
                  <td className="py-4 px-4">
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 bg-purple-500 rounded-full"></div>
                      Professional
                    </div>
                  </td>
                  <td className="py-4 px-4 text-gray-400">50%</td>
                  <td className="py-4 px-4 font-semibold">{analytics.visitors.professional}</td>
                  <td className="py-4 px-4 font-semibold">{analytics.conversions.professional}</td>
                  <td className="py-4 px-4 font-semibold">{conversionRateProfessional.toFixed(2)}%</td>
                  <td className="py-4 px-4">
                    {conversionRateProfessional === bestRate ? (
                      <span className="text-green-400 font-semibold">🏆 Winner</span>
                    ) : (
                      <span className="text-gray-400">-</span>
                    )}
                  </td>
                </tr>
                <tr className="border-b border-gray-700">
                  <td className="py-4 px-4">
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                      Original
                    </div>
                  </td>
                  <td className="py-4 px-4 text-gray-400">25%</td>
                  <td className="py-4 px-4 font-semibold">{analytics.visitors.original}</td>
                  <td className="py-4 px-4 font-semibold">{analytics.conversions.original}</td>
                  <td className="py-4 px-4 font-semibold">{conversionRateOriginal.toFixed(2)}%</td>
                  <td className="py-4 px-4">
                    {conversionRateOriginal === bestRate ? (
                      <span className="text-green-400 font-semibold">🏆 Winner</span>
                    ) : (
                      <span className="text-gray-400">-</span>
                    )}
                  </td>
                </tr>
                <tr>
                  <td className="py-4 px-4">
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                      High-Conversion
                    </div>
                  </td>
                  <td className="py-4 px-4 text-gray-400">25%</td>
                  <td className="py-4 px-4 font-semibold">{analytics.visitors.highConversion}</td>
                  <td className="py-4 px-4 font-semibold">{analytics.conversions.highConversion}</td>
                  <td className="py-4 px-4 font-semibold">{conversionRateHighConversion.toFixed(2)}%</td>
                  <td className="py-4 px-4">
                    {conversionRateHighConversion === bestRate ? (
                      <span className="text-green-400 font-semibold">🏆 Winner</span>
                    ) : (
                      <span className="text-gray-400">-</span>
                    )}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div className="mt-8 bg-gray-800 rounded-xl p-6 border border-gray-700">
          <h3 className="text-xl font-bold mb-4">Test URLs</h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <a href="/" className="bg-blue-600 hover:bg-blue-700 text-white p-4 rounded-lg text-center font-semibold transition-colors">
              🎲 Random (gewichtet)
            </a>
            <a href="/?variant=professional" className="bg-purple-600 hover:bg-purple-700 text-white p-4 rounded-lg text-center font-semibold transition-colors">
              ⭐ Professional
            </a>
            <a href="/?variant=original" className="bg-gray-600 hover:bg-gray-700 text-white p-4 rounded-lg text-center font-semibold transition-colors">
              📊 Original
            </a>
            <a href="/?variant=high-conversion" className="bg-red-600 hover:bg-red-700 text-white p-4 rounded-lg text-center font-semibold transition-colors">
              🔥 High-Conversion
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
