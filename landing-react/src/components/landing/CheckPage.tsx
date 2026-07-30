'use client';

import React from 'react';
import Link from 'next/link';
import { ArrowLeft, CheckCircle2, Clock, Lock, ShieldCheck } from 'lucide-react';
import WebsiteScanner from './WebsiteScanner';

export interface CheckPageSection {
  heading: string;
  body: string[];
}

export interface CheckPageFaq {
  q: string;
  a: string;
}

export interface CheckPageProps {
  h1: string;
  lead: string;
  bullets: string[];
  sections: CheckPageSection[];
  faq: CheckPageFaq[];
  related: { href: string; label: string }[];
}

/**
 * Gemeinsames Layout der Check-Landingpages (/dsgvo-website-check, /bfsg-check,
 * /barrierefreiheit-website-testen).
 *
 * Aufbau folgt der Suchintention: Das Tool steht oben, der erklaerende Text
 * darunter. Wer nach "... check" sucht, will pruefen, nicht lesen.
 */
export default function CheckPage({ h1, lead, bullets, sections, faq, related }: CheckPageProps) {
  const faqJsonLd = {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: faq.map(({ q, a }) => ({
      '@type': 'Question',
      name: q,
      acceptedAnswer: { '@type': 'Answer', text: a },
    })),
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-blue-50">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(faqJsonLd) }}
      />

      <div className="container mx-auto px-4 py-12 max-w-4xl">
        <Link
          href="/"
          className="inline-flex items-center gap-2 text-blue-600 hover:text-blue-700 mb-8 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Zurück zur Startseite
        </Link>

        <header className="mb-10">
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">{h1}</h1>
          <p className="text-lg text-gray-700 leading-relaxed">{lead}</p>

          <ul className="mt-6 grid gap-3 sm:grid-cols-2">
            {bullets.map((b) => (
              <li key={b} className="flex items-start gap-2 text-gray-700">
                <CheckCircle2 className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
                <span>{b}</span>
              </li>
            ))}
          </ul>

          <div className="mt-6 flex flex-wrap gap-4 text-sm text-gray-600">
            <span className="inline-flex items-center gap-1.5">
              <Clock className="w-4 h-4 text-blue-600" /> Ergebnis in unter einer Minute
            </span>
            <span className="inline-flex items-center gap-1.5">
              <Lock className="w-4 h-4 text-blue-600" /> Keine Anmeldung nötig
            </span>
            <span className="inline-flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4 text-blue-600" /> Kostenlos
            </span>
          </div>
        </header>

        <section aria-label="Website prüfen" className="mb-14">
          <WebsiteScanner />
        </section>

        <div className="space-y-10">
          {sections.map((s) => (
            <section key={s.heading} className="bg-white rounded-xl shadow-lg p-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">{s.heading}</h2>
              <div className="space-y-4 text-gray-700 leading-relaxed">
                {s.body.map((p, i) => (
                  <p key={i}>{p}</p>
                ))}
              </div>
            </section>
          ))}

          <section className="bg-white rounded-xl shadow-lg p-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Häufige Fragen</h2>
            <dl className="space-y-6">
              {faq.map(({ q, a }) => (
                <div key={q}>
                  <dt className="font-semibold text-gray-900 mb-1">{q}</dt>
                  <dd className="text-gray-700 leading-relaxed">{a}</dd>
                </div>
              ))}
            </dl>
          </section>

          {related.length > 0 && (
            <section className="bg-white rounded-xl shadow-lg p-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">Weitere Prüfungen</h2>
              <ul className="space-y-2">
                {related.map(({ href, label }) => (
                  <li key={href}>
                    <Link href={href} className="text-blue-600 hover:text-blue-700 hover:underline">
                      {label}
                    </Link>
                  </li>
                ))}
              </ul>
            </section>
          )}
        </div>
      </div>
    </div>
  );
}
