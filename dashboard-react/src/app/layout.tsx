export const runtime = 'nodejs'
import type { Metadata } from 'next'
import Link from 'next/link';
import './globals.css'
import Script from 'next/script'
import Providers from './providers'  // <— WICHTIG: Provider einbinden
import { AIAssistant } from '@/components/ai/AIAssistant'

export const metadata: Metadata = {
  title: 'Complyo Dashboard - KI-gestützte Website-Compliance',
  description: 'Automatische DSGVO, TTDSG & Barrierefreiheits-Compliance mit KI',
  keywords: ['DSGVO', 'TTDSG', 'Compliance', 'Website', 'KI', 'Automation'],
  authors: [{ name: 'Complyo Team' }],
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="de" className="scroll-smooth">
      <head>
        <link rel="icon" type="image/png" href="/favicon-dark.png" media="(prefers-color-scheme: dark)" />
        <link rel="icon" type="image/png" href="/favicon-light.png" media="(prefers-color-scheme: light)" />
        <link rel="apple-touch-icon" href="/favicon-dark.png" />
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                try {
                  var theme = localStorage.getItem('complyo-theme');
                  if (!theme) {
                    theme = 'dark'; // ✅ ALWAYS dark by default!
                    localStorage.setItem('complyo-theme', 'dark');
                  }
                  document.documentElement.classList.add(theme);
                } catch (e) {
                  document.documentElement.classList.add('dark');
                }
              })();
            `,
          }}
        />
      </head>
      <body className="min-h-screen text-white dark:text-white light:text-gray-900 antialiased">
        {/* Cookie-Banner - DSGVO-konform, lädt nach Interaktivität */}
        <Script
          src="https://api.complyo.tech/api/widgets/cookie-compliance.js"
          data-site-id="complyo-tech"
          data-complyo-site-id="complyo-tech"
          strategy="afterInteractive"
        />
        <Providers>
          {children}
          <AIAssistant />
        </Providers>
      </body>
    </html>
  )
}
