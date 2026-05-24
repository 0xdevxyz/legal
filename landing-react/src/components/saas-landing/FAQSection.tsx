'use client';
import React, { useState } from 'react';
import { ChevronDown } from 'lucide-react';

const faqs = [
  {
    q: 'Was kostet Complyo und gibt es eine kostenlose Version?',
    a: 'Ja! Complyo bietet eine kostenlose Starter-Version mit einem Website-Scan und Basis-Report. Das Pro-Paket kostet 49€/Monat (zzgl. MwSt.) und umfasst alle 4 Compliance-Module, KI-Fixes und unbegrenzte Websites. Jederzeit kündbar.',
  },
  {
    q: 'Was ist der Unterschied zu Overlay-Lösungen wie Eye-Able®?',
    a: 'Im Gegensatz zu Overlay-Widgets bietet Complyo echte Code-Fixes. Das bedeutet: Ihr Quellcode wird tatsächlich verbessert – kein Widget, das Probleme nur überdeckt. Das Ergebnis ist nachhaltige, zertifizierungsfähige Barrierefreiheit.',
  },
  {
    q: 'Wie schnell bin ich mit Complyo DSGVO-konform?',
    a: 'Viele Nutzer sind innerhalb von 30–60 Minuten compliant. Der Scan dauert ca. 2–5 Minuten, danach erhalten Sie sofort umsetzbare KI-Fixes. Das Cookie-Banner ist in unter 10 Minuten eingerichtet.',
  },
  {
    q: 'Funktioniert Complyo mit WordPress, Shopify & Co.?',
    a: 'Ja. Complyo bietet ein WordPress-Plugin, eine Joomla-Extension und einen einfachen JavaScript-Embed-Code für jede andere Plattform. Für Shopify und Webflow gibt es einen Copy-Paste Snippet.',
  },
  {
    q: 'Was passiert bei Gesetzesänderungen (z.B. neue DSGVO-Vorgaben)?',
    a: 'Im Pro-Plan erhalten Sie automatische Benachrichtigungen bei relevanten Gesetzesänderungen durch BfDI, EDPB und LfDI. Im Expert-Plan übernehmen wir alle Updates direkt für Sie.',
  },
  {
    q: 'Ist Complyo selbst DSGVO-konform?',
    a: 'Natürlich. Complyo verarbeitet keine personenbezogenen Daten Ihrer Website-Besucher. Alle Scans laufen anonymisiert. Unsere Server stehen in Deutschland und erfüllen alle DSGVO-Anforderungen.',
  },
  {
    q: 'Kann ich Complyo für mehrere Websites nutzen?',
    a: 'Im Pro-Plan können Sie unbegrenzt viele Websites hinzufügen und verwalten. Jede Website bekommt ein eigenes Dashboard, eigene Scan-Historie und eigene KI-Fixes.',
  },
];

export default function FAQSection() {
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  return (
    <section className="bg-gray-50 py-24" id="faq">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-14">
          <p className="text-sm font-semibold text-blue-600 uppercase tracking-widest mb-3">FAQ</p>
          <h2 className="font-heading text-3xl sm:text-4xl font-extrabold text-gray-900 mb-4">
            Frequently asked questions
          </h2>
          <p className="text-lg text-gray-500">Alles was Sie über Complyo wissen müssen.</p>
        </div>

        <div className="space-y-3">
          {faqs.map((faq, i) => (
            <div key={i} className="bg-white rounded-2xl border border-gray-100 overflow-hidden shadow-sm">
              <button
                className="w-full flex items-center justify-between px-6 py-5 text-left gap-4"
                onClick={() => setOpenIndex(openIndex === i ? null : i)}
              >
                <span className="font-semibold text-gray-900 text-sm leading-snug">{faq.q}</span>
                <ChevronDown className={`w-5 h-5 text-gray-400 flex-shrink-0 transition-transform duration-200 ${openIndex === i ? 'rotate-180' : ''}`} />
              </button>
              {openIndex === i && (
                <div className="px-6 pb-5">
                  <p className="text-sm text-gray-500 leading-relaxed">{faq.a}</p>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
