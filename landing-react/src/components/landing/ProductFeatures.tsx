'use client';

import React from 'react';
import { BarChart3, Code, TrendingUp, Shield, Zap, FileCheck } from 'lucide-react';

/**
 * ProductFeatures - Zeigt die 3 Hauptfeatures mit visuellen Mockups
 */
export default function ProductFeatures() {
  const features = [
    {
      icon: BarChart3,
      title: 'Compliance-Audit',
      description: 'Detailliertes Dashboard mit Echtzeitbewertung Ihrer Website nach WCAG 2.1, DSGVO und BFSG.',
      color: 'from-blue-500 to-cyan-500',
      stats: [
        { label: 'Score-Genauigkeit', value: '99%' },
        { label: 'Prüfpunkte', value: '127' }
      ]
    },
    {
      icon: Code,
      title: 'KI-Fix Generator',
      description: 'Copy-Paste Code mit präziser Lokalisierung und Schritt-für-Schritt-Anleitung zur Umsetzung.',
      color: 'from-purple-500 to-pink-500',
      stats: [
        { label: 'Fix-Genauigkeit', value: '94%' },
        { label: 'Ø Umsetzungszeit', value: '12 Min' }
      ]
    },
    {
      icon: TrendingUp,
      title: 'Score-Verlauf',
      description: 'Verfolgen Sie Ihre Compliance-Verbesserungen über Zeit mit detailliertem Tracking und Trends.',
      color: 'from-green-500 to-emerald-500',
      stats: [
        { label: 'Ø Verbesserung', value: '+47%' },
        { label: 'Tracking', value: '24/7' }
      ]
    }
  ];

  return (
    <section className="bg-gray-900 text-white py-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-16">
          <h2 className="text-4xl font-bold mb-4">
            Alles was Sie für echte Compliance brauchen
          </h2>
          <p className="text-xl text-gray-400 max-w-3xl mx-auto">
            Professionelle Tools für nachhaltigen Rechtsschutz – keine Overlay-Lösungen
          </p>
        </div>
        
        {/* Features Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {features.map((feature, index) => (
            <div
              key={index}
              className="bg-gray-800 rounded-2xl p-8 border border-gray-700 hover:border-gray-600 transition-all group"
            >
              {/* Icon */}
              <div className={`w-16 h-16 bg-gradient-to-br ${feature.color} rounded-2xl flex items-center justify-center mb-6 transform group-hover:scale-110 transition-transform`}>
                <feature.icon className="w-8 h-8 text-white" />
              </div>
              
              {/* Content */}
              <h3 className="text-2xl font-bold mb-3">{feature.title}</h3>
              <p className="text-gray-400 mb-6 leading-relaxed">
                {feature.description}
              </p>
              
              {/* Stats */}
              <div className="grid grid-cols-2 gap-4 pt-6 border-t border-gray-700">
                {feature.stats.map((stat, statIndex) => (
                  <div key={statIndex}>
                    <div className={`text-2xl font-bold bg-gradient-to-r ${feature.color} bg-clip-text text-transparent`}>
                      {stat.value}
                    </div>
                    <div className="text-sm text-gray-500">{stat.label}</div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
        
        {/* Additional Features */}
        <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="flex items-start gap-4 bg-gray-800/50 rounded-xl p-6 border border-gray-700">
            <Shield className="w-8 h-8 text-blue-400 flex-shrink-0 mt-1" />
            <div>
              <h4 className="font-semibold mb-2">Rechtssicher mit eRecht24</h4>
              <p className="text-sm text-gray-400">
                Automatische Integration von rechtssicheren Impressum- und Datenschutztexten
              </p>
            </div>
          </div>
          
          <div className="flex items-start gap-4 bg-gray-800/50 rounded-xl p-6 border border-gray-700">
            <Zap className="w-8 h-8 text-yellow-400 flex-shrink-0 mt-1" />
            <div>
              <h4 className="font-semibold mb-2">Quick Wins priorisiert</h4>
              <p className="text-sm text-gray-400">
                KI identifiziert die wichtigsten Fixes mit dem besten Kosten-Nutzen-Verhältnis
              </p>
            </div>
          </div>
          
          <div className="flex items-start gap-4 bg-gray-800/50 rounded-xl p-6 border border-gray-700">
            <FileCheck className="w-8 h-8 text-green-400 flex-shrink-0 mt-1" />
            <div>
              <h4 className="font-semibold mb-2">Export & Dokumentation</h4>
              <p className="text-sm text-gray-400">
                PDF/Excel-Export aller Analysen und Fixes für Ihre Unterlagen
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

