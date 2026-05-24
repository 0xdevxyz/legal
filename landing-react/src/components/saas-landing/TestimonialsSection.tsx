'use client';
import React from 'react';
import { Star } from 'lucide-react';

const testimonials = [
  {
    name: 'Sandra K.',
    role: 'Online-Shop Betreiberin',
    company: 'BioNaturshop.de',
    avatar: 'S',
    color: '#3B82F6',
    stars: 5,
    quote: 'Complyo hat uns in einem Wochenende DSGVO-konform gemacht. Das Cookie-Banner war in 10 Minuten eingerichtet und die KI-generierten Rechtstexte sind verständlicher als alles, was wir vorher hatten.',
  },
  {
    name: 'Marcus T.',
    role: 'Webentwickler & Freelancer',
    company: 'mt-webdesign.de',
    avatar: 'M',
    color: '#8B5CF6',
    stars: 5,
    quote: 'Als Entwickler schätze ich besonders die Code-Fixes. Kein vages "Sie müssen XYZ machen" – sondern exakter Quellcode mit Dateiname und Zeilennummer. Ich empfehle Complyo allen meinen Kunden.',
  },
  {
    name: 'Julia R.',
    role: 'Marketing-Leiterin',
    company: 'TechStartup GmbH',
    avatar: 'J',
    color: '#EC4899',
    stars: 5,
    quote: 'Der Compliance-Score ist von 42% auf 94% gestiegen. Das Barrierefreiheits-Modul hat uns auf BFSG vorbereitet, bevor das Gesetz in Kraft trat. Absolut empfehlenswert!',
  },
];

export default function TestimonialsSection() {
  return (
    <section className="bg-white py-24">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-14">
          <p className="text-sm font-semibold text-blue-600 uppercase tracking-widest mb-3">Kundenstimmen</p>
          <h2 className="font-heading text-3xl sm:text-4xl font-extrabold text-gray-900 mb-4">
            What our users are saying about us
          </h2>
          <p className="text-lg text-gray-500">
            Über 2.500 Websites vertrauen auf Complyo – hier sind einige Stimmen.
          </p>
        </div>

        {/* Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {testimonials.map((t, i) => (
            <div key={i} className="bg-gray-50 rounded-2xl p-7 border border-gray-100 flex flex-col">
              {/* Stars */}
              <div className="flex gap-1 mb-4">
                {[1,2,3,4,5].map(s => (
                  <Star key={s} className="w-4 h-4 text-yellow-400 fill-yellow-400" />
                ))}
              </div>
              {/* Quote */}
              <p className="text-gray-600 text-sm leading-relaxed flex-1 mb-6">"{t.quote}"</p>
              {/* Author */}
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full flex items-center justify-center text-white font-bold text-sm flex-shrink-0" style={{backgroundColor: t.color}}>
                  {t.avatar}
                </div>
                <div>
                  <p className="text-sm font-bold text-gray-900">{t.name}</p>
                  <p className="text-xs text-gray-400">{t.role} · {t.company}</p>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Trust Bar */}
        <div className="mt-14 flex flex-wrap items-center justify-center gap-8 text-center">
          {[
            { val: '2.500+', label: 'Websites geschützt' },
            { val: '4.9/5', label: 'Kundenbewertung' },
            { val: '98%', label: 'Kundenzufriedenheit' },
            { val: '< 5 Min', label: 'Durchschnittliche Setup-Zeit' },
          ].map((stat, i) => (
            <div key={i}>
              <p className="text-2xl font-extrabold text-gray-900">{stat.val}</p>
              <p className="text-xs text-gray-400 mt-0.5">{stat.label}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
