'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { Menu, X } from 'lucide-react';
import HeroSection from './alfima-landing/HeroSection';
import ProductFeatures from './alfima-landing/ProductFeatures';
import BenefitsGrid from './alfima-landing/BenefitsGrid';
import Testimonials from './alfima-landing/Testimonials';
import PricingTable from './alfima-landing/PricingTable';
import FAQAccordion from './alfima-landing/FAQAccordion';
import TrustMetrics from './alfima-landing/TrustMetrics';
import CTASection from './alfima-landing/CTASection';
import { Logo } from './Logo';

const DASHBOARD_URL = process.env.NEXT_PUBLIC_DASHBOARD_URL || 'https://app.complyo.tech';

/**
 * AlfimaLanding - Creator Business Landing Page
 * Inspiriert von alfima.io - All-in-One für digitale Produkte
 */
export default function AlfimaLanding() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

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
                href={DASHBOARD_URL}
                className="rounded-full border border-slate-200 px-4 py-2 text-slate-900 transition hover:border-slate-400"
              >
                Login
              </a>
            </div>
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden p-2 rounded-lg text-slate-700 hover:bg-slate-100 transition-colors"
              aria-label={mobileMenuOpen ? 'Menü schließen' : 'Menü öffnen'}
              aria-expanded={mobileMenuOpen}
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
          {mobileMenuOpen && (
            <div className="md:hidden border-t border-slate-200 bg-white">
              <div className="px-4 py-4 space-y-3">
                <a href="#features" onClick={() => setMobileMenuOpen(false)} className="block text-slate-700 hover:text-slate-900 font-semibold py-2">Features</a>
                <a href="#pricing" onClick={() => setMobileMenuOpen(false)} className="block text-slate-700 hover:text-slate-900 font-semibold py-2">Preise</a>
                <a href="#faq" onClick={() => setMobileMenuOpen(false)} className="block text-slate-700 hover:text-slate-900 font-semibold py-2">FAQ</a>
                <a href={DASHBOARD_URL} className="block text-center rounded-full border border-slate-200 px-4 py-3 text-slate-900 font-semibold hover:border-slate-400 transition">Login</a>
              </div>
            </div>
          )}
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
