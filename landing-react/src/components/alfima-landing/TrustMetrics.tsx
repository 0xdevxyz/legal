'use client';

import React from 'react';
import { Globe, Scan, Shield, Award } from 'lucide-react';

const metrics = [
  {
    icon: Globe,
    value: '2.500+',
    label: 'Websites geschützt',
    description: 'vertrauen auf Complyo Compliance',
    color: 'from-cyan-400 to-blue-500'
  },
  {
    icon: Scan,
    value: '50.000+',
    label: 'Compliance-Scans',
    description: 'erfolgreich durchgeführt',
    color: 'from-emerald-500 to-teal-500'
  },
  {
    icon: Shield,
    value: '14 Tage',
    label: 'kostenfrei testen',
    description: 'inkl. vollem Funktionsumfang',
    color: 'from-violet-500 to-fuchsia-500'
  }
];

export default function TrustMetrics() {
  return (
    <section className="bg-white py-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {metrics.map((metric) => (
            <div
              key={metric.label}
              className="text-center rounded-3xl border border-slate-100 bg-slate-50 p-8 shadow-lg"
            >
              <div className={`inline-flex w-20 h-20 items-center justify-center rounded-2xl bg-gradient-to-br ${metric.color} text-white mb-6 shadow-2xl`}>
                <metric.icon className="w-10 h-10" />
              </div>

              <div className={`text-5xl font-bold bg-gradient-to-r ${metric.color} bg-clip-text text-transparent mb-2`}>
                {metric.value}
              </div>

              <div className="text-xl font-semibold text-slate-900 mb-2">{metric.label}</div>
              <p className="text-sm text-slate-500">{metric.description}</p>
            </div>
          ))}
        </div>
        <div className="mt-12 text-center text-sm uppercase tracking-[0.4em] text-slate-400 flex items-center justify-center gap-2">
          <Award className="w-4 h-4 text-slate-400" />
          Made in Germany – 100% DSGVO-konform
        </div>
      </div>
    </section>
  );
}
