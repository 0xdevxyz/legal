'use client';

import React from 'react';

/**
 * IntegrationsSection - Integrationen und Kompatibilität
 */
export default function IntegrationsSection() {
  const integrations = [
    { name: 'WordPress', icon: '🔌' },
    { name: 'Shopify', icon: '🛒' },
    { name: 'Wix', icon: '🎨' },
    { name: 'Squarespace', icon: '📐' },
    { name: 'Webflow', icon: '🌊' },
    { name: 'HTML/CSS', icon: '💻' }
  ];

  return (
    <section className="py-20 bg-gradient-to-br from-purple-50 via-white to-blue-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold mb-4 bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
            Einfache Integration
          </h2>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Complyo funktioniert mit allen Plattformen. Ein einziger Code-Schnipsel genügt.
          </p>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-8">
          {integrations.map((integration) => (
            <div
              key={integration.name}
              className="flex flex-col items-center p-6 bg-white rounded-2xl shadow-lg hover:shadow-xl transition-all hover:-translate-y-1"
            >
              <div className="text-5xl mb-3">{integration.icon}</div>
              <div className="font-semibold text-gray-800">{integration.name}</div>
            </div>
          ))}
        </div>

        <div className="mt-16 max-w-3xl mx-auto">
          <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl p-8 shadow-2xl">
            <h3 className="text-white text-xl font-semibold mb-4">
              🚀 So einfach geht's:
            </h3>
            <pre className="bg-black/30 text-green-400 p-4 rounded-lg overflow-x-auto">
              <code>{`<script
  src="https://api.complyo.tech/api/widgets/accessibility.js"
  data-site-id="IHR-SITE-ID"
  data-auto-fix="true"
></script>`}</code>
            </pre>
            <p className="text-gray-300 mt-4 text-sm">
              ✨ Ein Skript-Tag - fertig! Das Widget lädt automatisch und macht Ihre Webseite barrierefrei.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
