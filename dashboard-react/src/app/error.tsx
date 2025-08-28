'use client'

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  return (
    <div style={{ padding: 24 }}>
      <h1>Unerwarteter Fehler</h1>
      <pre style={{ whiteSpace: 'pre-wrap' }}>{error?.message}</pre>
      <button onClick={() => reset()}>Nochmal versuchen</button>
    </div>
  )
}
