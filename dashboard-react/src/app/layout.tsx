export const runtime = 'nodejs'
import type { Metadata } from 'next'
import Link from 'next/link';
import './globals.css'
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
        <Providers>
          {children}
          <AIAssistant />
        </Providers>
      </body>
    </html>
  )
}
