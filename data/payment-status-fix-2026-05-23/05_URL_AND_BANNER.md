# URL säubern & Banner-Lebenszyklus

## Problem
- Nach Rückkehr von Stripe blieben `?success=true&session_id=...` in der URL.
- Bei Reload wurde `verify-checkout` erneut aufgerufen (unnötig, potenziell fehlergebend).
- Banner war nicht schließbar und zeigte keinen konkreten Plan-Namen.

## Fixes

### URL säubern
Nach erfolgreicher Verifikation (auch bei `already_active`) und nach finalem Retry-Fehlschlag:
```ts
router.replace('/subscription', { scroll: false });
```
→ URL ist danach sauber `/subscription`, kein Reload-Problem.

### Banner mit Plan-Name
```tsx
<span>
  Zahlung erfolgreich — Ihr <strong>{activatedPlanName || planLabel}</strong> wurde aktiviert.
</span>
```
`activatedPlanName` wird aus dem `verify-checkout`-Response (`res.data.plan`) befüllt.

### Banner schließbar
```tsx
<button onClick={() => setActivationSuccess(false)}>
  <X className="w-4 h-4" />
</button>
```

### Polling-Feedback
Während Retries: blaues Banner „Plan wird aktiviert — bitte einen Moment warten…" mit Spinner.
Nach finalem Fehlschlag: gelbes Warn-Banner mit „Erneut prüfen"-Button.
