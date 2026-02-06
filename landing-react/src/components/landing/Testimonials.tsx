'use client';

import React, { useState } from 'react';
import { ChevronLeft, ChevronRight, Star, Quote } from 'lucide-react';

/**
 * Testimonials - Kundenstimmen Slider
 */
export default function Testimonials() {
  const [currentIndex, setCurrentIndex] = useState(0);

  const testimonials = [
    {
      name: 'Thomas Müller',
      role: 'CTO',
      company: 'TechStart GmbH',
      industry: 'E-Commerce',
      image: '👨‍💼',
      quote: 'Complyo hat uns geholfen, unsere WCAG-Compliance von 45% auf 92% zu steigern. Die KI-generierten Fixes waren präzise und einfach umzusetzen. Absolute Empfehlung!',
      metric: '45% → 92%',
      metricLabel: 'WCAG Score'
    },
    {
      name: 'Sarah Schmidt',
      role: 'Marketing Managerin',
      company: 'WebPro Agency',
      industry: 'Agentur',
      image: '👩‍💼',
      quote: 'Als Nicht-Entwicklerin war ich skeptisch. Aber die Schritt-für-Schritt-Anleitungen waren so klar, dass ich viele Fixes selbst umsetzen konnte. Der Expertenservice hat den Rest übernommen.',
      metric: '€12.000',
      metricLabel: 'Bußgeld vermieden'
    },
    {
      name: 'Michael Weber',
      role: 'Geschäftsführer',
      company: 'Handwerk Online',
      industry: 'Handwerk',
      image: '👨‍🔧',
      quote: 'Endlich eine Compliance-Lösung ohne monatliche Widget-Kosten. Die einmalige Umsetzung war ihr Geld wert – jetzt sind wir dauerhaft geschützt.',
      metric: '3 Wochen',
      metricLabel: 'Bis vollständig compliant'
    },
    {
      name: 'Lisa Hoffmann',
      role: 'Entwicklerin',
      company: 'StartupHub Berlin',
      industry: 'SaaS',
      image: '👩‍💻',
      quote: 'Die genaue Code-Lokalisierung mit Datei und Zeile hat uns Stunden an Debugging erspart. Kein anderes Tool bietet so präzise Lösungen.',
      metric: '80%',
      metricLabel: 'Zeitersparnis'
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
    <section className="bg-gray-900 text-white py-20">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-16">
          <h2 className="text-4xl font-bold mb-4">
            Was unsere Kunden sagen
          </h2>
          <p className="text-xl text-gray-400">
            Echte Erfahrungen von echten Unternehmen
          </p>
        </div>
        
        {/* Testimonial Card */}
        <div className="relative">
          <div className="bg-gradient-to-br from-gray-800 to-gray-900 rounded-3xl p-12 border border-gray-700 shadow-2xl">
            {/* Quote Icon */}
            <Quote className="w-16 h-16 text-blue-500/20 mb-6" />
            
            {/* Stars */}
            <div className="flex gap-1 mb-6">
              {[...Array(5)].map((_, i) => (
                <Star key={i} className="w-5 h-5 fill-yellow-400 text-yellow-400" />
              ))}
            </div>
            
            {/* Quote */}
            <blockquote className="text-2xl font-medium leading-relaxed mb-8 text-gray-100">
              "{current.quote}"
            </blockquote>
            
            {/* Author */}
            <div className="flex items-center justify-between flex-wrap gap-6">
              <div className="flex items-center gap-4">
                <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-500 rounded-full flex items-center justify-center text-3xl">
                  {current.image}
                </div>
                <div>
                  <div className="font-bold text-lg">{current.name}</div>
                  <div className="text-gray-400">{current.role}</div>
                  <div className="text-sm text-gray-500">{current.company} • {current.industry}</div>
                </div>
              </div>
              
              {/* Metric */}
              <div className="bg-gradient-to-r from-blue-500/20 to-purple-500/20 border border-blue-400/30 rounded-xl px-6 py-4 text-center">
                <div className="text-3xl font-bold text-blue-400">{current.metric}</div>
                <div className="text-sm text-gray-400">{current.metricLabel}</div>
              </div>
            </div>
          </div>
          
          {/* Navigation Buttons */}
          <div className="flex items-center justify-center gap-4 mt-8">
            <button
              onClick={prevTestimonial}
              className="w-12 h-12 bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-full flex items-center justify-center transition-colors"
              aria-label="Vorheriges Testimonial"
            >
              <ChevronLeft className="w-6 h-6" />
            </button>
            
            {/* Dots */}
            <div className="flex gap-2">
              {testimonials.map((_, index) => (
                <button
                  key={index}
                  onClick={() => setCurrentIndex(index)}
                  className={`w-2 h-2 rounded-full transition-all ${
                    index === currentIndex
                      ? 'bg-blue-500 w-8'
                      : 'bg-gray-700 hover:bg-gray-600'
                  }`}
                  aria-label={`Gehe zu Testimonial ${index + 1}`}
                />
              ))}
            </div>
            
            <button
              onClick={nextTestimonial}
              className="w-12 h-12 bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-full flex items-center justify-center transition-colors"
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

