'use client';

import React from 'react';

const getAppUrl = (path: string) => {
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      return `http://localhost:3000${path}`;
    }
  }
  return `https://app.complyo.tech${path}`;
};

export default function CTAModern() {
  return (
    <section className="py-20 bg-gradient-to-br from-purple-600 via-blue-600 to-purple-700">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <h2 className="text-4xl md:text-5xl font-bold text-white mb-6">
          Bereit für eine barrierefreie Website?
        </h2>
        <p className="text-xl text-purple-100 mb-8 max-w-2xl mx-auto">
          Starten Sie jetzt kostenlos und machen Sie Ihre Website für alle zugänglich.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <a
            href={getAppUrl('/register?plan=complete')}
            className="px-8 py-4 bg-white text-purple-600 rounded-full font-semibold text-lg hover:bg-gray-100 transition-all hover:scale-105 shadow-xl"
          >
            Kostenlos starten
          </a>
          <a
            href="#pricing"
            className="px-8 py-4 bg-purple-800 text-white rounded-full font-semibold text-lg hover:bg-purple-900 transition-all hover:scale-105 shadow-xl"
          >
            Preise ansehen
          </a>
        </div>
      </div>
    </section>
  );
}
