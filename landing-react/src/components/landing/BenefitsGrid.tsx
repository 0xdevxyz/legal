'use client';

import React from 'react';
import { Zap, Scale, Globe, Target, Shield, Clock } from 'lucide-react';

/**
 * BenefitsGrid - Vorteile von Complyo in Grid-Form
 */
export default function BenefitsGrid() {
  const benefits = [
    {
      icon: Zap,
      title: 'Sofortige Integration',
      description: 'Erste Analyse in unter 5 Minuten. Kein Setup, keine Installation – einfach URL eingeben.',
      color: 'text-yellow-500',
      bgColor: 'bg-yellow-500/10'
    },
    {
      icon: Scale,
      title: 'Rechtssicher',
      description: 'Mit eRecht24-API Integration für garantiert aktuelle und rechtskonforme Texte.',
      color: 'text-blue-500',
      bgColor: 'bg-blue-500/10'
    },
    {
      icon: Globe,
      title: 'Nachhaltig',
      description: 'Echte Code-Fixes statt Overlay-Widgets für dauerhafte Compliance ohne Abhängigkeiten.',
      color: 'text-green-500',
      bgColor: 'bg-green-500/10'
    },
    {
      icon: Target,
      title: 'Präzise',
      description: 'Genaue Code-Lokalisierung mit Zeilen- und Dateiangaben für schnelle Umsetzung.',
      color: 'text-purple-500',
      bgColor: 'bg-purple-500/10'
    },
    {
      icon: Shield,
      title: 'Abmahn-Schutz',
      description: 'Vermeiden Sie teure Bußgelder bis 50.000€ durch proaktive Compliance-Prüfung.',
      color: 'text-red-500',
      bgColor: 'bg-red-500/10'
    },
    {
      icon: Clock,
      title: 'Zeit sparen',
      description: 'KI-generierte Lösungen reduzieren Umsetzungszeit um durchschnittlich 80%.',
      color: 'text-cyan-500',
      bgColor: 'bg-cyan-500/10'
    }
  ];

  return (
    <section className="bg-white py-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-16">
          <h2 className="text-4xl font-bold text-gray-900 mb-4">
            Warum Unternehmen Complyo vertrauen
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Nachhaltige Compliance-Lösung statt Quick-Fixes mit versteckten Risiken
          </p>
        </div>
        
        {/* Benefits Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {benefits.map((benefit, index) => (
            <div
              key={index}
              className="group"
            >
              <div className="bg-gray-50 rounded-2xl p-8 border-2 border-gray-100 hover:border-blue-500 transition-all h-full">
                {/* Icon */}
                <div className={`w-14 h-14 ${benefit.bgColor} rounded-xl flex items-center justify-center mb-6 transform group-hover:scale-110 transition-transform`}>
                  <benefit.icon className={`w-7 h-7 ${benefit.color}`} />
                </div>
                
                {/* Content */}
                <h3 className="text-xl font-bold text-gray-900 mb-3">
                  {benefit.title}
                </h3>
                <p className="text-gray-600 leading-relaxed">
                  {benefit.description}
                </p>
              </div>
            </div>
          ))}
        </div>
        
        {/* Bottom CTA */}
        <div className="mt-16 text-center">
          <div className="inline-block bg-gradient-to-r from-blue-50 to-purple-50 rounded-2xl p-8 border-2 border-blue-200">
            <div className="text-4xl font-bold text-gray-900 mb-2">
              €250.000+
            </div>
            <div className="text-gray-600 mb-4">
              Bußgelder durch Complyo vermieden
            </div>
            <div className="text-sm text-gray-500">
              Basierend auf durchschnittlichen DSGVO-Strafen für die erkannten Verstöße
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

