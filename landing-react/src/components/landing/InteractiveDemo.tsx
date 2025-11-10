'use client';

import React, { useState } from 'react';
import { Shield, Cookie, FileText, CheckCircle, AlertTriangle } from 'lucide-react';

/**
 * InteractiveDemo - Interaktive Tabs mit Live-Demos
 */
export default function InteractiveDemo() {
  const [activeTab, setActiveTab] = useState(0);

  const tabs = [
    {
      id: 'wcag',
      name: 'WCAG Audit',
      icon: Shield,
      color: 'blue',
      content: {
        title: 'WCAG 2.1 AA Compliance-Check',
        description: 'Automatische Prüfung aller 127 Prüfpunkte',
        mockData: [
          { category: 'Barrierefreiheit', issues: 8, severity: 'critical', status: 'Kritisch' },
          { category: 'Kontrast', issues: 3, severity: 'warning', status: 'Warnung' },
          { category: 'Tastatur-Navigation', issues: 12, severity: 'critical', status: 'Kritisch' },
          { category: 'Alt-Texte', issues: 5, severity: 'warning', status: 'Warnung' },
          { category: 'Formular-Labels', issues: 0, severity: 'success', status: '✓ Bestanden' }
        ]
      }
    },
    {
      id: 'cookies',
      name: 'Cookie-Scanner',
      icon: Cookie,
      color: 'purple',
      content: {
        title: 'Erkannte Cookies & Tracking',
        description: 'DSGVO-konforme Cookie-Analyse',
        mockData: [
          { name: 'Google Analytics (_ga)', type: 'Marketing', consent: 'Erforderlich', status: 'critical' },
          { name: 'Session Cookie', type: 'Notwendig', consent: 'Nicht erforderlich', status: 'success' },
          { name: 'Facebook Pixel', type: 'Marketing', consent: 'Erforderlich', status: 'critical' },
          { name: 'Matomo (_pk)', type: 'Analyse', consent: 'Erforderlich', status: 'warning' }
        ]
      }
    },
    {
      id: 'erecht24',
      name: 'eRecht24 Texte',
      icon: FileText,
      color: 'green',
      content: {
        title: 'Rechtssichere Dokumente',
        description: 'Automatisch generierte Rechtstexte',
        mockData: [
          { name: 'Impressum', status: 'success', updated: '12.10.2025' },
          { name: 'Datenschutzerklärung', status: 'success', updated: '12.10.2025' },
          { name: 'Cookie-Richtlinie', status: 'success', updated: '12.10.2025' },
          { name: 'AGB', status: 'warning', updated: '15.09.2025', note: 'Update verfügbar' }
        ]
      }
    }
  ];

  const activeContent = tabs[activeTab].content;

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'text-red-600 bg-red-100';
      case 'warning': return 'text-yellow-600 bg-yellow-100';
      case 'success': return 'text-green-600 bg-green-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  return (
    <section className="bg-white py-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold text-gray-900 mb-4">
            Interaktive Funktionsübersicht
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Erkunden Sie die leistungsstarken Analyse-Tools von Complyo
          </p>
        </div>
        
        {/* Tabs */}
        <div className="flex flex-col lg:flex-row gap-6">
          {/* Tab Buttons */}
          <div className="lg:w-1/4 space-y-2">
            {tabs.map((tab, index) => {
              const Icon = tab.icon;
              const isActive = activeTab === index;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(index)}
                  className={`w-full flex items-center gap-3 p-4 rounded-xl transition-all text-left ${
                    isActive
                      ? `bg-${tab.color}-600 text-white shadow-lg scale-105`
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  <Icon className="w-6 h-6 flex-shrink-0" />
                  <span className="font-semibold">{tab.name}</span>
                </button>
              );
            })}
          </div>
          
          {/* Tab Content */}
          <div className="lg:w-3/4">
            <div className="bg-gray-50 rounded-2xl p-8 border-2 border-gray-200 min-h-96">
              <h3 className="text-2xl font-bold text-gray-900 mb-2">
                {activeContent.title}
              </h3>
              <p className="text-gray-600 mb-6">
                {activeContent.description}
              </p>
              
              {/* WCAG Tab */}
              {activeTab === 0 && (
                <div className="space-y-3">
                  {activeContent.mockData.map((item: any, index: number) => (
                    <div
                      key={index}
                      className="bg-white rounded-lg p-4 border border-gray-200 flex items-center justify-between"
                    >
                      <div className="flex-1">
                        <div className="font-semibold text-gray-900">{item.category}</div>
                        <div className="text-sm text-gray-600">{item.issues} gefundene Issues</div>
                      </div>
                      <span className={`px-4 py-2 rounded-full text-sm font-semibold ${getSeverityColor(item.severity)}`}>
                        {item.status}
                      </span>
                    </div>
                  ))}
                </div>
              )}
              
              {/* Cookie Tab */}
              {activeTab === 1 && (
                <div className="space-y-3">
                  {activeContent.mockData.map((item: any, index: number) => (
                    <div
                      key={index}
                      className="bg-white rounded-lg p-4 border border-gray-200"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <div className="font-semibold text-gray-900">{item.name}</div>
                        <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getSeverityColor(item.status)}`}>
                          {item.type}
                        </span>
                      </div>
                      <div className="text-sm text-gray-600">
                        Einwilligung: <span className="font-medium">{item.consent}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
              
              {/* eRecht24 Tab */}
              {activeTab === 2 && (
                <div className="space-y-3">
                  {activeContent.mockData.map((item: any, index: number) => (
                    <div
                      key={index}
                      className="bg-white rounded-lg p-4 border border-gray-200 flex items-center justify-between"
                    >
                      <div>
                        <div className="font-semibold text-gray-900 mb-1">{item.name}</div>
                        <div className="text-sm text-gray-600">
                          Letztes Update: {item.updated}
                        </div>
                        {item.note && (
                          <div className="text-sm text-yellow-600 mt-1">⚠️ {item.note}</div>
                        )}
                      </div>
                      {item.status === 'success' ? (
                        <CheckCircle className="w-6 h-6 text-green-500" />
                      ) : (
                        <AlertTriangle className="w-6 h-6 text-yellow-500" />
                      )}
                    </div>
                  ))}
                </div>
              )}
              
              {/* CTA */}
              <div className="mt-6 pt-6 border-t border-gray-200">
                <a
                  href="/register"
                  className="inline-flex items-center gap-2 text-blue-600 hover:text-blue-700 font-semibold"
                >
                  Jetzt selbst testen →
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

