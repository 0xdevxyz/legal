'use client';

import React from 'react';
import { CheckCircle } from 'lucide-react';

/**
 * ComplianceBadges - Zeigt alle unterstützten Compliance-Standards
 */
export default function ComplianceBadges() {
  const standards = [
    {
      name: 'BFSG',
      fullName: 'Barrierefreiheitsstärkungsgesetz',
      description: 'Ab 2025 Pflicht für digitale Dienstleistungen',
      status: 'supported'
    },
    {
      name: 'DSGVO',
      fullName: 'Datenschutz-Grundverordnung',
      description: 'EU-weite Datenschutzanforderungen',
      status: 'supported'
    },
    {
      name: 'WCAG 2.1 AA',
      fullName: 'Web Content Accessibility Guidelines',
      description: 'Internationale Barrierefreiheits-Standards',
      status: 'supported'
    },
    {
      name: 'ePrivacy',
      fullName: 'ePrivacy-Richtlinie',
      description: 'Cookie-Consent und elektronische Kommunikation',
      status: 'supported'
    },
    {
      name: 'Cookie-Richtlinie',
      fullName: 'Cookie-Einwilligungspflicht',
      description: 'DSGVO-konforme Cookie-Banner',
      status: 'supported'
    },
    {
      name: 'Impressumspflicht',
      fullName: 'Telemediengesetz §5',
      description: 'Pflichtangaben für geschäftsmäßige Websites',
      status: 'supported'
    }
  ];

  return (
    <section className="bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900 text-white py-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-16">
          <h2 className="text-4xl font-bold mb-4">
            Vollständige Compliance-Abdeckung
          </h2>
          <p className="text-xl text-gray-300 max-w-3xl mx-auto">
            Alle relevanten deutschen und europäischen Gesetze in einem System
          </p>
        </div>
        
        {/* Badges Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {standards.map((standard, index) => (
            <div
              key={index}
              className="bg-white/10 backdrop-blur-sm border border-white/20 rounded-2xl p-6 hover:bg-white/15 transition-all group"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="bg-green-500/20 border border-green-400 rounded-full px-4 py-1 text-sm font-semibold text-green-400">
                  {standard.name}
                </div>
                <CheckCircle className="w-6 h-6 text-green-400 flex-shrink-0" />
              </div>
              
              <h3 className="text-lg font-bold mb-2 group-hover:text-blue-300 transition-colors">
                {standard.fullName}
              </h3>
              
              <p className="text-sm text-gray-300">
                {standard.description}
              </p>
            </div>
          ))}
        </div>
        
        {/* Bottom Stats */}
        <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-8 text-center">
          <div>
            <div className="text-4xl font-bold mb-2">127</div>
            <div className="text-gray-400">Prüfpunkte</div>
          </div>
          <div>
            <div className="text-4xl font-bold mb-2">6</div>
            <div className="text-gray-400">Compliance-Bereiche</div>
          </div>
          <div>
            <div className="text-4xl font-bold mb-2">24/7</div>
            <div className="text-gray-400">Monitoring</div>
          </div>
        </div>
      </div>
    </section>
  );
}

