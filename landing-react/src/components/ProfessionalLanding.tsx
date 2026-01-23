'use client';

import React from 'react';
import Link from 'next/link';
import HeroSection from './landing/HeroSection';
import ProductFeatures from './landing/ProductFeatures';
import BenefitsGrid from './landing/BenefitsGrid';
import Testimonials from './landing/Testimonials';
import PricingTable from './landing/PricingTable';
import FAQAccordion from './landing/FAQAccordion';
import TrustMetrics from './landing/TrustMetrics';
import CTASection from './landing/CTASection';
import { Logo } from './Logo';

export default function ProfessionalLanding() {
  return (
    <div className="min-h-screen bg-white">
      <header>
        <nav className="backdrop-blur sticky top-0 z-30 border-b border-white/10 bg-white/80">
          <div className="max-w-7xl mx-auto flex items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
            <Link href="/" aria-label="Startseite">
              <Logo size="lg" variant="dark" />
            </Link>
            <div className="hidden items-center gap-8 text-sm font-semibold text-slate-700 md:flex">
              <a href="#features" className="hover:text-slate-900 transition">
                Features
              </a>
              <a href="#pricing" className="hover:text-slate-900 transition">
                Preise
              </a>
              <a href="#faq" className="hover:text-slate-900 transition">
                FAQ
              </a>
              <a
                href={process.env.NODE_ENV === 'production' ? 'https://app.complyo.tech' : 'http://localhost:3001'}
                className="rounded-full border border-slate-200 px-4 py-2 text-slate-900 transition hover:border-slate-400"
              >
                Login
              </a>
            </div>
          </div>
        </nav>
        <HeroSection />
      </header>

      <main role="main">
        <ProductFeatures />
        <BenefitsGrid />
        <TrustMetrics />
        <Testimonials />
        <PricingTable />
        <FAQAccordion />
      </main>

      <footer role="contentinfo" className="relative z-10">
        <CTASection />
        <div className="bg-slate-900 text-slate-400 py-8">
          <div className="max-w-7xl mx-auto flex flex-col items-center justify-between gap-4 px-4 sm:px-6 lg:px-8 md:flex-row">
            <p className="text-sm">© {new Date().getFullYear()} Complyo GmbH. Alle Rechte vorbehalten.</p>
            <div className="flex items-center gap-6 text-sm">
              <Link href="/impressum" className="hover:text-white transition">
                Impressum
              </Link>
              <Link href="/datenschutz" className="hover:text-white transition">
                Datenschutz
              </Link>
              <Link href="/agb" className="hover:text-white transition">
                AGB
              </Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
