# Phase 6: Redesign Foundation
Datum: 2026-05-22
Status: completed

## Implementierte Änderungen

### components.json (neu)
- shadcn/ui New York style konfiguriert
- typescript: true, rsc: true
- cssVariables: true
- Aliases: @/components, @/lib/utils, @/components/ui

### tailwind.config.ts
- shadcn/ui Standard-Tokens ergänzt: card, popover, primary, secondary, muted, accent, destructive, border, input, ring, chart-1..5
- borderRadius mit CSS-Variable `--radius`
- Bestehende complyo.* Token-Farben bleiben erhalten

### globals.css
- shadcn/ui New York OKLCH-kompatible Tokens in `:root` (dark) und `.light` ergänzt:
  - --card, --popover, --primary, --secondary, --muted, --accent, --destructive, --border, --input, --ring, --radius, --chart-1..5
- Vollständig kompatibel mit bestehenden Glassmorphism-Styles

### providers.tsx
- `next-themes@0.4.6` ThemeProvider als Root-Wrapper
- `attribute="class"`, `defaultTheme="dark"`, `enableSystem`, `storageKey="complyo-theme"`
- Kompatibel mit bestehendem ThemeContext (gleicher localStorage-Key)

### next-themes
- `next-themes@0.4.6` installiert

## TypeScript
- `tsc --noEmit`: 0 Fehler ✓

## Hinweise
- Tailwind bleibt v3 (kein Breaking-Change-Upgrade auf v4 in dieser Phase)
- shadcn/ui Komponenten in `components/ui/` bereits vorhanden, jetzt korrekt konfiguriert
- `components/ui-v2/` wird in P7 (Redesign Pages) angelegt wenn neue Komponenten benötigt werden
