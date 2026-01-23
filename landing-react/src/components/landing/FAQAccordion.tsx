'use client';

import React, { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';

const faqs = [
  {
    question: 'Ich habe noch keine Reichweite, lohnt sich alfima trotzdem?',
    answer:
      'Absolut. Wir zeigen dir in der alfima Academy, wie du ohne große Reichweite mit Kursen, PDFs und Mini-Events Geld verdienst. Du bekommst konkrete Launchpläne und Support beim Positionieren.'
  },
  {
    question: 'Was steckt hinter der All-in-One-Plattform?',
    answer:
      'Landingpage, Content-Produktion, Checkout, Memberbereich, CRM, Terminbuchung, E-Mail-Marketing, Automationen und Analysen – direkt aus einem Dashboard gesteuert.'
  },
  {
    question: 'Was passiert nach den ersten 14 Tagen?',
    answer:
      'Dein Zugang bleibt erhalten, du kannst zum Creator-Plan wechseln. Die Daten bleiben gespeichert, sodass du jederzeit reaktivieren kannst. Support & Academy laufen weiter ohne Zusatzkosten.'
  },
  {
    question: 'Wie schnell kann ich ein Angebot live schalten?',
    answer:
      'Mit unseren Launch-Templates und Auto-Checkout-Blocks brauchst du nur wenige Stunden für deinen ersten Kurs. Coachings und Membership-Seiten sind in 2 Tagen fertig.'
  },
  {
    question: 'Welche Automationen sind dabei?',
    answer:
      'E-Mail-Strecken, Reminder, Upsells, Payment-Reminder, Terminbuchungen inkl. Kalender-Sync und Segmentierung nach Verhalten – alles als Flow editierbar.'
  },
  {
    question: 'Wie sieht der Support aus?',
    answer:
      'Du bekommst 1:1 Onboarding-Calls, persönlichen WhatsApp-Support sowie wöchentliche LIVE-Coachings mit dem Gründerteam. Technische Fragen beantworten wir innerhalb weniger Stunden.'
  }
];

export default function FAQAccordion() {
  const [openIndex, setOpenIndex] = useState<number | null>(0);

  return (
    <section id="faq" className="bg-white py-20">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <p className="text-sm uppercase tracking-[0.4em] text-slate-500">FAQ</p>
          <h2 className="text-4xl font-bold mt-4">Alles, was Creator wissen wollen</h2>
          <p className="text-lg text-slate-500 mt-3">
            Klar, präzise Antworten zu Preisen, Launch, Support und dem All-in-One Versprechen.
          </p>
        </div>

        <div className="space-y-4">
          {faqs.map((faq, index) => (
            <div key={index} className="rounded-3xl border border-slate-100 bg-slate-50 shadow-sm">
              <button
                onClick={() => setOpenIndex(openIndex === index ? null : index)}
                className="w-full flex items-center justify-between px-6 py-5 text-left text-lg font-semibold text-slate-900 transition hover:bg-white"
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
            href="https://alfima.io#contact"
            className="inline-flex items-center gap-2 rounded-full border border-slate-300 px-6 py-3 text-sm font-semibold text-slate-900 transition hover:bg-slate-100"
          >
            Zum Support
          </a>
        </div>
      </div>
    </section>
  );
}
