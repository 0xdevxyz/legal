'use client';
import React from 'react';
import { ArrowRight, Star, CheckCircle2, ShieldCheck, Zap } from 'lucide-react';

export default function HeroSection() {
  return (
    <section className="relative bg-white pt-24 pb-16 overflow-hidden">
      <div className="absolute top-0 right-0 w-[600px] h-[600px] bg-gradient-to-bl from-blue-50 via-indigo-50 to-transparent rounded-full blur-3xl opacity-70 pointer-events-none" />
      <div className="absolute bottom-0 left-0 w-[400px] h-[400px] bg-gradient-to-tr from-orange-50 via-yellow-50 to-transparent rounded-full blur-3xl opacity-60 pointer-events-none" />

      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center min-h-[580px]">

          <div>
            <div className="inline-flex items-center gap-2 bg-blue-50 border border-blue-100 rounded-full px-4 py-1.5 mb-6">
              <ShieldCheck className="w-4 h-4 text-blue-600" />
              <span className="text-xs font-semibold text-blue-700 uppercase tracking-wide">DSGVO · WCAG · Cookie Compliance</span>
            </div>

            <h1 className="font-heading text-4xl sm:text-5xl lg:text-6xl font-extrabold text-gray-900 leading-[1.1] mb-6">
              Websites{' '}
              <span className="text-blue-600">rechtssicher</span>{' '}
              machen mit{' '}
              <span className="relative inline-block">
                <span className="text-orange-500">KI</span>
                <span className="absolute -bottom-1 left-0 right-0 h-1 bg-orange-200 rounded-full" />
              </span>
              &#8209;Compliance
            </h1>

            <p className="text-lg text-gray-500 mb-8 leading-relaxed max-w-xl">
              Complyo scannt und analysiert deine Website auf DSGVO-, Cookie- und Barrierefreiheitsprobleme – und liefert konkrete Lösungsvorschläge, die du direkt umsetzen kannst.
            </p>

            <div className="flex flex-col sm:flex-row gap-3 mb-8 text-sm">
              {['Kostenloser Website-Scan', 'Early-Access-Vorteile', 'Jederzeit abmeldbar'].map((item, i) => (
                <div key={i} className="flex items-center gap-1.5 text-gray-500">
                  <CheckCircle2 className="w-4 h-4 text-green-500 flex-shrink-0" />
                  <span>{item}</span>
                </div>
              ))}
            </div>

            <div className="flex flex-col sm:flex-row gap-3">
              <a href="#waitlist" className="inline-flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold px-6 py-3.5 rounded-xl transition-colors shadow-md shadow-blue-100">
                Auf Warteliste
                <ArrowRight className="w-4 h-4" />
              </a>
              <a href="#scanner" className="inline-flex items-center justify-center gap-2 bg-gray-50 hover:bg-gray-100 text-gray-700 font-semibold px-6 py-3.5 rounded-xl border border-gray-200 transition-colors">
                Website jetzt scannen
              </a>
            </div>

            <div className="mt-10 flex items-center gap-4">
              <div className="flex -space-x-2">
                {['#3B82F6','#8B5CF6','#EC4899','#F97316','#10B981'].map((c,i) => (
                  <div key={i} className="w-8 h-8 rounded-full border-2 border-white flex items-center justify-center text-white text-xs font-bold" style={{backgroundColor: c}}>
                    {String.fromCharCode(65+i)}
                  </div>
                ))}
              </div>
              <div>
                <div className="flex items-center gap-0.5">
                  {[1,2,3,4,5].map(i => <Star key={i} className="w-3.5 h-3.5 text-yellow-400 fill-yellow-400" />)}
                </div>
                <p className="text-xs text-gray-500 mt-0.5">Werde einer der <strong>ersten Tester</strong></p>
              </div>
            </div>
          </div>

          <div className="relative flex justify-center lg:justify-end">
            <div className="relative w-full max-w-[520px]">
              <div className="absolute inset-0 bg-gradient-to-br from-blue-200 to-indigo-200 rounded-3xl blur-2xl opacity-30 scale-95" />

              <div className="relative bg-white rounded-2xl shadow-2xl border border-gray-100 overflow-hidden">
                <div className="bg-gray-50 border-b border-gray-100 px-5 py-3 flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-red-400" />
                  <div className="w-3 h-3 rounded-full bg-yellow-400" />
                  <div className="w-3 h-3 rounded-full bg-green-400" />
                  <span className="ml-3 text-xs text-gray-400">app.complyo.de – Dashboard</span>
                </div>

                <div className="p-6 space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-xs text-gray-400 uppercase tracking-wide font-semibold">Compliance Score</p>
                      <p className="text-3xl font-extrabold text-gray-900">94 <span className="text-xl text-gray-400">/100</span></p>
                    </div>
                    <div className="flex items-center gap-1.5 bg-green-50 text-green-700 text-xs font-semibold px-3 py-1.5 rounded-full">
                      <Zap className="w-3.5 h-3.5" />
                      +47% verbessert
                    </div>
                  </div>

                  <div className="space-y-2.5">
                    {[
                      {label:'DSGVO', val:98, color:'bg-blue-500'},
                      {label:'Cookie Consent', val:91, color:'bg-indigo-500'},
                      {label:'WCAG 2.1 AA', val:88, color:'bg-purple-500'},
                      {label:'Impressum', val:100, color:'bg-green-500'},
                    ].map((item) => (
                      <div key={item.label}>
                        <div className="flex justify-between text-xs text-gray-500 mb-1">
                          <span>{item.label}</span>
                          <span className="font-semibold text-gray-700">{item.val}%</span>
                        </div>
                        <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
                          <div className={`h-full ${item.color} rounded-full`} style={{width:`${item.val}%`}} />
                        </div>
                      </div>
                    ))}
                  </div>

                  <div className="grid grid-cols-2 gap-2 pt-2">
                    {[
                      {label:'Kritische Fehler', val:'0', color:'text-green-600', bg:'bg-green-50'},
                      {label:'Quick Wins', val:'3', color:'text-blue-600', bg:'bg-blue-50'},
                      {label:'Lösungsvorschläge', val:'12', color:'text-purple-600', bg:'bg-purple-50'},
                      {label:'Websites', val:'1', color:'text-orange-600', bg:'bg-orange-50'},
                    ].map((item) => (
                      <div key={item.label} className={`${item.bg} rounded-xl p-3`}>
                        <p className={`text-2xl font-extrabold ${item.color}`}>{item.val}</p>
                        <p className="text-xs text-gray-500 mt-0.5">{item.label}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <div className="absolute -bottom-3 -left-3 bg-white rounded-xl shadow-lg border border-gray-100 px-4 py-2.5 flex items-center gap-2.5">
                <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">
                  <ShieldCheck className="w-4 h-4 text-green-600" />
                </div>
                <div>
                  <p className="text-xs font-bold text-gray-900">DSGVO-konform</p>
                  <p className="text-xs text-gray-400">Automatisch geprüft</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
