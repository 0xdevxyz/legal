# Projektstruktur-Analyse - INDEX

## Dokumentation in /data

Alle folgenden Dateien wurden in `/home/clawd/saas/legal/data/` erstellt:

1. **PROJECT_STRUCTURE_ANALYSIS.md** (umfassend)
   - Detaillierte Analyse aller Theme-Dateien
   - Farbpaletten und CSS-Variablen
   - Animationen und Keyframes
   - Layout und Theme-Management System
   - Dateien-Übersicht mit Zeilenzahlen

2. **THEME_FILES_DIRECTORY_MAP.md** (Dateibaum)
   - Vollständiger Dateibaum mit Pfaden
   - Absolute Dateipfade (alle 11 Hauptdateien)
   - Datei-Abhängigkeiten und Imports
   - CSS-Variablen-Übersicht
   - CSS Klassen nach Kategorie
   - Animationen - vollständige Liste

3. **THEME_QUICK_REFERENCE.md** (Praktisch)
   - Schnelle Übersicht zum Nachschlagen
   - Code-Beispiele für Entwickler
   - Häufige Aufgaben (Copy-Paste ready)
   - Color Palette Übersicht
   - Tipps & Best Practices

---

## ERGEBNIS: Gefundene Dateien

### Total: 11 Hauptdateien + 3 Layoutdateien

#### THEME & CONFIG (2)
1. `/home/clawd/saas/legal/dashboard-react/tailwind.config.ts` (94 Zeilen)
2. `/home/clawd/saas/legal/landing-react/tailwind.config.ts` (54 Zeilen)

#### CSS / STYLES (3)
3. `/home/clawd/saas/legal/dashboard-react/src/app/globals.css` (915 Zeilen)
4. `/home/clawd/saas/legal/landing-react/src/app/globals.css` (Tailwind directives)
5. `/home/clawd/saas/legal/landing-react/src/styles/design-system.css` (390 Zeilen)

#### THEME CONTEXT (1)
6. `/home/clawd/saas/legal/dashboard-react/src/contexts/ThemeContext.tsx` (77 Zeilen)
   - Enthält: ThemeProvider, useTheme() Hook, localStorage Persistierung

#### LAYOUT DATEIEN (3)
7. `/home/clawd/saas/legal/dashboard-react/src/app/layout.tsx`
8. `/home/clawd/saas/legal/dashboard-react/src/app/ai-compliance/layout.tsx`
9. `/home/clawd/saas/legal/landing-react/src/app/layout.tsx`

#### BUTTON KOMPONENTEN (2)
10. `/home/clawd/saas/legal/dashboard-react/src/components/ui/button.tsx` (50 Zeilen)
11. `/home/clawd/saas/legal/landing-react/src/components/ui/button.tsx` (50 Zeilen)

---

## KEY FINDINGS

### 1. Theme System
- **Basis**: CSS Custom Properties (:root, .light, .dark)
- **Verwaltung**: React Context (ThemeContext.tsx) mit useTheme() Hook
- **Persistierung**: localStorage ('complyo-theme')
- **Fallback**: System Preference (prefers-color-scheme)
- **Umschaltung**: Klasse-basiert (.dark / .light auf <html>)

### 2. Farbpalette (Complyo)
Dashboard:
- Blue: #0ea5e9 (Sky-500)
- Purple: #a855f7 (Purple-500)
- Indigo: #6366f1 (Indigo-500)
- Dark: #0c0a09 (Stone-950)
- Slate: #18181b (Zinc-900)
- Accent: #14b8a6 (Teal-500)

Landing:
- Primary: #2563eb (Blue-600)
- Secondary: #8b5cf6 (Violet)
- Success/Warning/Danger/Info Farben

### 3. Komponenten
Button mit 5 Varianten:
- default (Gradient Blue→Purple)
- secondary (Zinc-800, Border)
- outline (Border-2)
- ghost (Minimal)
- destructive (Red)

Größen: sm, md, lg

### 4. CSS Klassen Kategorien
- `.glass-*` (Glassmorphism)
- `.ai-*` (AI-Komponenten mit Animationen)
- `.text-theme-*` (Theme-aware Text)
- `.bg-theme-*` (Theme-aware Background)
- `.sidebar-*` (Sidebar Navigation)
- `.stat-card-*` (Dashboard Stats)
- `.gauge-*` / `.flow-*` (Gauges und Flow Widgets)

### 5. Animationen
Tailwind Keyframes (8):
- fadeIn, slideUp, slideDown, scaleIn
- pulseGlow, float, gradient, shimmer

