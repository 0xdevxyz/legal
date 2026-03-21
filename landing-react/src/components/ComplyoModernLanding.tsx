'use client';

import React, { useState } from 'react';
import { Menu, X, ArrowRight, Check } from 'lucide-react';

const DASHBOARD_URL = process.env.NEXT_PUBLIC_DASHBOARD_URL || 'https://app.complyo.de';
const REGISTER_URL = `${DASHBOARD_URL}/register`;

const c = {
  bg: '#faf9f7',
  white: '#ffffff',
  gray50: '#f9fafb',
  gray100: '#f3f4f6',
  gray200: '#e5e7eb',
  gray400: '#9ca3af',
  gray500: '#6b7280',
  gray600: '#4b5563',
  gray700: '#374151',
  gray900: '#111827',
  green50: '#f0fdf4',
  green200: '#bbf7d0',
  green700: '#15803d',
  orange500: '#f97316',
  blue600: '#2563eb',
  purple100: '#f3e8ff',
  purple700: '#7e22ce',
  yellow100: '#fef9c3',
  yellow700: '#a16207',
  green100: '#dcfce7',
};

export default function ComplyoModernLanding() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <div style={{ minHeight: '100vh', backgroundColor: c.bg, color: c.gray900, fontFamily: 'Inter, sans-serif', colorScheme: 'light' }}>

      {/* Nav */}
      <nav style={{ position: 'fixed', top: 0, left: 0, right: 0, zIndex: 50, backgroundColor: `${c.bg}ee`, backdropFilter: 'blur(12px)', borderBottom: `1px solid ${c.gray200}` }}>
        <div style={{ maxWidth: 960, margin: '0 auto', padding: '0 24px', height: 56, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <a href="/" style={{ fontWeight: 600, fontSize: 18, letterSpacing: '-0.03em', color: c.gray900, textDecoration: 'none' }}>complyo</a>
          <div style={{ display: 'flex', alignItems: 'center', gap: 32 }} className="hidden-mobile">
            <a href="#features" style={{ fontSize: 14, color: c.gray600, textDecoration: 'none' }}>Features</a>
            <a href="#pricing" style={{ fontSize: 14, color: c.gray600, textDecoration: 'none' }}>Preise</a>
            <a href={DASHBOARD_URL} style={{ fontSize: 14, color: c.gray600, textDecoration: 'none' }}>Anmelden</a>
            <a href={REGISTER_URL} style={{ backgroundColor: c.gray900, color: c.white, fontSize: 14, padding: '8px 18px', borderRadius: 999, textDecoration: 'none', fontWeight: 500 }}>
              Kostenlos starten
            </a>
          </div>
          <button onClick={() => setMobileMenuOpen(!mobileMenuOpen)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: c.gray700, padding: 4 }} className="show-mobile">
            {mobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
        {mobileMenuOpen && (
          <div style={{ backgroundColor: c.bg, borderTop: `1px solid ${c.gray200}`, padding: '16px 24px', display: 'flex', flexDirection: 'column', gap: 16, fontSize: 14 }}>
            <a href="#features" onClick={() => setMobileMenuOpen(false)} style={{ color: c.gray700, textDecoration: 'none' }}>Features</a>
            <a href="#pricing" onClick={() => setMobileMenuOpen(false)} style={{ color: c.gray700, textDecoration: 'none' }}>Preise</a>
            <a href={DASHBOARD_URL} style={{ color: c.gray700, textDecoration: 'none' }}>Anmelden</a>
            <a href={REGISTER_URL} style={{ backgroundColor: c.gray900, color: c.white, padding: '10px 18px', borderRadius: 999, textAlign: 'center', textDecoration: 'none', fontWeight: 500 }}>Kostenlos starten</a>
          </div>
        )}
      </nav>

      <style>{`
        @media (max-width: 768px) { .hidden-mobile { display: none !important; } }
        @media (min-width: 769px) { .show-mobile { display: none !important; } }
        * { box-sizing: border-box; }
      `}</style>

      {/* Hero */}
      <section style={{ paddingTop: 140, paddingBottom: 96, padding: '140px 24px 96px', textAlign: 'center' }}>
        <div style={{ maxWidth: 720, margin: '0 auto' }}>
          <h1 style={{ fontSize: 'clamp(36px, 6vw, 60px)', fontWeight: 700, lineHeight: 1.1, letterSpacing: '-0.03em', marginBottom: 24, color: c.gray900 }}>
            Website rechtssicher,<br />ohne Programmierer
          </h1>
          <p style={{ fontSize: 18, color: c.gray500, marginBottom: 40, maxWidth: 480, margin: '0 auto 40px', lineHeight: 1.7 }}>
            Complyo prüft Ihre Website auf DSGVO- und Barrierefreiheitsverstöße und liefert sofort umsetzbare Fixes — automatisch.
          </p>
          <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'center', gap: 16 }}>
            <a href={REGISTER_URL} style={{ display: 'inline-flex', alignItems: 'center', gap: 8, backgroundColor: c.gray900, color: c.white, padding: '12px 24px', borderRadius: 999, fontSize: 14, fontWeight: 500, textDecoration: 'none' }}>
              Kostenlos starten <ArrowRight size={16} />
            </a>
            <span style={{ fontSize: 14, color: c.gray400 }}>Complyo läuft auf Ihrer Website</span>
          </div>
        </div>

        {/* Dashboard Mock */}
        <div style={{ maxWidth: 800, margin: '64px auto 0', backgroundColor: c.white, borderRadius: 16, border: `1px solid ${c.gray200}`, boxShadow: '0 20px 60px rgba(0,0,0,0.08)', overflow: 'hidden' }}>
          <div style={{ backgroundColor: c.gray50, borderBottom: `1px solid ${c.gray200}`, padding: '12px 16px', display: 'flex', alignItems: 'center', gap: 8 }}>
            <div style={{ width: 12, height: 12, borderRadius: '50%', backgroundColor: '#f87171' }}></div>
            <div style={{ width: 12, height: 12, borderRadius: '50%', backgroundColor: '#fbbf24' }}></div>
            <div style={{ width: 12, height: 12, borderRadius: '50%', backgroundColor: '#34d399' }}></div>
            <div style={{ marginLeft: 16, backgroundColor: c.white, border: `1px solid ${c.gray200}`, borderRadius: 6, padding: '4px 12px', fontSize: 12, color: c.gray500 }}>
              app.complyo.de/dashboard
            </div>
          </div>
          <div style={{ padding: 32, backgroundColor: c.white }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24 }}>
              <div>
                <div style={{ fontSize: 11, color: c.gray400, textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 4 }}>Compliance Score</div>
                <div style={{ fontSize: 40, fontWeight: 700, color: c.gray900 }}>92%</div>
              </div>
              <div style={{ backgroundColor: c.green50, border: `1px solid ${c.green200}`, color: c.green700, fontSize: 13, fontWeight: 500, padding: '8px 16px', borderRadius: 999 }}>
                WCAG AA konform
              </div>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16 }}>
              {[
                { label: 'Gefundene Probleme', value: '3', color: c.orange500 },
                { label: 'Bereits behoben', value: '14', color: c.green700 },
                { label: 'Monitoring aktiv', value: '✓', color: c.blue600 },
              ].map((stat) => (
                <div key={stat.label} style={{ backgroundColor: c.gray50, borderRadius: 12, padding: 16, textAlign: 'center' }}>
                  <div style={{ fontSize: 24, fontWeight: 700, marginBottom: 4, color: stat.color }}>{stat.value}</div>
                  <div style={{ fontSize: 12, color: c.gray500 }}>{stat.label}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Trust */}
      <section style={{ padding: '48px 24px', borderTop: `1px solid ${c.gray200}`, borderBottom: `1px solid ${c.gray200}`, backgroundColor: c.white }}>
        <div style={{ maxWidth: 800, margin: '0 auto', textAlign: 'center' }}>
          <p style={{ fontSize: 11, color: c.gray400, textTransform: 'uppercase', letterSpacing: '0.15em', marginBottom: 32 }}>Genutzt von deutschen Unternehmen</p>
          <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: 32 }}>
            {['Mustermann GmbH', 'Digital AG', 'WebCraft', 'OnlineShop24', 'KanzleiNord', 'TechBerlin'].map((name) => (
              <span key={name} style={{ fontSize: 13, fontWeight: 600, color: c.gray400 }}>{name}</span>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section id="features" style={{ padding: '96px 24px', backgroundColor: c.bg }}>
        <div style={{ maxWidth: 900, margin: '0 auto' }}>
          <h2 style={{ fontSize: 32, fontWeight: 700, textAlign: 'center', marginBottom: 12, color: c.gray900 }}>So funktioniert Complyo</h2>
          <p style={{ textAlign: 'center', color: c.gray500, marginBottom: 64, maxWidth: 480, margin: '0 auto 64px' }}>
            In drei Schritten von der ungeprüften Website zur rechtssicheren Online-Präsenz.
          </p>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 20 }}>
            {[
              { step: '1', title: 'Website verbinden', desc: 'URL eingeben — Complyo scannt sofort alle Seiten auf rechtliche und Barrierefreiheitsprobleme.', tag: 'Dauert 2 Minuten', tagBg: c.purple100, tagColor: c.purple700 },
              { step: '2', title: 'Fixes erhalten', desc: 'KI analysiert jeden Befund und liefert konkrete Lösungen — kein Programmierwissen nötig.', tag: 'Dauert 5 Minuten', tagBg: c.yellow100, tagColor: c.yellow700 },
              { step: '3', title: 'Dauerhaft geschützt', desc: 'Complyo überwacht Ihre Website laufend und warnt automatisch bei neuen Problemen.', tag: 'Spart täglich Zeit', tagBg: c.green100, tagColor: c.green700 },
            ].map((item) => (
              <div key={item.step} style={{ backgroundColor: c.white, borderRadius: 16, border: `1px solid ${c.gray200}`, padding: 24 }}>
                <span style={{ display: 'inline-block', fontSize: 11, fontWeight: 600, padding: '4px 12px', borderRadius: 999, backgroundColor: item.tagBg, color: item.tagColor, marginBottom: 20 }}>
                  {item.tag}
                </span>
                <div style={{ fontSize: 40, fontWeight: 700, color: c.gray200, marginBottom: 12 }}>{item.step}</div>
                <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 8, color: c.gray900 }}>{item.title}</h3>
                <p style={{ fontSize: 14, color: c.gray500, lineHeight: 1.6 }}>{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section style={{ padding: '96px 24px', backgroundColor: c.white, borderTop: `1px solid ${c.gray200}`, borderBottom: `1px solid ${c.gray200}` }}>
        <div style={{ maxWidth: 900, margin: '0 auto' }}>
          <h2 style={{ fontSize: 32, fontWeight: 700, textAlign: 'center', marginBottom: 12, color: c.gray900 }}>Alles was Sie brauchen</h2>
          <p style={{ textAlign: 'center', color: c.gray500, marginBottom: 64, maxWidth: 480, margin: '0 auto 64px' }}>
            Complyo deckt alle rechtlichen Pflichten für Ihre Website ab.
          </p>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 16 }}>
            {[
              { title: 'WCAG Barrierefreiheits-Scan', desc: 'Automatische Prüfung auf über 50 Kriterien nach WCAG 2.1 AA.' },
              { title: 'DSGVO Cookie-Compliance', desc: 'Prüft Ihre Cookie-Banner und Einwilligungslösungen.' },
              { title: 'KI-generierte Fixes', desc: 'Konkrete Lösungsvorschläge für jeden Befund — sofort umsetzbar.' },
              { title: 'Rechtssichere Dokumentation', desc: 'Export-Berichte für Behörden, Audits und Ihre Unterlagen.' },
              { title: 'Monitoring & Alerts', desc: 'Tägliche Überwachung — sofortige Benachrichtigung bei neuen Problemen.' },
              { title: 'Experten on Demand', desc: 'Professionelle Unterstützung wenn Sie Hilfe bei der Umsetzung brauchen.' },
            ].map((f) => (
              <div key={f.title} style={{ display: 'flex', gap: 16, padding: 20, borderRadius: 12, backgroundColor: c.gray50, border: `1px solid ${c.gray100}` }}>
                <div style={{ flexShrink: 0, width: 20, height: 20, marginTop: 2, backgroundColor: c.gray900, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Check size={12} color={c.white} />
                </div>
                <div>
                  <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 4, color: c.gray900 }}>{f.title}</div>
                  <div style={{ fontSize: 13, color: c.gray500, lineHeight: 1.6 }}>{f.desc}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" style={{ padding: '96px 24px', backgroundColor: c.bg }}>
        <div style={{ maxWidth: 960, margin: '0 auto' }}>
          <h2 style={{ fontSize: 32, fontWeight: 700, textAlign: 'center', marginBottom: 12, color: c.gray900 }}>Einfache Preise</h2>
          <p style={{ textAlign: 'center', color: c.gray500, marginBottom: 64, maxWidth: 480, margin: '0 auto 64px' }}>
            Kein verstecktes Kleingedrucktes. Jederzeit kündbar.
          </p>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 20, alignItems: 'start' }}>
            {([
              {
                slug: 'free',
                name: 'Kostenlos',
                priceMain: '0',
                priceSub: '/Monat',
                priceNote: '',
                desc: 'Für erste Einschätzung',
                features: ['1 Website', 'Vollständiger Compliance-Scan', 'Abmahnrisiko in Euro', 'PDF-Report', 'Handlungsempfehlungen'],
                cta: 'Kostenlos starten',
                ctaHref: REGISTER_URL,
                highlighted: false,
              },
              {
                slug: 'single',
                name: 'Einzelmodul',
                priceMain: 'ab 19',
                priceSub: '/Modul/Monat',
                priceNote: '19 € je gebuchtem Modul',
                desc: 'Nur was Sie brauchen',
                features: ['1 Website', 'Frei wählbare Module', 'Cookie & DSGVO', 'Barrierefreiheit', 'Rechtliche Texte', 'Monitoring'],
                cta: 'Module wählen',
                ctaHref: `${REGISTER_URL}?plan=single`,
                highlighted: false,
              },
              {
                slug: 'complete',
                name: 'Komplett',
                priceMain: '49',
                priceSub: '/Monat',
                priceNote: 'Alle 4 Module inklusive',
                desc: 'Der intelligente Weg',
                features: ['1 Website', 'Alle 4 Module inklusive', 'KI-Fixes & Automatisierung', 'Monatliche Re-Scans', 'Live-Dashboard'],
                cta: 'Jetzt starten',
                ctaHref: `${REGISTER_URL}?plan=complete`,
                highlighted: true,
              },
              {
                slug: 'expert',
                name: 'Experten-Service',
                priceMain: '39',
                priceSub: '/Monat',
                priceNote: '+ 2.990 € Einrichtung (einmalig)',
                desc: 'Full-Service durch Experten',
                features: ['1 Website', 'Alle 4 Module inklusive', 'Persönliche Anwalts-Betreuung', 'Branchenspezifische Compliance', '100 % Umsetzungsgarantie'],
                cta: 'Experten kontaktieren',
                ctaHref: `${REGISTER_URL}?plan=expert`,
                highlighted: false,
              },
              {
                slug: 'agency',
                name: 'Agentur',
                priceMain: '490',
                priceSub: '/Monat',
                priceNote: '25 Websites – ein Account',
                desc: 'Für Agenturen & Dienstleister',
                features: ['25 Websites zentral', 'Alle 4 Module inklusive', 'White-Label-Dashboard', 'Agentur-Reports für Kunden', 'Priority Support'],
                cta: 'Agentur-Plan anfragen',
                ctaHref: `${REGISTER_URL}?plan=agency`,
                highlighted: false,
              },
            ] as const).map((plan) => (
              <div key={plan.slug} style={{
                borderRadius: 16,
                border: `1px solid ${plan.highlighted ? c.gray900 : c.gray200}`,
                padding: 28,
                display: 'flex',
                flexDirection: 'column',
                backgroundColor: plan.highlighted ? c.gray900 : c.white,
              }}>
                <div style={{ marginBottom: 24 }}>
                  <div style={{ fontSize: 11, fontWeight: 600, textTransform: 'uppercase' as const, letterSpacing: '0.1em', marginBottom: 8, color: c.gray400 }}>
                    {plan.name}
                  </div>
                  <div style={{ display: 'flex', alignItems: 'flex-end', gap: 4, marginBottom: 4 }}>
                    <span style={{ fontSize: 36, fontWeight: 700, color: plan.highlighted ? c.white : c.gray900 }}>€{plan.priceMain}</span>
                    <span style={{ fontSize: 12, marginBottom: 5, color: plan.highlighted ? c.gray400 : c.gray500 }}>{plan.priceSub}</span>
                  </div>
                  {plan.priceNote && (
                    <div style={{ fontSize: 11, color: plan.highlighted ? c.gray400 : c.gray500, marginBottom: 4 }}>{plan.priceNote}</div>
                  )}
                  <div style={{ fontSize: 13, color: plan.highlighted ? c.gray400 : c.gray500 }}>{plan.desc}</div>
                </div>
                <ul style={{ listStyle: 'none', padding: 0, margin: '0 0 32px', display: 'flex', flexDirection: 'column', gap: 10, flex: 1 }}>
                  {plan.features.map((f) => (
                    <li key={f} style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 13 }}>
                      <Check size={14} color={c.gray400} style={{ flexShrink: 0 }} />
                      <span style={{ color: plan.highlighted ? c.gray200 : c.gray600 }}>{f}</span>
                    </li>
                  ))}
                </ul>
                <a href={plan.ctaHref} style={{
                  display: 'block',
                  textAlign: 'center',
                  fontSize: 13,
                  fontWeight: 500,
                  padding: '12px 16px',
                  borderRadius: 999,
                  textDecoration: 'none',
                  backgroundColor: plan.highlighted ? c.white : c.gray900,
                  color: plan.highlighted ? c.gray900 : c.white,
                }}>
                  {plan.cta}
                </a>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section style={{ padding: '96px 24px', backgroundColor: c.gray900, textAlign: 'center' }}>
        <div style={{ maxWidth: 600, margin: '0 auto' }}>
          <h2 style={{ fontSize: 36, fontWeight: 700, color: c.white, marginBottom: 16, letterSpacing: '-0.02em' }}>Bereit für eine rechtssichere Website?</h2>
          <p style={{ fontSize: 16, color: c.gray400, marginBottom: 40 }}>
            Deutsche Unternehmen schützen sich bereits mit Complyo.
          </p>
          <a href={REGISTER_URL} style={{ display: 'inline-flex', alignItems: 'center', gap: 8, backgroundColor: c.white, color: c.gray900, padding: '14px 28px', borderRadius: 999, fontSize: 14, fontWeight: 600, textDecoration: 'none' }}>
            Kostenlos starten <ArrowRight size={16} />
          </a>
          <p style={{ marginTop: 16, fontSize: 12, color: c.gray500 }}>Kein Risiko — kostenlos, kein Vertrag</p>
        </div>
      </section>

      {/* Footer */}
      <footer style={{ backgroundColor: c.gray900, borderTop: `1px solid #1f2937`, padding: '40px 24px' }}>
        <div style={{ maxWidth: 960, margin: '0 auto', display: 'flex', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'center', gap: 16, fontSize: 13, color: c.gray500 }}>
          <span style={{ fontWeight: 600, color: c.white }}>complyo</span>
          <div style={{ display: 'flex', gap: 24 }}>
            <a href="/datenschutz" style={{ color: c.gray500, textDecoration: 'none' }}>Datenschutz</a>
            <a href="/impressum" style={{ color: c.gray500, textDecoration: 'none' }}>Impressum</a>
            <a href="/agb" style={{ color: c.gray500, textDecoration: 'none' }}>AGB</a>
          </div>
          <span>© {new Date().getFullYear()} Complyo</span>
        </div>
      </footer>

    </div>
  );
}
