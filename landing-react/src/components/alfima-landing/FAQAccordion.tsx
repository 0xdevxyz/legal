'use client';

import React, { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';

const faqs = [
  {
    question: 'Ist Complyo wirklich DSGVO-konform?',
    answer:
      'Ja, absolut. Complyo wurde von spezialisierten IT-Anwälten entwickelt und wird regelmäßig auf aktuelle Rechtsprechung und Gesetzesänderungen geprüft. Alle Vorlagen sind anwaltlich geprüft und werden automatisch aktualisiert.'
  },
  {
    question: 'Wie schnell kann ich den Cookie-Banner einrichten?',
    answer:
      'Die Integration dauert nur 5 Minuten. Du fügst einfach einen Script-Tag in deine Website ein oder nutzt unser WordPress/Shopify Plugin. Der Banner ist sofort aktiv und DSGVO-konform.'
  },
  {
    question: 'Was passiert, wenn sich Gesetze ändern?',
    answer:
      'Wir überwachen kontinuierlich die Rechtslage und passen alle Vorlagen und Funktionen automatisch an. Du wirst über wichtige Änderungen informiert und musst dich um nichts kümmern.'
  },
  {
    question: 'Unterstützt Complyo Google Consent Mode v2?',
    answer:
      'Ja, Complyo unterstützt Google Consent Mode v2 vollständig. Die Integration mit Google Analytics, Google Ads und anderen Google-Diensten funktioniert nahtlos und ist vollständig DSGVO-konform.'
  },
  {
    question: 'Kann ich mehrere Websites verwalten?',
    answer:
      'Ja, mit dem Professional-Plan kannst du bis zu 5 Websites zentral verwalten. Für mehr Websites bieten wir individuelle Enterprise-Lösungen an. Alle Websites werden in einem Dashboard verwaltet.'
  },
  {
    question: 'Wie funktioniert der Support?',
    answer:
      'Wir bieten E-Mail-Support für alle Kunden. Professional und Enterprise Kunden erhalten Prioritäts-Support mit schnelleren Antwortzeiten. Bei rechtlichen Fragen beraten wir dich gerne.'
  }
];

export default function FAQAccordion() {
  const [openIndex, setOpenIndex] = useState<number | null>(0);

  return (
    <section id="faq" className="bg-white py-20">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <p className="text-sm uppercase tracking-[0.4em] text-slate-500">FAQ</p>
          <h2 className="text-4xl font-bold mt-4">Häufig gestellte Fragen</h2>
          <p className="text-lg text-slate-500 mt-3">
            Alles, was du über Complyo und DSGVO-Compliance wissen musst.
          </p>
        </div>

        <div className="space-y-4">
          {faqs.map((faq, index) => (
            <div key={index} className="rounded-3xl border border-slate-100 bg-slate-50 shadow-sm">
              <button
                onClick={() => setOpenIndex(openIndex === index ? null : index)}
                className="w-full flex items-center justify-between px-6 py-5 text-left text-lg font-semibold text-slate-900 transition hover:bg-white rounded-3xl"
              >
                <span>{faq.question}</span>
                {openIndex === index ? (
                  <ChevronUp className="w-5 h-5 text-slate-500" />
                ) : (
                  <ChevronDown className="w-5 h-5 text-slate-500" />
                )}
              </button>
              {openIndex === index && (
                <div className="border-t border-slate-100 px-6 py-5 text-base text-slate-600">
                  {faq.answer}
                </div>
              )}
            </div>
          ))}
        </div>

        <div className="mt-12 text-center">
          <p className="text-sm text-slate-500 mb-3">Weitere Fragen? Wir helfen gern.</p>
          <a
            href="mailto:support@complyo.tech"
            className="inline-flex items-center gap-2 rounded-full border border-slate-300 px-6 py-3 text-sm font-semibold text-slate-900 transition hover:bg-slate-100"
          >
            Support kontaktieren
          </a>
        </div>
      </div>
    </section>
  );
}
