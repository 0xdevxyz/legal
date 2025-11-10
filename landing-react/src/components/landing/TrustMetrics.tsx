'use client';

import React from 'react';
import { Users, TrendingUp, Shield } from 'lucide-react';

/**
 * TrustMetrics - Vertrauenszahlen und Erfolgsmetriken
 */
export default function TrustMetrics() {
  const metrics = [
    {
      icon: Users,
      value: '2.500+',
      label: 'Websites geschützt',
      description: 'Vertrauen uns bei ihrer Compliance',
      color: 'from-blue-500 to-cyan-500'
    },
    {
      icon: TrendingUp,
      value: '+47%',
      label: 'Durchschnittlicher Score-Anstieg',
      description: 'Nach erster KI-Optimierung',
      color: 'from-green-500 to-emerald-500'
    },
    {
      icon: Shield,
      value: '€250.000+',
      label: 'Bußgeld vermieden',
      description: 'Durch proaktive Compliance-Prüfung',
      color: 'from-purple-500 to-pink-500'
    }
  ];

  return (
    <section className="bg-white py-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {metrics.map((metric, index) => (
            <div
              key={index}
              className="text-center group"
            >
              {/* Icon */}
              <div className={`inline-flex w-20 h-20 bg-gradient-to-br ${metric.color} rounded-2xl items-center justify-center mb-6 transform group-hover:scale-110 transition-transform shadow-lg`}>
                <metric.icon className="w-10 h-10 text-white" />
              </div>
              
              {/* Value */}
              <div className={`text-5xl font-bold bg-gradient-to-r ${metric.color} bg-clip-text text-transparent mb-2`}>
                {metric.value}
              </div>
              
              {/* Label */}
              <div className="text-xl font-semibold text-gray-900 mb-2">
                {metric.label}
              </div>
              
              {/* Description */}
              <div className="text-gray-600">
                {metric.description}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

