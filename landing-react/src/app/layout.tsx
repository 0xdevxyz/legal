import './globals.css'
import type { Metadata, Viewport } from 'next'
import { Inter } from 'next/font/google'
import Script from 'next/script'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Complyo - Website Compliance & Abmahnschutz',
  description: 'Von abmahngefaehrdet zu rechtssicher in 24 Stunden. DSGVO, TTDSG, Barrierefreiheit - KI-gestuetzte Compliance-Loesung.',
  keywords: 'DSGVO, TTDSG, Website Compliance, Abmahnschutz, Barrierefreiheit, Cookie Banner',
  authors: [{ name: 'Complyo Team' }],
  robots: 'index, follow',
  metadataBase: new URL('https://complyo.tech'),
  openGraph: {
    title: 'Complyo - Website Compliance & Abmahnschutz',
    description: 'Von abmahngefaehrdet zu rechtssicher in 24 Stunden. DSGVO, TTDSG, Barrierefreiheit - KI-gestuetzte Compliance-Loesung fuer Ihr Unternehmen.',
    url: 'https://complyo.tech',
    siteName: 'Complyo',
    locale: 'de_DE',
    type: 'website',
    images: [{ url: '/logo-dark.png', width: 512, height: 512, alt: 'Complyo Logo' }],
  },
  twitter: {
    card: 'summary',
    title: 'Complyo - Website Compliance & Abmahnschutz',
    description: 'DSGVO, TTDSG & Barrierefreiheit - KI-gestuetzte Compliance-Loesung.',
    images: ['/logo-dark.png'],
  },
  alternates: {
    canonical: '/',
  },
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
        <script dangerouslySetInnerHTML={{ __html: `(function(){try{if(window.matchMedia('(prefers-color-scheme: dark)').matches){document.documentElement.classList.add('dark')}}catch(e){}})()` }} />
        <link rel="icon" type="image/png" href="/favicon-dark.png" media="(prefers-color-scheme: dark)" />
        <link rel="icon" type="image/png" href="/favicon-light.png" media="(prefers-color-scheme: light)" />
        <link rel="apple-touch-icon" href="/favicon-dark.png" />
        <meta name="theme-color" content="#0a0a0a" media="(prefers-color-scheme: dark)" />
        <meta name="theme-color" content="#ffffff" media="(prefers-color-scheme: light)" />
      </head>
      <body className={`${inter.className} antialiased`}>
        {/* Cookie-Banner Script - lädt Content Blocker + Banner in einem Bundle */}
        <Script
          src="https://api.complyo.tech/api/widgets/cookie-compliance.js"
          data-site-id="complyo-tech"
          data-complyo-site-id="complyo-tech"
          strategy="beforeInteractive"
        />
        
        {children}
        <Script
          src="https://api.complyo.tech/api/widgets/accessibility.js?version=6"
          data-site-id="scan-91778ad450e1"
          data-auto-fix="true"
          data-show-toolbar="true"
          strategy="afterInteractive"
        />
      </body>
    </html>
  )
}
