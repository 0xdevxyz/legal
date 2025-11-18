'use client';

import React from 'react';

export default function TestimonialsModern() {
  const testimonials = [
    {
      name: 'Maria Schmidt',
      role: 'CEO, TechStart GmbH',
      quote: 'Complyo hat uns geholfen, unsere Website in Rekordzeit barrierefrei zu machen.',
      rating: 5
    },
    {
      name: 'Thomas Müller',
      role: 'Marketing Manager',
      quote: 'Die KI-gestützten Lösungen sind beeindruckend und sparen uns enorm viel Zeit.',
      rating: 5
    },
    {
      name: 'Sarah Weber',
      role: 'Web Developer',
      quote: 'Super einfache Integration und sofort sichtbare Ergebnisse!',
      rating: 5
    }
  ];

  return (
    <section className="py-20 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-4xl md:text-5xl font-bold mb-4">
            Was unsere Kunden sagen
          </h2>
        </div>

        <div className="grid md:grid-cols-3 gap-8">
          {testimonials.map((testimonial, idx) => (
            <div
              key={idx}
              className="p-8 bg-gradient-to-br from-purple-50 to-blue-50 rounded-2xl shadow-lg"
            >
              <div className="flex mb-4">
                {[...Array(testimonial.rating)].map((_, i) => (
                  <span key={i} className="text-yellow-400 text-xl">⭐</span>
                ))}
              </div>
              <p className="text-gray-700 mb-6 italic">"{testimonial.quote}"</p>
              <div>
                <p className="font-semibold">{testimonial.name}</p>
                <p className="text-sm text-gray-600">{testimonial.role}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
