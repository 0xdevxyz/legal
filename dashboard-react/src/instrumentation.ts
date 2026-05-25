import * as Sentry from '@sentry/nextjs'

const SENTRY_DSN = process.env.SENTRY_DSN

export async function register() {
  if (!SENTRY_DSN) return

  if (process.env.NEXT_RUNTIME === 'nodejs') {
    Sentry.init({
      dsn: SENTRY_DSN,
      environment: process.env.NODE_ENV || 'production',
      release: process.env.GIT_COMMIT || 'unknown',
      tracesSampleRate: 0.1,
      sendDefaultPii: false,
    })
  }

  if (process.env.NEXT_RUNTIME === 'edge') {
    Sentry.init({
      dsn: SENTRY_DSN,
      environment: process.env.NODE_ENV || 'production',
      release: process.env.GIT_COMMIT || 'unknown',
      tracesSampleRate: 0.1,
    })
  }
}

export const onRequestError = Sentry.captureRequestError
