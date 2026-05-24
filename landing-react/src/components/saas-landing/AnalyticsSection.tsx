'use client';
import React from 'react';
import { TrendingUp, ArrowRight } from 'lucide-react';

export default function AnalyticsSection() {
  const months = ['Jan','Feb','Mär','Apr','Mai','Jun'];
  const scores = [42, 55, 63, 71, 85, 94];

  return (
    <section className="bg-gradient-to-br from-blue-50 via-indigo-50 to-white py-24">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">

          {/* LEFT: Text + Stats */}
          <div>
            <p className="text-sm font-semibold text-blue-600 uppercase tracking-widest mb-3">Analytics & Reporting</p>
            <h2 className="font-heading text-3xl sm:text-4xl font-extrabold text-gray-900 mb-5 leading-tight">
              Gain smarter analytics<br />insights over time
            </h2>
            <p className="text-lg text-gray-500 mb-10 leading-relaxed">
              Verfolgen Sie Ihren Compliance-Fortschritt über Monate. Complyo zeigt Ihnen genau, wo Sie standen und wohin Sie sich verbessert haben.
            </p>

            {/* Stats Grid */}
            <div className="grid grid-cols-3 gap-4">
              {[
                { val: '94%', label: 'Ø Compliance Score', color: 'text-blue-600' },
                { val: '127', label: 'Fixes automatisch', color: 'text-green-600' },
                { val: '18h', label: 'Zeit gespart', color: 'text-purple-600' },
              ].map((stat, i) => (
                <div key={i} className="bg-white rounded-2xl p-5 shadow-sm border border-gray-100 text-center">
                  <p className={`text-3xl font-extrabold ${stat.color}`}>{stat.val}</p>
                  <p className="text-xs text-gray-500 mt-1">{stat.label}</p>
                </div>
              ))}
            </div>

            <a href="https://app.complyo.de/register" className="inline-flex items-center gap-2 mt-8 text-blue-600 font-semibold text-sm hover:gap-3 transition-all">
              Meine Website analysieren <ArrowRight className="w-4 h-4" />
            </a>
          </div>

          {/* RIGHT: Chart Mock */}
          <div className="relative">
            <div className="absolute inset-0 bg-white rounded-3xl blur-xl opacity-80 scale-95" />
            <div className="relative bg-white rounded-2xl shadow-xl border border-gray-100 p-6">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <p className="text-sm font-semibold text-gray-900">Compliance Score Verlauf</p>
                  <p className="text-xs text-gray-400">Letzte 6 Monate</p>
                </div>
                <div className="flex items-center gap-1.5 text-green-600 bg-green-50 text-xs font-semibold px-3 py-1.5 rounded-full">
                  <TrendingUp className="w-3.5 h-3.5" />
                  +52 Punkte
                </div>
              </div>

              {/* Bar Chart */}
              <div className="flex items-end justify-between gap-3 h-40 mb-3">
                {months.map((month, i) => (
                  <div key={i} className="flex-1 flex flex-col items-center gap-1.5">
                    <span className="text-xs text-gray-500 font-semibold">{scores[i]}%</span>
                    <div className="w-full rounded-lg transition-all" style={{
                      height: `${(scores[i]/100)*120}px`,
                      background: i === months.length-1
                        ? 'linear-gradient(180deg,#3B82F6,#6366F1)'
                        : '#E0E7FF'
                    }} />
                  </div>
                ))}
              </div>
              <div className="flex justify-between gap-3">
                {months.map((m,i) => (
                  <span key={i} className="flex-1 text-center text-xs text-gray-400">{m}</span>
                ))}
              </div>

              {/* Legend */}
              <div className="mt-5 pt-4 border-t border-gray-100 grid grid-cols-2 gap-3">
                {[
                  {label:'DSGVO', val:'98%', color:'bg-blue-500'},
                  {label:'Cookie', val:'91%', color:'bg-indigo-500'},
                  {label:'WCAG', val:'88%', color:'bg-purple-500'},
                  {label:'Impressum', val:'100%', color:'bg-green-500'},
                ].map((item,i) => (
                  <div key={i} className="flex items-center gap-2">
                    <div className={`w-2.5 h-2.5 rounded-full ${item.color}`} />
                    <span className="text-xs text-gray-500">{item.label}</span>
                    <span className="text-xs font-bold text-gray-800 ml-auto">{item.val}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

        </div>
      </div>
    </section>
  );
}
