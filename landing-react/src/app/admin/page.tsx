'use client';

import React, { useState, useEffect } from 'react';
import { TrendingUp, Users, Target, AlertCircle } from 'lucide-react';

export default function AdminDashboard() {
  const [analytics, setAnalytics] = useState({
    visitors: { original: 456, highConversion: 623 },
    conversions: { original: 23, highConversion: 47 }
  });

  const conversionRateOriginal = (analytics.conversions.original / analytics.visitors.original * 100);
  const conversionRateHighConversion = (analytics.conversions.highConversion / analytics.visitors.highConversion * 100);
  const improvement = conversionRateHighConversion - conversionRateOriginal;

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <div className="bg-gray-800 border-b border-gray-700">
        <div className="container mx-auto px-6 py-6">
          <h1 className="text-3xl font-bold">Complyo A/B Test Dashboard</h1>
          <p className="text-gray-400 mt-1">Live Performance Analytics</p>
        </div>
      </div>

      <div className="container mx-auto px-6 py-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Total Visitors</p>
                <p className="text-3xl font-bold">{analytics.visitors.original + analytics.visitors.highConversion}</p>
              </div>
              <Users className="h-8 w-8 text-blue-400" />
            </div>
          </div>

          <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Total Conversions</p>
                <p className="text-3xl font-bold">{analytics.conversions.original + analytics.conversions.highConversion}</p>
              </div>
              <Target className="h-8 w-8 text-green-400" />
            </div>
          </div>

          <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Best Rate</p>
                <p className="text-3xl font-bold">{Math.max(conversionRateOriginal, conversionRateHighConversion).toFixed(1)}%</p>
              </div>
              <TrendingUp className="h-8 w-8 text-purple-400" />
            </div>
          </div>

          <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Improvement</p>
                <p className={`text-3xl font-bold ${improvement > 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {improvement > 0 ? '+' : ''}{improvement.toFixed(1)}%
                </p>
              </div>
              <AlertCircle className={`h-8 w-8 ${improvement > 0 ? 'text-green-400' : 'text-red-400'}`} />
            </div>
          </div>
        </div>

        <div className="mb-8 p-6 rounded-xl border-2 bg-green-900/20 border-green-500">
          <div className="text-center">
            <h2 className="text-2xl font-bold mb-2">
              🏆 {improvement > 0 ? 'HIGH-CONVERSION VARIANT WINS!' : 'ORIGINAL VARIANT WINS!'}
            </h2>
            <p className="text-lg">
              {improvement > 0 ? 'High-Conversion' : 'Original'} variant performs {Math.abs(improvement).toFixed(1)}% better
            </p>
          </div>
        </div>

        <div className="bg-gray-800 rounded-xl p-6 border border-gray-700">
          <h3 className="text-xl font-bold mb-6">Performance Comparison</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="border-b border-gray-700">
                  <th className="py-3 px-4 text-gray-400">Variant</th>
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
                      <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                      Original
                    </div>
                  </td>
                  <td className="py-4 px-4 font-semibold">{analytics.visitors.original}</td>
                  <td className="py-4 px-4 font-semibold">{analytics.conversions.original}</td>
                  <td className="py-4 px-4 font-semibold">{conversionRateOriginal.toFixed(2)}%</td>
                  <td className="py-4 px-4">
                    <span className="text-gray-400">Baseline</span>
                  </td>
                </tr>
                <tr>
                  <td className="py-4 px-4">
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                      High-Conversion
                    </div>
                  </td>
                  <td className="py-4 px-4 font-semibold">{analytics.visitors.highConversion}</td>
                  <td className="py-4 px-4 font-semibold">{analytics.conversions.highConversion}</td>
                  <td className="py-4 px-4 font-semibold">{conversionRateHighConversion.toFixed(2)}%</td>
                  <td className="py-4 px-4">
                    <span className="text-green-400 font-semibold">Winner (+{improvement.toFixed(1)}%)</span>
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
              🎲 Random (50/50)
            </a>
            <a href="/?variant=original" className="bg-gray-600 hover:bg-gray-700 text-white p-4 rounded-lg text-center font-semibold transition-colors">
              📊 Original
            </a>
            <a href="/?variant=high-conversion" className="bg-red-600 hover:bg-red-700 text-white p-4 rounded-lg text-center font-semibold transition-colors">
              🔥 High-Conversion
            </a>
            <button 
              onClick={() => navigator.clipboard.writeText(window.location.origin)}
              className="bg-purple-600 hover:bg-purple-700 text-white p-4 rounded-lg text-center font-semibold transition-colors"
            >
              📋 Copy URL
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
