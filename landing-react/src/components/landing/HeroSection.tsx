'use client';

 import React from 'react';
 import { ArrowRight, Sparkles, MessageCircle } from 'lucide-react';

 const quickStats = [
   { label: 'Creator & Coaches', value: '1.000+', detail: 'verwalten digitale Produkte' },
   { label: 'Innenumsatz', value: '15 Mio €', detail: 'durch Launches & Sales' },
   { label: 'WhatsApp Support', value: '24/7', detail: 'inkl. persönlichem Onboarding' }
 ];

 const modules = [
   'Online-Kurse',
   'E-Books & PDFs',
   'Mitgliederbereiche',
   'E-Mail-Marketing',
   'Terminbuchungen',
   'CRM & Automationen'
 ];

 export default function HeroSection() {
   return (
     <section className="relative overflow-hidden bg-gradient-to-br from-slate-950 via-indigo-900 to-sky-900 text-white">
       <div
         className="absolute inset-0 opacity-40"
         style={{
           backgroundImage:
             'radial-gradient(circle at 20% 20%, rgba(255,255,255,0.2) 0, transparent 50%), radial-gradient(circle at 80% 0%, rgba(14,165,233,0.25) 0, transparent 40%)'
         }}
       />

       <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 lg:py-24">
         <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
           <div className="space-y-6">
             <div className="inline-flex items-center gap-2 rounded-full bg-white/10 px-4 py-2 text-xs font-semibold uppercase tracking-[0.3em] text-white/80">
               <Sparkles className="w-4 h-4 text-white" />
               All-in-One Creator Business
             </div>

             <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold leading-tight">
               Baue digitale Produkte und Communitys mit{' '}
               <span className="bg-gradient-to-r from-cyan-400 via-blue-500 to-violet-500 bg-clip-text text-transparent">
                 nur einer Plattform
               </span>
             </h1>

             <p className="text-lg text-white/80 leading-relaxed max-w-2xl">
               Kurse, eBooks, Mitgliederbereiche, Termine, E-Mail-Automationen und ein integriertes CRM –
               alles zentral gesteuert. Die alfi AI schlägt dir Inhalte, Upsells und Performance-Verbesserungen
               vor, während du deine Community skalierst.
             </p>

             <div className="flex flex-wrap gap-3">
               {modules.map((module) => (
                 <span
                   key={module}
                   className="rounded-full border border-white/30 px-4 py-1 text-sm text-white/80 backdrop-blur"
                 >
                   {module}
                 </span>
               ))}
             </div>

             <div className="flex flex-wrap gap-4">
               <a
                 href="#pricing"
                 className="inline-flex items-center gap-2 rounded-xl bg-white px-6 py-3 text-base font-semibold text-slate-950 transition hover:bg-slate-100 shadow-lg"
               >
                 14 Tage kostenfrei testen
                 <ArrowRight className="w-4 h-4" />
               </a>
               <a
                 href="#features"
                 className="inline-flex items-center gap-2 rounded-xl border border-white/40 px-6 py-3 text-base font-semibold text-white transition hover:border-white"
               >
                 Live Demo ansehen
                 <MessageCircle className="w-4 h-4" />
               </a>
             </div>

             <div className="grid w-full grid-cols-2 sm:grid-cols-3 gap-4 text-sm text-white/80">
               {quickStats.map((stat) => (
                 <div key={stat.label} className="rounded-2xl bg-white/10 px-4 py-3">
                   <div className="text-lg font-bold text-white">{stat.value}</div>
                   <div className="text-[10px] uppercase tracking-[0.3em] text-white/70">{stat.label}</div>
                   <p className="text-xs text-white/70">{stat.detail}</p>
                 </div>
               ))}
             </div>

             <p className="text-sm text-white/70">
               WhatsApp-Support, persönliche Onboarding-Calls und wöchentliche LIVE-Coachings mit dem Gründerteam
               halten dich auf Kurs.
             </p>
           </div>

           <div className="relative">
             <div className="absolute -inset-2 rounded-3xl bg-gradient-to-br from-cyan-400/40 via-blue-500/40 to-violet-500/40 blur-3xl" />
             <div className="relative rounded-3xl border border-white/10 bg-white/5 p-8 shadow-2xl backdrop-blur">
               <div className="rounded-2xl border border-white/10 bg-slate-900/80 p-6 text-white">
                 <p className="text-xs uppercase tracking-[0.3em] text-white/50">Live Blick ins Cockpit</p>
                 <div className="mt-4 space-y-4 text-left">
                   <div>
                     <p className="text-xs text-white/60">Conversion Funnel</p>
                     <div className="text-3xl font-bold">+28% Conversion</div>
                   </div>
                   <div>
                     <p className="text-xs text-white/60">Newsletter Open Rate</p>
                     <div className="text-3xl font-bold">68%</div>
                   </div>
                   <div>
                     <p className="text-xs text-white/60">Member Launches</p>
                     <div className="text-3xl font-bold">8</div>
                   </div>
                 </div>
                 <div className="mt-6 rounded-2xl bg-white/10 px-4 py-3 text-sm text-white/80">
                   <p className="font-semibold">alfi AI Vorschläge</p>
                   <p className="text-xs text-white/70">Automatisierte E-Mails, Upsells & Launch-Checklisten</p>
                 </div>
               </div>
             </div>
           </div>
         </div>
       </div>
     </section>
   );
 }
