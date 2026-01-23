'use client';

import React, { useState } from 'react';
import { ChevronLeft, ChevronRight, Star, Quote } from 'lucide-react';

export default function Testimonials() {
  const [currentIndex, setCurrentIndex] = useState(0);

  const testimonials = [
    {
      name: 'Jana Richter',
      role: 'Founder, Launch Academy',
      company: 'Launch Academy',
      industry: 'Online Courses',
      image: '🧠',
      quote:
        'Innerhalb von zwei Tagen hatte ich Kursseiten, Member-Only Inhalte und E-Mail-Automationen live. Die alfi AI hat mir sogar Newsletter-Vorlagen vorgeschlagen.',
      metric: '2 Tage',
      metricLabel: 'bis zum ersten Launch'
    },
    {
      name: 'Felix Neumann',
      role: 'Coach & Podcaster',
      company: 'Mindflow Club',
      industry: 'Coaching',
      image: '🎙️',
      quote:
        'Meeting-Terminbuchungen, CRM und Upsells laufen automatisch über alfima. Ich muss mich nur auf meine Community konzentrieren.',
      metric: '40%',
      metricLabel: 'Termin-Konversion'
    },
    {
      name: 'Kim Bauer',
      role: 'Marketing Managerin',
      company: 'Creative Cofounders',
      industry: 'SaaS',
      image: '💼',
      quote:
        'Die Plattform ersetzt mehrere Tools: Shop, Community, Newsletter und Automationen sprechen perfekt miteinander. Der Support antwortet sogar per WhatsApp.',
      metric: '73%',
      metricLabel: 'E-Mail-Öffnungsrate'
    }
  ];

  const nextTestimonial = () => {
    setCurrentIndex((prev) => (prev + 1) % testimonials.length);
  };

  const prevTestimonial = () => {
    setCurrentIndex((prev) => (prev - 1 + testimonials.length) % testimonials.length);
  };

  const current = testimonials[currentIndex];

  return (
    <section className="bg-slate-900 text-white py-20">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <p className="text-sm uppercase tracking-[0.4em] text-white/60">Erfolgsgeschichten</p>
          <h2 className="text-4xl font-bold mt-4">Das sagen Creator, die alfima bereits nutzen</h2>
          <p className="text-lg text-white/70 mt-3">
            Nochmaliger Boost für digitale Produkte, Termine und Communitys mit einem Tool.
          </p>
        </div>

        <div className="relative">
          <div className="rounded-3xl border border-white/10 bg-gradient-to-br from-white/10 to-slate-900/70 p-12 shadow-2xl backdrop-blur">
            <Quote className="w-16 h-16 text-cyan-400/60 mb-6" />
            <div className="flex gap-1 mb-6">
              {[...Array(5)].map((_, i) => (
                <Star key={i} className="w-5 h-5 text-yellow-400" />
              ))}
            </div>
            <blockquote className="text-2xl font-semibold leading-relaxed text-white/90">
              "{current.quote}"
            </blockquote>
            <div className="mt-10 flex flex-col lg:flex-row items-center justify-between gap-6">
              <div className="flex items-center gap-4">
                <div className="flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-cyan-500 to-blue-500 text-3xl">
                  {current.image}
                </div>
                <div>
                  <div className="text-lg font-semibold">{current.name}</div>
                  <div className="text-sm text-white/70">
                    {current.role} — {current.company}
                  </div>
                </div>
              </div>
              <div className="rounded-2xl border border-white/20 bg-white/10 px-6 py-4 text-center text-sm uppercase tracking-[0.3em] text-white/80">
                <div className="text-3xl font-bold text-white">{current.metric}</div>
                <div className="text-xs text-white/70">{current.metricLabel}</div>
              </div>
            </div>
          </div>

          <div className="mt-10 flex items-center justify-center gap-4">
            <button
              onClick={prevTestimonial}
              className="h-12 w-12 rounded-full border border-white/20 bg-white/10 text-white transition hover:bg-white/20"
              aria-label="Vorheriges Testimonial"
            >
              <ChevronLeft className="w-6 h-6" />
            </button>
            <div className="flex gap-2">
              {testimonials.map((_, index) => (
                <button
                  key={index}
                  onClick={() => setCurrentIndex(index)}
                  className={`h-2 rounded-full transition-all ${index === currentIndex ? 'w-8 bg-cyan-400' : 'w-2 bg-white/30'}`}
                  aria-label={`Gehe zu Testimonial ${index + 1}`}
                />
              ))}
            </div>
            <button
              onClick={nextTestimonial}
              className="h-12 w-12 rounded-full border border-white/20 bg-white/10 text-white transition hover:bg-white/20"
              aria-label="Nächstes Testimonial"
            >
              <ChevronRight className="w-6 h-6" />
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}
