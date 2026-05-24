# Auth-Session-Refresh nach Plan-Aktivierung

## Problem

Nach `verify-checkout` wurde `subscription-status` neu geladen, aber die NextAuth-Session
(`useAuth().user.plan_type`, `user.active_modules`) blieb veraltet. Sidebar und andere Seiten
zeigten weiterhin den alten Plan, bis der User sich neu einloggte.

## Fix

### AuthContext.tsx
`refreshUser`-Funktion hinzugefügt, die `update()` von NextAuth aufruft:

```ts
const refreshUser = async () => {
  await update();
};
```

Im `AuthContextType`-Interface und im Default-Fallback (`useAuth()` ohne Provider) ergänzt.

### subscription/page.tsx

Nach erfolgreichem `verify-checkout`:
```ts
await updateSession();          // NextAuth zieht neue plan_type/active_modules
await loadSubscriptionStatus(); // subscription-status neu laden
```

`useSession().update` direkt importiert (kein Umweg über AuthContext nötig, da `useSession` in
'next-auth/react' direkt verfügbar ist).

## Hinweis
NextAuth `update()` ist nicht garantiert synchron — daher wird `subscription-status` als
primäre Wahrheitsquelle für die Plan-Anzeige verwendet. Die Session liefert nur ein Backup.
