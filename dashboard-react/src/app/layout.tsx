export const runtime = 'nodejs'
import type { Metadata } from 'next'
import './globals.css'
import Providers from './providers'  // <— WICHTIG: Provider einbinden

export const metadata: Metadata = {
  title: 'Complyo Dashboard - KI-gestützte Website-Compliance',
  description: 'Automatische DSGVO, TTDSG & Barrierefreiheits-Compliance mit KI',
  keywords: ['DSGVO', 'TTDSG', 'Compliance', 'Website', 'KI', 'Automation'],
  authors: [{ name: 'Complyo Team' }],
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="de">
      <body className="min-h-screen">
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
