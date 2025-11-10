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
      <body className="min-h-screen bg-gradient-mesh text-white antialiased">
        <Providers>
          {children}
          <AIAssistant />
        </Providers>
      </body>
    </html>
  )
}
