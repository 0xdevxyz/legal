# Polling & Fehlerbehandlung

## Problem
`.catch(() => {})` schluckte alle Fehler bei `verify-checkout` still. Bei verzögertem Webhook
sah der User nichts außer dem veralteten Plan-Status.

## Implementierung

### Konstanten
```ts
const MAX_RETRIES = 6;
const RETRY_INTERVAL_MS = 5000;  // 30 s Gesamt-Fenster
```

### Retry-Logik in `handleVerifyCheckout`
```ts
async (sessionId: string, attempt = 1) => {
  setVerifying(true);
  try {
    const res = await apiClient.get(`/api/stripe/verify-checkout?session_id=${sessionId}`);
    if (res.data.activated || res.data.already_active) {
      // Erfolg
    } else if (attempt < MAX_RETRIES) {
      console.warn(`[verify-checkout] retry ${attempt}/${MAX_RETRIES}`);
      setTimeout(() => handleVerifyCheckout(sessionId, attempt + 1), RETRY_INTERVAL_MS);
    } else {
      setVerifyError('Aktivierung dauert ungewöhnlich lange...');
    }
  } catch {
    if (attempt < MAX_RETRIES) {
      setTimeout(() => handleVerifyCheckout(sessionId, attempt + 1), RETRY_INTERVAL_MS);
    } else {
      setVerifyError('Aktivierung dauert ungewöhnlich lange...');
    }
  }
}
```

### Cleanup
`useEffect` gibt eine Cleanup-Funktion zurück, die ausstehende Timeouts abbricht:
```ts
return () => { if (retryTimerRef.current) clearTimeout(retryTimerRef.current); };
```

### UI-Zustände
| Zustand | UI |
|---------|-----|
| Verifying = true | Blauer Spinner-Banner |
| verifyError gesetzt | Gelbes Warn-Banner mit Retry-Button |
| activationSuccess = true | Grünes Erfolgs-Banner mit Plan-Name, schließbar |