CSS Keyframes (14+):
- ai-pulse, ai-typing, ai-loading, ai-scan-line
- slide-in-* Variationen
- gauge-fill, flow-pulse, etc.

### 6. Accessibility (WCAG 2.4.7)
- :focus-visible automatisch auf allen interaktiven Elementen
- 2px outline mit Kontrast ≥3:1
- Focus Indicators in Dark und Light Mode

### 7. Responsive Design
- Tailwind Breakpoints
- Mobile-First Approach
- Sidebar collapsible
- Media Queries für Print und prefers-color-scheme

### 8. CSS Variablen
Root Level (~30+ Variablen):
- --background, --foreground
- --card-bg, --card-border
- --glass-bg, --glass-border
- --sidebar-* (Sidebar UI)
- --gauge-* (Gauge colors)
- --flow-* (Flow widget colors)
- --topbar-height, --sidebar-width

---

## STRUKTUR ÜBERSICHT

```
Theme System Architecture:
├── Config Layer
│   ├── tailwind.config.ts (Tailwind Theme Definition)
│   └── CSS Custom Properties (:root selectors)
│
├── Management Layer
│   ├── ThemeContext.tsx (React State)
│   ├── useTheme() Hook (Komponenten API)
│   └── localStorage (Persistierung)
│
├── Styling Layer
│   ├── globals.css (Global Styles)
│   ├── design-system.css (Landing Design Tokens)
│   └── UI Component Styles
│
├── Component Layer
│   ├── Button (5 Varianten)
│   ├── Cards (glass-effect, glass-card, glass-strong)
│   ├── AI-Elements (glow, badge, scanning, etc.)
│   └── Sidebar Navigation
│
└── Layout Layer
    ├── Root Layout (ThemeProvider wrapper)
    ├── Sub-Layouts (AI-Compliance)
    └── Dynamic Class Management (.dark / .light)
```

---

## SCHNELL-LINKS

### Zum Anschauen
- Farbpalette: `tailwind.config.ts` Zeile 12-24 (Dashboard) oder design-system.css Zeile 6-99 (Landing)
- Animationen: `tailwind.config.ts` Zeile 40-87 oder `globals.css` Zeile 138-194
- Theme Context: `ThemeContext.tsx` komplett (77 Zeilen)
- Button Component: `button.tsx` komplett (50 Zeilen)
- Glassmorphism: `globals.css` Zeile 434-467

### Zum Bearbeiten
- Neuer CSS Class: `globals.css` hinzufügen (Dark/Light modes berücksichtigen!)
- Neuer Tailwind Utility: `tailwind.config.ts` theme.extend anpassen
- Theme Persistierung ändern: `ThemeContext.tsx` Zeile 22
- Button Variante hinzufügen: `button.tsx` im variants Object

---

## WICHTIGE ERKENNTNISSE

1. **Dual Theme System**: Dark ist default, Light ist Override
2. **CSS-in-JS nicht nötig**: Alles mit CSS Custom Properties und Tailwind
3. **Performant**: Keine JavaScript-Animationen, reine CSS
4. **Responsive**: Sidebar, Gauge, Flow alle responsive gebaut
5. **Accessible**: WCAG 2.4.7 Focus Indikatoren eingebaut
6. **Wartbar**: Zentrale CSS-Variablen für einfache Änderungen
7. **Skalierbar**: Landing hat eigenes Design System, Dashboard erweitert Tailwind

---

## VERWENDETE TECHNOLOGIEN

- **CSS**: CSS Custom Properties, @layer, @keyframes, @media
- **Tailwind CSS**: config.ts, utility-first, dark mode class
- **React**: Context API, Hooks (useTheme, useContext)
- **Next.js**: App Router (layout.tsx)
- **Browser APIs**: localStorage, matchMedia (prefers-color-scheme)

---

## NÄCHSTE SCHRITTE (falls Modifikationen nötig)

1. Für neue Farben: `tailwind.config.ts` → `theme.extend.colors` aktualisieren
2. Für neue Animationen: `tailwind.config.ts` → `theme.extend.animation` oder `globals.css` @keyframes
3. Für neue Komponenten: Button-Pattern folgen (Varianten + Sizes)
4. Für neue CSS-Klassen: Immer `.light` und `.dark` Variants berücksichtigen
5. Für Performance: transform/opacity nutzen, width/height vermeiden

---

## ANALYSE DATUM

2026-05-02
Status: ABGESCHLOSSEN
Dokumentation: 3 Dateien in /data/
Hauptdateien analysiert: 11+3
Code-Zeilen gesamt: 1500+

