import './globals.css'
import type { Metadata, Viewport } from 'next'
import { Inter } from 'next/font/google'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Complyo - Website Compliance & Abmahnschutz',
  description: 'Von abmahngefährdet zu rechtssicher in 24 Stunden. DSGVO, TTDSG, Barrierefreiheit - KI-gestützte Compliance-Lösung.',
  keywords: 'DSGVO, TTDSG, Website Compliance, Abmahnschutz, Barrierefreiheit, Cookie Banner',
  authors: [{ name: 'Complyo Team' }],
  robots: 'index, follow',
}

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="de" className="scroll-smooth">
      <head>
        <link rel="icon" href="/favicon.ico" />
        <meta name="theme-color" content="#0a0a0a" />
      </head>
      <body className={`${inter.className} antialiased`}>
        {children}
      </body>
    </html>
  )
}
