'use client';
import React from 'react';

const integrations = [
  { name: 'WordPress', emoji: '🔵', desc: 'Plugin verfügbar' },
  { name: 'Shopify', emoji: '🟢', desc: 'App verfügbar' },
  { name: 'Joomla', emoji: '🟠', desc: 'Extension verfügbar' },
  { name: 'GitHub', emoji: '⚫', desc: 'CI/CD Integration' },
  { name: 'Stripe', emoji: '🟣', desc: 'Zahlungsabwicklung' },
  { name: 'Google Analytics', emoji: '🔴', desc: 'Consent Mode' },
  { name: 'TYPO3', emoji: '🟡', desc: 'Extension verfügbar' },
  { name: 'Webflow', emoji: '🔷', desc: 'Embed-Code' },
];

export default function IntegrationsSection() {
  return (
    <section className="bg-gray-50 py-24" id="integrations">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">

          {/* LEFT: Text */}
          <div>
            <p className="text-sm font-semibold text-blue-600 uppercase tracking-widest mb-3">Integrationen</p>
            <h2 className="font-heading text-3xl sm:text-4xl font-extrabold text-gray-900 mb-5 leading-tight">
              Connect your<br />favorite tools
            </h2>
            <p className="text-lg text-gray-500 mb-8 leading-relaxed">
              Complyo lässt sich nahtlos in Ihre bestehende Infrastruktur integrieren. WordPress-Plugin, Joomla-Extension oder einfacher Embed-Code – in wenigen Minuten einsatzbereit.
            </p>
            <div className="space-y-3">
              {['Einfache Integration per Copy-Paste Code', 'Offizielle Plugins für die größten CMS', 'REST API für individuelle Integrationen', 'Webhook-Unterstützung für Automatisierungen'].map((item, i) => (
                <div key={i} className="flex items-center gap-2.5 text-sm text-gray-600">
                  <div className="w-1.5 h-1.5 bg-blue-600 rounded-full flex-shrink-0" />
                  {item}
                </div>
              ))}
            </div>
          </div>

          {/* RIGHT: Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-2 xl:grid-cols-4 gap-3">
            {integrations.map((item, i) => (
              <div key={i} className="bg-white rounded-2xl p-4 border border-gray-100 shadow-sm hover:shadow-md transition-shadow text-center">
                <div className="text-3xl mb-2">{item.emoji}</div>
                <p className="text-sm font-bold text-gray-800">{item.name}</p>
                <p className="text-xs text-gray-400 mt-0.5">{item.desc}</p>
              </div>
            ))}
          </div>

        </div>
      </div>
    </section>
  );
}
