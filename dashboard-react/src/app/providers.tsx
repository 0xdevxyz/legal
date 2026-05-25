'use client'

import React from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { SessionProvider } from 'next-auth/react'
import { ThemeProvider as NextThemesProvider } from 'next-themes'
import { AuthProvider } from '@/contexts/AuthContext'
import { ThemeProvider } from '@/contexts/ThemeContext'
import { ToastProvider } from '@/components/ui/Toast'
import { ActiveSiteProvider } from '@/contexts/ActiveSiteContext'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60_000,
      retry: 1,
    },
  },
})

export default function Providers({ children }: { children: React.ReactNode }) {
  return (
    <NextThemesProvider
      attribute="class"
      defaultTheme="dark"
      enableSystem
      storageKey="complyo-theme"
    >
      <SessionProvider>
        <QueryClientProvider client={queryClient}>
          <ThemeProvider>
            <AuthProvider>
              <ActiveSiteProvider>
                <ToastProvider>
                  {children}
                </ToastProvider>
              </ActiveSiteProvider>
            </AuthProvider>
          </ThemeProvider>
        </QueryClientProvider>
      </SessionProvider>
    </NextThemesProvider>
  )
}
