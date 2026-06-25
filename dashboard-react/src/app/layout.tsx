export const runtime = 'nodejs'
import type { Metadata } from 'next'
import './globals.css'
import Script from 'next/script'
import Providers from './providers'
import dynamic from 'next/dynamic'

const SidebarLayout = dynamic(
  () => import('@/components/dashboard/SidebarLayout').then((m) => m.SidebarLayout),
  { ssr: false }
)

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
                  // One-time migration to the new light-by-default look: flips
                  // any previously stored 'dark' to 'light' exactly once. The
                  // theme toggle keeps working normally afterwards.
                  var MIGRATION_KEY = 'complyo-theme-light-migration';
                  var theme = localStorage.getItem('complyo-theme');
                  if (!localStorage.getItem(MIGRATION_KEY)) {
                    theme = 'light';
                    localStorage.setItem('complyo-theme', 'light');
                    localStorage.setItem(MIGRATION_KEY, '1');
                  }
                  if (!theme) {
                    theme = 'light';
                    localStorage.setItem('complyo-theme', 'light');
                  }
                  document.documentElement.classList.add(theme);
                } catch (e) {
                  document.documentElement.classList.add('light');
                }
              })();
            `,
          }}
        />
      </head>
      <body className="min-h-screen text-white dark:text-white light:text-gray-900 antialiased">
        <Script
          src="https://api.complyo.de/api/widgets/cookie-compliance.js"
          data-site-id="complyo-tech"
          data-complyo-site-id="complyo-tech"
          strategy="afterInteractive"
        />
        <Providers>
          <SidebarLayout>
            {children}
          </SidebarLayout>
        </Providers>
      </body>
    </html>
  )
}
