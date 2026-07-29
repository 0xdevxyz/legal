'use client';

import React from 'react';
import Link from 'next/link';
import { ArrowLeft, ArrowRight, CalendarDays, Clock, Info } from 'lucide-react';

export interface ArticleSection {
  heading: string;
  body?: string[];
  list?: string[];
  ordered?: boolean;
}

export interface ArticleFaq {
  q: string;
  a: string;
}

export interface ArticlePageProps {
  h1: string;
  lead: string;
  updated: string;
  readingMinutes: number;
  sections: ArticleSection[];
  faq: ArticleFaq[];
  cta: { heading: string; text: string; href: string; label: string };
  related: { href: string; label: string }[];
  slug: string;
}

/**
 * Gemeinsames Layout der Ratgeber-Artikel.
 *
 * Enthaelt Article- und FAQPage-JSON-LD, ein Inhaltsverzeichnis (Sprungmarken)
 * und einen CTA auf das passende Pruef-Tool.
 */
export default function ArticlePage({
  h1,
  lead,
  updated,
  readingMinutes,
  sections,
  faq,
  cta,
  related,
  slug,
}: ArticlePageProps) {
  const anchor = (s: string) =>
    s
      .toLowerCase()
      .replace(/[äöüß]/g, (m) => ({ ä: 'ae', ö: 'oe', ü: 'ue', ß: 'ss' })[m] || m)
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-|-$/g, '');

  const jsonLd = [
    {
      '@context': 'https://schema.org',
      '@type': 'Article',
      headline: h1,
      description: lead,
      dateModified: updated,
      mainEntityOfPage: `https://complyo.de/ratgeber/${slug}/`,
      publisher: { '@type': 'Organization', name: 'Complyo' },
    },
    {
      '@context': 'https://schema.org',
      '@type': 'FAQPage',
      mainEntity: faq.map(({ q, a }) => ({
        '@type': 'Question',
        name: q,
        acceptedAnswer: { '@type': 'Answer', text: a },
      })),
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-blue-50">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />

      <div className="container mx-auto px-4 py-12 max-w-3xl">
        <Link
          href="/"
          className="inline-flex items-center gap-2 text-blue-600 hover:text-blue-700 mb-8 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Zurück zur Startseite
        </Link>

        <article>
          <header className="mb-8">
            <h1 className="text-4xl font-bold text-gray-900 mb-4">{h1}</h1>
            <p className="text-lg text-gray-700 leading-relaxed">{lead}</p>
            <div className="mt-4 flex flex-wrap gap-4 text-sm text-gray-500">
              <span className="inline-flex items-center gap-1.5">
                <CalendarDays className="w-4 h-4" /> Stand: {updated}
              </span>
              <span className="inline-flex items-center gap-1.5">
                <Clock className="w-4 h-4" /> {readingMinutes} Min. Lesezeit
              </span>
            </div>
          </header>

          <nav aria-label="Inhalt" className="bg-white rounded-xl shadow p-6 mb-10">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-gray-500 mb-3">
              Inhalt
            </h2>
            <ol className="space-y-1.5 list-decimal list-inside text-blue-600">
              {sections.map((s) => (
                <li key={s.heading}>
                  <a href={`#${anchor(s.heading)}`} className="hover:underline">
                    {s.heading}
                  </a>
                </li>
              ))}
            </ol>
          </nav>

          <div className="space-y-8">
            {sections.map((s) => (
              <section
                key={s.heading}
                id={anchor(s.heading)}
                className="bg-white rounded-xl shadow-lg p-8 scroll-mt-8"
              >
                <h2 className="text-2xl font-bold text-gray-900 mb-4">{s.heading}</h2>
                <div className="space-y-4 text-gray-700 leading-relaxed">
                  {s.body?.map((p, i) => (
                    <p key={i}>{p}</p>
                  ))}
                  {s.list &&
                    (s.ordered ? (
                      <ol className="list-decimal list-outside ml-5 space-y-2">
                        {s.list.map((li, i) => (
                          <li key={i}>{li}</li>
                        ))}
                      </ol>
                    ) : (
                      <ul className="list-disc list-outside ml-5 space-y-2">
                        {s.list.map((li, i) => (
                          <li key={i}>{li}</li>
                        ))}
                      </ul>
                    ))}
                </div>
              </section>
            ))}

            <section className="bg-blue-600 rounded-xl shadow-lg p-8 text-white">
              <h2 className="text-2xl font-bold mb-3">{cta.heading}</h2>
              <p className="mb-6 text-blue-50 leading-relaxed">{cta.text}</p>
              <Link
                href={cta.href}
                className="inline-flex items-center gap-2 bg-white text-blue-700 font-semibold px-6 py-3 rounded-lg hover:bg-blue-50 transition-colors"
              >
                {cta.label}
                <ArrowRight className="w-4 h-4" />
              </Link>
            </section>

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
                <h2 className="text-2xl font-bold text-gray-900 mb-4">Weiterlesen</h2>
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

            <aside className="flex gap-3 rounded-xl border border-gray-200 bg-gray-50 p-5 text-sm text-gray-600">
              <Info className="w-5 h-5 flex-shrink-0 text-gray-400 mt-0.5" />
              <p>
                Dieser Beitrag gibt einen allgemeinen Überblick und ersetzt keine Rechtsberatung. Ob
                und wie die beschriebenen Pflichten in Ihrem konkreten Fall gelten, kann nur eine
                Anwältin oder ein Anwalt verbindlich beurteilen.
              </p>
            </aside>
          </div>
        </article>
      </div>
    </div>
  );
}
