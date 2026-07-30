import type { Metadata } from 'next';
import Link from 'next/link';
import { ArrowLeft, ArrowRight } from 'lucide-react';

export const metadata: Metadata = {
  title: 'Ratgeber: Website-Compliance verständlich erklärt | Complyo',
  description:
    'Ratgeber zu DSGVO, Cookie-Banner und Barrierefreiheit: praxisnahe Anleitungen und Checklisten für rechtssichere Websites.',
  alternates: { canonical: '/ratgeber/' },
};

const ARTICLES = [
  {
    href: '/ratgeber/barrierefreiheit-website-checkliste/',
    title: 'Barrierefreiheit Website: Checkliste mit 12 Punkten',
    teaser:
      'Die zwölf Kriterien nach WCAG 2.1 AA, an denen Websites in der Praxis am häufigsten scheitern – mit Hinweis, was sich automatisch prüfen lässt.',
  },
  {
    href: '/ratgeber/cookie-banner-pflicht/',
    title: 'Cookie-Banner-Pflicht: Was wirklich gilt',
    teaser:
      'Wann ein Banner Pflicht ist, wann nicht – und warum der häufigste Fehler technischer Natur ist.',
  },
  {
    href: '/ratgeber/wordpress-cookie-banner/',
    title: 'WordPress Cookie-Banner richtig einrichten',
    teaser:
      'Welche Plugins taugen, warum die Installation allein nicht reicht und wie Sie das Ergebnis selbst überprüfen.',
  },
];

export default function Page() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-blue-50">
      <div className="container mx-auto px-4 py-12 max-w-3xl">
        <Link
          href="/"
          className="inline-flex items-center gap-2 text-blue-600 hover:text-blue-700 mb-8 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Zurück zur Startseite
        </Link>

        <h1 className="text-4xl font-bold text-gray-900 mb-4">Ratgeber</h1>
        <p className="text-lg text-gray-700 mb-10 leading-relaxed">
          Praxisnahe Anleitungen zu Datenschutz, Cookie-Einwilligung und Barrierefreiheit – ohne
          Juristendeutsch, mit konkreten Prüfschritten.
        </p>

        <div className="space-y-4">
          {ARTICLES.map((a) => (
            <Link
              key={a.href}
              href={a.href}
              className="block bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow group"
            >
              <h2 className="text-xl font-bold text-gray-900 mb-2 group-hover:text-blue-700 transition-colors">
                {a.title}
              </h2>
              <p className="text-gray-700 leading-relaxed mb-3">{a.teaser}</p>
              <span className="inline-flex items-center gap-1.5 text-blue-600 font-medium">
                Weiterlesen
                <ArrowRight className="w-4 h-4" />
              </span>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
