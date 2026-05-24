# Frontend-Fix: Field-Mismatch plan → plan_type

## Problem

`SubStatus`-Interface verwendete `plan: string`, aber das Backend liefert `plan_type: string`.

```ts
// Alt (falsch)
interface SubStatus { plan: string; ... }
// Lese-Stellen: sub?.plan ?? user?.plan_type ?? 'free'  →  immer undefined
```

## Fix

```ts
// Neu (korrekt)
interface SubStatus { plan_type: string; ... }
// Lese-Stellen: sub?.plan_type ?? user?.plan_type ?? 'free'
```

Geänderte Stellen in `subscription/page.tsx`:
- Interface `SubStatus` (war Zeile 80)
- `currentPlanType` (war Zeile 174) 
- `isCurrentPlan` im Planvergleich (war Zeile 309)
- `isFreePlan`-Check (war Zeile 176)

Zusätzlich: `PLAN_LABELS['unknown'] = 'Unbekannt'` als Safety-Fallback — verhindert leeren String.
