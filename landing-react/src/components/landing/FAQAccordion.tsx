'use client';

import React, { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';

/**
 * FAQAccordion - Häufig gestellte Fragen
 */
export default function FAQAccordion() {
  const [openIndex, setOpenIndex] = useState<number | null>(0);

  const faqs = [
    {
      question: 'Ist Complyo WCAG 2.1 AA konform?',
      answer: 'Ja, Complyo prüft Ihre Website nach allen Kriterien der WCAG 2.1 Level AA. Unser Scanner analysiert über 127 Prüfpunkte und gibt Ihnen konkrete Handlungsempfehlungen mit Code-Beispielen für jedes identifizierte Problem.'
    },
    {
      question: 'Was ist der Unterschied zu Eye-Able® und anderen Overlay-Lösungen?',
      answer: 'Im Gegensatz zu Overlay-Widgets wie Eye-Able® bietet Complyo echte Code-Fixes. Das bedeutet: Sie passen Ihren tatsächlichen Quellcode an, statt ein Widget einzubinden. Das Resultat ist nachhaltige Compliance ohne Abhängigkeit von Drittanbietern, bessere Performance und echte Barrierefreiheit statt kosmetischer Korrekturen.'
    },
    {
      question: 'Wie integriere ich Complyo in meine Website?',
      answer: 'Für die Analyse benötigen Sie keine Integration. Einfach URL eingeben und scannen. Die KI-generierten Fixes erhalten Sie als Copy-Paste Code mit genauer Lokalisierung (Datei, Zeile). Sie implementieren diese direkt in Ihrem Quellcode – ohne externe Dependencies.'
    },
    {
      question: 'Was passiert nach der KI-Optimierung?',
      answer: 'Nach Implementierung der Fixes können Sie einen neuen Scan durchführen, um Ihre Verbesserungen zu messen. Der Score-Verlauf zeigt Ihnen die Entwicklung über Zeit. Im DIY-Plan haben Sie unbegrenzte Analysen – beim Expertenservice übernehmen wir monatliche Updates für Sie.'
    },
    {
      question: 'Bietet Complyo auch Workshops oder Schulungen an?',
      answer: 'Ja, im Expertenservice bieten wir individuelle Workshops und Schulungen für Ihr Team an. Diese umfassen Einführung in WCAG 2.1, DSGVO-Best-Practices und technische Umsetzung der Fixes. Kontaktieren Sie uns für ein maßgeschneidertes Angebot.'
    },
    {
      question: 'Wie aktuell sind die rechtlichen Anforderungen?',
      answer: 'Durch unsere eRecht24-Integration sind alle rechtlichen Texte und Anforderungen immer auf dem neuesten Stand. Bei Gesetzesänderungen erhalten Sie automatische Updates (im Expertenservice) oder Benachrichtigungen (DIY-Plan) mit angepassten Lösungen.'
    },
    {
      question: 'Kann ich Complyo auch für mehrere Websites nutzen?',
      answer: 'Ja, im DIY-Plan können Sie unbegrenzt viele Websites analysieren. Allerdings haben Sie nur eine KI-Optimierung verfügbar. Für mehrere professionelle Umsetzungen empfehlen wir den Expertenservice oder kontaktieren Sie uns für ein Enterprise-Angebot.'
    },
    {
      question: 'Was ist der Unterschied zwischen Analyse und KI-Optimierung?',
      answer: 'Eine Analyse scannt Ihre Website und zeigt alle Compliance-Probleme auf. Die KI-Optimierung geht weiter: Sie generiert detaillierte, rechtssichere Lösungen mit Copy-Paste Code, Schritt-für-Schritt-Anleitungen und Priorisierung nach Wichtigkeit. Im DIY-Plan ist eine KI-Optimierung inklusive.'
    }
  ];

  return (
    <section className="bg-gray-50 py-20" id="faq">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-16">
          <h2 className="text-4xl font-bold text-gray-900 mb-4">
            Häufig gestellte Fragen
          </h2>
          <p className="text-xl text-gray-600">
            Alles was Sie über Complyo wissen müssen
          </p>
        </div>
        
        {/* Accordion */}
        <div className="space-y-4">
          {faqs.map((faq, index) => (
            <div
              key={index}
              className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden"
            >
              {/* Question */}
              <button
                onClick={() => setOpenIndex(openIndex === index ? null : index)}
                className="w-full flex items-center justify-between p-6 text-left hover:bg-gray-50 transition-colors"
              >
                <span className="font-semibold text-gray-900 pr-8">
                  {faq.question}
                </span>
                {openIndex === index ? (
                  <ChevronUp className="w-5 h-5 text-blue-600 flex-shrink-0" />
                ) : (
                  <ChevronDown className="w-5 h-5 text-gray-400 flex-shrink-0" />
                )}
              </button>
              
              {/* Answer */}
              {openIndex === index && (
                <div className="px-6 pb-6 text-gray-600 leading-relaxed border-t border-gray-100 pt-4">
                  {faq.answer}
                </div>
              )}
            </div>
          ))}
        </div>
        
        {/* Contact CTA */}
        <div className="mt-12 text-center">
          <p className="text-gray-600 mb-4">
            Haben Sie weitere Fragen?
          </p>
          <a
            href="/contact"
            className="inline-flex items-center gap-2 text-blue-600 hover:text-blue-700 font-semibold"
          >
            Kontaktieren Sie uns
            <ChevronDown className="w-4 h-4 transform -rotate-90" />
          </a>
        </div>
      </div>
    </section>
  );
}

