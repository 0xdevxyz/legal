# Baseline — Ist-Zustand

## Beobachtetes Verhalten (Screenshot 2026-05-23)

- URL nach Rückkehr von Stripe: `?success=true&session_id=cs_test_b1JZYjZQ1xiG24qp3jE9fesu3cglq7iptg8kyWzAT0oD4dHIGwsRnKOlou?session_id=cs_test_...`
  → **Doppeltes `?`** — der session_id-Parameter ist doppelt und die zweite Instanz startet einen neuen Query-String.
- Plan-Anzeige: **„Unbekannt"**, Badge: **„Kostenlos"**
- Browser-Console: `XHR failed: GET /api/stripe/verify-checkout?session_id=cs_test_... → 400 (Bad Request)`

## Reproduktionsschritte

1. Einloggen als freier User
2. Subscription-Seite öffnen → `/subscription`
3. „Jetzt upgraden" für ein Paket klicken
4. Stripe Checkout mit Test-Karte `4242 4242 4242 4242` abschließen
5. Rückkehr zur App → Bug tritt auf

## Betroffene Code-Stellen

### Bug 1: Doppelter Query-String
**Datei:** `backend/stripe_routes.py:225`
```python
success_url=request.success_url + "?session_id={CHECKOUT_SESSION_ID}",
```
Frontend sendet bereits: `?success=true&session_id={CHECKOUT_SESSION_ID}`
→ Ergebnis: `...?success=true&session_id=xyz?session_id=xyz` (kaputte URL)

### Bug 2: Field-Mismatch plan vs plan_type
**Datei:** `dashboard-react/src/app/subscription/page.tsx:80`
```ts
interface SubStatus { plan: string; ... }  // falsch
```
**Backend** liefert `stripe_routes.py:328`:
```python
return { "plan_type": row["plan_type"], ... }
```
→ `sub.plan` ist immer `undefined` → `planLabel` = „Unbekannt"

### Bug 3: Kein Auth-Session-Refresh
**Datei:** `dashboard-react/src/app/subscription/page.tsx:99-122`
Nach Aktivierung wird `subscription-status` neu geladen, aber `useAuth().user.plan_type` (aus NextAuth-Session) bleibt veraltet.

### Bug 4: Query-Params bleiben in URL
**Datei:** `dashboard-react/src/app/subscription/page.tsx:99-108`
Kein `router.replace()` nach Verifikation → Bei Reload wird `verify-checkout` erneut aufgerufen.

### Bug 5: Stille Fehlerbehandlung
**Datei:** `dashboard-react/src/app/subscription/page.tsx:107`
```ts
.catch(() => {});  // Fehler werden verschluckt, kein UI-Feedback
```

## API-Response-Struktur (subscription-status)
```json
{
  "plan_type": "pro",
  "status": "active",
  "has_subscription": true,
  "fixes_limit": 999999,
  "websites_max": 10
}
```
**Kein `modules`-Array** → `activeModuleIds` bleibt leer.
